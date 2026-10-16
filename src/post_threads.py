"""Threads自動投稿 (無料)。本日分のキューから1日N件をテキスト投稿。
Secrets: THREADS_USER_ID / THREADS_ACCESS_TOKEN が無ければスキップ。
値はログに出さない。"""
import os, time, pathlib, datetime
import requests
import yaml

try:
    from load_env import load_env
    load_env()
except Exception:
    pass

BASE = pathlib.Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(BASE / "config.yaml", encoding="utf-8"))
QUEUE = BASE / "data" / "sns_queue"
DONE = BASE / "data" / "sns_done"
DONE.mkdir(exist_ok=True)

JST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(JST).date().isoformat()
API = "https://graph.threads.net/v1.0"

USER_ID = os.getenv("THREADS_USER_ID", "")
TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")


def publish(text: str):
    r = requests.post(f"{API}/{USER_ID}/threads",
                      data={"media_type": "TEXT", "text": text, "access_token": TOKEN},
                      timeout=30)
    r.raise_for_status()
    cid = r.json()["id"]
    last = None
    for _ in range(6):
        time.sleep(10)
        p = requests.post(f"{API}/{USER_ID}/threads_publish",
                          data={"creation_id": cid, "access_token": TOKEN},
                          timeout=30)
        if p.status_code == 200:
            return p.json()
        last = p.text[:200]
    raise RuntimeError(f"publish失敗: {last}")


def main():
    if not (USER_ID and TOKEN):
        print("[threads] THREADS_USER_ID/THREADS_ACCESS_TOKEN 未設定 -> スキップ")
        return
    max_n = int(CFG.get("sns", {}).get("max_posts_per_day", 3))
    files = sorted(QUEUE.glob(f"{TODAY}*.txt"))[:max_n]
    if not files:
        print("[threads] 本日の投稿キュー無し")
        return
    print(f"[threads] {len(files)}件投稿開始")
    for f in files:
        text = f.read_text(encoding="utf-8")
        try:
            res = publish(text)
            print(f"[threads] 投稿OK {f.name}: {res.get('id')}")
            f.rename(DONE / f.name)
        except Exception as e:
            print(f"[threads] 投稿失敗 {f.name}: {e}")


if __name__ == "__main__":
    main()
