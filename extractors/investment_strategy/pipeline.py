"""3개 채널 최근 영상 → 투자 전략 문서 파이프라인. youtube_toolkit 재사용."""
from __future__ import annotations

import glob
import json
import logging
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from dotenv import load_dotenv

from config import CHANNELS, DEFAULT_OUTPUT_DIR, DEFAULT_WORKERS, FALLBACK_ENV_PATHS, MAX_CHARS_PER_VIDEO, TRANSCRIPT_MIN_CHARS, ChannelData, ChannelInfo, VideoSummary
from llm import InvestmentLLM, condense_text
from report import StrategyReport

log = logging.getLogger(__name__)

# -- 캐시 및 날짜 필터 상수 -------------------------------------------------
CACHE_FILE = "analyzed_cache.json"
DAYS_BACK = 7  # 오늘부터 7일 전까지 분석 (요청: 오늘 부터 7일 전까지)


def _load_env() -> None:
    for path in FALLBACK_ENV_PATHS:
        full = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        if os.path.exists(full):
            load_dotenv(full, override=False)
            log.info("env 로드: %s", full)


def _load_cache(output_dir: str) -> dict[str, str]:
    """이미 분석된 비디오 ID → published_at 매핑 로드."""
    cache_path = os.path.join(output_dir, CACHE_FILE)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            log.warning("캐시 로드 실패: %s", exc)
    return {}


def _save_cache(output_dir: str, cache: dict[str, str]) -> None:
    """분석된 비디오 ID → published_at 매핑 캐시 저장."""
    cache_path = os.path.join(output_dir, CACHE_FILE)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.warning("캐시 저장 실패: %s", exc)


def _save_analysis_json(
    output_dir: str,
    report_path: str,
    channels_data: list[ChannelData],
    strategy_html: str,
) -> str:
    """리포트와 같은 타임스탬프의 구조화 JSON을 저장 (뷰어용)."""
    base = os.path.splitext(os.path.basename(report_path))[0]
    m = re.search(r"(\d{8}_\d{6})", base)
    stamp = m.group(1) if m else datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"analysis_{stamp}.json")
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "strategy_html": strategy_html,
        "channels": [
            {
                "name": c["name"],
                "handle": c.get("handle", ""),
                "url": c["url"],
                "videos": c.get("videos", []),
            }
            for c in channels_data
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def _video_key(summary: dict) -> str:
    """중복 제거용 영상 키 (YouTube video id 우선, 없으면 URL/영상 id).

    채널명과 무관하게 같은 영상이면 같은 키로 취급한다.
    """
    url = summary.get("url", summary.get("video_url", ""))
    match = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else (url or summary.get("video_id", ""))


def _load_previous_videos(output_dir: str) -> dict[str, VideoSummary]:
    """analysis_*.json 전체에서 영상 요약을 전역 키 기준 하나로 로드.

    같은 영상이 여러 리포트에 있어도 키 충돌 시 최신 published_at 기준으로 유지한다.
    """
    previous: dict[str, VideoSummary] = {}
    for path in glob.glob(os.path.join(output_dir, "analysis_*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            log.warning("이전 분석 데이터 로드 실패 (%s): %s", path, exc)
            continue
        for channel in data.get("channels", []):
            for video in channel.get("videos", []):
                key = _video_key(video)
                if not key:
                    continue
                video.setdefault("channel", channel.get("name", ""))
                existing = previous.get(key)
                if existing is None:
                    previous[key] = video
                else:
                    existing_at = existing.get("published_at", "")
                    new_at = video.get("published_at", "")
                    if new_at and (not existing_at or new_at > existing_at):
                        previous[key] = video
    return previous


def _is_recent(published_at: str, days: int = DAYS_BACK) -> bool:
    """published_at이 최근 N일 이내인지 확인."""
    if not published_at:
        return False
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        cutoff = datetime.now(dt.tzinfo) - timedelta(days=days)
        return dt >= cutoff
    except (ValueError, AttributeError):
        return False


class InvestmentPipeline:
    def __init__(
        self,
        videos_per_channel: int = 5,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        max_workers: int = DEFAULT_WORKERS,
    ) -> None:
        _load_env()
        from youtube_toolkit import YoutubeAnalyzer  # env 로드 후 import

        self.videos_per_channel = videos_per_channel
        self.list_limit = videos_per_channel * 2  # 캐시·날짜 필터 후 부족분 보충용
        self.max_workers = max(1, max_workers)
        self.analyzer = YoutubeAnalyzer()
        self.llm = InvestmentLLM(order=["freellmapi"])
        self.reporter = StrategyReport(output_dir=output_dir)
        self._cache = _load_cache(output_dir)
        self._stats_lock = threading.Lock()
        self._stats: dict[str, int] = {}

    def _list_channel_videos(self, handle: str) -> list[str]:
        """채널 업로드 플레이리스트에서 최신 영상 ID를 가져온다.

        YouTube API가 최신 업로드를 안정적으로 제공하도록 안내하는 경로이며,
        검색 색인 지연과 search.list의 별도 호출 한도를 피한다.
        """
        try:
            video_ids = self.analyzer.channels.list_uploads_video_ids(
                handle, max_results=self.list_limit
            )
            if video_ids:
                return video_ids
            log.info("%s: uploads 목록 비어있음 → search API 폴백", handle)
        except Exception as exc:
            log.warning("%s: uploads 조회 실패(%s) → search API 폴백", handle, exc)
        return self.analyzer.channels.list_recent_video_ids(
            handle, max_results=self.list_limit
        )

    def _list_or_log(self, channel: ChannelInfo) -> list[str]:
        log.info("[%s] 최신 영상 %d개 조회 중...", channel["name"], self.videos_per_channel)
        try:
            return self._list_channel_videos(channel["handle"])
        except Exception as exc:
            log.error("[%s] 조회 실패: %s", channel["name"], exc)
            return []

    def _bump(self, key: str) -> None:
        with self._stats_lock:
            self._stats[key] = self._stats.get(key, 0) + 1

    def _process_video(self, channel: ChannelInfo, video_id: str) -> VideoSummary | None:
        """영상 1개: 수집 → 요약. 워커 스레드에서 실행된다."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        log.info("[%s] %s 분석 중...", channel["name"], video_id)
        try:
            # transcript fetch 비활성화로 1.5s·429 회피 (설명 부족 시 아래에서 보강)
            content = self.analyzer.analyze(video_id, include_transcript=False)
        except Exception as exc:
            log.error("[%s] %s 분석 실패: %s", channel["name"], video_id, exc)
            self._bump("failed")
            return None

        title = content.metadata.title or video_id
        published_at = content.metadata.published_at or ""
        log.info("[%s] %s - 제목: %s", channel["name"], video_id, title)
        log.info("[%s] %s - 날짜: %s", channel["name"], video_id, published_at)

        # 기간 밖 영상은 LLM 호출 없이 스킵
        if not _is_recent(published_at):
            log.info(
                "[%s] %s - 게시일 %s, 최근 %d일 범위 밖 → LLM 생략",
                channel["name"], video_id, published_at or "없음", DAYS_BACK,
            )
            self._bump("skipped_stale")
            return None

        # 설명이 빈약하면 자막을 추가로 가져와 요약 품질 보강
        combined = condense_text((content.combined_text or "").strip())
        if len(combined) < TRANSCRIPT_MIN_CHARS:
            transcript_text = self.analyzer.get_transcript(video_id) or ""
            if transcript_text:
                combined = condense_text(
                    f"{content.combined_text or ''}\n{transcript_text}"
                )
                log.info("[%s] %s - 설명 부족 → 자막 보강 (%d자)", channel["name"], video_id, len(combined))
            else:
                log.warning("(%s) %s: 자막+설명 비어있음 → basic 요약", channel["name"], video_id)

        summary = self.llm.summarize_video(
            title=title,
            url=url,
            text=combined[:MAX_CHARS_PER_VIDEO],
            channel_name=channel["name"],
        )
        summary["published_at"] = published_at

        # LLM이 투자 무관으로 판정한 영상은 제외
        if summary.get("relevant") is False:
            log.info("[%s] %s - 투자 무관 판정 → 제외: %s", channel["name"], video_id, title)
            self._bump("skipped_irrelevant")
            return None
        self._bump("analyzed")
        return summary

    def run(self, channels: list[ChannelInfo] | None = None) -> dict:
        channels = channels or CHANNELS
        self._stats = {}
        all_summaries: list[VideoSummary] = []
        channels_data: list[ChannelData] = []

        # 1) 채널별 최신 영상 목록 (채널 단위 병렬)
        listings: dict[str, list[str]] = {}
        if self.max_workers <= 1 or len(channels) == 1:
            for channel in channels:
                listings[channel["name"]] = self._list_or_log(channel)
        else:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(channels))) as executor:
                futures = {executor.submit(self._list_or_log, ch): ch for ch in channels}
                for future in as_completed(futures):
                    channel = futures[future]
                    listings[channel["name"]] = future.result()

        # 2) 최근 N일 이내이며 아직 분석되지 않은 영상만 필터링
        filtered_ids: dict[str, list[str]] = {}  # channel_name -> [video_id, ...]
        for channel_name, video_ids in listings.items():
            recent_and_new: list[str] = []
            for vid in video_ids:
                # 캐시에 이미 분석된 경우 제외 (영상 키로 비교)
                if _video_key({"url": f"https://www.youtube.com/watch?v={vid}"} if not vid.startswith("http") else {"url": vid}) in self._cache:
                    continue
                recent_and_new.append(vid)
            # 최신순 정렬 상태이므로 채널당 요청 개수까지만 분석 (나머지는 기간 밖이거나 캐시됨)
            if recent_and_new:
                filtered_ids[channel_name] = recent_and_new[: self.videos_per_channel]
            log.info(
                "[%s] 전체 %d개 중 캐시 제외 후 %d개 분석 대상",
                channel_name,
                len(video_ids),
                len(recent_and_new),
            )

        # 3) 영상 작업을 채널 경계 없이 한 풀에 넣어 병렬 처리
        jobs: list[tuple[ChannelInfo, str]] = []
        for channel in channels:
            video_ids = filtered_ids.get(channel["name"]) or []
            if not video_ids:
                continue
            log.info("[%s] %d개 발견, 분석 중...", channel["name"], len(video_ids))
            jobs.extend((channel, video_id) for video_id in video_ids)

        summaries_by_channel: dict[str, list[tuple[int, VideoSummary]]] = {
            channel["name"]: [] for channel in channels
        }
        if self.max_workers <= 1 or len(jobs) <= 1:
            for index, (channel, video_id) in enumerate(jobs):
                summary = self._process_video(channel, video_id)
                if summary is not None:
                    summaries_by_channel[channel["name"]].append((index, summary))
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._process_video, channel, video_id): (index, channel["name"])
                    for index, (channel, video_id) in enumerate(jobs)
                }
                for future in as_completed(futures):
                    index, channel_name = futures[future]
                    try:
                        summary = future.result()
                    except Exception as exc:
                        log.error("[%s] 영상 처리 실패: %s", channel_name, exc)
                        continue
                    if summary is not None:
                        summaries_by_channel[channel_name].append((index, summary))

        # 3) 채널 순서 유지 + 게시일 내림차순 정렬 후 요청 개수만 유지
        for channel in channels:
            ordered = [
                summary
                for _, summary in sorted(
                    summaries_by_channel.get(channel["name"], []), key=lambda item: item[0]
                )
            ]
            ordered.sort(key=lambda x: x.get("published_at", ""), reverse=True)
            ordered = ordered[: self.videos_per_channel]
            channels_data.append({**channel, "videos": ordered})
            all_summaries.extend(ordered)

        # --- 캐시 업데이트: 실제 분석 완료한 영상만 반영 ---
        now_cache = dict(self._cache)
        for summary in all_summaries:
            key = _video_key(summary)
            published = summary.get("published_at")
            if key and published:
                now_cache[key] = published
        self._cache = now_cache
        _save_cache(output_dir=self.reporter.output_dir, cache=self._cache)
        # -------------------------------------------------------

        # 분석 이력 재사용 없음: 이미 분석된 영상은 스킵하므로 이전 분석 데이터는 병합하지 않는다.
        # 최근 DAYS_BACK일 이내이면서 이번 실행에서 새로 분석된 영상만 리포트에 사용한다.
        all_summaries = [
            s for s in all_summaries
            if _is_recent(s.get("published_at", ""), DAYS_BACK)
        ]

        if not all_summaries:
            # all videos already in cache or outside date range - inform user
            if self._cache:
                log.info("이미 분석된 영상이 전부 캐시에 존재하거나 날짜 범위를 벗어났습니다. (캐시된 영상 수: %d)", len(self._cache))
            else:
                raise RuntimeError("설정된 채널에서 분석할 영상을 가져오지 못해 리포트를 생성하지 않았습니다.")
            return {
                "channels": len(channels_data),
                "videos_analyzed": 0,
                "fallback_summaries": 0,
                "llm_used": self.llm.available,
                "report_path": "",
                "stats": dict(self._stats),
            }

        fallback = sum(
            1 for s in all_summaries
            if str(s.get("thesis", "")).startswith("(LLM 미사용)")
        )
        if fallback:
            log.warning(
                "%d/%d 영상이 LLM 요약 없이 basic으로 대체되었습니다 (자막 없음 또는 프로바이더 한도).",
                fallback,
                len(all_summaries),
            )

        log.info("종합 투자 전략 생성 중...")
        strategy_md = self.llm.synthesize_strategy(all_summaries) if all_summaries else ""
        report_path = self.reporter.generate(channels_data, strategy_md)
        log.info("리포트 생성: %s", report_path)
        strategy_html = self.reporter.md.convert(strategy_md) if strategy_md else ""
        analysis_path = _save_analysis_json(
            self.reporter.output_dir, report_path, channels_data, strategy_html
        )
        log.info("분석 데이터 저장: %s", analysis_path)

        # 뷰어 자동 갱신 (실패해도 리포트 생성에는 영향 없음)
        try:
            from build_viewer import build as build_viewer
            viewer_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "viewer.html"
            )
            build_viewer(
                os.path.abspath(self.reporter.output_dir), viewer_path
            )
        except Exception as exc:
            log.warning("뷰어 갱신 실패: %s", exc)

        # 채널별 개별 HTML 리포트 생성
        m = re.search(r"(\d{8}_\d{6})", os.path.basename(report_path))
        stamp = m.group(1) if m else datetime.now().strftime("%Y%m%d_%H%M%S")
        for channel_data in channels_data:
            channel_report = self.reporter.generate(
                [channel_data], "", filename=f"{channel_data['name']}_{stamp}"
            )
            log.info("채널 리포트 생성: %s", channel_report)
        stats = dict(self._stats)
        log.info("영상 처리 통계: %s", stats)
        return {
            "channels": len(channels_data),
            "videos_analyzed": len(all_summaries),
            "fallback_summaries": fallback,
            "llm_used": self.llm.available,
            "report_path": report_path,
            "stats": stats,
        }