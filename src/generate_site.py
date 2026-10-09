"""products.json から静的HTMLを生成 (トップ/カテゴリ/商品詳細/sitemap/rss)。
- 取扱ソース自動検出: Amazonリンクが無ければ楽天専用コピーになる
- 集客: カテゴリ別ページ、JSON-LD構造化データ、OGP、更新日表示
- 薬機法・ステマ規制対応: 効果断定を避け、PR表記を全頁に"""
import json, html, pathlib, datetime, re
import yaml

try:
    from load_env import load_env
    load_env()
except Exception:
    pass

BASE = pathlib.Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))
DATA = BASE / "data"
OUT = BASE / CFG["site_gen"]["output_dir"]
import os
SITE_URL = os.getenv("SITE_URL", CFG["site"]["url"]).rstrip("/")
SITE_NAME = os.getenv("SITE_NAME", CFG["site"]["name"])
JST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(JST).date()  # runnerはUTCのためJSTに補正
YM = TODAY.strftime("%Y年%m月")

CSS = """
:root{--pink:#e91e63;--pink-d:#c2185b;--bg:#fff5f7;--ink:#4a3340;--mut:#98707f;--gold:#f5a623}
*{box-sizing:border-box}body{font-family:'Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif;margin:0;color:var(--ink);background:#fff;line-height:1.8}
a{color:var(--pink-d)}.wrap{max-width:1000px;margin:0 auto;padding:0 16px}
.hero{background:linear-gradient(135deg,#ff5e8a,#b6205a);color:#fff;padding:44px 0 36px;text-align:center}
.hero h1{margin:0 0 8px;font-size:1.7em}.hero p{margin:4px 0;opacity:.95}.hero .date{display:inline-block;background:rgba(255,255,255,.25);border-radius:20px;padding:2px 14px;font-size:.85em;margin-top:8px}
nav.top{position:sticky;top:0;background:#fff;border-bottom:1px solid #f3dfe5;z-index:10}
nav.top .wrap{display:flex;gap:16px;overflow-x:auto;padding:10px 16px;white-space:nowrap}
nav.top a{text-decoration:none;font-weight:bold;font-size:.95em}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}
.chip{background:var(--bg);border:1px solid #f0c9d4;border-radius:20px;padding:4px 14px;text-decoration:none;font-size:.9em}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin:16px 0 32px}
.card{border:1px solid #f0dde3;border-radius:14px;padding:12px;position:relative;background:#fff;transition:transform .15s}
.card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(233,30,99,.12)}
.card img{width:100%;height:170px;object-fit:contain;background:#faf7f8;border-radius:8px}
.card h3{font-size:.92em;margin:8px 0;min-height:3.2em}
.card h3 a{color:var(--ink);text-decoration:none}
.rank{position:absolute;top:-10px;left:-6px;color:#fff;font-weight:bold;font-size:.85em;padding:2px 12px;border-radius:12px;background:#b0a0a6}
.rank.r1{background:linear-gradient(135deg,#ffd54f,#ff8f00)}.rank.r2{background:linear-gradient(135deg,#e0e0e0,#8d8d8d)}.rank.r3{background:linear-gradient(135deg,#ffab91,#bf5f2a)}
.stars{color:var(--gold);font-weight:bold}.price{color:var(--pink-d);font-weight:bold;font-size:1.15em}
.btn{display:inline-block;padding:9px 14px;border-radius:10px;text-decoration:none;margin:6px 6px 0 0;font-weight:bold;font-size:.92em}
.r{background:#bf0000;color:#fff}.a{background:#ff9900;color:#111}
.note{font-size:.82em;color:var(--mut)}.pr{font-size:.8em;background:#fff8e1;padding:10px 14px;border-radius:10px;margin:12px 0}
.detail{display:grid;grid-template-columns:320px 1fr;gap:20px;margin:20px 0}
.detail img{width:100%;border-radius:12px;border:1px solid #f0dde3}
.cta{background:var(--bg);border-radius:14px;padding:16px;margin:16px 0}
h2.sec{border-left:5px solid var(--pink);padding-left:10px;margin-top:32px}
footer{background:#3a2530;color:#e8c9d3;padding:24px 0;margin-top:40px;font-size:.85em}
footer a{color:#ffd9e4}
@media(max-width:640px){.detail{grid-template-columns:1fr}.hero h1{font-size:1.3em}}
"""

def esc(s): return html.escape(str(s or ""))

def _is_real_amazon(url):
    u = url or ""
    # PA-APIの商品URL(/dp/)か紹介料タグ付きのみ本物。素の検索リンクは除外
    return "amazon.co.jp" in u and ("/dp/" in u or "tag=" in u)

def detect_sources(products):
    has_r = any((p.get("links", {}).get("rakuten") or (p.get("url", "") if p.get("source") == "rakuten" else "")) for p in products)
    has_a = any(_is_real_amazon(p.get("links", {}).get("amazon")) for p in products)
    if has_r and has_a:
        return "楽天・Amazon"
    if has_a:
        return "Amazon"
    return "楽天"

def btns(p):
    b = ""
    lk = p.get("links", {})
    if lk.get("rakuten"):
        b += f'<a class="btn r" href="{esc(lk["rakuten"])}" rel="nofollow sponsored noopener" target="_blank">楽天で最安値をチェック</a>'
    elif p.get("url") and p.get("source") == "rakuten":
        b += f'<a class="btn r" href="{esc(p["url"])}" rel="nofollow sponsored noopener" target="_blank">楽天で最安値をチェック</a>'
    if lk.get("amazon") and _is_real_amazon(lk.get("amazon")):
        b += f'<a class="btn a" href="{esc(lk["amazon"])}" rel="nofollow sponsored noopener" target="_blank">Amazonでチェック</a>'
    return b

def stars(avg):
    try:
        v = float(avg or 0)
    except Exception:
        v = 0.0
    full = int(v)
    return "★" * full + "☆" * (5 - full)

def rank_badge(i):
    cls = f"r{i}" if i <= 3 else ""
    return f'<span class="rank {cls}">{i}位</span>'

def card(p, i=None):
    img = f'<img src="{esc(p.get("image",""))}" alt="{esc(p.get("name",""))}" loading="lazy">' if p.get("image") else ""
    price = f'<span class="price">{p["price"]:,}円</span>' if p.get("price") else "価格はリンク先で確認"
    badge = rank_badge(i) if i else ""
    return f"""<div class="card">{badge}{img}<h3><a href="product-{p['id']}.html">{esc(p['name'][:60])}</a></h3>
<div><span class="stars">{stars(p.get('review_avg'))}</span> {esc(p.get('review_avg',0))} ({esc(p.get('review_count',0))}件)</div>
<div>{price}</div><div class="note">{esc(p.get('shop',''))}</div>{btns(p)}</div>"""

def page(title, desc, body, extra_head="", canonical=""):
    canon = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    ads_cfg = CFG.get("ads", {})
    ad_head = ""
    if ads_cfg.get("adsense_client"):
        ad_head = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(ads_cfg["adsense_client"])}" crossorigin="anonymous"></script>'
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}"><meta property="og:site_name" content="{esc(SITE_NAME)}">
{canon}{ad_head}{extra_head}<style>{CSS}</style></head><body>
<nav class="top"><div class="wrap"><a href="index.html">🏠 トップ</a><a href="ranking.html">👑 ランキング</a><a href="privacy.html">🔒 プライバシー</a><a href="about.html">ℹ️ 運営者</a></div></nav>
<div class="wrap"><p class="pr">PR: 当サイトはアフィリエイト広告を利用しています。掲載価格・在庫は取得時点のもので変更される場合があります。化粧品の効果には個人差があります。</p></div>
{body}
{ad_block("article")}
<footer><div class="wrap"><p>© {esc(SITE_NAME)} / 価格・レビューは毎日自動更新 (最終更新 {TODAY.isoformat()})</p>
<p><a href="privacy.html">プライバシーポリシー</a> ｜ <a href="about.html">運営者情報・お問い合わせ</a></p>
<p>効果・効能の断定的な表示はしていません。肌に合わない場合は使用を中止し専門医にご相談ください。</p></div></footer></body></html>"""

def ad_block(kind):
    """表示課金広告枠。ID未設定なら何も出さない"""
    ads_cfg = CFG.get("ads", {})
    client = ads_cfg.get("adsense_client", "")
    slot = ads_cfg.get("adsense_slot_top" if kind == "top" else "adsense_slot_article", "")
    if not (client and slot):
        return ""
    return f"""<div class="wrap"><div style="margin:20px 0;text-align:center">
<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(client)}" data-ad-slot="{esc(slot)}" data-ad-format="auto" data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div></div>"""

def jsonld_itemlist(items, url):
    els = []
    for i, p in enumerate(items[:20], 1):
        els.append({"@type": "ListItem", "position": i, "url": f"{url}/product-{p['id']}.html", "name": p["name"][:80]})
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": els}, ensure_ascii=False) + "</script>"

def detail(p, src_label, related):
    price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先で確認"
    ld = {"@context": "https://schema.org", "@type": "Product", "name": p["name"][:100],
          "image": p.get("image", ""), "description": (p.get("caption") or "")[:200],
          "offers": {"@type": "Offer", "priceCurrency": "JPY", "price": p.get("price", 0), "availability": "https://schema.org/InStock"}}
    try:
        ld["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": float(p.get("review_avg", 0) or 0), "reviewCount": int(p.get("review_count", 0) or 0)}
    except Exception:
        pass
    rel = "".join(card(r) for r in related[:4])
    body = f"""<div class="hero"><div class="wrap"><h1>{esc(p['name'][:60])}</h1>
<p><span class="stars">{stars(p.get('review_avg'))}</span> {esc(p.get('review_avg',0))} ({esc(p.get('review_count',0))}件のレビュー) / {esc(price)}</p></div></div>
<div class="wrap"><p><a href="index.html">← トップへ</a> ｜ {esc(p.get('keyword',''))}</p>
<div class="detail"><div>{'<img src="'+esc(p['image'])+'" alt="'+esc(p['name'])+'">' if p.get('image') else ''}</div>
<div><p>販売店: {esc(p.get('shop',''))} (取扱: {esc(src_label)})</p>
<div class="cta">{btns(p)}<p class="note">ボタン先の最新価格・在庫・レビューをご確認ください</p></div></div></div>
<h2 class="sec">失敗しない選び方 (3ポイント)</h2>
<ul><li>肌質・成分表示を確認し、初めてはパッチテストを</li><li>レビューは件数と低評価理由の両方をチェック</li><li>容量あたり価格でコスパ比較 ({esc(src_label)}横断がお得)</li></ul>
<h2 class="sec">同じ悩みの人気商品</h2><div class="cards">{rel}</div></div>"""
    head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
    return page(f"{p['name'][:50]}の口コミ・最安値 | {SITE_NAME}",
                f"{p['name'][:80]}のレビュー・価格まとめ。{src_label}横断で比較。",
                body, head, f"{SITE_URL}/product-{p['id']}.html")

def cat_slug(kw):
    return re.sub(r"\s+", "-", kw.strip())[:30]

def main():
    f = DATA / "products.json"
    if not f.exists():
        print("[site] products.json が無い"); return
    products = json.loads(f.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    top_n = CFG["site_gen"]["top_n"]
    src_label = detect_sources(products)
    print(f"[site] 取扱ソース: {src_label}")
    by_kw = {}
    for p in products:
        by_kw.setdefault(p.get("keyword", "その他"), []).append(p)

    chips = "".join(f'<a class="chip" href="cat-{i}.html">{esc(kw)} ({len(v)}件)</a>' for i, (kw, v) in enumerate(by_kw.items()))
    top = products[:top_n]
    hero = f"""<div class="hero"><div class="wrap"><h1>💄 {esc(SITE_NAME)}</h1>
<p>{esc(src_label)}の人気コスメをレビュー件数・評価・価格で自動比較</p>
<p>全{len(products)}商品掲載中・口コミ合計{sum(p.get('review_count',0) for p in products):,}件を集計</p>
<span class="date">📅 {YM}版・毎日6時自動更新</span></div></div>"""
    index_body = hero + f"""<div class="wrap"><h2 class="sec">悩み別に探す</h2><div class="chips">{chips}</div>
<h2 class="sec">👑 今週の人気ランキング TOP{len(top)}</h2><div class="cards">{''.join(card(p, i+1) for i, p in enumerate(top))}</div></div>"""
    (OUT / "index.html").write_text(
        page(f"{SITE_NAME}｜{src_label}コスメの口コミ・価格比較【{YM}版】",
             f"{src_label}の人気コスメ{len(products)}商品をレビュー・価格で自動比較。毎日更新。",
             index_body, jsonld_itemlist(top, SITE_URL), f"{SITE_URL}/index.html"), encoding="utf-8")

    rank_sorted = sorted(products, key=lambda x: -x.get("review_count", 0))[:top_n]
    (OUT / "ranking.html").write_text(
        page(f"コスメ人気ランキング【{YM}版】レビュー件数順｜{SITE_NAME}",
             f"レビュー件数で集計したコスメランキングTOP{len(rank_sorted)}。{src_label}横断・毎日更新。",
             f"""<div class="hero"><div class="wrap"><h1>👑 コスメ人気ランキング</h1><p>レビュー件数順・{YM}版・毎日自動更新</p></div></div>
<div class="wrap"><div class="cards">{''.join(card(p, i+1) for i, p in enumerate(rank_sorted))}</div></div>""",
             jsonld_itemlist(rank_sorted, SITE_URL), f"{SITE_URL}/ranking.html"), encoding="utf-8")

    cat_files = []
    for i, (kw, v) in enumerate(by_kw.items()):
        v_sorted = sorted(v, key=lambda x: -x.get("review_count", 0))
        (OUT / f"cat-{i}.html").write_text(
            page(f"{kw} おすすめ{len(v_sorted)}選【{YM}版】口コミ・価格比較｜{SITE_NAME}",
                 f"{kw}の人気商品をレビュー件数・評価・価格で比較。{src_label}横断・毎日更新。",
                 f"""<div class="hero"><div class="wrap"><h1>{esc(kw)} おすすめ</h1><p>レビュー件数順・{len(v_sorted)}商品・{YM}版</p></div></div>
<div class="wrap"><p><a href="index.html">← トップへ</a></p><div class="cards">{''.join(card(p, j+1) for j, p in enumerate(v_sorted))}</div></div>""",
                 jsonld_itemlist(v_sorted, SITE_URL), f"{SITE_URL}/cat-{i}.html"), encoding="utf-8")
        cat_files.append(f"cat-{i}.html")

    for p in products:
        related = [r for r in by_kw.get(p.get("keyword", ""), []) if r["id"] != p["id"]]
        related = sorted(related, key=lambda x: -x.get("review_count", 0))
        (OUT / f"product-{p['id']}.html").write_text(detail(p, src_label, related), encoding="utf-8")

    # 審査・信頼性用固定ページ
    op = CFG["site"]
    (OUT / "privacy.html").write_text(page(
        f"プライバシーポリシー｜{SITE_NAME}",
        f"{SITE_NAME}のプライバシーポリシー。広告配信・アクセス解析・Cookieについて。",
        f"""<div class="wrap"><h1>プライバシーポリシー</h1>
<h2 class="sec">広告の配信について</h2>
<p>当サイトでは、第三者配信の広告サービス (Google AdSense等) を利用する場合があります。広告配信事業者は、ユーザーの興味に応じた広告を表示するためCookieを使用することがあります。Cookieを無効にする方法やGoogleポリシーについては <a href="https://policies.google.com/technologies/ads" rel="noopener" target="_blank">Googleポリシーと規約</a> をご覧ください。</p>
<h2 class="sec">アフィリエイトについて</h2>
<p>当サイトは楽天アフィリエイト等のアフィリエイトプログラムに参加しています。商品購入時に販売店から紹介料を受け取る場合があります。価格・在庫は取得時点の情報です。</p>
<h2 class="sec">アクセス解析について</h2>
<p>サイト改善のためアクセス解析を利用する場合があります。データは匿名で収集されます。</p>
<h2 class="sec">免責事項</h2>
<p>掲載情報の正確性には努めますが保証しません。化粧品の効果には個人差があります。損害等の責任は負いかねます。</p>
<p class="note">制定 {TODAY.isoformat()} / {esc(SITE_NAME)}</p></div>""",
        "", f"{SITE_URL}/privacy.html"), encoding="utf-8")
    (OUT / "about.html").write_text(page(
        f"運営者情報・お問い合わせ｜{SITE_NAME}",
        f"{SITE_NAME}の運営者情報とお問い合わせ先。",
        f"""<div class="wrap"><h1>運営者情報・お問い合わせ</h1>
<p>サイト名: {esc(SITE_NAME)} / 運営: {esc(op.get('operator', ''))}</p>
<p>連絡先: {esc(op.get('contact', ''))}</p>
<p>内容: {esc(src_label)}の人気コスメを自動集計し、レビュー・価格比較を毎日更新しています。</p></div>""",
        "", f"{SITE_URL}/about.html"), encoding="utf-8")

    urls = ["index.html", "ranking.html", "privacy.html", "about.html"] + cat_files + [f"product-{p['id']}.html" for p in products]
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in urls:
        sm += f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>"
    sm += "</urlset>"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    rss = f'<?xml version="1.0"?><rss version="2.0"><channel><title>{esc(SITE_NAME)}</title><link>{SITE_URL}</link><description>{esc(src_label)}コスメ毎日更新</description>'
    for p in top[:20]:
        rss += f"<item><title>{esc(p['name'][:80])}</title><link>{SITE_URL}/product-{p['id']}.html</link><description>{esc(p.get('keyword',''))}</description></item>"
    rss += "</channel></rss>"
    (OUT / "rss.xml").write_text(rss, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"[site] 生成完了: {len(products)}商品 + カテゴリ{len(cat_files)}頁 -> {OUT}")

if __name__ == "__main__":
    main()
