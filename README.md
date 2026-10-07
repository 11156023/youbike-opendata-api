# YouBike 2.0 Taipei Station API — 基於 Open Data 之 RESTful API 服務

以 **臺北市 YouBike 2.0 站點即時資訊** Open Data 為主題，使用 **Python + FastAPI + SQLite** 實作的 RESTful API Server，提供行政區（Areas）與站點（Stations）兩個 Resource 的完整 CRUD、搜尋、附近站點查詢、即時車況回報與統計功能，並附 Swagger UI 線上文件、Python API Client、Bruno 測試集與 Render 部署設定。

| 項目 | 內容 |
|---|---|
| Open Data | 臺北市政府交通局 — YouBike2.0 臺北市公共自行車即時資訊（[data.taipei](https://data.taipei/dataset/detail?id=c6bc8aeb-ccd8-4e9c-9b4c-6ed4ee72be0b)） |
| 來源 URL | https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json |
| 資料檔 | [`data/youbike_stations.json`](data/youbike_stations.json)（單一 JSON 檔，1,813 站、13 個行政區，下載於 2026-10-07） |
| 技術 | Python 3.12+、FastAPI、SQLAlchemy 2、SQLite、Pydantic v2、uvicorn |
| 線上文件 | Swagger UI `/docs`、ReDoc `/redoc`、OpenAPI JSON `/openapi.json` |
| AI 輔助工具 | Claude Code（設定檔：[`CLAUDE.md`](CLAUDE.md)） |
| 雲端部署 | Render（[`render.yaml`](render.yaml) + [`Dockerfile`](Dockerfile)）；API Server URL：_部署後填入_ |

## 目錄結構

```
opendata-api/
├── app/                      FastAPI 應用程式
│   ├── main.py               進入點、Swagger 設定、啟動時自動匯入資料
│   ├── config.py             設定（資料檔路徑、DATABASE_URL、Open Data URL）
│   ├── database.py           SQLAlchemy engine / session
│   ├── models.py             ORM：Area、Station
│   ├── schemas.py            Pydantic 輸入 / 輸出模型
│   ├── crud.py               資料存取層
│   ├── importer.py           Open Data JSON → SQLite（upsert）
│   └── routers/              areas.py、stations.py、stats.py
├── data/youbike_stations.json   Open Data 原始資料檔（SQLite 檔 youbike.db 會自動產生）
├── scripts/
│   ├── import_data.py        匯入 / 重新下載 / 重建資料庫
│   ├── export_openapi.py     匯出 docs/openapi.json
│   └── gen_bruno.py          產生 Bruno collection
├── client/api_client.py      Python API Client（含示範流程與 Markdown 實測輸出）
├── bruno/youbike-api/        Bruno collection（API 測試工具組態）
├── tests/                    pytest 整合測試
├── docs/
│   ├── API_SPEC.md           API 規格說明
│   ├── openapi.json          OpenAPI 3.1 規格（由 FastAPI 自動產生）
│   └── api_examples.md       實測範例（Request / Response / Status Code）
├── CLAUDE.md                 AI 輔助開發設定檔
├── Dockerfile / render.yaml  雲端部署
└── requirements.txt
```

## 環境建置

需要 Python 3.12 以上。

```bash
cd opendata-api
python -m venv .venv
```

啟用虛擬環境：

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

安裝套件：

```bash
pip install -r requirements.txt
```

## 匯入資料

將 Open Data JSON 匯入 SQLite（`data/youbike.db`）。Server 首次啟動若資料庫為空也會自動匯入，此步驟可省略。

```bash
python scripts/import_data.py
```

其他選項：`--refresh` 先從 Open Data 來源重新下載最新資料；`--reset` 先清空資料庫再匯入。

## 啟動 API Server

```bash
uvicorn app.main:app --reload
```

啟動後開啟：

- Swagger UI：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc
- 健康檢查：http://127.0.0.1:8000/health

若 8000 埠已被占用，改用 `uvicorn app.main:app --reload --port 8010`。

## API 一覽

所有端點皆以 `/api/v1` 為前綴，完整規格見 [docs/API_SPEC.md](docs/API_SPEC.md)。

| Resource | Method | Path | 說明 |
|---|---|---|---|
| Areas | GET | /areas | 列出行政區（含站點數） |
| | POST | /areas | 新增行政區 |
| | GET / PUT / DELETE | /areas/{id} | 讀取 / 更新 / 刪除 |
| | GET | /areas/{id}/stations | 行政區內站點（分頁） |
| Stations | GET | /stations | 搜尋 / 列出（q、area_id、is_active、min_bikes、min_docks、sort、order、limit、offset） |
| | GET | /stations/nearby | 座標附近站點（lat、lng、radius、only_with_bikes） |
| | POST | /stations | 新增站點 |
| | GET / PUT / PATCH / DELETE | /stations/{sno} | 讀取 / 完整更新 / 部分更新 / 刪除 |
| | PATCH | /stations/{sno}/availability | 回報即時可借 / 可還數量 |
| Stats & Admin | GET | /stats/summary | 全市車況摘要 |
| | GET | /stats/areas | 各行政區統計 |
| | POST | /admin/reload | 重新匯入 Open Data（`?refresh=true` 先重新下載） |

狀態碼：200 成功、201 建立、204 刪除、404 找不到、409 衝突（重複 / 仍有關聯資料）、422 驗證失敗、502 外部來源失敗。

### 範例

```bash
curl "http://127.0.0.1:8000/api/v1/stations?q=捷運&min_bikes=5&sort=available_bikes&order=desc&limit=3"
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/stations -H "Content-Type: application/json" -d "{\"sno\":\"DEMO0001\",\"name_zh\":\"YouBike2.0_示範站\",\"area_id\":1,\"latitude\":25.033,\"longitude\":121.5654,\"total_docks\":20,\"available_bikes\":8,\"available_docks\":12}"
```

更多 Request / Response 實例見 [docs/api_examples.md](docs/api_examples.md)。

## API 測試

### 方式一：Python API Client

`client/api_client.py` 提供 `YouBikeClient` 類別封裝所有端點，執行後會依序呼叫 26 個 API 操作（含 404 / 409 / 422 錯誤案例），印出 Request / Response，並可輸出 Markdown 實測紀錄。

```bash
python client/api_client.py --markdown docs/api_examples.md
```

連到其他 server 請加 `--base-url https://<your-server>`。

### 方式二：Bruno

1. 安裝 [Bruno](https://www.usebruno.com/)。
2. Open Collection → 選擇 `bruno/youbike-api` 資料夾。
3. 右上角選擇環境 `local`（或修改 `render` 環境的 baseUrl）。
4. 依資料夾 Areas → Stations → Stats 順序執行，或在 collection 上按右鍵 → Run 全部執行；每個請求都有 assert 驗證狀態碼。

### 方式三：pytest 自動化測試

使用獨立測試資料庫，不影響正式資料。

```bash
pytest -q
```

## 雲端部署（Render）

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/11156023/youbike-opendata-api)

1. 點上方按鈕（或 Render Dashboard → New → **Blueprint** → 連結本 repo），Render 會讀取 `render.yaml` 以 Docker 方式建置，建置時自動匯入 Open Data。
2. 按 **Deploy Blueprint**，等待約 3～5 分鐘建置完成。
3. 部署完成後，API Server URL 為 `https://youbike-opendata-api.onrender.com`（名稱若被占用 Render 會自動加後綴），Swagger UI 在 `/docs`。

免費方案閒置後會休眠，第一次請求需等待約 30 秒。SQLite 存於容器內，重新部署會還原為原始 Open Data。

也可本機以 Docker 執行：

```bash
docker build -t youbike-api . && docker run -p 8000:8000 youbike-api
```

## AI 輔助開發

本專案使用 Claude Code 協助設計 API 規格、撰寫程式碼、測試、Bruno collection 與文件。專案層級的 AI 設定與開發慣例記錄於 [`CLAUDE.md`](CLAUDE.md)。

## 資料授權

資料來源：臺北市政府交通局，依「政府資料開放授權條款－第1版」釋出。
