import json
import logging
from typing import Optional

from shared.ai_providers import build_clients

log = logging.getLogger(__name__)

DOMAINS = (
    "개발 도구",
    "업무·비즈니스",
    "문서·지식",
    "콘텐츠·창작",
    "모델·AI 인프라",
    "교육·연구",
    "의료·바이오",
    "금융·법률",
    "로봇·기기",
    "접근성·번역",
    "기타 AI 도구",
)


def infer_domain(repo_info: dict) -> str:
    """LLM이 없을 때 이름·요약 설명·토픽으로 분야를 대략 정한다."""
    import re

    text = " ".join(
        [
            str(repo_info.get("full_name", "")),
            str(repo_info.get("description", "")),
            " ".join(repo_info.get("topics") or []),
        ]
    ).casefold()
    rules = (
        ("의료·바이오", ("health", "medical", "clinical", "biomedical", "patient")),
        ("금융·법률", ("finance", "trading", "accounting", "legal", "banking")),
        ("로봇·기기", ("robot", "robotics", "hardware", "embedded", "iot")),
        ("접근성·번역", ("accessibility", "translation", "translator", "caption", "speech-to-text")),
        ("교육·연구", ("education", "educational", "tutor", "course", "classroom", "curriculum", "research", "scientific", "academic")),
        ("콘텐츠·창작", ("image generation", "video generation", "diffusion", "music generation", "creative", "animation")),
        ("문서·지식", ("document", "knowledge base", "rag", "wiki", "ocr")),
        ("업무·비즈니스", ("crm", "customer", "sales", "support", "meeting", "workflow")),
        ("모델·AI 인프라", ("inference", "serving", "model gateway", "llm hosting", "training")),
        ("개발 도구", ("coding", "developer", "code", "programming", "software", "mcp", "cli")),
    )
    for domain, keywords in rules:
        if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
            return domain
    return "기타 AI 도구"


def infer_ai_related(repo_info: dict) -> bool:
    """보수적인 키워드 기준으로 AI가 프로젝트의 핵심인지 추정한다."""
    import re

    text = " ".join(
        [
            str(repo_info.get("full_name", "")),
            str(repo_info.get("description", "")),
            " ".join(repo_info.get("topics") or []),
            str(repo_info.get("readme_snippet", ""))[:2000],
        ]
    ).casefold()
    if re.search(r"\b(ai|ml|llm|gpt|rag)\b", text):
        return True
    if re.search(r"\bcoding[- ]agents?\b|\bagent[- ]skills?\b", text):
        return True
    if "mcp" in text and re.search(r"\b(coding|code|programming|developer)\b", text):
        return True
    if re.search(r"\b(token[- ]optimizers?|token[- ]optimization|context[- ]window)\b", text):
        return True
    return any(
        phrase in text
        for phrase in (
            "artificial intelligence",
            "machine learning",
            "language model",
            "neural network",
            "generative",
            "diffusion model",
            "text to speech",
            "speech recognition",
            "computer vision",
            "embedding model",
            "agentic",
            "ai agent",
            "agent memory",
            "model routing",
            "model gateway",
            "model serving",
            "model inference",
            "text-to-video",
            "text to video",
            "context quality decay",
            "context compaction",
            "context compression",
            "prompt compression",
        )
    )

try:
    from config.settings import DIGEST_MIN_STARS
except Exception:
    DIGEST_MIN_STARS = 100


def _install_hint_for(repo_info: dict) -> str:
    """LLM 없이 언어별 관례로 설치 한 줄 추론."""
    lang = (repo_info.get("language") or "").lower()
    full = repo_info.get("full_name", "")
    name = full.split("/")[-1] if "/" in full else full
    if lang in ("typescript", "javascript"):
        return f"npx {name}  # 또는 저장소 README 확인"
    if lang == "python":
        return f"pip install {name}"
    if lang == "rust":
        return f"cargo install --git https://github.com/{full}"
    if lang == "go":
        return f"go install github.com/{full}@latest"
    return ""


class LLMClassifier:
    """Classifies and summarizes repositories using LLM."""

    def __init__(self, order: Optional[list[str]] = None):
        """Initialize LLM classifier.

        AI 키는 환경변수 우선, `secret/api key.txt` 차순으로
        ai_providers 모듈에서 해석한다.

        Args:
            order: 프로바이더 우선순위 (기본값은 ai_providers 기준)
        """
        self.clients = build_clients(order=order)

    def analyze_repository(self, repo_info: dict, transcript_text: str = "") -> dict:
        """
        Analyze if repository is a coding tool and generate summary.

        Args:
            repo_info: Repository metadata
            transcript_text: Video transcript context

        Returns:
            Analysis result dictionary
        """
        if not self.clients:
            return self._basic_analysis(repo_info)

        # 인기 저장소도 한글 요약을 만들기 위해 LLM 분석을 그대로 사용한다.
        # (과거에는 stars>1000이면 기본 분석으로 건너뛰어 영문 설명이 노출됐다.)
        readme = (repo_info.get("readme_snippet", "") or "")[:2000]
        topics = ", ".join((repo_info.get("topics") or [])[:10]) or "없음"
        prompt = f"""
당신은 GitHub 오픈소스 프로젝트를 분석하는 전문가입니다.
아래 리포지토리 정보+README+유튜브 자막을 보고 AI가 핵심인 프로젝트인지 판정하고,
분야와 실제 용도를 실무자가 바로 이해할 수 있는 한글로 요약하세요.

**분석 기준:**
- AI가 핵심 기능인 도구와 AI 시스템을 만들거나 운영하는 기반 기술을 포함하세요.
- 개발 외에도 업무, 지식·문서, 창작, 교육·연구, 의료·바이오, 금융·법률,
  로봇·기기, 접근성 분야의 AI 도구를 포함하세요.
- AI가 핵심이 아닌 일반 소프트웨어는 AI 도구로 분류하지 마세요.

**분야 판정:**
- 개발 도구뿐 아니라 업무·비즈니스, 문서·지식, 콘텐츠·창작, 모델·AI 인프라, 교육·연구,
  의료·바이오, 금융·법률, 로봇·기기, 접근성·번역을 포함해 프로젝트의 주된 사용 분야를 고르세요.
- AI가 핵심 기능이 아니거나 실제 용도가 확인되지 않으면 "기타 AI 도구"로 억지 분류하지 말고
  내용을 근거로 가장 알맞은 분야를 선택하세요.

[Repo Info]
- Name: {repo_info['full_name']}
- Description: {(repo_info.get('description', 'N/A') or 'N/A')[:500]}
- Language: {repo_info.get('language', 'N/A')}
- Stars: {repo_info.get('stars', 0)} / Forks: {repo_info.get('forks', 0)} / OpenIssues: {repo_info.get('open_issues', 0)}
- License: {repo_info.get('license', 'N/A')} / Pushed: {repo_info.get('pushed_at', 'N/A')} / Release: {repo_info.get('latest_release', 'N/A')}
- Topics: {topics}

[README 발췌]
{(readme if readme else "README 없음")}

[Video Context: 자막 + 화면 요약]
{(transcript_text[:2500] if transcript_text else "No video context available")}

다음 JSON 스키마로만 응답 (설명 없이 JSON만):
{{
    "is_ai_tool": true/false,
    "is_coding_tool": true/false,
    "confidence_score": 0.0-1.0,
    "domain": "개발 도구" | "업무·비즈니스" | "문서·지식" | "콘텐츠·창작" | "모델·AI 인프라" | "교육·연구" | "의료·바이오" | "금융·법률" | "로봇·기기" | "접근성·번역" | "기타 AI 도구",
    "category": "AI/ML 도구" | "코드 에디터/IDE" | "개발 프레임워크" | "DevOps/인프라" | "프로그래밍 언어/라이브러리" | "기타 개발 도구",
    "summary_ko": "핵심 기능 한글 2문장 (뭘 하는 도구인지 + 누구에게 유용한지)",
    "why_hot": "왜 지금 뜨는지 1문장 (README/자막 근거, 과장 금지)",
    "key_features": ["구체 기능1", "구체 기능2", "구체 기능3", "구체 기능4"],
    "install_ko": "설치 방법 한글 1문장 (예: 릴리즈 페이지의 dmg를 받아 Applications에 드래그)",
    "install_cmd": "실제 설치 명령어 있는 그대로 (예: npx skills add foo -g — 없으면 빈 문자열, 한글 설명 넣지 말 것)",
    "usecase_ko": "추천 용도 한 줄 (예: 터미널에서 AI 코딩할 때)",
    "verdict": "써볼 만함 | 지켜볼 만함 | 패스 중 하나 + 이유 1줄 (예: 써볼 만함 — 설치 1분, 문서 충실)",
    "pros": "장점 1줄 (실무 관점)",
    "cons": "주의점 1줄 (라이선스 함정, 설치 무게, 문서 부족 등 — 없으면 빈 문자열)",
    "target_audience": "대상 개발자층"
}}
"""
        
        # Try each provider until success (fast failover)
        for provider in self.clients:
            try:
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    timeout=30,
                    max_tokens=2000,
                )
                
                content = response.choices[0].message.content or ""

                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                    # 필수 필드 누락 시 다음 프로바이더로 폴백
                    if (isinstance(result, dict) and result.get("summary_ko")
                            and result.get("verdict") and result.get("key_features")):
                        if not isinstance(result.get("is_ai_tool"), bool):
                            result["is_ai_tool"] = infer_ai_related(repo_info)
                        if result.get("domain") not in DOMAINS:
                            result["domain"] = infer_domain(repo_info)
                        return result
                    continue
                else:
                    continue
                    
            except Exception as e:
                log.warning("LLM Error (%s): %s", provider['name'], e)
                continue
        
        # All providers failed, use basic analysis
        return self._basic_analysis(repo_info)
    
    def _basic_analysis(self, repo_info: dict) -> dict:
        """Basic analysis without LLM."""
        description = repo_info.get('description', '').lower()
        name = repo_info.get('full_name', '').lower()
        
        coding_keywords = [
            'ai', 'ml', 'machine learning', 'deep learning', 'llm', 'gpt', 'transformer', 
            'neural', 'model', 'inference', 'training', 'agent', 'code', 'copilot',
            'editor', 'ide', 'vscode', 'vim', 'emacs', 'debug', 'test', 'lint', 'format',
            'framework', 'library', 'sdk', 'cli', 'api', 'database', 'docker', 'kubernetes',
            'devops', 'ci/cd', 'git', 'github', 'programming', 'python', 'javascript', 'rust',
            'developer', 'coding', 'automation', 'refactor', 'deploy'
        ]
        
        is_coding = any(keyword in description or keyword in name for keyword in coding_keywords)
        
        # Determine category
        category = "기타 개발 도구"
        if any(kw in description for kw in ['ai', 'ml', 'llm', 'model', 'neural']):
            category = "AI/ML 도구"
        elif any(kw in description for kw in ['editor', 'ide', 'vscode']):
            category = "코드 에디터/IDE"
        elif any(kw in description for kw in ['framework', 'library']):
            category = "개발 프레임워크"
        elif any(kw in description for kw in ['docker', 'kubernetes', 'devops', 'ci/cd']):
            category = "DevOps/인프라"
        elif any(kw in description for kw in ['language', 'compiler', 'interpreter']):
            category = "프로그래밍 언어/라이브러리"
        
        return {
            "is_ai_tool": infer_ai_related(repo_info),
            "is_coding_tool": is_coding,
            "confidence_score": 0.5 if is_coding else 0.0,
            "domain": infer_domain(repo_info),
            "category": category,
            "digest_section": 1 if category in ("AI/ML 도구", "코드 에디터/IDE") else 2,
            "summary_ko": (repo_info.get('description', 'No description available') or 'No description available')[:200],
            "why_hot": "",
            "key_features": list(dict.fromkeys((repo_info.get("topics") or [])[:3])) or [],
            "install_ko": "저장소 README의 설치 안내 참고",
            "install_cmd": _install_hint_for(repo_info),
            "usecase_ko": "",
            "verdict": "",
            "pros": "",
            "cons": "",
            "target_audience": "Developers",
            "_fallback": True
        }

    @staticmethod
    def passes_digest_filter(repo_info: dict, analysis: dict) -> bool:
        """agents/daily-digest-prompt.md Filter Criteria 판정.

        - is_coding_tool=True
        - stars >= DIGEST_MIN_STARS (급성장 예외는 호출자가 stars 추이로 판단)
        - description 비어있지 않음
        """
        if not analysis.get("is_ai_tool", analysis.get("is_coding_tool")):
            return False
        if (repo_info.get("stars") or 0) < DIGEST_MIN_STARS:
            return False
        if not (repo_info.get("description") or "").strip():
            return False
        return True
