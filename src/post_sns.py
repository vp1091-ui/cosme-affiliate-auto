"""SNS自動投稿。X API v2 (Freeでも月1500件まで可)。
キー無しでも data/sns_queue に原稿が残るので手動コピペで運用可。"""
import os, pathlib, json
import requests

BASE = pathlib.Path(__file__).resolve().parents[1]
QUEUE = BASE / "data" / "sns_queue"
DONE = BASE / "data" / "sns_done"
DONE.mkdir(exist_ok=True)

BEARER = os.getenv("X_BEARER_TOKEN", "")
API_KEY = os.getenv("X_API_KEY", "")
API_SEC = os.getenv("X_API_SECRET", "")
ACC_TOK = os.getenv("X_ACCESS_TOKEN", "")
ACC_SEC = os.getenv("X_ACCESS_SECRET", "")

def post_with_bearer(text: str):
    # OAuth2 App-onlyでは投稿不可のため、基本はOAuth1.0aが必要。
    # ここでは v2 POST /2/tweets を OAuth1.0a で叩く簡易実装(requests_oauthlib無しでは署名が複雑なため、
    # キーがある場合のみ tweepy無し・httpx署名は外部に委譲)。
    # 現実的低コスト運用: GitHub Actions + X Free plan では bearerだけでは投稿できない -> ログに明示。
    raise RuntimeError("X投稿には OAuth1.0a (API Key/Secret + Access Token/Secret) が必要です")

def post_oauth1(text: str):
    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        raise RuntimeError("requests_oauthlib 未インストール (pip install requests_oauthlib)")
    auth = OAuth1(API_KEY, API_SEC, ACC_TOK, ACC_SEC)
    r = requests.post("https://api.twitter.com/2/tweets", auth=auth, json={"text": text}, timeout=20)
    r.raise_for_status()
    return r.json()

def main():
    files = sorted(QUEUE.glob("*.txt"))
    if not files:
        print("[sns] 投稿キュー無し"); return
    print(f"[sns] {len(files)}件のキュー")
    if not (API_KEY and API_SEC and ACC_TOK and ACC_SEC):
        print("[sns] Xキー未設定 -> 自動投稿スキップ。data/sns_queue を手動コピペで投稿してください (ROOM/Pinterest転用可)")
        return
    for f in files[:5]:
        text = f.read_text(encoding="utf-8")
        try:
            res = post_oauth1(text)
            print(f"[sns] 投稿OK {f.name}: {res.get('data',{}).get('id')}")
            f.rename(DONE / f.name)
        except Exception as e:
            print(f"[sns] 投稿失敗 {f.name}: {e}")

if __name__ == "__main__":
    main()
