"""호환 심(shim): 기존 DataCollector API를 youtube_toolkit 위임으로 유지.

실제 수집 로직은 D:\\dev\\codex-home\\projects\\youtube_toolkit 에 있으며,
이 클래스는 동일 시그니처를 그대로 노출하는 얇은 래퍼다.
신규 코드는 `from youtube_toolkit import YoutubeAnalyzer` 를 직접 사용할 것.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

# youtube_toolkit(D:\dev\codex-home\projects\youtube_toolkit)을 import 경로에 추가.
# 이 파일은 .../github_awesome_extractor/modules/ 에 있으므로 두 단계 위가 부모다.
# 패키지로 설치되지 않은 복사형 모듈이므로 필요.
_TOOLKIT_PARENT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
if _TOOLKIT_PARENT not in sys.path:
    sys.path.insert(0, _TOOLKIT_PARENT)

from youtube_toolkit import YoutubeAnalyzer, YoutubeConfig  # noqa: E402


class DataCollector:
    """youtube_toolkit.YoutubeAnalyzer 기반 호환 래퍼."""

    def __init__(self, api_key: Optional[str] = None, **config_overrides):
        self.analyzer = YoutubeAnalyzer(
            YoutubeConfig(api_key=api_key, **config_overrides)
            if (api_key or config_overrides) else None
        )

    def get_video_transcript(self, video_id: str, languages: list[str] | None = None) -> Optional[str]:
        """자막 텍스트 반환 (없으면 None). URL 입력도 가능."""
        if languages is not None:
            analyzer = YoutubeAnalyzer(YoutubeConfig(languages=tuple(languages)))
            return analyzer.get_transcript(video_id)
        return self.analyzer.get_transcript(video_id)

    def get_video_metadata(self, video_id: str) -> dict:
        """영상 메타데이터 dict 반환. URL 입력도 가능."""
        return self.analyzer.get_metadata(video_id)

    def parse_video_metadata(self, video_data: dict) -> dict:
        """구버전 호환: YouTube API 원시 응답 -> 메타데이터 dict."""
        snippet = video_data.get("snippet", {})
        video_id = video_data.get("id", "")
        if isinstance(video_id, dict):
            video_id = video_id.get("videoId", "")
        return {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }

    def get_combined_text(self, video_id: str) -> tuple[str, dict]:
        """설명 + 자막 결합 텍스트와 메타데이터 dict 반환. URL 입력도 가능."""
        return self.analyzer.get_combined_text(video_id)
