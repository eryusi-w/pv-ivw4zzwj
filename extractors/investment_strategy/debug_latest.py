import sys
import os
import logging

# Set working directory to project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import InvestmentPipeline
from config import CHANNELS

# Suppress excessive logging
logging.basicConfig(level=logging.INFO)

def check_latest():
    pipe = InvestmentPipeline(videos_per_channel=1)
    print("\n=== Current Latest Videos according to YouTube API ===")
    for ch in CHANNELS:
        try:
            v_ids = pipe._list_channel_videos(ch["handle"])
            if v_ids:
                vid = v_ids[0]
                content = pipe.analyzer.analyze(vid)
                print(f"[{ch['name']}]")
                print(f"  Title: {content.metadata.title}")
                print(f"  Published At: {content.metadata.published_at}")
                print(f"  URL: https://www.youtube.com/watch?v={vid}")
            else:
                print(f"[{ch['name']}] No videos found.")
        except Exception as e:
            print(f"[{ch['name']}] Error: {e}")
    print("======================================================\n")

if __name__ == "__main__":
    check_latest()
