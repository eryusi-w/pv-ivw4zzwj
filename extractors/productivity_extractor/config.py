"""블로그 트래픽 확장용 4대 카테고리 자동화 수집기 설정."""
from __future__ import annotations

from typing import TypedDict


class ChannelInfo(TypedDict):
    name: str
    handle: str
    url: str
    main_category: str


class ContentItem(TypedDict):
    id: str
    title: str
    url: str
    source_name: str
    main_category: str  # 업무·생산성, 생활금융·세테크, 모바일·디지털생활, 1인비즈니스·부업
    sub_category: str   # 세부 태그 (엑셀, 절세, 갤럭시, 숏폼 등)
    published_at: str
    target_audience: str
    summary: str
    core_features: list[str]
    step_by_step: list[str]
    practical_prompt_or_tips: str
    recommendation_reason: str
    keywords: list[str]
    blog_title_candidate: str


# 4대 카테고리 정의
MAIN_CATEGORIES = [
    "업무·생산성",
    "생활금융·세테크",
    "모바일·디지털생활",
    "1인비즈니스·부업",
]

# 카테고리별 큐레이션 채널
CHANNELS: list[ChannelInfo] = [
    # 1. 업무·생산성
    {"name": "오빠두엑셀", "handle": "@oppadu", "url": "https://www.youtube.com/@oppadu", "main_category": "업무·생산성"},
    {"name": "일잘러 장피엠", "handle": "@changpm", "url": "https://www.youtube.com/@changpm", "main_category": "업무·생산성"},
    
    # 2. 생활금융·세테크
    {"name": "1분미만(생활팁)", "handle": "@1min", "url": "https://www.youtube.com/@1min", "main_category": "생활금융·세테크"},
    {"name": "절세TV", "handle": "@tax_tv", "url": "https://www.youtube.com/@tax_tv", "main_category": "생활금융·세테크"},

    # 3. 모바일·디지털생활
    {"name": "디에디트", "handle": "@theedit", "url": "https://www.youtube.com/@theedit", "main_category": "모바일·디지털생활"},
    {"name": "주연 ZUYONI", "handle": "@zuyoni", "url": "https://www.youtube.com/@zuyoni", "main_category": "모바일·디지털생활"},

    # 4. 1인비즈니스·부업
    {"name": "노마드코더", "handle": "@nomadcoders", "url": "https://www.youtube.com/@nomadcoders", "main_category": "1인비즈니스·부업"},
]

# 분석 산출물은 naver-blog 의 sources/ 로 모은다(2026-11-15 이동).
DEFAULT_OUTPUT_DIR = r"D:\dev\codex-home\projects\naver-blog\sources\productivity_extractor"
DEFAULT_VIDEOS_PER_CHANNEL = 2
DEFAULT_WORKERS = 4
MAX_CHARS_PER_ITEM = 3000

FALLBACK_ENV_PATHS = [
    ".env",
    "../github_awesome_extractor/.env",
    "../investment_strategy/.env",
]
