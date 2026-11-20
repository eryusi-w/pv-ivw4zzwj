# 투자 전략 리포트 생성기

5개 투자 유튜브 채널의 최신 영상을 분석해 투자 전략 문서를 만듭니다.
`youtube_toolkit/` 모듈을 재사용합니다 (`../../../youtube_toolkit`, 즉 `projects/youtube_toolkit`에 있어야 함).

- 송팀장 https://www.youtube.com/@Song_Teamjang
- 경제사냥꾼 https://www.youtube.com/@경제사냥꾼
- sng_tv https://www.youtube.com/@sng_tv
- 테스프레소 https://www.youtube.com/@%ED%85%8C%EC%8A%A4%ED%94%84%EB%A0%88%EC%86%8C
- 비연세 https://www.youtube.com/@biyonsei

## 설치

```bash
cd projects/naver-blog/extractors/investment_strategy
pip install -r requirements.txt
```

API 키는 `../github_awesome_extractor/.env`를 자동 재사용합니다.
(`YOUTUBE_API_KEY`, `BYNARA_API_KEY` 또는 `OPENROUTER_API_KEY_1/2`)
자체 `.env` 파일을 만들어 덮어쓸 수도 있습니다.

## 사용법

```bash
# 기본: 채널당 최신 5개 영상
python main.py

# 채널당 3개씩
python main.py --videos 3

# 특정 채널만
python main.py --channel 송팀장 --videos 3
```

결과는 `../../sources/investment_strategy/investment_strategy_YYYYMMDD_HHMMSS.html` 로 저장됩니다.
리포트와 함께 `analysis_YYYYMMDD_HHMMSS.json` (구조화된 분석 데이터)도 같은 폴더에 저장됩니다.
※ 산출물은 `naver-blog/sources/investment_strategy/`에 저장된다(`config.py`의 `DEFAULT_OUTPUT_DIR`)

## 분석 뷰어

```bash
python build_viewer.py            # ../sources/investment_strategy/analysis_*.json → viewer.html 생성
```

`viewer.html`을 브라우저로 열면 분석 일시·채널별로 영상 분석 내용을 조회할 수 있습니다.
새 분석을 실행하면 뷰어가 자동으로 갱신됩니다. 수동 갱신이 필요하면 `python build_viewer.py`를 실행하세요.
기존 HTML 리포트만 있는 경우 `python backfill_analyses.py`로 JSON을 먼저 생성하세요 (실행 시 뷰어도 함께 갱신됩니다).

## 동작 방식

1. `YoutubeAnalyzer.channels.list_uploads_video_ids()` 로 채널 업로드 목록의 최신 영상 조회
2. `YoutubeAnalyzer.analyze()` 로 자막+설명 수집 (`youtube_toolkit` 재사용)
3. LLM이 영상별 투자 요약 (주장/섹터/종목/단기·중장기 전략/리스크/시각)
4. 전체 요약을 종합 투자 전략 문서로 통합 + 부록에 영상별 요약 첨부

영상은 채널별 최신순으로 분석하며, 리포트에 게시일을 표시합니다. 세 채널 모두에서
분석할 영상을 가져오지 못하면 빈 리포트 대신 오류를 반환합니다.
