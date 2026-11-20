"""LLMClassifier 실경로 1회 검증 (fake repo 1건)."""
from modules import LLMClassifier

clf = LLMClassifier()
print(f"clients: {len(clf.clients)}")

result = clf.analyze_repository(
    {
        "full_name": "Hmbown/CodeWhale",
        "description": "Open-source terminal coding agent",
        "language": "Rust",
        "stars": 40952,
        "readme_snippet": "",
    },
    "terminal coding agent",
)
print("is_coding_tool:", result.get("is_coding_tool"))
print("category:", result.get("category"))
print("summary_ko:", (result.get("summary_ko") or "")[:150])
print("features:", len(result.get("key_features", [])))
