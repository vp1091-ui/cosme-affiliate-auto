# URLの統一（わかりやす版）

## 結論：あなたがやることは1つだけ

**Cloudflareの管理画面で「wwwを付けたURLを、wwwなしのURLへ飛ばす」ルールを1つ追加するだけです。**

それ以外（canonicalタグ・内部リンク・sitemap・`.html`なし化）は、すべてコード側で自動対応済みなので、何もしなくて大丈夫です。

---

## なぜ必要なの？

同じページが複数のURLで見えると、Googleが「どれが本物か」判断できず、検索評価が分散します。

| 見え方 | 今の状態 | 本物にするURL |
|---|---|---|
| `https://mitekosu.com/` | ✅ 本物 | これ |
| `https://www.mitekosu.com/` | ⚠️ 別URLとして見える | ↑へ飛ばす |
| `https://mitekosu.com/product-56.html` | ⚠️ 自動で飛ぶ | `https://mitekosu.com/product-56` |
| `https://mitekosu.com/product-56` | ✅ 本物 | これ |

**本物にする形： `https://mitekosu.com/...`（wwwなし・`.html`なし）**

---

## すでに自動でやっていること（作業不要）

`generate_site.py` が毎朝の更新時に、以下を全部この形に統一しています：

- 各ページの `<link rel="canonical" href="https://mitekosu.com/...">`
- `og:url`（SNSでシェアされるときのURL）
- ページ内のリンク（`product-56.html` → `product-56`）
- `sitemap.xml` と `rss.xml`
- 構造化データ（JSON-LD）の中のURL

さらに、Cloudflare Pagesが `.html` 付きURLを自動で `.html` なしへ301リダイレクトしてくれます。  
（例：`/product-56.html` を開くと `/product-56` に飛ぶ。確認済み）

👉 つまり **canonical・内部リンク・sitemap・`.html`の問題は解決済み** です。

---

## 残っている作業：www → wwwなし のリダイレクト

### 手順（Cloudflare 日本語画面）

1. **https://dash.cloudflare.com** にログイン
2. トップのドメイン一覧から **`mitekosu.com`** をクリック
3. 左のメニューから **「ルール」** → **「リダイレクトルール」** をクリック
4. **「ルールを作成」** ボタンを押す
5. 以下を入力します

| 項目 | 入力する内容 |
|---|---|
| ルール名 | `wwwなしへリダイレクト` |
| 「リクエストが一致した場合」 | **ホスト名** / **次と等しい** / `www.mitekosu.com` |
| 「その後」 | **リダイレクト** / **301（永続的）** / `https://mitekosu.com%{uri}` |

※ URLの最後 `%{uri}` は、入力欄の右にある「変数を挿入」から **uri** を選ぶと自動で入ります。  
　手入力でも `https://mitekosu.com%{uri}` でOKです（`{{uri}}` と表示される場合も同じ意味です）。

6. **「保存してデプロイ」** を押す
7. 数十秒待って、ブラウザで **`https://www.mitekosu.com/`** を開く  
　→ アドレスバーが **`https://mitekosu.com/`** に変われば完了です

### うまくいかないとき

- **DNSの設定を確認**：「DNS」→「レコード」で `www` のレコードが **プロキシ済み（オレンジ色の雲）** になっているか確認してください。グレー（DNSのみ）だとCloudflareのルールが働きません。
- ブラウザのキャッシュが効いている場合は、Ctrl+F5 でハードリロードしてみてください。

---

## おまけ：http → https も設定したい場合

同じ「リダイレクトルール」画面でもう1つ追加します。

| 項目 | 入力する内容 |
|---|---|
| ルール名 | `httpをhttpsへ` |
| 「リクエストが一致した場合」 | **SSL** / **オフ** |
| 「その後」 | **リダイレクト** / **301** / `https://mitekosu.com%{uri}` |

---

## `public/_redirects` は使わないでください

以前、このファイルに `https://www.mitekosu.com/* ...` と書いたところ、Cloudflare Pagesのビルドが失敗しました。

エラー例：
```
Invalid _redirects configuration:
Only relative URLs are allowed.
```

`_redirects` には **サイト内のパス（`/old` → `/new` のような形）しか書けません**。  
ホスト名（`www` の有無）や `http/https` の切り替えは、上の **ダッシュボードのリダイレクトルール** で設定してください。このファイルは既に削除済みです。

---

## 確認コマンド（任意）

PowerShellで確認する場合：

```powershell
curl.exe -I https://www.mitekosu.com/
```

`HTTP/1.1 301` と `Location: https://mitekosu.com/` が返ればOKです。

Search Consoleを使っている場合は、「設定」→「アドレス変更」で新しいURLを `https://mitekosu.com/` に指定しておくと、Googleへの伝達が早くなります。
