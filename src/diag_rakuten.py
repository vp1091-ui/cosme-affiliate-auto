"""楽天0件診断: .env読み込み・API生応答・フィルター通過数を表示。ID自体は表示しない。"""
import os, pathlib, json
import requests
try:
    from load_env import load_env
    load_env()
except Exception as e:
    print("load_env失敗:", e)

BASE = pathlib.Path(__file__).resolve().parents[1]
APP_ID = os.getenv("RAKUTEN_APP_ID", "")
AFF_ID = os.getenv("RAKUTEN_AFFILIATE_ID", "")
print(f"APP_ID: {'設定あり(' + str(len(APP_ID)) + '桁)' if APP_ID else '未設定'}")
print(f"AFF_ID: {'設定あり(' + str(len(AFF_ID)) + '桁)' if AFF_ID else '未設定(収益なし・取得は可)'}")
print(f".env存在: {(BASE/'.env').exists()}")

if not APP_ID:
    print("-> .env の RAKUTEN_APP_ID が空。STEP4に戻る"); raise SystemExit

# 最小条件で1件テスト (フィルターなし・ジャンルなし)
url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
for label, params in [
    ("最小(化粧水/hits=1)", {"format": "json", "applicationId": APP_ID, "keyword": "化粧水", "hits": 1}),
    ("本番条件", {"format": "json", "applicationId": APP_ID, "keyword": "化粧水 敏感肌", "hits": 5, "genreId": "100939", "sort": "+reviewCount"}),
]:
    try:
        r = requests.get(url, params=params, timeout=20)
        print(f"\n[{label}] HTTP {r.status_code}")
        j = r.json()
        if "error" in j:
            print("API error応答:", json.dumps(j, ensure_ascii=False)[:500])
        else:
            print("count:", j.get("count"), "/ Items:", len(j.get("Items", [])))
            if j.get("Items"):
                d = j["Items"][0]["Item"]
                print("先頭例:", d.get("itemName", "")[:60], "| review:", d.get("reviewCount"), d.get("reviewAverage"))
    except Exception as e:
        print(f"[{label}] 例外: {e}")
