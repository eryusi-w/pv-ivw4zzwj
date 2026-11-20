"""투자 전략 마크다운/HTML 리포트 생성."""
from __future__ import annotations

import os
from datetime import datetime

import markdown

from config import DEFAULT_OUTPUT_DIR, ChannelData, VideoSummary


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
            color: #1a1a2e;
            background: #fafafa;
        }}
        .container {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}
        h1 {{
            color: #1a1a2e;
            font-size: 2.2rem;
            font-weight: 700;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 0.75rem;
            margin-bottom: 1.5rem;
        }}
        h2 {{
            color: #1e3a5f;
            font-size: 1.6rem;
            font-weight: 600;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }}
        h3 {{
            color: #2d4a6b;
            font-size: 1.3rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 0.75rem;
        }}
        h4 {{
            color: #3d5a7b;
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        p {{
            margin-bottom: 1rem;
        }}
        strong {{
            font-weight: 600;
            color: #1a1a2e;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 0.75rem 1rem;
            border: 1px solid #e2e8f0;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: #f1f5f9;
            font-weight: 600;
            color: #1e3a5f;
        }}
        tr:nth-child(even) td {{
            background: #fafafa;
        }}
        tr:hover td {{
            background: #f0f7ff;
        }}
        ul, ol {{
            margin: 0.75rem 0;
            padding-left: 1.5rem;
        }}
        li {{
            margin-bottom: 0.4rem;
        }}
        li::marker {{
            color: #2563eb;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 2rem 0;
        }}
        code {{
            background: #f1f5f9;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }}
        pre {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 1.25rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5rem 0;
        }}
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        blockquote {{
            border-left: 4px solid #2563eb;
            padding-left: 1rem;
            margin: 1.5rem 0;
            color: #475569;
            font-style: italic;
        }}
        .meta {{
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }}
        .meta strong {{
            color: #334155;
        }}
        .disclaimer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 0.9rem;
            text-align: center;
        }}
        .video-item {{
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid #e2e8f0;
        }}
        .video-item:last-child {{
            border-bottom: none;
        }}
        .published {{
            color: #64748b;
            font-size: 0.85rem;
        }}
        .key-points li {{
            margin-bottom: 0.25rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


class StrategyReport:
    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # markdown 설정: 테이블, 코드 하이라이트 등 지원
        self.md = markdown.Markdown(
            extensions=[
                "tables",
                "fenced_code",
                "codehilite",
                "toc",
                "attr_list",
            ],
            output_format="html5",
        )

    def generate(
        self,
        channels_data: list[ChannelData],
        strategy_md: str = "",
        filename: str | None = None,
    ) -> str:
        """HTML 리포트 파일만 생성합니다."""
        if filename is None:
            base_name = f"investment_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        else:
            base_name = os.path.splitext(filename)[0]

        html_filename = f"{base_name}.html"
        md_content = self._build(channels_data, strategy_md)

        # HTML 저장 경로 결정 및 중복 방지
        html_path = os.path.join(self.output_dir, html_filename)
        if os.path.exists(html_path):
            base, ext = os.path.splitext(html_filename)
            i = 1
            while True:
                new_html_path = os.path.join(self.output_dir, f"{base}_{i}{ext}")
                if not os.path.exists(new_html_path):
                    html_path = new_html_path
                    break
                i += 1

        # HTML 변환 및 저장
        html_content = self._to_html(md_content, base_name)
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        except OSError as exc:
            raise OSError(f"HTML 리포트 저장 실패 ({html_path}): {exc}") from exc

        return html_path

    def _build(self, channels_data: list[ChannelData], strategy_md: str) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        total = sum(len(c.get("videos", [])) for c in channels_data)
        md = f"# 📈 투자 전략 리포트\n\n**생성 일시:** {date_str}\n**분석 영상:** 총 {total}개\n\n---\n\n"
        if strategy_md:
            md += strategy_md.strip() + "\n\n---\n\n"
        md += "## 부록: 영상별 요약\n\n"
        for channel in channels_data:
            md += f"### {channel['name']} ({channel['url']})\n\n"
            videos = channel.get("videos", [])
            if not videos:
                md += "분석된 영상이 없습니다.\n\n"
                continue
            for i, summary in enumerate(videos, 1):
                published_line = (
                    f"- 게시일: {summary['published_at'][:10]}\n"
                    if summary.get("published_at")
                    else ""
                )
                md += (
                    f"#### {i}. {summary.get('title', 'Untitled')}\n"
                    f"- 링크: {summary.get('url', '')}\n"
                    f"{published_line}"
                    f"- 핵심 주장: {summary.get('thesis', '')}\n"
                    f"- 시각: {summary.get('sentiment', '')} "
                    f"(신뢰도 {summary.get('confidence', '')})\n"
                )
                for point in summary.get("key_points", []) or []:
                    md += f"  - {point}\n"
                sectors = summary.get("sectors", []) or []
                stocks = summary.get("stocks", []) or []
                if sectors:
                    md += f"- 섹터: {', '.join(sectors)}\n"
                if stocks:
                    md += f"- 종목: {', '.join(stocks)}\n"
                if summary.get("strategy_short"):
                    md += f"- 단기: {summary['strategy_short']}\n"
                if summary.get("strategy_long"):
                    md += f"- 중장기: {summary['strategy_long']}\n"
                risks = summary.get("risks", []) or []
                if risks:
                    md += f"- 리스크: {', '.join(risks)}\n"
                md += "\n"
        md += "---\n본 문서는 정보 제공용이며 투자 권유가 아닙니다.\n"
        return md

    def _to_html(self, md_content: str, title: str) -> str:
        """마크다운을 HTML로 변환하고 템플릿에 적용."""
        # 마크다운 → HTML 변환
        html_body = self.md.convert(md_content)
        # 제목에서 타임스탬프 부분 제거하여 깔끔한 페이지 제목 생성
        clean_title = "투자 전략 리포트"
        return HTML_TEMPLATE.format(title=clean_title, content=html_body)
