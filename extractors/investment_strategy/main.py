"""CLI: python main.py [--videos 5] [--channel 송팀장] [--out output]"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

log = logging.getLogger(__name__)



sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CHANNELS, DEFAULT_OUTPUT_DIR, DEFAULT_VIDEOS_PER_CHANNEL, DEFAULT_WORKERS
from pipeline import InvestmentPipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="유튜브 투자 채널 분석 → 투자 전략 문서 생성")
    parser.add_argument("--videos", type=int, default=DEFAULT_VIDEOS_PER_CHANNEL,
                        help="채널당 최근 영상 수 (기본 5)")
    parser.add_argument("--channel", action="append", default=None,
                        help="특정 채널만 분석 (이름 또는 핸들, 반복 가능)")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_DIR, help="출력 디렉토리")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"병렬 처리 워커 수 (기본 {DEFAULT_WORKERS}, 1이면 순차 실행)")
    args = parser.parse_args()
    if args.videos < 1:
        parser.error("--videos는 1 이상이어야 합니다.")
    if args.workers < 1:
        parser.error("--workers는 1 이상이어야 합니다.")

    channels = CHANNELS
    if args.channel:
        wanted = set(args.channel)
        channels = [c for c in CHANNELS if c["name"] in wanted or c["handle"] in wanted]
        if not channels:
            log.error("일치하는 채널 없음. 사용 가능: %s", [c['name'] for c in CHANNELS])
            sys.exit(1)

    pipeline = InvestmentPipeline(
        videos_per_channel=args.videos, output_dir=args.out, max_workers=args.workers
    )
    result = pipeline.run(channels)
    log.info("결과: %s", json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
