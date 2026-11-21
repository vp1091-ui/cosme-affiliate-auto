"""SEO記事ひな形 + SNS投稿文を自動生成。薬機法NGワードを除去。

アフィリ投稿: 全商品を候補にし、カテゴリをローテーション + 直近投稿の除外で
「毎日同じ商品ばかり」を解消。
日常つぶやき: アフィリリンク/PR表記なしの普通の投稿を1日2件追加。
"""
import json, re, os, random, pathlib, datetime
from datetime import timedelta
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

# ===== アフィリ投稿用: 人間らしい言い回しプール (カテゴリ別+汎用) =====
KW_HOOK = {
    "クレンジング": ["落とすたび、素肌が深呼吸", "毛穴の奥まで、リセット完了", "メイクを落として、潤う肌へ", "今日の疲れも、一緒にオフ", "肌をいたわる、摩擦レス", "洗い上がりのさっぱり感が癖になる", "夜のルーティンをちょっと楽しみに"],
    "美容液": ["今日の一滴が、明日のハリになる", "肌悩みの核心へ、まっすぐ届く", "これ1本で、肌の格が上がる", "使うほど、吸いつくような肌へ", "毛穴もくすみも、恐れない肌", "夜のひと滴を、ゆっくり馴染ませて", "お手入れが好きになる一本"],
    "ファンデーション": ["隠さない、これが私の素肌美", "夕方まで、崩れを忘れる肌", "ひと塗りで、プロの仕上がり", "重ね塗りにも慣れる、自然なツヤ肌", "まとう、光の透明感", "今日の肌に、ちょうどいいカバー", "鏡を見るのが少し楽しみになる"],
    "日焼け止め": ["塗ったのを忘れる、軽さ", "太陽の下でも、ずっと透明感", "もうビクビクしない、UVケア", "きしまない、白浮きゼロ", "ひと塗りで、UVも美肌も", "顔だけじゃなく手にもぬりぬり", "朝の支度に欠かせない一本"],
    "シャンプー": ["サロン専売品で評判良いやつ", "アミノ酸系でしっとり", "カラーパーマの人向け", "泡立ちに癒されるシャンタイム", "翌日のまとまりが違うシャンプー", "お風呂が少しだけ待ち遠しい", "髪の手触りで一日が変わる"],
    "ハンドクリーム": ["触れたくなる、やわらか手肌", "ベタつきゼロ。すぐスマホへ", "カサつく手肌、瞬時にうるおう", "手洗いに負けない、続くバリア", "ふんわり香って、心もほどける", "カバンに一本入れておきたい", "手を見るたび、ちょっと嬉しい"],
    "化粧水": ["ごくごく飲むように、潤う肌", "乾くひまを与えない、保水力", "ひと雫で、もっちり弾む肌", "毛穴キュッ、肌つるん", "水のような軽さ、濃厚な潤い", "ハンドプレスでじゅわっと馴染む", "洗顔後の一番乗りはこれ"],
    "リップ": ["ひと塗りで、主役の唇へ", "色ツヤずっと、落ちない自信", "カサつく唇、瞬時にぷるん", "つけてる方が、潤うルージュ", "私のなじむ、運命の1色", "お直し用にもう一本欲しい", "リップ変えると気分も変わる"],
}
G_HOOK = ["レビュー多くて安心", "口コミ件数が多い人気組", "高評価の率がすごい", "リピ多めで安定の人気", "気になってた子をついにチェック", "みんなが選ぶ定番ってやっぱり強い", "レビュー見て納得の一本"]

# ===== 日常つぶやき (アフィリなし・PRなしの普通の投稿) =====
# {cat} はその日の投稿カテゴリから自動で入る
CHAT_TEMPLATES = [
    """朝、鏡の前で「今日はこれだ」と手に取る一本があるだけで、気持ちが整う。
最近は{cat}をゆっくり馴染ませる時間が好き。
みんなの朝の定番は？""",
    """寝落ちする直前までスキンケアしてる自分、ちょっと笑える。
でも{cat}だけは欠かせない。
続けてると手触りが変わってくるのが、地味に楽しい。""",
    """今日は久しぶりにコスメ棚を整理した。
使い切れた子、まだ半分残ってる子、いろいろ出てきた。
「また買おう」と思ったの、結局{cat}だった。""",
    """プチプラでも、自分の肌に合うとテンション上がるよね。
高ければいいってわけじゃない。最近それを実感した。
みんなのコスパ最強コスメ、こっそり教えて。""",
    """乾燥する季節になると、急に{cat}の出番が増える。
手洗いのあととか、つい重ねちゃう。
みんなは一日に何回くらい塗り直してる？""",
    """使うたびに「買ってよかった」と思うコスメ、ありますか？
私は{cat}がまさにそれ。
レビュー見て買った中で、嬉しいはずれが少ないんだよね。""",
    """ファンデの色、季節で変えちゃう。
少し日焼けした夏と、冬の肌とで全然違う。
みんなは何色くらい使い分けてる？""",
    """今日のメイク、リップだけ替えたら印象が全然違って見えた。
やっぱり唇の色って大事だなぁ。
最近お気に入りの色、知りたい。""",
    """スキンケアって、続けてこそだなって思う。
{cat}も、1日目より1ヶ月目の方がしっくりくる。
焦らず、自分のペースでいこう。""",
    """シャンプーを変えた翌日の朝、髪のまとまりが違うと嬉しい。
小さなことだけど、そこで一日の機嫌が決まる。""",
    """コスメは買うときより、使い切ったときに達成感がある。
空の容器を見ると「よく頑張った」って思えてしまう。""",
    """今日は肌がごきげん。
前の日に{cat}を丁寧に塗っただけなのに、朝の手触りが違う。
単純なことだけど、嬉しい。""",
    """「これ、どうやって使うの？」って背面を読んだこと、あるある？
{cat}も最初は戸惑ったけど、慣れると手放せなくなった。""",
    """美容の情報って、新しいものばかり目が行きがち。
でも結局戻ってくるのは、使い慣れた{cat}だったりする。""",
    """寝る前の5分、スキンケアだけはスマホを置いて向き合うようにしてる。
{cat}を馴染ませる時間が、地味に一番のリラックス。""",
    """日焼け止め、顔だけじゃなく手の甲にも塗るようになった。
小さな習慣だけど、続けると差が出る気がする。
みんなはどこまで塗ってる？""",
    """ドラッグストアで{cat}の棚の前、10分くらい迷ってしまう。
結局いつも同じのを買うんだけどね。""",
    """肌がちょっと疲れた日は、あれこれ足すより、{cat}だけに絞ると落ち着く。
シンプルが一番、ってことが多い。""",
    """コスメの投稿を見てると、みんなの「これ好き！」が伝わってくる。
今日は私も{cat}の話をしたくなった。
おすすめの使い方、あったら教えて。""",
    """ハンドクリーム、手を洗ったあとに塗るのが習慣。
ベタつかないタイプだと、すぐスマホが触れるから助かる。""",
    """朝のうちに{cat}を済ませておくと、夜が少し楽になる。
先回りした自分を、夜の自分がいつも褒めてくれる。""",
    """新しいコスメを開封する日って、ちょっと特別。
{cat}も、買った日より初めて使った日のことを覚えてる。""",
    """「今日は何もしたくない」日でも、{cat}だけはやる。
それが自分のルール。
みんなのゆるい美容習慣、聞いてみたい。""",
    """化粧水をつけたあと、ハンドプレスでじっくり馴染ませる。
ただそれだけなのに、肌がもっちりするから好き。
みんなはどうやって塗ってる？""",
]


def category_of(p: dict) -> str:
    """keyword '化粧水 敏感肌' -> '化粧水'"""
    kw = p.get("keyword") or ""
    return kw.split()[0] if kw.split() else "スキンケア"


def recent_posted_ids(days: int) -> set:
    """直近N日ぶんの投稿済み商品ID。sns/*.md はGitHubにcommitされるので
    Actions上でも履歴が残る。"""
    ids = set()
    for d in range(1, days + 1):
        day = (today() - timedelta(days=d)).isoformat()
        md = BASE / "sns" / f"{day}.md"
        if md.exists():
            ids |= set(re.findall(r"product-(\d+)\.html", md.read_text(encoding="utf-8")))
        for f in QUEUE.glob(f"{day}_product-*.txt"):
            ids.add(f.name.split("_")[1].replace("product-", "").replace(".txt", ""))
    return ids


def recent_chat_ids(days: int) -> set:
    """直近N日に使った日常つぶやきのテンプレートID。"""
    ids = set()
    for d in range(1, days + 1):
        day = (today() - timedelta(days=d)).isoformat()
        md = BASE / "sns" / f"{day}.md"
        if md.exists():
            m = re.search(r"<!--\s*chat_ids:\s*([\d,\s]*)\s*-->", md.read_text(encoding="utf-8"))
            if m:
                ids |= {int(x) for x in re.findall(r"\d+", m.group(1))}
    return ids


def _round_robin(cands, n, rng, exclude_ids, top_ratio):
    """カテゴリをシャッフルして1カテゴリ1件ずつ選ぶ (同じカテゴリが一日に集中しない)。"""
    by_kw = {}
    for p in cands:
        by_kw.setdefault(p.get("keyword") or "その他", []).append(p)
    for v in by_kw.values():
        v.sort(key=lambda x: -(x.get("review_count", 0) or 0))
    cats = list(by_kw)
    rng.shuffle(cats)
    picks = []
    for _ in range(len(cats) + 3):
        if len(picks) >= n:
            break
        progressed = False
        for kw in cats:
            if len(picks) >= n:
                break
            pool = [p for p in by_kw[kw]
                    if str(p["id"]) not in exclude_ids and p["id"] not in {q["id"] for q in picks}]
            if not pool:
                continue
            top = max(1, int(len(pool) * top_ratio))
            # 8割は上位層、2割は下位層からも拾って固定化を防ぐ
            chosen = (rng.choice(pool[top:]) if len(pool) > top and rng.random() < 0.2
                      else rng.choice(pool[:top]))
            picks.append(chosen)
            progressed = True
        if not progressed:
            break
    return picks


def pick_affiliate(products, n, rng, exclude_ids, min_reviews, top_ratio):
    """レビュー下限を満たす全商品から、カテゴリ横断でn件選ぶ。"""
    cands = [p for p in products
             if (p.get("review_count", 0) or 0) >= min_reviews and (p.get("price", 0) or 0) > 0]
    if not cands:
        cands = list(products)
    picks = _round_robin(cands, n, rng, exclude_ids, top_ratio)
    if len(picks) < n:
        # 履歴除外で足りない場合は除外なしで補充
        used = {p["id"] for p in picks}
        rest = [p for p in cands if p["id"] not in used]
        picks += _round_robin(rest, n - len(picks), rng, set(), top_ratio)
    return picks


def build_affiliate_text(p, rng, site):
    price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先"
    url = p["links"].get("rakuten") or p.get("url", "")
    cats = CFG["sns"]["hashtags"]
    tags = rng.choice(cats)
    tail = "#PR アフィリエイト広告を利用しています"
    kw = p.get("keyword", "")
    hook = next((rng.choice(h) for k, h in KW_HOOK.items() if k in kw), rng.choice(G_HOOK))
    site_cta = f"比較一覧は {site}"
    name = short_name(p["name"], 40)
    # 280字=URL2件をt.co一律23字換算。残りを本文に
    body_max = 280 - 23 * 2 - len(tags) - len(tail) - len(site_cta) - 6
    body = f"{hook}。\n{name} ▶★{p.get('review_avg',0)}({p.get('review_count',0)}件) {price}"
    if len(body) > body_max:
        over = len(body) - body_max
        name = name[:-1 - over] + "…" if over + 1 < len(name) else name[:30] + "…"
        body = f"{hook}。\n{name} ▶★{p.get('review_avg',0)}({p.get('review_count',0)}件) {price}"
    return f"{body}\n{tags}\n{url}\n{tail}\n{site_cta}"


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

    sns_cfg = CFG.get("sns", {})
    rng = random.Random(today().isoformat())
    n_posts = int(sns_cfg.get("max_posts_per_day", 7))
    n_chat = int(sns_cfg.get("chat_posts_per_day", 2))
    history_days = int(sns_cfg.get("affiliate_history_days", 10))
    min_reviews = int(sns_cfg.get("affiliate_min_review_count", 10))
    top_ratio = float(sns_cfg.get("affiliate_top_ratio", 0.7))
    site = os.getenv("SITE_URL", CFG["site"]["url"]).rstrip("/")

    # ---- アフィリ投稿: 直近の投稿商品を除外し、カテゴリを均等に回す ----
    recent_ids = recent_posted_ids(history_days)
    picks = pick_affiliate(products, n_posts, rng, recent_ids, min_reviews, top_ratio)
    print(f"[posts] アフィリ候補: 全{len(products)}件 / 直近{history_days}日除外{len(recent_ids)}件 -> {len(picks)}件")

    bundle = [f"# SNS原稿 {today().isoformat()}（コピペ用 アフィリ{len(picks)}件＋日常{n_chat}件）", "",
              "アフィリ投稿の目安: ①7:30 ②9:30 ③12:15 ④15:00 ⑤18:00 ⑥20:00 ⑦21:30",
              "日常つぶやきの目安: ⑧12:45 ⑨22:30 (PRなし・リンクなしの普通の投稿)", "",
              "## ■ アフィリエイト投稿 (PR表記あり)", ""]
    for i, p in enumerate(picks, 1):
        text = build_affiliate_text(p, rng, site)
        (QUEUE / f"{today().isoformat()}_product-{p['id']}.txt").write_text(text, encoding="utf-8")
        bundle += [f"### アフィリ {i}/{len(picks)}：{clean(p['name'])[:40]}", "", "```", text, "```",
                   f"商品ページ: {site}/product-{p['id']}.html", ""]

    # ---- 日常つぶやき: 直近使ったテンプレを除外して選ぶ ----
    chat_recent = recent_chat_ids(history_days)
    chat_pool = [i for i in range(len(CHAT_TEMPLATES)) if i not in chat_recent]
    if len(chat_pool) < n_chat:
        chat_pool = list(range(len(CHAT_TEMPLATES)))
    chat_ids = rng.sample(chat_pool, min(len(chat_pool), n_chat))
    bundle += ["## ■ 日常つぶやき (アフィリなし・PRなしの普通の投稿)", ""]
    chat_times = ["12:45", "22:30"]
    for i, idx in enumerate(chat_ids, 1):
        text = CHAT_TEMPLATES[idx]
        if "{cat}" in text:
            text = text.replace("{cat}", category_of(rng.choice(picks or products)))
        if rng.random() < float(sns_cfg.get("chat_hashtag_rate", 0.6)):
            tags = sns_cfg.get("chat_hashtags", [])
            if tags:
                text += "\n" + rng.choice(tags)
        text = clean(text)
        # zz_ 接頭辞でアフィリ投稿の後ろに並ぶようにする (自動投稿時の順序維持)
        (QUEUE / f"{today().isoformat()}_zz_chat-{i}.txt").write_text(text, encoding="utf-8")
        when = chat_times[i - 1] if i - 1 < len(chat_times) else "適当な時間"
        bundle += [f"### 日常 {i}/{n_chat}（{when}ごろ）", "", "```", text, "```", ""]

    # 履歴は sns/*.md に埋め込んで GitHub に残す (次回の重複回避に使う)
    bundle += [f"<!-- chat_ids: {','.join(map(str, chat_ids))} -->"]
    sns_dir = BASE / "sns"
    sns_dir.mkdir(exist_ok=True)
    (sns_dir / f"{today().isoformat()}.md").write_text("\n".join(bundle), encoding="utf-8")
    print(f"[posts] 記事 {len(CFG['keywords'])}件 + アフィリ原稿 {len(picks)}件 + 日常つぶやき {len(chat_ids)}件 生成")

if __name__ == "__main__":
    main()
