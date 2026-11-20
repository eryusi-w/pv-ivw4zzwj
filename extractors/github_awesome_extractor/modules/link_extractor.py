import logging
import re
from typing import Optional

log = logging.getLogger(__name__)


class LinkExtractor:
    """Extracts and normalizes GitHub URLs from text."""
    
    # GitHub URL patterns
    GITHUB_URL_PATTERNS = [
        r'https?://github\.com/([\w\.-]+)/([\w\.-]+)',
        r'github\.com/([\w\.-]+)/([\w\.-]+)',
        r'github\.com/([\w\.-]+)/([\w\.-]+)/',
    ]
    
    # Short URL patterns
    SHORT_URL_PATTERNS = {
        'bit.ly': r'bit\.ly/[\w]+',
        'tinyurl': r'tinyurl\.com/[\w]+',
        'goo.gl': r'goo\.gl/[\w]+',
    }
    
    def extract_github_repos(self, text: str) -> list[tuple[str, str]]:
        """
        Extract GitHub repository references from text.
        
        Args:
            text: Input text to search
            
        Returns:
            List of (owner, repo) tuples (deduplicated)
        """
        matches = []
        
        for pattern in self.GITHUB_URL_PATTERNS:
            found = re.findall(pattern, text)
            matches.extend(found)
        
        # Deduplicate while preserving order
        # CodeWhale 같은 누락 방지: .git 접미사, 문장 끝 마침표/쉼표, 대소문자 정리
        seen = set()
        unique_matches = []
        for owner, repo in matches:
            # Clean up repo name (query params, fragments, trailing punct)
            repo = repo.split('?')[0].split('#')[0].split('/')[0]
            repo = repo.rstrip('./-_,;)]\'"')
            owner = owner.strip().rstrip('./-_,;)]\'"')
            if repo.lower().endswith('.git'):
                repo = repo[:-4]
            if not owner or not repo:
                continue
            key = f"{owner}/{repo}".lower()

            if key not in seen:
                seen.add(key)
                unique_matches.append((owner, repo))

        return unique_matches
    
    def normalize_url(self, url: str) -> Optional[str]:
        """Normalize and expand shortened URLs."""
        import requests

        for service, pattern in self.SHORT_URL_PATTERNS.items():
            if re.search(pattern, url):
                try:
                    response = requests.head(url, allow_redirects=True, timeout=10)
                    return response.url
                except Exception as e:
                    log.warning("Failed to normalize URL %s: %s", url, e)
                    return None

        if re.match(self.GITHUB_URL_PATTERNS[0], url):
            return url

        return None
    
    def extract_all_links(self, text: str) -> list[str]:
        """Extract all URLs from text."""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)