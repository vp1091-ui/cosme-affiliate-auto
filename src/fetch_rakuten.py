"""楽天市場 API: 商品検索 + ランキング取得。アフィリエイトリンク付きで保存。"""
import os, json, time, urllib.parse, pathlib
import requests
import yaml

try:
    from load_env import load_env
    load_env()
except Exception:
    pass

BASE = pathlib.Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

APP_ID = os.getenv("RAKUTEN_APP_ID", "")
AFF_ID = os.getenv("RAKUTEN_AFFILIATE_ID", "")
KEY = os.getenv("RAKUTEN_ACCESS_KEY", "")
# 新APIはReferer+Originが許可サイトと完全一致必須 (スキーム含む。登録が example.com なら http)
REFERER = os.getenv("RAKUTEN_REFERER", "http://example.com").rstrip("/")
SITE_URL = os.getenv("SITE_URL", CFG.get("site", {}).get("url", "https://example.com")).rstrip("/")

SEARCH_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
RANK_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Ranking/20260701"

def _mask(s: str) -> str:
    s = str(s)
    for secret in (APP_ID, AFF_ID, KEY):
        if secret and len(secret) > 6:
            s = s.replace(secret, secret[:4] + "***")
    return s

def rakuten_get(url, params):
    params = {"format": "json", "applicationId": APP_ID, "accessKey": KEY, **params}
    if AFF_ID:
        params["affiliateId"] = AFF_ID
    # 新API必須: Referer+Originを許可サイトと完全一致で送る
    headers = {
        "Referer": REFERER + "/",
        "Origin": REFERER,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0",
    }
    r = requests.get(url, params=params, headers=headers, timeout=20)
    try:
        r.raise_for_status()
    except Exception as e:
        body = (r.text or "")[:300]
        raise RuntimeError(f"{e} | body={_mask(body)}")
    return r.json()

def fetch_keyword(keyword, hits=30):
    if not APP_ID:
        print("[rakuten] RAKUTEN_APP_ID 未設定 -> ダミーでスキップ")
        return []
    try:
        j = rakuten_get(SEARCH_URL, {
            "keyword": keyword,
            "hits": hits,
            "sort": CFG["rakuten"].get("sort", "+reviewCount"),
            "genreId": CFG["rakuten"].get("genre_id", "100939"),
            "imageFlag": 1,
            "reviewFlag": 1,
        })
    except Exception as e:
        print(f"[rakuten] {keyword} 失敗: {_mask(e)}")
        return []
    items = []
    for it in j.get("Items", []):
        d = it["Item"]
        try:
            rc = int(float(d.get("reviewCount", 0) or 0))
            ra = float(d.get("reviewAverage", 0) or 0)
        except Exception:
            rc, ra = 0, 0.0
        if rc < CFG["rakuten"]["min_review_count"]:
            continue
        if ra < CFG["rakuten"]["min_review_average"]:
            continue
        items.append({
            "source": "rakuten",
            "keyword": keyword,
            "name": d.get("itemName", ""),
            "price": int(d.get("itemPrice", 0) or 0),
            "review_count": rc,
            "review_avg": ra,
            "shop": d.get("shopName", ""),
            "url": d.get("affiliateUrl") or d.get("itemUrl", ""),
            "image": (d.get("mediumImageUrls") or [{"imageUrl": ""}])[0]["imageUrl"],
            "caption": d.get("itemCaption", "")[:500],
            "jan": "",
        })
    time.sleep(2)  # 新APIのレート制限配慮
    return items

def fetch_ranking():
    if not APP_ID:
        return []
    try:
        j = rakuten_get(RANK_URL, {"genreId": CFG["rakuten"]["genre_id"]})
    except Exception as e:
        print(f"[rakuten] rankingスキップ(新型host未提供): {_mask(e) if '404' not in str(e) else 'Resource not found'}")
        return []
    out = []
    for i, it in enumerate(j.get("Items", []), 1):
        d = it["Item"]
        out.append({
            "source": "rakuten",
            "keyword": "ランキング",
            "rank": i,
            "name": d.get("itemName", ""),
            "price": int(d.get("itemPrice", 0) or 0),
            "review_count": int(float(d.get("reviewCount", 0) or 0)),
            "review_avg": float(d.get("reviewAverage", 0) or 0),
            "shop": d.get("shopName", ""),
            "url": d.get("affiliateUrl") or d.get("itemUrl", ""),
            "image": (d.get("mediumImageUrls") or [{"imageUrl": ""}])[0]["imageUrl"],
            "caption": d.get("itemCaption", "")[:500],
            "jan": "",
        })
    return out

def main():
    all_items = []
    for kw in CFG["keywords"]:
        print(f"[rakuten] {kw} 取得中...")
        all_items += fetch_keyword(kw, CFG["rakuten"]["hits_per_keyword"])
    print("[rakuten] ランキング取得中...")
    ranking = fetch_ranking()
    (DATA / "rakuten_items.json").write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "rakuten_ranking.json").write_text(json.dumps(ranking, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[rakuten] 保存: {len(all_items)}件 + ranking {len(ranking)}件")

if __name__ == "__main__":
    main()
