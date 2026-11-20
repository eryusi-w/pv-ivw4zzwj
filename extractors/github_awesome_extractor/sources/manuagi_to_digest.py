"""ManuAGI 수집 결과(manuagi_repos.json) -> 보강 JSON + ai-tools-archive.html 생성.

산출 정책:
- 지정한 영상 게시 기간의 GitHub 후보를 기존 아카이브에 저장소별로 누적
- 최초 등록일은 유지하고, 용도·주요 기능·분야로 정리
- 중복 저장소는 한 항목으로 병합

파이프라인: manuagi_collector.py -> 본 스크립트
입력:  output/manuagi_repos.json
출력: output/manuagi_repos.enriched.json, output/ai-tools-archive.html
"""
from __future__ import annotations

import json
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import time
from html import escape as html_escape
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_OUTPUT_DIR = _HERE.parent.parent / "output"
_SRC_JSON = _OUTPUT_DIR / "manuagi_repos.json"
_ENRICHED_JSON = _OUTPUT_DIR / "manuagi_repos.enriched.json"
_TARGET_HTML = _OUTPUT_DIR / "ai-tools-archive.html"
_TARGET_TIMEZONE = timezone(timedelta(hours=9), name="KST")

_CODEX_HOME = str(_HERE.parent.parent.parent)
if _CODEX_HOME not in sys.path:
    sys.path.insert(0, _CODEX_HOME)

from dotenv import load_dotenv

load_dotenv()

from github_awesome_extractor.modules import GitHubEnricher  # type: ignore[import-not-found]

# 한글 요약 (원문 영문은 md에 병기)
KO = {
    "public-apis/public-apis": "무료 공개 API 모음집. 개발용 API 카탈로그",
    "mattpocock/skills": "실전 엔지니어용 Agent Skills 모음집",
    "affaan-m/ECC": "에이전트 하네스 성능 최적화 시스템 (스킬·기억·보안 내장)",
    "anomalyco/opencode": "오픈소스 터미널 AI 코딩 에이전트",
    "github/spec-kit": "스펙 기반 개발 입문 툴킷 (Spec-Driven Development)",
    "3b1b/manim": "수학 설명 영상용 애니메이션 엔진",
    "ruvnet/ruflo": "멀티 에이전트 스웜 오케스트레이션 하네스",
    "tt-a1i/archify": "아키텍처 다이어그램 생성 에이전트 스킬",
    "heygen-com/hyperframes": "HTML로 영상을 렌더링하는 에이전트용 영상 프레임워크",
    "blader/humanizer": "AI 생성 티를 지워주는 글쓰기 스킬",
    "ayghri/i-have-adhd": "코딩 에이전트의 장황한 답변을 막는 출력 스킬",
    "Hmbown/Codewhale": "Rust 기반 터미널 코딩 에이전트 (MCP·로컬우선)",
    "llvm/llvm-project": "모듈형 컴파일러·툴체인 기술 모음",
    "volcengine/OpenViking": "에이전트용 자가진화 컨텍스트 DB (메모리+RAG+스킬 통합)",
    "bilawalsidhu/gods-eye-view": "브라우저 위성 시뮬레이터·실시간 공간정보 시각화",
    "dokku/dokku": "도커 기반 셀프호스팅 PaaS (앱 수명주기 관리)",
    "freestylefly/awesome-gpt-image-2": "GPT 이미지 프롬프트 사례·템플릿 모음집 (Prompt as Code)",
    "modular/modular": "MAX·Mojo 포함 모듈러 AI 플랫폼",
    "titanwings/distilly": "사고방식을 증류해 재사용 스킬로 만드는 생성기",
    "pascalorg/editor": "로컬 CLI·MCP 지원 오픈소스 3D 건축 에디터",
    "Tencent/WeKnora": "문서를 RAG·추론 에이전트·위키로 바꾸는 LLM 지식 플랫폼",
    "mksglu/context-mode": "코딩 에이전트 컨텍스트 최적화·세션 메모리 영속화",
    "m1k1o/neko": "도커·WebRTC 셀프호스팅 가상 브라우저",
    "imputnet/helium": "프라이빗·고속 웹 브라우저",
    "google/skills": "구글 제품·기술용 Agent Skills",
    "mlc-ai/web-llm": "브라우저 내 고성능 LLM 추론 엔진",
    "vorssaint/vorssaint-utils": "macOS 메뉴바 유틸리티 모음 (무료·오픈소스)",
    "Sonarr/Sonarr": "뉴스그룹·토렌트용 스마트 PVR",
    "earthtojake/text-to-cad": "CAD·CAE·CAM용 에이전트 스킬 라이브러리",
    "cactus-compute/needle": "14MB 초소형 온디바이스 파운데이션 모델",
    "Abdess/retrobios": "레트로 에뮬레이터용 검증 BIOS·펌웨어 팩",
    "openai/plugins": "OpenAI 플러그인 저장소 (참고·아카이브 성격)",
    "microsoft/aspire": "코드 우선 관측 가능 dev·배포 도구",
    "apache/maka": "작업 전체 기록을 보존하는 고성능 에이전트 워크스페이스",
    "google/artemis": "자연어 지시를 안드로이드 자동화로 바꾸는 테스팅 에이전트",
    "vitali87/code-graph-rag": "모노레포용 코드 그래프 RAG 검색·이해·편집",
    "armory3d/armorpaint": "3D 페인팅·텍스처링 제작 툴",
    "capricorn86/happy-dom": "GUI 없는 JS 브라우저 구현체 (테스트용 DOM)",
    "Tencent/teamai-cli": "팀 AI 네이티브화 CLI",
    "vastsa/PI-Desktop": "로컬우선 AI 코딩 에이전트 데스크톱 (Electron+Rust)",
    "nab138/iloader": "사용 친화적 iOS 사이드로더",
    "jordan-gibbs/hyperresearch": "에이전트 주도 리서치 지식베이스 (수집·검색·합성)",
    "NVIDIA-NeMo/Switchyard": "멀티 모델 라우팅·벤치마킹 게이트웨이 (OpenAI·Anthropic 호환)",
    "alsk1992/CloddsBot": "1000+ 시장 자율운영 AI 트레이딩 에이전트",
    "melgarafael/DeskcommCRM": "AI 에이전트 내장 셀프호스팅 CRM (WhatsApp 연동)",
    "Albert-Weasker/niubigeo": "AI 브랜드 가시성·경쟁사 리포트 (오픈소스)",
    "alphaXiv/OpenResearch": "코딩 에이전트를 리서치 에이전트로 전환",
    "p1neappleXpress/OpenFlux": "플러그형 전송 지원 TCP 터널 네트워크 연구툴",
    "zane-ops/zane-ops": "셀프호스팅 PaaS (웹·DB·정적호스팅·빠른 배포)",
    "huozhi/sugar-high": "초경량 코드 구문 하이라이터",
    "Vincentwei1021/anything2explainer": "주제 입력→내레이션 설명영상 생성 스킬",
    "NxcoreAI/EverRoom": "프로젝트·결정·출처를 기억하는 워크스페이스",
    "gazijarin/itsgiving": "회의용 밈 표현 툴",
    "okf-memory/okf-agent-memory": "Git 네이티브 코딩 에이전트 영속 메모리 (OKF v0.2)",
    "Station-Sciences/bot-crossing": "AI 에이전트가 플레이하는 비디오 게임",
    "yappologistic/Spun": "리눅스용 CD형 로컬 음악 플레이어",
    "jaskirat1616/mactap-app": "맥북 노크로 단축어 실행하는 앱",
    "openshaders/openshaders": "오픈소스 셰이더 공유 허브",
    "noskillish/bankmcp": "은행계좌 읽기 MCP 서버 (셀프호스팅·읽기전용·오픈뱅킹)",
    "blakeshao/kool-brushez": "p5js 브러시 모음",
    "x1xhlol/system-prompts-and-models-of-ai-tools": "여러 AI 개발 도구의 시스템 프롬프트, 내부 도구, 모델 정보를 모은 자료집",
    "wshobson/agents": "Claude Code, Codex, Cursor 등 여러 코딩 에이전트에서 사용하는 플러그인 모음",
    "TauricResearch/TradingAgents": "LLM 기반 멀티 에이전트 금융 거래 프레임워크",
    "Snailclimb/JavaGuide": "Java 면접과 백엔드 개발을 위한 컴퓨터 기초·데이터베이스·시스템 설계 안내서",
    "Significant-Gravitas/AutoGPT": "AI를 활용하고 AI 애플리케이션을 만들도록 돕는 에이전트 도구",
    "Shubhamsaboo/awesome-llm-apps": "AI 에이전트, 스킬, RAG 애플리케이션을 만들기 위한 오픈소스 예제 모음",
    "rohitg00/ai-engineering-from-scratch": "모델 내부 구조와 검색·에이전트 시스템을 직접 구현하며 배우는 AI 엔지니어링 교육 과정",
    "openclaw/openclaw": "운영체제와 플랫폼에 관계없이 다양한 작업을 수행하는 개인용 AI 에이전트",
    "open-webui/open-webui": "Ollama와 OpenAI API 등 여러 모델을 연결해 대화할 수 있는 웹 인터페이스",
    "omnara-ai/omnara": "Claude와 OpenAI 에이전트를 자체 환경에서 운영·관리하는 오픈소스 플랫폼",
    "NousResearch/hermes-agent": "사용자와 함께 적응하며 여러 작업을 수행하는 AI 에이전트",
    "nextlevelbuilder/ui-ux-pro-max-skill": "여러 플랫폼의 UI·UX 설계에 필요한 디자인 지침을 제공하는 에이전트 스킬",
    "n8n-io/n8n": "시각적 흐름과 코드를 결합해 앱·AI 작업을 자동화하는 워크플로 플랫폼",
    "multica-ai/andrej-karpathy-skills": "LLM 코딩 에이전트의 작업 방식을 개선하는 지침을 담은 스킬 파일",
    "msitarzewski/agency-agents": "개발·마케팅·커뮤니티 등 다양한 역할을 수행하는 전문 AI 에이전트 모음",
    "langgenius/dify": "AI 모델과 도구를 연결해 RAG·에이전트 워크플로를 만들고 배포하는 플랫폼",
    "langflow-ai/langflow": "AI 에이전트와 워크플로를 시각적으로 구성하고 배포하는 도구",
    "langchain-ai/langchain": "에이전트 기반 AI 애플리케이션의 개발과 운영을 지원하는 플랫폼",
    "github/spec-kit": "스펙 기반 개발을 시작하고 진행하는 데 필요한 템플릿과 도구 모음",
    "firecrawl/firecrawl": "웹 데이터를 수집·변환해 AI 에이전트와 애플리케이션에서 활용하도록 돕는 도구",
    "feder-cr/git-ai": "AI 에이전트가 함께 작업할 수 있도록 변경 이력과 코드를 관리하는 버전 관리 시스템",
    "f/prompts.chat": "프롬프트를 공유·검색하고 조직 내부에서 자체 운영할 수 있는 오픈소스 카탈로그",
    "deepseek-ai/DeepInfer": "DeepSeek 모델을 대규모 서비스에서 실행하기 위한 고성능 추론 프레임워크",
    "Comfy-Org/ComfyUI": "노드 그래프로 확산 모델을 구성하고 이미지 생성을 실행하는 인터페이스와 API",
    "AUTOMATIC1111/stable-diffusion-webui": "Stable Diffusion 이미지 생성 모델을 브라우저에서 실행하는 웹 인터페이스",
    "ai-job-search-dev/ai-job-search": "공고 분석, 이력서·지원서 맞춤 작성, 면접 준비를 돕는 로컬 AI 구직 도구",
    "AgriciDaniel/claude-seo": "기술 SEO와 콘텐츠 최적화 작업을 수행하는 Claude Code 스킬·에이전트 모음",
    "cloudflare/security-audit-skill": "코딩 에이전트가 단계별 보안 감사를 수행하고 검증된 결과를 구조화해 보고하도록 돕는 스킬",
    "DietrichGebert/ponytail": "불필요한 코드를 줄이고 기존 해법을 우선하도록 코딩 에이전트의 작업 방식을 안내하는 스킬",
    "JuliusBrussee/caveman": "코딩 에이전트의 응답을 짧고 압축된 표현으로 바꿔 토큰 사용량을 줄이는 스킬·프록시",
    "rtk-ai/rtk": "개발 명령의 출력을 정리해 LLM에 전달하는 토큰 절약형 CLI 프록시",
    "headroomlabs-ai/headroom": "도구 출력·로그·파일·RAG 문맥을 압축해 LLM에 전달하는 라이브러리·프록시·MCP 서버",
    "oraios/serena": "MCP로 코드의 의미 검색과 편집을 제공해 코딩 에이전트의 저장소 탐색을 돕는 도구",
    "alexgreensh/token-optimizer": "불필요한 토큰과 컨텍스트 품질 저하 요인을 찾아 에이전트 대화를 정리하는 도구",
    "ZuzooVn/machine-learning-for-software-engineers": "머신러닝 엔지니어가 되기 위한 학습 계획과 단계별 실천 로드맵",
    "VoltAgent/awesome-design-md": "인기 브랜드 디자인 시스템 분석과 코딩 에이전트용 DESIGN.md 모음집",
    "vinitgirdhar/Token-Optimizer": "문서 업로드 시 로컬에서 마크다운으로 변환해 토큰을 아끼는 브라우저 확장",
    "togg53192-cmd/jailbreaks": "주요 LLM 탈옥 프롬프트 모음 및 안전성 평가 데이터셋",
    "thedotmack/claude-mem": "에이전트 세션 간 기억을 압축하고 보존하는 영속 메모리 시스템",
    "tensorflow/tensorflow": "구글의 대표적인 오픈소스 딥러닝·머신러닝 프레임워크",
    "scikit-learn/scikit-learn": "파이썬 데이터 분석 및 고전 머신러닝 표준 라이브러리",
    "pbakaus/impeccable": "코딩 에이전트의 UI 정렬 디테일과 디자인 완성도를 높이는 스킬",
    "openai/codex": "터미널 환경에서 가볍고 빠르게 동작하는 CLI 코딩 에이전트",
    "ooples/token-optimizer-mcp": "에이전트 간 토큰 절감률을 측정하고 로컬 지식 그래프를 공유하는 MCP 서버",
    "ollama/ollama": "오픈소스 LLM을 로컬 컴퓨터에서 명령어 한 줄로 구동하는 도구",
    "NVIDIA-NeMo/Speech": "엔비디아의 대규모 음성 인식(ASR) 및 음성 합성(TTS) AI 프레임워크",
    "Nutlope/hallmark": "모던 웹 랜딩페이지와 UI 컴포넌트를 빠르게 생성하는 디자인 도구",
    "NirDiamant/GenAI_Agents": "기초 챗봇부터 멀티 에이전트·RAG까지 50개 이상의 실전 튜토리얼 모음집",
    "nightly-labs/openbot": "로컬 환경에서 지속 협업하는 상주형 AI 팀원 운영 데스크톱 워크스페이스",
    "nadimtuhin/claude-token-optimizer": "Claude Code 세션 시작 시 시스템 프롬프트를 압축해 초기 토큰을 아끼는 CLI",
    "Motionsites-AI/claude-skill": "웹사이트 모션 효과와 인터랙티브 애니메이션 코딩을 돕는 Claude 전용 스킬",
    "morluto/rea": "바이너리, 번들, 앱 동작을 에이전트로 분석·복원하는 리버스 엔지니어링 도구",
    "mlabonne/llm-course": "LLM 기초부터 파인튜닝, RAG, 양자화까지 단계별로 완주하는 오픈소스 로드맵",
    "milind-soni/OpenMausBot": "가상 머신 샌드박스에서 브라우저와 터미널을 자율 제어하는 오픈소스 에이전트",
    "microsoft/ML-For-Beginners": "12주 26개 레슨과 퀴즈로 배우는 마이크로소프트의 머신러닝 입문 코스",
    "microsoft/generative-ai-for-beginners": "21개 레슨으로 배우는 마이크로소프트의 생성형 AI 및 LLM 앱 개발 과정",
    "macro-inc/macro": "이메일, 채팅, 문서, 태스크를 통합해 AI와 함께 일하는 팀 워크스페이스",
    "Leonxlnx/taste-skill": "코딩 에이전트에게 시각적 감각(Art Direction)과 세련된 UI 스타일을 주입하는 스킬",
    "l0ng-ai/openidea": "자연어 대화로 프로젝트 아이디어를 구체화하고 스펙 초안을 잡아주는 기획 도구",
    "kittimasak/thai-token-optimizer": "다국어 텍스트 처리 시 토크나이저 분절을 최적화해 토큰을 절감하는 도구",
    "KINGSTAR-OMEGA/claude-token-optimizer": "Claude CLI 세션의 컨텍스트를 구조적으로 경량화해 비용을 줄이는 고효율 스킬",
    "josephmisiti/awesome-machine-learning": "언어별 머신러닝 프레임워크와 도구를 총망라한 오픈소스 큐레이션",
    "JetBrains/thinkrail": "가벼운 실제 IDE 환경에서 Pi 에이전트와 함께 개발하는 바이브 코딩 환경",
    "jakubkrehel/skills": "뛰어난 웹 인터페이스와 사용자 경험을 구축하도록 돕는 실전 프론트엔드 스킬",
    "ifixai-ai/iFixAi": "에러 로그를 분석해 자동으로 원인을 규명하고 패치를 제안하는 자율 디버깅 도구",
    "hugohe3/ppt-master": "문서나 주제 키워드를 입력하면 네이티브 파워포인트(PPTX)로 자동 변환하는 AI 도구",
    "huggingface/transformers": "수만 개의 최신 사전학습 트랜스포머 모델을 다운로드하고 추론하는 표준 라이브러리",
    "HKUDS/DeepTutor": "PDF 교재나 전공 서적을 바탕으로 개인 맞춤형 과외와 퀴즈를 제공하는 홍콩대 AI 튜터",
    "Graphify-Labs/graphify": "비정형 문서와 텍스트를 의미 기반의 지식 그래프(Knowledge Graph)로 자동 변환하는 도구",
    "gradio-app/gradio": "몇 줄의 파이썬 코드로 머신러닝 모델의 대화형 웹 데모 UI를 생성하는 프레임워크",
    "GoogleCloudPlatform/generative-ai": "구글 클라우드 환경에서 Gemini 및 Vertex AI를 활용하는 공식 샘플 코드",
    "fighting41love/funNLP": "감성 분석, 민감어 필터링, 개체명 인식 등 100여 개 이상의 NLP 처리 도구 모음",
    "farion1231/cc-switch": "Claude Code, Codex, OpenCode 등 다중 코딩 도구 설정을 전환하는 올인원 데스크톱 앱",
    "elayadesign/ai-design-skills": "깃허브 트렌딩 1위 실전 디자인 시스템 가이드라인과 코딩 에이전트용 디자인 스킬",
    "earendil-works/pi": "통합 LLM API, 에이전트 루프, 인터랙티브 TUI를 갖춘 완성형 AI 에이전트 툴킷",
    "Donchitos/Claude-Code-Game-Studios": "49개 전문 AI 에이전트와 72개 스킬로 실제 게임 개발 스튜디오 조직을 구현한 시스템",
    "deepseek-ai/DeepSeek-V3": "고효율 MoE 아키텍처와 뛰어난 추론 능력을 갖춘 오픈소스 플래그십 LLM",
    "deepseek-ai/deepseek-harness": "모든 구성요소를 플러그인 형태로 조립해 확장하는 DeepSeek 전용 에이전트 하네스",
    "cheaper-inference/OmniRoute": "375개 공급자 1,400개 모델을 하나로 묶고 자동 쿼터 폴백을 제공하는 무료 AI 게이트웨이",
    "bytedance/deer-flow": "샌드박스와 장기 기억을 갖추고 몇 시간 단위의 심층 조사를 완수하는 바이트댄스 슈퍼에이전트",
    "ASK-Ai-Canada/ASK-Claude-Token-Optimizer": "Claude Code CLI의 불필요한 입출력을 정제해 토큰을 최대 98.9% 절감하는 최적화 도구",
    "Anil-matcha/Open-Generative-AI": "600개 이상의 모델을 검열 없이 실행할 수 있는 오픈소스 생성형 이미지·영상 스튜디오",
    "andrewyng/aisuite": "코드 변경 없이 공급자 이름만 바꿔 여러 LLM을 호출하는 앤드류 응 교수의 경량 SDK",
    "akitaonrails/ai-memory": "코딩 에이전트의 이전 작업 컨텍스트와 결정 사항을 세션 종료 후에도 영속화하는 라이브러리",
    "aishwaryanr/awesome-generative-ai-guide": "생성형 AI 연구 동향, 면접 예상 질문, 실습 노트북을 모은 원스톱 가이드",
    "addyosmani/agent-skills": "구글 크롬 엔지니어링 리드 애디 오스마니가 공개한 실무용 AI 코딩 에이전트 스킬",
    "remotion-dev/skills": "React 코드로 영상을 렌더링하고 제작하는 Remotion 전용 에이전트 스킬",
    "fastapi/fastapi": "파이썬 타입 힌트를 기반으로 빠르고 직관적인 API를 구축하는 현대적 웹 프레임워크",
    "android/skills": "안드로이드 앱 개발 및 테스트 자동화를 위한 전용 에이전트 스킬",
    "pingdotgg/t3code": "T3 스택 기반의 풀스택 웹 개발 및 실무 코딩 에이전트 도구",
    "chrisryugj/kordoc": "HWP 및 HWPX 공문서 서식 파싱과 텍스트 자동 추출 도구",
    "edwardkim/rhwp": "Rust로 작성된 고성능 HWP/HWPX 문서 파서 및 변환기",
    "Canine89/hwpxskill": "공문서 HWPX 서식 채우기 및 문서 작성을 돕는 AI 에이전트 스킬",
    "DoHyun468/claw-hwp": "한글(HWP) 문서의 본문과 표 데이터를 구조화해 다루는 오픈소스 도구",
    "airmang/python-hwpx": "파이썬 환경에서 HWPX 문서 생성 및 서식을 프로그래밍하는 라이브러리",
    "wheresryan22/anatomy": "소프트웨어 아키텍처와 시스템 원리를 직관적인 다이어그램 그림으로 해부해주는 스킬",
    "cursor/plugins": "Cursor 에디터 환경에서 에이전트 동작과 도구를 확장하는 공식 플러그인 모음",
    "stablyai/orca": "웹·모바일 서비스의 E2E 테스트와 QA를 자동화하는 오픈소스 AI 테스팅 에이전트",
    "obra/superpowers": "코딩 에이전트에게 쉘 실행, 웹 검색, 시스템 제어 권한을 부여하는 확장 도구",
    "featherless-ai/simple-jev": "브라우저 및 로컬 환경에서 가볍게 동작하는 경량 자율 AI 에이전트 구현체",
    "davidmokos/expo-gpt-live": "React Native(Expo) 환경에서 OpenAI Realtime 음성 API를 연동한 모바일 라이브 챗",
    "CopilotKit/OpenBot": "웹 애플리케이션 내부에 바로 삽입할 수 있는 오픈소스 인앱 AI 어시스턴트 프레임워크",
}

FEATS = {
    "anomalyco/opencode": ["터미널 기반 코딩 에이전트", "오픈소스", "다양한 모델 연동"],
    "Hmbown/Codewhale": ["Rust 기반 터미널 에이전트", "MCP 지원", "로컬우선·커뮤니티 개선"],
    "volcengine/OpenViking": ["Agent Memory 통합", "Knowledge RAG", "자가진화 컨텍스트 DB"],
    "mksglu/context-mode": ["툴 출력 98% 절감 샌드박스", "세션 메모리 영속화", "MCP+훅 17개 플랫폼 라우팅"],
    "okf-memory/okf-agent-memory": ["Git 네이티브 영속 메모리", "BM25 초고속 인메모리 검색", "외부 DB 없이 토큰 80% 절감"],
    "cloudflare/security-audit-skill": ["단계별 저장소 보안 감사", "별도 검증 에이전트", "기계 판독 가능한 감사 결과"],
    "DietrichGebert/ponytail": ["불필요한 코드 작성 억제", "기존 코드 재사용 우선", "간결한 코딩 에이전트 지침"],
    "JuliusBrussee/caveman": ["에이전트 응답 압축", "코딩 에이전트용 스킬·프록시", "토큰 사용량 절감"],
    "rtk-ai/rtk": ["개발 CLI 출력 정리", "LLM 토큰 소비 절감", "Rust 단일 실행 파일"],
    "headroomlabs-ai/headroom": ["도구 출력·로그 압축", "JSON·RAG 문맥 최적화", "라이브러리·프록시·MCP 제공"],
    "oraios/serena": ["코드 의미 기반 검색", "심볼 단위 코드 편집", "MCP 기반 코딩 에이전트 연동"],
    "alexgreensh/token-optimizer": ["불필요한 토큰 진단", "컨텍스트 압축 상태 점검", "대화 품질 저하 방지"],
    "VoltAgent/awesome-design-md": ["DESIGN.md 템플릿", "디자인 시스템 가이드", "바이브 코딩 UI"],
    "vinitgirdhar/Token-Optimizer": ["로컬 마크다운 변환", "문서 파일 압축", "브라우저 확장"],
    "togg53192-cmd/jailbreaks": ["탈옥 프롬프트 분석", "LLM 안전성 연구", "레드팀 테스트"],
    "thedotmack/claude-mem": ["세션 간 메모리 영속화", "컨텍스트 자동 압축", "다중 에이전트 지원"],
    "tensorflow/tensorflow": ["딥러닝 프레임워크", "분산 학습 지원", "엔드투엔드 ML"],
    "TauricResearch/TradingAgents": ["멀티 에이전트 트레이딩", "금융 데이터 분석", "알고리즘 전략"],
    "Snailclimb/JavaGuide": ["Java 백엔드 핵심 요약", "분산 시스템 설계", "AI 응용 개발 가이드"],
    "Significant-Gravitas/AutoGPT": ["자율형 AI 에이전트", "도구 실행 루프", "목표 지향 워크플로"],
    "scikit-learn/scikit-learn": ["전통 머신러닝 알고리즘", "데이터 전처리 파이프라인", "모델 평가 지표"],
    "pbakaus/impeccable": ["UI 디테일 튜닝", "디자인 품질 검증", "에이전트 스타일링 스킬"],
    "openclaw/openclaw": ["크로스플랫폼 에이전트", "로컬 데이터 통제", "자동화 태스크 수행"],
    "openai/codex": ["터미널 코딩 에이전트", "경량 실행", "CLI 인터랙션"],
    "open-webui/open-webui": ["Ollama/API 통합 지원", "RAG 내장", "역할 및 사용자 권한 관리"],
    "ooples/token-optimizer-mcp": ["MCP 서버", "토큰 절감 측정", "로컬 지식 그래프 연동"],
    "ollama/ollama": ["원클릭 로컬 LLM 실행", "OpenAI 호환 API", "GPU 가속 지원"],
    "NVIDIA-NeMo/Speech": ["음성 인식(ASR)", "음성 합성(TTS)", "엔비디아 GPU 가속"],
    "Nutlope/hallmark": ["모던 웹 UI 템플릿", "랜딩페이지 생성", "디자인 프로토타이핑"],
    "NousResearch/hermes-agent": ["자가 적응형 에이전트", "추론 능력 강화", "오픈소스 프레임워크"],
    "NirDiamant/GenAI_Agents": ["50+ 에이전트 튜토리얼", "LangGraph/MCP 구현체", "실전 RAG 패턴"],
    "nightly-labs/openbot": ["로컬 우선 워크스페이스", "상주형 AI 팀원", "데스크톱 앱"],
    "nadimtuhin/claude-token-optimizer": ["Claude Code 토큰 최적화", "세션 시작 비용 절감", "CLI 도구"],
    "multica-ai/andrej-karpathy-skills": ["카파시 개발 규칙", "신중한 리팩토링 지침", "에이전트 판단력 개선"],
    "Motionsites-AI/claude-skill": ["모션 인터랙션 스킬", "CSS/JS 애니메이션", "Claude 전용 확장"],
    "morluto/rea": ["바이너리/앱 역공학", "에이전트 기반 분석", "정적/동적 구조 추적"],
    "mlabonne/llm-course": ["LLM 학습 로드맵", "실습용 주피터 노트북", "파인튜닝·양자화 가이드"],
    "milind-soni/OpenMausBot": ["VM 기반 샌드박스", "브라우저 자율 제어", "터미널 자동화"],
    "microsoft/ML-For-Beginners": ["12주 26강 커리큘럼", "MS 공식 교육 자료", "입문자 맞춤형 실습"],
    "microsoft/generative-ai-for-beginners": ["21강 생성형 AI 코스", "RAG 및 에이전트 기초", "실습 프로젝트 포함"],
    "macro-inc/macro": ["통합 업무 워크스페이스", "팀 커뮤니케이션", "AI 협업 지원"],
    "Leonxlnx/taste-skill": ["디자인 감각(Taste) 주입", "고품질 UI 가이드", "에이전트 스타일 프리셋"],
    "langgenius/dify": ["노드 기반 비주얼 빌더", "강력한 RAG 파이프라인", "엔터프라이즈 권한 관리"],
    "l0ng-ai/openidea": ["아이디어 구조화", "아키텍처 브레인스토밍", "프로젝트 스펙 초안"],
    "kittimasak/thai-token-optimizer": ["다국어 토큰 최적화", "토크나이저 효율화", "프롬프트 경량화"],
    "KINGSTAR-OMEGA/claude-token-optimizer": ["Claude 전용 토큰 절감", "컨텍스트 정리 스킬", "세션 비용 최적화"],
    "josephmisiti/awesome-machine-learning": ["언어별 ML 프레임워크 큐레이션", "데이터셋 및 도구 목록", "글로벌 인기 자료집"],
    "JetBrains/thinkrail": ["경량 IDE 환경", "Pi 에이전트 내장", "바이브 코딩 최적화"],
    "jakubkrehel/skills": ["프론트엔드 UX 스킬", "컴포넌트 설계 규칙", "인터페이스 최적화"],
    "ifixai-ai/iFixAi": ["자동 버그 진단", "에러 로그 분석", "패치 코드 자동 생성"],
    "hugohe3/ppt-master": ["문서→PPT 자동 생성", "네이티브 PPTX 출력", "레이아웃 자동 디자인"],
    "huggingface/transformers": ["수천 개 사전학습 모델 허브", "PyTorch/TF 지원", "간결한 파이프라인 API"],
    "HKUDS/DeepTutor": ["PDF 기반 과외 에이전트", "지식 개념 맞춤 설명", "이해도 점검 퀴즈"],
    "Graphify-Labs/graphify": ["비정형 문서 지식그래프화", "Graph RAG 연동", "엔티티 관계 시각화"],
    "gradio-app/gradio": ["파이썬 기반 빠른 웹 UI", "원클릭 공유 링크", "다양한 입출력 컴포넌트"],
    "GoogleCloudPlatform/generative-ai": ["구글 공식 Gemini 예제", "Vertex AI RAG 구현체", "실전 아키텍처 가이드"],
    "firecrawl/firecrawl": ["JS 렌더링 웹 크롤링", "클린 마크다운 변환", "LLM 맞춤형 API"],
    "fighting41love/funNLP": ["100+ NLP 도구 및 리소스", "텍스트 전처리/정제", "언어 분석 데이터셋"],
    "farion1231/cc-switch": ["크로스플랫폼 데스크톱 GUI", "다중 코딩 도구 통합 관리", "스킬 원클릭 전환"],
    "elayadesign/ai-design-skills": ["디자인 시스템 지침", "트렌딩 UI 스타일 가이드", "에이전트 전용 프론트 스킬"],
    "earendil-works/pi": ["초경량 에이전트 루프", "인터랙티브 TUI", "다양한 모델 프로바이더 연동"],
    "Donchitos/Claude-Code-Game-Studios": ["49개 전문 게임 에이전트", "실제 스튜디오 조직 구조", "72개 게임 워크플로 스킬"],
    "deepseek-ai/DeepSeek-V3": ["고효율 MoE 아키텍처", "우수한 코딩·수학 추론력", "완전 오픈 가중치 제공"],
    "deepseek-ai/deepseek-harness": ["플러그인 기반 아키텍처", "DeepSeek 전용 에이전트 하네스", "모듈형 도구 통합"],
    "cheaper-inference/OmniRoute": ["단일 엔드포인트 멀티 모델 라우팅", "자동 쿼터 폴백", "최대 95% 토큰 압축 내장"],
    "bytedance/deer-flow": ["장기 실행(Long-horizon) 에이전트", "샌드박스 및 서브에이전트", "심층 리서치 워크플로"],
    "ASK-Ai-Canada/ASK-Claude-Token-Optimizer": ["최대 98.9% 토큰 절감", "Claude Code CLI 최적화", "컨텍스트 정리"],
    "Anil-matcha/Open-Generative-AI": ["600+ 이미지/영상 모델 지원", "자체 호스팅 가능", "무검열 생성형 미디어 스튜디오"],
    "andrewyng/aisuite": ["통일된 다중 공급자 인터페이스", "간결한 문법", "코드 변경 없는 모델 전환"],
    "akitaonrails/ai-memory": ["에이전트 결정 사항 영속화", "프로젝트 기억 관리", "세션 간 지식 유지"],
    "aishwaryanr/awesome-generative-ai-guide": ["생성형 AI 기술 로드맵", "인터뷰 예상 질문 및 해설", "실습 주피터 노트북"],
    "AgriciDaniel/claude-seo": ["테크니컬 SEO 진단", "Claude Code 전용 스킬", "콘텐츠 및 메타태그 최적화"],
    "addyosmani/agent-skills": ["프로덕션 엔지니어링 스킬", "실무 코드 품질 지침", "Claude Code·Codex·Cursor 호환"],
    "remotion-dev/skills": ["React 기반 비디오 렌더링", "프로그래밍 방식 영상 제작", "에이전트 스킬"],
    "fastapi/fastapi": ["고성능 파이썬 웹 프레임워크", "자동 OpenAPI 문서화", "비동기 ASGI 지원"],
    "android/skills": ["안드로이드 앱 개발 자동화", "UI 테스트 에이전트", "SDK 연동 스킬"],
    "pingdotgg/t3code": ["T3 풀스택 코딩 에이전트", "Next.js 및 TypeScript 지원", "실무 개발 보조"],
    "chrisryugj/kordoc": ["HWP/HWPX 공문서 파싱", "텍스트 자동 추출", "서식 데이터 정제"],
    "edwardkim/rhwp": ["Rust 기반 고속 HWP 파서", "대용량 한글 문서 처리", "CLI 및 라이브러리 제공"],
    "Canine89/hwpxskill": ["HWPX 공문서 서식 자동화", "한글 표/본문 채우기", "에이전트 문서 스킬"],
    "DoHyun468/claw-hwp": ["HWP 문서 본문/표 추출", "구조화 데이터 변환", "문서 자동화 툴"],
    "airmang/python-hwpx": ["파이썬 HWPX 생성/편집", "스타일 및 서식 프로그래밍", "오픈소스 라이브러리"],
    "wheresryan22/anatomy": ["아키텍처 그림 다이어그램", "소프트웨어 구조 해부", "에이전트 시각화 스킬"],
    "cursor/plugins": ["Cursor 에이전트 확장", "개발 도구 플러그인 모음", "워크플로 맞춤화"],
    "stablyai/orca": ["AI QA 에이전트", "E2E 테스트 자동화", "버그 자동 탐지"],
    "obra/superpowers": ["에이전트 권한 확장", "도구 실행 라이브러리", "시스템 자동화"],
    "featherless-ai/simple-jev": ["경량 자율 에이전트", "로컬 인터랙션", "미니멀 루프"],
    "davidmokos/expo-gpt-live": ["Expo/React Native", "OpenAI Realtime API", "초저지연 음성 대화"],
    "CopilotKit/OpenBot": ["인앱 AI 어시스턴트", "React/Next.js 지원", "오픈소스 프레임워크"],
}

# 추천 용도 (한 줄)
USECASE = {
    "public-apis/public-apis": "무료 공개 API 찾을 때",
    "mattpocock/skills": "Agent Skills 작성 참고용",
    "affaan-m/ECC": "에이전트 하네스 성능 튜닝용",
    "anomalyco/opencode": "터미널에서 AI 코딩할 때",
    "github/spec-kit": "스펙 기반 개발 도입용",
    "3b1b/manim": "수학 설명 영상 제작용",
    "ruvnet/ruflo": "멀티 에이전트 운영용",
    "tt-a1i/archify": "아키텍처 문서 다이어그램용",
    "heygen-com/hyperframes": "에이전트 영상 자동 생성용",
    "blader/humanizer": "AI 티 나는 글 다듬기용",
    "ayghri/i-have-adhd": "에이전트 답변 간결화용",
    "Hmbown/Codewhale": "터미널에서 AI 코딩할 때",
    "llvm/llvm-project": "컴파일러·툴체인 개발용",
    "volcengine/OpenViking": "에이전트 기억·지식 통합용",
    "bilawalsidhu/gods-eye-view": "공간정보 시각화·학습용",
    "dokku/dokku": "저비용 셀프호스팅 배포용",
    "freestylefly/awesome-gpt-image-2": "이미지 프롬프트 레퍼런스용",
    "modular/modular": "고성능 AI 추론·Mojo 개발용",
    "titanwings/distilly": "노하우 스킬화용",
    "pascalorg/editor": "건축 3D 설계·AI 협업용",
    "Tencent/WeKnora": "문서 RAG 지식베이스 구축용",
    "mksglu/context-mode": "코딩 에이전트 토큰 절감용",
    "m1k1o/neko": "원격 브라우저·협업 시청용",
    "imputnet/helium": "프라이버시 중시 브라우징용",
    "google/skills": "구글 연동 에이전트 개발용",
    "mlc-ai/web-llm": "브라우저 내 AI 실행용",
    "vorssaint/vorssaint-utils": "macOS 생산성 향상용",
    "Sonarr/Sonarr": "미디어 자동 수집용",
    "earthtojake/text-to-cad": "CAD 자동화용",
    "cactus-compute/needle": "초소형 기기 AI 탑재용",
    "Abdess/retrobios": "레트로 게임 환경 구축용",
    "openai/plugins": "플러그인 구조 참고용",
    "microsoft/aspire": "분산앱 개발·배포 관측용",
    "apache/maka": "에이전트 작업 감사·재현용",
    "google/artemis": "안드로이드 테스트 자동화용",
    "vitali87/code-graph-rag": "대형 코드베이스 이해·검색용",
    "armory3d/armorpaint": "3D 텍스처 제작용",
    "capricorn86/happy-dom": "프론트 테스트 DOM용",
    "Tencent/teamai-cli": "팀 AI 도입용",
    "vastsa/PI-Desktop": "데스크톱 AI 코딩용",
    "nab138/iloader": "iOS 사이드로딩용",
    "jordan-gibbs/hyperresearch": "리서치 자동 수집·정리용",
    "NVIDIA-NeMo/Switchyard": "멀티 모델 비용 최적화용",
    "alsk1992/CloddsBot": "자동매매 연구용 (투자 주의)",
    "melgarafael/DeskcommCRM": "채팅 영업 CRM 구축용",
    "Albert-Weasker/niubigeo": "브랜드 AI 노출 진단용",
    "alphaXiv/OpenResearch": "리서치 에이전트 구축용",
    "p1neappleXpress/OpenFlux": "네트워크 터널 연구용",
    "zane-ops/zane-ops": "셀프호스팅 배포용",
    "huozhi/sugar-high": "코드 하이라이팅용",
    "Vincentwei1021/anything2explainer": "설명 영상 자동 제작용",
    "NxcoreAI/EverRoom": "프로젝트 지식 관리용",
    "gazijarin/itsgiving": "회의 분위기 전환용",
    "okf-memory/okf-agent-memory": "코딩 에이전트 기억 영속화용",
    "Station-Sciences/bot-crossing": "에이전트 행동 실험용",
    "yappologistic/Spun": "리눅스 음악 감상용",
    "jaskirat1616/mactap-app": "맥북 단축어 실행용",
    "openshaders/openshaders": "셰이더 학습·공유용",
    "noskillish/bankmcp": "가계부 AI 연동용",
    "blakeshao/kool-brushez": "p5js 드로잉용",
    "cloudflare/security-audit-skill": "AI 코딩 에이전트로 저장소 보안 감사를 수행할 때",
    "DietrichGebert/ponytail": "코딩 에이전트가 과도한 설계나 불필요한 코드를 만들지 않게 하고 싶을 때",
    "JuliusBrussee/caveman": "코딩 에이전트의 토큰 사용량을 줄이고 응답을 간결하게 만들 때",
    "rtk-ai/rtk": "에이전트가 실행한 개발 명령의 긴 출력을 줄여 모델 입력을 아끼고 싶을 때",
    "headroomlabs-ai/headroom": "도구·로그·파일 정보를 LLM에 전달하기 전에 압축하고 싶을 때",
    "oraios/serena": "코딩 에이전트가 큰 저장소의 코드를 검색하고 편집하도록 지원할 때",
    "alexgreensh/token-optimizer": "토큰 낭비와 컨텍스트 품질 저하를 진단하고 싶을 때",
    "ZuzooVn/machine-learning-for-software-engineers": "머신러닝 엔지니어가 되기 위한 학습 계획을 따라 공부할 때",
    "VoltAgent/awesome-design-md": "코딩 에이전트에 브랜드 디자인 시스템 지침을 제공할 때",
    "vinitgirdhar/Token-Optimizer": "문서 파일 첨부 시 로컬 마크다운 변환으로 토큰을 아낄 때",
    "togg53192-cmd/jailbreaks": "LLM 모델의 안전성 한계 및 레드팀 프롬프트 테스트 연구용",
    "thedotmack/claude-mem": "에이전트의 세션 간 작업 맥락과 기억을 유지할 때",
    "tensorflow/tensorflow": "대규모 딥러닝 신경망 모델을 구축하고 분산 학습할 때",
    "TauricResearch/TradingAgents": "멀티 AI 에이전트로 금융 시장 데이터와 거래 전략을 분석할 때",
    "Snailclimb/JavaGuide": "Java 백엔드 아키텍처 학습 및 AI 연동 백엔드 설계 참고용",
    "Significant-Gravitas/AutoGPT": "자율형 AI 에이전트에게 복잡한 목표를 스스로 수행하게 할 때",
    "scikit-learn/scikit-learn": "파이썬에서 분류·회귀 등 전통 머신러닝 알고리즘을 적용할 때",
    "pbakaus/impeccable": "에이전트가 만든 웹 UI의 타이포그래피와 디테일을 다듬을 때",
    "openclaw/openclaw": "개인 데이터를 직접 통제하며 OS 전반의 작업을 AI에 위임할 때",
    "openai/codex": "터미널에서 가볍고 빠르게 코드 생성과 수정을 요청할 때",
    "open-webui/open-webui": "로컬 및 클라우드 LLM을 웹 브라우저 채팅 UI로 사용할 때",
    "ooples/token-optimizer-mcp": "여러 에이전트의 중복 컨텍스트를 MCP로 공유해 토큰을 아낄 때",
    "ollama/ollama": "내 컴퓨터에서 로컬 오픈소스 LLM을 무료로 실행하고 API로 호출할 때",
    "NVIDIA-NeMo/Speech": "고성능 음성 인식(ASR) 및 음성 합성(TTS) 모델을 구축할 때",
    "Nutlope/hallmark": "모던 웹 랜딩페이지 컴포넌트를 빠르게 프로토타이핑할 때",
    "NousResearch/hermes-agent": "지속적으로 학습하고 발전하는 적응형 에이전트를 구축할 때",
    "NirDiamant/GenAI_Agents": "LangGraph와 MCP 기반의 최신 멀티 에이전트 패턴을 학습할 때",
    "nightly-labs/openbot": "로컬 데스크톱에서 상주형 AI 팀원을 두고 협업할 때",
    "nadimtuhin/claude-token-optimizer": "Claude Code 시작 시 소모되는 시스템 프롬프트 토큰을 절약할 때",
    "multica-ai/andrej-karpathy-skills": "코딩 에이전트의 과도한 코드 생성이나 성급한 결정을 제어할 때",
    "Motionsites-AI/claude-skill": "웹사이트의 화려한 인터랙션 효과와 모션 애니메이션을 코딩할 때",
    "morluto/rea": "바이너리나 미지의 앱 구조를 에이전트로 분석·역공학할 때",
    "mlabonne/llm-course": "LLM 내부 동작 원리와 파인튜닝 실무 기술을 공부할 때",
    "milind-soni/OpenMausBot": "격리된 VM 샌드박스에서 AI에게 브라우징과 터미널 제어를 맡길 때",
    "microsoft/ML-For-Beginners": "데이터 과학과 기초 머신러닝을 체계적인 커리큘럼으로 입문할 때",
    "microsoft/generative-ai-for-beginners": "프롬프트 엔지니어링부터 RAG·에이전트 구축 기초를 실습할 때",
    "macro-inc/macro": "이메일·채팅·문서를 통합해 AI 지원 워크플로를 팀에 도입할 때",
    "Leonxlnx/taste-skill": "코딩 에이전트가 트렌디하고 세련된 고품질 UI를 디자인하게 할 때",
    "langgenius/dify": "드래그 앤 드롭으로 RAG 챗봇과 AI 에이전트 서비스를 만들 때",
    "l0ng-ai/openidea": "새 프로젝트 기획 시 아이디어를 구조화하고 스펙 초안을 잡을 때",
    "kittimasak/thai-token-optimizer": "다국어 텍스트 처리 시 토크나이저 분절을 최적화해 토큰을 아낄 때",
    "KINGSTAR-OMEGA/claude-token-optimizer": "긴 코딩 세션에서 Claude 컨텍스트 한도 도달과 비용 증가를 막을 때",
    "josephmisiti/awesome-machine-learning": "언어와 도메인에 맞는 머신러닝 라이브러리를 비교·탐색할 때",
    "JetBrains/thinkrail": "에이전트 중심의 가볍고 민첩한 바이브 코딩 환경을 꾸밀 때",
    "jakubkrehel/skills": "프론트엔드 UI 컴포넌트의 완성도와 UX 디테일을 높일 때",
    "ifixai-ai/iFixAi": "런타임 오류 로그를 바탕으로 신속하게 버그 패치를 생성할 때",
    "hugohe3/ppt-master": "문서나 기획안을 전문적인 발표용 파워포인트 슬라이드로 변환할 때",
    "huggingface/transformers": "사전학습된 최첨단 트랜스포머 신경망 모델을 다운로드해 추론할 때",
    "HKUDS/DeepTutor": "두꺼운 전공 서적이나 자격증 PDF를 넣고 개인 맞춤형 AI 과외를 받을 때",
    "Graphify-Labs/graphify": "비정형 문서를 지식 그래프로 변환하고 Graph RAG를 구축할 때",
    "gradio-app/gradio": "머신러닝 모델의 대화형 웹 데모 UI를 파이썬으로 빠르게 만들 때",
    "GoogleCloudPlatform/generative-ai": "엔터프라이즈 환경에서 구글 Gemini API와 Vertex AI 솔루션을 구현할 때",
    "firecrawl/firecrawl": "웹사이트 내용을 AI 에이전트가 읽기 쉬운 클린 마크다운으로 긁어올 때",
    "fighting41love/funNLP": "텍스트 전처리, 감성 분석, 민감어 마스킹 등 자연어 처리를 수행할 때",
    "farion1231/cc-switch": "여러 AI 코딩 도구의 모델과 스킬 설정을 GUI에서 원클릭 전환할 때",
    "elayadesign/ai-design-skills": "코딩 에이전트가 최신 디자인 시스템과 레이아웃 규칙에 맞춰 개발할 때",
    "earendil-works/pi": "터미널에서 가볍고 강력한 TUI 코딩 보조 에이전트를 운영할 때",
    "Donchitos/Claude-Code-Game-Studios": "게임 기획부터 프로그래밍까지 전 과정을 전문 AI 팀에 분업시킬 때",
    "deepseek-ai/DeepSeek-V3": "오픈소스 최상위 성능의 코딩·추론 모델을 자체 인프라에서 구동할 때",
    "deepseek-ai/deepseek-harness": "DeepSeek 모델에 도구·메모리·검색을 플러그인 방식으로 결합할 때",
    "cheaper-inference/OmniRoute": "비용 최적화 및 쿼터 폴백으로 중단 없는 AI 코딩 환경을 구축할 때",
    "bytedance/deer-flow": "장시간 동안 자율적인 다단계 심층 조사와 코드 작성을 위임할 때",
    "ASK-Ai-Canada/ASK-Claude-Token-Optimizer": "Claude Code 사용 시 발생하는 토큰 비용을 최소화하고 싶을 때",
    "Anil-matcha/Open-Generative-AI": "자체 환경에서 무검열로 고품질 AI 이미지와 영상을 생성할 때",
    "andrewyng/aisuite": "파이썬 코드 변경 없이 여러 LLM 공급자 모델을 쉽게 교체·테스트할 때",
    "akitaonrails/ai-memory": "프로젝트 변경 이력과 의사결정 맥락을 에이전트가 영구 기억하게 할 때",
    "aishwaryanr/awesome-generative-ai-guide": "생성형 AI 기술 로드맵과 엔지니어 면접 자료를 체계적으로 공부할 때",
    "AgriciDaniel/claude-seo": "웹사이트 개발 중 테크니컬 SEO와 검색 최적화를 AI로 자동 점검할 때",
    "addyosmani/agent-skills": "코딩 에이전트에게 실무 수준의 아키텍처 설계와 코드 리뷰 능력을 줄 때",
    "remotion-dev/skills": "React 코드로 프로그래밍 방식의 영상을 자동 렌더링·제작할 때",
    "fastapi/fastapi": "파이썬으로 빠르고 현대적인 고성능 RESTful API를 구축할 때",
    "android/skills": "안드로이드 앱 개발 워크플로와 UI 테스트를 에이전트로 자동화할 때",
    "pingdotgg/t3code": "풀스택 웹 애플리케이션 개발 시 실무형 코딩 에이전트를 활용할 때",
    "chrisryugj/kordoc": "한글 공문서(HWP/HWPX)의 텍스트와 서식을 자동 추출·처리할 때",
    "edwardkim/rhwp": "대용량 HWP 한글 문서를 초고속으로 파싱하고 텍스트를 변환할 때",
    "Canine89/hwpxskill": "HWPX 양식 문서를 AI 에이전트로 자동 작성하고 서식을 맞출 때",
    "DoHyun468/claw-hwp": "HWP 문서의 표와 본문 데이터를 구조화하여 업무를 자동화할 때",
    "airmang/python-hwpx": "파이썬 스크립트로 HWPX 문서를 동적으로 생성하고 편집할 때",
    "wheresryan22/anatomy": "복잡한 시스템 아키텍처와 동작 원리를 직관적인 다이어그램으로 해부할 때",
    "cursor/plugins": "Cursor 에디터에서 에이전트의 개발 도구와 플러그인을 확장할 때",
    "stablyai/orca": "웹·모바일 앱의 기능 오류를 사전에 감지하고 QA 테스트를 자동화할 때",
    "obra/superpowers": "에이전트에 강력한 시스템 제어 권한과 외부 도구 연동 능력을 부여할 때",
    "featherless-ai/simple-jev": "경량화된 자율 에이전트 루프와 상호작용 메커니즘을 테스트·구현할 때",
    "davidmokos/expo-gpt-live": "모바일 앱에서 지연 없는 초저지연 양방향 음성 AI 대화를 구현할 때",
    "CopilotKit/OpenBot": "웹 서비스나 대시보드 안에 맞춤형 AI 어시스턴트를 손쉽게 삽입할 때",
}


def esc(s: str | None) -> str:
    return (s or "").replace("|", "/").replace("\n", " ").strip()


# 토픽 영문 -> 한글 (상위 빈출 위주, 없으면 원문 유지)
TOPIC_KO = {
    "agent-skills": "에이전트 스킬", "agent-memory": "에이전트 메모리",
    "agent-plugins": "에이전트 플러그인", "agentic-rag": "에이전트 RAG",
    "context-database": "컨텍스트 DB", "self-evolving": "자가진화",
    "architecture-as-code": "아키텍처 코드화", "architecture-diagram": "아키텍처 다이어그램",
    "code-visualization": "코드 시각화", "claude-skill": "Claude 스킬",
    "mermaid-alternative": "Mermaid 대안", "diagram-as-code": "다이어그램 코드화",
    "diagrams-as-code": "다이어그램 코드화", "diagrams": "다이어그램",
    "system-design": "시스템 설계", "text-to-diagram": "텍스트→다이어그램",
    "data-flow-diagram": "데이터흐름도",
    "sequence-diagram": "시퀀스 다이어그램", "software-architecture": "소프트웨어 아키텍처",
    "ai-writing": "AI 글쓰기", "claude-code": "Claude Code", "codex": "Codex",
    "cursor": "Cursor", "prompt-engineering": "프롬프트 엔지니어링",
    "writing-tools": "글쓰기 도구", "browser": "브라우저", "chromium": "Chromium",
    "privacy": "프라이버시", "web-browser": "웹 브라우저",
    "alt-tab": "창 전환", "app-uninstaller": "앱 삭제", "appkit": "AppKit",
    "finder": "Finder", "free": "무료", "coding-agents": "코딩 에이전트",
    "developer-tools": "개발자 도구", "dsh-plugin": "DSH 플러그인",
    "ai-coding": "AI 코딩", "ai-agents": "AI 에이전트", "mcp": "MCP",
    "cli": "CLI", "open-source": "오픈소스",
    "llm": "LLM", "llms": "LLM", "large-language-models": "대형 언어 모델",
    "machine-learning": "머신러닝", "deep-learning": "딥러닝", "neural-network": "인공신경망",
    "generative-ai": "생성형 AI", "genai": "생성형 AI",
    "autonomous-agents": "자율 에이전트", "multi-agent": "멀티 에이전트",
    "multi-agent-systems": "멀티 에이전트 시스템",
    "nlp": "자연어 처리", "rag": "RAG", "knowledge-graph": "지식 그래프",
    "mcp-server": "MCP 서버", "token-optimization": "토큰 최적화",
    "speech-recognition": "음성 인식", "speech-synthesis": "음성 합성",
    "tts": "음성 합성(TTS)", "asr": "음성 인식(ASR)",
    "design-system": "디자인 시스템", "vibe-coding": "바이브 코딩",
    "workflow": "워크플로", "workflow-automation": "워크플로 자동화",
    "tutorials": "튜토리얼", "interview": "기술 면접",
    "python": "Python", "rust": "Rust", "java": "Java",
    "ollama": "Ollama", "openai": "OpenAI", "anthropic": "Anthropic",
}

# 라이선스 한글 주석
def enrich(
    data: dict,
    use_llm: bool = True,
    cache: dict | None = None,
    known: dict[str, dict] | None = None,
) -> list[dict]:
    """GitHub 보강 + LLM 분석. enriched.json의 analysis를 캐시로 재사용.

    - cache: {full_name: analysis} — 기존 enriched.json에서 로드, LLM 호출 절약
    - known: {full_name(casefold): 기존 아카이브 항목} — 설명이 있는 등록 도구는
      GitHub 조회와 AI 판정을 다시 하지 않는다 (stars도 갱신하지 않음)
    - KO/FEATS/USECASE 하드코딩은 LLM 결과가 없을 때의 폴백으로만 사용
    """
    enricher = GitHubEnricher()
    classifier = None
    if use_llm:
        try:
            from github_awesome_extractor.modules import LLMClassifier  # type: ignore[import-not-found]
            classifier = LLMClassifier(order=["freellmapi"])
            if not classifier.clients:
                print("[WARN] LLM 클라이언트 없음 — 기본 분석으로 진행")
                classifier = None
        except Exception as e:
            print(f"[WARN] LLM 초기화 실패 ({e}) — 기본 분석으로 진행")
            classifier = None
    cache = cache or {}
    # 영상별 컨텍스트 (자막 발췌 + 화면 요약) — 수집본 videos에서 매핑
    vid_ctx: dict[str, str] = {}
    for v in data.get("videos", []):
        vid = v.get("video_id", "") or v.get("title", "")
        parts = []
        if v.get("transcript_excerpt"):
            parts.append(f"[자막] {v['transcript_excerpt'][:1500]}")
        if v.get("visual_summary"):
            parts.append(f"[화면] {v['visual_summary'][:1000]}")
        if parts:
            vid_ctx[vid] = "\n".join(parts)
            if v.get("title"):
                vid_ctx[v["title"]] = vid_ctx[vid]
    out: list[dict] = []
    items = data.get("repos", [])
    for i, item in enumerate(items, 1):
        owner, repo = item["owner"], item["repo"]
        # 이미 등록되어 있고 설명이 있는 도구는 재조회·재분석하지 않는다.
        # stars도 갱신하지 않아 실행마다 수치와 판정이 흔들리지 않게 한다.
        registered = (known or {}).get(f"{owner}/{repo}".casefold())
        if registered and str(registered.get("description") or "").strip():
            kept = dict(registered)
            for field in ("source_video", "source_video_id", "source_url"):
                if item.get(field):
                    kept[field] = item[field]
            for field in ("discovery_sources", "discovery_queries"):
                if item.get(field):
                    kept[field] = list(item[field])
            out.append(kept)
            print(f"  [{i}/{len(items)}] {kept.get('full_name')} "
                  f"★{kept.get('stars') or 0:,} (등록됨·건너뜀)")
            continue
        prefetched_info = item.get("repository_info")
        if isinstance(prefetched_info, dict) and prefetched_info.get("full_name"):
            info = dict(prefetched_info)
        else:
            info = enricher.get_repo_info(owner, repo)
        info["topics"] = info.get("topics", [])
        info["source_video"] = item.get("source_video", "")
        info["source_video_id"] = item.get("source_video_id", "")
        info["source_url"] = item.get("source_url", "")
        for discovery_field in ("discovery_sources", "discovery_queries"):
            if item.get(discovery_field):
                info[discovery_field] = list(item[discovery_field])
        ctx = (vid_ctx.get(item.get("source_video_id", ""))
               or vid_ctx.get(item.get("source_video", ""), ""))
        fn = info["full_name"]
        # 캐시 유효 조건: verdict 있음, 또는 LLM 없이 만든 폴백인데 지금도 LLM 없음
        cached = cache.get(fn) or {}
        cache_ok = bool(cached.get("verdict")) or (
            cached.get("_fallback") and classifier is None)
        if cache_ok:
            analysis = dict(cached)
            try:
                from github_awesome_extractor.modules.llm_classifier import (  # type: ignore[import-not-found]
                    infer_ai_related,
                    infer_domain,
                )
                analysis.setdefault("is_ai_tool", infer_ai_related(info))
                analysis.setdefault("domain", infer_domain(info))
            except Exception:
                analysis.setdefault("is_ai_tool", bool(analysis.get("is_coding_tool")))
                analysis.setdefault("domain", "기타 AI 도구")
            info["analysis"] = analysis
            print(f"  [{i}/{len(items)}] {fn} ★{info.get('stars', 0):,} (캐시)")
        elif classifier:
            if fn in cache:
                print(f"  [{i}/{len(items)}] {fn} 구캐시 무효 → 재분석")
            try:
                info["analysis"] = classifier.analyze_repository(info, ctx)
                print(f"  [{i}/{len(items)}] {fn} ★{info.get('stars', 0):,} (LLM"
                      + ("+화면" if "[화면]" in ctx else "") + ")")
            except Exception as e:
                print(f"  [{i}/{len(items)}] {fn} LLM 실패: {e}")
                info["analysis"] = fallback_analysis(fn, info)
            time.sleep(0.5)
        else:
            info["analysis"] = fallback_analysis(fn, info)
            print(f"  [{i}/{len(items)}] {fn} ★{info.get('stars', 0):,}")
        out.append(info)
        time.sleep(0.5)
    # 다음 실행에서 GitHub API를 다시 호출하지 않도록 조회 결과를 보관한다.
    enricher.save_cache()
    return out


def fallback_analysis(fn: str, info: dict) -> dict:
    """LLM 없을 때: 하드코딩 사전 + 토픽 기반 최소 분석."""
    try:
        from github_awesome_extractor.modules.llm_classifier import (  # type: ignore[import-not-found]
            _install_hint_for,
            infer_ai_related,
            infer_domain,
        )
        install = _install_hint_for(info)
        is_ai_tool = infer_ai_related(info)
        domain = infer_domain(info)
    except Exception:
        install = ""
        is_ai_tool = False
        domain = "기타 AI 도구"
    feats = list(FEATS.get(fn, [])) or [TOPIC_KO.get(t, t) for t in dict.fromkeys((info.get("topics") or [])[:3])]
    feats = [item for item in feats if _has_hangul(str(item))]
    # 한글 요약: KO 매핑이 있으면 사용, 없으면 한글 설명만 채택한다.
    if fn in KO:
        summary_ko = KO[fn]
    else:
        desc = str(info.get("description") or "")
        summary_ko = desc if _has_hangul(desc) else ""
    # 한글 요약 길이 제한
    if len(summary_ko) > 200:
        summary_ko = summary_ko[:200]
    # 추천 용도: 한글 매핑이 있으면 사용, 없으면 한글 요약에서 만든다.
    desc_short = _short_head(str(info.get("description") or ""))
    usecase = USECASE.get(fn) or (desc_short if _has_hangul(desc_short) else "") or (KO.get(fn) and _short_head(KO[fn])) or f"{domain} 활용 및 연구용"
    return {
        "summary_ko": summary_ko,
        "is_ai_tool": is_ai_tool,
        "domain": domain,
        "why_hot": "",
        "key_features": feats,
        "install_ko": "저장소 README의 설치 안내 참고",
        "install_cmd": install,
        "install_hint": install,
        "usecase_ko": usecase,
        "verdict": "",
        "pros": "",
        "cons": "",
        "category": "기타 개발 도구",
        "is_coding_tool": True,
        "confidence_score": 0.4,
        "_fallback": True,
    }


def load_analysis_cache() -> dict:
    """기존 enriched.json의 analysis 재사용."""
    if not _ENRICHED_JSON.exists():
        return {}
    try:
        old = json.loads(_ENRICHED_JSON.read_text(encoding="utf-8"))
        return {r["full_name"]: r.get("analysis", {}) for r in old.get("repos", []) if r.get("analysis")}
    except Exception:
        return {}


def load_repo_archive() -> list[dict]:
    """현재 enriched.json을 누적 아카이브로 읽는다."""
    if not _ENRICHED_JSON.exists():
        return []
    try:
        payload = json.loads(_ENRICHED_JSON.read_text(encoding="utf-8"))
        repos = payload.get("repos", [])
        return [repo for repo in repos if isinstance(repo, dict) and repo.get("full_name")]
    except (OSError, json.JSONDecodeError, AttributeError):
        return []


def merge_repo_archive(
    archived: list[dict], current: list[dict], registered_at: str
) -> list[dict]:
    """새 후보를 저장소 이름으로 병합하고 최초 등록일을 유지한다."""
    merged: dict[str, dict] = {}
    for repo in archived:
        key = str(repo.get("full_name", "")).strip().casefold()
        if key:
            existing = dict(repo)
            if not existing.get("registered_at"):
                existing["registered_at"] = registered_at
            merged[key] = existing

    for repo in current:
        key = str(repo.get("full_name", "")).strip().casefold()
        if not key:
            continue
        previous = merged.get(key, {})
        item = {**previous, **repo}
        item["registered_at"] = previous.get("registered_at") or repo.get("registered_at") or registered_at

        old_analysis = previous.get("analysis") or {}
        new_analysis = item.get("analysis") or {}
        if old_analysis and not old_analysis.get("_fallback") and new_analysis.get("_fallback"):
            item["analysis"] = old_analysis
        merged[key] = item

    return sorted(
        merged.values(),
        key=lambda item: (
            str(item.get("registered_at") or ""),
            str(item.get("full_name") or "").casefold(),
        ),
        reverse=True,
    )


def _analysis_for(r: dict) -> dict:
    """repo dict에 내장된 analysis 우선, 없으면 폴백 생성."""
    if r.get("analysis"):
        return r["analysis"]
    return fallback_analysis(r["full_name"], r)


def _is_ai_catalog_item(repo: dict) -> bool:
    """레거시 데이터도 AI 관련 여부를 보완해 아카이브 표시 대상을 고른다."""
    analysis = _analysis_for(repo)
    if isinstance(analysis.get("is_ai_tool"), bool):
        return analysis["is_ai_tool"]
    try:
        from github_awesome_extractor.modules.llm_classifier import infer_ai_related  # type: ignore[import-not-found]
        analysis["is_ai_tool"] = infer_ai_related(repo)
    except Exception:
        analysis["is_ai_tool"] = bool(analysis.get("is_coding_tool"))
    repo["analysis"] = analysis
    return analysis["is_ai_tool"]


def _repo_domain(repo: dict) -> str:
    """폴백 분석 항목은 최신 메타데이터로 분야를 다시 계산한다."""
    analysis = _analysis_for(repo)
    if analysis.get("_fallback"):
        try:
            from github_awesome_extractor.modules.llm_classifier import infer_domain  # type: ignore[import-not-found]
            return infer_domain(repo)
        except Exception:
            pass
    return str(analysis.get("domain") or analysis.get("category") or "기타 AI 도구")


def _has_hangul(value: str) -> bool:
    """문자열에 한글이 포함됐는지 확인한다(영문 노출 방지 판정용)."""
    return any("가" <= char <= "힣" for char in value)


def _audience_ko(analysis: dict) -> str:
    """추천 대상을 한글로만 노출한다."""
    audience = str(analysis.get("target_audience") or "").strip()
    return audience if _has_hangul(audience) else "개발자·실무자"


def _features_ko(repo: dict, analysis: dict, limit: int = 5) -> list[str]:
    """주요 기능 태그에 영문이 그대로 노출되지 않도록 한글 항목만 남긴다."""
    values = analysis.get("key_features") or repo.get("topics") or []
    if isinstance(values, str):
        values = [values]
    features: list[str] = []
    for value in values:
        raw = str(value).strip()
        if not raw:
            continue
        text = TOPIC_KO.get(raw.lower()) or TOPIC_KO.get(raw) or raw
        if not _has_hangul(text) or text in features:
            continue
        features.append(text)
    return features[:limit]


def _description_ko(repo: dict, analysis: dict | None = None) -> str:
    """영문 원문이 화면에 직접 노출되지 않도록 한국어 요약을 선택한다."""
    analysis = analysis or _analysis_for(repo)
    full_name = str(repo.get("full_name", ""))
    if full_name in KO:
        return KO[full_name]

    summary = str(analysis.get("summary_ko") or "").strip()
    if summary.startswith("설명: "):
        summary = summary[len("설명: "):]

    if not analysis.get("_fallback") and summary and _has_hangul(summary):
        return summary
    description = str(repo.get("description") or "").strip()
    if _has_hangul(description):
        return description
    domain = _repo_domain(repo)
    return f"{domain} 분야의 오픈소스 프로젝트입니다."


def _trunc_words(s: str, limit: int = 100) -> str:
    """단어 경계에서 자르기 (부록 중간 잘림 방지)."""
    s = (s or "").strip()
    if len(s) <= limit:
        return s
    parts = s[:limit].rsplit(" ", 1)
    return (parts[0] if len(parts) > 1 else s[:limit]).rstrip(".,;:") + "…"


def _short_head(s: str, limit: int = 90) -> str:
    """<summary> 헤더용 한 줄 요약: 첫 문장 + 길이 제한 (본문과 중복 방지)."""
    s = (s or "").strip().rstrip(".")
    if not s:
        return ""
    for sep in (". ", "! ", "? ", ".\n"):
        if sep in s:
            s = s.split(sep)[0]
            break
    s = s.rstrip(".")
    return s[:limit] + ("…" if len(s) > limit else "")


def _body_text(s: str) -> str:
    """본문 요약: 마침표 중복(합니다..) 방지."""
    s = (s or "").strip()
    return s.rstrip(".") + ("." if s else "")


def _usecase_ko(repo: dict, analysis: dict, summary: str) -> str:
    """저장된 영어 용도보다 등록된 한국어 용도를 우선한다."""
    full_name = str(repo.get("full_name", ""))
    curated = USECASE.get(full_name)
    if curated:
        return curated

    usecase = str(analysis.get("usecase_ko") or "").strip()
    if _has_hangul(usecase) and usecase != "개발 도구 활용":
        return usecase

    if _has_hangul(summary) and "확인 필요" not in summary and "등록하지 않았습니다" not in summary:
        return _short_head(summary)

    domain = _repo_domain(repo)
    return f"{domain} 관련 프로젝트 및 실무 활용"


def row_detail(r: dict, today: str) -> str:
    """프로젝트 용도·기능·등록일을 아카이브 표의 한 행으로 만든다."""
    full_name = str(r.get("full_name", "Unknown"))
    analysis = _analysis_for(r)
    summary = _description_ko(r, analysis)
    usecase = _usecase_ko(r, analysis, summary)
    features = _features_ko(r, analysis, limit=4)
    audience = _audience_ko(analysis)
    domain = _repo_domain(r)
    registered_at = str(r.get("registered_at") or today)
    html_features = "".join(
        f"<li>{html_escape(esc(item), quote=False)}</li>" for item in features[:4]
    )
    feature_block = f"<ul>{html_features}</ul>" if html_features else "<p>기능 정보가 없습니다.</p>"
    show_summary = bool(summary and not (usecase and summary.startswith(usecase)))
    more_content = (
        (f"<p>{html_escape(esc(summary), quote=False)}</p>" if show_summary else "")
        + (
            f"<p><b>추천 대상:</b> {html_escape(esc(audience), quote=False)}</p>"
            if audience
            else ""
        )
    )
    more = f"<details><summary>대상과 설명</summary>{more_content}</details>" if more_content else ""
    use_text = usecase or _short_head(summary)
    html_url = str(r.get("html_url") or f"https://github.com/{full_name}")
    link = html_escape(esc(html_url), quote=True)
    label = html_escape(esc(full_name), quote=False)
    return (
        f"| [{label}]({link}) | {html_escape(esc(domain), quote=False)} | "
        f"<b>용도:</b> {html_escape(esc(use_text), quote=False)}<br>"
        f"<b>주요 기능:</b>{feature_block}{more} | "
        f"{html_escape(esc(audience or '—'), quote=False)} | "
        f"{html_escape(esc(registered_at), quote=False)} |"
    )


def build_md(
    repos: list[dict],
    videos_scanned: int,
    today: str,
    target_from_date: str = "",
    target_to_date: str = "",
) -> str:
    """전체 보관 프로젝트를 분야별로 누적 표시한다."""
    groups: dict[str, list[dict]] = {}
    catalog_repos = [repo for repo in repos if _is_ai_catalog_item(repo)]
    for repo in catalog_repos:
        analysis = _analysis_for(repo)
        domain = _repo_domain(repo)
        groups.setdefault(domain, []).append(repo)

    period = ""
    if target_from_date and target_to_date:
        period = f"**대상 영상 기간:** {target_from_date}–{target_to_date}  \n"

    lines = [
        "# AI 도구 아카이브",
        "",
        period + f"**등록 프로젝트:** {len(catalog_repos)}개 · **최근 갱신:** {today}  ",
        f"**이번 실행 분석 영상:** {videos_scanned}개",
        "",
        "프로젝트의 용도와 주요 기능을 분야별로 정리합니다. 등록일은 이 아카이브에 처음 추가된 날짜입니다.",
        "",
    ]
    for domain in sorted(groups, key=str.casefold):
        rows = sorted(
            groups[domain],
            key=lambda item: (
                str(item.get("registered_at") or ""),
                str(item.get("full_name") or "").casefold(),
            ),
            reverse=True,
        )
        lines.extend(
            [
                f"## {domain}",
                "",
                "| 프로젝트 | 분야 | 용도 및 주요 기능 | 대상 | 등록일 |",
                "|---|---|---|---|---|",
            ]
        )
        lines.extend(row_detail(repo, today) for repo in rows)
        lines.append("")
    if not catalog_repos:
        lines.append("아직 등록된 프로젝트가 없습니다.")
    return "\n".join(lines).rstrip() + "\n"


def build_html(
    repos: list[dict],
    today: str,
    target_from_date: str = "",
    target_to_date: str = "",
) -> str:
    """목업과 같은 카드형 대시보드를 실제 누적 저장소 데이터로 렌더링한다."""
    domains = [
        ("dev", "개발 도구"),
        ("business", "업무·비즈니스"),
        ("knowledge", "문서·지식"),
        ("creative", "콘텐츠·창작"),
        ("infra", "모델·AI 인프라"),
        ("education", "교육·연구"),
        ("health", "의료·바이오"),
        ("finance", "금융·법률"),
        ("robotics", "로봇·기기"),
        ("accessibility", "접근성·번역"),
        ("other", "기타 AI 도구"),
    ]
    slug_by_domain = {label: slug for slug, label in domains}
    catalog = [repo for repo in repos if _is_ai_catalog_item(repo)]
    counts: dict[str, int] = {}
    cards: list[str] = []

    for repo in catalog:
        analysis = _analysis_for(repo)
        domain = _repo_domain(repo)
        slug = slug_by_domain.get(domain, "other")
        counts[domain] = counts.get(domain, 0) + 1
        full_name = str(repo.get("full_name", "Unknown"))
        safe_url = str(repo.get("html_url") or f"https://github.com/{full_name}")
        if not safe_url.startswith("https://github.com/"):
            safe_url = f"https://github.com/{full_name}"
        label = html_escape(full_name, quote=False)
        description = _description_ko(repo, analysis)
        usecase = _usecase_ko(repo, analysis, description)
        features = _features_ko(repo, analysis)
        feature_html = "".join(
            f"<li>{html_escape(esc(value), quote=False)}</li>" for value in features
        ) or '<li class="muted-chip">세부 기능 정보 없음</li>'
        audience = _audience_ko(analysis)
        registered = str(repo.get("registered_at") or today)
        cards.append(
            f'<article class="tool" data-kind="{slug}">'
            f'<div class="tool-head"><h3 class="name">'
            f'<a href="{html_escape(safe_url, quote=True)}" target="_blank" rel="noreferrer">'
            f'{label} ↗</a><span class="badge">{html_escape(domain, quote=False)}</span></h3></div>'
            f'<p class="use">{html_escape(esc(usecase), quote=False)}</p>'
            '<div class="details">'
            f'<div><span class="field-label">주요 기능</span><ul>{feature_html}</ul></div>'
            f'<div><span class="field-label">이런 분께</span>'
            f'<span class="audience">{html_escape(esc(audience), quote=False)}</span></div>'
            f'<div><span class="field-label">등록일</span>'
            f'<time datetime="{html_escape(registered, quote=True)}">'
            f'{html_escape(registered, quote=False)}</time></div>'
            '</div></article>'
        )

    category_buttons = [
        '<button class="category" type="button" data-category="all" aria-pressed="true">'
        '<span class="cat-dot"></span>전체 분야'
        f'<span class="count">{len(catalog)}</span></button>'
    ]
    for slug, domain in domains:
        category_buttons.append(
            f'<button class="category" type="button" data-category="{slug}" aria-pressed="false">'
            f'<span class="cat-dot"></span>{html_escape(domain, quote=False)}'
            f'<span class="count">{counts.get(domain, 0)}</span></button>'
        )

    cards_html = "\n".join(cards) or '<div class="empty">아직 등록된 프로젝트가 없습니다.</div>'
    from_value = html_escape(target_from_date, quote=True)
    to_value = html_escape(target_to_date, quote=True)
    period_note = (
        f"YouTube 영상 게시일 {html_escape(target_from_date, quote=False)}–"
        f"{html_escape(target_to_date, quote=False)} 기준"
        if target_from_date and target_to_date
        else "YouTube 영상 최근 3일 기준"
    )
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 도구 아카이브</title>
<style>
:root{{--bg:#f5f6f8;--surface:#fff;--soft:#eef0f4;--text:#20232a;--muted:#626975;--line:#dfe2e8;--accent:#5746d8;--green:#176b4b}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.window{{display:grid;grid-template-columns:224px minmax(0,1fr);min-height:100vh}}.sidebar{{padding:23px 16px;border-right:1px solid var(--line);background:var(--surface)}}
.brand{{display:flex;gap:10px;align-items:center;margin:0 0 30px 4px;font-weight:600}}.brand-mark{{display:grid;width:30px;height:30px;place-items:center;border-radius:9px;color:var(--accent);background:#efedff;font-weight:600}}
.side-label,.field-label{{color:var(--muted);font-size:11px;font-weight:500;letter-spacing:.04em}}.side-label{{margin:0 8px 9px;font-size:12px;letter-spacing:0}}
.category-list{{display:grid;gap:3px}}.category{{display:flex;width:100%;gap:9px;align-items:center;padding:8px 9px;border:0;border-radius:8px;color:var(--muted);background:transparent;text-align:left;font:inherit;cursor:pointer}}
.category:hover,.category[aria-pressed="true"]{{color:var(--accent);background:#efedff}}.category[aria-pressed="true"]{{font-weight:500}}.cat-dot{{width:7px;height:7px;border-radius:50%;background:currentColor;opacity:.68}}.count{{margin-left:auto;font-size:11px}}
.topbar{{display:flex;min-height:58px;align-items:center;justify-content:space-between;gap:12px;padding:0 30px;border-bottom:1px solid var(--line);background:var(--surface)}}.crumb,.top-tag,.section-note{{color:var(--muted)}}.top-tag{{padding:5px 9px;border:1px solid var(--line);border-radius:99px;font-size:12px}}
.content{{width:min(100%,1040px);margin:0 auto;padding:35px 30px 42px}}.eyebrow{{margin:0 0 8px;color:var(--accent);font-size:12px;font-weight:500;letter-spacing:.06em;text-transform:uppercase}}
h1{{margin:0;font-size:clamp(25px,3vw,32px);font-weight:500;letter-spacing:-.035em;line-height:1.2}}.intro{{max-width:680px;margin:10px 0 24px;color:var(--muted)}}
.date-controls{{display:flex;flex-wrap:wrap;align-items:end;gap:10px 14px;padding:13px 15px;border:1px solid var(--line);border-radius:10px;background:var(--surface)}}.date-group{{display:grid;gap:5px}}.date-group>span:first-child{{color:var(--muted);font-size:11px}}.date-inputs{{display:flex;flex-wrap:wrap;align-items:center;gap:7px}}
input[type=date]{{min-height:34px;padding:5px 8px;border:1px solid var(--line);border-radius:7px;color:var(--text);background:var(--bg);font:inherit}}.apply-range{{min-height:34px;padding:6px 11px;border:0;border-radius:7px;background:var(--soft);font:inherit;cursor:pointer}}.date-status{{flex:1 1 220px;color:var(--muted);font-size:12px}}.command{{display:none;flex-basis:100%;padding:8px 10px;border-radius:7px;background:var(--soft);font:12px ui-monospace,monospace;overflow-wrap:anywhere}}
.section-heading{{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 16px;margin:26px 0 12px}}h2{{margin:0;font-size:16px;font-weight:500}}.section-note{{font-size:12px}}.cards{{display:grid;gap:11px}}.tool{{padding:17px 19px;border:1px solid var(--line);border-radius:11px;background:var(--surface)}}
.name{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0;font-size:15px;font-weight:500}}.name a{{color:var(--text);text-decoration:none;overflow-wrap:anywhere}}.name a:hover{{color:var(--accent)}}.badge{{padding:3px 8px;border-radius:99px;color:var(--green);background:var(--soft);font-size:11px;font-weight:400}}.use{{margin:7px 0 12px;color:var(--muted)}}
.details{{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(160px,1fr) auto;gap:14px 24px}}.field-label{{display:block;margin-bottom:5px}}ul{{display:flex;flex-wrap:wrap;gap:6px;margin:0;padding:0;list-style:none}}li{{padding:4px 8px;border:1px solid var(--line);border-radius:6px;font-size:12px}}.muted-chip{{color:var(--muted)}}.audience{{color:var(--text)}}.empty{{padding:22px 18px;border:1px dashed var(--line);border-radius:10px;color:var(--muted);background:var(--surface)}}
@media(max-width:760px){{.window{{grid-template-columns:1fr}}.sidebar{{padding:14px;border-right:0;border-bottom:1px solid var(--line)}}.brand{{margin:0 0 12px 3px}}.category-list{{display:flex;gap:5px;overflow-x:auto;padding-bottom:3px}}.side-label{{display:none}}.category{{width:auto;white-space:nowrap}}.topbar{{padding:0 16px}}.content{{padding:25px 16px 32px}}.details{{grid-template-columns:1fr;gap:10px}}}}
</style></head><body><div class="window">
<aside class="sidebar" aria-label="분야 선택"><div class="brand"><span class="brand-mark">AI</span><span>도구 아카이브</span></div><p class="side-label">분야별 둘러보기</p><nav class="category-list" aria-label="도구 분야">{''.join(category_buttons)}</nav></aside>
<main><header class="topbar"><span class="crumb">라이브러리 / 모든 도구</span><span class="top-tag">실제 수집 데이터 · {html_escape(today, quote=False)}</span></header>
<section class="content"><p class="eyebrow">AI tools, by what they help you do</p><h1>쓰임새로 찾는 AI 도구</h1>
<p class="intro">개발부터 업무와 창작까지, 각 프로젝트가 해결하는 일과 주요 기능을 한눈에 살펴보세요.</p>
<div class="date-controls" aria-label="YouTube 영상 게시일 범위 지정"><label class="date-group"><span>YouTube 영상 게시일 · 한국 시간</span><span class="date-inputs"><input id="from-date" type="date" value="{from_value}" aria-label="게시 시작일"><span>부터</span><input id="to-date" type="date" value="{to_value}" aria-label="게시 종료일"><span>까지</span></span></label>
<button class="apply-range" id="apply-range" type="button">기간 선택</button><span class="date-status" id="date-status">{period_note} · 종료일 포함<br>GitHub 인기·Trending은 현재 기준으로 수집</span><code class="command" id="command"></code></div>
<div class="section-heading"><h2 id="results-heading">전체 분야 · {len(catalog)}개</h2><span class="section-note">프로젝트별 용도와 기능 중심으로 정리</span></div>
<div class="cards" aria-live="polite">{cards_html}</div><div class="empty" id="empty" hidden>이 분야의 후보는 아직 없습니다.</div>
</section></main></div>
<script>(()=>{{const buttons=[...document.querySelectorAll('.category')],cards=[...document.querySelectorAll('.tool')],heading=document.querySelector('#results-heading'),empty=document.querySelector('#empty');
buttons.forEach(button=>button.addEventListener('click',()=>{{const selected=button.dataset.category;buttons.forEach(item=>item.setAttribute('aria-pressed',String(item===button)));let visible=0;cards.forEach(card=>{{const show=selected==='all'||card.dataset.kind===selected;card.hidden=!show;if(show)visible++}});heading.textContent=(selected==='all'?'전체 분야':button.childNodes[1].textContent.trim())+' · '+visible+'개';empty.hidden=visible>0}}));
document.querySelector('#apply-range').addEventListener('click',()=>{{const from=document.querySelector('#from-date').value,to=document.querySelector('#to-date').value,status=document.querySelector('#date-status'),command=document.querySelector('#command');if(!from||!to||from>to){{status.textContent='시작일과 종료일을 확인하세요.';command.style.display='none';return}}status.textContent=from+'–'+to+' 대상 기간으로 설정됨 · 종료일 포함';command.textContent='python sources/manuagi_collector.py --from-date '+from+' --to-date '+to;command.style.display='block'}})}})();</script>
</body></html>'''


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--regen-html", "--regen-md", dest="regen_html", action="store_true",
                    help="GitHub API 호출 없이 enriched.json만으로 html 재생성")
    ap.add_argument("--no-llm", action="store_true", help="LLM 분석 생략")
    args = ap.parse_args()
    use_llm = (not args.no_llm) and (os.environ.get("SKIP_LLM", "") != "1")

    if args.regen_html:
        if not _ENRICHED_JSON.exists():
            raise SystemExit(f"보강본 없음: {_ENRICHED_JSON}")
        old = json.loads(_ENRICHED_JSON.read_text(encoding="utf-8"))
        enriched = old.get("repos", [])
        today = datetime.now(_TARGET_TIMEZONE).date().isoformat()
        enriched = merge_repo_archive(enriched, [], today)
        # analysis 없는 구버전 항목은 폴백으로 채움
        for r in enriched:
            if not r.get("analysis"):
                r["analysis"] = fallback_analysis(r["full_name"], r)
            r["description_ko"] = _description_ko(r)
        old["repos"] = enriched
        _ENRICHED_JSON.write_text(
            json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        _TARGET_HTML.write_text(
            build_html(
                enriched,
                today,
                old.get("target_from_date", ""),
                old.get("target_to_date", ""),
            ),
            encoding="utf-8",
        )
        print(f"[SUCCESS] html 재생성 (API 호출 없음): {_TARGET_HTML}")
        return

    if not _SRC_JSON.exists():
        raise SystemExit(f"수집본 없음: {_SRC_JSON} — 먼저 manuagi_collector.py 실행 필요")
    data = json.loads(_SRC_JSON.read_text(encoding="utf-8"))
    print(f"[INFO] 수집본: 영상 {data.get('videos_scanned')}개, 후보 {len(data.get('repos', []))}개")

    archived = load_repo_archive()
    known = {
        str(repo.get("full_name", "")).strip().casefold(): repo
        for repo in archived
        if repo.get("full_name")
    }
    cache = load_analysis_cache()
    if cache:
        print(f"[INFO] analysis 캐시 {len(cache)}건 재사용")
    analyzed_candidates = enrich(data, use_llm=use_llm, cache=cache, known=known)
    current_enriched = [repo for repo in analyzed_candidates if _is_ai_catalog_item(repo)]
    excluded_candidates = len(analyzed_candidates) - len(current_enriched)
    today = datetime.now(_TARGET_TIMEZONE).date().isoformat()
    enriched = merge_repo_archive(archived, current_enriched, today)
    for repo in enriched:
        repo["description_ko"] = _description_ko(repo)
    catalog_total = sum(1 for repo in enriched if _is_ai_catalog_item(repo))
    _ENRICHED_JSON.write_text(
        json.dumps(
            {
                "channel": data.get("channel"),
                "videos_scanned": data.get("videos_scanned"),
                "repos_found_this_run": len(current_enriched),
                "candidates_excluded_this_run": excluded_candidates,
                "repos_total": catalog_total,
                "collected_at": data.get("collected_at"),
                "enriched_at": datetime.now(timezone.utc).isoformat(),
                "target_from_date": data.get("target_from_date", ""),
                "target_to_date": data.get("target_to_date", ""),
                "repos": enriched,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[INFO] 보강 JSON 저장: {_ENRICHED_JSON}")

    _TARGET_HTML.write_text(
        build_html(
            enriched,
            today,
            data.get("target_from_date", ""),
            data.get("target_to_date", ""),
        ),
        encoding="utf-8",
    )
    print(
        f"[INFO] 이번 실행 AI 프로젝트 {len(current_enriched)}개, "
        f"범위 외 후보 {excluded_candidates}개 제외, 누적 아카이브 {catalog_total}개"
    )
    print(f"[SUCCESS] html 저장: {_TARGET_HTML}")
    # 분석済 기록 — 다음 수집부터 이 영상들은 스킵
    try:
        from github_awesome_extractor.sources.state import mark_many  # type: ignore[import-not-found]
        title_to_id = {v.get("title", ""): v.get("video_id", "")
                       for v in data.get("videos", [])}
        by_vid: dict[str, dict] = {}
        for it in data.get("repos", []):
            vid = it.get("source_video_id", "") or title_to_id.get(it.get("source_video", ""), "")
            if not vid:
                continue
            by_vid.setdefault(vid, {"video_id": vid, "title": it.get("source_video", ""),
                                    "repos": []})["repos"].append(f"{it['owner']}/{it['repo']}")
        n = mark_many(list(by_vid.values()))
        print(f"[INFO] 분석済 기록: 영상 {n}개")
    except Exception as e:
        print(f"[WARN] 분석済 기록 실패: {e}")
    catalog_repos = [r for r in enriched if _is_ai_catalog_item(r)]
    no_llm = [r["full_name"] for r in catalog_repos
              if not (r.get("analysis") or {}).get("summary_ko")]
    if no_llm:
        print(f"[WARN] 요약 없음 (원문 표시): {no_llm}")
    no_feat = [r["full_name"] for r in catalog_repos
               if not (r.get("analysis") or {}).get("key_features")]
    if no_feat:
        print(f"[WARN] 핵심기능 없음: {no_feat}")


if __name__ == "__main__":
    main()
