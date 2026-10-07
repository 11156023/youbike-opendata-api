# API 實測範例

- 產生時間：2026-10-07 19:51:25
- API Server：`https://youbike-opendata-api.onrender.com`
- 產生方式：`python client/api_client.py --markdown docs/api_examples.md`

| # | 操作 | Method | Path | Status |
|---|------|--------|------|--------|
| 1 | Health check | `GET` | `/health` | 200 |
| 2 | 列出所有行政區 | `GET` | `/api/v1/areas` | 200 |
| 3 | 取得單一行政區 | `GET` | `/api/v1/areas/1` | 200 |
| 4 | 新增行政區 | `POST` | `/api/v1/areas` | 201 |
| 5 | 新增重複行政區 → 409 | `POST` | `/api/v1/areas` | 409 |
| 6 | 更新行政區 | `PUT` | `/api/v1/areas/14` | 200 |
| 7 | 刪除仍有站點的行政區 → 409 | `DELETE` | `/api/v1/areas/1` | 409 |
| 8 | 行政區內站點 | `GET` | `/api/v1/areas/1/stations?limit=3` | 200 |
| 9 | 列出站點（分頁） | `GET` | `/api/v1/stations?limit=3` | 200 |
| 10 | 關鍵字搜尋 | `GET` | `/api/v1/stations?q=%E6%8D%B7%E9%81%8B&limit=3` | 200 |
| 11 | 篩選+排序 | `GET` | `/api/v1/stations?min_bikes=10&sort=available_bikes&order=desc&limit=3` | 200 |
| 12 | 附近站點 | `GET` | `/api/v1/stations/nearby?lat=25.0418&lng=121.5436&radius=500&limit=3&only_with_bikes=true` | 200 |
| 13 | 取得單一站點 | `GET` | `/api/v1/stations/500101001` | 200 |
| 14 | 查無站點 → 404 | `GET` | `/api/v1/stations/NOPE` | 404 |
| 15 | 新增站點 | `POST` | `/api/v1/stations` | 201 |
| 16 | 新增重複站點 → 409 | `POST` | `/api/v1/stations` | 409 |
| 17 | 資料驗證失敗 → 422（latitude 超出範圍） | `POST` | `/api/v1/stations` | 422 |
| 18 | 部分更新 | `PATCH` | `/api/v1/stations/DEMO0001` | 200 |
| 19 | 完整更新 | `PUT` | `/api/v1/stations/DEMO0001` | 200 |
| 20 | 即時車況回報 | `PATCH` | `/api/v1/stations/DEMO0001/availability` | 200 |
| 21 | 車況超過總車位 → 422 | `PATCH` | `/api/v1/stations/DEMO0001/availability` | 422 |
| 22 | 全市摘要 | `GET` | `/api/v1/stats/summary` | 200 |
| 23 | 各行政區統計 | `GET` | `/api/v1/stats/areas` | 200 |
| 24 | 刪除站點 | `DELETE` | `/api/v1/stations/DEMO0001` | 204 |
| 25 | 刪除後再查 → 404 | `GET` | `/api/v1/stations/DEMO0001` | 404 |
| 26 | 刪除行政區 | `DELETE` | `/api/v1/areas/14` | 204 |

## 1. Health check

**Request**

```http
GET /health
```

**Response** `200`

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## 2. 列出所有行政區  GET /areas

**Request**

```http
GET /api/v1/areas
```

**Response** `200`

```json
[
  {
    "name_zh": "大安區",
    "name_en": "Daan Dist.",
    "id": 1,
    "station_count": 218
  },
  {
    "name_zh": "大同區",
    "name_en": "Datong Dist",
    "id": 2,
    "station_count": 84
  },
  {
    "name_zh": "士林區",
    "name_en": "Shilin Dist",
    "id": 3,
    "station_count": 156
  },
  "... 共 13 筆，以下省略"
]
```

## 3. 取得單一行政區  GET /areas/{id}

**Request**

```http
GET /api/v1/areas/1
```

**Response** `200`

```json
{
  "name_zh": "大安區",
  "name_en": "Daan Dist.",
  "id": 1,
  "station_count": 218
}
```

## 4. 新增行政區  POST /areas

**Request**

```http
POST /api/v1/areas
```

Request Body:

```json
{
  "name_zh": "測試示範區",
  "name_en": "Demo Dist."
}
```

**Response** `201`

```json
{
  "name_zh": "測試示範區",
  "name_en": "Demo Dist.",
  "id": 14,
  "station_count": 0
}
```

## 5. 新增重複行政區 → 409

**Request**

```http
POST /api/v1/areas
```

Request Body:

```json
{
  "name_zh": "測試示範區",
  "name_en": null
}
```

**Response** `409`

```json
{
  "detail": "行政區 '測試示範區' 已存在"
}
```

## 6. 更新行政區  PUT /areas/{id}

**Request**

```http
PUT /api/v1/areas/14
```

Request Body:

```json
{
  "name_en": "Demo District (updated)"
}
```

**Response** `200`

```json
{
  "name_zh": "測試示範區",
  "name_en": "Demo District (updated)",
  "id": 14,
  "station_count": 0
}
```

## 7. 刪除仍有站點的行政區 → 409

**Request**

```http
DELETE /api/v1/areas/1
```

**Response** `409`

```json
{
  "detail": "行政區仍有 218 個站點，請先刪除或移轉站點"
}
```

## 8. 行政區內站點  GET /areas/{id}/stations

**Request**

```http
GET /api/v1/areas/1/stations?limit=3
```

**Response** `200`

```json
{
  "total": 218,
  "limit": 3,
  "offset": 0,
  "items": [
    {
      "name_zh": "YouBike2.0_捷運科技大樓站",
      "name_en": "YouBike2.0_MRT Technology Bldg. Sta.",
      "area_id": 1,
      "address_zh": "復興南路二段235號前",
      "address_en": "No.235， Sec. 2， Fuxing S. Rd.",
      "latitude": 25.02605,
      "longitude": 121.5436,
      "total_docks": 28,
      "available_bikes": 5,
      "available_docks": 22,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101001",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573451"
    },
    {
      "name_zh": "YouBike2.0_復興南路二段273號前",
      "name_en": "YouBike2.0_No.273， Sec. 2， Fuxing S. Rd.",
      "area_id": 1,
      "address_zh": "復興南路二段273號西側",
      "address_en": "No.273， Sec. 2， Fuxing S. Rd. (West)",
      "latitude": 25.02565,
      "longitude": 121.54357,
      "total_docks": 21,
      "available_bikes": 7,
      "available_docks": 14,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101002",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573455"
    },
    {
      "name_zh": "YouBike2.0_國北教大實小東側門",
      "name_en": "YouBike2.0_NTUE Experiment Elementary School (East)",
      "area_id": 1,
      "address_zh": "和平東路二段96巷7號",
      "address_en": "No. 7， Ln. 96， Sec. 2， Heping E. Rd",
      "latitude": 25.02429,
      "longitude": 121.54124,
      "total_docks": 28,
      "available_bikes": 1,
      "available_docks": 26,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101003",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573456"
    }
  ]
}
```

## 9. 列出站點（分頁）  GET /stations?limit=3

**Request**

```http
GET /api/v1/stations?limit=3
```

**Response** `200`

```json
{
  "total": 1813,
  "limit": 3,
  "offset": 0,
  "items": [
    {
      "name_zh": "YouBike2.0_捷運科技大樓站",
      "name_en": "YouBike2.0_MRT Technology Bldg. Sta.",
      "area_id": 1,
      "address_zh": "復興南路二段235號前",
      "address_en": "No.235， Sec. 2， Fuxing S. Rd.",
      "latitude": 25.02605,
      "longitude": 121.5436,
      "total_docks": 28,
      "available_bikes": 5,
      "available_docks": 22,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101001",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573451"
    },
    {
      "name_zh": "YouBike2.0_復興南路二段273號前",
      "name_en": "YouBike2.0_No.273， Sec. 2， Fuxing S. Rd.",
      "area_id": 1,
      "address_zh": "復興南路二段273號西側",
      "address_en": "No.273， Sec. 2， Fuxing S. Rd. (West)",
      "latitude": 25.02565,
      "longitude": 121.54357,
      "total_docks": 21,
      "available_bikes": 7,
      "available_docks": 14,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101002",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573455"
    },
    {
      "name_zh": "YouBike2.0_國北教大實小東側門",
      "name_en": "YouBike2.0_NTUE Experiment Elementary School (East)",
      "area_id": 1,
      "address_zh": "和平東路二段96巷7號",
      "address_en": "No. 7， Ln. 96， Sec. 2， Heping E. Rd",
      "latitude": 25.02429,
      "longitude": 121.54124,
      "total_docks": 28,
      "available_bikes": 1,
      "available_docks": 26,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101003",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573456"
    }
  ]
}
```

## 10. 關鍵字搜尋  GET /stations?q=捷運&limit=3

**Request**

```http
GET /api/v1/stations?q=%E6%8D%B7%E9%81%8B&limit=3
```

**Response** `200`

```json
{
  "total": 201,
  "limit": 3,
  "offset": 0,
  "items": [
    {
      "name_zh": "YouBike2.0_捷運科技大樓站",
      "name_en": "YouBike2.0_MRT Technology Bldg. Sta.",
      "area_id": 1,
      "address_zh": "復興南路二段235號前",
      "address_en": "No.235， Sec. 2， Fuxing S. Rd.",
      "latitude": 25.02605,
      "longitude": 121.5436,
      "total_docks": 28,
      "available_bikes": 5,
      "available_docks": 22,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101001",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573451"
    },
    {
      "name_zh": "YouBike2.0_捷運公館站(2號出口)",
      "name_en": "YouBike2.0_MRT Gongguan Sta. (Exit 2)",
      "area_id": 1,
      "address_zh": "捷運公館站(2號出口)外側",
      "address_en": "MRT Gongguan Sta. (Exit 2)",
      "latitude": 25.01491,
      "longitude": 121.53438,
      "total_docks": 99,
      "available_bikes": 23,
      "available_docks": 37,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101022",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573464"
    },
    {
      "name_zh": "YouBike2.0_捷運麟光站(2號出口)",
      "name_en": "YouBike2.0_MRT Linguang Sta. (Exit 2)",
      "area_id": 1,
      "address_zh": "和平東路三段420號東北側",
      "address_en": "No. 420， Sec. 3， Heping E. Rd. (Northeast)",
      "latitude": 25.0181,
      "longitude": 121.55929,
      "total_docks": 69,
      "available_bikes": 3,
      "available_docks": 66,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101100",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573477"
    }
  ]
}
```

## 11. 篩選+排序  GET /stations?min_bikes=10&sort=available_bikes&order=desc&limit=3

**Request**

```http
GET /api/v1/stations?min_bikes=10&sort=available_bikes&order=desc&limit=3
```

**Response** `200`

```json
{
  "total": 668,
  "limit": 3,
  "offset": 0,
  "items": [
    {
      "name_zh": "YouBike2.0_捷運公館站(3號出口)",
      "name_en": "YouBike2.0_MRT Gongguan Sta.(Exit.3)",
      "area_id": 1,
      "address_zh": "捷運公館站(3號出口)西側",
      "address_en": "MRT Gongguan Sta.(Exit.3)(West)",
      "latitude": 25.01551,
      "longitude": 121.53374,
      "total_docks": 99,
      "available_bikes": 86,
      "available_docks": 13,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500101181",
      "area_name": "大安區",
      "updated_at": "2026-10-07T11:47:41.573510"
    },
    {
      "name_zh": "YouBike2.0_松山車站",
      "name_en": "YouBike2.0_Songshan Sta.",
      "area_id": 11,
      "address_zh": "松山路11號南側",
      "address_en": "No. 11， Songshan Rd. (South)",
      "latitude": 25.0489,
      "longitude": 121.57841,
      "total_docks": 70,
      "available_bikes": 69,
      "available_docks": 1,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500112049",
      "area_name": "信義區",
      "updated_at": "2026-10-07T11:47:41.883832"
    },
    {
      "name_zh": "YouBike2.0_北投運動中心",
      "name_en": "YouBike2.0_Beitou Sports Center",
      "area_id": 8,
      "address_zh": "石牌路一段39巷100號(旁)",
      "address_en": "No. 100， Ln. 39， Sec. 1， Shipai Rd.",
      "latitude": 25.11666,
      "longitude": 121.50962,
      "total_docks": 89,
      "available_bikes": 59,
      "available_docks": 28,
      "is_active": true,
      "info_time": "2026-10-07T18:58:03",
      "sno": "500109032",
      "area_name": "北投區",
      "updated_at": "2026-10-07T11:47:41.809487"
    }
  ]
}
```

## 12. 附近站點  GET /stations/nearby

**Request**

```http
GET /api/v1/stations/nearby?lat=25.0418&lng=121.5436&radius=500&limit=3&only_with_bikes=true
```

**Response** `200`

```json
[
  {
    "name_zh": "YouBike2.0_捷運忠孝復興站(1號出口)",
    "name_en": "YouBike2.0_MRT Zhongxiao Fuxing Sta. (Exit 1)",
    "area_id": 1,
    "address_zh": "忠孝東路三段303號",
    "address_en": "No. 303， Sec. 3， ZhongXiao E. Rd.",
    "latitude": 25.04199,
    "longitude": 121.54362,
    "total_docks": 27,
    "available_bikes": 27,
    "available_docks": 0,
    "is_active": true,
    "info_time": "2026-10-07T18:58:21",
    "sno": "500101251",
    "area_name": "大安區",
    "updated_at": "2026-10-07T11:47:41.573538",
    "distance_m": 21.2
  },
  {
    "name_zh": "YouBike2.0_捷運忠孝復興站(4號出口)",
    "name_en": "YouBike2.0_MRT Zhongxiao Fuxing Sta. (Exit 4)",
    "area_id": 1,
    "address_zh": "忠孝東路四段7號前",
    "address_en": "No. 7， Sec. 4， ZhongXiao E. Rd.",
    "latitude": 25.04173,
    "longitude": 121.54412,
    "total_docks": 25,
    "available_bikes": 4,
    "available_docks": 21,
    "is_active": true,
    "info_time": "2026-10-07T18:58:04",
    "sno": "500101247",
    "area_name": "大安區",
    "updated_at": "2026-10-07T11:47:41.573536",
    "distance_m": 53.0
  },
  {
    "name_zh": "YouBike2.0_捷運忠孝復興站(3號出口)",
    "name_en": "YouBike2.0_MRT Zhongxiao Fuxing Sta. (Exit 3)",
    "area_id": 1,
    "address_zh": "忠孝東路四段48號前",
    "address_en": "No. 48， Sec. 4， ZhongXiao E. Rd.",
    "latitude": 25.04152,
    "longitude": 121.54414,
    "total_docks": 37,
    "available_bikes": 11,
    "available_docks": 26,
    "is_active": true,
    "info_time": "2026-10-07T18:58:03",
    "sno": "500101233",
    "area_name": "大安區",
    "updated_at": "2026-10-07T11:47:41.573531",
    "distance_m": 62.7
  }
]
```

## 13. 取得單一站點  GET /stations/{sno}

**Request**

```http
GET /api/v1/stations/500101001
```

**Response** `200`

```json
{
  "name_zh": "YouBike2.0_捷運科技大樓站",
  "name_en": "YouBike2.0_MRT Technology Bldg. Sta.",
  "area_id": 1,
  "address_zh": "復興南路二段235號前",
  "address_en": "No.235， Sec. 2， Fuxing S. Rd.",
  "latitude": 25.02605,
  "longitude": 121.5436,
  "total_docks": 28,
  "available_bikes": 5,
  "available_docks": 22,
  "is_active": true,
  "info_time": "2026-10-07T18:58:03",
  "sno": "500101001",
  "area_name": "大安區",
  "updated_at": "2026-10-07T11:47:41.573451"
}
```

## 14. 查無站點 → 404

**Request**

```http
GET /api/v1/stations/NOPE
```

**Response** `404`

```json
{
  "detail": "找不到站點 sno=NOPE"
}
```

## 15. 新增站點  POST /stations

**Request**

```http
POST /api/v1/stations
```

Request Body:

```json
{
  "sno": "DEMO0001",
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 20,
  "available_bikes": 8,
  "available_docks": 12,
  "is_active": true
}
```

**Response** `201`

```json
{
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 20,
  "available_bikes": 8,
  "available_docks": 12,
  "is_active": true,
  "info_time": null,
  "sno": "DEMO0001",
  "area_name": "測試示範區",
  "updated_at": "2026-10-07T11:51:28.218144"
}
```

## 16. 新增重複站點 → 409

**Request**

```http
POST /api/v1/stations
```

Request Body:

```json
{
  "sno": "DEMO0001",
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 20,
  "available_bikes": 8,
  "available_docks": 12,
  "is_active": true
}
```

**Response** `409`

```json
{
  "detail": "站點 sno=DEMO0001 已存在"
}
```

## 17. 資料驗證失敗 → 422（latitude 超出範圍）

**Request**

```http
POST /api/v1/stations
```

Request Body:

```json
{
  "sno": "DEMO0002",
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 999,
  "longitude": 121.5654,
  "total_docks": 20,
  "available_bikes": 8,
  "available_docks": 12,
  "is_active": true
}
```

**Response** `422`

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "body",
        "latitude"
      ],
      "msg": "Input should be less than or equal to 90",
      "input": 999,
      "ctx": {
        "le": 90.0
      }
    }
  ]
}
```

## 18. 部分更新  PATCH /stations/{sno}

**Request**

```http
PATCH /api/v1/stations/DEMO0001
```

Request Body:

```json
{
  "is_active": false,
  "name_zh": "YouBike2.0_示範站(暫停)"
}
```

**Response** `200`

```json
{
  "name_zh": "YouBike2.0_示範站(暫停)",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 20,
  "available_bikes": 8,
  "available_docks": 12,
  "is_active": false,
  "info_time": null,
  "sno": "DEMO0001",
  "area_name": "測試示範區",
  "updated_at": "2026-10-07T11:51:28.715318"
}
```

## 19. 完整更新  PUT /stations/{sno}

**Request**

```http
PUT /api/v1/stations/DEMO0001
```

Request Body:

```json
{
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 30,
  "available_bikes": 8,
  "available_docks": 22,
  "is_active": true
}
```

**Response** `200`

```json
{
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 30,
  "available_bikes": 8,
  "available_docks": 22,
  "is_active": true,
  "info_time": null,
  "sno": "DEMO0001",
  "area_name": "測試示範區",
  "updated_at": "2026-10-07T11:51:28.903988"
}
```

## 20. 即時車況回報  PATCH /stations/{sno}/availability

**Request**

```http
PATCH /api/v1/stations/DEMO0001/availability
```

Request Body:

```json
{
  "available_bikes": 5,
  "available_docks": 25
}
```

**Response** `200`

```json
{
  "name_zh": "YouBike2.0_示範站",
  "name_en": "Demo Sta.",
  "area_id": 14,
  "address_zh": "示範路100號",
  "address_en": "No.100, Demo Rd.",
  "latitude": 25.033,
  "longitude": 121.5654,
  "total_docks": 30,
  "available_bikes": 5,
  "available_docks": 25,
  "is_active": true,
  "info_time": "2026-10-07T11:51:29.084599",
  "sno": "DEMO0001",
  "area_name": "測試示範區",
  "updated_at": "2026-10-07T11:51:29.085199"
}
```

## 21. 車況超過總車位 → 422

**Request**

```http
PATCH /api/v1/stations/DEMO0001/availability
```

Request Body:

```json
{
  "available_bikes": 20,
  "available_docks": 20
}
```

**Response** `422`

```json
{
  "detail": "可借 + 可還 (40) 超過總車位 30"
}
```

## 22. 全市摘要  GET /stats/summary

**Request**

```http
GET /api/v1/stats/summary
```

**Response** `200`

```json
{
  "area_count": 14,
  "station_count": 1814,
  "active_station_count": 1787,
  "total_docks": 51534,
  "available_bikes": 16080,
  "available_docks": 34037,
  "bike_ratio": 0.312,
  "empty_stations": 148,
  "full_stations": 72,
  "last_info_time": "2026-10-07T18:58:21"
}
```

## 23. 各行政區統計  GET /stats/areas

**Request**

```http
GET /api/v1/stats/areas
```

**Response** `200`

```json
[
  {
    "area_id": 1,
    "area_name": "大安區",
    "station_count": 218,
    "active_station_count": 214,
    "total_docks": 6714,
    "available_bikes": 1749,
    "available_docks": 4758,
    "bike_ratio": 0.2605
  },
  {
    "area_id": 2,
    "area_name": "大同區",
    "station_count": 84,
    "active_station_count": 84,
    "total_docks": 2401,
    "available_bikes": 808,
    "available_docks": 1562,
    "bike_ratio": 0.3365
  },
  {
    "area_id": 3,
    "area_name": "士林區",
    "station_count": 156,
    "active_station_count": 151,
    "total_docks": 3921,
    "available_bikes": 1698,
    "available_docks": 2119,
    "bike_ratio": 0.4331
  },
  "... 共 14 筆，以下省略"
]
```

## 24. 刪除站點  DELETE /stations/{sno}

**Request**

```http
DELETE /api/v1/stations/DEMO0001
```

**Response** `204`

(no content)

## 25. 刪除後再查 → 404

**Request**

```http
GET /api/v1/stations/DEMO0001
```

**Response** `404`

```json
{
  "detail": "找不到站點 sno=DEMO0001"
}
```

## 26. 刪除行政區  DELETE /areas/{id}

**Request**

```http
DELETE /api/v1/areas/14
```

**Response** `204`

(no content)
