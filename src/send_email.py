"""本日のSNS原稿をメール送信 (出先での手動投稿用)。Gmail SMTP。
Secrets: GMAIL_USER / GMAIL_APP_PASSWORD / MAIL_TO が無ければスキップ。
値はログに出さない。"""
import os, pathlib, datetime, smtplib
from email.mime.text import MIMEText

try:
    from load_env import load_env
    load_env()
except Exception:
    pass

BASE = pathlib.Path(__file__).resolve().parents[1]
JST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(JST).date().isoformat()


def build_body():
    bundle = BASE / "sns" / f"{TODAY}.md"
    if bundle.exists():
        return bundle.read_text(encoding="utf-8"), f"sns/{TODAY}.md"
    files = sorted((BASE / "data" / "sns_queue").glob(f"{TODAY}*.txt"))
    if files:
        parts = [f.read_text(encoding="utf-8") for f in files]
        return "\n\n-----\n\n".join(parts), f"sns_queue {len(files)}件"
    return "", ""


def main():
    user = os.getenv("GMAIL_USER", "")
    pw = os.getenv("GMAIL_APP_PASSWORD", "")
    to = os.getenv("MAIL_TO", "")
    if not (user and pw and to):
        print("[mail] GMAIL_USER/GMAIL_APP_PASSWORD/MAIL_TO 未設定 -> スキップ")
        return
    body, src = build_body()
    if not body:
        print("[mail] 本日の原稿なし -> スキップ")
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"【みてコス】本日のSNS原稿 {TODAY}"
    msg["From"] = user
    msg["To"] = to
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls()
        s.login(user, pw)
        s.send_message(msg)
    print(f"[mail] 送信OK -> {src}")


if __name__ == "__main__":
    main()
