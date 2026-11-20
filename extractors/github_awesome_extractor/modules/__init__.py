"""github_awesome_extractor 전용 모듈 묶음.

범용 모듈(ai_providers)은 shared/ 에 있으며 여기서 재노출만 한다.
"""
import os as _os
import sys as _sys

# shared (D:\dev\codex-home\shared) import 경로 확보
_CODEX_HOME = _os.path.dirname(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))))
)
if _CODEX_HOME not in _sys.path:
    _sys.path.insert(0, _CODEX_HOME)

from shared.ai_providers import build_clients, get_api_key, get_api_keys
from .data_collector import DataCollector
from .link_extractor import LinkExtractor
from .github_enricher import GitHubEnricher
from .llm_classifier import LLMClassifier
from .document_generator import DocumentGenerator

__all__ = [
    "DataCollector",
    "LinkExtractor",
    "GitHubEnricher",
    "LLMClassifier",
    "DocumentGenerator",
    "build_clients",
    "get_api_key",
    "get_api_keys",
]
