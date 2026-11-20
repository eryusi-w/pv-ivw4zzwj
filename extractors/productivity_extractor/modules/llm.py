"""4대 카테고리 통합 LLM 분석기. shared/ai_providers 경유."""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
CODEX_HOME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(PROJECT_DIR))))
if CODEX_HOME not in sys.path:
    sys.path.insert(0, CODEX_HOME)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config import ContentItem, FALLBACK_ENV_PATHS

# .env 로드
try:
    from dotenv import load_dotenv

    for env_path in FALLBACK_ENV_PATHS:
        full_path = os.path.normpath(os.path.join(CURRENT_DIR, env_path))
        if os.path.isfile(full_path):
            load_dotenv(full_path, override=False)
except ImportError:
    pass

from shared.ai_providers import build_clients

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 네이버 블로그 검색 유입을 극대화하는 IT/재테크/생산성 전문 테크 블로거입니다.
주어진 정보(주제, 카테고리, 설명)를 분석하여 독자의 클릭을 유도하고 체류 시간을 늘릴 수 있는 고품질 블로그 원고 재료로 가공하세요.

반드시 유효한 단일 JSON 객체로만 응답하세요. 마크다운 백틱 없이 JSON 문자열만 출력하세요.

JSON 구조:
{
  "title_ko": "네이버 검색 상위 노출 및 클릭을 부르는 문제해결형 제목 (예: 해외주식 양도세 250만원 넘었을 때 합법적으로 0원 만드는 법)",
  "target_audience": "이 글을 반드시 읽어야 하는 타겟 독자 (예: 올해 미국 주식 수익이 250만원을 초과한 직장인)",
  "summary": "독자의 흥미를 끄는 핵심 효용 1~2문장 요약",
  "sub_category": "세부 키워드/분류 (예: 절세/세금, 엑셀/데이터, 아이폰설정, 숏폼제작)",
  "core_features": [
    "핵심 실무 특징/장점 1",
    "핵심 실무 특징/장점 2",
    "핵심 실무 특징/장점 3"
  ],
  "step_by_step": [
    "1단계: 사전 준비 및 확인",
    "2단계: 핵심 실행 및 설정 방법",
    "3단계: 실무 적용 및 최종 확인"
  ],
  "practical_prompt_or_tips": "독자가 복사해서 바로 쓰는 프롬프트, 엑셀 수식, 스마트폰 설정 경로, 또는 절세 계산 공식",
  "recommendation_reason": "네이버 블로그 독자에게 강력 추천하는 이유",
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7", "키워드8", "키워드9", "키워드10"]
}
"""


class ContentLLM:
    """4대 카테고리 콘텐츠 분석 LLM."""

    def __init__(self, order: list[str] | None = None) -> None:
        try:
            self.clients: list[dict] = build_clients(order=order)
        except Exception as e:
            log.warning("LLM 클라이언트 생성 실패: %s. 기본 모드로 동작합니다.", e)
            self.clients = []

    @property
    def available(self) -> bool:
        return bool(self.clients)

    def analyze_item(
        self,
        title: str,
        text: str,
        source_name: str = "",
        main_category: str = "업무·생산성",
        sub_category: str = "일반",
        url: str = "",
        published_at: str = "",
    ) -> ContentItem:
        """아이템을 분석하여 ContentItem 구조로 반환."""
        cleaned_text = self._clean_text(text)[:3000]

        if not self.available:
            return self._basic_fallback(title, source_name, main_category, sub_category, url, published_at)

        prompt = f"""[분석 대상]
- 카테고리: {main_category} > {sub_category}
- 제목: {title}
- 출처: {source_name}
- 본문 요약:
{cleaned_text}

위 내용을 바탕으로 네이버 검색 유입용 블로그 재료 JSON을 작성하세요."""

        for provider in self.clients:
            client = provider["client"]
            model = provider["model"]
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                )
                raw_content = resp.choices[0].message.content or ""
                parsed = self._parse_json(raw_content)
                if parsed:
                    return {
                        "id": re.sub(r"[^a-zA-Z0-9_-]", "", url.split("v=")[-1] if "v=" in url else title)[:30],
                        "title": title,
                        "url": url,
                        "source_name": source_name,
                        "main_category": main_category,
                        "sub_category": parsed.get("sub_category", sub_category),
                        "published_at": published_at,
                        "target_audience": parsed.get("target_audience", "실무자 및 직장인"),
                        "summary": parsed.get("summary", title),
                        "core_features": parsed.get("core_features", ["실무 적용성", "시간/비용 절감", "쉬운 실행"]),
                        "step_by_step": parsed.get("step_by_step", ["1단계 시작", "2단계 적용", "3단계 완료"]),
                        "practical_prompt_or_tips": parsed.get("practical_prompt_or_tips", "실무 팁을 확인하세요."),
                        "recommendation_reason": parsed.get("recommendation_reason", "독자에게 유용한 필수 정보입니다."),
                        "keywords": parsed.get("keywords", ["생산성", "직장인팁", "꿀팁", "자동화", "재테크"]),
                        "blog_title_candidate": parsed.get("title_ko", title),
                    }
            except Exception as e:
                log.warning("프로바이더 %s (%s) 호출 실패: %s. 다음 시도", provider.get("name"), model, e)
                continue

        return self._basic_fallback(title, source_name, main_category, sub_category, url, published_at)

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        try:
            cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", raw.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None

    @staticmethod
    def _basic_fallback(
        title: str, source_name: str, main_category: str, sub_category: str, url: str, published_at: str
    ) -> ContentItem:
        return {
            "id": re.sub(r"[^a-zA-Z0-9_-]", "", url.split("v=")[-1] if "v=" in url else title)[:30],
            "title": title,
            "url": url,
            "source_name": source_name,
            "main_category": main_category,
            "sub_category": sub_category,
            "published_at": published_at,
            "target_audience": "실전 정보를 찾는 독자",
            "summary": f"{title}에 관한 핵심 팁 가이드입니다.",
            "core_features": ["빠른 실행", "오류 해결", "비용/시간 절감"],
            "step_by_step": ["1단계: 준비", "2단계: 핵심 실행", "3단계: 결과 확인"],
            "practical_prompt_or_tips": "본문 가이드를 참고하여 단계별로 따라해보세요.",
            "recommendation_reason": "실생활과 업무에서 바로 활용할 수 있는 핵심 정보입니다.",
            "keywords": [main_category, sub_category, "꿀팁", "가이드", "정보"],
            "blog_title_candidate": f"[실전 가이드] {title}",
        }
