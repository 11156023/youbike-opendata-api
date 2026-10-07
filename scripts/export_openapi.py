"""將 FastAPI 自動產生的 OpenAPI 規格輸出為 docs/openapi.json（不需啟動 server）。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

out = ROOT / "docs" / "openapi.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"已輸出 {out}")
