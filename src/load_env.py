""" .env を os.environ に読み込む小物 (依存なし)。各スクリプトから import して使う。"""
import os, pathlib

def load_env():
    base = pathlib.Path(__file__).resolve().parents[1]
    f = base / ".env"
    if not f.exists():
        return False
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and (k not in os.environ or not os.environ[k]):
            os.environ[k] = v
    return True
