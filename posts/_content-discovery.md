# 콘텐츠 발굴 — 유입 키워드 분석 (2026-11-13)

네이버 블로그 통계(`admin.blog.naver.com/ryusi79/stat/referer` → `blog.stat.naver.com/blog/user/referer/total`)에서 실제 유입 검색어를 수집하고, 발행 글 120건과 대조했다.

## 유입 키워드 (기간별)

**월간 (10월)**
| 키워드 | 비중 | 기존 글 |
|--------|------|---------|
| mattpocock / mattpocock-skills | 8.57%+2.86%×2 | ✅ "SKILLS 스킬 완벽 가이드" |
| Perplexi | 2.86% | ✅ Perplexity 글 다수 |
| ai ppt 추천 / ppt ai | 2.86%×2 | ✅ ppt-master |
| archify | 2.86% | ✅ archify |
| grill-me 사용방법 | 2.86% | ❌ 없음(수집 풀에도 없음) |
| ollama ai/로컬/설치 | 2.86%×3 | ✅ Ollama 글 |
| 클로드코드 디자인 스킬 | 2.86% | ✅ interfaces/UI UX Pro Max |
| 프로시저 시각화 | 2.86% | ❌ 없음 |

**주간 (11.02~11.08)**
| 키워드 | 비중 | 기존 글 |
|--------|------|---------|
| im not ai 설치방법 | 2.32% | ✅ im-not-ai |
| freellmapi | 1.32% | ✅ FreeLLMAPI 2편 |
| n8n 업무자동화 | 1.32% | ✅ n8n 2편 |
| Firecrawl / firecrawl | 1.65% | ✅ firecrawl |
| archify | 0.99% | ✅ |
| 윤문 | 0.99% | △ im-not-ai·caveman 부분 커버 |
| AI 활용 팁 | 0.66% | ✅ tip 시리즈 |
| Open WebUI | 1.32% | ✅ |
| UI UX Pro Max 사용방법 / UXUI SKILL | 1.32% | ✅ |
| agents.md | 0.66% | ✅ AGENTS.md |
| graphify / im-not-ai / ollama / ppt master | 각 0.66% | ✅ |
| 지능형시스템 UI/UX | 0.66% | △ UI UX Pro Max 부분 |
| 클로드 랜딩페이지 | 0.66% | △ "랜딩페이지 디자인 기준" 부분 |
| /caveman | 0.33% | ✅ |

**일간 (11.12)**
artcraft·ppt github·strata(각 4.29%), freellmapi·AI 시스템 아키텍처·AI 에이전트 입문 강의·Claude-Code-Game-Studios 설정방법·FreeLLMAPI·Open WebUI·UI UX Pro Max(각 1.43~2.86%), ai 문체 제거 명령어·astryx·comfyui 사용법·freellmapi github/사용법·graphify·heretic 설치·ollama java·open-webui 설치(각 1.43%)

## 발견한 공백 (검색 수요 O, 전용 글 X)

1. **AI 시스템 아키텍처** (일간 1.43%) — archify 다이어그램 글만 있고 개념·설계 가이드는 없음. 키워드 첫 단어가 "AI"라 경쟁 낮음.
2. **AI 에이전트 입문** (일간 1.43%) — "마이크로소프트 생성 AI 입문 21강"은 MS 강의라 에이전트 입문 수요를 못 받음. 개념→도구→첫 실습 순서의 입문 글.
3. **AI 문체 제거·윤문 명령어** (일간+주간) — im-not-ai·caveman 개별 글은 있으나 "윤문/문체 제거 명령어 모음" 검색 의도 글이 없음. 두 도구+프롬프트 기법 묶음.
4. **클로드 랜딩페이지** (주간 0.66%) — 수집 풀에 `Motionsites-AI/claude-skill`(1,099★, "award-level cinematic landing pages" 스킬) 있음. ai-tips 묶음 후보 또는 단독 검토 가치.
5. **프로시저 시각화** (월간 2.86%) — 의미 불명확. 네이버 검색으로 실수요 확인 필요(DB 프로시저? 의료?).
6. **grill-me** (월간 2.86%) — 수집 풀에 없는 도구. GitHub에서 실체 확인 후 글감 후보.
7. **comfyui 사용법** (일간 1.43%) — 시드에만 있고 풀에 repo 없음. 재수집 대상.

## 구조적 문제

- **A등급 단독 후보 고갈**: `next-tool.mjs` 기준 A등급 잔여 0. B/C만 남아 단건 생산이 사실상 끝남.
- **키워드-주제 역전 필요**: 지금 파이프라인은 "stars 높은 repo → 글". 유입 상위 키워드 중 repo 없는 것(아키텍처·입문·윤문·프로시저·grill-me)은 이 파이프라인으로 못 만듦 → 키워드 먼저 정하고 글을 쓰는 수동/반자동 경로 필요.
- **수집 풀 재충전**: `github_awesome_extractor` 재실행으로 새 YouTube 영상 → 새 repo 확보가 단건 글의 유일한 공급원.

## 적용한 변경

- `lib/tool-selection.mjs`: `isPublished` 버그 수정 — `(도구명)` 괄호 표기 매칭 추가(rea·pi 같은 3자 이름도 정확히 판별), `PUBLISHED_ALIASES` 추가(GenAI_Agents·claude-plugins·dsh-superagent의 옛 제목 형식 대응). 발행 도구가 후보로 다시 뜨던 문제 해소.
- `DEMAND_SEEDS` 추가: `mattpocock`, `grill-me`, `claude-skill` (월간·주간 유입 확인분)

## 2026-11-14 유입분석 수집 (SPA 우회 성공)

접근법: `admin.blog.naver.com/ryusi79/stat/referer`의 `statmain` iframe이 cross-origin이라 부모에서 못 읽음 → iframe src `https://blog.stat.naver.com/blog/user/referer/total?blogId=ryusi79`를 직접 열어 수집. 일간/주간 탭 전환은 링크 클릭으로 가능.

### 일간 (2026-11-13)
artcraft 5.17%, getartcraft 3.45%, ollama 활용법 3.45%, strata 3.45%, GSD Shipping 1.72%, Heretic 사용 1.72%, UI UX Pro Max 스킬 1.72%, claude omniroute 1.72%, claude 접속 1.72%, cluade caveman 1.72%, comfyui 사용법 1.72%, freellm 1.72%, mattpocock 1.72%, ollama 용량 1.72%, prompt.chat 1.72%, text to cad 1.72%, ui ux pro max 1.72%, wincustoms 1.72%, 숫자값들이 나온 홈페이지 디자인 1.72%

### 주간 (~2026-11-14)
im not ai 설치방법 2.32%, freellmapi 1.32%, n8n 업무자동화 1.32%, Firecrawl 0.99%, archify 0.99%, 윤문 0.99%, AI 활용 팁 0.66%, Open WebUI 0.66%, UI UX Pro Max 사용방법 0.66%, UXUI SKILL 0.66%, agents.md 0.66%, graphify 0.66%, im-not-ai 0.66%, ollama 0.66%, ppt master 0.66%, 지능형시스템 UI/UX 0.66%, 클로드 랜딩페이지 0.66%, /caveman 0.33%

### 공백 분석 (11-14 기준)

이전 공백 7개 중 5개는 11-13에 발행 완료(AI 시스템 아키텍처 #74, AI 에이전트 입문 #75, AI 문체 제거 #76, claude-skill #73, ComfyUI #78).

**남은/새 공백:**
1. ~~im not ai 설치방법~~ → im-not-ai-setup-guide 발행(…803023)
2. ~~ollama 용량·활용법~~ → ollama-model-management 발행(…804078)
3. ~~n8n 업무자동화~~ → n8n-first-workflow 발행(…805309)
4. ~~claude 접속·omniroute~~ → claude-code-setup(…806741) + claude-omniroute-setup(…811014) 발행
5. ~~UI UX Pro Max 사용방법~~ → ui-ux-pro-max-guide 발행(…812374)

**남은 공백 후보 (11-14 후반 기준):**
- ~~**getartcraft**~~ → getartcraft-guide 발행(…815679). storytold/artcraft 동일 제품 확인, Studio+Crafting Apps 각도로 분리.
- ~~**GSD Shipping**~~ → gsd-ship-autonomous 발행(…817479). `/gsd:ship` 명령·`/gsd auto` 자율 모드 확인, gsd-core 글과 각도 분리.
- **freellmapi** — 이미 2편 발행(개요+통합), 추가 가치 낮음으로 보류.
- **숫자값들이 나온 홈페이지 디자인 / 지능형시스템 UI/UX** — 의미 불명·대학 강의성 키워드로 판단, 작성 보류.

**구조적 관찰:** 비-AI 카테고리(PC·IT·보문·업무)는 아직 검색 유입 0 — evergreen이라 시간 필요. AI 도구 키워드가 유입의 대부분.
