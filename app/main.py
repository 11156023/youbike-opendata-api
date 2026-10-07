"""FastAPI 應用程式進入點。

啟動：uvicorn app.main:app --reload
Swagger UI：http://127.0.0.1:8000/docs
ReDoc：     http://127.0.0.1:8000/redoc
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app import importer, models  # noqa: F401  (models 需被 import 才會註冊到 Base.metadata)
from app.config import API_PREFIX, APP_TITLE, APP_VERSION, DATA_FILE
from app.database import Base, SessionLocal, engine
from app.routers import areas, stations, stats

DESCRIPTION = """
以 **臺北市 YouBike 2.0 站點即時資訊** Open Data 為主題的 RESTful API。

資料來源：臺北市政府交通局（data.taipei）
`https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json`

## Resources
| Resource | 說明 |
|---|---|
| **Areas** | 行政區（由站點資料的 `sarea` 欄位整理而成） |
| **Stations** | YouBike 2.0 站點：位置、車位、即時可借 / 可還數量 |
| **Stats & Admin** | 車況統計與 Open Data 重新匯入 |

所有端點皆以 `/api/v1` 為前綴。資料儲存於 SQLite，首次啟動若資料庫為空會自動匯入 `data/youbike_stations.json`。
"""

TAGS = [
    {"name": "Areas", "description": "行政區 CRUD"},
    {"name": "Stations", "description": "站點 CRUD、關鍵字搜尋、附近站點查詢、即時車況回報"},
    {"name": "Stats & Admin", "description": "統計摘要與資料重新匯入"},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(models.Station).count() == 0 and DATA_FILE.exists():
            importer.import_file(db, DATA_FILE)
    yield


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=DESCRIPTION,
    openapi_tags=TAGS,
    lifespan=lifespan,
    contact={"name": "IoTApp Open Data RESTful API Homework"},
    license_info={"name": "政府資料開放授權條款－第1版", "url": "https://data.gov.tw/license"},
)

app.include_router(areas.router, prefix=API_PREFIX)
app.include_router(stations.router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", tags=["Health"], summary="健康檢查")
def health():
    return {"status": "ok", "version": APP_VERSION}
