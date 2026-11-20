# GitHub Awesome AI Tool Extractor Configuration

# YouTube Channel Settings
YOUTUBE_CHANNEL_HANDLES = [
    "@ManuAGI",
    "@GithubAwesome",
    "@AIstackengineer",
    "@Mindung-EasyAI",
    "@honjobs",
    "@Solostack-1",
    "@TheLayperson",
    "@CodingArtisan",
]

# GitHub API Settings
GITHUB_TOKEN = ""  # Set via environment variable GITHUB_TOKEN

# OpenAI Settings  
OPENAI_API_KEY = ""  # Set via environment variable OPENAI_API_KEY
OPENAI_MODEL = "gpt-4o"

# Output Settings
OUTPUT_DIR = "output"
REPORT_FORMAT = "markdown"  # markdown or html

# Agent prompts (moved from repo-root agents/ — see agents/AGENTS.md,
# agents/daily-digest-prompt.md)
import os
AGENT_PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents")
WEEKLY_DIGEST_PROMPT = os.path.join(AGENT_PROMPT_DIR, "AGENTS.md")
DAILY_DIGEST_PROMPT = os.path.join(AGENT_PROMPT_DIR, "daily-digest-prompt.md")

# Daily/Weekly digest integration (criteria from agents/*.md)
# Filter: Star 100+ 또는 최근 급성장, 1회 최대 5개, ai 정보_도구.md 중복 금지
DIGEST_MIN_STARS = 100
DIGEST_MAX_PER_RUN = 5
DIGEST_TARGET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
    "digest",
    "ai 정보_도구.md",
)
DIGEST_KEYWORDS = ["AI agent", "coding tool", "MCP", "open source"]

# Category placement rules (agents/AGENTS.md Step 4)
# Section 1: CLI 에이전트, 코드 인텔리전스, MCP
# Section 2: 메모리, 오케스트레이션, SDLC, 워크플로우
# Section 3: 배포/인프라/모니터링 (digest 범위 외 — daily는 1/2만)
DIGEST_CATEGORIES = {
    1: "AI 코딩 에이전트 & 터미널/문서 보조 도구",
    2: "AI 워크플로우, 에이전트 메모리 및 오케스트레이션",
    3: "고성능 개발 인프라, 모니터링",
}
DIGEST_DAILY_SECTIONS = (1, 2)

# Performance Settings
PERFORMANCE = {
    "max_workers": 8,  # 병렬 작업자 수
    "cache_enabled": True,  # 캐싱 활성화
    "cache_size": 100,  # 캐시 크기
    "progress_bar": True,  # 진행률 표시
    "timeout_github": 15,  # GitHub API 타임아웃 (초)
    "timeout_llm": 20,  # LLM 타임아웃 (초)
    "batch_llm": False,  # LLM 배치 처리 (추후 구현)
    "max_repos_per_run": 20,  # 한 번에 처리할 최대 리포지토리 수
}