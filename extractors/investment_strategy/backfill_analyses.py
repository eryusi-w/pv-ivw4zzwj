"""기존 investment_strategy_*.html 리포트를 analysis_*.json으로 변환 (1회성 백필).

사용법: python backfill_analyses.py [output_dir]
"""
from __future__ import annotations

import json
import os
import re
import sys

from bs4 import BeautifulSoup

from config import DEFAULT_OUTPUT_DIR

FIELD_PREFIXES = {
    "링크": "url",
    "게시일": "published_at",
    "핵심 주장": "thesis",
    "시각": "sentiment_raw",
    "섹터": "sectors",
    "종목": "stocks",
    "단기": "strategy_short",
    "중장기": "strategy_long",
    "리스크": "risks",
}


def _split_list(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def _parse_video(h4, ul) -> dict:
    video: dict = {
        "title": re.sub(r"^\d+\.\s*", "", h4.get_text(" ", strip=True))
    }
    key_points: list[str] = []
    for li in ul.find_all("li", recursive=False):
        text = li.get_text(" ", strip=True)
        # 중첩 ul(세부 포인트)은 key_points로
        nested = li.find("ul")
        if nested:
            key_points.extend(
                n.get_text(" ", strip=True) for n in nested.find_all("li", recursive=False)
            )
        matched = False
        for prefix, field in FIELD_PREFIXES.items():
            if text.startswith(prefix + ":") or text.startswith(prefix + "："):
                value = re.sub(r"^[^:：]+[:：]\s*", "", text).strip()
                if field == "sentiment_raw":
                    m = re.match(r"(\w+)\s*\(신뢰도\s*([\d.]+)\)", value)
                    video["sentiment"] = m.group(1) if m else value
                    try:
                        video["confidence"] = float(m.group(2)) if m else 0.0
                    except ValueError:
                        video["confidence"] = 0.0
                elif field in ("sectors", "stocks"):
                    video[field] = _split_list(value)
                elif field == "risks":
                    video[field] = _split_list(value)
                else:
                    video[field] = value
                matched = True
                break
        if not matched and not nested:
            key_points.append(text)
    if key_points:
        video["key_points"] = key_points
    return video


def _serialize_nodes(nodes) -> str:
    return "".join(str(n) for n in nodes)


def parse_report(html_path: str) -> dict | None:
    soup = BeautifulSoup(open(html_path, encoding="utf-8").read(), "html.parser")
    container = soup.select_one(".container") or soup.body
    if not container:
        return None

    generated_at = ""
    p = container.find("p")
    if p:
        m = re.search(r"생성 일시:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", p.get_text(" ", strip=True))
        if m:
            generated_at = m.group(1).strip()

    appendix = container.find("h2", string=lambda s: s and "부록" in s)
    if not appendix:
        return None

    # 전략 섹션: 헤더(p, hr) 이후 ~ 부록 h2 이전
    strategy_nodes = []
    for node in container.children:
        if node is appendix:
            break
        if getattr(node, "name", None) in ("h1", "p", "hr"):
            continue
        strategy_nodes.append(node)
    strategy_html = _serialize_nodes(strategy_nodes)

    channels = []
    current = None
    node = appendix.find_next_sibling()
    while node:
        if node.name == "h3":
            text = node.get_text(" ", strip=True)
            m = re.match(r"(.+?)\s*\((https?://[^)]+)\)", text)
            current = {
                "name": m.group(1).strip() if m else text,
                "handle": "",
                "url": m.group(2).strip() if m else "",
                "videos": [],
            }
            channels.append(current)
        elif node.name == "h4" and current is not None:
            ul = node.find_next_sibling("ul")
            if ul:
                current["videos"].append(_parse_video(node, ul))
        node = node.find_next_sibling()

    base = os.path.splitext(os.path.basename(html_path))[0]
    m = re.search(r"(\d{8})_(\d{6})", base)
    date = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else generated_at[:10]
    stamp = f"{m.group(1)}_{m.group(2)}" if m else ""

    return {
        "generated_at": generated_at or date,
        "date": date,
        "stamp": stamp,
        "strategy_html": strategy_html,
        "channels": channels,
    }


def main() -> None:
    output_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    reports = sorted(
        f for f in os.listdir(output_dir)
        if f.startswith("investment_strategy_") and f.endswith(".html")
    )
    for name in reports:
        path = os.path.join(output_dir, name)
        data = parse_report(path)
        if not data or not data["channels"]:
            print(f"skip {name}: 파싱 실패")
            continue
        stamp = data.pop("stamp")
        out = os.path.join(output_dir, f"analysis_{stamp}.json" if stamp else f"analysis_{name}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        n = sum(len(c["videos"]) for c in data["channels"])
        print(f"{name} -> {os.path.basename(out)} ({n} videos)")

    try:
        from build_viewer import build as build_viewer
        build_viewer(
            os.path.abspath(output_dir),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer.html"),
        )
    except Exception as exc:
        print(f"뷰어 갱신 실패: {exc}")


if __name__ == "__main__":
    main()
