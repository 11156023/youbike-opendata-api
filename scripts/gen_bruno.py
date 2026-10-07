"""產生 Bruno collection（bruno/youbike-api/）。

Bruno 以純文字 .bru 檔儲存，可直接用 Bruno「Open Collection」開啟此資料夾。
此腳本讓 collection 可重現、可版本控制；修改後執行：python scripts/gen_bruno.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "bruno" / "youbike-api"


def bru(name: str, seq: int, method: str, url: str, *, body: dict | None = None, query: dict | None = None,
        asserts: dict | None = None, post_script: str | None = None, docs: str | None = None) -> str:
    parts = [f"meta {{\n  name: {name}\n  type: http\n  seq: {seq}\n}}"]
    body_type = "json" if body is not None else "none"
    parts.append(f"{method} {{\n  url: {url}\n  body: {body_type}\n  auth: none\n}}")
    if query:
        lines = "\n".join(f"  {k}: {v}" for k, v in query.items())
        parts.append(f"params:query {{\n{lines}\n}}")
    if body is not None:
        text = json.dumps(body, ensure_ascii=False, indent=2).replace('"{{areaId}}"', "{{areaId}}")
        text = "\n".join("  " + line for line in text.splitlines())
        parts.append(f"body:json {{\n{text}\n}}")
    if asserts:
        lines = "\n".join(f"  {k}: {v}" for k, v in asserts.items())
        parts.append(f"assert {{\n{lines}\n}}")
    if post_script:
        lines = "\n".join("  " + line for line in post_script.strip().splitlines())
        parts.append(f"script:post-response {{\n{lines}\n}}")
    if docs:
        parts.append(f"docs {{\n  {docs}\n}}")
    return "\n\n".join(parts) + "\n"


def write(path: str, content: str) -> None:
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


STATION = {
    "sno": "BRUNO0001", "name_zh": "YouBike2.0_Bruno測試站", "name_en": "Bruno Test Sta.", "area_id": "{{areaId}}",
    "address_zh": "測試路1號", "address_en": "No.1, Test Rd.", "latitude": 25.033, "longitude": 121.5654,
    "total_docks": 20, "available_bikes": 8, "available_docks": 12, "is_active": True,
}


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)

    write("bruno.json", json.dumps({
        "version": "1", "name": "YouBike 2.0 Taipei Station API", "type": "collection",
        "ignore": ["node_modules", ".git"],
    }, ensure_ascii=False, indent=2) + "\n")
    write("collection.bru", """meta {
  name: YouBike 2.0 Taipei Station API
}

docs {
  臺北市 YouBike 2.0 站點 Open Data RESTful API 測試集。
  使用前請在 Bruno 右上角選擇環境 local（或 render 雲端環境，自行修改 baseUrl）。
  建議執行順序：Areas → Stations → Stats；各資料夾依序號執行，Create 會把 id 寫入變數供後續請求使用。
  也可在 collection 上按右鍵 → Run 一次跑完所有請求與 assert。
}
""")
    write("environments/local.bru", "vars {\n  baseUrl: http://127.0.0.1:8000\n  api: http://127.0.0.1:8000/api/v1\n}\n")
    write("environments/render.bru",
          "vars {\n  baseUrl: https://youbike-opendata-api.onrender.com\n"
          "  api: https://youbike-opendata-api.onrender.com/api/v1\n}\n")

    write("Health.bru", bru("Health", 1, "get", "{{baseUrl}}/health",
                            asserts={"res.status": "eq 200", "res.body.status": "eq ok"}))

    # ---------- Areas ----------
    write("Areas/folder.bru", "meta {\n  name: Areas\n  seq: 1\n}\n")
    write("Areas/01 List Areas.bru", bru(
        "01 List Areas", 1, "get", "{{api}}/areas", asserts={"res.status": "eq 200"},
        post_script='if (res.getStatus() === 200 && res.getBody().length) {\n  bru.setVar("firstAreaId", res.getBody()[0].id);\n}'))
    write("Areas/02 Create Area.bru", bru(
        "02 Create Area", 2, "post", "{{api}}/areas", body={"name_zh": "Bruno測試區", "name_en": "Bruno Test Dist."},
        asserts={"res.status": "eq 201", "res.body.station_count": "eq 0"},
        post_script='if (res.getStatus() === 201) {\n  bru.setVar("areaId", res.getBody().id);\n}'))
    write("Areas/03 Get Area.bru", bru(
        "03 Get Area", 3, "get", "{{api}}/areas/{{areaId}}",
        asserts={"res.status": "eq 200", "res.body.name_zh": "eq Bruno測試區"}))
    write("Areas/04 Update Area.bru", bru(
        "04 Update Area", 4, "put", "{{api}}/areas/{{areaId}}", body={"name_en": "Bruno Test District (updated)"},
        asserts={"res.status": "eq 200", "res.body.name_en": "eq Bruno Test District (updated)"}))
    write("Areas/05 List Area Stations.bru", bru(
        "05 List Area Stations", 5, "get", "{{api}}/areas/{{firstAreaId}}/stations?limit=5&offset=0",
        query={"limit": 5, "offset": 0}, asserts={"res.status": "eq 200", "res.body.items": "length 5"}))
    write("Areas/06 Delete Area (409 has stations).bru", bru(
        "06 Delete Area (409 has stations)", 6, "delete", "{{api}}/areas/{{firstAreaId}}",
        asserts={"res.status": "eq 409"}))
    write("Areas/07 Delete Area.bru", bru(
        "07 Delete Area", 7, "delete", "{{api}}/areas/{{areaId}}", asserts={"res.status": "eq 204"},
        docs="請先執行 Stations / 12 Delete Station，否則此行政區仍有站點會回 409。"))

    # ---------- Stations ----------
    write("Stations/folder.bru", "meta {\n  name: Stations\n  seq: 2\n}\n")
    write("Stations/01 List Stations.bru", bru(
        "01 List Stations", 1, "get", "{{api}}/stations?limit=5&offset=0&sort=sno&order=asc",
        query={"limit": 5, "offset": 0, "sort": "sno", "order": "asc",
               "~q": "捷運", "~area_id": 1, "~is_active": "true", "~min_bikes": 5, "~min_docks": 5},
        asserts={"res.status": "eq 200", "res.body.items": "length 5"}))
    write("Stations/02 Search Stations.bru", bru(
        "02 Search Stations", 2, "get", "{{api}}/stations?q=捷運&min_bikes=5&sort=available_bikes&order=desc&limit=5",
        query={"q": "捷運", "min_bikes": 5, "sort": "available_bikes", "order": "desc", "limit": 5},
        asserts={"res.status": "eq 200"}))
    write("Stations/03 Nearby Stations.bru", bru(
        "03 Nearby Stations", 3, "get",
        "{{api}}/stations/nearby?lat=25.0418&lng=121.5436&radius=500&limit=5&only_with_bikes=true",
        query={"lat": 25.0418, "lng": 121.5436, "radius": 500, "limit": 5, "only_with_bikes": "true"},
        asserts={"res.status": "eq 200"}))
    write("Stations/04 Get Station.bru", bru(
        "04 Get Station", 4, "get", "{{api}}/stations/500101001",
        asserts={"res.status": "eq 200", "res.body.sno": "eq 500101001"}))
    write("Stations/05 Create Station.bru", bru(
        "05 Create Station", 5, "post", "{{api}}/stations", body=STATION,
        asserts={"res.status": "eq 201", "res.body.sno": "eq BRUNO0001"},
        docs="需先執行 Areas / 02 Create Area 取得 areaId 變數。"))
    write("Stations/06 Create Station (409 duplicate).bru", bru(
        "06 Create Station (409 duplicate)", 6, "post", "{{api}}/stations", body=STATION,
        asserts={"res.status": "eq 409"}))
    write("Stations/07 Create Station (422 invalid).bru", bru(
        "07 Create Station (422 invalid)", 7, "post", "{{api}}/stations",
        body={**STATION, "sno": "BRUNO0002", "latitude": 999}, asserts={"res.status": "eq 422"},
        docs="latitude 超出 -90~90 範圍，Pydantic 驗證失敗回 422。"))
    write("Stations/08 Patch Station.bru", bru(
        "08 Patch Station", 8, "patch", "{{api}}/stations/BRUNO0001",
        body={"is_active": False, "name_zh": "YouBike2.0_Bruno測試站(暫停)"},
        asserts={"res.status": "eq 200", "res.body.is_active": "eq false"}))
    put_body = {k: v for k, v in STATION.items() if k != "sno"}
    put_body.update({"total_docks": 30, "available_docks": 22})
    write("Stations/09 Put Station.bru", bru(
        "09 Put Station", 9, "put", "{{api}}/stations/BRUNO0001", body=put_body,
        asserts={"res.status": "eq 200", "res.body.total_docks": "eq 30"}))
    write("Stations/10 Report Availability.bru", bru(
        "10 Report Availability", 10, "patch", "{{api}}/stations/BRUNO0001/availability",
        body={"available_bikes": 5, "available_docks": 25},
        asserts={"res.status": "eq 200", "res.body.available_bikes": "eq 5"}))
    write("Stations/11 Report Availability (422 overflow).bru", bru(
        "11 Report Availability (422 overflow)", 11, "patch", "{{api}}/stations/BRUNO0001/availability",
        body={"available_bikes": 20, "available_docks": 20}, asserts={"res.status": "eq 422"},
        docs="可借 + 可還 超過總車位 30，回 422。"))
    write("Stations/12 Delete Station.bru", bru(
        "12 Delete Station", 12, "delete", "{{api}}/stations/BRUNO0001", asserts={"res.status": "eq 204"}))
    write("Stations/13 Get Station (404).bru", bru(
        "13 Get Station (404)", 13, "get", "{{api}}/stations/BRUNO0001", asserts={"res.status": "eq 404"}))

    # ---------- Stats ----------
    write("Stats/folder.bru", "meta {\n  name: Stats\n  seq: 3\n}\n")
    write("Stats/01 Summary.bru", bru("01 Summary", 1, "get", "{{api}}/stats/summary", asserts={"res.status": "eq 200"}))
    write("Stats/02 Area Stats.bru", bru("02 Area Stats", 2, "get", "{{api}}/stats/areas", asserts={"res.status": "eq 200"}))
    write("Stats/03 Reload Open Data.bru", bru(
        "03 Reload Open Data", 3, "post", "{{api}}/admin/reload?refresh=false", query={"refresh": "false"},
        asserts={"res.status": "eq 200"},
        docs="refresh=true 會先從臺北市 Open Data 來源重新下載最新即時資料再匯入（upsert）。"))

    print(f"已產生 Bruno collection：{OUT}")
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(OUT))


if __name__ == "__main__":
    main()
