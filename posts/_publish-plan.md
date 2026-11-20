# 발행 계획 (2026-11-13 선별)

잔여 후보 기준. 단독 = `run.mjs ai-tools [--tool owner/repo]`, 묶음 = `run.mjs ai-tips --min C`.
주의: C등급 도구는 stars 0·분석 폴백이 섞여 있어 `draft: true`/`needsMetadata`가 붙을 수 있다. 그 경우 README 보강 또는 GitHub 재확인 후 진행.

## 단독 글 24편 (점수 순)

| # | 명령 | 도구 | 등급·stars |
|---|------|------|-----------|
| 1 | `run.mjs ai-tools` (1순위 자동) | langgenius/dify | A · 159,948 |
| 2 | `run.mjs ai-tools` | Anil-matcha/Open-Generative-AI | A · 31,826 |
| 3 | `run.mjs ai-tools` | NVIDIA-NeMo/Speech | A · 18,650 |
| 4 | `run.mjs ai-tools` | NVIDIA/SkillSpector | A · 24,541 |
| 5 | `run.mjs ai-tools` | morluto/rea | A · 408,583 |
| 6 | `run.mjs ai-tools` | openclaw/openclaw | A · 393,391 |
| 7 | `run.mjs ai-tools` | obra/superpowers | A · 308,724 |
| 8 | `run.mjs ai-tools` | affaan-m/ECC | A · 292,802 |
| 9 | `run.mjs ai-tools` | deepseek-ai/deepseek-harness | A · 266,031 |
| 10 | `run.mjs ai-tools` | NousResearch/hermes-agent | A · 258,565 |
| 11 | `run.mjs ai-tools` | Significant-Gravitas/AutoGPT | A · 187,822 |
| 12 | `run.mjs ai-tools` | github/spec-kit | A · 148,253 |
| 13 | `run.mjs ai-tools` | TauricResearch/TradingAgents | A · 120,138 |
| 14 | `run.mjs ai-tools` | earendil-works/pi | A · 118,846 |
| 15 | `run.mjs ai-tools` | stablyai/orca | A · 112,018 |
| 16 | `run.mjs ai-tools` | deepseek-ai/DeepSeek-V3 | A · 104,815 |
| 17 | `run.mjs ai-tools` | FlashML-org/FreeToken | A · 16,720 |
| 18 | `run.mjs ai-tools` | heygen-com/hyperframes | A · 80,201 |
| 19 | `run.mjs ai-tools` | anthropics/claude-plugins-official | A · 46,233 |
| 20 | `run.mjs ai-tools` | NirDiamant/GenAI_Agents | A · 24,735 |
| 21 | `run.mjs ai-tools` | deepseek-ai/dsh-superagent-prototype | A · 19,660 |
| 22 | `run.mjs ai-tools` | GoogleCloudPlatform/generative-ai | A · 17,825 |
| 23 | `run.mjs ai-tools --min B` | unclebob/ub-mode | B · 7,217 |
| 24 | `run.mjs ai-tools --min B` | Oldcircle/geo-sleuth | B · 6,152 |

> 1~22는 인자 없이 `run.mjs ai-tools`만 실행하면 선별 1순위가 자동 선택된다. 23~24는 `--tool`로 지정하거나 `--min B` 후 자동 선별(점수 5라 A 소진 후에나 뽑힘).

## 묶음 글 5편 (`run.mjs ai-tips --min C`, 상황당 1편)

| # | 상황 | 도구 3개 |
|---|------|----------|
| 25 | 개발 도구 | emanuele-em/kanzo(C) · vercel-labs/agent-browser(C) · max-sixty/worktrunk(C) |
| 26 | AI 인프라 | NVIDIA/spark-local-inference(C) · adventists-ai/sophon-realtime(C) · JustVugg/colibri(C) |
| 27 | 콘텐츠·창작 | AgriciDaniel/claude-seo(C) · sarpstar/cinecode(C) · ConardLi/garden-skills(C) |
| 28 | 문서·지식 | AienTech/dossier(B) · yjid/kensaku(C) · davemessew/AgentFlux(C) |
| 29 | 금융·법률 | ZhuLinsen/daily_stock_analysis(C) · finic-ai/kairos(C) · shiyu-coder/Kronos(C) |

> `ai-tips`는 상황을 SITUATIONS 순서로 자동 선택하므로 `--min C`로 실행할 때마다 다음 미작성 상황이 만들어진다. 업무·비즈니스·교육·연구는 도구 3개 미만으로 묶음 불가.
> 묶음 도구는 전부 단독 불가 등급이라 단독 글과 겹치지 않는다.
