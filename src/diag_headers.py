"""ヘッダ条件振り分け: テストフォーム成功 vs 直接400 の差を特定。IDは表示しない。"""
import os, json
import requests
from load_env import load_env
load_env()
APP_ID = os.getenv("RAKUTEN_APP_ID", "")
URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
BASE_P = {"format": "json", "applicationId": APP_ID, "keyword": "化粧水", "hits": 1}

combos = {
    "A_default": {},
    "B_browserUA": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"},
    "C_browserUA+Referer": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                            "Referer": "http://example.com/", "Origin": "http://example.com"},
    "D_browserUA+Referer_https": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                                  "Referer": "https://example.com/", "Origin": "https://example.com"},
}
for name, h in combos.items():
    try:
        r = requests.get(URL, params=BASE_P, headers=h or None, timeout=20)
        body = r.text[:160].replace(APP_ID, "***")
        print(f"[{name}] HTTP {r.status_code} {body}")
    except Exception as e:
        print(f"[{name}] 例外 {str(e)[:160]}")
