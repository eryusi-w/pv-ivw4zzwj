import base64
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

log = logging.getLogger(__name__)

# 조회 결과를 디스크에 보관해 다음 실행에서 API를 다시 호출하지 않는다.
# 비인증 GitHub 한도는 시간당 60회이므로 실행 간 재사용이 필수다.
_META_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "repo_meta_cache.json",
)
META_CACHE_TTL = timedelta(hours=24)


class GitHubEnricher:
    """Enriches repository data with GitHub API information."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub enricher with token."""
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            # secret/api key.txt 폴백 (환경변수 없을 때)
            try:
                import sys
                _HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                _ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_HOME))))
                if _ROOT not in sys.path:
                    sys.path.insert(0, _ROOT)
                from shared.ai_providers import get_github_tokens
                toks = get_github_tokens()
                if toks:
                    self.token = toks[0]
            except Exception:
                pass
        self.headers = {"Accept": "application/vnd.github.mercy-preview+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self._cache = {}  # Simple in-memory cache
        self._disk_cache = self._load_disk_cache()
        self._dirty = False

    @staticmethod
    def _load_disk_cache() -> dict:
        """output/repo_meta_cache.json 로드 (없거나 깨졌으면 빈 사전)."""
        try:
            with open(_META_CACHE_FILE, encoding="utf-8") as f:
                payload = json.load(f)
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _cached_info(self, cache_key: str) -> Optional[dict]:
        """TTL 이내에 저장된 조회 결과만 재사용한다."""
        entry = self._disk_cache.get(cache_key)
        if not isinstance(entry, dict):
            return None
        try:
            fetched_at = datetime.fromisoformat(entry.get("fetched_at", ""))
        except ValueError:
            return None
        if datetime.now(timezone.utc) - fetched_at > META_CACHE_TTL:
            return None
        info = entry.get("info")
        return info if isinstance(info, dict) else None

    def save_cache(self) -> None:
        """디스크 캐시를 파일로 저장한다 (변경이 있을 때만)."""
        if not self._dirty:
            return
        try:
            os.makedirs(os.path.dirname(_META_CACHE_FILE), exist_ok=True)
            with open(_META_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._disk_cache, f, ensure_ascii=False, indent=0)
            self._dirty = False
        except OSError as e:
            log.warning("메타데이터 캐시 저장 실패: %s", e)

    def _get(self, url: str, timeout: int = 10):
        import requests
        try:
            r = requests.get(url, headers=self.headers, timeout=timeout)
            if r.status_code == 401 and "Authorization" in self.headers:
                # Public repositories remain readable when a configured token is stale.
                self.headers.pop("Authorization", None)
                r = requests.get(url, headers=self.headers, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def _readme_snippet(self, owner: str, repo_name: str, limit: int = 2000) -> str:
        """README 앞부분 텍스트 (설치법/기능 파악용). 실패 시 ''."""
        data = self._get(f"https://api.github.com/repos/{owner}/{repo_name}/readme")
        if not data or not data.get("content"):
            return ""
        try:
            raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return ""
        # 마크다운 기호 정리 후 앞부분만
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        # 배지/빈 헤더 스킵
        cleaned = [ln for ln in lines if not ln.startswith("![")][:60]
        return " ".join(cleaned)[:limit]
    
    def get_repo_info(self, owner: str, repo_name: str) -> dict:
        """
        Fetch repository metadata from GitHub (cached).

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            Repository information dictionary
        """
        cache_key = f"{owner}/{repo_name}".lower()
        if cache_key in self._cache:
            log.debug("Cache hit for %s", cache_key)
            return self._cache[cache_key]

        cached = self._cached_info(cache_key)
        if cached is not None:
            log.debug("Disk cache hit for %s", cache_key)
            self._cache[cache_key] = cached
            return cached

        try:
            url = f"https://api.github.com/repos/{owner}/{repo_name}"
            response = self._get(url)
            if response:
                repo = response
                # latest_release는 카탈로그 표시에 쓰이지 않아 호출하지 않는다 (repo당 1콜 절약).
                result = {
                    "full_name": repo.get("full_name", f"{owner}/{repo_name}"),
                    "html_url": repo.get("html_url", f"https://github.com/{owner}/{repo_name}"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "open_issues": repo.get("open_issues_count", 0),
                    "language": repo.get("language", "Unknown"),
                    "description": repo.get("description", "") or "",
                    "topics": repo.get("topics", []),
                    "homepage": repo.get("homepage", "") or "",
                    "default_branch": repo.get("default_branch", "") or "",
                    "pushed_at": repo.get("pushed_at", "") or "",
                    "updated_at": repo.get("updated_at", ""),
                    "latest_release": "",
                    "readme_snippet": self._readme_snippet(owner, repo_name),
                    "license": repo.get("license", {}).get("spdx_id", "N/A") if repo.get("license") else "N/A"
                }
                self._cache[cache_key] = result
                self._disk_cache[cache_key] = {
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "info": result,
                }
                self._dirty = True
                return result
            else:
                result = self._empty_repo_info(owner, repo_name)
                self._cache[cache_key] = result
                return result

        except Exception as e:
            result = self._empty_repo_info(owner, repo_name, str(e))
            self._cache[cache_key] = result
            return result
    
    def _empty_repo_info(self, owner: str, repo_name: str, error: str = "") -> dict:
        """Return empty repo info structure."""
        return {
            "full_name": f"{owner}/{repo_name}",
            "html_url": f"https://github.com/{owner}/{repo_name}",
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
            "language": "Unknown",
            "description": "",
            "topics": [],
            "homepage": "",
            "default_branch": "",
            "pushed_at": "",
            "readme_snippet": "",
            "updated_at": "",
            "latest_release": "",
            "license": "N/A",
            "error": error
        }
