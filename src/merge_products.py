"""楽天+Amazonを名寄せして products.json を作る。価格比較・重複排除。"""
import json, re, pathlib

BASE = pathlib.Path(__file__).resolve().parents[1]
DATA = BASE / "data"

def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"【.*?】|\[.*?\]|\(.*?\)|（.*?）", "", s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"送料無料|ポイント\d+倍|楽天市場|amazon|限定|公式|正規品", "", s)
    return s[:40]

def score(it):
    # レビュー件数×評価を重視、価格0は後回し
    p = it.get("price", 0) or 999999
    return (it.get("review_count", 0) * (it.get("review_avg", 0) or 3.0), -p)

def main():
    rak = json.loads((DATA / "rakuten_items.json").read_text(encoding="utf-8")) if (DATA / "rakuten_items.json").exists() else []
    amz = json.loads((DATA / "amazon_items.json").read_text(encoding="utf-8")) if (DATA / "amazon_items.json").exists() else []
    rank = json.loads((DATA / "rakuten_ranking.json").read_text(encoding="utf-8")) if (DATA / "rakuten_ranking.json").exists() else []
    pool = rak + amz

    seen, products = set(), []
    for it in sorted(pool, key=score, reverse=True):
        key = norm(it.get("name", ""))
        if len(key) < 6 or key in seen:
            continue
        seen.add(key)
        # 同一商品の楽天/Amazonリンクを紐付け
        links = {"rakuten": "", "amazon": ""}
        for cand in pool:
            if norm(cand.get("name", "")) == key:
                if cand["source"] == "rakuten" and not links["rakuten"]:
                    links["rakuten"] = cand["url"]
                    it.setdefault("image", cand.get("image", ""))
                    if not it.get("price") and cand.get("price"):
                        it["price"] = cand["price"]
                if cand["source"].startswith("amazon") and not links["amazon"]:
                    links["amazon"] = cand["url"]
        it["links"] = links
        products.append(it)

    # ランキング情報を付与
    rank_names = {norm(r["name"]): r.get("rank", 99) for r in rank}
    for p in products:
        p["rank"] = rank_names.get(norm(p["name"]), 99)

    products = sorted(products, key=lambda x: (x["rank"], -x.get("review_count", 0)))[:200]
    for i, p in enumerate(products, 1):
        p["id"] = i
    (DATA / "products.json").write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[merge] products.json: {len(products)}件")

if __name__ == "__main__":
    main()
