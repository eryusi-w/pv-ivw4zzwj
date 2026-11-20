# 직장인 업무·생산성 도구 및 팁 수집기 (productivity_extractor)

직장인, 학생, 1인 사업가의 칼퇴와 업무 효율을 돕는 생산성 도구, 실무 AI 활용법, 엑셀/문서 팁을 수집하고 네이버 블로그 포스팅용 재료로 구조화하는 파이프라인입니다.

## 1. 주요 기능

- **실무 생산성 소스 큐레이션**: 엑셀 수식 자동화, AI PPT 제작, 회의록 요약, 노션 템플릿, PDF 도구 등 대중적 검색량이 높은 테마 수집
- **YouTube 생산성 채널 연동**: `youtube_toolkit`을 활용하여 오빠두엑셀, 일잘러 장피엠 등 대표 채널 최신 영상 메타데이터 수집
- **LLM 구조화 가공**: 단순 정보 나열이 아닌 '문제해결형 제목', '핵심 효용 3가지', '3단계 실천 가이드', '복사해서 쓰는 프롬프트'로 가공
- **일자별 이력 관리 (`investment_strategy` 스타일)**:
  - 수집 일시 타임스탬프(`YYYYMMDD_HHMMSS`)로 누적 보존
  - `../../sources/productivity_extractor/analysis_YYYYMMDD_HHMMSS.json` (원시/분석 데이터)
  - `../../sources/productivity_extractor/productivity_YYYYMMDD_HHMMSS.html` (일자별 웹 리포트)
  - `../../sources/productivity_extractor/blog_recommendation.txt` (네이버 블로그 1순위 포스팅 재료)
  - ※ 산출물은 `naver-blog/sources/productivity_extractor/`에 저장된다(`config.py`의 `DEFAULT_OUTPUT_DIR`)
- **통합 뷰어 대시보드 (`viewer.html`)**: 역대 수집 일자별 데이터를 브라우저에서 날짜순/카테고리별로 열람

## 2. 설치 및 환경설정

기존 `../github_awesome_extractor/.env`의 API 키를 자동으로 재사용합니다.

```bash
cd projects/naver-blog/extractors/productivity_extractor
pip install -r requirements.txt
```

## 3. 사용법

### 기본 수집 실행 (큐레이션 + YouTube)
```bash
python main.py
```

### YouTube 수집 없이 큐레이션 도구만 빠르게 수집
```bash
python main.py --no-youtube
```

### 뷰어 대시보드 재생성
```bash
python build_viewer.py
```
생성된 `../../sources/productivity_extractor/viewer.html`을 브라우저로 열면 수집된 모든 일자의 데이터와 카테고리 필터를 확인할 수 있습니다.

## 4. 네이버 블로그(`projects/naver-blog`) 연동

`../../sources/productivity_extractor/blog_recommendation.txt` 및 최신 `analysis_*.json`을 소스로 사용하여 상위 `naver-blog`의 '업무·생산성' 신규 포스팅으로 자동 변환할 수 있습니다.
