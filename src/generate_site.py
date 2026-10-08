"""products.json から静的HTML (トップ/ランキング/商品詳細/sitemap/rss) を生成。
薬機法・ステマ規制対応: 効果断定を避け、PR表記を全頁に入れる。"""
import json, html, pathlib, datetime, urllib.parse
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
SITE_URL = __import__("os").getenv("SITE_URL", CFG["site"]["url"]).rstrip("/")
SITE_NAME = __import__("os").getenv("SITE_NAME", CFG["site"]["name"])

CSS = """body{font-family:sans-serif;max-width:900px;margin:0 auto;padding:16px;line-height:1.7;color:#333}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.card{border:1px solid #eee;border-radius:12px;padding:12px}
.card img{width:100%;height:180px;object-fit:contain;background:#fafafa}
.btn{display:inline-block;padding:8px 12px;border-radius:8px;text-decoration:none;margin:4px 4px 0 0}
.r{background:#bf0000;color:#fff}.a{background:#ff9900;color:#111}
.note{font-size:.85em;color:#666}.pr{font-size:.8em;background:#fff8e1;padding:8px;border-radius:8px}
header nav a{margin-right:12px}"""

HEADER = """<header><nav><a href="index.html">トップ</a> <a href="ranking.html">ランキング</a></nav>
<p class="pr">PR: 当サイトはアフィリエイト広告を利用しています。掲載価格・在庫は取得時点のもので、変更される場合があります。化粧品の効果には個人差があります。</p></header>"""

def esc(s): return html.escape(str(s or ""))

def btns(p):
    b = ""
    if p.get("links", {}).get("rakuten"):
        b += f'<a class="btn r" href="{esc(p["links"]["rakuten"])}" rel="nofollow sponsored noopener" target="_blank">楽天で見る</a>'
    elif p.get("url") and p.get("source") == "rakuten":
        b += f'<a class="btn r" href="{esc(p["url"])}" rel="nofollow sponsored noopener" target="_blank">楽天で見る</a>'
    if p.get("links", {}).get("amazon"):
        b += f'<a class="btn a" href="{esc(p["links"]["amazon"])}" rel="nofollow sponsored noopener" target="_blank">Amazonで見る</a>'
    return b

def card(p):
    img = f'<img src="{esc(p.get("image",""))}" alt="{esc(p.get("name",""))}" loading="lazy">' if p.get("image") else ""
    price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先で確認"
    return f"""<div class="card">{img}<h3><a href="product-{p['id']}.html">{esc(p['name'][:60])}</a></h3>
<p>★{esc(p.get('review_avg',0))} ({esc(p.get('review_count',0))}件) / {esc(price)}</p>
<p class="note">{esc((p.get('keyword','')))} / {esc(p.get('shop',''))}</p>{btns(p)}</div>"""

def page(title, body):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | {esc(SITE_NAME)}</title>
<meta name="description" content="{esc(CFG['site']['description'])}">
<style>{CSS}</style></head><body>{HEADER}<h1>{esc(title)}</h1>{body}
<footer><p class="note">© {esc(SITE_NAME)} / 価格・レビューは毎日自動更新 / お問い合わせはサイト運営者まで</p></footer></body></html>"""

def detail(p):
    price = f'{p["price"]:,}円' if p.get("price") else "価格はリンク先で確認"
    # 薬機法配慮: 断定的効果表現を避けた定型文
    body = f"""<p><a href="index.html">← トップへ</a></p>
{'<img src="'+esc(p['image'])+'" style="max-width:320px">' if p.get('image') else ''}
<p>キーワード: {esc(p.get('keyword',''))} / ショップ: {esc(p.get('shop',''))}</p>
<p>参考価格: {esc(price)} / レビュー★{esc(p.get('review_avg',0))} ({esc(p.get('review_count',0))}件)</p>
{btns(p)}
<h2>選び方のポイント</h2>
<ul><li>肌質・成分表示を確認し、パッチテストを推奨します</li>
<li>レビュー件数と低評価内容の両方を確認しましょう</li>
<li>価格だけでなく容量・使用量目安でコスパ比較しましょう</li></ul>
<h2>口コミ傾向</h2><p class="note">{esc((p.get('caption') or 'レビュー情報をもとに自動集計しています。')[:300])}</p>"""
    return page(p["name"][:60], body)

def main():
    f = DATA / "products.json"
    if not f.exists():
        print("[site] products.json が無い。先に run_all の取得系を実行");
        return
    products = json.loads(f.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    top_n = CFG["site_gen"]["top_n"]
    top = products[:top_n]

    (OUT / "index.html").write_text(page("人気コスメ自動比較トップ",
        f"<p>{esc(CFG['site']['description'])} 毎日6時自動更新。</p><div class='cards'>{''.join(card(p) for p in top)}</div>"), encoding="utf-8")
    rank_sorted = sorted(products, key=lambda x: (x.get("rank", 99), -x.get("review_count", 0)))[:top_n]
    (OUT / "ranking.html").write_text(page("楽天コスメランキング連動",
        f"<div class='cards'>{''.join(card(p) for p in rank_sorted)}</div>"), encoding="utf-8")
    for p in products:
        (OUT / f"product-{p['id']}.html").write_text(detail(p), encoding="utf-8")

    today = datetime.date.today().isoformat()
    urls = ["index.html", "ranking.html"] + [f"product-{p['id']}.html" for p in products]
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in urls:
        sm += f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{today}</lastmod></url>"
    sm += "</urlset>"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    rss = f'<?xml version="1.0"?><rss version="2.0"><channel><title>{esc(SITE_NAME)}</title><link>{SITE_URL}</link><description>毎日更新コスメ比較</description>'
    for p in top[:20]:
        rss += f"<item><title>{esc(p['name'][:80])}</title><link>{SITE_URL}/product-{p['id']}.html</link><description>{esc(p.get('keyword',''))}</description></item>"
    rss += "</channel></rss>"
    (OUT / "rss.xml").write_text(rss, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"[site] 生成完了: {len(products)}商品 -> {OUT}")

if __name__ == "__main__":
    main()
