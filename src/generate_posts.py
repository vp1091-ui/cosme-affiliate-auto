"""SEO記事ひな形 + SNS投稿文を自動生成。薬機法NGワードを除去。"""
import json, re, os, random, pathlib, datetime
import yaml

JST = datetime.timezone(datetime.timedelta(hours=9))

def today():
    return datetime.datetime.now(JST).date()

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
    ym = today().strftime("%Y年%m月")
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

    # 人間らしい言い回しプール (日付シードで選択。カテゴリ別+汎用)
    KW_HOOK = {
        "クレンジング": ["落とすたび、素肌が深呼吸", "毛穴の奥まで、リセット完了", "メイクを落として、潤う肌へ","今日の疲れも、一緒にオフ","肌をいたわる、摩擦レス"],
        "美容液": ["ビタミンC系で人気なコレ", "くすみケアに取り入れてる人結構いるかも", "これからの季節は保湿重視で", "じんわり潤いを届ける1滴", "押しの強い原液系ならコレ"],
        "ファンデーション": ["隠さない、これが私の素肌美", "夕方まで、崩れを忘れる肌", "ひと塗りで、プロの仕上がり","塗るほどに、美肌が育つ","まとう、光の透明感"],
        "日焼け止め": ["塗ったのを忘れる、軽さ", "太陽の下でも、ずっと美白", "もう焼かない、乾かさない","きしまない、白浮きゼロ","ひと塗りで、UVも美肌も"],
        "シャンプー": ["サロン専売品で評判良いやつ", "アミノ酸系でしっとり", "カラーパーマの人向け", "泡立ちに癒されるシャンタイム", "翌日のまとまりが違うシャンプー"],
        "ハンドクリーム": ["触れたくなる、やわらか手肌", "ベタつきゼロ。すぐスマホへ", "カサつく手肌、瞬時にうるおう","手洗いに負けない、続くバリア","ふんわり香って、心もほどける"],
        "化粧水": ["ごくごく飲むように、潤う肌", "乾くひまを与えない、保水力", "ひと雫で、もっちり弾む肌","毛穴キュッ、肌つるん","水のような軽さ、濃厚な潤い"],
        "リップ": ["ひと塗りで、主役の唇へ", "色ツヤずっと、落ちない自信", "カサつく唇、瞬時にぷるん","つけてる方が、潤うルージュ","私のなじむ、運命の1色"],
    }
    G_HOOK = ["レビュー多くて安心", "口コミ件数が多い人気組", "高評価の率がすごい", "リピ多めで安定の人気"]

    # 本日のSNS投稿文 (1日N件): 高評価プールから日替わりランダム
    rng = random.Random(today().isoformat())
    ranked = sorted(products, key=lambda x: -x.get("review_count", 0))
    pool = ranked[:50] if len(ranked) > 50 else ranked
    n_posts = int(CFG["sns"].get("max_posts_per_day", 4))
    picks = rng.sample(pool, min(len(pool), n_posts))
    bundle = [f"# SNS原稿 {today().isoformat()}（コピペ用・1日{n_posts}件）", "",
              "投稿時間の目安: ①7:30 ②12:15 ③18:00 ④21:30", ""]
    for p in picks:
        price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先"
        url = p["links"].get("rakuten") or p.get("url", "")
        cats = CFG["sns"]["hashtags"]
        tags = rng.choice(cats)
        tail = "#PR アフィリエイト広告を利用しています"
        kw = p.get("keyword", "")
        hook = next((rng.choice(h) for k, h in KW_HOOK.items() if k in kw), rng.choice(G_HOOK))
        site = os.getenv("SITE_URL", CFG["site"]["url"]).rstrip("/")
        site_cta = f"比較一覧は {site}"
        name = short_name(p["name"], 40)
        # 280字=URL2件をt.co一律23字換算。残りを本文に
        body_max = 280 - 23 * 2 - len(tags) - len(tail) - len(site_cta) - 6
        body = f"{hook}。\n{name} ▶★{p.get('review_avg',0)}({p.get('review_count',0)}件) {price}"
        if len(body) > body_max:
            over = len(body) - body_max
            name = name[:-1 - over] + "…" if over + 1 < len(name) else name[:30] + "…"
            body = f"{hook}。\n{name} ▶★{p.get('review_avg',0)}({p.get('review_count',0)}件) {price}"
        text = f"{body}\n{tags}\n{url}\n{tail}\n{site_cta}"
        (QUEUE / f"{today().isoformat()}_product-{p['id']}.txt").write_text(text, encoding="utf-8")
        bundle += [f"## {clean(p['name'])[:40]}", "", "```", text, "```", f"商品ページ: {site}/product-{p['id']}.html", ""]
    sns_dir = BASE / "sns"
    sns_dir.mkdir(exist_ok=True)
    (sns_dir / f"{today().isoformat()}.md").write_text("\n".join(bundle), encoding="utf-8")
    print(f"[posts] 記事 {len(CFG['keywords'])}件 + SNS原稿 {len(picks)}件 生成")

if __name__ == "__main__":
    main()
