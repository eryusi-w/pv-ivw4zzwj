import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import json
import logging
from datetime import datetime, timezone
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

# youtube_toolkit (D:\dev\codex-home\projects\youtube_toolkit) import 경로 확보.
# pipeline.py는 .../naver-blog/github_awesome_extractor/ 에 있으므로 세 단계 위의 projects/ 가 대상이다.
_TOOLKIT_PARENT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _TOOLKIT_PARENT not in sys.path:
    sys.path.insert(0, _TOOLKIT_PARENT)

from youtube_toolkit import YoutubeAnalyzer
from modules import (
    LinkExtractor,
    GitHubEnricher,
    LLMClassifier,
    DocumentGenerator
)
from dotenv import load_dotenv
from config.settings import PERFORMANCE


def _load_done_video_ids() -> set[str]:
    """output/analyzed_videos.json에서 이미 분석 완료된 video_id 집합을 읽는다."""
    state_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "analyzed_videos.json"
    )
    if not os.path.exists(state_path):
        return set()
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _mark_video_analyzed(video_id: str, title: str, repos: list[str]) -> None:
    """분석 완료된 영상 video_id를 state 파일에 기록한다."""
    state_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "analyzed_videos.json"
    )
    state: dict = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
    state[video_id] = {
        "title": title,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "repos": repos or [],
    }
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _load_registered_repo_names() -> set[str]:
    """output/manuagi_repos.enriched.json에서 이미 등록된 full_name 집합을 읽는다."""
    enriched_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "manuagi_repos.enriched.json"
    )
    if not os.path.exists(enriched_path):
        return set()
    try:
        with open(enriched_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            str(r.get("full_name", "")).strip().casefold()
            for r in data.get("repos", [])
            if isinstance(r, dict) and r.get("full_name")
        }
    except Exception:
        return set()


class Pipeline:
    """Main pipeline for extracting and analyzing AI tools from YouTube videos."""

    def __init__(self, videos_per_channel: int = 5, force: bool = False):
        load_dotenv()

        # YouTube 수집은 youtube_toolkit 사용 (기존 DataCollector 대체).
        # video_id 외에 watch/youtu.be/shorts/embed/live URL도 직접 입력 가능.
        self.collector = YoutubeAnalyzer()
        self.extractor = LinkExtractor()
        self.github_enricher = GitHubEnricher()
        self.classifier = LLMClassifier(order=["freellmapi"])
        self.doc_generator = DocumentGenerator()
        self.videos_per_channel = videos_per_channel
        self.force = force or os.environ.get("FORCE_REANALYZE", "") == "1"
        self._done_video_ids = set() if self.force else _load_done_video_ids()
        self._registered_repos = set() if self.force else _load_registered_repo_names()

    def _list_channel_videos(self, handle: str) -> list[str]:
        """업로드 플레이리스트 경유(저할당량) 우선, 실패 시 search API 폴백."""
        try:
            video_ids = self.collector.channels.list_uploads_video_ids(
                handle, max_results=self.videos_per_channel
            )
            if video_ids:
                return video_ids
            log.info("%s: uploads 목록 비어있음 → search API 폴백", handle)
        except Exception as exc:
            log.warning("%s: uploads 조회 실패(%s) → search API 폴백", handle, exc)
        return self.collector.channels.list_recent_video_ids(
            handle, max_results=self.videos_per_channel
        )

    def _analyze_single_repo(self, owner: str, repo_name: str, text: str) -> dict:
        """Analyze a single repository with error handling."""
        try:
            log.info("  [%s/%s] Fetching GitHub info...", owner, repo_name)
            repo_info = self.github_enricher.get_repo_info(owner, repo_name)

            # Log stars if available
            stars = repo_info.get('stars', 0)
            if stars and stars > 0:
                log.info("  [%s/%s] Stars: %s", owner, repo_name, f"{stars:,}")

            log.info("  [%s/%s] Analyzing with LLM...", owner, repo_name)
            analysis = self.classifier.analyze_repository(repo_info, text)

            return {"repo_info": repo_info, "analysis": analysis}

        except Exception as e:
            log.error("  [%s/%s] Error: %s", owner, repo_name, e)
            # Return minimal info even on error
            return {
                "repo_info": {
                    "full_name": f"{owner}/{repo_name}",
                    "html_url": f"https://github.com/{owner}/{repo_name}",
                    "stars": 0,
                    "forks": 0,
                    "language": "Unknown",
                    "description": f"GitHub repository: {owner}/{repo_name}",
                    "readme_snippet": "",
                    "updated_at": "",
                    "license": "N/A"
                },
                "analysis": {
                    "is_coding_tool": True,
                    "category": "기타 개발 도구",
                    "summary_ko": f"GitHub 저장소: {owner}/{repo_name}",
                    "key_features": [],
                    "target_audience": "Developers"
                }
            }

    def process_from_text(self, text: str, video_metadata: dict, limit: int = None, workers: int = None) -> dict:
        """Process from raw text input, skipping already analyzed repos."""
        import concurrent.futures

        # Use performance settings if not specified
        if limit is None:
            limit = PERFORMANCE.get("max_repos_per_run", 20)
        if workers is None:
            workers = PERFORMANCE.get("max_workers", 8)

        log.info("=" * 50)
        log.info("Processing from text input...")
        log.info("=" * 50)

        # Extract repos
        repos = self.extractor.extract_github_repos(text)
        log.info("Found %d repositories", len(repos))
        for o, r in repos:
            key = f"{o}/{r}".lower()
            if key in self._registered_repos:
                log.info("  [SKIP] %s/%s - already registered", o, r)
            else:
                log.info("  - %s/%s", o, r)

        if not repos:
            log.info("No GitHub repositories found in text.")
            return {"repos_found": 0, "new_repos": 0, "already_registered": 0, 
                    "tools_analyzed": 0, "missing": [], "report_path": None}

        # Filter out already registered repos
        targets = [(o, r) for o, r in repos if f"{o}/{r}".lower() not in self._registered_repos][:limit]
        log.info("New repos to analyze: %d", len(targets))

        if not targets:
            log.info("All repositories already registered.")
            return {"repos_found": len(repos), "new_repos": 0, "already_registered": len(repos),
                    "tools_analyzed": 0, "missing": [], "report_path": None}

        results_by_key: dict[str, dict] = {}
        missing: list[str] = []
        show_progress = PERFORMANCE.get("progress_bar", True)
        max_workers = max(1, workers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_repo = {
                ex.submit(self._analyze_single_repo, o, r, text): (o, r)
                for o, r in targets
            }
            with tqdm(total=len(targets), desc="Analyzing repositories", unit="repo") as pbar:
                for fut in concurrent.futures.as_completed(future_to_repo):
                    o, r = future_to_repo[fut]
                    key = f"{o}/{r}".lower()
                    try:
                        results_by_key[key] = fut.result(timeout=120)
                        pbar.set_postfix_str(f"{o}/{r}")
                    except Exception as e:
                        log.error("  [%s/%s] WORKER TIMEOUT/ERROR: %s", o, r, e)
                        missing.append(f"{o}/{r}")
                        results_by_key[key] = {
                            "repo_info": {
                                "full_name": f"{o}/{r}",
                                "html_url": f"https://github.com/{o}/{r}",
                                "stars": 0, "forks": 0, "language": "Unknown",
                                "description": "", "readme_snippet": "",
                                "updated_at": "", "license": "N/A",
                                "error": f"worker-failed: {e}",
                            },
                            "analysis": {
                                "is_coding_tool": True,
                                "category": "기타 개발 도구",
                                "summary_ko": f"GitHub 저장소: {o}/{r} (분석 실패, 기본 표시)",
                                "key_features": [],
                                "target_audience": "Developers",
                            },
                        }
                    pbar.update(1)

        # Reorder to input order
        results = [results_by_key[f"{o}/{r}".lower()] for o, r in targets]

        log.info("Analyzed %d/%d new repositories", len(results), len(targets))
        if missing:
            log.info("Missing (filled with fallback): %s", missing)

        # Generate report
        report_path = self.doc_generator.generate_markdown_report(
            video_metadata, results
        )

        log.info("Report generated: %s", report_path)
        log.info("=" * 50)

        return {
            "repos_found": len(repos),
            "new_repos": len(targets),
            "already_registered": len(repos) - len(targets),
            "tools_analyzed": len(results),
            "missing": missing,
            "report_path": report_path
        }

    def process_video(self, video_id_or_url: str) -> dict:
        """Process a single YouTube video (video_id 또는 전체 URL)."""
        log.info("=" * 50)
        log.info("Processing video: %s", video_id_or_url)
        log.info("=" * 50)

        # Step 1: Get transcript and description (youtube_toolkit)
        combined_text, video_metadata = self.collector.get_combined_text(video_id_or_url)
        video_id = video_metadata.get("video_id", video_id_or_url)
        log.info("Text length: %d chars", len(combined_text))

        if not combined_text:
            log.info("No text content found.")
            return {"repos_found": 0, "tools_analyzed": 0, "report_path": None}

        # Step 2: Extract GitHub repos
        repos = self.extractor.extract_github_repos(combined_text)
        log.info("Found %d repositories", len(repos))

        # Step 3: Analyze each repo (parallel)
        import concurrent.futures
        max_repos = PERFORMANCE.get("max_repos_per_run", 20)
        
        # Filter out already registered repos
        targets = [(o, r) for o, r in repos 
                     if f"{o}/{r}".lower() not in self._registered_repos][:max_repos]
        log.info("New repos to analyze: %d", len(targets))
        
        results_by_key: dict[str, dict] = {}
        show_progress = PERFORMANCE.get("progress_bar", True)
        max_workers = PERFORMANCE.get("max_workers", 8)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_repo = {
                ex.submit(self._analyze_single_repo, o, r, combined_text): (o, r)
                for o, r in targets
            }
            if show_progress:
                with tqdm(total=len(targets), desc="Analyzing repositories", unit="repo") as pbar:
                    for fut in concurrent.futures.as_completed(future_to_repo):
                        o, r = future_to_repo[fut]
                        try:
                            results_by_key[f"{o}/{r}".lower()] = fut.result(timeout=120)
                            pbar.set_postfix_str(f"{o}/{r}")
                        except Exception as e:
                            log.error("  [%s/%s] WORKER ERROR: %s", o, r, e)
                            results_by_key[f"{o}/{r}".lower()] = {
                                "repo_info": {
                                    "full_name": f"{o}/{r}",
                                    "html_url": f"https://github.com/{o}/{r}",
                                    "stars": 0, "forks": 0, "language": "Unknown",
                                    "description": "", "readme_snippet": "",
                                    "updated_at": "", "license": "N/A",
                                    "error": str(e),
                                },
                                "analysis": {
                                    "is_coding_tool": True,
                                    "category": "기타 개발 도구",
                                    "summary_ko": f"GitHub 저장소: {o}/{r} (분석 실패, 기본 표시)",
                                    "key_features": [],
                                    "target_audience": "Developers",
                                },
                            }
                        pbar.update(1)
            else:
                for fut in concurrent.futures.as_completed(future_to_repo):
                    o, r = future_to_repo[fut]
                    try:
                        results_by_key[f"{o}/{r}".lower()] = fut.result(timeout=120)
                    except Exception as e:
                        log.error("  [%s/%s] WORKER ERROR: %s", o, r, e)
                        results_by_key[f"{o}/{r}".lower()] = {
                            "repo_info": {
                                "full_name": f"{o}/{r}",
                                "html_url": f"https://github.com/{o}/{r}",
                                "stars": 0, "forks": 0, "language": "Unknown",
                                "description": "", "readme_snippet": "",
                                "updated_at": "", "license": "N/A",
                                "error": str(e),
                            },
                            "analysis": {
                                "is_coding_tool": True,
                                "category": "기타 개발 도구",
                                "summary_ko": f"GitHub 저장소: {o}/{r} (분석 실패, 기본 표시)",
                                "key_features": [],
                                "target_audience": "Developers",
                            },
                        }

        results = [results_by_key[f"{o}/{r}".lower()] for o, r in targets]

        # Mark video as analyzed (if not force mode)
        if not self.force:
            analyzed_repos = [f"{o}/{r}" for o, r in targets]
            _mark_video_analyzed(video_id, video_metadata.get("title", ""), analyzed_repos)

        # Step 4: Generate report
        report_path = self.doc_generator.generate_markdown_report(
            video_metadata, results
        )

        log.info("Report generated: %s", report_path)
        log.info("=" * 50)

        return {
            "video_id": video_id,
            "repos_found": len(repos),
            "new_repos": len(targets),
            "already_registered": len(repos) - len(targets),
            "tools_analyzed": len(results),
            "report_path": report_path
        }

    def process_channels(self, channels: list[dict] | None = None) -> dict:
        """Process multiple YouTube channels based on configured channels."""
        import concurrent.futures
        from config.settings import YOUTUBE_CHANNEL_HANDLES

        channels = channels or [{"name": handle, "handle": handle} for handle in YOUTUBE_CHANNEL_HANDLES]
        channels_data: list[dict] = []
        all_tools: list[dict] = []

        for channel in channels:
            log.info("[%s] 최근 영상 %d개 조회 중...", channel['name'], self.videos_per_channel)
            try:
                video_ids = self._list_channel_videos(channel["handle"])
            except Exception as exc:
                log.error("[%s] 조회 실패: %s", channel['name'], exc)
                channels_data.append({**channel, "videos": []})
                continue
            log.info("[%s] %d개 발견, 분석 중...", channel['name'], len(video_ids))

            channel_tools: list[dict] = []
            for j, video_id in enumerate(video_ids, 1):
                url = f"https://www.youtube.com/watch?v={video_id}"
                log.info("  (%d/%d) %s 분석 중...", j, len(video_ids), video_id)
                try:
                    combined_text, video_metadata = self.collector.get_combined_text(video_id)
                    log.info("  (%d/%d) 텍스트 길이: %d", j, len(video_ids), len(combined_text))

                    if not combined_text:
                        log.warning("  (%d/%d) 자막+설명 비어있음 → 건너뜀", j, len(video_ids))
                        continue

                    # Skip if already analyzed video
                    if video_id in self._done_video_ids and not self.force:
                        log.info("  (%d/%d) 이미 분석 완료된 영상 → 건너뜀", j, len(video_ids))
                        continue

                    repos = self.extractor.extract_github_repos(combined_text)
                    
                    # Filter out already registered repos
                    new_repos = [(o, r) for o, r in repos 
                                 if f"{o}/{r}".lower() not in self._registered_repos]
                    log.info("  (%d/%d) %d개 새 리포지토리 발견", j, len(video_ids), len(new_repos))

                    targets = new_repos[:10]  # 영상당 최대 10개
                    if not targets:
                        log.info("  (%d/%d) 새 리포지토리 없음 → 스킵", j, len(video_ids))
                        # Mark this video as analyzed even if no new repos
                        if not self.force:
                            _mark_video_analyzed(video_id, video_metadata.get("title", ""), [])
                        continue

                    results_by_key: dict[str, dict] = {}
                    show_progress = PERFORMANCE.get("progress_bar", True)
                    max_workers = PERFORMANCE.get("max_workers", 8)

                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                        future_to_repo = {
                            ex.submit(self._analyze_single_repo, o, r, combined_text): (o, r)
                            for o, r in targets
                        }
                        if show_progress:
                            with tqdm(total=len(targets), desc=f"  Analyzing repos (video {j})", unit="repo") as pbar:
                                for fut in concurrent.futures.as_completed(future_to_repo):
                                    o, r = future_to_repo[fut]
                                    try:
                                        results_by_key[f"{o}/{r}".lower()] = fut.result(timeout=120)
                                        pbar.set_postfix_str(f"{o}/{r}")
                                    except Exception as e:
                                        log.error("  [%s/%s] WORKER ERROR: %s", o, r, e)
                                        results_by_key[f"{o}/{r}".lower()] = {
                                            "repo_info": {
                                                "full_name": f"{o}/{r}",
                                                "html_url": f"https://github.com/{o}/{r}",
                                                "stars": 0, "forks": 0, "language": "Unknown",
                                                "description": "", "readme_snippet": "",
                                                "updated_at": "", "license": "N/A",
                                                "error": str(e),
                                            },
                                            "analysis": {
                                                "is_coding_tool": True,
                                                "category": "기타 개발 도구",
                                                "summary_ko": f"GitHub 저장소: {o}/{r} (분석 실패, 기본 표시)",
                                                "key_features": [],
                                                "target_audience": "Developers",
                                            },
                                        }
                                    pbar.update(1)
                        else:
                            for fut in concurrent.futures.as_completed(future_to_repo):
                                o, r = future_to_repo[fut]
                                try:
                                    results_by_key[f"{o}/{r}".lower()] = fut.result(timeout=120)
                                except Exception as e:
                                    log.error("  [%s/%s] WORKER ERROR: %s", o, r, e)
                                    results_by_key[f"{o}/{r}".lower()] = {
                                        "repo_info": {
                                            "full_name": f"{o}/{r}",
                                            "html_url": f"https://github.com/{o}/{r}",
                                            "stars": 0, "forks": 0, "language": "Unknown",
                                            "description": "", "readme_snippet": "",
                                            "updated_at": "", "license": "N/A",
                                            "error": str(e),
                                        },
                                        "analysis": {
                                            "is_coding_tool": True,
                                            "category": "기타 개발 도구",
                                            "summary_ko": f"GitHub 저장소: {o}/{r} (분석 실패, 기본 표시)",
                                            "key_features": [],
                                            "target_audience": "Developers",
                                        },
                                    }

                    results = [results_by_key[f"{o}/{r}".lower()] for o, r in targets]
                    channel_tools.extend(results)
                    
                    # Mark video as analyzed
                    if not self.force:
                        _mark_video_analyzed(video_id, video_metadata.get("title", ""), 
                                               [f"{o}/{r}" for o, r in targets])

                except Exception as exc:
                    log.error("  (%d/%d) 분석 실패: %s", j, len(video_ids), exc)
                    continue

            channels_data.append({**channel, "videos": channel_tools})
            all_tools.extend(channel_tools)

        # Generate comprehensive report
        log.info("총 %d개 리포지토리 분석 완료, 리포트 생성 중...", len(all_tools))
        report_path = self.doc_generator.generate_markdown_report(
            {"title": "Channel Analysis", "url": "Multiple Videos"}, all_tools
        )

        return {
            "channels": len(channels_data),
            "total_repos_analyzed": len(all_tools),
            "report_path": report_path,
            "channels_data": channels_data
        }


def main():
    """Main entry point."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Awesome AI Tool Extractor")
    parser.add_argument("input", nargs="?", help="video_id_or_url or --text or --channels")
    parser.add_argument("--text", help="process from text input")
    parser.add_argument("--channels", action="store_true", help="process configured YouTube channels")
    parser.add_argument("--videos", type=int, default=5, help="videos per channel (default: 5)")
    parser.add_argument("--force", action="store_true", help="force reanalysis of already processed items")
    args = parser.parse_args()

    pipeline = Pipeline(videos_per_channel=args.videos, force=args.force)

    if args.channels:
        result = pipeline.process_channels()
    elif args.text:
        result = pipeline.process_from_text(args.text, {
            "title": "Manual Input",
            "url": "N/A"
        })
    elif args.input:
        video_id = args.input
        result = pipeline.process_video(video_id)
    else:
        log.error("Usage: python pipeline.py <video_id_or_url>")
        log.error("   or: python pipeline.py --text 'transcript text here'")
        log.error("   or: python pipeline.py --channels")
        log.error("   or: python pipeline.py --force <video_id>")
        log.error(" input: 11자리 video_id 또는 watch/youtu.be/shorts/embed/live URL")
        sys.exit(1)

    log.info("=== Result ===")
    log.info("%s", json.dumps(result, indent=2, ensure_ascii=False))
    try:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except UnicodeEncodeError:
        print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()