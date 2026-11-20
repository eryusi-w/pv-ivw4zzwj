"""투자 전략 프로그램 설정: 분석 대상 채널 + 기본값."""
from __future__ import annotations

from typing import TypedDict


class ChannelInfo(TypedDict):
    name: str
    handle: str
    url: str


class VideoSummary(TypedDict):
    title: str
    url: str
    channel: str
    published_at: str
    thesis: str
    key_points: list[str]
    sectors: list[str]
    stocks: list[str]
    strategy_short: str
    strategy_long: str
    risks: list[str]
    sentiment: str
    confidence: float
    relevant: bool


class ChannelData(TypedDict):
    name: str
    handle: str
    url: str
    videos: list[VideoSummary]

# 요청받은 5개 채널
CHANNELS: list[ChannelInfo] = [
    {"name": "송팀장", "handle": "@Song_Teamjang", "url": "https://www.youtube.com/@Song_Teamjang"},
    {"name": "경제사냥꾼", "handle": "@경제사냥꾼", "url": "https://www.youtube.com/@경제사냥꾼"},
    {"name": "sng_tv", "handle": "@sng_tv", "url": "https://www.youtube.com/@sng_tv"},
    {"name": "테스프레소", "handle": "@테스프레소", "url": "https://www.youtube.com/@%ED%85%8C%EC%8A%A4%ED%94%84%EB%A0%88%EC%86%8C"},
    {"name": "비연세", "handle": "@biyonsei", "url": "https://www.youtube.com/@biyonsei"},
]

DEFAULT_VIDEOS_PER_CHANNEL = 5
# 분석 산출물은 naver-blog 의 sources/ 로 모은다(2026-11-15 이동).
DEFAULT_OUTPUT_DIR = r"D:\dev\codex-home\projects\naver-blog\sources\investment_strategy"

# 영상 수집·요약 병렬 워커 수.
# 높이면 빨라지지만 LLM 무료 등급 TPM(예: groq 8k/min)에서 429가 늘어난다.
DEFAULT_WORKERS = 4

# LLM에 넘길 영상당 최대 텍스트 길이 (자막+설명 결합본 기준)
# 6000 → 3000 로 낮추어 토큰 소진 및 429 위험 감소
MAX_CHARS_PER_VIDEO = 3000

# 설명 텍스트가 이 길이 미만이면 자막을 추가로 가져와 요약 품질 보강
# (youtube-transcript-api는 429에 취약하므로 필요한 영상에만 호출)
TRANSCRIPT_MIN_CHARS = 300

# 기존 github_awesome_extractor/.env 재사용 (키 중복 관리 방지)
FALLBACK_ENV_PATHS = [
    ".env",
    "../github_awesome_extractor/.env",
]
