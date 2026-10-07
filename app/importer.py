"""將 Open Data JSON 匯入 SQLite（供 scripts/import_data.py 與 /admin/reload 共用）。"""
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import models

DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, DT_FORMAT)
    except ValueError:
        return None


def load_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Open Data 格式錯誤：預期為 JSON 陣列")
    return data


def import_records(db: Session, records: list[dict]) -> dict:
    """Upsert 行政區與站點，回傳統計數字。"""
    area_cache: dict[str, models.Area] = {a.name_zh: a for a in db.query(models.Area).all()}
    inserted = updated = 0

    for r in records:
        area_name = (r.get("sarea") or "未分類").strip()
        area = area_cache.get(area_name)
        if area is None:
            area = models.Area(name_zh=area_name, name_en=(r.get("sareaen") or "").strip() or None)
            db.add(area)
            db.flush()  # 取得 id
            area_cache[area_name] = area

        values = dict(
            name_zh=r.get("sna", "").strip(),
            name_en=(r.get("snaen") or "").strip() or None,
            area_id=area.id,
            address_zh=(r.get("ar") or "").strip() or None,
            address_en=(r.get("aren") or "").strip() or None,
            latitude=float(r.get("latitude") or 0),
            longitude=float(r.get("longitude") or 0),
            total_docks=int(r.get("Quantity") or 0),
            available_bikes=int(r.get("available_rent_bikes") or 0),
            available_docks=int(r.get("available_return_bikes") or 0),
            is_active=str(r.get("act", "1")) == "1",
            info_time=parse_dt(r.get("infoTime")),
        )
        sno = str(r["sno"])
        station = db.get(models.Station, sno)
        if station is None:
            db.add(models.Station(sno=sno, **values))
            inserted += 1
        else:
            for k, v in values.items():
                setattr(station, k, v)
            updated += 1

    db.commit()
    return {
        "areas": db.query(models.Area).count(),
        "stations": db.query(models.Station).count(),
        "inserted": inserted,
        "updated": updated,
    }


def import_file(db: Session, path: Path) -> dict:
    result = import_records(db, load_json(path))
    result["source"] = str(path)
    return result
