# URL正規化（www / http の混在防止）設定手順

## 正規URLのルール（2026-11-27 統一）

**正規形: `https://mitekosu.com/...`（wwwなし・`.html`なし）**

`generate_site.py` の `canonical_url()` が全ページの canonical / og:url / 構造化データ / sitemap / RSS をこの形に統一します。

```html
<link rel="canonical" href="https://mitekosu.com/cat-0">
```

内部リンクも `pretty_links()` で `.html` を除去し、`index.html` は `/` に統一しています。  
ホスティング側で `.html` → 拡張子なし の301が既に効いているため、その形式に合わせています。

`config.yaml` の `site.url` を変更すれば、全ページの canonical / og:url / sitemap に反映されます。

### www からのリダイレクト（未設定なら設定してください）

`https://www.mitekosu.com/` は現在200を返すため、以下の Redirect Rule を追加してください。

- Rules → Redirect Rules → Create rule
- When: `Hostname` `equals` `www.mitekosu.com`
- Then: `Redirect` / `301` / `https://mitekosu.com%{uri}`

加えて、サーバー側で 301 リダイレクトを設定してください。以下は環境別の手順です。

---

## 1. Cloudflare Pages（この構成）

**注意**: Pages の `_redirects` は「左側に相対パス」しか書けません。  
`https://www.mitekosu.com/* ...` のようなホスト名付きの書き方はビルドが失敗します（エラー例: `Only relative URLs are allowed` / `Valid status codes are ... Got 0`）。  
そのため `public/_redirects` は削除済みです。**ホスト単位のリダイレクトはダッシュボードの Redirect Rules で設定してください。**

### Cloudflare ダッシュボードでの設定

1. https://dash.cloudflare.com → `mitekosu.com` のゾーンを開く
2. **Rules → Redirect Rules → Create rule**
3. Rule name: `www to apex`
   - When: `Hostname` `equals` `www.mitekosu.com`
   - Then: `Redirect` / `301` / `https://mitekosu.com%{uri}`
4. もう1つ作成: Rule name: `http to https`
   - When: `SSL` `is off`
   - Then: `Redirect` / `301` / `https://mitekosu.com%{uri}`
5. DNS で `www` と apex（`mitekosu.com`）の両方を Cloudflare に向けておく

Pages の `_redirects` で書けるのは `/old.html /new.html 301` のような**サイト内パスのみ**です。

---

## 2. Cloudflare を CDN として使っている場合（他のサーバーが origin）

**Rules → Redirect Rules → Create rule**

- Rule name: `www to apex`
- When incoming requests match: `Hostname` `equals` `www.mitekosu.com`
- Then: `Redirect` / `301` / `https://mitekosu.com{{uri}}`
- さらに `SSL` が `Off` のリクエストも `https://mitekosu.com{{uri}}` へ 301 する別ルールを追加

---

## 3. Apache（.htaccess）を使う場合

ドキュメントルートの `.htaccess` に以下を追加します。

```apache
RewriteEngine On

# http -> https
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://mitekosu.com/$1 [R=301,L]

# www -> apex
RewriteCond %{HTTP_HOST} ^www\.mitekosu\.com$ [NC]
RewriteRule ^(.*)$ https://mitekosu.com/$1 [R=301,L]
```

WordPress 等と併用する場合は既存のルールより上に置いてください。

---

## 4. Nginx を使う場合

```nginx
server {
    listen 80;
    server_name www.mitekosu.com mitekosu.com;
    return 301 https://mitekosu.com$request_uri;
}
server {
    listen 443 ssl;
    server_name www.mitekosu.com;
    return 301 https://mitekosu.com$request_uri;
}
```

---

## 確認方法

```powershell
curl -I https://www.mitekosu.com/
```

`HTTP/2 301` と `location: https://mitekosu.com/` が返ればOKです。
Search Console で「ドメインの変更」または「アドレス変更」を設定し、任意のURLを `https://mitekosu.com/` に指定してください。
