"""ai_providers 검증: 키 값은 절대 출력하지 않고 마스킹만 표시."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from shared import ai_providers as ap

keys = ap.load_secret_keys()
print("== parsed providers ==")
for provider in sorted(keys):
    masked = [ap.mask_key(k) for k in keys[provider]]
    print(f"  {provider}: {len(keys[provider])} keys {masked}")

print("== build_clients ==")
clients = ap.build_clients()
for c in clients:
    print(f"  {c['name']}")
print(f"total clients: {len(clients)}")

print("== github/youtube getters ==")
print(f"  github tokens: {len(ap.get_github_tokens())}")
print(f"  youtube key: {ap.mask_key(ap.get_youtube_key() or '')}")
