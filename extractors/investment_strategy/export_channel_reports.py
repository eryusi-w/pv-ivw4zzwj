"""analysis_*.json으로부터 채널별 개별 HTML 리포트를 생성합니다.

pipeline이 채널별 HTML 저장을 지원하기 전의 과거 분석 데이터에 대해
한 번 실행하면 됩니다. 사용법: python export_channel_reports.py [output_dir]
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_OUTPUT_DIR
from report import StrategyReport


def main() -> None:
    output_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    reporter = StrategyReport(output_dir=output_dir)

    for path in sorted(glob.glob(os.path.join(output_dir, "analysis_*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        base = os.path.basename(path)
        m = re.match(r"analysis_(\d{8}_\d{6})", base)
        stamp = m.group(1) if m else "unknown"
        for channel in data.get("channels", []):
            name = channel.get("name", "unknown")
            out = reporter.generate(
                [channel], "", filename=f"{name}_{stamp}"
            )
            print(f"{base} / {name} -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
