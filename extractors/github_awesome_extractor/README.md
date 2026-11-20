# GitHub Awesome AI Tool Extractor

YouTube 채널과 GitHub 탐색을 통해 여러 분야의 AI 프로젝트를 모아 누적 카탈로그로 정리하는 도구

## 기능

- YouTube 영상, 분야별 GitHub 인기 검색, 일간·주간 Trending에서 프로젝트 후보 수집
- 개발·업무·문서·창작·교육·의료 등 분야별 AI 프로젝트 분류
- 기간을 지정해 YouTube 영상 후보 백필
- 최초 등록일을 보존하는 누적 Markdown 카탈로그 생성

## 설치

```bash
cd projects/naver-blog/extractors/github_awesome_extractor
pip install -r requirements.txt
```

> 유튜브 수집은 `projects/youtube_toolkit`을 사용합니다 (이 저장소는 `projects/naver-blog/extractors/` 아래에 있으며, `pipeline.py`·`modules/data_collector.py`·`sources/manuagi_collector.py`가 `../../../youtube_toolkit` 경로를 자동으로 찾습니다).
> (`modules.DataCollector`는 구 코드 호환용 얇은 래퍼이며, 신규 코드는
> `from youtube_toolkit import YoutubeAnalyzer`를 직접 사용하세요.)

## 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 설정하세요:

```
GITHUB_TOKEN=your_github_token  # 선택사항
YOUTUBE_API_KEY=your_youtube_data_api_key  # ManuAGI 기간 검색에 필요
OPENAI_API_KEY=your_openai_key  # 선택사항 (외부 LLM 분석 사용 시)
```

## 사용법

### 유튜브 영상 분석

```bash
python pipeline.py <video_id_or_url>
# 예: python pipeline.py NcR3AU8GSrQ
# 예: python pipeline.py "https://www.youtube.com/watch?v=NcR3AU8GSrQ"
# (watch / youtu.be / shorts / embed / live URL 모두 가능)
```

### 텍스트 직접 입력

```bash
python pipeline.py --text "여기에 트랜스크립트나 텍스트 입력"
```

### ManuAGI 다이제스트 수집 및 누적

기본 실행은 최근 3일간 게시된 영상을 대상으로 합니다. 처음 아카이브를 채우거나
특정 기간을 다시 수집하려면 날짜 범위를 지정할 수 있습니다. 날짜는 서울 시간 기준이며
종료일도 포함됩니다. 채널별 조회 영상 상한은 기본 50개입니다.

```bash
# 최근 3일
python sources/manuagi_collector.py

# 지정 기간 백필 (예: 2026년 8월 전체, 채널별 최대 100개)
python sources/manuagi_collector.py --from-date 2026-08-01 --to-date 2026-08-31 --max-videos-per-channel 100

# 수집 후보를 보강하고 누적 다이제스트 생성
python sources/manuagi_to_digest.py
```

`output/manuagi_repos.enriched.json`은 저장소별 누적 데이터를 보관합니다. `output/ai-tools-archive.html`은 분야 필터와 카드형 목록이 있는 대시보드입니다.
YouTube 영상 후보와 함께 GitHub의 AI·LLM·에이전트·MCP·토큰 최적화·컨텍스트 윈도·머신러닝·생성형 AI 검색 결과와 일간·주간 Trending 저장소도 후보로 살핍니다. 일반 검색은 저장소 이름·설명·토픽을 보고, 컨텍스트 윈도 검색은 README도 살핍니다. 비활성 저장소와 포크는 제외합니다. 기본 GitHub 검색 후보는 검색어별 결과를 합쳐 최대 60개이며, `--popular-limit`으로 조정하거나 `--popular-limit 0`으로 끌 수 있습니다. `--trending-limit`은 일간·주간 각각의 후보 수를 조정합니다. `--from-date`/`--to-date`는 YouTube 영상 게시일에 적용되고, GitHub 검색 및 Trending은 실행 시점 기준입니다. 별점은 후보 발굴에만 사용하고 최종 카탈로그에는 용도·주요 기능·분야를 표시합니다.
별점 하한은 검색어별로 다르게 설정해 새 프로젝트와 인기 프로젝트를 함께 찾으며, 전체 검색 결과 상한은 최대 100개입니다. 기간 지정은 YouTube 영상에 적용되고, 인기·Trending 후보는 실행 시점 기준으로 수집합니다. HTML의 날짜 선택은 다음에 실행할 수집 명령을 만들어 보여주며, 수집은 아래 CLI 명령으로 실행합니다. LLM 분석을 생략하려면 두 번째 명령에 `--no-llm`을 추가할 수 있습니다.
프로젝트 설명은 한국어로 표시합니다. LLM 분석을 사용하면 한국어 요약을 생성하고, LLM을 사용하지 않는 경우에는 저장된 한국어 설명을 사용합니다. 아직 한국어 설명이 등록되지 않은 신규 프로젝트에는 별도 안내 문구가 표시됩니다.
각 프로젝트의 등록일은 아카이브에 처음 추가된 날짜로 유지됩니다. 이미 처리한 영상도 다시
포함하려면 수집 명령에 `--force`를 추가하세요.

기능 회귀 테스트는 개발 의존성을 설치한 뒤 외부 API 호출 없이 실행할 수 있습니다.

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests/test_catalog_features.py
```

## 출력

분석 결과는 `output/` 디렉토리에 Markdown 파일로 저장됩니다.

## 에이전트 프롬프트 (`agents/`)

repo-root `agents/`에서 이동됨:

- `agents/AGENTS.md` — 위클리 다이제스트 (스캔→필터→분석→추가→보고, Section 1/2/3 배치 규칙)
- `agents/daily-digest-prompt.md` — 데일리 실행 프롬프트 (스캔 소스 1~24, 1회 최대 5개)

연동 지점:

- `sources/manuagi_collector.py` — 지정한 게시일 범위의 영상과 GitHub 분야별 검색·일간·주간 Trending에서 후보 수집
- `modules/llm_classifier.py` — AI 관련 여부와 개발·업무·문서·창작 등 분야 분류
- `sources/manuagi_to_digest.py` — 저장소별 누적, 최초 등록일 보존, 용도·기능 중심 Markdown 생성

## 프로젝트 구조

```
github_awesome_extractor/
├── agents/
│   ├── AGENTS.md                # 위클리 다이제스트 에이전트 프롬프트 (구 repo-root agents/에서 이동)
│   └── daily-digest-prompt.md   # 데일리 다이제스트 실행 프롬프트 + 스캔 소스 1~24
├── modules/
│   ├── data_collector.py      # 유튜브 트�랜스크립트 수집
│   ├── link_extractor.py      # GitHub URL 추출
│   ├── github_enricher.py     # GitHub API 데이터 보강
│   ├── llm_classifier.py      # LLM 기반 분류 및 요약
│   └── document_generator.py  # 리포트 생성
├── config/
│   └── settings.py            # 설정 파일
├── templates/                 # 리포트 템플릿
├── output/                    # 생성된 리포트
├── pipeline.py                # 메인 파이프라인
└── requirements.txt
```
