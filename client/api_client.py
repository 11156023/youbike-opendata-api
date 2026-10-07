"""YouBike 2.0 Station API 的 Python API Client。

提供 `YouBikeClient` 類別封裝所有端點，並附帶一個示範流程 (`run_demo`)，
依序呼叫各 API 並印出 Request / Response，同時可輸出成 Markdown 實測紀錄。

用法（先啟動 API Server）：
    python client/api_client.py
    python client/api_client.py --base-url http://127.0.0.1:8000 --markdown docs/api_examples.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Any

import requests


class YouBikeClient:
    """對 RESTful API 的薄封裝；每個方法回傳 `requests.Response`。"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.api = f"{self.base_url}/api/v1"
        self.timeout = timeout
        self.session = requests.Session()
        self.log: list[dict[str, Any]] = []

    # ---- 底層 ----
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = path if path.startswith("http") else f"{self.api}{path}"
        if kwargs.get("params"):  # bool → "true"/"false"，避免送出 Python 的 True/False
            kwargs["params"] = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in kwargs["params"].items()}
        resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
        self.log.append(
            {
                "method": method,
                "url": resp.request.url,
                "body": kwargs.get("json"),
                "status": resp.status_code,
                "response": _safe_json(resp),
            }
        )
        return resp

    # ---- Health ----
    def health(self) -> requests.Response:
        return self._request("GET", f"{self.base_url}/health")

    # ---- Areas ----
    def list_areas(self) -> requests.Response:
        return self._request("GET", "/areas")

    def get_area(self, area_id: int) -> requests.Response:
        return self._request("GET", f"/areas/{area_id}")

    def create_area(self, name_zh: str, name_en: str | None = None) -> requests.Response:
        return self._request("POST", "/areas", json={"name_zh": name_zh, "name_en": name_en})

    def update_area(self, area_id: int, **fields) -> requests.Response:
        return self._request("PUT", f"/areas/{area_id}", json=fields)

    def delete_area(self, area_id: int) -> requests.Response:
        return self._request("DELETE", f"/areas/{area_id}")

    def list_area_stations(self, area_id: int, **params) -> requests.Response:
        return self._request("GET", f"/areas/{area_id}/stations", params=params)

    # ---- Stations ----
    def list_stations(self, **params) -> requests.Response:
        return self._request("GET", "/stations", params=params)

    def nearby(self, lat: float, lng: float, radius: float = 500, **params) -> requests.Response:
        return self._request("GET", "/stations/nearby", params={"lat": lat, "lng": lng, "radius": radius, **params})

    def get_station(self, sno: str) -> requests.Response:
        return self._request("GET", f"/stations/{sno}")

    def create_station(self, station: dict) -> requests.Response:
        return self._request("POST", "/stations", json=station)

    def replace_station(self, sno: str, station: dict) -> requests.Response:
        return self._request("PUT", f"/stations/{sno}", json=station)

    def patch_station(self, sno: str, **fields) -> requests.Response:
        return self._request("PATCH", f"/stations/{sno}", json=fields)

    def report_availability(self, sno: str, available_bikes: int, available_docks: int) -> requests.Response:
        return self._request(
            "PATCH", f"/stations/{sno}/availability",
            json={"available_bikes": available_bikes, "available_docks": available_docks},
        )

    def delete_station(self, sno: str) -> requests.Response:
        return self._request("DELETE", f"/stations/{sno}")

    # ---- Stats / Admin ----
    def summary(self) -> requests.Response:
        return self._request("GET", "/stats/summary")

    def area_stats(self) -> requests.Response:
        return self._request("GET", "/stats/areas")

    def reload(self, refresh: bool = False) -> requests.Response:
        return self._request("POST", "/admin/reload", params={"refresh": str(refresh).lower()})


# ---------------------------------------------------------------------------
def _safe_json(resp: requests.Response):
    if not resp.content:
        return None
    try:
        return resp.json()
    except ValueError:
        return resp.text


def _truncate(obj, max_items: int = 3):
    """列表過長時只保留前幾筆，方便閱讀。"""
    if isinstance(obj, list) and len(obj) > max_items:
        return obj[:max_items] + [f"... 共 {len(obj)} 筆，以下省略"]
    if isinstance(obj, dict) and isinstance(obj.get("items"), list) and len(obj["items"]) > max_items:
        return {**obj, "items": obj["items"][:max_items] + [f"... 共 {len(obj['items'])} 筆，以下省略"]}
    return obj


def show(title: str, resp: requests.Response, entry: dict) -> None:
    print(f"\n=== {title} ===")
    print(f"Request : {entry['method']} {entry['url']}")
    if entry["body"] is not None:
        print(f"Body    : {json.dumps(entry['body'], ensure_ascii=False)}")
    print(f"Response: {resp.status_code} {resp.reason}")
    if entry["response"] is not None:
        print(json.dumps(_truncate(entry["response"]), ensure_ascii=False, indent=2))


def run_demo(client: YouBikeClient) -> list[tuple[str, dict]]:
    """依序執行所有 API 操作並印出結果；回傳 (標題, log) 清單供輸出 Markdown。"""
    steps: list[tuple[str, dict]] = []

    def step(title: str, resp: requests.Response, expect: int | tuple[int, ...]):
        entry = client.log[-1]
        show(title, resp, entry)
        expected = expect if isinstance(expect, tuple) else (expect,)
        assert resp.status_code in expected, f"{title}: 預期 {expected} 實際 {resp.status_code}"
        steps.append((title, entry))
        return entry["response"]

    step("Health check", client.health(), 200)

    # ---- Areas ----
    areas = step("列出所有行政區  GET /areas", client.list_areas(), 200)
    first_area_id = areas[0]["id"]
    step("取得單一行政區  GET /areas/{id}", client.get_area(first_area_id), 200)
    new_area = step("新增行政區  POST /areas", client.create_area("測試示範區", "Demo Dist."), 201)
    step("新增重複行政區 → 409", client.create_area("測試示範區"), 409)
    step("更新行政區  PUT /areas/{id}", client.update_area(new_area["id"], name_en="Demo District (updated)"), 200)
    step("刪除仍有站點的行政區 → 409", client.delete_area(first_area_id), 409)
    step("行政區內站點  GET /areas/{id}/stations", client.list_area_stations(first_area_id, limit=3), 200)

    # ---- Stations ----
    step("列出站點（分頁）  GET /stations?limit=3", client.list_stations(limit=3), 200)
    step("關鍵字搜尋  GET /stations?q=捷運&limit=3", client.list_stations(q="捷運", limit=3), 200)
    step("篩選+排序  GET /stations?min_bikes=10&sort=available_bikes&order=desc&limit=3",
         client.list_stations(min_bikes=10, sort="available_bikes", order="desc", limit=3), 200)
    step("附近站點  GET /stations/nearby", client.nearby(25.0418, 121.5436, radius=500, limit=3, only_with_bikes=True), 200)
    step("取得單一站點  GET /stations/{sno}", client.get_station("500101001"), 200)
    step("查無站點 → 404", client.get_station("NOPE"), 404)

    demo = {
        "sno": "DEMO0001", "name_zh": "YouBike2.0_示範站", "name_en": "Demo Sta.", "area_id": new_area["id"],
        "address_zh": "示範路100號", "address_en": "No.100, Demo Rd.", "latitude": 25.0330, "longitude": 121.5654,
        "total_docks": 20, "available_bikes": 8, "available_docks": 12, "is_active": True,
    }
    step("新增站點  POST /stations", client.create_station(demo), 201)
    step("新增重複站點 → 409", client.create_station(demo), 409)
    step("資料驗證失敗 → 422（latitude 超出範圍）", client.create_station({**demo, "sno": "DEMO0002", "latitude": 999}), 422)
    step("部分更新  PATCH /stations/{sno}", client.patch_station("DEMO0001", is_active=False, name_zh="YouBike2.0_示範站(暫停)"), 200)
    step("完整更新  PUT /stations/{sno}",
         client.replace_station("DEMO0001", {**{k: v for k, v in demo.items() if k != "sno"}, "total_docks": 30, "available_docks": 22}), 200)
    step("即時車況回報  PATCH /stations/{sno}/availability", client.report_availability("DEMO0001", 5, 25), 200)
    step("車況超過總車位 → 422", client.report_availability("DEMO0001", 20, 20), 422)

    # ---- Stats ----
    step("全市摘要  GET /stats/summary", client.summary(), 200)
    step("各行政區統計  GET /stats/areas", client.area_stats(), 200)

    # ---- 清理 ----
    step("刪除站點  DELETE /stations/{sno}", client.delete_station("DEMO0001"), 204)
    step("刪除後再查 → 404", client.get_station("DEMO0001"), 404)
    step("刪除行政區  DELETE /areas/{id}", client.delete_area(new_area["id"]), 204)

    print(f"\n全部 {len(steps)} 個步驟皆符合預期狀態碼。")
    return steps


def to_markdown(steps: list[tuple[str, dict]], base_url: str) -> str:
    lines = [
        "# API 實測範例",
        "",
        f"- 產生時間：{datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- API Server：`{base_url}`",
        f"- 產生方式：`python client/api_client.py --markdown docs/api_examples.md`",
        "",
        "| # | 操作 | Method | Path | Status |",
        "|---|------|--------|------|--------|",
    ]
    for i, (title, e) in enumerate(steps, 1):
        path = e["url"].replace(base_url, "")
        lines.append(f"| {i} | {title.split('  ')[0]} | `{e['method']}` | `{path}` | {e['status']} |")
    lines.append("")
    for i, (title, e) in enumerate(steps, 1):
        path = e["url"].replace(base_url, "")
        lines += [f"## {i}. {title}", "", "**Request**", "", "```http", f"{e['method']} {path}", "```"]
        if e["body"] is not None:
            lines += ["", "Request Body:", "", "```json", json.dumps(e["body"], ensure_ascii=False, indent=2), "```"]
        lines += ["", f"**Response** `{e['status']}`", ""]
        if e["response"] is not None:
            lines += ["```json", json.dumps(_truncate(e["response"]), ensure_ascii=False, indent=2), "```"]
        else:
            lines += ["(no content)"]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="YouBike API client demo")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--markdown", help="將實測結果輸出為 Markdown 檔案路徑")
    args = parser.parse_args()

    client = YouBikeClient(args.base_url)
    try:
        client.health()
    except requests.ConnectionError:
        print(f"無法連線到 {args.base_url}，請先啟動 API Server：uvicorn app.main:app --reload")
        sys.exit(1)
    client.log.clear()

    steps = run_demo(client)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(to_markdown(steps, args.base_url))
        print(f"實測紀錄已輸出：{args.markdown}")


if __name__ == "__main__":
    main()
