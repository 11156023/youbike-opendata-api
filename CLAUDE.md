# CLAUDE.md — AI 輔助開發設定

本專案使用 **Claude Code**（Anthropic 官方 CLI / 桌面版）作為 AI 輔助開發工具。此檔案是 Claude Code 讀取的專案說明，也作為作業繳交的「AI 輔助開發相關設定檔」。

## 專案概要

- 主題：臺北市 YouBike 2.0 站點即時資訊 Open Data → RESTful API
- 技術：Python 3.12+ / FastAPI / SQLAlchemy 2 / SQLite / Pydantic v2
- 原始資料：`data/youbike_stations.json`（單一 JSON 檔，1,813 站、13 個行政區）
- API 前綴：`/api/v1`；Swagger UI 在 `/docs`

## 目錄結構

```
app/
  config.py      設定（資料檔路徑、DATABASE_URL、Open Data URL）
  database.py    SQLAlchemy engine / session / Base
  models.py      ORM：Area, Station
  schemas.py     Pydantic 輸入輸出模型（Swagger 文件來源）
  crud.py        資料存取層（所有查詢集中於此）
  importer.py    Open Data JSON → SQLite upsert
  main.py        FastAPI app、lifespan（空庫自動匯入）
  routers/       areas.py, stations.py, stats.py
scripts/import_data.py   匯入 / 重新下載 / 重建資料庫
client/api_client.py     Python API Client + 示範流程 + Markdown 實測輸出
tests/                   pytest 整合測試（獨立測試 DB）
bruno/youbike-api/       Bruno collection（可直接 Open Collection）
docs/                    API 規格、openapi.json、實測紀錄
```

## 開發慣例

- Router 只做參數驗證與 HTTP 狀態碼，查詢邏輯放在 `crud.py`。
- 新增欄位時同步更新 `models.py`、`schemas.py`、`importer.py`，並補 `tests/test_api.py`。
- 錯誤碼：404 找不到、409 重複 / 有關聯資料、422 驗證失敗、502 外部資料來源失敗。
- 所有註解與 API 描述使用繁體中文；程式識別字使用英文。
- 修改 API 後執行 `pytest -q`，並重新產生 `docs/openapi.json`（`python scripts/export_openapi.py`）。

## 常用指令

```bash
python scripts/import_data.py            # 匯入資料
uvicorn app.main:app --reload            # 啟動 server
pytest -q                                # 測試
python client/api_client.py --markdown docs/api_examples.md   # 跑 client 並輸出實測紀錄
```

## AI 開發紀錄

本專案的 API 設計（Resource 切分、端點命名、狀態碼）、程式碼、測試、Bruno collection 與文件，皆由 Claude Code 依據作業需求與使用者選定的方向（資料集、測試工具、部署方式）協助產生，並經本機執行 pytest 與 Python client 驗證。
