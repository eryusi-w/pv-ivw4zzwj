"""YouTube 기간별 후보와 GitHub 인기·주간 Trending 프로젝트 수집.

daily-digest-prompt.md Line 27 참조:
    기본은 최근 3일 영상이며 --from-date/--to-date로 백필할 수 있다.
    GitHub의 분야별 별점순 검색과 주간 Trending도 함께 후보로 보탠다.

주의: 실행할 때마다 YouTube API에서 지정 기간의 영상을 실시간 조회한다.
수집본(manuagi_repos.json)은 매 실행 덮어쓰며, 누적 아카이브는 manuagi_to_digest.py가 관리한다.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser

import json
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlparse

import requests

_CODEX_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODEX_HOME not in sys.path:
    sys.path.insert(0, _CODEX_HOME)
# 저장소와 같은 상위 디렉터리(naver-blog)의 youtube_toolkit·패키지 import 경로 확보
_PARENT = os.path.dirname(_CODEX_HOME)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
# youtube_toolkit은 projects/ 아래에 남아 있으므로 두 단계 더 위도 필요
_PROJECTS = os.path.dirname(os.path.dirname(_PARENT))
if _PROJECTS not in sys.path:
    sys.path.insert(0, _PROJECTS)

from dotenv import load_dotenv
load_dotenv()

from youtube_toolkit import YoutubeAnalyzer  # type: ignore[import-not-found]
from github_awesome_extractor.modules import LinkExtractor  # type: ignore[import-not-found]
from github_awesome_extractor.sources.state import (  # type: ignore[import-not-found]
    allow_reanalyze, analyzed_ids, is_analyzed,
)

CHANNEL_HANDLES = [
    "@ManuAGI",
    "@GithubAwesome",
    "@AIstackengineer",
    "@Mindung-EasyAI",
    "@honjobs",
    "@Solostack-1",
    "@TheLayperson",
    "@CodingArtisan",
]
DAYS_WINDOW = 3
TARGET_TIMEZONE = timezone(timedelta(hours=9), name="KST")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
GITHUB_DAILY_TRENDING_URL = "https://github.com/trending?since=daily"
GITHUB_TRENDING_URL = "https://github.com/trending?since=weekly"
POPULAR_SEARCH_QUERIES = (
    ("ai", "AI stars:>=50 in:name,description,topics"),
    ("llm", "LLM stars:>=25 in:name,description,topics"),
    ("agents", '"coding agent" stars:>=10 in:name,description,topics'),
    ("mcp", "MCP stars:>=10 in:name,description,topics"),
    ("token_optimizer", '"token-optimizer" in:name stars:>=10'),
    ("context_window", '"context window" in:readme stars:>=10'),
    ("machine_learning", '"machine learning" stars:>=50 in:name,description,topics'),
    ("generative_ai", '"generative AI" stars:>=25 in:name,description,topics'),
)


class _TrendingRepoParser(HTMLParser):
    """Extract repository paths from GitHub's weekly trending page."""

    def __init__(self) -> None:
        super().__init__()
        self.repositories: list[tuple[str, str]] = []
        self.repository_details: dict[str, dict] = {}
        self._article_depth = 0
        self._current_repo: tuple[str, str] | None = None
        self._capture_field = ""
        self._capture_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "article":
            self._article_depth += 1
            self._current_repo = None
        if tag != "a":
            if self._article_depth and self._current_repo:
                if tag == "p":
                    self._capture_field = "description"
                    self._capture_text = []
                elif tag == "span" and attributes.get("itemprop") == "programmingLanguage":
                    self._capture_field = "language"
                    self._capture_text = []
            return
        if not self._article_depth:
            return
        href = attributes.get("href", "") or ""
        path = urlparse(href).path.strip("/")
        parts = path.split("/")
        reserved = {"topics", "collections", "sponsors", "trending", "login", "signup"}
        if len(parts) == 2 and all(parts) and parts[0].casefold() not in reserved:
            pair = (parts[0], parts[1])
            if pair not in self.repositories:
                self.repositories.append(pair)
            if self._article_depth:
                self._current_repo = pair
                self.repository_details.setdefault(
                    f"{pair[0]}/{pair[1]}".casefold(), {"description": "", "language": ""}
                )

    def handle_data(self, data: str) -> None:
        if self._capture_field and self._article_depth and self._current_repo:
            self._capture_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "article":
            self._article_depth = max(0, self._article_depth - 1)
            self._current_repo = None
            self._capture_field = ""
        elif tag in {"p", "span"} and self._capture_field and self._current_repo:
            key = f"{self._current_repo[0]}/{self._current_repo[1]}".casefold()
            value = " ".join(" ".join(self._capture_text).split())
            self.repository_details.setdefault(key, {})[self._capture_field] = value
            self._capture_field = ""
            self._capture_text = []


def _github_discoveries(popular_limit: int, trending_limit: int) -> tuple[list[dict], dict[str, int]]:
    """Search multiple AI domains and supplement candidates with weekly Trending."""
    candidates: list[dict] = []
    by_key: dict[str, dict] = {}
    counts = {"popular": 0, "daily_trending": 0, "weekly_trending": 0}
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if popular_limit:
        query_count = len(POPULAR_SEARCH_QUERIES)
        base_limit, remainder = divmod(popular_limit, query_count)
        for index, (query_key, query) in enumerate(POPULAR_SEARCH_QUERIES):
            per_query_limit = base_limit + (1 if index < remainder else 0)
            if per_query_limit == 0:
                continue
            try:
                response = requests.get(
                    GITHUB_SEARCH_URL,
                    params={
                        "q": f"{query} fork:false archived:false",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": min(100, per_query_limit),
                    },
                    headers=headers,
                    timeout=20,
                )
                # 잘못되었거나 만료된 토큰은 한 번 제거하고 이후 검색도 공개 요청으로 진행한다.
                if response.status_code == 401 and "Authorization" in headers:
                    headers = {"Accept": "application/vnd.github+json"}
                    response = requests.get(
                        GITHUB_SEARCH_URL,
                        params={
                            "q": f"{query} fork:false archived:false",
                            "sort": "stars",
                            "order": "desc",
                            "per_page": min(100, per_query_limit),
                        },
                        headers=headers,
                        timeout=20,
                    )
                response.raise_for_status()
                for repo in response.json().get("items", []):
                    full_name = repo.get("full_name", "")
                    if "/" not in full_name:
                        continue
                    owner, name = full_name.split("/", 1)
                    key = full_name.casefold()
                    candidate = by_key.get(key)
                    if candidate is None:
                        candidate = {
                            "owner": owner,
                            "repo": name,
                            "source_video": "",
                            "source_video_id": "",
                            "source_url": "",
                            "discovery_sources": ["popular"],
                            "discovery_queries": [],
                            "repository_info": {
                                "full_name": full_name,
                                "html_url": repo.get("html_url", f"https://github.com/{full_name}"),
                                "stars": repo.get("stargazers_count", 0),
                                "forks": repo.get("forks_count", 0),
                                "open_issues": repo.get("open_issues_count", 0),
                                "language": repo.get("language") or "Unknown",
                                "description": repo.get("description") or "",
                                "topics": repo.get("topics") or [],
                                "homepage": repo.get("homepage") or "",
                                "default_branch": repo.get("default_branch") or "",
                                "pushed_at": repo.get("pushed_at") or "",
                                "updated_at": repo.get("updated_at") or "",
                                "latest_release": "",
                                "readme_snippet": "",
                                "license": (repo.get("license") or {}).get("spdx_id", "N/A"),
                            },
                        }
                        by_key[key] = candidate
                    candidate["discovery_queries"].append(query_key)
                print(f"[INFO] GitHub 검색 '{query_key}': {len(response.json().get('items', []))}개")
            except Exception as exc:
                print(f"[WARN] GitHub 검색 '{query_key}'을 건너뜁니다: {exc}")
        candidates.extend(by_key.values())
        counts["popular"] = len(candidates)

    if trending_limit:
        for source, url in (
            ("daily_trending", GITHUB_DAILY_TRENDING_URL),
            ("weekly_trending", GITHUB_TRENDING_URL),
        ):
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": "github-awesome-extractor"},
                    timeout=20,
                )
                response.raise_for_status()
                parser = _TrendingRepoParser()
                parser.feed(response.text)
                for owner, name in parser.repositories[:trending_limit]:
                    details = parser.repository_details.get(
                        f"{owner}/{name}".casefold(), {}
                    )
                    candidates.append({"owner": owner, "repo": name, "source_video": "",
                                       "source_video_id": "", "source_url": "",
                                       "discovery_sources": [source],
                                       "repository_info": {
                                           "full_name": f"{owner}/{name}",
                                           "html_url": f"https://github.com/{owner}/{name}",
                                           "description": details.get("description", ""),
                                           "language": details.get("language", "Unknown"),
                                           "topics": [],
                                           "stars": 0,
                                           "license": "N/A",
                                           "latest_release": "",
                                           "readme_snippet": "",
                                       }})
                    counts[source] += 1
            except Exception as exc:
                label = "일간" if source == "daily_trending" else "주간"
                print(f"[WARN] {label} Trending 검색을 건너뜁니다: {exc}")
    return candidates, counts


def _target_bounds(
    from_date: date | None, to_date: date | None
) -> tuple[datetime, datetime, str, str]:
    """날짜 범위를 서울 시간 기준의 [시작, 끝) 구간으로 변환한다."""
    if (from_date is None) != (to_date is None):
        raise ValueError("--from-date와 --to-date를 함께 지정하세요.")

    if from_date is None:
        end_at = datetime.now(TARGET_TIMEZONE)
        start_at = end_at - timedelta(days=DAYS_WINDOW)
        return (
            start_at,
            end_at,
            start_at.date().isoformat(),
            end_at.date().isoformat(),
        )

    if from_date > to_date:
        raise ValueError("--from-date는 --to-date보다 늦을 수 없습니다.")
    start_at = datetime.combine(from_date, time.min, tzinfo=TARGET_TIMEZONE)
    end_at = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=TARGET_TIMEZONE)
    return start_at, end_at, from_date.isoformat(), to_date.isoformat()


def _videos_in_date_range(
    analyzer: YoutubeAnalyzer,
    handle: str,
    start_at: datetime,
    end_at: datetime,
    max_results: int,
) -> list:
    """YouTube 검색 API에서 날짜 범위에 해당하는 영상만 가져와 분석한다."""
    api_key = analyzer.config.api_key
    if not api_key:
        raise RuntimeError("날짜 범위 검색에는 YOUTUBE_API_KEY가 필요합니다.")

    channel_id = analyzer.channels.resolve_channel_id(handle)
    video_ids: list[str] = []
    page_token = ""
    while len(video_ids) < max_results:
        params = {
            "part": "id",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "publishedAfter": start_at.astimezone(timezone.utc).isoformat(),
            "publishedBefore": end_at.astimezone(timezone.utc).isoformat(),
            "maxResults": min(50, max_results - len(video_ids)),
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params=params,
            timeout=analyzer.config.timeout,
            verify=True,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            message = payload["error"].get("message", "YouTube API 검색 실패")
            raise RuntimeError(message)

        video_ids.extend(
            item["id"]["videoId"]
            for item in payload.get("items", [])
            if item.get("id", {}).get("videoId")
        )
        page_token = payload.get("nextPageToken", "")
        if not page_token:
            break

    return analyzer.analyze_many(video_ids[:max_results])


def filter_recent_videos(
    contents: list[dict],
    days: int = DAYS_WINDOW,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[dict]:
    """지정된 시간 범위 또는 최근 N일 영상만 필터링한다."""
    if start_at is None or end_at is None:
        end_at = datetime.now(timezone.utc)
        start_at = end_at - timedelta(days=days)
    recent = []
    for vc in contents:
        published_at = vc.get("metadata", {}).get("published_at")
        if not published_at:
            continue
        try:
            video_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if start_at.astimezone(timezone.utc) <= video_dt < end_at.astimezone(timezone.utc):
            recent.append(vc)
    return recent


def collect_manuagi_github_links(
    from_date: date | None = None,
    to_date: date | None = None,
    max_videos_per_channel: int = 50,
    popular_limit: int = 60,
    trending_limit: int = 20,
) -> dict:
    analyzer = YoutubeAnalyzer()
    extractor = LinkExtractor()
    start_at, end_at, target_from, target_to = _target_bounds(from_date, to_date)
    if max_videos_per_channel < 1:
        raise ValueError("max_videos_per_channel은 1 이상이어야 합니다.")
    if popular_limit < 0 or popular_limit > 100 or trending_limit < 0:
        raise ValueError("popular_limit은 0~100, trending_limit은 0 이상이어야 합니다.")

    all_repos = []
    seen = set()
    videos_meta = []
    skipped = 0
    done_ids = analyzed_ids()
    if done_ids and not allow_reanalyze():
        print(f"[INFO] 분석 완료된 {len(done_ids)}개 영상은 스킵 (FORCE_REANALYZE=1로 강제 재분석)")
    use_frames = os.environ.get("SKIP_FRAMES", "") != "1"
    frames_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "output", "video_frames")

    for handle in CHANNEL_HANDLES:
        print(f"\n[CHANNEL] {handle}")

        # 날짜 범위에 해당하는 영상만 검색해, 초기 백필 때도 오래된 대상이 포함되게 한다.
        recent_videos = _videos_in_date_range(
            analyzer, handle, start_at, end_at, max_videos_per_channel
        )

        if not recent_videos:
            print(f"[{handle}] 채널에서 최근 영상을 찾을 수 없습니다.")
            continue

        # 3일 이내 영상 필터링 (게시일 내림차순 정렬 후 판정)
        recent_contents = [
            {"metadata": vc.metadata.to_dict(), "combined_text": vc.combined_text}
            for vc in recent_videos
        ]
        recent_contents.sort(key=lambda c: c["metadata"].get("published_at", ""), reverse=True)

        recent_videos_filtered = filter_recent_videos(
            recent_contents, start_at=start_at, end_at=end_at
        )

        print(f"[INFO] {handle} 조회 영상: {len(recent_videos)}개")
        print(f"[INFO] 대상 기간 {target_from}–{target_to}: {len(recent_videos_filtered)}개")

        for vc in recent_videos_filtered:
            meta = vc["metadata"]
            title = meta.get("title", "Unknown")
            video_id = meta.get("video_id", "")
            if video_id and video_id in done_ids and not allow_reanalyze():
                print(f"  [SKIP] {title} (분석 완료)")
                skipped += 1
                continue
            # 화면 내용 분석 (프레임 추출 + 비전 요약, 베스트에포트)
            visual_summary, frame_paths = "", []
            if use_frames and video_id:
                try:
                    from youtube_toolkit import frames as _frames  # type: ignore[import-not-found]
                    vis = _frames.analyze_video_visual(video_id, frames_dir)
                    visual_summary = vis.get("visual_summary", "")
                    frame_paths = vis.get("frames", [])
                    print(f"  [VISUAL] {title}: 프레임 {len(frame_paths)}장"
                          + (" (요약 OK)" if visual_summary else " (요약 없음)"))
                except Exception as e:
                    print(f"  [VISUAL] {title} 실패: {e}")
            videos_meta.append({
                "video_id": video_id,
                "title": title,
                "published_at": meta.get("published_at", ""),
                "url": meta.get("url", ""),
                "transcript_excerpt": (vc.get("combined_text", "") or "")[:1500],
                "visual_summary": visual_summary,
                "frames": frame_paths,
            })
            repos = extractor.extract_github_repos(vc["combined_text"])
            for owner, repo in repos:
                key = f"{owner}/{repo}".lower()
                if key not in seen:
                    seen.add(key)
                    all_repos.append({"owner": owner, "repo": repo,
                                      "source_video": title,
                                      "source_video_id": video_id,
                                      "source_url": meta.get("url", "")})
                    print(f"  [FOUND] {owner}/{repo} (from: {title})")

    github_candidates, discovery_counts = _github_discoveries(popular_limit, trending_limit)
    repo_by_key = {f"{r['owner']}/{r['repo']}".casefold(): r for r in all_repos}
    for candidate in github_candidates:
        key = f"{candidate['owner']}/{candidate['repo']}".casefold()
        existing = repo_by_key.get(key)
        if existing is None:
            all_repos.append(candidate)
            repo_by_key[key] = candidate
        else:
            sources = set(existing.get("discovery_sources", []))
            sources.update(candidate.get("discovery_sources", []))
            existing["discovery_sources"] = sorted(sources)
            queries = set(existing.get("discovery_queries", []))
            queries.update(candidate.get("discovery_queries", []))
            if queries:
                existing["discovery_queries"] = sorted(queries)

    # Public API rate limits are smaller without a valid token; prioritize GitHub-discovered rows.
    all_repos.sort(key=lambda item: bool(item.get("discovery_sources")), reverse=True)

    result = {
        "channels": CHANNEL_HANDLES,
        "videos_scanned": len(videos_meta),
        "videos_skipped": skipped,
        "repos_found": len(all_repos),
        "repos": all_repos,
        "videos": videos_meta,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "target_from_date": target_from,
        "target_to_date": target_to,
        "max_videos_per_channel": max_videos_per_channel,
        "discovery_counts": discovery_counts,
        "popular_limit": popular_limit,
        "trending_limit": trending_limit,
    }

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="기존 분석 완료된 영상도 재수집")
    ap.add_argument("--no-frames", action="store_true", help="화면 프레임 분석 생략")
    ap.add_argument("--from-date", type=date.fromisoformat, help="대상 영상 게시 시작일 (YYYY-MM-DD, 서울 시간)")
    ap.add_argument("--to-date", type=date.fromisoformat, help="대상 영상 게시 종료일 (YYYY-MM-DD, 서울 시간, 포함)")
    ap.add_argument(
        "--max-videos-per-channel",
        type=int,
        default=50,
        help="채널별 최대 분석 영상 수 (기본값: 50)",
    )
    ap.add_argument("--popular-limit", type=int, default=60,
                    help="AI·LLM·에이전트·MCP·토큰·컨텍스트·머신러닝 분야별 GitHub 검색 후보 총수 (0이면 생략, 기본값: 60)")
    ap.add_argument("--trending-limit", type=int, default=20,
                    help="GitHub 일간·주간 Trending별 후보 수 (0이면 생략, 기본값: 각 20)")
    args = ap.parse_args()
    if args.force:
        os.environ["FORCE_REANALYZE"] = "1"
    if args.no_frames:
        os.environ["SKIP_FRAMES"] = "1"
    try:
        output = collect_manuagi_github_links(
            from_date=args.from_date,
            to_date=args.to_date,
            max_videos_per_channel=args.max_videos_per_channel,
            popular_limit=args.popular_limit,
            trending_limit=args.trending_limit,
        )
    except ValueError as exc:
        ap.error(str(exc))
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "output",
        "manuagi_repos.json",
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Results saved: {output_path}")
    print(f"   - Videos scanned: {output['videos_scanned']}")
    print(f"   - GitHub projects found: {output['repos_found']}")


if __name__ == "__main__":
    main()
