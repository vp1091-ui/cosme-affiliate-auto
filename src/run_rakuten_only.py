"""楽天だけモード: Amazonを使わず public/ を作る。初回はこれを使う。"""
import json, pathlib, runpy
from load_env import load_env

BASE = pathlib.Path(__file__).resolve().parents[1]
load_env()

# Amazon残骸があれば楽天だけにするために空にする (楽天だけ開始用)
amz = BASE / "data" / "amazon_items.json"
amz.write_text("[]", encoding="utf-8")

for mod in ["fetch_rakuten", "merge_products", "generate_site", "generate_posts"]:
    print(f"\n===== {mod} (rakuten only) =====")
    runpy.run_module(mod, run_name="__main__")

print("\n[rakuten-only] 完了。public/index.html を開いて確認。")
print("件数が0件なら .env の RAKUTEN_APP_ID / RAKUTEN_AFFILIATE_ID を確認。")
