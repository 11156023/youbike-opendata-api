"""應用程式設定：所有可調整的參數集中於此，可用環境變數覆寫。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 原始 Open Data 檔案（單一 JSON 檔）
DATA_FILE = Path(os.getenv("YOUBIKE_DATA_FILE", BASE_DIR / "data" / "youbike_stations.json"))

# SQLite 資料庫位置
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'youbike.db'}")

# Open Data 來源 URL（臺北市政府交通局 YouBike2.0 即時資訊）
OPEN_DATA_URL = os.getenv(
    "OPEN_DATA_URL",
    "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json",
)

API_PREFIX = "/api/v1"
APP_TITLE = "YouBike 2.0 Taipei Station API"
APP_VERSION = "1.0.0"
