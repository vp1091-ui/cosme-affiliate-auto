# コスメ自動アフィリ (月0〜1000円 / SNSまで全自動)

`C:\Users\DELL\Documents\Opencode\cosme-affiliate-auto` に作成済み。

## 0. 全体像 (低コスト構成)
- 商品データ: 楽天市場API (無料) + Amazon PA-API (無料、無くても検索リンクで代替)
- サイト生成: Python静的HTML → `public/` (サーバー代0円)
- ホスティング: Cloudflare Pages / Vercel / GitHub Pages のいずれか無料枠
- 自動更新: GitHub Actions cron 毎日6時 (無料) → `public/` を自動commit→ホスティングが自動再デプロイ
- ドメインのみ実費: 年1000円前後 (.com/.jpはCloudflare Registrarが安い) → 月1000円以内に収まる
- SNS: `data/sns_queue/*.txt` を自動生成 → Gmailにコピペ用原稿を送信 → 手動でXに投稿 (アフィリ7件＋日常つぶやき2件/日)

## 1. 初期取得 (ID取得: 0円)
1. 楽天Web Service: https://webservice.rakuten.co.jp/ でアプリID発行 → アフィリエイトIDは楽天アフィリエイトで取得しリンク連携
2. Amazonアソシエイト: https://affiliate.amazon.co.jp/ 登録 → 180日以内に3件売上が必要。未達だとPA-APIが停止するので最初は「検索リンク代替」で運用可 (本ツールは対応済み)
3. X Developer (任意): FreeプランでOAuth1.0aキー取得。無くても手動運用可
4. `.env.example` を `.env` にコピーして記入。PowerShell例:
```powershell
Copy-Item .env.example .env
notepad .env
```

## 2. ローカル実行
```powershell
cd C:\Users\DELL\Documents\Opencode\cosme-affiliate-auto
py -m pip install -r requirements.txt
# .envを読み込んで実行 (手動で環境変数設定するか、$env:RAKUTEN_APP_ID="xxx" のように設定)
py src/run_all.py
# public/index.html をブラウザで開いて確認
```
キー無しでも空振りせず、雛形HTML・SNS原稿フォルダが作られる。キー設定後に本データが入る。

## 3. GitHub + 自動化
1. GitHubで空リポジトリ作成 → このフォルダをpush
2. Repo Settings > Secrets > Actions に `RAKUTEN_APP_ID` 等を登録
3. `.github/workflows/daily.yml` が毎日自動実行。Actionsログで確認
4. Cloudflare Pages: https://pages.cloudflare.com/ で「Gitリポジトリからデプロイ」→ ビルド出力 `public` を指定。独自ドメインを接続

## 4. 収益化のコツ
- 楽天料率: コスメ 2〜4%前後。Amazon 2〜3%。単価3000円×100件/月で約6000〜12000円が目安
- 最初は `config.yaml` の8キーワードを上位表示狙いのロングテールに絞る (例: 化粧水 敏感肌 プチプラ)
- 記事Markdownは `public/articles/` に生成。はてな/WordPressに流用可
- 必ず全頁に「PR表記」あり (本ツールは自動挿入済み)。薬機法NG (治る・消える・痩せる等) は自動除去済み

## 5. よくある落とし穴
- Amazon PA-APIが403/429: 売上条件未達か申請直後。検索リンク代替で継続し、ROOM・楽天中心で3件作ってから再申請
- 楽天API 429: `hits_per_keyword` を30→10に下げ、`config.yaml` キーワードを減らす
- X自動投稿されない: Freeプランは月1500件・App-onlyでは投稿不可。OAuth1.0a4種必須。無ければ `data/sns_queue` 手動投稿でOK
- 検索流入が無い: sitemapをSearch Console登録、RSSをPinterest・ROOMに連携

## 6. SNS原稿の中身 (毎朝メールで届くもの)
`sns/YYYY-MM-DD.md` がメール本文として届きます。コピペ用の ``` ブロックごとに1投稿です。

- **■ アフィリエイト投稿 (7件/目安)**: PR表記・アフィリリンクあり
  - 商品は **全200件** を候補に、カテゴリを1件ずつ順番に回すため、同じカテゴリが一日に集中しません
  - 直近 `affiliate_history_days` (既定10日) に投稿した商品は除外。除外で足りない時だけ補充します
  - カテゴリ内はレビュー上位70%を中心に、20%の確率で下位からも拾うので固定化しません
- **■ 日常つぶやき (2件/目安 12:45・22:30)**: PR表記も商品リンクもない、普通のつぶやき
  - 24種類のテンプレートから日付シードで選択。直近10日で使ったものは出ません
  - 最後の `<!-- chat_ids: ... -->` は次回の重複回避用の履歴なので消さないでください (`sns/` はGitHubにcommitされます)

設定は `config.yaml` の `sns:` セクション (`max_posts_per_day` / `chat_posts_per_day` / `affiliate_history_days` など) で変更できます。

## 7. AdSense審査・収益化対応 (2026-11-26 追加)
- **必須ページ**: `privacy.html`（AdSense/Cookie・PR表記・免責・解析）/ `contact.html`（Googleフォーム埋め込み）/ `about.html`（運営者情報）を自動生成。フッターから全ページへ1クリックで遷移
  - Googleフォームを使う場合は `config.yaml` の `site.contact_form_url` に**埋め込み用URL**を設定（未設定時はX DM用の案内を表示）
- **独自コンテンツ**: 各カテゴリページに「選び方ガイド / 注目成分 / 肌質別診断 / FAQ」を約1,500文字追加。さらに `public/articles/column-01〜08.html` と一覧 `articles.html` を生成
- **比較しやすさ**: カテゴリ最上部に目的別TOP3比較表、価格帯フィルター・並び替えJS、レビュー数/評価/価格の自動バッジを追加
- **商品名整形**: `src/content.py` の `clean_product_name()` が【期間限定】【送料無料】【★P10倍】等を除去（サイト・SNS・構造化データで共通利用）
- **SEO**: 全ページに canonical、カテゴリ/コラムに BreadcrumbList・FAQPage・ItemList の JSON-LD を出力
- **リダイレクト**: ホスト単位の www/http → https は Cloudflare ダッシュボードの Redirect Rules で設定（手順は `URL_CANONICAL.md`）

## ファイル一覧
- src/fetch_rakuten.py: 楽天検索+ランキング
- src/fetch_amazon.py: PA-API + フォールバック検索リンク
- src/merge_products.py: 名寄せ・価格比較
- src/generate_site.py: 静的HTML/sitemap/rss + 必須ページ/独自コンテンツ/構造化データ
- src/content.py: 商品名整形 + カテゴリ別ガイド/FAQ/コラムデータ
- src/generate_posts.py: 記事雛形 + SNS原稿 (アフィリのバリエーション化 + 日常つぶやき生成)
- src/post_sns.py: X自動投稿 (任意)
- src/run_all.py: 一括実行
