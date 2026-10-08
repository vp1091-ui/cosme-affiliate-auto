# コスメ自動アフィリ (月0〜1000円 / SNSまで全自動)

`C:\Users\DELL\Documents\Opencode\cosme-affiliate-auto` に作成済み。

## 0. 全体像 (低コスト構成)
- 商品データ: 楽天市場API (無料) + Amazon PA-API (無料、無くても検索リンクで代替)
- サイト生成: Python静的HTML → `public/` (サーバー代0円)
- ホスティング: Cloudflare Pages / Vercel / GitHub Pages のいずれか無料枠
- 自動更新: GitHub Actions cron 毎日6時 (無料) → `public/` を自動commit→ホスティングが自動再デプロイ
- ドメインのみ実費: 年1000円前後 (.com/.jpはCloudflare Registrarが安い) → 月1000円以内に収まる
- SNS: `data/sns_queue/*.txt` を自動生成 → Xキーあれば自動投稿、無ければコピペでROOM/Instagram/Pinterestに転用

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

## ファイル一覧
- src/fetch_rakuten.py: 楽天検索+ランキング
- src/fetch_amazon.py: PA-API + フォールバック検索リンク
- src/merge_products.py: 名寄せ・価格比較
- src/generate_site.py: 静的HTML/sitemap/rss
- src/generate_posts.py: 記事雛形 + SNS原稿
- src/post_sns.py: X自動投稿 (任意)
- src/run_all.py: 一括実行
