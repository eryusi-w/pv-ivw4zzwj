"""YouTube 기반 업무·생산성 팁 영상 수집기."""
from __future__ import annotations

import logging
import os
import re
import sys
from typing import Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
PROJECTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PROJECT_ROOT)))
CODEX_HOME = os.path.dirname(PROJECTS_DIR)

if PROJECTS_DIR not in sys.path:
    sys.path.insert(0, PROJECTS_DIR)
if CODEX_HOME not in sys.path:
    sys.path.insert(0, CODEX_HOME)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import CHANNELS, ChannelInfo

log = logging.getLogger(__name__)


class YouTubeCollector:
    """생산성 채널 최신 영상 수집."""

    def __init__(self) -> None:
        self.analyzer = None
        try:
            from youtube_toolkit import YoutubeAnalyzer

            self.analyzer = YoutubeAnalyzer()
        except Exception as e:
            log.warning("youtube_toolkit 로드 실패 (수동 큐레이션 및 검색 폴백 사용): %s", e)

    def collect_from_channel(self, channel: ChannelInfo, limit: int = 3) -> list[dict[str, Any]]:
        """특정 채널에서 최신 영상 메타데이터 수집."""
        results: list[dict[str, Any]] = []
        if not self.analyzer:
            return results

        handle = channel["handle"]
        try:
            video_ids = self.analyzer.channels.list_uploads_video_ids(handle, max_results=limit)
            if not video_ids:
                video_ids = self.analyzer.channels.list_recent_video_ids(handle, max_results=limit)

            for vid in video_ids[:limit]:
                try:
                    content = self.analyzer.analyze(vid, include_transcript=False)
                    desc = getattr(content, "description", "") or ""
                    title = getattr(content, "title", "") or ""
                    published_at = getattr(content, "published_at", "") or ""
                    results.append({
                        "video_id": vid,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "description": desc,
                        "channel_name": channel["name"],
                        "category": channel.get("category", "업무생산성"),
                        "published_at": published_at,
                    })
                except Exception as ex:
                    log.warning("[%s] 영상 %s 분석 실패: %s", channel["name"], vid, ex)
        except Exception as e:
            log.warning("[%s] 채널 목록 조회 실패: %s", channel["name"], e)

        return results

    def collect_all_channels(self, limit_per_channel: int = 3) -> list[dict[str, Any]]:
        """설정된 모든 생산성 채널에서 최신 영상 수집."""
        all_videos: list[dict[str, Any]] = []
        for ch in CHANNELS:
            vids = self.collect_from_channel(ch, limit=limit_per_channel)
            all_videos.extend(vids)
        return all_videos
