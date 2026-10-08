"""全自動実行オーケストレータ: 取得 -> 統合 -> サイト -> 記事/SNS原稿 -> (任意)投稿"""
import runpy, pathlib
SRC = pathlib.Path(__file__).parent
for mod in ["fetch_rakuten", "fetch_amazon", "merge_products", "generate_site", "generate_posts"]:
    print(f"\n===== {mod} =====")
    runpy.run_module(mod, run_name="__main__")
print("\n[run_all] 完了。public/ をホスティングにデプロイ / data/sns_queue を確認してください。")
print("X自動投稿する場合のみ post_sns を実行 (キー必要)。")
