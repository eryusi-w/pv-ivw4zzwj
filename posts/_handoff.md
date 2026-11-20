# 새 세션 인수인계 (2026-11-14 갱신)

이 파일은 컨텍스트 리셋 후 작업을 이어가기 위한 스냅샷이다. 먼저 `AGENT.md`·`AGENTS.md`·`NOTES.md`를 읽고, 이 파일의 "다음 작업"부터 진행한다.

## 현재 상태

- 총 발행 글 **174건** (`posts/_published_titles.json`, `blog_documentation_ryusi79.md` 108~126번까지 등록)
- 카테고리(실측 확인): `AI 활용` / `디지털·모바일`(구 PC·IT) / `보안·IT상식` / `업무·생산성` / `투자·금융`(구 투자) — publish.mjs는 카테고리명을 정확히 일치시켜야 함
- **추가 카테고리 생성 금지** — 사용자가 명시. Git 등 개발 주제는 `PC·IT`에 분류한다.
- AI 후보 풀 소진: `next-tool.mjs --refresh` 결과 A등급 단독 후보 0. B등급 잔여 7개는 묶음용.
- **주제 큐 소진**: `posts/_topic_queue.md` 18개 항목 전부 발행 완료(11-14). 다음 주제는 새 후보 발굴 필요.

## 11-14 큐 15편 추가 발행 (93~107번)

- 보안 4: 개인정보처리방침(…763138), 스미싱악성앱(…764294), 기관사칭전화(…765400), 원격지원사기(…766452)
- 업무 5: XLOOKUP(…770418), Notion(…771356), 한글단축키(…772664), 조건부서식(…774079), 회의록(…775192)
- PC·IT 6: SSD(…781730), VSCode확장(…782779), 윈도우단축키(…783773), 브라우저보안(…784820), GitHub입문(…786140), 프린터드라이버(…787484)

## 중요 운영 교훈 (11-14, NOTES.md에도 기록)

- **write.mjs는 RESUME 없이 실행하면 기존 글쓰기 탭을 전부 닫는다** → write 여러 개를 몰아 돌리면 앞 글 본문 유실. 반드시 편별로 write→typography→publish 순차 실행.
- **ego `nodejs -e`에 셸 env(POST_CONFIG)를 넘겨도 상주 런타임에 반영 안 됨** → `-e` 안에서 `process.env.POST_CONFIG` 직접 설정 필수.
- 이미지 앵커는 h2 텍스트와 정확히 일치해야 함(`?`·괄호 포함). 불일치 시 config 수정 후 `RESUME=1`로 남은 장만 삽입.
- named space 재생성은 `taskSpace()`가 아니라 `claimTaskSpace('naver-blog-check')` (listTaskSpaces에 등록됨).
- `image-text.json` 스키마: headerTitle/headerRight/accent/cover[3]/chips[4]/cards[4]/rows[4]/flow[3]/items[5] — items.mjs 템플릿 기준.
- **post.html은 LF 개행 필수** — CRLF면 `<pre><code>` 코드가 `\r\n`으로 추출돼 에디터와 불일치, `codeOk` 실패·RESUME 무한 재시도. 작성 후 `\r\n`→`\n` 변환 습관화.

## 오늘(11-13) 발행 완료 (37편)

- AI 28편 + 신규 포맷 4편(비교·ComfyUI·AGENTS.md·주간뉴스) + PC·IT 2편 + 업무·보안 2편 + 엑셀피벗·Bitwarden·Git 3편
- 상세 URL은 `posts/_published_titles.json`과 `blog_documentation_ryusi79.md` 77~89번 참고.

## 오늘(11-14) 발행 완료 (18편)

- 큐 첫 3편(Docker·보고서·개인정보유출, 90~92번) + 큐 나머지 15편(93~107번). 큐 전량 소진.

## 미해결 / 보류

1. **`update.mjs` 본문 클리어 실패** — 레거시 글 4건(ollama-local-llm, firecrawl-intro, interfaces-design-skills, n8n-review)에 내부 링크 추가한 `post.html`이 남아 있으나, 수정 모드에서 본문 삭제가 `sel=0` 3회 실패로 중단됨(라이브 변경 없음). 해결하려면 레거시 마크업(h3·span 장식 헤딩) 대응 클리어 로직 수정 또는 수동 비우기 후 재실행.
2. **`mromidev-claude-animated-shorts`** — `--tool` 지정 과정에서 생긴 미검토 초안. 채택/폐기 결정 필요.
3. **`nirdiamant-genai-agents`** — #31과 중복이라 의도적 미발행.
4. **`ai-tools-news-week1`** — 연재 시리즈 1회차. 다음 회차는 extractor 재수집 후 새 등록분으로 작성 가능.

## 소스 발굴 조사 결과 (이번 세션)

### GitHub 수집 재활용
- `github_awesome_extractor`는 AI 전용: `modules/llm_classifier.py` 프롬프트가 "AI가 핵심이 아닌 일반 소프트웨어는 AI 도구로 분류하지 마세요"로 필터링.
- `output/manuagi_repos.enriched.json`에 `is_ai_tool=false` 66개 있으나 전부 분석 미비 스텁(도메인·용도 없음) — 그대로 사용 불가.
- 비-AI 확장 시 필요 작업: 수집 소스(현재 YouTube awesome-list 기반)를 유틸리티·보안·생산성 목록으로 교체 + 분류 프롬프트를 주제별로 분기 + 별도 출력 파일. 기존 AI 파이프라인 동작은 유지할 것.
- **단기 결론**: PC·IT·보안·업무 주제는 양이 적고 evergreen라 수동 방식(GitHub API 사실 확인 → 직접 작성)이 빠름.

### 검색 수요 데이터 — 수집 성공 (11-14)
- `admin.blog.naver.com/ryusi79/stat/referer`의 `statmain` iframe이 cross-origin이라 부모 evaluate 불가 → iframe src `https://blog.stat.naver.com/blog/user/referer/total?blogId=ryusi79&isIE8=false`를 새 탭으로 직접 열면 통계가 보임. 일간/주간 탭은 `a` 클릭으로 전환.
- 수집 결과와 공백 분석은 `posts/_content-discovery.md` "2026-11-14 유입분석 수집" 섹션.
- `posts/_content-discovery.md`에 AI 키워드 유입 분석 결과 있음(수요 키워드 vs 발행 글 대조, 공백 키워드 7개 정리).
- `DEMAND_SEEDS`는 `lib/tool-selection.mjs`에 있음(mattpocock, grill-me, claude-skill 등).

## 다음 작업 후보 (우선순위 제안)

1. ~~주제 큐 파일 생성~~ — **완료**: `posts/_topic_queue.md` 18개 항목 전부 발행됨(11-14). **큐가 비었으므로 다음 주제 후보 발굴이 필요** — 통계 스크래핑 또는 새 큐 작성.
2. ~~통계 스크래핑 재시도~~ — **완료**: `blog.stat.naver.com/blog/user/referer/total?blogId=ryusi79` 직접 오픈으로 일간·주간 유입 키워드 수집 성공(`_content-discovery.md`). 공백 키워드 대응 글 6편 발행(108~113번).
2-1. **남은 공백 후보**: getartcraft(114)·GSD Shipping(115) 해소. freellmapi는 2편 발행돼 보류. 의미 불명 키워드 2개(숫자값 홈페이지 디자인·지능형시스템 UI/UX)는 작성 보류 — `_content-discovery.md` 참조. **검색 수요 기반 공백은 사실상 소진 — 다음 발굴은 통계 재수집 또는 새 주제 큐 필요.**
3. **extractor 비-AI 모드** — 수집량이 필요해지면 구현.
4. **기존 글 개선 재시도** — `update.mjs` 클리어 로직 수정 후 4건 링크 보강 재발행.

## 블로그 설정 잔여 (11-13 세션)

- **소개글**: `"정말 필요한 걸까?" — 새 도구를 만날 때마다 던지는 질문, 이 블로그의 기준입니다.`를 `#frmIntroduce`에 입력해뒀으나 **저장 버튼을 누르지 못해 미적용 가능성 높음**. `admin.blog.naver.com/ryusi79/config/bloginfo` → iframe `#papermain` → `cgiform` 확인 필요.
- **프로필 이미지**: `assets/profile/profile-bubble.png`(800×800, 말풍선+? 디자인) 생성 완료, 미업로드.
- **블로그씨 질문**: 커스텀 문구 불가로 보임(배달 on/off만 존재). 문구 후보만 전달함.

## 발행 절차 요약 (반복 확인용)

1. `post.config.json`에서 `draft: true` 제거 → `validate.mjs --ready` 통과
2. task space `naver-blog-check` 없으면 `taskSpace('naver-blog-check')`로 재생성, ego 창 전면 필요 시 `SetForegroundWindow`
3. write → typography → publish 순서, 6~7편마다 `finish.mjs`로 탭 정리(8탭 상한)
4. 발행 후 `blog_documentation_ryusi79.md`·`_published_titles.json --refresh`·`NOTES.md` 갱신

## image-text 규격 (재발 방지)

- 표지 줄 ≤24자, 칩 ≤16자, 항목 설명 ≤24자, caution ≤20자, 설치/클론 행 ≤60자
- 초과 시 `image-text.json` 단축 후 `tools/images.mjs` 재렌더

## 카테고리 리네이밍 (11-14, 사용자 적용)

- 새 카테고리 추가 없이 기존 5개 명칭 확장: `PC·IT`→디지털·모바일 계열, `투자`→투자·금융 계열(사용자가 관리 페이지에서 직접 변경). `업무·생산성`·`보안·IT상식`·`AI 활용` 유지.
- side-hustle 글감 3편을 `AI 활용`으로 발행(116~118번): Vrew 숏폼, 스마트스토어 상세페이지, Canva 카드뉴스.
- 남은 제안 영역: 모바일 꿀팁(리네임된 PC·IT 계열), 세테크·연말정산(투자·금융 계열) — YMYL 검증 필요.

- 모바일·세테크 3편 발행(119~121번): 카톡 숨은기능(디지털·모바일), 갤럭시 통화녹음(디지털·모바일), 정부지원금 조회(투자·금융).
- 잔여 주제 5편 발행(122~126번): 연말정산(투자·금융), 아이폰 누끼(디지털·모바일), ChatGPT+엑셀·Gamma PPT·회의 전사(업무·생산성). checkText는 코드블록이 아닌 본문 문단 문구로 지정할 것.
- 세부 후속 3편 발행(127~129번): ISA→연금저축 세액공제(투자·금융), 파킹통장 비교(투자·금융), 유튜브 광고 차단(디지털·모바일). 총 177건.
- 세부 후속 후보 소진: ISA·파킹통장·유튜브광고 완료. 다음은 통계 재수집 또는 새 큐 필요.
- update.mjs 버그 수정: 수정 모드에서 scrollIntoView 좌표 어긋남 + shift선택/Delete 무력 → 스크롤타깃 scrollTop 보정 + Control+A→Delete로 해결. chatgpt-excel-prompt 글(…840405)에 VLOOKUP 예시 추가 재발행 완료.
- productivity_extractor 큐 소진: 12개 아이템 중 11개가 당일 수동 발행분과 중복, 나머지 1개(해외주식 양도세)만 미발행. 중복 빌드 prod-* 2개 삭제함.
- mromidev-claude-animated-shorts 발행(…868172, #130): 추출기 환각 내용(딥시크·일레븐랩스)을 README 팩트체크로 교정 후 윤문·발행. ai-tools 잔여 초안 소진.
