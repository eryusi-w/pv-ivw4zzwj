"""분석済 영상 추적: 이미 md에 반영한 video_id는 다시 분석하지 않음.

파일: output/analyzed_videos.json
  {video_id: {"title": str, "analyzed_at": iso, "repos": [full_name...]}}
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_STATE_FILE = _HERE.parent.parent / "output" / "analyzed_videos.json"


def _load() -> dict:
    if not _STATE_FILE.exists():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def is_analyzed(video_id: str) -> bool:
    return video_id in _load()


def mark_analyzed(video_id: str, title: str = "", repos: list[str] | None = None) -> None:
    state = _load()
    state[video_id] = {
        "title": title,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "repos": repos or [],
    }
    _save(state)


def mark_many(items: list[dict]) -> int:
    """[{'video_id','title','repos'}] 일괄 기록. 반환: 기록 건수."""
    state = _load()
    for it in items:
        vid = it.get("video_id", "")
        if not vid:
            continue
        state[vid] = {
            "title": it.get("title", ""),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "repos": it.get("repos", []),
        }
    _save(state)
    return len(items)


def analyzed_ids() -> set[str]:
    return set(_load())


def allow_reanalyze() -> bool:
    return os.environ.get("FORCE_REANALYZE", "") == "1"
