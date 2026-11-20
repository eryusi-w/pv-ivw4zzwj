"""Offline regression tests for the cumulative AI project catalog."""
from __future__ import annotations

import importlib
import sys
import types
from datetime import date
from pathlib import Path

import pytest


def _install_optional_dependency_stubs() -> None:
    """Keep unit tests independent from optional LLM SDKs and credentials."""
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    sys.modules.setdefault("dotenv", dotenv)

    openai = types.ModuleType("openai")
    openai.OpenAI = type("OpenAI", (), {})
    sys.modules.setdefault("openai", openai)


def _load_app_modules():
    _install_optional_dependency_stubs()
    repo_parent = str(Path(__file__).resolve().parents[2])
    if repo_parent not in sys.path:
        sys.path.insert(0, repo_parent)
    collector = importlib.import_module("github_awesome_extractor.sources.manuagi_collector")
    digest = importlib.import_module("github_awesome_extractor.sources.manuagi_to_digest")
    return collector, digest


collector, digest = _load_app_modules()


def test_requested_date_range_is_inclusive_kst():
    start, end, from_text, to_text = collector._target_bounds(
        date(2026, 8, 1), date(2026, 8, 31)
    )

    assert (from_text, to_text) == ("2026-08-01", "2026-08-31")
    assert start.isoformat() == "2026-08-01T00:00:00+09:00"
    assert end.isoformat() == "2026-09-01T00:00:00+09:00"


def test_date_range_requires_both_dates_and_valid_order():
    with pytest.raises(ValueError, match="함께 지정"):
        collector._target_bounds(date(2026, 8, 1), None)
    with pytest.raises(ValueError, match="늦을 수 없습니다"):
        collector._target_bounds(date(2026, 8, 2), date(2026, 8, 1))


def test_trending_parser_keeps_only_repository_paths():
    parser = collector._TrendingRepoParser()
    parser.feed(
        '<a href="/trending/developers">developers</a>'
        '<article><a href="/owner/project">project</a>'
        '<a href="/owner/project/stargazers">stars</a>'
        '<a href="/topics/ai">topic</a></article>'
        '<article><a href="/another/tool">tool</a></article>'
        '<article><a href="/sample/health-ai">sample / health-ai</a>'
        '<p>Clinical assistant for patient records</p>'
        '<span itemprop="programmingLanguage">Python</span></article>'
    )

    assert parser.repositories == [
        ("owner", "project"), ("another", "tool"), ("sample", "health-ai")
    ]
    assert parser.repository_details["sample/health-ai"] == {
        "description": "Clinical assistant for patient records",
        "language": "Python",
    }


def test_github_discoveries_deduplicate_popular_and_trending(monkeypatch):
    search_queries = []

    class Response:
        def __init__(self, body, status_code=200):
            self.body = body
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return self.body

    class FakeHTMLResponse(Response):
        text = (
            '<article><a href="/owner/project">project</a></article>'
            '<article><a href="/new/tool">tool</a></article>'
        )

    def fake_get(url, **kwargs):
        if url == collector.GITHUB_SEARCH_URL:
            search_queries.append(kwargs["params"]["q"])
            return Response({"items": [{"full_name": "Owner/Project"}]})
        return FakeHTMLResponse({})

    monkeypatch.setattr(collector.requests, "get", fake_get)
    candidates, counts = collector._github_discoveries(60, 5)
    deduped = {}
    for item in candidates:
        key = f"{item['owner']}/{item['repo']}".casefold()
        deduped.setdefault(key, set()).update(item["discovery_sources"])

    assert counts == {"popular": 1, "daily_trending": 2, "weekly_trending": 2}
    assert deduped == {
        "owner/project": {"popular", "daily_trending", "weekly_trending"},
        "new/tool": {"daily_trending", "weekly_trending"},
    }
    assert len(search_queries) == len(collector.POPULAR_SEARCH_QUERIES)
    assert len(candidates[0]["discovery_queries"]) == len(collector.POPULAR_SEARCH_QUERIES)
    assert all("fork:false" in query and "archived:false" in query for query in search_queries)


def test_popular_search_retries_without_rejected_token(monkeypatch):
    calls = []

    class Response:
        status_code = 401

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return {"items": [{"full_name": "owner/public-ai"}]}

    def fake_get(url, **kwargs):
        calls.append(kwargs)
        response = Response()
        if "Authorization" not in kwargs["headers"]:
            response.status_code = 200
        return response

    monkeypatch.setenv("GITHUB_TOKEN", "test-token-value")
    monkeypatch.setattr(collector.requests, "get", fake_get)
    candidates, counts = collector._github_discoveries(1, 0)

    assert len(calls) == 2
    assert "Authorization" in calls[0]["headers"]
    assert "Authorization" not in calls[1]["headers"]
    assert candidates[0]["owner"] == "owner"
    assert counts["popular"] == 1


def test_repo_enricher_retries_public_request_after_auth_failure(monkeypatch):
    enricher_module = importlib.import_module(
        "github_awesome_extractor.modules.github_enricher"
    )
    enricher = enricher_module.GitHubEnricher(token="test-token-value")
    calls = []

    class Response:
        def __init__(self, status_code):
            self.status_code = status_code

        def json(self):
            return {"full_name": "owner/project"}

    def fake_get(url, **kwargs):
        calls.append(kwargs["headers"].copy())
        return Response(401 if len(calls) == 1 else 200)

    monkeypatch.setattr("requests.get", fake_get)
    assert enricher._get("https://api.github.com/repos/owner/project") == {
        "full_name": "owner/project"
    }
    assert "Authorization" in calls[0]
    assert "Authorization" not in calls[1]


def test_collection_merges_sources_and_records_requested_period(monkeypatch):
    monkeypatch.setattr(collector, "YoutubeAnalyzer", lambda: object())
    monkeypatch.setattr(collector, "LinkExtractor", lambda: object())
    monkeypatch.setattr(collector, "analyzed_ids", lambda: set())
    monkeypatch.setattr(collector, "allow_reanalyze", lambda: False)
    monkeypatch.setattr(collector, "_videos_in_date_range", lambda *args: [])
    monkeypatch.setattr(
        collector,
        "_github_discoveries",
        lambda *args: (
            [
                {"owner": "owner", "repo": "project", "discovery_sources": ["popular"]},
                {"owner": "OWNER", "repo": "Project", "discovery_sources": ["weekly_trending"]},
            ],
            {"popular": 1, "weekly_trending": 1},
        ),
    )

    result = collector.collect_manuagi_github_links(
        date(2026, 8, 1), date(2026, 8, 31), popular_limit=2, trending_limit=2
    )

    assert result["target_from_date"] == "2026-08-01"
    assert result["target_to_date"] == "2026-08-31"
    assert result["repos_found"] == 1
    assert result["repos"][0]["discovery_sources"] == ["popular", "weekly_trending"]


def test_collection_rejects_search_limit_over_github_api_maximum():
    with pytest.raises(ValueError, match="0~100"):
        collector.collect_manuagi_github_links(popular_limit=101)


def test_archive_preserves_registration_date_and_catalog_hides_discovery_signals():
    previous = {
        "full_name": "owner/health-ai",
        "registered_at": "2026-08-01",
        "stars": 9999,
        "source_url": "https://youtube.example/video",
        "analysis": {
            "is_ai_tool": True,
            "domain": "의료·바이오",
            "summary_ko": "의료 영상 분석 모델을 운영하는 도구입니다.",
            "usecase_ko": "의료 영상 검토용",
            "key_features": ["영상 분류", "모델 배포"],
        },
    }
    current = {**previous, "registered_at": "2026-10-27", "stars": 12000}
    merged = digest.merge_repo_archive([previous], [current], "2026-10-27")
    markdown = digest.build_md(merged, 0, "2026-10-27")

    assert len(merged) == 1
    assert merged[0]["registered_at"] == "2026-08-01"
    assert "의료·바이오" in markdown
    assert "의료 영상 검토용" in markdown
    assert "영상 분류" in markdown
    assert "2026-08-01" in markdown
    assert "9999" not in markdown and "12000" not in markdown
    assert "youtube.example" not in markdown
    assert "왜 뜨나" not in markdown


def test_enrich_uses_github_candidate_metadata_without_api_calls(monkeypatch):
    class FailingEnricher:
        def __init__(self):
            pass

        def get_repo_info(self, *_args):
            raise AssertionError("prefetched metadata should avoid another API request")

        def save_cache(self):
            pass

    monkeypatch.setattr(digest, "GitHubEnricher", FailingEnricher)
    monkeypatch.setattr(digest.time, "sleep", lambda *_args: None)
    enriched = digest.enrich(
        {
            "repos": [
                {
                    "owner": "sample",
                    "repo": "health-ai",
                    "discovery_sources": ["user_requested"],
                    "discovery_queries": ["sample-list"],
                    "repository_info": {
                        "full_name": "sample/health-ai",
                        "html_url": "https://github.com/sample/health-ai",
                        "stars": 0,
                        "description": "AI clinical assistant for patient records",
                        "topics": [],
                        "language": "Python",
                    },
                }
            ]
        },
        use_llm=False,
    )
    assert enriched[0]["description"] == "AI clinical assistant for patient records"
    assert enriched[0]["discovery_sources"] == ["user_requested"]
    assert enriched[0]["discovery_queries"] == ["sample-list"]


def test_enrich_skips_registered_repo_with_description(monkeypatch):
    class FailingEnricher:
        def __init__(self):
            pass

        def get_repo_info(self, *_args):
            raise AssertionError("등록된 도구는 다시 조회하지 않아야 한다")

        def save_cache(self):
            pass

    monkeypatch.setattr(digest, "GitHubEnricher", FailingEnricher)
    monkeypatch.setattr(digest.time, "sleep", lambda *_args: None)
    known = {
        "sample/known-tool": {
            "full_name": "sample/known-tool",
            "description": "AI agent memory tool",
            "stars": 42,
            "analysis": {"is_ai_tool": True, "summary_ko": "등록 시점 요약"},
        }
    }
    enriched = digest.enrich(
        {"repos": [{"owner": "sample", "repo": "known-tool",
                    "discovery_sources": ["weekly_trending"]}]},
        use_llm=False,
        known=known,
    )
    assert enriched[0]["stars"] == 42
    assert enriched[0]["analysis"]["summary_ko"] == "등록 시점 요약"
    assert enriched[0]["discovery_sources"] == ["weekly_trending"]


def test_enrich_refreshes_registered_repo_without_description(monkeypatch):
    calls = []

    class RecordingEnricher:
        def __init__(self):
            pass

        def get_repo_info(self, owner, repo_name):
            calls.append(f"{owner}/{repo_name}")
            return {
                "full_name": "sample/blank-tool",
                "html_url": "https://github.com/sample/blank-tool",
                "stars": 7,
                "description": "AI coding agent",
                "topics": [],
                "language": "Python",
                "readme_snippet": "",
            }

        def save_cache(self):
            pass

    monkeypatch.setattr(digest, "GitHubEnricher", RecordingEnricher)
    monkeypatch.setattr(digest.time, "sleep", lambda *_args: None)
    known = {
        "sample/blank-tool": {
            "full_name": "sample/blank-tool",
            "description": "",
            "stars": 0,
            "analysis": {"is_ai_tool": True, "_fallback": True},
        }
    }
    enriched = digest.enrich(
        {"repos": [{"owner": "sample", "repo": "blank-tool"}]},
        use_llm=False,
        known=known,
    )
    assert calls == ["sample/blank-tool"]
    assert enriched[0]["description"] == "AI coding agent"
    assert enriched[0]["stars"] == 7


def test_ai_domain_classifier_includes_non_development_fields():
    classifier = importlib.import_module("github_awesome_extractor.modules.llm_classifier")
    health_tool = {
        "full_name": "sample/clinic-assistant",
        "description": "An AI assistant for clinical patient records",
    }
    general_tool = {
        "full_name": "sample/todo-list",
        "description": "A simple offline task list application",
    }
    agent_tool = {
        "full_name": "openclaw/openclaw",
        "description": "Personal AI assistant that handles everyday tasks",
        "readme_snippet": "Machine learning research for future agents",
    }
    workflow_tool = {
        "full_name": "sample/workflow",
        "description": "Workflow automation platform with native AI capabilities",
    }
    coding_agent_tool = {
        "full_name": "cloudflare/security-audit-skill",
        "description": "A coding-agent skill for multi-phase security audits",
    }
    token_optimizer_tool = {
        "full_name": "alexgreensh/token-optimizer",
        "description": "Find ghost tokens, survive compaction, and avoid context quality decay",
    }
    mcp_coding_tool = {
        "full_name": "oraios/serena",
        "description": "A powerful MCP toolkit for coding with semantic retrieval and editing",
    }

    assert classifier.infer_ai_related(health_tool)
    assert classifier.infer_domain(health_tool) == "의료·바이오"
    assert not classifier.infer_ai_related(general_tool)
    assert classifier.infer_domain(agent_tool) == "기타 AI 도구"
    assert classifier.infer_domain(workflow_tool) == "업무·비즈니스"
    assert classifier.infer_ai_related(coding_agent_tool)
    assert classifier.infer_ai_related(token_optimizer_tool)
    assert classifier.infer_ai_related(mcp_coding_tool)


def test_fallback_catalog_uses_repository_description_as_purpose():
    row = {
        "full_name": "n8n-io/n8n",
        "description": "Workflow automation platform with native AI capabilities",
        "topics": [],
        "registered_at": "2026-10-27",
        "analysis": {
            "_fallback": True,
            "is_ai_tool": True,
            "domain": "교육·연구",
            "summary_ko": "설명: Workflow automation platform with native AI capabilities",
            "usecase_ko": "개발 도구 활용",
            "key_features": [],
        },
    }

    markdown = digest.build_md([row], 0, "2026-10-27")

    assert "업무·비즈니스" in markdown
    assert "용도:</b> 시각적 흐름과 코드를 결합해 앱·AI 작업을 자동화하는 워크플로 플랫폼" in markdown
    assert "개발 도구 활용" not in markdown
    assert "교육·연구" not in markdown


def test_machine_learning_study_plan_has_korean_description():
    row = {
        "full_name": "ZuzooVn/machine-learning-for-software-engineers",
        "html_url": "https://github.com/ZuzooVn/machine-learning-for-software-engineers",
        "description": "A complete daily plan for studying to become a machine learning engineer",
        "analysis": {
            "_fallback": True,
            "is_ai_tool": True,
            "domain": "개발 도구",
            "summary_ko": "A complete daily plan for studying to become a machine learning engineer",
            "usecase_ko": "A complete daily plan for studying to become a machine learning engineer",
            "key_features": [],
        },
    }

    korean = "머신러닝 엔지니어가 되기 위한 학습 계획과 단계별 실천 로드맵"
    html = digest.build_html([row], "2026-10-27")
    markdown = digest.build_md([row], 0, "2026-10-27")

    assert digest._description_ko(row) == korean
    assert "머신러닝 엔지니어가 되기 위한 학습 계획을 따라 공부할 때" in html
    assert "머신러닝 엔지니어가 되기 위한 학습 계획을 따라 공부할 때" in markdown
    assert "A complete daily plan for studying" not in html


def test_html_catalog_matches_mockup_card_layout_and_filters_private_signals():
    row = {
        "full_name": "n8n-io/n8n",
        "html_url": "https://github.com/sample/workflow",
        "description": "Workflow automation platform with native AI capabilities",
        "topics": ["ai", "workflow"],
        "registered_at": "2026-10-27",
        "stars": 12345,
        "source_url": "https://youtube.example/video",
        "analysis": {
            "_fallback": True,
            "is_ai_tool": True,
            "domain": "교육·연구",
            "summary_ko": "설명: Workflow automation platform with native AI capabilities",
            "usecase_ko": "개발 도구 활용",
            "key_features": ["AI 워크플로 자동화", "앱 연동"],
        },
    }

    html = digest.build_html([row], "2026-10-27", "2026-10-24", "2026-10-27")

    assert 'class="sidebar"' in html
    assert 'class="tool" data-kind="business"' in html
    assert 'id="from-date" type="date" value="2026-10-24"' in html
    assert 'id="to-date" type="date" value="2026-10-27"' in html
    assert "YouTube 영상 게시일 · 한국 시간" in html
    assert "GitHub 인기·Trending은 현재 기준으로 수집" in html
    assert "기간 선택" in html and "--from-date" in html
    assert "시각적 흐름과 코드를 결합해 앱·AI 작업을 자동화하는 워크플로 플랫폼" in html
    assert "Workflow automation platform" not in html
    assert "2026-10-27</time>" in html
    assert "12345" not in html
    assert "youtube.example" not in html
    assert "왜 뜨나" not in html
