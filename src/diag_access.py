"""Access key付与形の特定: どの渡し方で200になるか総当たり。キー値は表示しない。"""
import os
import requests
from load_env import load_env
load_env()
APP_ID = os.getenv("RAKUTEN_APP_ID", "")
AFF_ID = os.getenv("RAKUTEN_AFFILIATE_ID", "")
KEY = os.getenv("RAKUTEN_ACCESS_KEY", "")
print(f"APP_ID: {'あり' if APP_ID else 'なし'} / AFF_ID: {'あり' if AFF_ID else 'なし'} / ACCESS_KEY: {'あり(' + str(len(KEY)) + '桁)' if KEY else 'なし -> .envに設定してから再実行'}")
if not KEY:
    raise SystemExit
URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
BASE = {"format": "json", "applicationId": APP_ID, "keyword": "化粧水", "hits": 1}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"}

def mask(t: str) -> str:
    for s in (APP_ID, AFF_ID, KEY):
        if s and len(s) > 4:
            t = t.replace(s, "***")
    return t

variants = {
    "1_accessKey_param": (dict(BASE, accessKey=KEY), None),
    "2_access_key_param": (dict(BASE, access_key=KEY), None),
    "3_key_param": (dict(BASE, key=KEY), None),
    "4_Authorization_header": (dict(BASE), {"Authorization": f"Bearer {KEY}", **UA}),
    "5_x-api-key_header": (dict(BASE), {"x-api-key": KEY, **UA}),
    "6_accessKey+aff": (dict(BASE, accessKey=KEY, affiliateId=AFF_ID), None),
}
for name, (params, headers) in variants.items():
    try:
        r = requests.get(URL, params=params, headers=headers, timeout=20)
        print(f"[{name}] HTTP {r.status_code} {mask(r.text[:150])}")
    except Exception as e:
        print(f"[{name}] 例外 {mask(str(e))[:150]}")
