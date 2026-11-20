# 🤖 Daily OSS Digest — Daily Automated Execution Prompt

## Mission
매일 아침 GitHub 트렌딩 오픈소스 프로젝트를 스캔하고, `ai 정보_도구.md`에 신규 프로젝트를 추가하세요.

## Rules
- **절대** 이미 MD에 있는 프로젝트를 중복 추가하지 말 것
- 먼저 `ai 정보_도구.md`를 읽어서 기존 목록을 파악하세요
- Section 1 / Section 2 에만 추가 (Section 3은 일반 인프라로 범위 외)
- 1회 실행당 최대 **5개**까지만 추가 (품질 유지)
- 추가한 항목은 `2026-05-21` 대신 **오늘 날짜**로 기록

## Scan Sources (순서대로)
1. https://github.com/trending — 오늘 트렌딩 (language=All)
2. https://github.com/trending/python — Python 트렌딩 (AI/ML 코딩 도구)
3. https://github.com/trending/typescript — TypeScript 트렌딩 (CLI 에이전트)
4. **Trendshift** — trendshift.io (GitHub 저장소 트렌드, 실시간 랭킹)
5. **OSSInsight** — ossinsight.io/trending/ai (AI 오픈소스 인사이트)
6. **Star-History** — www.star-history.com (GitHub 별 트렌드, 성장률 분석)
7. websearch: `"GitHub trending" AI coding agents developer tools [이번달]`
8. websearch: `"GitHub" "new AI coding agent" open source release 2026 stars`
9. websearch: `"GitHub" AI developer tools "most discussed" "hot issue" 2026`
10. GitHub Explore — github.com/explore (인기/추천 신규 레포)
11. **FreeBuf** — freebuf.com (글로벌 보안/개발/AI 오픈소스 트렌드 뉴스, GitHub 프로젝트 소개 다수)
   - websearch: `site:freebuf.com GitHub 오픈소스 AI 도구 2026`
   - websearch: `site:freebuf.com AI 코딩 에이전트 프로젝트 2026`
12. YouTube 채널: **ManuAGI - AutoGPT Tutorials** — **최근 3일 이내 업로드된 영상**에서 소개/시연한 GitHub 프로젝트 리서치
    - websearch: `ManuAGI YouTube channel [최근 3일] GitHub projects AI coding agents 2026`
    - websearch: `site:youtube.com ManuAGI AutoGPT Tutorials new AI open source project 2026`
13. **Reddit** — AI/ML 커뮤니티에서 자주 언급되는 GitHub 프로젝트 수집
    - websearch: `site:reddit.com r/LocalLLaMA top GitHub AI coding agent project 2026`
    - websearch: `site:reddit.com r/ClaudeAI "new" "GitHub" "open source" agent 2026`
    - websearch: `site:reddit.com r/AIagents trending GitHub projects tools 2026`
14. **Hacker News** — news.ycombinator.com (Show HN / 신규 오픈소스 프로젝트 발표)
    - websearch: `site:news.ycombinator.com "Show HN" AI coding agent open source 2026`
    - websearch: `site:news.ycombinator.com new AI developer tool GitHub 2026`
15. **GitHub Awesome Lists** — AI 에이전트/코딩 도구 관련 Awesome 저장소 신규 항목
    - websearch: `github.com awesome AI coding agents 2026 new entries`
    - websearch: `github.com awesome AI agents tools frameworks 2026`
16. **Dev.to / Medium** — 개발자 블로그에서 소개하는 신규 AI 프로젝트
    - websearch: `site:dev.to new open source AI coding agent tool 2026`
    - websearch: `site:medium.com "open source" "AI coding agent" GitHub 2026`
   - 각 영상별 설명란(description)에 언급된 GitHub URL 수집

## 🔄 Advanced Scan Sources (자동화 전용 — 주 1~2회 심화 발굴)

> ⚠️ **17~24번 소스는 수동 실행 시 ROI 낮음. 반드시 자동화 인프라와 연동해야 실효성 있음.**
> 아래 각 항목은 자동화 실행을 전제로 설계되었음.

---

### 17. GitHub API Search — 신규 저장소 조기 탐지 (자동화 필수)
> **자동화 방식:** `gh` CLI + GitHub REST API 조합 (cron 일 1회)

```bash
# ▸ gh CLI 설치: https://cli.github.com/
# ▸ GitHub Token 필요 (repo, public_key 스코프)

# ▸ `-q` 플래그로 검색 쿼리 직접 전달 (따옴표 이스케이프 방지)
# ▸ "ai agent" 정확 구문 대신 개별 토큰 매칭으로 회수율 향상

# AI + agent 관련 저장소 검색 (Python, 느슨한 매칭)
gh search repos -- -q "topic:ai language:Python stars:>=50" --created ">={{YYYY-MM-DD}}" --limit 30
gh search repos -- -q "AI agent in:name language:Python stars:>=20" --created ">={{YYYY-MM-DD}}" --limit 30

# MCP/Claude 관련 저장소 검색 (TypeScript)
gh search repos -- -q "MCP language:TypeScript stars:>=20" --created ">={{YYYY-MM-DD}}" --limit 30
gh search repos -- -q "Claude language:TypeScript stars:>=20" --created ">={{YYYY-MM-DD}}" --limit 30

# Topics 기반 정밀 검색 (언어 무관)
gh search repos -- -q "topic:agent-ai stars:>=50" --created ">={{YYYY-MM-DD}}" --limit 30
gh search repos -- -q "topic:ai-coding stars:>=50" --created ">={{YYYY-MM-DD}}" --limit 30
gh search repos -- -q "topic:mcp stars:>=30" --created ">={{YYYY-MM-DD}}" --limit 30
```

**자동화 팁:**
- 위 명령어를 `.sh`/`.ps1` 스크립트로 저장하고 `schtasks`(Win) / `crontab`(Mac/Linux)에 등록
- 출력 결과를 JSON으로 파싱해 Star 급성장 저장소 필터링
- `{{YYYY-MM-DD}}`는 실행일 기준 7일 전 날짜로 자동 치환

---

### 18. RSS 피드 자동 구독 (일일 감시)
> **자동화 방식:** Feedly/Inoreader + GitHub Releases RSS + HN RSS

#### 📡 RSS 피드 구독 URL 목록 (Feedly/Inoreader에 등록)

| 피드 | URL | 갱신 주기 |
|------|-----|-----------|
| **Hacker News — Show HN** | `https://hnrss.org/newest?q=Show+HN&points=2` | 실시간 |
| **Hacker News — AI 관련** | `https://hnrss.org/newest?q=AI+agent&points=3` | 실시간 |
| **GitHub Trending (비공식)** | `https://github-trends-api.vercel.app/api/rss` | 6시간 |
| **Product Hunt — AI** | `https://www.producthunt.com/topics/ai/feed` ⚠️ | 24시간 |
> ⚠️ Product Hunt RSS는 공식 지원하지 않아 URL이 변경될 수 있음. PH API(GraphQL) 우선 사용 권장.
| **TLDR AI Newsletter** | `https://tldr.tech/api/rss/ai` | 24시간 |
| **Hugging Face Daily Papers** | `https://huggingface.co/api/daily_papers?format=rss` | 24시간 |
| **Papers with Code — Latest** | `https://paperswithcode.com/rss/latest` | 24시간 |

#### 🔧 자동 감시 설정 (Feedly Pro 기준)
```
1. Feedly에 위 RSS URL 모두 구독
2. "AI coding agent" / "MCP" / "open source" 키워드로 Board 자동 분류
3. 매일 오전 9시 Feedly Board 확인 → 신규 프로젝트 추출
```

#### 🐚 대안: CLI 기반 RSS 리더 (자동화 스크립트용)
```bash
# newsboat 설치
# config 파일에 위 RSS URL 등록 → `newsboat -x reload` 로 갱신
# 출력 파싱 → AI 관련 글 필터링 → GitHub URL 추출
```

---

### 19. Hacker News — Show HN 발표 모니터링
> **자동화 방식:** HN Algolia API + 시간대 필터 (cron 2시간 간격)

```bash
# ▸ HN Algolia API: https://hn.algolia.com/api
# ▸ 시간대 필터: 미국 동부 오전 6시~12시 (한국 시간 오후 7시~익일 오전 1시)
#   → 이 시간대에 Show HN 글이 가장 많이 게시됨
# ▸ 실행 시간: 한국 시간 오후 8시, 오후 11시, 익일 오전 6시 (하루 3회)

curl "https://hn.algolia.com/api/v1/search?query=Show+HN+AI+agent&tags=story&numericFilters=points>2,created_at_i>{{UNIX_TIMESTAMP_24H_AGO}}&hitsPerPage=50"
```

**⏰ 시간대 필터 설명:**
- 미국 동부 기준 **오전 6시~낮 12시** = Show HN 게시 피크 시간
- 한국 시간으로 **오후 7시~익일 오전 1시**에 해당
- 이 시간대에 집중 스캔 시 조기 발견 확률 3배 이상

---

### 20. Twitter/X 해시태그 모니터링
> **자동화 방식:** Twitter API v2 + 키워드 필터 (시간대 설정 필수)

#### API 설정 (Bearer Token 필요)
```
# Twitter Developer Portal에서 Elevated Access 신청
# Bearer Token 발급 후 아래 엔드포인트 호출
GET https://api.twitter.com/2/tweets/search/recent?query=
  (#AIagents OR #AIcoding OR #OpenSourceAI) (GitHub OR "just released") -is:retweet
&tweet.fields=created_at,public_metrics
&max_results=100
&start_time={{YYYY-MM-DD}}T00:00:00Z
```

**⏰ 시간대 필터:**
- **스캔 시간:** 한국 시간 **오전 8시, 오후 2시, 오후 9시** (하루 3회)
- 미국 동부 기준 **오전 8시~11시** 인플루언서 포스팅 집중 시간대 반영
- `start_time` 파라미터로 최근 4시간 범위만 조회 (rate limit 절약)

#### 키 인플루언서 직접 모니터링
```
@mattpocock  → TypeScript/CLI 도구 발표
@ThePrimeagen → 오픈소스 코딩 도구 리뷰
@Swyx        → AI 인프라/에이전트 트렌드
@khoiucd     → AI 코딩 도구
@t3dotgg     → 웹 개발/AI 도구
```

---

### 21. Product Hunt — API 연동
> **자동화 방식:** Product Hunt API v1 (GraphQL) — 웹검색 대신 API 직접 호출 권장

```graphql
# ▸ API 키 발급: https://api.producthunt.com/v1/me (Developer 등록 필요)
# ▸ Rate Limit: 1000 req/hour (일 1회 호출이면 충분)
# ▸ 엔드포인트: POST https://api.producthunt.com/v2/api/graphql

query {
  posts(
    first: 20
    order: NEWEST
    topic: { slug: "ai" }
    postedAfter: "{{YYYY-MM-DD}}"  # 24시간 전
  ) {
    nodes {
      id
      name
      tagline
      url
      website
      votesCount
      topics { nodes { name } }
    }
  }
}
```

#### fallback: 웹검색 (API 키 없을 때)
```
websearch: `site:producthunt.com "2026" "AI" "agent" OR "coding" [이번주]`
websearch: `site:producthunt.com newest AI tools for developers 2026`
```

#### YC Startup Directory 병행 확인
```
websearch: `site:ycombinator.com directory AI 2026 tool`
websearch: `site:workatastartup.com AI developer tools company`
```

---

### 22. 뉴스레터 RSS 자동 구독
> **자동화 방식:** Feedly/Inoreader Board 자동 분류 + 키워드 알림

| 뉴스레터 | RSS Feed URL | 주요 키워드 필터 |
|----------|--------------|------------------|
| **TLDR AI** (`tldr.tech/ai`) | `https://tldr.tech/api/rss/ai` | "open source", "agent", "coding" |
| **Import AI** (`importai.substack.com`) | `https://importai.substack.com/feed` | "GitHub", "open source", "tool" |
| **The Rundown AI** (`therundown.ai`) | `https://www.therundown.ai/feed` | "open source", "GitHub stars" |
| **Hugging Face Daily Papers** | `https://huggingface.co/api/daily_papers?format=rss` | "code generation", "agent" |
| **Papers with Code** | `https://paperswithcode.com/rss/latest` | "code generation", "agent framework" |

**자동화 설정:**
1. Feedly Pro의 **Monitor** 기능으로 위 뉴스레터 RSS 등록
2. 키워드 필터: `"open source" AND ("AI agent" OR "coding tool" OR "MCP")`
3. 매칭 시 Slack/이메일 알림 → 일간 다이제스트에 자동 포함

---

### 23. GitHub Advanced Search — 키워드 조합 자동화 (cron)
> **자동화 방식:** `gh` CLI + 커스텀 키워드 조합을 정기 실행

```bash
# ▸ 실행 주기: 매일 오전 10시, 오후 10시 (2회)
# ▸ 아래 쿼리들을 for문으로 순회하며 JSON 결과 수집

# AI Agent 프레임워크
gh search repos -- -q "AI agent framework" --stars ">=100" --pushed ">={{YYYY-MM-DD}}" --limit 20

# MCP 서버 (OR는 개별 쿼리로 분할)
gh search repos -- -q "MCP server" --stars ">=50" --created ">={{YYYY-MM-DD}}" --limit 20
gh search repos -- -q "Claude plugin" --stars ">=50" --created ">={{YYYY-MM-DD}}" --limit 20

# 언어 필터링: Rust/Go 신규 AI 도구 (성능 중심)
gh search repos -- -q "topic:ai language:Rust" --stars ">=30" --created ">={{YYYY-MM-DD}}" --limit 20
gh search repos -- -q "topic:ai language:Go" --stars ">=30" --created ">={{YYYY-MM-DD}}" --limit 20

# AI SDK / 라이브러리 (느슨한 매칭)
gh search repos -- -q "AI SDK" --stars ">=200" --pushed ">={{YYYY-MM-DD}}" --limit 20

# Code Review 도구
gh search repos -- -q "code review AI" --stars ">=50" --pushed ">={{YYYY-MM-DD}}" --limit 20
```

> **`{{YYYY-MM-DD}}`** 는 실행 스크립트에서 오늘 날짜로 치환 (예: `2026-05-25`)

---

### 24. GitHub Discussions — 커뮤니티 발표 스캔
> **자동화 방식:** GitHub GraphQL API + 특정 저장소 Discussions 감시

```graphql
# 특정 저장소의 Discussions 최신 글 조회
query {
  repository(owner: "openai", name: "openai-cookbook") {
    discussions(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        title
        url
        createdAt
        labels(first: 5) { nodes { name } }
      }
    }
  }
}
```

**타겟 저장소 (Discussions 활동 활발):**
- `github.com/anthropics/claude-code/discussions`
- `github.com/openai/openai-cookbook/discussions`
- `github.com/microsoft/autogen/discussions`
- `github.com/langchain-ai/langchain/discussions`
- `github.com/crewAIInc/crewAI/discussions`

#### fallback 검색 (GraphQL 없을 때):
```
websearch: `site:github.com/discussions "we just open-sourced" OR "now available" AI agent 2026`
websearch: `site:github.com/discussions label:showcase OR label:announcement AI coding 2026`
```

## Filter Criteria (모두 통과해야 추가)
- ✅ AI 코딩 에이전트 / 개발 도구 / 에이전트 메모리 / 오케스트레이션 / **GitHub/코드 검색 도구** 관련 우선, 그 외 고스타·급성장 OSS도 후보에 포함 (주제 무관 제외 조건 없음)
- ✅ Star 100+ 또는 최근 24시간 내 급성장
- ✅ `ai 정보_도구.md`에 없는 신규 프로젝트
- ❌ 설명이 부족하거나 저장소가 비어있으면 제외

## Output Format
기존 MD의 아코디언 테이블 구조를 정확히 따라 작성:

```
| [**프로젝트명**](GitHub URL) | <details><summary><b>한줄 요약 [상세 열기]</b></summary><br>핵심 설명. 주요 기능은 bullet 리스트.<br><br><b>💡 핵심 기능:</b><br><ul><li><b>기능:</b> 설명</li></ul></details> | [오늘 날짜] |
```

## 카테고리 배치
- Section 1 → CLI 코딩 에이전트, 코드 인텔리전스, MCP 도구
- Section 2 → 에이전트 메모리, 오케스트레이션, SDLC, 워크플로우

## Execution Log
완료 후 아래 포맷으로 결과를 출력하세요:
```
📦 Daily OSS Digest — [날짜]
✅ 추가: 프로젝트A, 프로젝트B (총 N개)
⏭️ 스킵 (중복): 프로젝트X, 프로젝트Y
⏭️ 스킵 (부적합): 프로젝트Z (사유: AI 코딩 무관)
```

## Git Commit
변경사항이 있으면 아래 메시지로 커밋하세요:
```
docs: add N OSS projects to ai 정보_도구.md [YYYY-MM-DD]
```

---

## 🚀 실행 전략 및 팁

### Daily (매일) 실행 흐름
1. **Scan Sources 1~16** — 기본 스캔 (5~10분)
   - 웹 자동화 또는 수동 브라우징
2. **필터링 & 추가** — 5개 이하만 추가 (품질 우선)
3. **Git Commit** — 변경사항 있으면 즉시 커밋

### Weekly (주 1회) 심화 발굴
- **Advanced Scan Sources 17~24** 중 3~5개 선택 실행
- GitHub API, RSS 피드, 커뮤니티 신규 발표 모니터링
- 더 깊은 신규 프로젝트 발굴로 보충

## 🛠️ 자동화 실행 인프라 (구현 가이드)

### 1. 자동화 스크립트 구조

```
scripts/
├── daily-digest.ps1        # 주 진입점: Sources 1~24 자동 실행
├── sources/
│   ├── github-api.ps1      # Source 17, 23: gh CLI 래퍼
│   ├── rss-monitor.ps1     # Source 18: RSS 피드 수집
│   ├── hackernews.ps1      # Source 19: HN Algolia API
│   ├── twitter-monitor.ps1 # Source 20: Twitter API v2
│   ├── producthunt.ps1     # Source 21: Product Hunt API
│   ├── newsletters.ps1     # Source 22: 뉴스레터 RSS
│   └── discussions.ps1     # Source 24: GitHub Discussions API
├── filter.js               # 중복/적합성 필터링
├── merge-results.ps1       # 결과 병합 → ai 정보_도구.md 업데이트
└── config.json             # API 키, 토큰, 타겟 저장소 목록
```

> 📁 **note:** `scripts/` 디렉토리가 생성되어 있습니다. 필요 시 스크립트를 직접 실행하세요.

### 3. 설정 파일 예시 (`config.json`)

```json
{
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "twitter_bearer_token": "AAAAAAAAAAAAAAAAAAAAxxxxxxxxxxxx",
  "producthunt_token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "target_repos": [
    "anthropics/claude-code",
    "openai/openai-cookbook",
    "microsoft/autogen",
    "langchain-ai/langchain",
    "crewAIInc/crewAI"
  ],
  "filter": {
    "min_stars": 50,
    "max_per_run": 5,
    "keywords": ["AI agent", "coding tool", "MCP", "open source"]
  },
  "schedule": {
    "basic": ["09:00", "21:00"],
    "hn_timing": "19:00,22:00,05:00",
    "twitter_timing": "08:00,14:00,21:00"
  }
}
```

## 🎯 높은 신규 발굴율 유지 핵심

✅ **조기 감지** — Show HN, Product Hunt는 공식 트렌딩보다 3~7일 먼저 노출  
✅ **깊은 검색** — GitHub Advanced Search로 아직 트렌딩 진입 전 저장소 포착  
✅ **커뮤니티 신뢰** — Reddit r/AIagents, HN은 커뮤니티 평가 포함된 프로젝트만 제시  
✅ **자동화 필수** — 17~24번 소스는 자동화 없이 수동 실행 시 ROI 극히 낮음  
✅ **시간대 전략** — 각 소스별 최적 시간대에 실행해야 조기 발견 확률 극대화  
✅ **API 우선** — 웹스크래핑/웹검색 대신 API 직접 호출이 안정적이고 빠름  
✅ **단계적 도입** — 1) `gh` CLI → 2) RSS → 3) Twitter API → 4) PH API 순서로 구축
