# 楽天だけ開始手順書 (アプリID発行→表示まで)

この通り実行すれば開始できる。所要30〜60分。費用0円。

## STEP 0. 前提
- 楽天会員 (通常の買い物アカウントでOK)
- Windows + Pythonあり。このフォルダ: `cosme-affiliate-auto/`

## STEP 1. 楽天アフィリエイト登録 (5分)
1. https://affiliate.rakuten.co.jp/ を開く → 楽天会員でログイン
2. 新規登録・規約同意 → サイト情報登録
   - サイト名: `コスメ自動比較ナビ` (仮でOK、後で変更可)
   - URL: 持っていなければ `https://example.com` で仮登録 → Pages公開後に修正
3. 登録完了を確認

## STEP 2. アプリID発行 (5分) ★ここが開始点
1. https://webservice.rakuten.co.jp/ を開く → 楽天会員でログイン
2. 「アプリID発行」をクリック → 新規アプリ作成し、下記で入力
   - アプリ名: `cosme-auto` (何でもOK)
   - アプリケーションURL: アフィリエイトに登録したURLと同じ実在URL (例: Pages仮ドメイン `xxx.pages.dev` や保有ブログ。スキームなし `example.com` 形式で通る場合あり)。`https://example.com` は予約ドメインで登録不可のため使わない
   - アプリケーションタイプ: `Webアプリケーション` (選択肢にあればWebサービス/Webサイトも可。スマホアプリは選ばない)
   - 許可されたWebサイト: 上と同じ実在URLを1件のみ (APIを動かす公開サイトの意味。`src/fetch_rakuten.py:24` はこのURLをRefererとして送るので、`.env` の `SITE_URL` と一致させること)
   - ※エラー `更新されたWebサイトリストに登録されているWebサイトからのみ` が出たら: example.comが原因。アフィリエイト登録済みの実在URLに入れ直す。未保有なら先にPages仮ドメインか無料ブログURLを用意する
   - 注意: 保存時に「APIリクエストは、更新されたWebサイトリストに登録されているWebサイトからのみ受け付けます」と出たら、①URLの表記ゆれを確認 (httpsあり・末尾スラッシュなし・wwwなしで統一)、②いったん保存→数分待って再読込。ツール側は `SITE_URL` をRefererとして送るよう修正済み (`src/fetch_rakuten.py:23`) ので、`.env` の `SITE_URL` と登録URLを一致させればPython/GitHub Actionsからも許可される
   - 認証: 不要 / 概略: 自分のサイト用
   - データ利用目的 (コピペ用):
     `自身が運営するコスメ比較サイト(https://example.com)において、楽天市場APIで取得した商品名・価格・レビュー件数/評価・画像URL・商品URL(アフィリエイトリンク)を用いて比較・ランキング表示を行うため。取得は1日1回の定期実行のみ。取得データの第三者提供・再頒布は行わない。`
   - 予想QPS: `1` (8キーワード+ランキングを1日1回順次取得、1秒間隔。常時アクセスなし)
3. 発行された `アプリケーションID (appId)` をコピー
   - 例: `10xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - これが `RAKUTEN_APP_ID`

## STEP 3. アフィリエイトID確認 (5分)
1. https://affiliate.rakuten.co.jp/ にログイン
2. 右上アカウント or 設定 → `アフィリエイトID` をコピー
   - 形式例: `2bxxxxxx.xxxxxxxx` のようにドット入り
   - 不明な場合: アフィリエイト画面で商品リンク作成 → 生成URL内の `?pc=...&m=...` ではなく `affiliateId` パラメータに使うID。管理画面ヘルプで「アフィリエイトID」と検索
3. これが `RAKUTEN_AFFILIATE_ID`
   - 未設定でも商品取得は動くが、収益にならない (通常リンクになる)。必ず設定すること

## STEP 4. .env 設定 (3分)
PowerShellで実行:
```powershell
cd C:\Users\DELL\Documents\Opencode\cosme-affiliate-auto
Copy-Item .env.example .env
notepad .env
```
`.env` をこう編集 (2行だけ):
```
RAKUTEN_APP_ID=ここにSTEP2のIDを貼る
RAKUTEN_AFFILIATE_ID=ここにSTEP3のIDを貼る
SITE_URL=https://example.com
SITE_NAME=コスメ自動比較
```
保存して閉じる。Amazon/X欄は楽天だけ開始では空でOK。

## STEP 5. 実行 (5分)
```powershell
cd C:\Users\DELL\Documents\Opencode\cosme-affiliate-auto
py -m pip install -r requirements.txt
py src/run_rakuten_only.py
```
成功目安:
- `[rakuten] 保存: 50件以上` と出る
- `[merge] products.json: XX件`
- `[site] 生成完了`
- `public/index.html` ができる

確認:
```powershell
start public/index.html
```
ブラウザで商品カード + 「楽天で見る」ボタンが出ればOK。
ボタンのリンクに `affiliateId` または `?pc=` 系パラメータが付いていれば収益化OK。

件数確認:
```powershell
py -c "import json; print(len(json.load(open('data/products.json',encoding='utf-8'))))"
```

## STEP 6. うまくいかない時
| 症状 | 対処 |
|---|---|
| `保存: 0件` | APP_ID間違い・未反映(発行直後は数分待つ)。`.env`保存忘れ。`notepad .env`で再確認 |
| `400 invalid applicationId` | アプリIDのコピーミス。前後空白を消す |
| `429 Too Many Requests` | `config.yaml` の `hits_per_keyword: 30` → `10` に下げ、キーワードを2〜3個に減らして再実行 |
| リンクが通常リンク | `RAKUTEN_AFFILIATE_ID` 未設定。設定後に再実行すればアフィリURLに変わる |
| 画像が出ない | 楽天側データ欠落。自動で非表示になるので無視でOK |

## STEP 7. 次 (公開・自動化)
1. GitHubにpush → Secretsに `RAKUTEN_APP_ID` `RAKUTEN_AFFILIATE_ID` `SITE_URL` 登録
2. Cloudflare Pagesで `public` を公開 → 独自ドメイン接続
3. 楽天アフィリエイトの登録サイトURLを本番URLに修正
4. Search Consoleに `sitemap.xml` 登録

公開後にAmazon追加したくなったら `py src/run_all.py` に切り替えるだけ。
