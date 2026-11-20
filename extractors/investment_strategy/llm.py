"""LLM 클라이언트. shared/ai_providers 경유 (환경변수 우선, secret 파일 차순위)."""
from __future__ import annotations

import json
import logging
import os
import re
import socket
import sys
import threading
import time
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from config import VideoSummary
from shared.ai_providers import build_clients

log = logging.getLogger(__name__)

# -- 프로바이더 상태 정책 -------------------------------------------------
# 죽은 엔드포인트를 매 호출마다 재시도하면 호출당 수 초를 버린다.
_PREFLIGHT_TIMEOUT = 0.35      # 로컬 엔드포인트 생존 확인 (초)
_COOLDOWN_RATE_LIMIT = 10.0    # 429: 잠깐 쉬고 다시 사용
_COOLDOWN_EMPTY = 10.0         # 빈 응답(추론 토큰 소진): 짧게 쉬고 재시도
_COOLDOWN_TRANSIENT = 60.0     # 연결/타임아웃: 중간 길이 제외
_COOLDOWN_BROKEN = 600.0       # 인증/모델 없음/잔액 부족 등: 런 전체 제외
_RATE_LIMIT_STRIKES = 2        # 429 연속 2회면 쿨다운 진입
_MAX_TOKEN_CEILING = 3000      # 빈 응답 재시도 시 상한
_WAIT_POLL = 0.5               # 대기 중 폴링 간격

# 프로바이더를 아예 못 쓰는 상태를 나타내는 메시지
_PERMANENT_HINTS = (
    "insufficient balance", "suspended", "invalid_api_key", "incorrect api key",
    "not found", "does not exist", "unsupported model",
)

_URL_RE = re.compile(r"https?://\S+")


class EmptyResponseError(RuntimeError):
    """추론 모델이 토큰 예산을 다 써서 본문 없이 끝난 경우."""


def _is_local_url(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").lower()
    return host in ("127.0.0.1", "localhost", "::1")


def _port_is_open(base_url: str) -> bool:
    parsed = urlparse(base_url)
    if not parsed.hostname:
        return False
    try:
        with socket.create_connection(
            (parsed.hostname, parsed.port or 80), timeout=_PREFLIGHT_TIMEOUT
        ):
            return True
    except OSError:
        return False


def _is_rate_limit(exc: Exception) -> bool:
    if getattr(exc, "status_code", None) == 429:
        return True
    name = type(exc).__name__
    if "RateLimit" in name:
        return True
    return "429" in str(exc)[:160]


def _is_transient(exc: Exception) -> bool:
    name = type(exc).__name__
    return any(key in name for key in ("Connection", "Timeout", "TryAgain", "InternalServer"))


def _is_permanent(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(hint in text for hint in _PERMANENT_HINTS)


def condense_text(text: str) -> str:
    """프롬프트에 넣기 전 잡음 제거.

    설명란의 링크/해시태그/과도한 공백은 토큰만 먹고 요약에 기여하지 않는다.
    토큰을 줄이면 응답 지연과 429(TPM 초과)가 함께 줄어든다.
    """
    if not text:
        return ""
    original = text.strip()
    cleaned = _URL_RE.sub(" ", original)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    # 링크 제거로 본문이 거의 사라졌다면 원문 유지 (정보 손실 방지)
    if len(cleaned) < 200 <= len(original):
        return original
    return cleaned


class InvestmentLLM:
    """투자 요약 전용. 키가 하나도 없으면 basic 모드(키워드 기반)로 폴백."""

    def __init__(self, order: list[str] | None = None) -> None:
        try:
            self.clients: list[dict] = build_clients(order=order)
        except ImportError:
            log.warning("openai 패키지 없음. basic 모드로 동작")
            self.clients = []

        # 재시도는 여기서 직접 관리한다. openai 내부 재시도(최대 24초 백오프)에
        # 맡기면 한 호출이 수십 초를 잡아먹고, 병렬 실행 이점도 사라진다.
        for provider in self.clients:
            provider["client"].max_retries = 0

        self.clients = [p for p in self.clients if self._reachable(p)]
        self._lock = threading.Lock()
        self._down_until: dict[str, float] = {}
        self._strikes: dict[str, int] = {}

    @staticmethod
    def _reachable(provider: dict) -> bool:
        """로컬 엔드포인트는 기동 여부를 먼저 확인해 죽은 프로바이더를 걸러낸다."""
        base_url = str(getattr(provider["client"], "base_url", ""))
        if not _is_local_url(base_url):
            return True
        if _port_is_open(base_url):
            return True
        log.warning(
            "로컬 LLM 엔드포인트 응답 없음 → 이번 실행에서 제외: %s (%s)",
            provider["name"], base_url,
        )
        return False

    @property
    def available(self) -> bool:
        return bool(self.clients)

    # -- 프로바이더 상태 -----------------------------------------------

    def _usable(self, patience: float = 0.0) -> list[dict]:
        now = time.time()
        with self._lock:
            down = dict(self._down_until)
        return [p for p in self.clients if down.get(p["name"], 0) <= now]

    def _next_wait(self) -> float:
        """모든 프로바이더가 쿨다운일 때 가장 빨리 풀리는 시각까지의 대기."""
        now = time.time()
        with self._lock:
            down = dict(self._down_until)
        if not self.clients:
            return 0.0
        if all(down.get(p["name"], 0) <= now for p in self.clients):
            # 쿨다운 없이 전부 실패한 경우: 과도한 즉시 재시도를 막는다
            return _WAIT_POLL
        return max(_WAIT_POLL, min(down.get(p["name"], 0) for p in self.clients) - now)

    def _mark_ok(self, name: str) -> None:
        with self._lock:
            self._strikes.pop(name, None)
            self._down_until.pop(name, None)

    def _mark_failure(self, name: str, exc: Exception) -> None:
        if _is_permanent(exc):
            cooldown = _COOLDOWN_BROKEN
            with self._lock:
                self._down_until[name] = time.time() + cooldown
                self._strikes.pop(name, None)
        elif _is_rate_limit(exc):
            with self._lock:
                strikes = self._strikes.get(name, 0) + 1
                if strikes >= _RATE_LIMIT_STRIKES:
                    self._down_until[name] = time.time() + _COOLDOWN_RATE_LIMIT
                    self._strikes[name] = 0
                else:
                    self._strikes[name] = strikes
        elif isinstance(exc, EmptyResponseError):
            with self._lock:
                self._down_until[name] = time.time() + _COOLDOWN_EMPTY
        else:
            cooldown = _COOLDOWN_TRANSIENT if _is_transient(exc) else _COOLDOWN_BROKEN
            with self._lock:
                self._down_until[name] = time.time() + cooldown
                self._strikes.pop(name, None)
        log.warning("LLM 오류 (%s): %s", name, str(exc)[:200])

    def _call_provider(
        self,
        provider: dict,
        prompt: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> tuple[str, Exception]:
        """프로바이더 1곳 호출. 빈 응답이면 예산을 늘려 1회만 재시도한다."""
        tokens = max_tokens
        last_error: Exception = EmptyResponseError("빈 응답")
        for _ in range(2):
            try:
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    timeout=timeout,
                    max_tokens=tokens,
                )
            except Exception as exc:
                return "", exc
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content, last_error
            last_error = EmptyResponseError(f"빈 응답 (max_tokens={tokens} 소진 추정)")
            if tokens >= _MAX_TOKEN_CEILING:
                break
            tokens = min(tokens * 2, _MAX_TOKEN_CEILING)
            log.info("%s: 빈 응답 → max_tokens=%d로 재시도", provider["name"], tokens)
        return "", last_error

    def _chat(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        timeout: float = 30,
        patience: float = 0.0,
    ) -> str | None:
        """프로바이더를 순환하며 응답을 얻는다.

        전부 실패하면 곧바로 포기하지 않고, ``patience`` 초 안에서 쿨다운이
        풀리는 프로바이더를 기다렸다가 다시 시도한다. 이게 없으면 한도 소진
        순간의 영상들이 조용히 basic 요약(=내용 없음)으로 대체된다.
        """
        if not self.clients:
            return None
        deadline = time.time() + max(0.0, patience)
        while True:
            for provider in self._usable():
                content, error = self._call_provider(
                    provider, prompt, temperature, max_tokens, timeout
                )
                if content:
                    self._mark_ok(provider["name"])
                    return content
                self._mark_failure(provider["name"], error)

            remaining = deadline - time.time()
            if remaining <= 0:
                return None
            wait = min(self._next_wait(), remaining)
            log.info("LLM 프로바이더 전부 사용 불가 → %.1fs 대기 후 재시도", wait)
            time.sleep(wait)

    @staticmethod
    def _extract_json(content: str) -> dict | None:
        """LLM 응답에서 JSON 추출. 코드펜스/직접파싱/균형괄호 순으로 시도."""
        if not content:
            return None
        text = content.strip()
        # 1) ```json ... ``` 코드펜스 우선
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
        if fence:
            try:
                parsed = json.loads(fence.group(1).strip())
                if isinstance(parsed, dict) and "thesis" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        # 2) 전체가 JSON인 경우
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        # 3) 균형괄호 스캔: 모든 { ... } 후보 수집 후 스키마 점수 최고점 반환
        #    (기존 탐욕적 r"\{[\s\S]*\}" 는 프롬프트 예시까지 통째로 잡아 실패 유발)
        expected = {
            "thesis", "key_points", "sectors", "stocks",
            "strategy_short", "strategy_long", "risks", "sentiment", "confidence",
        }
        best: dict | None = None
        best_score = -1
        for i, ch in enumerate(text):
            if ch != "{":
                continue
            depth = 0
            in_str = False
            esc = False
            for j in range(i, len(text)):
                c = text[j]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                elif c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            parsed = json.loads(text[i : j + 1])
                        except json.JSONDecodeError:
                            break  # 이 시작점에선 불가 → 다음 '{' 시도
                        if isinstance(parsed, dict) and "thesis" in parsed:
                            score = len(expected & set(parsed.keys()))
                            if score > best_score:
                                best, best_score = parsed, score
                        break
        return best

    # -- 영상 1개 요약 -------------------------------------------------

    def summarize_video(self, title: str, url: str, text: str, channel_name: str) -> VideoSummary:
        """영상 1개의 투자 관점 요약. 실패 시 basic 요약 반환."""
        body = condense_text(text or "")[:6000]
        if not body:
            log.info("빈 내용 → LLM 호출 없이 basic 요약: %s", title)
            return self._basic_summary(title, url, text, channel_name)
        if not self.available:
            return self._basic_summary(title, url, text, channel_name)
        prompt = f"""당신은 한국 주식/투자 전문 애널리스트입니다. 아래 유튜브 영상의 투자 관련 내용을 분석해주세요.

[채널] {channel_name}
[제목] {title}
[내용 (설명+자막 일부)]
{body}

다음 JSON 스키마로만 응답해주세요:
{{
    "thesis": "영상의 핵심 투자 주장 1-2문장",
    "key_points": ["핵심 포인트1", "핵심 포인트2", "핵심 포인트3"],
    "sectors": ["언급된 섹터1", "언급된 섹터2"],
    "stocks": ["언급된 종목1", "언급된 종목2"],
    "strategy_short": "단기 전략 1문장",
    "strategy_long": "중장기 전략 1문장",
    "risks": ["리스크1", "리스크2"],
    "sentiment": "bullish/bearish/neutral 중 하나",
    "confidence": 0.0-1.0 숫자,
    "relevant": true
}}

relevant: 영상 내용이 투자·경제와 관련이 있으면 true, 전혀 무관하면(예: 연예, 예능, 브이로그) false."""
        content = self._chat(prompt, patience=30.0)
        if content:
            result = self._extract_json(content)
            if result:
                result.setdefault("title", title)
                result.setdefault("url", url)
                result.setdefault("channel", channel_name)
                result.setdefault("published_at", "")
                return result
            log.warning("LLM 응답 JSON 파싱 실패 → basic 대체: %s", title)
        else:
            log.warning("LLM 요약 실패(프로바이더 한도 소진) → basic 대체: %s", title)
        return self._basic_summary(title, url, text, channel_name)

    def _basic_summary(self, title: str, url: str, text: str, channel_name: str) -> VideoSummary:
        return {
            "title": title,
            "url": url,
            "channel": channel_name,
            "published_at": "",
            "thesis": f"(LLM 미사용) {title}",
            "key_points": [text[:200]] if text and text.strip() else [],
            "sectors": [],
            "stocks": [],
            "strategy_short": "",
            "strategy_long": "",
            "risks": [],
            "sentiment": "neutral",
            "confidence": 0.0,
            "relevant": True,
        }

    # -- 종합 전략 -----------------------------------------------------

    def synthesize_strategy(self, per_video: list[VideoSummary]) -> str:
        """전체 영상 요약을 종합 투자 전략 마크다운으로 통합."""
        if not self.available:
            return ""
        # 자막이 없어 내용이 빈 basic 요약은 종합에서 제외 (채널 편향 방지).
        # 전부 basic이면 제목만으로 추측하지 않고 종합을 생략한다.
        def _confidence(summary: dict) -> float:
            try:
                return float(summary.get("confidence") or 0)
            except (TypeError, ValueError):
                return 0.0

        substantive = [
            s for s in per_video
            if _confidence(s) > 0 or s.get("sectors") or s.get("stocks")
        ]
        skipped = len(per_video) - len(substantive)
        if not substantive:
            log.warning("실질 요약 없음(자막 없는 영상 %d개) → 종합 전략 생략", len(per_video))
            return ""
        if skipped:
            log.info("자막 없는 basic 요약 %d개는 종합에서 제외", skipped)
        brief = "\n".join(
            f"- [{s.get('channel')}] {s.get('title')}\n"
            f"  주장: {str(s.get('thesis') or '')[:300]}\n"
            f"  섹터: {', '.join((s.get('sectors') or [])[:8])} / 종목: {', '.join((s.get('stocks') or [])[:8])}\n"
            f"  시각: {s.get('sentiment')} / 단기: {str(s.get('strategy_short') or '')[:200]} / 중장기: {str(s.get('strategy_long') or '')[:200]}\n"
            f"  리스크: {', '.join((s.get('risks') or [])[:5])}"
            for s in substantive
        )
        prompt = f"""당신은 한국 투자 전문 애널리스트입니다. 아래는 3개 투자 유튜브 채널의 최근 영상 요약입니다.
이를 종합하여 '투자 전략 문서'를 마크다운으로 작성해주세요.

[영상 요약]
{brief}

다음 구조로 작성해주세요:
## 1. 종합 요약 (3줄)
## 2. 공통 테마 (채널들이 공통으로 강조한 것)
## 3. 시각 차이 (채널 간 의견이 갈린 부분)
## 4. 섹터별 정리
## 5. 종합 투자 전략 (공격형/중립형/보수형으로 구분)
## 6. 리스크 및 유의사항

작성 규칙:
- 세 채널의 시각을 균형 있게 반영하고, 특정 채널 1곳에 편중되지 마세요.
- 섹터별 정리에는 요약에 등장한 모든 채널의 섹터·종목을 빠짐없이 포함하세요.
- 각 주장 뒤에는 근거가 된 채널명을 괄호로 표기해주세요.
- 요약에 없는 내용은 추측으로 보충하지 마세요. 과장된 수익 보장 표현은 피하고 객관적으로 작성해주세요.
마지막에 '본 문서는 정보 제공용이며 투자 권유가 아닙니다.' 문구를 포함해주세요."""
        return self._chat(prompt, temperature=0.4, max_tokens=2000, timeout=90, patience=20.0) or ""
