"""pytest fixtures：使用獨立的暫存 SQLite，不影響正式資料庫。"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 在 import app 之前設定環境變數，讓 config 讀到測試用資料庫
_TEST_DB = ROOT / "data" / "test_youbike.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.database import Base, engine
    from app.main import app

    if _TEST_DB.exists():
        _TEST_DB.unlink()
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:  # with 區塊會觸發 lifespan → 自動匯入資料
        yield c
    engine.dispose()
    if _TEST_DB.exists():
        _TEST_DB.unlink()
