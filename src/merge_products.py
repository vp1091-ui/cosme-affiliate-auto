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
    # タグ無しAmazon検索リンク(収益にならない代替)は商品化も紐付けもしない
    pool = [c for c in pool if not (c.get("source") == "amazon_fallback" and "tag=" not in (c.get("url") or ""))]

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

    # 全体200件に絞るが、カテゴリごとに最低10件は確保 (プチプラ救済)
    # 先に全体ソート→200件→不足カテゴリをプールから補充、の順で実施
    import yaml as _yaml
    try:
        _cfg = _yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))
        _keywords = _cfg.get("keywords", [])
    except Exception:
        _keywords = []
    products = sorted(products, key=lambda x: (x["rank"], -x.get("review_count", 0)))
    base = products[:200]
    base_keys = {id(p) for p in base}
    by_kw_base = {}
    for p in base:
        by_kw_base.setdefault(p.get("keyword", ""), []).append(p)
    for kw in _keywords:
        have = len(by_kw_base.get(kw, []))
        if have < 10:
            # プール全体から同keywordで未採用分を追加 (評価順)
            cands = [p for p in products if p.get("keyword") == kw and id(p) not in base_keys]
            cands = sorted(cands, key=lambda x: -x.get("review_count", 0))
            need = min(10 - have, len(cands))
            for c in cands[:need]:
                base.append(c)
                base_keys.add(id(c))
            by_kw_base[kw] = [p for p in base if p.get("keyword") == kw]
            have = len(by_kw_base[kw])
        if have < 10 and "プチプラ" in kw:
            # それでも不足 (API再取得前など) はプチプラ相当を複製補充: 安価+高評価を優先
            import copy as _copy
            used_norms = {norm(p.get("name", "")) for p in base if p.get("keyword") == kw}
            cheap_pool = [p for p in products if id(p) not in base_keys or True]
            def _cheap_key(p):
                price = p.get("price", 0) or 999999
                name = p.get("name", "")
                lip_bonus = 1 if any(w in name for w in ["リップ", "口紅", "ティント", "グロス", "リップクリーム"]) else 0
                return (lip_bonus, -(price <= 2000), p.get("review_avg", 0) or 0, p.get("review_count", 0))
            cheap_pool = sorted(cheap_pool, key=_cheap_key, reverse=True)
            for c in cheap_pool:
                if len([p for p in base if p.get("keyword") == kw]) >= 10:
                    break
                if norm(c.get("name", "")) in used_norms:
                    continue
                if (c.get("price", 0) or 999999) > 3000:
                    continue
                dup = _copy.deepcopy(c)
                dup["keyword"] = kw
                dup.pop("id", None)
                base.append(dup)
                used_norms.add(norm(c.get("name", "")))
    products = sorted(base, key=lambda x: (x["rank"], -x.get("review_count", 0)))[:220]
    for i, p in enumerate(products, 1):
        p["id"] = i
    (DATA / "products.json").write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[merge] products.json: {len(products)}件")

if __name__ == "__main__":
    main()
