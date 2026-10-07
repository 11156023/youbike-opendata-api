# API 規格說明 — YouBike 2.0 Taipei Station API

- Base URL（本機）：`http://127.0.0.1:8000`
- API 前綴：`/api/v1`
- 線上文件：Swagger UI `/docs`、ReDoc `/redoc`、OpenAPI JSON `/openapi.json`（亦匯出於 [openapi.json](openapi.json)）
- 資料格式：JSON（UTF-8）
- 認證：無（作業用途）

## 資料模型

### Area（行政區）

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | int | 主鍵，自動遞增 |
| name_zh | string | 中文名稱（唯一），來源 `sarea` |
| name_en | string? | 英文名稱，來源 `sareaen` |
| station_count | int | 回應時計算的站點數（唯讀） |

### Station（站點）

| 欄位 | 型別 | 來源欄位 | 說明 |
|---|---|---|---|
| sno | string | sno | 主鍵，站點代號 |
| name_zh | string | sna | 站名 |
| name_en | string? | snaen | 英文站名 |
| area_id | int | sarea → areas.id | 所屬行政區 |
| area_name | string | — | 行政區中文名（唯讀） |
| address_zh / address_en | string? | ar / aren | 地址 |
| latitude / longitude | float | latitude / longitude | 座標（-90~90 / -180~180） |
| total_docks | int ≥0 | Quantity | 總車位數 |
| available_bikes | int ≥0 | available_rent_bikes | 可借車輛數 |
| available_docks | int ≥0 | available_return_bikes | 可還空位數 |
| is_active | bool | act | 是否營運中 |
| info_time | datetime? | infoTime | 站點回報時間 |
| updated_at | datetime | — | 本系統最後更新時間（唯讀） |

分頁回應格式 `Page<T>`：`{ "total": int, "limit": int, "offset": int, "items": [T] }`

## 端點總覽

### Areas

| Method | Path | 說明 | 成功 | 錯誤 |
|---|---|---|---|---|
| GET | /areas | 列出所有行政區（含站點數） | 200 | — |
| POST | /areas | 新增行政區 | 201 | 409 名稱重複、422 驗證失敗 |
| GET | /areas/{id} | 取得單一行政區 | 200 | 404 |
| PUT | /areas/{id} | 更新行政區（欄位可部分提供） | 200 | 404、409 |
| DELETE | /areas/{id} | 刪除行政區 | 204 | 404、409 仍有站點 |
| GET | /areas/{id}/stations | 行政區內站點（分頁） | 200 | 404 |

### Stations

| Method | Path | 說明 | 成功 | 錯誤 |
|---|---|---|---|---|
| GET | /stations | 搜尋 / 列出站點（分頁、篩選、排序） | 200 | 422 參數錯誤 |
| GET | /stations/nearby | 座標附近站點（Haversine 距離，公尺） | 200 | 422 |
| POST | /stations | 新增站點 | 201 | 409 sno 重複、422 驗證失敗 / 行政區不存在 |
| GET | /stations/{sno} | 取得單一站點 | 200 | 404 |
| PUT | /stations/{sno} | 完整更新（需提供所有必填欄位） | 200 | 404、422 |
| PATCH | /stations/{sno} | 部分更新 | 200 | 404、422 |
| PATCH | /stations/{sno}/availability | 回報即時車況（可借 / 可還） | 200 | 404、422 超過總車位 |
| DELETE | /stations/{sno} | 刪除站點 | 204 | 404 |

`GET /stations` 查詢參數：

| 參數 | 型別 | 預設 | 說明 |
|---|---|---|---|
| q | string | — | 關鍵字，比對站名 / 英文站名 / 地址 |
| area_id | int | — | 行政區 id |
| is_active | bool | — | 是否營運中 |
| min_bikes | int | — | 可借車輛數下限 |
| min_docks | int | — | 可還空位數下限 |
| sort | enum | sno | sno, name_zh, available_bikes, available_docks, total_docks, updated_at |
| order | enum | asc | asc / desc |
| limit | int 1~200 | 20 | 每頁筆數 |
| offset | int ≥0 | 0 | 起始位移 |

`GET /stations/nearby` 查詢參數：`lat`（必填）、`lng`（必填）、`radius`（公尺，預設 500，上限 5000）、`limit`（預設 10）、`only_with_bikes`（預設 false）。

### Stats & Admin

| Method | Path | 說明 | 成功 | 錯誤 |
|---|---|---|---|---|
| GET | /stats/summary | 全市車況摘要（站數、總車位、可借、可還、空站 / 滿站數） | 200 | — |
| GET | /stats/areas | 各行政區車況統計 | 200 | — |
| POST | /admin/reload | 重新匯入 Open Data（upsert）；`?refresh=true` 先重新下載 | 200 | 404 資料檔不存在、502 下載失敗 |

### 其他

| Method | Path | 說明 |
|---|---|---|
| GET | /health | 健康檢查 `{ "status": "ok", "version": "1.0.0" }` |
| GET | / | 轉址到 /docs |

## 錯誤回應格式

```json
{ "detail": "找不到站點 sno=XXXX" }
```

422 驗證錯誤為 FastAPI 標準格式：`{ "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }`

## 設計說明

- **Resource 切分**：原始資料為扁平站點清單，`sarea` 行政區被正規化為獨立 Resource，`stations.area_id` 以外鍵參照，刪除仍有站點的行政區會回 409 以保護參照完整性。
- **PUT vs PATCH**：PUT 需提供完整欄位（未提供的 optional 欄位會被設為 null），PATCH 只更新有提供的欄位。
- **availability 子資源**：模擬站點 IoT 裝置定期上傳車況，只允許修改可借 / 可還數量並驗證不超過總車位。
- **狀態碼慣例**：201 建立、204 刪除無內容、404 找不到、409 衝突、422 驗證失敗、502 外部來源失敗。

實測範例請見 [api_examples.md](api_examples.md)。
