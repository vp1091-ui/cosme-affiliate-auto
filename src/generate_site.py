"""products.json から静的HTMLを生成 (トップ/カテゴリ/商品詳細/sitemap/rss)。
- 取扱ソース自動検出: Amazonリンクが無ければ楽天専用コピーになる
- 集客: カテゴリ別ページ、JSON-LD構造化データ、OGP、更新日表示
- 薬機法・ステマ規制対応: 効果断定を避け、PR表記を全頁に"""
import json, html, pathlib, datetime, re
import yaml

from content import clean_product_name, guide_for, GUIDES

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
.hero .logo{width:76px;height:76px;border-radius:50%;border:3px solid rgba(255,255,255,.85);object-fit:cover;background:#fff}
.hero .xlink{color:#fff;font-weight:bold}
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
/* --- 収益化・UX改善用 --- */
.badges{display:flex;gap:5px;flex-wrap:wrap;margin:6px 0}
.badge{font-size:.7em;font-weight:bold;padding:2px 8px;border-radius:20px;background:#fff0f4;color:var(--pink-d);border:1px solid #f7c6d4}
.badge.gold{background:#fff8e1;color:#a06800;border-color:#f3dfa0}
.badge.blue{background:#eef6ff;color:#245d94;border-color:#c9def5}
.top3{width:100%;border-collapse:collapse;margin:14px 0 8px;font-size:.92em}
.top3 th,.top3 td{border:1px solid #f0dde3;padding:9px 8px;text-align:left;vertical-align:top}
.top3 th{background:var(--bg);white-space:nowrap}
.top3 tr:nth-child(even){background:#fffafb}
.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:var(--bg);border:1px solid #f0c9d4;border-radius:12px;padding:12px;margin:12px 0}
.filters label{font-size:.85em;font-weight:bold}
.filters select,.filters input{padding:6px 8px;border:1px solid #e8c2ce;border-radius:8px;background:#fff;font-size:.9em}
.count{font-size:.85em;color:var(--mut);margin-left:auto}
.guide{background:#fffafc;border:1px solid #f4dce4;border-radius:14px;padding:18px 20px;margin:22px 0}
.guide h3{font-size:1.05em;margin:18px 0 8px;border-left:4px solid var(--pink);padding-left:8px}
.guide h3:first-child{margin-top:0}
.guide ol,.guide ul{padding-left:22px;margin:6px 0}
.guide li{margin:6px 0}
.guide .lead{font-weight:bold;background:#fff;border-radius:8px;padding:10px 12px}
.faq details{border-bottom:1px solid #f0dde3;padding:8px 0}
.faq summary{cursor:pointer;font-weight:bold;color:var(--pink-d)}
.faq p{margin:6px 0 10px}
.crumb{font-size:.82em;color:var(--mut);margin:10px 0}
.footnav{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin:10px 0}
.footnav a{text-decoration:underline}
.formbox{background:#fff;border:1px solid #f0dde3;border-radius:12px;padding:14px;max-width:680px;margin:0 auto}
.formbox iframe{width:100%;border:0;min-height:640px}
.column-promo{background:linear-gradient(135deg,#fff0f5,#ffe3ee);border:2px solid #f7c6d4;border-radius:16px;padding:20px 24px;margin:22px 0 10px}
.column-promo h2{font-size:1.6em;margin:0 0 6px;color:var(--pink-d)}
.column-promo .lead{font-size:1.05em;font-weight:bold;margin:0 0 12px}
.column-list{list-style:none;padding:0;margin:0 0 10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:8px}
.column-list li{background:#fff;border-radius:10px;padding:8px 12px;border:1px solid #f4dce4}
.column-list a{font-size:1.05em;font-weight:bold;text-decoration:none}
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

# 薬機法NG (断定・誇大)。商品説明の該当箇所は言い換え
NG_WORDS = ["治る", "治す", "シミが消える", "シワが消える", "痩せる", "美白になる",
            "アトピーが治る", "効果絶大", "100%効く", "完全無添加で安心"]

def clean_desc(s: str) -> str:
    s = s or ""
    for w in NG_WORDS:
        s = s.replace(w, "うるおいケア")
    return s

def excerpt(s: str, limit: int = 400) -> str:
    # 文の途中で切らない: 制限内で最後の「。」まで戻る
    s = clean_desc(s)
    if len(s) <= limit:
        return s
    cut = s[:limit]
    pos = cut.rfind("。")
    if pos > limit * 0.4:
        return cut[:pos + 1]
    return cut + "…"

# カテゴリ別の選び方1行 (共通3ポイントに加える)
CAT_TIP = {
    "化粧水": "保湿成分・アルコールの有無・詰め替えの有無を確認",
    "美容液": "主成分と濃度表記・朝用か夜用か・衛生的な容器かを確認",
    "クレンジング": "普段のメイク濃さとの相性・W洗顔要否・マツエク対応を確認",
    "日焼け止め": "SPF/PA値・白浮きの有無・石けんで落とせるかを確認",
    "リップ": "UV対応・ティントか・保湿の持続を確認",
    "ファンデーション": "色展開の豊富さ・崩れにくさ・石けん落ち対応を確認",
    "シャンプー": "アミノ酸系か・シリコンの有無・詰替でコスパ比較",
    "ハンドクリーム": "ベタつき・香りの強さ・持ち歩きサイズかを確認",
}

def cat_tip(keyword: str) -> str:
    for k, v in CAT_TIP.items():
        if k in (keyword or ""):
            return v
    return "容量あたり価格と使用量目安でコスパ比較"

def rank_badge(i):
    cls = f"r{i}" if i <= 3 else ""
    return f'<span class="rank {cls}">{i}位</span>'


def _num(v, default=0):
    try:
        return v if isinstance(v, (int, float)) else default
    except Exception:
        return default


def badges(p):
    """レビュー数・評価・価格から自動でマイクロコピーバッジを付与"""
    rc = int(_num(p.get("review_count")) or 0)
    avg = float(_num(p.get("review_avg")) or 0)
    price = int(_num(p.get("price")) or 0)
    out = []
    if rc >= 1000:
        out.append('<span class="badge gold">口コミ1,000件超え</span>')
    elif rc >= 500:
        out.append('<span class="badge">口コミ500件超え</span>')
    if avg >= 4.5:
        out.append('<span class="badge gold">★4.5以上の高評価</span>')
    elif avg >= 4.0:
        out.append('<span class="badge blue">★4.0以上</span>')
    if 0 < price <= 2000:
        out.append('<span class="badge">2,000円以下のプチプラ</span>')
    elif 0 < price <= 5000:
        out.append('<span class="badge blue">5,000円以下</span>')
    return '<div class="badges">' + "".join(out) + "</div>" if out else ""


def display_name(p, limit=46):
    """整形済み商品名。整形で空になった場合は元の名前に戻す"""
    name = clean_product_name(p.get("name", ""), limit)
    return name or str(p.get("name", ""))[:limit]


def jsonld_breadcrumb(items):
    els = [{"@type": "ListItem", "position": i, "name": n, "item": u}
           for i, (n, u) in enumerate(items, 1)]
    return '<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": els},
        ensure_ascii=False) + "</script>"


def jsonld_faq(faq):
    els = [{"@type": "Question", "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]
    return '<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": els},
        ensure_ascii=False) + "</script>"


def render_guide(kw):
    """カテゴリ独自コンテンツ4ブロック。FAQデータも構造化データ用に返す"""
    g = guide_for(kw)
    tips = "".join(f"<li><strong>{esc(t)}</strong>：{esc(d)}</li>" for t, d in g["tips"])
    ing = "".join(f"<li><strong>{esc(t)}</strong>：{esc(d)}</li>" for t, d in g["ingredients"])
    types = "".join(f"<li><strong>{esc(t)}</strong>：{esc(d)}</li>" for t, d in g["types"])
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in g["faq"])
    html = f"""<section class="guide">
<h3>失敗しない選び方ガイド</h3><p class="lead">{esc(g['lead'])}</p><ol>{tips}</ol>
<h3>注目成分の解説</h3><ul>{ing}</ul>
<h3>肌質・悩み別のおすすめタイプ診断</h3><ul>{types}</ul>
<h3>よくある質問（FAQ）</h3><div class="faq">{faq}</div>
</section>"""
    return html, g["faq"]


def top3_table(items):
    """目的別おすすめTOP3比較表 (コスパ / 口コミ数 / 高評価)"""
    cost_pool = [p for p in items if int(_num(p.get("price")) or 0) > 0]
    cost = sorted(cost_pool, key=lambda p: -(
        int(_num(p.get("review_count")) or 0) * float(_num(p.get("review_avg")) or 3.0)
        / max(1, int(_num(p.get("price"))))))[:1]
    by_reviews = sorted(items, key=lambda p: -int(_num(p.get("review_count")) or 0))[:1]
    high_pool = [p for p in items if int(_num(p.get("review_count")) or 0) >= 10] or items
    by_high = sorted(high_pool, key=lambda p: -float(_num(p.get("review_avg")) or 0))[:1]
    rows = [("コスパ重視", cost), ("口コミ数重視", by_reviews), ("高評価重視", by_high)]
    trs = ""
    for label, arr in rows:
        if not arr:
            continue
        p = arr[0]
        price = int(_num(p.get("price")) or 0)
        trs += (f'<tr><th>{esc(label)}</th>'
                f'<td><a href="product-{p["id"]}.html">{esc(display_name(p, 36))}</a></td>'
                f'<td>{esc(stars(p.get("review_avg")))} {esc(p.get("review_avg", 0))}</td>'
                f'<td>{esc(p.get("review_count", 0))}件</td>'
                f'<td>{price:,}円</td><td>{btns(p)}</td></tr>')
    return f"""<h2 class="sec">迷ったらコレ！目的別おすすめTOP3</h2>
<p class="note">同じカテゴリの商品を「容量あたりの満足度」「口コミの多さ」「評価の高さ」で比較しました。</p>
<table class="top3"><thead><tr><th>目的</th><th>商品</th><th>評価</th><th>口コミ</th><th>価格</th><th>チェック</th></tr></thead>
<tbody>{trs}</tbody></table>"""


def filter_bar(total):
    return f"""<div class="filters">
<label>価格帯 <select id="fPrice"><option value="999999">すべて</option><option value="2000">2,000円以下</option>
<option value="5000">5,000円以下</option><option value="10000">10,000円以下</option></select></label>
<label>並び替え <select id="fSort"><option value="default">おすすめ順</option><option value="rating">評価が高い順</option>
<option value="reviews">レビュー件数順</option><option value="price">安い順</option></select></label>
<span class="count" id="fCount">{total}件表示 / 全{total}件</span></div>"""


FILTER_JS = """<script>
(function(){
  var box=document.getElementById('cards');
  if(!box) return;
  var cards=Array.prototype.slice.call(box.children);
  var price=document.getElementById('fPrice'), sort=document.getElementById('fSort'), cnt=document.getElementById('fCount');
  function apply(){
    var max=parseInt(price.value,10)||999999, mode=sort.value;
    var list=cards.filter(function(c){return parseInt(c.dataset.price||'0',10)<=max;});
    list.sort(function(a,b){
      if(mode==='rating') return (parseFloat(b.dataset.rating)||0)-(parseFloat(a.dataset.rating)||0);
      if(mode==='reviews') return (parseInt(b.dataset.reviews)||0)-(parseInt(a.dataset.reviews)||0);
      if(mode==='price') return (parseInt(a.dataset.price)||0)-(parseInt(b.dataset.price)||0);
      return 0;
    });
    cards.forEach(function(c){c.style.display='none';});
    list.forEach(function(c){box.appendChild(c);c.style.display='';});
    cnt.textContent=list.length+'件表示 / 全'+cards.length+'件';
  }
  price.addEventListener('change',apply); sort.addEventListener('change',apply); apply();
})();
</script>"""

def card(p, i=None):
    name = display_name(p)
    img = f'<img src="{esc(p.get("image",""))}" alt="{esc(name)}" loading="lazy">' if p.get("image") else ""
    pr = int(_num(p.get("price")) or 0)
    price = f'<span class="price">{pr:,}円</span>' if pr else "価格はリンク先で確認"
    badge = rank_badge(i) if i else ""
    return f"""<div class="card" data-price="{pr}" data-rating="{float(_num(p.get('review_avg')) or 0)}" data-reviews="{int(_num(p.get('review_count')) or 0)}">{badge}{img}<h3><a href="product-{p['id']}.html">{esc(name)}</a></h3>
{badges(p)}
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
<nav class="top"><div class="wrap"><a href="index.html">🏠 トップ</a><a href="ranking.html">👑 ランキング</a><a href="about.html">ℹ️ 運営者情報</a><a href="contact.html">✉️ お問い合わせ</a><a href="privacy.html">🔒 プライバシー</a></div></nav>
<div class="wrap"><p class="pr">PR: 当サイトはアフィリエイト広告を利用しています。掲載価格・在庫は取得時点のもので変更される場合があります。化粧品の効果には個人差があります。</p></div>
{body}
{ad_block("article")}
<footer><div class="wrap"><p>© {esc(SITE_NAME)} / 価格・レビューは毎日自動更新 (最終更新 {TODAY.isoformat()})</p>
<nav class="footnav"><a href="about.html">運営者情報</a><a href="privacy.html">プライバシーポリシー</a><a href="contact.html">お問い合わせ</a><a href="ranking.html">ランキング</a></nav>
<p>運営: {esc(CFG['site'].get('operator',''))} ／ {esc(CFG['site'].get('contact',''))}</p>
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
        els.append({"@type": "ListItem", "position": i, "url": f"{url}/product-{p['id']}.html", "name": display_name(p, 80)})
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": els}, ensure_ascii=False) + "</script>"

def detail(p, src_label, related, rank_in_cat=0, cat_total=0):
    price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先で確認"
    desc = excerpt(p.get("caption", ""))
    rank_line = f"「{esc(p.get('keyword',''))}」カテゴリで{rank_in_cat}位／{cat_total}商品中" if rank_in_cat else ""
    lk = p.get("links", {}).get("rakuten") or (p.get("url", "") if p.get("source") == "rakuten" else "")
    review_btn = f'<a class="btn r" href="{esc(lk)}" rel="nofollow sponsored noopener" target="_blank">楽天で口コミ・レビューを見る</a>' if lk else ""
    ld = {"@context": "https://schema.org", "@type": "Product", "name": display_name(p, 100),
          "image": p.get("image", ""), "description": (p.get("caption") or "")[:200],
          "offers": {"@type": "Offer", "priceCurrency": "JPY", "price": p.get("price", 0), "availability": "https://schema.org/InStock"}}
    try:
        ld["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": float(p.get("review_avg", 0) or 0), "reviewCount": int(p.get("review_count", 0) or 0)}
    except Exception:
        pass
    rel = "".join(card(r) for r in related[:4])
    body = f"""<div class="hero"><div class="wrap"><h1>{esc(display_name(p, 46))}</h1>
<p><span class="stars">{stars(p.get('review_avg'))}</span> {esc(p.get('review_avg',0))} ({esc(p.get('review_count',0))}件のレビュー) / {esc(price)}</p></div></div>
<div class="wrap"><p><a href="index.html">← トップへ</a> ｜ {esc(p.get('keyword',''))}</p>
<div class="detail"><div>{'<img src="'+esc(p['image'])+'" alt="'+esc(p['name'])+'">' if p.get('image') else ''}</div>
<div><p>販売店: {esc(p.get('shop',''))} (取扱: {esc(src_label)})</p>
<div class="cta">{btns(p)}<p class="note">ボタン先の最新価格・在庫・レビューをご確認ください</p></div></div></div>
<h2 class="sec">この商品について</h2>
<ul><li>{rank_line}</li><li>レビュー {esc(p.get('review_count',0))}件・評価★{esc(p.get('review_avg',0))}</li>
<li>参考価格 {esc(price)} / 販売店 {esc(p.get('shop',''))}</li></ul>
<div class="cta">{review_btn}<p class="note">良い評価・厳しい評価の内訳は、楽天のレビュー欄 (高評価順・低評価順に並替可) で確認できます</p></div>
<h2 class="sec">ショップによる商品説明</h2><p>{esc(desc) if desc else '商品説明はリンク先の販売ページでご確認ください。'}</p>
<p class="note">出典: 販売店の掲載文を自動引用 (薬機法に配慮し一部言い換えあり)</p>
<h2 class="sec">失敗しない選び方</h2>
<ul><li>{esc(cat_tip(p.get('keyword','')))}</li>
<li>肌質・成分表示を確認し、初めてはパッチテストを</li><li>レビューは件数と低評価理由の両方をチェック</li></ul>
<h2 class="sec">同じ悩みの人気商品</h2><div class="cards">{rel}</div></div>"""
    head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
    return page(f"{display_name(p, 44)}の口コミ・最安値 | {SITE_NAME}",
                f"{display_name(p, 80)}のレビュー・価格まとめ。{src_label}横断で比較。",
                body, head, f"{SITE_URL}/product-{p['id']}.html")

def cat_slug(kw):
    return re.sub(r"\s+", "-", kw.strip())[:30]

def main():
    f = DATA / "products.json"
    if not f.exists():
        print("[site] products.json が無い"); return
    products = json.loads(f.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    # 固定アセット (ロゴ等) をpublicへ複製 — 再生成で消えないように毎回コピー
    import shutil as _shutil
    _assets = BASE / "assets"
    if _assets.is_dir():
        for _a in sorted(_assets.iterdir()):
            if _a.is_file() and _a.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico"):
                _shutil.copyfile(_a, OUT / _a.name)
    top_n = CFG["site_gen"]["top_n"]
    src_label = detect_sources(products)
    print(f"[site] 取扱ソース: {src_label}")
    by_kw = {}
    for p in products:
        by_kw.setdefault(p.get("keyword", "その他"), []).append(p)

    chips = "".join(f'<a class="chip" href="cat-{i}.html">{esc(kw)} ({len(v)}件)</a>' for i, (kw, v) in enumerate(by_kw.items()))
    top = products[:top_n]
    hero = f"""<div class="hero"><div class="wrap">
<img class="logo" src="x-icon.jpg" alt="{esc(SITE_NAME)} X @mitekosu">
<h1>💄 {esc(SITE_NAME)}</h1>
<p>{esc(src_label)}の人気コスメをレビュー件数・評価・価格で自動比較</p>
<p>全{len(products)}商品掲載中・口コミ合計{sum(p.get('review_count',0) for p in products):,}件を集計</p>
<span class="date">📅 {YM}版・毎日6時自動更新</span><br>
<span style="font-size:.9em"><a class="xlink" href="https://x.com/mitekosu" rel="noopener" target="_blank">𝕏 @mitekosuをフォロー</a> ｜ 初めての方は <a href="about.html" style="color:#fff;font-weight:bold">サイトについて →</a></span></div></div>"""
    # 代り映え対策: 高評価プールから日替わりランダム表示 (日付シードで日中は固定)
    import random as _random
    drng = _random.Random(TODAY.isoformat())
    sg = CFG.get("site_gen", {})
    min_avg = float(sg.get("high_rating_min_avg", 4.0))
    min_cnt = int(sg.get("high_rating_min_count", 10))
    per_cat = int(sg.get("daily_pick_per_category", 5))
    top_pick_n = int(sg.get("daily_pick_top", 8))
    column_count = min(int(sg.get("editorial_columns", 8)), len(by_kw))
    column_links = "".join(
        f'<li><a href="articles/column-{i:02d}.html">{esc(kw)}の選び方</a></li>'
        for i, (kw, _) in enumerate(by_kw.items(), 1) if i <= column_count)

    def high_pick(items, n):
        high = [p for p in items if (p.get("review_avg", 0) or 0) >= min_avg and (p.get("review_count", 0) or 0) >= min_cnt]
        if len(high) >= n:
            return drng.sample(high, n)
        # 不足分はレビュー件数上位から補完 (重複なし)
        rest = [p for p in sorted(items, key=lambda x: -x.get("review_count", 0)) if p not in high]
        need = n - len(high)
        extra = drng.sample(rest, min(need, len(rest))) if rest else []
        combined = high + extra
        return drng.sample(combined, min(n, len(combined))) if len(combined) > n else combined

    all_high = high_pick(products, min(top_pick_n, len(products)))
    sections = []
    for i, (kw, v) in enumerate(by_kw.items()):
        picks = high_pick(v, min(per_cat, len(v)))
        sections.append(f"""<h2 class="sec">{esc(kw)} ピックアップ <a class="chip" href="cat-{i}.html">👑 ランキング・高評価ランダムを見る →</a></h2>
<p class="note">★{min_avg}以上・レビュー{min_cnt}件以上の高評価から日替わりで{len(picks)}件表示 (詳しくは <a href="about.html">サイトについて →</a>)</p>
<div class="cards">{''.join(card(p) for p in picks)}</div>""")
    index_body = hero + f"""<div class="wrap">
<section class="column-promo">
<h2>📝 特集コラム｜失敗しないコスメの選び方</h2>
<p class="lead">レビュー件数だけでは分からない、注目成分や肌質別の選び方を編集部がまとめました。</p>
<ul class="column-list">{column_links}</ul>
<p><a href="articles.html">→ すべての特集コラムを見る</a></p>
</section>
<h2 class="sec">悩み別に探す</h2><div class="chips">{chips}</div>
<h2 class="sec">✨ 今日の高評価ピックアップ (日替わり)</h2>
<p class="note">評価★{min_avg}以上の人気商品からランダム表示。毎日変わります。</p>
<div class="cards">{''.join(card(p) for p in all_high)}</div>
{''.join(sections)}
<p><a href="ranking.html">👑 総合ランキング・今日のピックアップはこちら →</a></p>
<p><a href="articles.html">📝 特集コラム（選び方・注目成分・FAQ）はこちら →</a></p>
<p><a href="about.html">ℹ️ サイトについて・運営者情報はこちら →</a></p>
<p><a href="contact.html">✉️ お問い合わせはこちら →</a></p></div>"""
    (OUT / "index.html").write_text(
        page(f"{SITE_NAME}｜{src_label}コスメの口コミ・価格比較【{YM}版】",
             f"{src_label}の人気コスメ{len(products)}商品をレビュー・価格で自動比較。毎日更新。",
             index_body, jsonld_itemlist(top, SITE_URL), f"{SITE_URL}/index.html"), encoding="utf-8")

    rank_sorted = sorted(products, key=lambda x: -x.get("review_count", 0))[:top_n]
    rank_pick = high_pick(products, min(8, len(products)))
    (OUT / "ranking.html").write_text(
        page(f"コスメ人気ランキング【{YM}版】レビュー件数順｜{SITE_NAME}",
             f"レビュー件数で集計したコスメランキングTOP{len(rank_sorted)}。{src_label}横断・毎日更新。",
             f"""<div class="hero"><div class="wrap"><h1>👑 コスメ人気ランキング</h1><p>レビュー件数順・{YM}版・毎日自動更新</p><p style="font-size:.9em"><a href="about.html" style="color:#fff">集計方法はサイトについて →</a></p></div></div>
<div class="wrap"><h2 class="sec">✨ 今日の高評価ランダム (日替わり)</h2><p class="note">★{min_avg}以上からランダムで表示。ランキング固定化による代り映えの無さを解消します。</p><div class="cards">{''.join(card(p) for p in rank_pick)}</div>
<h2 class="sec">👑 総合ランキング TOP{len(rank_sorted)}</h2><div class="cards">{''.join(card(p, i+1) for i, p in enumerate(rank_sorted))}</div>
<p><a href="articles.html">📝 特集コラム（選び方・注目成分・FAQ）はこちら →</a></p>
<p><a href="about.html">ℹ️ サイトについて・運営者情報はこちら →</a></p>
<p><a href="contact.html">✉️ お問い合わせはこちら →</a></p></div>""",
             jsonld_itemlist(rank_sorted, SITE_URL), f"{SITE_URL}/ranking.html"), encoding="utf-8")

    cat_files = []
    for i, (kw, v) in enumerate(by_kw.items()):
        v_sorted = sorted(v, key=lambda x: -x.get("review_count", 0))
        cat_pick = high_pick(v, min(5, len(v)))
        guide_html, faq_data = render_guide(kw)
        use_filter = bool(sg.get("filter_enabled", True))
        cat_body = f"""<div class="hero"><div class="wrap"><h1>{esc(kw)} おすすめ</h1>
<p>レビュー件数順・{len(v_sorted)}商品・{YM}版</p></div></div>
<div class="wrap">
<p class="crumb"><a href="index.html">トップ</a> ＞ {esc(kw)}</p>
{top3_table(v_sorted)}
<h2 class="sec">✨ 高評価ランダムピックアップ (日替わり)</h2>
<p class="note">★{min_avg}以上・レビュー{min_cnt}件以上から日替わりで表示</p>
<div class="cards">{''.join(card(p) for p in cat_pick)}</div>
<h2 class="sec">👑 {esc(kw)} ランキング全{len(v_sorted)}件</h2>
{filter_bar(len(v_sorted)) if use_filter else ''}
<div class="cards" id="cards">{''.join(card(p, j+1) for j, p in enumerate(v_sorted))}</div>
{FILTER_JS if use_filter else ''}
{guide_html if sg.get('guide_enabled', True) else ''}
<p><a href="index.html">← トップへ</a> ｜ <a href="ranking.html">総合ランキング →</a> ｜ <a href="contact.html">お問い合わせ →</a></p>
</div>"""
        cat_head = (jsonld_breadcrumb([("トップ", f"{SITE_URL}/index.html"), (kw, f"{SITE_URL}/cat-{i}.html")])
                    + jsonld_itemlist(v_sorted, SITE_URL)
                    + (jsonld_faq(faq_data) if sg.get('guide_enabled', True) else ""))
        (OUT / f"cat-{i}.html").write_text(
            page(f"{kw} おすすめ{len(v_sorted)}選【{YM}版】口コミ・価格比較｜{SITE_NAME}",
                 f"{kw}の人気商品をレビュー件数・評価・価格で比較。選び方ガイド・FAQ付き。{src_label}横断・毎日更新。",
                 cat_body, cat_head, f"{SITE_URL}/cat-{i}.html"), encoding="utf-8")
        cat_files.append(f"cat-{i}.html")

    for p in products:
        cat_all = sorted(by_kw.get(p.get("keyword", ""), []), key=lambda x: -x.get("review_count", 0))
        pos = next((j + 1 for j, r in enumerate(cat_all) if r["id"] == p["id"]), 0)
        related = [r for r in cat_all if r["id"] != p["id"]]
        (OUT / f"product-{p['id']}.html").write_text(detail(p, src_label, related, pos, len(cat_all)), encoding="utf-8")

    # 審査・信頼性用固定ページ
    # ===== 審査・信頼性用の固定ページ =====
    op = CFG["site"]
    contact_url = (op.get("contact_form_url") or "").strip()
    contact_email = (op.get("contact_email") or "").strip()

    privacy_body = f"""<div class="wrap"><h1>プライバシーポリシー</h1>
<p class="note">制定・最終改定: {TODAY.isoformat()} ／ 運営: {esc(op.get('operator',''))}</p>

<h2 class="sec">1. はじめに</h2>
<p>{esc(SITE_NAME)}（以下「当サイト」）は、広告収入により無料で運営されています。当サイトをご利用になる方（以下「ユーザー」）の個人情報がどのように扱われるかを、以下に説明します。当サイトを利用した時点で、本ポリシーに同意されたものとみなします。</p>

<h2 class="sec">2. 第三者配信広告（Google AdSense）について</h2>
<p>当サイトでは、Google LLCが提供する第三者配信型広告サービス「Google AdSense」を利用しています。広告配信事業者は、ユーザーの興味関心に沿った広告を表示するため、Cookie（クッキー）または類似の技術を使用して情報を収集することがあります。収集される情報には、閲覧したページ、閲覧日時、使用しているブラウザや端末の種類、大まかな地域情報などが含まれる場合がありますが、氏名・住所・メールアドレスなどの個人を直接特定する情報は含まれません。</p>
<p>Googleは、DoubleClickなどの配信プラットフォームを通じて、過去の閲覧履歴に基づく興味関心広告を配信することがあります。これを望まない場合は、<a href="https://www.google.com/settings/ads" rel="noopener" target="_blank">Googleの広告設定</a>からパーソナライズ広告を無効にできます。業界のオプトアウトについては <a href="https://www.aboutads.info/choices/" rel="noopener" target="_blank">aboutads.info</a> もご利用ください。Cookieをブラウザの設定から無効にすることも可能です。</p>
<p>広告の配信およびCookieの利用に関するGoogleの規約については、<a href="https://policies.google.com/technologies/ads" rel="noopener" target="_blank">Googleポリシーと規約</a>をご確認ください。</p>

<h2 class="sec">3. アフィリエイト広告について（PR表記）</h2>
<p>当サイトは、楽天アフィリエイトをはじめとするアフィリエイトプログラムに参加しています。商品リンクを経由して購入が行われた場合、販売店から当サイトに紹介料が支払われることがあります。これは一般消費者に対する表示の適正化に関する法律（いわゆるステマ規制）に従い、全ページおよび各SNS投稿に「PR」表記として明示しています。</p>
<p>掲載商品の選択および順位は、レビュー件数・評価・価格などの公開情報をもとに自動的に決定されており、広告主からの対価によって特定の商品を意図的に上位に表示することはしていません。価格・在庫・ポイント数は取得時点の情報であり、リンク先で最新情報をご確認ください。</p>

<h2 class="sec">4. アクセス解析ツールについて</h2>
<p>当サイトでは、サービス品質の改善および閲覧状況の把握のため、アクセス解析ツールを利用する場合があります。解析にはIPアドレスなどの情報が一時的に処理されますが、個人を特定する目的では使用せず、統計的なデータとして匿名で収集・保存します。ブラウザでCookieを無効にすることで、解析対象から外れることができます。今後 Google Analytics 等の解析サービスを導入する際は、本ポリシーを改定して事前にお知らせします。</p>

<h2 class="sec">5. 掲載情報の出典と免責事項</h2>
<p>商品情報は楽天市場API等の公開データをもとに自動取得しています。掲載内容の正確性には努めていますが、価格・在庫・仕様の変更や取得エラーによる誤差が生じる場合があります。掲載情報によって生じたいかなる損害についても、当サイトは責任を負いかねます。</p>
<p>化粧品の効果・効能には個人差があります。当サイトは断定的な効果をうたう表示を行っていません。肌に合わないと感じた場合は直ちに使用を中止し、必要に応じて専門医にご相談ください。</p>

<h2 class="sec">6. お問い合わせ</h2>
<p>個人情報の取り扱い、広告表示、掲載内容に関するご質問は、<a href="contact.html">お問い合わせページ</a>よりご連絡ください。返信には通常数日を要する場合があります。</p>

<h2 class="sec">7. プライバシーポリシーの改定</h2>
<p>法令の変更やサービス内容の更新に伴い、本ポリシーを改定することがあります。改定後の内容は、当ページに最新のものを掲載します。</p>
</div>"""
    (OUT / "privacy.html").write_text(page(
        f"プライバシーポリシー｜{SITE_NAME}",
        f"{SITE_NAME}のプライバシーポリシー。Google AdSenseの第三者配信広告・Cookie、アフィリエイトPR表記、アクセス解析、免責事項について。",
        privacy_body, jsonld_breadcrumb([("トップ", f"{SITE_URL}/index.html"), ("プライバシーポリシー", f"{SITE_URL}/privacy.html")]),
        f"{SITE_URL}/privacy.html"), encoding="utf-8")

    if contact_url:
        form_h = int(_num(op.get("contact_form_height"), 951) or 951)
        form = f"""<div class="formbox"><iframe src="{esc(contact_url)}" title="お問い合わせフォーム" height="{form_h}">このブラウザはiframeに対応していません。</iframe></div>
<p style="text-align:center;margin-top:10px"><a href="{esc(contact_url)}" rel="noopener" target="_blank">フォームが表示されない場合はこちらから入力 →</a></p>"""
    else:
        form = ("""<div class="formbox"><p>お問い合わせフォームを準備中です。お手数ですが、下記の連絡先よりご連絡ください。</p>"""
                + f"<p>X: <a href=\"https://x.com/mitekosu\" rel=\"noopener\" target=\"_blank\">@mitekosu にDM</a></p>"
                + (f"<p>メール: <a href=\"mailto:{esc(contact_email)}\">{esc(contact_email)}</a></p>" if contact_email else "")
                + "</div>")
    contact_body = f"""<div class="wrap"><h1>お問い合わせ</h1>
<p class="crumb"><a href="index.html">トップ</a> ＞ お問い合わせ</p>
<p>{esc(SITE_NAME)}へのご質問、ご指摘、掲載内容の修正依頼などはこちらからご連絡ください。個人情報の取り扱いは <a href="privacy.html">プライバシーポリシー</a> に従います。</p>
{form}
<h2 class="sec">お問い合わせにあたって</h2>
<ul><li>商品の価格・在庫に関するお問い合わせは、各リンク先の販売店へお願いします。</li>
<li>効果・効能に関するご相談は、医療機関または専門家へご相談ください。</li>
<li>返信は内容確認の上、数日以内に行うよう努めています。</li></ul>
<p><a href="index.html">← トップへ戻る</a></p>
</div>"""
    (OUT / "contact.html").write_text(page(
        f"お問い合わせ｜{SITE_NAME}",
        f"{esc(SITE_NAME)}へのお問い合わせフォーム。ご質問・ご指摘はこちらから。",
        contact_body,
        jsonld_breadcrumb([("トップ", f"{SITE_URL}/index.html"), ("お問い合わせ", f"{SITE_URL}/contact.html")]),
        f"{SITE_URL}/contact.html"), encoding="utf-8")

    (OUT / "about.html").write_text(page(
        f"サイトについて・運営者情報｜{SITE_NAME}",
        f"{SITE_NAME}のサイト概要・運営者情報。お問い合わせはサイト内のフォームから。",
        f"""<div class="wrap"><h1>サイトについて</h1>
<p>{esc(SITE_NAME)}は、{esc(src_label)}の人気コスメをレビュー件数・評価・価格で自動比較するサイトです。毎日6時に自動更新しています。</p>
<h2 class="sec">選定・表示方法</h2>
<ul><li>楽天市場API等から取得し、レビュー件数と評価を基準に掲載</li>
<li>カテゴリページでは「目的別おすすめTOP3」「絞り込み・並び替え」「選び方ガイド・FAQ」を併載</li>
<li>レビュー件数・評価・価格から自動でバッジを付与し、比較しやすく表示</li>
<li>商品名は販促文言を自動除去し、ブランド名・商品名を優先して表示</li></ul>
<h2 class="sec">編集方針</h2>
<p>ランキングは公開されているレビュー件数・評価にもとづく自動集計です。広告主からの対価で順位を操作することはありません。化粧品の効果には個人差があるため、断定的な表現は使用していません。</p>
<h2 class="sec">運営者情報・お問い合わせ</h2>
<p>サイト名: {esc(SITE_NAME)} / 運営: {esc(op.get('operator', ''))}</p>
<p>連絡先: <a href="contact.html">お問い合わせページ（サイト内フォーム）→</a></p>
<p>従来の X（@mitekosu）DM に加え、サイト内のお問い合わせフォームからもご連絡いただけます。</p>
<p><a href="index.html">← トップへ戻る</a></p></div>""",
        jsonld_breadcrumb([("トップ", f"{SITE_URL}/index.html"), ("サイトについて", f"{SITE_URL}/about.html")]),
        f"{SITE_URL}/about.html"), encoding="utf-8")

    # ===== 編集部コラム (独自コンテンツ。商品一覧とは別ディレクトリに固定ページとして保存) =====
    art_dir = OUT / "articles"
    art_dir.mkdir(parents=True, exist_ok=True)
    col_count = min(int(sg.get("editorial_columns", 8)), len(cat_files))
    editorial_files = []
    for idx, ((kw, v), catfile) in enumerate(zip(by_kw.items(), cat_files), 1):
        if idx > col_count:
            break
        g = guide_for(kw)
        tips = "".join(f"<li><strong>{esc(t)}</strong>：{esc(d)}</li>" for t, d in g["tips"])
        ing = "".join(f"<li><strong>{esc(t)}</strong>：{esc(d)}</li>" for t, d in g["ingredients"])
        types = "".join(f"<li><strong>{esc(t)}</strong>：{esc(d)}</li>" for t, d in g["types"])
        faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in g["faq"])
        col_body = f"""<div class="hero"><div class="wrap"><h1>{esc(kw)}の選び方</h1>
<p>編集部ガイド・{YM}版 / 失敗しないための比較ポイント</p></div></div>
<div class="wrap"><p class="crumb"><a href="index.html">トップ</a> ＞ <a href="articles.html">特集コラム</a> ＞ {esc(kw)}の選び方</p>
<section class="guide"><p class="lead">{esc(g['lead'])}</p>
<h3>選び方の3原則</h3><ol>{tips}</ol>
<h3>注目成分の解説</h3><ul>{ing}</ul>
<h3>肌質・悩み別のおすすめタイプ診断</h3><ul>{types}</ul>
<h3>よくある質問</h3><div class="faq">{faq}</div></section>
<h2 class="sec">実際の商品を比較する</h2>
<p>この記事の考え方をもとに、{esc(kw)}の人気商品をレビュー件数・評価・価格で比較しています。</p>
<div class="cards">{''.join(card(p) for p in sorted(v, key=lambda x: -x.get('review_count', 0))[:4])}</div>
<p><a href="{catfile}">→ {esc(kw)}のランキング・全商品を見る</a></p>
<p class="note">PR: 当サイトはアフィリエイト広告を利用しています。化粧品の効果には個人差があります。</p>
</div>"""
        col_path = f"articles/column-{idx:02d}.html"
        col_head = (jsonld_breadcrumb([("トップ", f"{SITE_URL}/index.html"),
                                       ("特集コラム", f"{SITE_URL}/articles.html"),
                                       (f"{kw}の選び方", f"{SITE_URL}/{col_path}")])
                    + jsonld_faq(g["faq"]))
        (OUT / col_path).write_text(page(
            f"{kw}の選び方 | 失敗しない比較ポイント｜{SITE_NAME}",
            f"{kw}を選ぶときの失敗しないポイントを、成分・肌質別・FAQつきで解説。",
            col_body, col_head, f"{SITE_URL}/{col_path}"), encoding="utf-8")
        editorial_files.append(col_path)

    # コラム一覧ページ
    col_links = "".join(
        f'<li><a href="{u}">{esc(list(by_kw.items())[i][0])}の選び方｜失敗しない比較ポイント</a></li>'
        for i, u in enumerate(editorial_files))
    (OUT / "articles.html").write_text(page(
        f"特集コラム｜{SITE_NAME}",
        f"{SITE_NAME}の編集部コラム一覧。コスメの選び方・注目成分・肌質別診断を解説。",
        f"""<div class="hero"><div class="wrap"><h1>📝 特集コラム</h1><p>編集部がまとめたコスメの選び方ガイド</p></div></div>
<div class="wrap"><p class="crumb"><a href="index.html">トップ</a> ＞ 特集コラム</p>
<p>商品の自動比較だけでなく、選び方の考え方・注目成分・肌質別の診断をまとめた編集部コンテンツです。</p>
<ul>{col_links}</ul>
<p><a href="index.html">← トップへ戻る</a></p></div>""",
        jsonld_breadcrumb([("トップ", f"{SITE_URL}/index.html"), ("特集コラム", f"{SITE_URL}/articles.html")]),
        f"{SITE_URL}/articles.html"), encoding="utf-8")

    urls = (["index.html", "ranking.html", "articles.html", "contact.html", "privacy.html", "about.html"]
            + cat_files + editorial_files + [f"product-{p['id']}.html" for p in products])
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in urls:
        sm += f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>"
    sm += "</urlset>"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    rss = f'<?xml version="1.0"?><rss version="2.0"><channel><title>{esc(SITE_NAME)}</title><link>{SITE_URL}</link><description>{esc(src_label)}コスメ毎日更新</description>'
    for p in top[:20]:
        rss += f"<item><title>{esc(display_name(p, 80))}</title><link>{SITE_URL}/product-{p['id']}.html</link><description>{esc(p.get('keyword',''))}</description></item>"
    rss += "</channel></rss>"
    (OUT / "rss.xml").write_text(rss, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    # AdSense: ads.txt (再生成で消えないよう毎回出力。client未設定なら何もしない)
    _client = (CFG.get("ads", {}) or {}).get("adsense_client", "")
    _m = re.search(r"pub-\d+", _client or "")
    if _m:
        (OUT / "ads.txt").write_text(f"google.com, {_m.group(0)}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    print(f"[site] 生成完了: {len(products)}商品 + カテゴリ{len(cat_files)}頁 -> {OUT}")

if __name__ == "__main__":
    main()
