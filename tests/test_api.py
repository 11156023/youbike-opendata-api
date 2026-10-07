"""API 整合測試：涵蓋 Areas / Stations / Stats 的 CRUD 與錯誤處理。"""
API = "/api/v1"


# ---------- Health / Docs ----------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_available(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


# ---------- Areas ----------
def test_list_areas_seeded(client):
    r = client.get(f"{API}/areas")
    assert r.status_code == 200
    areas = r.json()
    assert len(areas) >= 12
    assert any(a["name_zh"] == "大安區" for a in areas)
    assert all(a["station_count"] > 0 for a in areas)


def test_area_crud(client):
    # Create
    r = client.post(f"{API}/areas", json={"name_zh": "測試區", "name_en": "Test Dist."})
    assert r.status_code == 201
    area = r.json()
    assert area["station_count"] == 0
    aid = area["id"]

    # Duplicate -> 409
    assert client.post(f"{API}/areas", json={"name_zh": "測試區"}).status_code == 409

    # Read
    assert client.get(f"{API}/areas/{aid}").json()["name_en"] == "Test Dist."

    # Update
    r = client.put(f"{API}/areas/{aid}", json={"name_en": "Testing District"})
    assert r.status_code == 200 and r.json()["name_en"] == "Testing District"

    # Delete
    assert client.delete(f"{API}/areas/{aid}").status_code == 204
    assert client.get(f"{API}/areas/{aid}").status_code == 404


def test_delete_area_with_stations_conflict(client):
    aid = client.get(f"{API}/areas").json()[0]["id"]
    assert client.delete(f"{API}/areas/{aid}").status_code == 409


def test_area_stations(client):
    aid = client.get(f"{API}/areas").json()[0]["id"]
    r = client.get(f"{API}/areas/{aid}/stations", params={"limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0 and len(body["items"]) == 5
    assert all(s["area_id"] == aid for s in body["items"])


# ---------- Stations ----------
def test_list_stations_pagination_and_filter(client):
    r = client.get(f"{API}/stations", params={"limit": 10, "offset": 0})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1800 and len(body["items"]) == 10

    r = client.get(f"{API}/stations", params={"q": "捷運", "limit": 3})
    assert all("捷運" in s["name_zh"] or "捷運" in (s["address_zh"] or "") for s in r.json()["items"])

    r = client.get(f"{API}/stations", params={"min_bikes": 5, "sort": "available_bikes", "order": "desc", "limit": 5})
    bikes = [s["available_bikes"] for s in r.json()["items"]]
    assert bikes == sorted(bikes, reverse=True) and all(b >= 5 for b in bikes)


def test_list_stations_invalid_sort(client):
    assert client.get(f"{API}/stations", params={"sort": "bogus"}).status_code == 422


def test_nearby(client):
    # 捷運科技大樓站附近
    r = client.get(f"{API}/stations/nearby", params={"lat": 25.02605, "lng": 121.5436, "radius": 500, "limit": 5})
    assert r.status_code == 200
    items = r.json()
    assert 0 < len(items) <= 5
    assert items[0]["distance_m"] < 50  # 最近的就是那一站
    assert all(items[i]["distance_m"] <= items[i + 1]["distance_m"] for i in range(len(items) - 1))


def test_station_crud(client):
    aid = client.get(f"{API}/areas").json()[0]["id"]
    payload = {
        "sno": "TEST0001", "name_zh": "YouBike2.0_測試站", "name_en": "Test Sta.", "area_id": aid,
        "address_zh": "測試路1號", "latitude": 25.0, "longitude": 121.5,
        "total_docks": 20, "available_bikes": 8, "available_docks": 12, "is_active": True,
    }
    # Create
    r = client.post(f"{API}/stations", json=payload)
    assert r.status_code == 201
    assert r.json()["area_name"]
    # Duplicate -> 409
    assert client.post(f"{API}/stations", json=payload).status_code == 409
    # Bad area -> 422
    assert client.post(f"{API}/stations", json={**payload, "sno": "TEST0002", "area_id": 999999}).status_code == 422

    # Read
    assert client.get(f"{API}/stations/TEST0001").json()["name_zh"] == "YouBike2.0_測試站"

    # PATCH
    r = client.patch(f"{API}/stations/TEST0001", json={"is_active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False

    # PUT（完整替換，未提供的 optional 欄位變 null）
    put_body = {k: v for k, v in payload.items() if k != "sno"}
    put_body.update({"name_en": None, "total_docks": 30, "available_bikes": 10, "available_docks": 20})
    r = client.put(f"{API}/stations/TEST0001", json=put_body)
    assert r.status_code == 200
    assert r.json()["total_docks"] == 30 and r.json()["name_en"] is None and r.json()["is_active"] is True

    # Availability report
    r = client.patch(f"{API}/stations/TEST0001/availability", json={"available_bikes": 3, "available_docks": 27})
    assert r.status_code == 200 and r.json()["available_bikes"] == 3 and r.json()["info_time"]
    # 超過總車位 -> 422
    r = client.patch(f"{API}/stations/TEST0001/availability", json={"available_bikes": 20, "available_docks": 20})
    assert r.status_code == 422

    # Delete
    assert client.delete(f"{API}/stations/TEST0001").status_code == 204
    assert client.get(f"{API}/stations/TEST0001").status_code == 404
    assert client.delete(f"{API}/stations/TEST0001").status_code == 404


def test_station_validation(client):
    r = client.post(f"{API}/stations", json={"sno": "X", "name_zh": "x", "area_id": 1, "latitude": 999, "longitude": 0,
                                             "total_docks": 1, "available_bikes": 0, "available_docks": 0})
    assert r.status_code == 422


# ---------- Stats / Admin ----------
def test_stats(client):
    r = client.get(f"{API}/stats/summary")
    assert r.status_code == 200
    s = r.json()
    assert s["station_count"] >= 1800 and 0 <= s["bike_ratio"] <= 1

    r = client.get(f"{API}/stats/areas")
    assert r.status_code == 200
    assert sum(a["station_count"] for a in r.json()) == s["station_count"]


def test_admin_reload(client):
    r = client.post(f"{API}/admin/reload")
    assert r.status_code == 200
    body = r.json()
    assert body["inserted"] == 0 and body["updated"] >= 1800
