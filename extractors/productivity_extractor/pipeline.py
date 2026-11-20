"""4대 카테고리(업무생산성/생활금융/모바일/부업) 통합 수집 파이프라인.

일자별(YYYYMMDD_HHMMSS)로 분석 JSON과 리포트를 보존하며,
blog_recommendation.txt에 카테고리별 1순위 추천 포스팅을 각각 생성합니다.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import ContentItem, DEFAULT_OUTPUT_DIR, MAIN_CATEGORIES
from modules.llm import ContentLLM
from sources.multi_collector import MultiCategoryCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


class MultiCategoryPipeline:
    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = os.path.normpath(os.path.join(CURRENT_DIR, output_dir))
        os.makedirs(self.output_dir, exist_ok=True)
        self.llm = ContentLLM()
        self.collector = MultiCategoryCollector()

    def run(self, category: str | None = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log.info("=== 4대 카테고리 자동화 수집 파이프라인 시작 (일시: %s) ===", timestamp)

        if category and category in MAIN_CATEGORIES:
            raw_items = self.collector.collect_by_category(category)
            log.info("단일 카테고리 '%s' 수집: %d건", category, len(raw_items))
        else:
            raw_items = self.collector.collect_all()
            log.info("4대 카테고리 전체 수집: %d건", len(raw_items))

        analyzed_items: list[ContentItem] = []
        log.info("총 %d건 아이템 LLM 분석 시작...", len(raw_items))
        for idx, item in enumerate(raw_items, 1):
            log.info("[%d/%d] [%s] 분석 중: %s", idx, len(raw_items), item.get("main_category", ""), item["title"][:35])
            analyzed = self.llm.analyze_item(
                title=item["title"],
                text=item.get("description", ""),
                source_name=item.get("source_name", "큐레이션"),
                main_category=item.get("main_category", "업무·생산성"),
                sub_category=item.get("sub_category", "일반"),
                url=item.get("url", ""),
                published_at=item.get("published_at", datetime.now().strftime("%Y-%m-%d")),
            )
            analyzed_items.append(analyzed)

        # 1. 일자별 JSON
        json_path = os.path.join(self.output_dir, f"analysis_{timestamp}.json")
        payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": timestamp,
            "total_items": len(analyzed_items),
            "categories": MAIN_CATEGORIES,
            "items": analyzed_items,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        log.info("일자별 분석 JSON 저장 완료: %s", json_path)

        # 2. 일자별 HTML 리포트
        html_path = os.path.join(self.output_dir, f"report_{timestamp}.html")
        self._generate_html_report(html_path, payload)
        log.info("일자별 HTML 리포트 저장 완료: %s", html_path)

        # 3. 4대 카테고리별 1순위 추천 텍스트
        rec_path = os.path.join(self.output_dir, "blog_recommendation.txt")
        self._generate_blog_recommendations(rec_path, analyzed_items)
        log.info("4대 카테고리 추천 원고 재료 저장 완료: %s", rec_path)

        # 4. 뷰어 대시보드 갱신
        try:
            from build_viewer import build_viewer
            viewer_path = build_viewer(self.output_dir)
            log.info("뷰어 대시보드 갱신 완료: %s", viewer_path)
        except Exception as e:
            log.warning("뷰어 갱신 오류 (무시 가능): %s", e)

        return json_path

    def _generate_html_report(self, path: str, payload: dict[str, Any]) -> None:
        items = payload["items"]
        cards_html = ""
        for it in items:
            features = "".join(f"<li>{f}</li>" for f in it["core_features"])
            steps = "".join(f"<li>{s}</li>" for s in it["step_by_step"])
            keywords = " ".join(f'<span class="tag">#{k}</span>' for k in it["keywords"])
            cards_html += f"""
            <div class="card">
                <div class="card-header">
                    <span class="badge">{it['main_category']} &gt; {it['sub_category']}</span>
                    <span class="source">{it['source_name']}</span>
                </div>
                <h2>{it['blog_title_candidate']}</h2>
                <p class="summary">{it['summary']}</p>
                <div class="section-title">🎯 대상 독자</div>
                <p class="desc">{it['target_audience']}</p>
                <div class="section-title">✨ 핵심 실무 특징</div>
                <ul>{features}</ul>
                <div class="section-title">🚀 3단계 실천 가이드</div>
                <ol>{steps}</ol>
                <div class="section-title">💡 실전 팁 / 프롬프트 / 설정</div>
                <pre><code>{it['practical_prompt_or_tips']}</code></pre>
                <div class="tags">{keywords}</div>
                <div class="card-footer">
                    <a href="{it['url']}" target="_blank" class="btn">원문/공식 링크 →</a>
                </div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>4대 카테고리 트래픽 리포트 ({payload['timestamp']})</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 2rem; margin: 0; }}
  .container {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; color: #0f172a; }}
  .meta {{ color: #64748b; font-size: 0.9rem; margin-bottom: 2rem; }}
  .card {{ background: #fff; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }}
  .badge {{ background: #e0e7ff; color: #3730a3; padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
  .source {{ font-size: 0.8rem; color: #64748b; }}
  h2 {{ font-size: 1.25rem; margin-top: 0; margin-bottom: 0.8rem; color: #1e293b; line-height: 1.4; }}
  .summary {{ font-size: 0.95rem; color: #475569; margin-bottom: 1rem; line-height: 1.5; }}
  .section-title {{ font-size: 0.85rem; font-weight: 700; color: #0f172a; margin-top: 1rem; margin-bottom: 0.4rem; }}
  ul, ol {{ margin: 0; padding-left: 1.2rem; font-size: 0.9rem; color: #334155; }}
  li {{ margin-bottom: 0.3rem; }}
  pre {{ background: #0f172a; color: #e2e8f0; padding: 0.8rem; border-radius: 6px; font-size: 0.85rem; overflow-x: auto; white-space: pre-wrap; }}
  .tags {{ margin-top: 1rem; }}
  .tag {{ font-size: 0.75rem; color: #2563eb; margin-right: 0.5rem; }}
  .card-footer {{ margin-top: 1.2rem; text-align: right; }}
  .btn {{ display: inline-block; padding: 0.4rem 0.8rem; background: #2563eb; color: #fff; text-decoration: none; border-radius: 6px; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>📈 4대 카테고리 블로그 유입 리포트</h1>
  <div class="meta">수집 일시: {payload['generated_at']} | 총 {payload['total_items']}개 항목</div>
  {cards_html}
</div>
</body>
</html>
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_blog_recommendations(self, path: str, items: list[ContentItem]) -> None:
        lines = [
            "=" * 60,
            f"  네이버 블로그 4대 카테고리별 1순위 추천 글감 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            "=" * 60,
            "",
        ]

        for cat in MAIN_CATEGORIES:
            cat_items = [it for it in items if it["main_category"] == cat]
            if not cat_items:
                continue
            top = cat_items[0]
            lines.extend([
                f"[{cat}] 1순위 추천 글감",
                f"- 추천제목: {top['blog_title_candidate']}",
                f"- 세부분야: {top['sub_category']} ({top['source_name']})",
                f"- 타겟독자: {top['target_audience']}",
                f"- 핵심요약: {top['summary']}",
                f"- 핵심특징: 1) {top['core_features'][0] if len(top['core_features'])>0 else ''} | 2) {top['core_features'][1] if len(top['core_features'])>1 else ''}",
                f"- 실전팁/프롬프트: {top['practical_prompt_or_tips']}",
                f"- 추천태그: {', '.join(top['keywords'])}",
                f"- 원문링크: {top['url']}",
                "-" * 60,
                "",
            ])

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="4대 카테고리 수집 파이프라인")
    parser.add_argument("--category", type=str, choices=MAIN_CATEGORIES, help="특정 카테고리만 수집")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_DIR, help="출력 폴더")
    args = parser.parse_args()

    pipeline = MultiCategoryPipeline(output_dir=args.output)
    pipeline.run(category=args.category)


if __name__ == "__main__":
    main()
