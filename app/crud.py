"""資料存取層：封裝所有 SQLAlchemy 查詢，讓 router 保持精簡。"""
import math
from datetime import datetime

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from app import models, schemas


# ---------- Area ----------
def list_areas(db: Session) -> list[tuple[models.Area, int]]:
    stmt = (
        select(models.Area, func.count(models.Station.sno))
        .outerjoin(models.Station)
        .group_by(models.Area.id)
        .order_by(models.Area.id)
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def get_area(db: Session, area_id: int) -> models.Area | None:
    return db.get(models.Area, area_id)


def get_area_by_name(db: Session, name_zh: str) -> models.Area | None:
    return db.scalar(select(models.Area).where(models.Area.name_zh == name_zh))


def station_count_of_area(db: Session, area_id: int) -> int:
    return db.scalar(select(func.count(models.Station.sno)).where(models.Station.area_id == area_id)) or 0


def create_area(db: Session, data: schemas.AreaCreate) -> models.Area:
    area = models.Area(**data.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def update_area(db: Session, area: models.Area, data: schemas.AreaUpdate) -> models.Area:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(area, k, v)
    db.commit()
    db.refresh(area)
    return area


def delete_area(db: Session, area: models.Area) -> None:
    db.delete(area)
    db.commit()


# ---------- Station ----------
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


SORTABLE = {
    "sno": models.Station.sno,
    "name_zh": models.Station.name_zh,
    "available_bikes": models.Station.available_bikes,
    "available_docks": models.Station.available_docks,
    "total_docks": models.Station.total_docks,
    "updated_at": models.Station.updated_at,
}


def list_stations(
    db: Session,
    *,
    q: str | None = None,
    area_id: int | None = None,
    is_active: bool | None = None,
    min_bikes: int | None = None,
    min_docks: int | None = None,
    sort: str = "sno",
    order: str = "asc",
    limit: int = 20,
    offset: int = 0,
) -> tuple[int, list[models.Station]]:
    stmt = select(models.Station)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            models.Station.name_zh.ilike(like)
            | models.Station.name_en.ilike(like)
            | models.Station.address_zh.ilike(like)
        )
    if area_id is not None:
        stmt = stmt.where(models.Station.area_id == area_id)
    if is_active is not None:
        stmt = stmt.where(models.Station.is_active == is_active)
    if min_bikes is not None:
        stmt = stmt.where(models.Station.available_bikes >= min_bikes)
    if min_docks is not None:
        stmt = stmt.where(models.Station.available_docks >= min_docks)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    col = SORTABLE.get(sort, models.Station.sno)
    stmt = stmt.order_by(col.desc() if order == "desc" else col.asc()).limit(limit).offset(offset)
    return total, list(db.scalars(stmt).all())


def nearby_stations(
    db: Session, lat: float, lng: float, radius_m: float, limit: int, only_with_bikes: bool
) -> list[tuple[models.Station, float]]:
    # 先用經緯度方框粗略篩選，再用 Haversine 精算距離
    dlat = radius_m / 111_000
    dlng = radius_m / (111_000 * max(math.cos(math.radians(lat)), 0.01))
    stmt = select(models.Station).where(
        models.Station.latitude.between(lat - dlat, lat + dlat),
        models.Station.longitude.between(lng - dlng, lng + dlng),
    )
    if only_with_bikes:
        stmt = stmt.where(models.Station.available_bikes > 0, models.Station.is_active.is_(True))
    result = []
    for s in db.scalars(stmt):
        d = _haversine_m(lat, lng, s.latitude, s.longitude)
        if d <= radius_m:
            result.append((s, round(d, 1)))
    result.sort(key=lambda t: t[1])
    return result[:limit]


def get_station(db: Session, sno: str) -> models.Station | None:
    return db.get(models.Station, sno)


def create_station(db: Session, data: schemas.StationCreate) -> models.Station:
    station = models.Station(**data.model_dump())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


def update_station(db: Session, station: models.Station, data: schemas.StationUpdate, partial: bool) -> models.Station:
    payload = data.model_dump(exclude_unset=partial)
    for k, v in payload.items():
        setattr(station, k, v)
    db.commit()
    db.refresh(station)
    return station


def update_availability(db: Session, station: models.Station, data: schemas.AvailabilityUpdate) -> models.Station:
    station.available_bikes = data.available_bikes
    station.available_docks = data.available_docks
    station.info_time = data.info_time or datetime.now()
    db.commit()
    db.refresh(station)
    return station


def delete_station(db: Session, station: models.Station) -> None:
    db.delete(station)
    db.commit()


# ---------- Stats ----------
def summary_stats(db: Session) -> dict:
    s = models.Station
    row = db.execute(
        select(
            func.count(s.sno),
            func.coalesce(func.sum(func.cast(s.is_active, Integer)), 0),
            func.coalesce(func.sum(s.total_docks), 0),
            func.coalesce(func.sum(s.available_bikes), 0),
            func.coalesce(func.sum(s.available_docks), 0),
            func.coalesce(func.sum(func.cast(s.available_bikes == 0, Integer)), 0),
            func.coalesce(func.sum(func.cast(s.available_docks == 0, Integer)), 0),
            func.max(s.info_time),
        )
    ).one()
    count, active, docks, bikes, free, empty, full, last = row
    return dict(
        area_count=db.scalar(select(func.count(models.Area.id))) or 0,
        station_count=count,
        active_station_count=active,
        total_docks=docks,
        available_bikes=bikes,
        available_docks=free,
        bike_ratio=round(bikes / docks, 4) if docks else 0.0,
        empty_stations=empty,
        full_stations=full,
        last_info_time=last,
    )


def area_stats(db: Session) -> list[dict]:
    s, a = models.Station, models.Area
    rows = db.execute(
        select(
            a.id,
            a.name_zh,
            func.count(s.sno),
            func.coalesce(func.sum(func.cast(s.is_active, Integer)), 0),
            func.coalesce(func.sum(s.total_docks), 0),
            func.coalesce(func.sum(s.available_bikes), 0),
            func.coalesce(func.sum(s.available_docks), 0),
        )
        .outerjoin(s)
        .group_by(a.id)
        .order_by(a.id)
    ).all()
    return [
        dict(
            area_id=r[0], area_name=r[1], station_count=r[2], active_station_count=r[3],
            total_docks=r[4], available_bikes=r[5], available_docks=r[6],
            bike_ratio=round(r[5] / r[4], 4) if r[4] else 0.0,
        )
        for r in rows
    ]
