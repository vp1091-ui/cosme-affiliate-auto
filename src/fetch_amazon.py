"""Amazon PA-API v5 + フォールバック。
PA-APIキーが無くても動作する: Amazon検索リンク(tag付き)を生成して収益化を止めない。
PA-APIがある場合は価格・画像・ASINを正確に取得する。
"""
import os, json, hashlib, hmac, datetime, pathlib
import requests
import yaml

BASE = pathlib.Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))
DATA = BASE / "data"

ACCESS = os.getenv("AMAZON_ACCESS_KEY", "")
SECRET = os.getenv("AMAZON_SECRET_KEY", "")
TAG = os.getenv("AMAZON_PARTNER_TAG", "")
HOST = os.getenv("AMAZON_HOST", "webservices.amazon.co.jp")
REGION = os.getenv("AMAZON_REGION", "us-east-1")

def amazon_search_url(keyword: str) -> str:
    import urllib.parse
    q = urllib.parse.quote_plus(keyword)
    base = f"https://www.amazon.co.jp/s?k={q}"
    return f"{base}&tag={TAG}" if TAG else base

def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def paapi_search(keyword, item_count=10):
    """PA-API SearchItems (SigV4)。失敗時は [] を返す。"""
    if not (ACCESS and SECRET and TAG):
        return []
    service = "ProductAdvertisingAPI"
    endpoint = f"https://{HOST}/paapi5/searchitems"
    amz_date = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    datestamp = amz_date[:8]
    payload = json.dumps({
        "PartnerTag": TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.co.jp",
        "Keywords": keyword,
        "SearchIndex": "Beauty",
        "ItemCount": item_count,
        "Resources": ["Images.Primary.Medium", "ItemInfo.Title", "Offers.Listings.Price", "CustomerReviews.Count", "CustomerReviews.StarRating"],
    })
    # --- SigV4 ---
    def h(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
    canonical_headers = f"content-encoding:amz-1.0\ncontent-type:application/json; charset=utf-8\nhost:{HOST}\nx-amz-date:{amz_date}\n"
    signed_headers = "content-encoding;content-type;host;x-amz-date"
    canonical = f"POST\n/paapi5/searchitems\n\n{canonical_headers}\n{signed_headers}\n{h(payload)}"
    scope = f"{datestamp}/{REGION}/{service}/aws4_request"
    to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n{h(canonical)}"
    k = ("AWS4" + SECRET).encode()
    for m in (datestamp, REGION, service, "aws4_request"):
        k = hmac.new(k, m.encode(), hashlib.sha256).digest()
    sig = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
    headers = {
        "content-encoding": "amz-1.0",
        "content-type": "application/json; charset=utf-8",
        "host": HOST,
        "x-amz-date": amz_date,
        "x-amz-target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        "Authorization": f"AWS4-HMAC-SHA256 Credential={ACCESS}/{scope}, SignedHeaders={signed_headers}, Signature={sig}",
    }
    try:
        r = requests.post(endpoint, data=payload, headers=headers, timeout=20)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        print(f"[amazon] PA-API失敗 {keyword}: {e}")
        return []
    out = []
    for it in (j.get("SearchResult", {}) or {}).get("Items", []):
        try:
            title = it.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "")
            detail = it.get("DetailPageURL", "")
            img = ((it.get("Images", {}).get("Primary", {}).get("Medium") or {}).get("URL")) or ""
            price = ((it.get("Offers", {}).get("Listings") or [{}])[0].get("Price") or {}).get("Amount", 0)
            out.append({
                "source": "amazon", "keyword": keyword, "asin": it.get("ASIN", ""),
                "name": title, "price": int(price or 0),
                "review_count": 0, "review_avg": 0.0,
                "shop": "Amazon.co.jp", "url": detail, "image": img, "caption": "", "jan": "",
            })
        except Exception:
            continue
    return out

def main():
    all_items = []
    use_api = bool(ACCESS and SECRET and TAG)
    print(f"[amazon] PA-API={'ON' if use_api else 'OFF(検索リンク代替)'}")
    for kw in CFG["keywords"]:
        if use_api and CFG["amazon"].get("enabled"):
            items = paapi_search(kw)
            if items:
                all_items += items
                continue
        # フォールバック: APIなしでもリンクだけ作る
        if CFG["amazon"].get("fallback_search"):
            all_items.append({
                "source": "amazon_fallback", "keyword": kw, "asin": "",
                "name": f"{kw} のAmazon検索結果",
                "price": 0, "review_count": 0, "review_avg": 0.0,
                "shop": "Amazon.co.jp", "url": amazon_search_url(kw),
                "image": "", "caption": "", "jan": "",
            })
    (DATA / "amazon_items.json").write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[amazon] 保存: {len(all_items)}件")

if __name__ == "__main__":
    main()
