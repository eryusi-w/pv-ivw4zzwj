import logging
import os
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)


class DocumentGenerator:
    """Generates markdown reports from analysis results."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize document generator."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_markdown_report(self, video_metadata: dict, tools: list[dict], 
                                  filename: Optional[str] = None) -> str:
        """Generate markdown report from analysis results."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coding_tools_report_{timestamp}.md"
        
        markdown_content = self._build_markdown(video_metadata, tools)

        output_path = os.path.join(self.output_dir, filename)
        # Handle file naming collision
        if os.path.exists(output_path):
            base, ext = os.path.splitext(filename)
            i = 1
            while True:
                new_path = os.path.join(self.output_dir, f"{base}_{i}{ext}")
                if not os.path.exists(new_path):
                    output_path = new_path
                    break
                i += 1

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        log.info("Generated report: %s", output_path)
        return output_path
    
    def _build_markdown(self, video_metadata: dict, tools: list[dict]) -> str:
        """Build markdown content."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        md = f"""# 🚀 [GitHub Awesome] 코딩 도구 리포트

**생성 일시:** {date_str}

---

"""
        
        # Show ALL tools (no filtering by is_coding_tool)
        if not tools:
            md += "## 분석된 도구가 없습니다.\n"
            return md
        
        md += f"## 총 {len(tools)}개의 도구가 발견되었습니다.\n\n"
        
        for i, tool in enumerate(tools, 1):
            repo = tool.get('repo_info', {})
            analysis = tool.get('analysis', {})
            
            license_info = repo.get('license', 'N/A') or 'N/A'
            
            # Use analysis summary if available, otherwise use repo description
            summary = analysis.get('summary_ko', '') or repo.get('description', 'N/A') or 'N/A'
            category = analysis.get('category', 'N/A') or 'N/A'
            target = analysis.get('target_audience', 'N/A') or 'N/A'
            
            md += f"""### {i}. {repo.get('full_name', 'Unknown')}
* **카테고리:** {category}
* **라이선스:** {license_info}
* **링크:** [GitHub 바로가기]({repo.get('html_url', '#')})
* **개요:** {summary}
* **주요 특징:**
"""
            
            features = analysis.get('key_features', [])
            if features:
                for feature in features:
                    md += f"  * {feature}\n"
            else:
                md += "  * (상세 정보 없음)\n"
            
            md += f"\n* **대상 개발자:** {target}\n\n---\n\n"
        
        return md

    def build_digest_row(self, repo: dict, analysis: dict, date_str: Optional[str] = None) -> str:
        """agents/AGENTS.md Step 4 아코디언 테이블 행 생성.

        신템플릿: 요약/왜뜨나/기능/설치/용도/메타 한 번에.
        analysis에 why_hot·install_hint·usecase_ko가 있으면 사용한다.
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        name = repo.get("full_name", "Unknown").split("/")[-1]
        url = repo.get("html_url", "#")
        summary = analysis.get("summary_ko", "") or repo.get("description", "") or "N/A"
        why = (analysis.get("why_hot") or "").strip()
        features = analysis.get("key_features", []) or []
        if features:
            items = "".join(f"<li>{f}</li>" for f in features[:5])
            feature_html = f"<br><b>핵심 기능:</b><br><ul>{items}</ul>"
        elif repo.get("topics"):
            items = "".join(f"<li>{t}</li>" for t in repo["topics"][:3])
            feature_html = f"<br><b>핵심 기능:</b><br><ul>{items}</ul>"
        else:
            feature_html = ""
        why_html = f"<br>🔥 <b>왜 뜨나:</b> {why}" if why else ""
        verdict = (analysis.get("verdict") or "").strip()
        verdict_html = f"<br>✅ <b>한줄 평:</b> {verdict}" if verdict else ""
        pros = (analysis.get("pros") or "").strip()
        cons = (analysis.get("cons") or "").strip()
        pc_html = ""
        if pros or cons:
            pc_html = "<br>👍 <b>장점:</b> " + (pros or "-")
            if cons:
                pc_html += "<br>⚠️ <b>주의:</b> " + cons
        install_ko = (analysis.get("install_ko") or "").strip()
        install = (analysis.get("install_cmd") or analysis.get("install_hint") or "").strip()
        install_html = ""
        if install_ko or install:
            install_html = "<br>💻 <b>설치:</b> " + install_ko
            if install:
                install_html += f" <code>{install}</code>"
        usecase = (analysis.get("usecase_ko") or "").strip()
        use_html = f"<br>🎯 <b>추천 용도:</b> {usecase}" if usecase else ""
        pushed = (repo.get("pushed_at") or "")[:10]
        meta = f"<b>라이선스:</b> {repo.get('license', 'N/A')}"
        if pushed:
            meta += f" | <b>최근푸시:</b> {pushed}"
        if repo.get("latest_release"):
            meta += f" | <b>릴리즈:</b> {repo['latest_release']}"
        return (
            f"| [**{name}**]({url}) "
            f"| <details><summary><b>{summary} [상세 열기]</b></summary>"
            f"<br>{summary}.{verdict_html}{why_html}{use_html}{install_html}{pc_html}"
            f"<br><br>{meta}{feature_html}</details> "
            f"| {date_str} |"
        )

    def build_digest_rows(self, tools: list[dict], date_str: Optional[str] = None) -> list[str]:
        """분석 결과 리스트를 digest 테이블 행 리스트로 변환."""
        return [
            self.build_digest_row(t.get("repo_info", {}), t.get("analysis", {}), date_str)
            for t in tools
        ]