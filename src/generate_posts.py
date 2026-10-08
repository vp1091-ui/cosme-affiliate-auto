"""SEO記事ひな形 + SNS投稿文を自動生成。薬機法NGワードを除去。"""
import json, re, os, pathlib, datetime
import yaml

BASE = pathlib.Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))
DATA = BASE / "data"
QUEUE = DATA / "sns_queue"
QUEUE.mkdir(exist_ok=True)

NG = ["治る", "治す", "シミが消える", "シワが消える", "痩せる", "美白になる", "アトピーが治る", "効果絶大", "100%"]

def clean(s: str) -> str:
    for w in NG:
        s = s.replace(w, "うるおいケア")
    return s

def short_name(s: str, limit: int = 48) -> str:
    # SNS用: 【販促文言】除去→空白整理→短縮 (クリックされやすい形に)
    s = re.sub(r"【[^】]*】", "", clean(s))
    s = re.sub(r"\s+", " ", s).strip(" /|】")
    return s if len(s) <= limit else s[:limit] + "…"

ARTICLE_TPL = """# {kw} 比較 {ym}【自動更新】

PR: 本記事はアフィリエイト広告を利用しています。

## 結論: レビュー件数上位3選
{top3}

## 選び方 (3ポイント)
1. 肌質と成分表示を確認 (敏感肌はパッチテスト推奨)
2. レビューは件数 + 低評価理由の両方を見る
3. 容量あたり価格で比較する

## 比較表
{table}

## 注意点
- 化粧品の効果には個人差があります。断定的な効果はうたえません。
- 価格・在庫はリンク先で最新を確認してください。
"""

def main():
    f = DATA / "products.json"
    if not f.exists():
        print("[posts] products.json無し"); return
    products = json.loads(f.read_text(encoding="utf-8"))
    ym = datetime.date.today().strftime("%Y年%m月")
    art_dir = BASE / "public" / "articles"
    art_dir.mkdir(parents=True, exist_ok=True)

    # キーワード別に記事生成
    for kw in CFG["keywords"]:
        items = [p for p in products if p.get("keyword") == kw][:8]
        if not items:
            continue
        top3 = "\n".join(f"- {clean(p['name'][:50])} ★{p.get('review_avg',0)}({p.get('review_count',0)}件) {p.get('price',0):,}円" for p in items[:3])
        table = "\n".join(f"| {clean(p['name'][:30])} | {p.get('price',0):,}円 | ★{p.get('review_avg',0)} | [楽天]({p['links'].get('rakuten','')}) [Amazon]({p['links'].get('amazon','')}) |" for p in items)
        table = "| 商品 | 価格 | 評価 | リンク |\n|---|---|---|---|\n" + table
        md = ARTICLE_TPL.format(kw=kw, ym=ym, top3=top3, table=table)
        safe = re.sub(r"[\\/:*?\"<>| ]+", "_", kw)[:40]
        (art_dir / f"{safe}.md").write_text(md, encoding="utf-8")

    # SNS投稿文 (1日N件)
    picks = sorted(products, key=lambda x: -x.get("review_count", 0))[:CFG["sns"]["max_posts_per_day"]]
    bundle = [f"# SNS原稿 {datetime.date.today().isoformat()}（コピペ用）", "", "X無料枠の範囲内 (1日3件) で自動生成。Xキー未設定の場合は以下を手動投稿。", ""]
    for p in picks:
        price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先"
        url = p["links"].get("rakuten") or p.get("url", "")
        tags = CFG["sns"]["hashtags"]
        tail = "#PR アフィリエイト広告を利用しています"
        meta = f"★{p.get('review_avg',0)}({p.get('review_count',0)}件) {price}"
        # URLは絶対に切らない (切ると収益リンクが壊れる)。
        # XはURLをt.co短縮で一律23字換算するため、本文はその基準で280字に収める
        budget = 280 - 23 - len(tags) - len(tail) - 4
        name = short_name(p["name"])
        head = f"【自動更新】{name}\n{meta}"
        if len(head) > budget:
            name = name[:max(0, budget - len("【自動更新】\n" + meta) - 1)] + "…"
            head = f"【自動更新】{name}\n{meta}"
        text = f"{head}\n{tags}\n{url}\n{tail}"
        (QUEUE / f"{datetime.date.today().isoformat()}_product-{p['id']}.txt").write_text(text, encoding="utf-8")
        bundle += [f"## {clean(p['name'])[:40]}", "", "```", text, "```", f"商品ページ: {os.getenv('SITE_URL', CFG['site']['url']).rstrip('/')}/product-{p['id']}.html", ""]
    sns_dir = BASE / "sns"
    sns_dir.mkdir(exist_ok=True)
    (sns_dir / f"{datetime.date.today().isoformat()}.md").write_text("\n".join(bundle), encoding="utf-8")
    print(f"[posts] 記事 {len(CFG['keywords'])}件 + SNS原稿 {len(picks)}件 生成")

if __name__ == "__main__":
    main()
