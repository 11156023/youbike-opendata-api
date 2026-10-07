"""Station（YouBike 站點）Resource：CRUD + 搜尋 / 附近站點 / 即時車況回報。"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.routers.areas import station_out

router = APIRouter(prefix="/stations", tags=["Stations"])


def _get_or_404(db: Session, sno: str):
    station = crud.get_station(db, sno)
    if not station:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到站點 sno={sno}")
    return station


def _check_area(db: Session, area_id: int | None):
    if area_id is not None and not crud.get_area(db, area_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"行政區 id={area_id} 不存在")


@router.get("", response_model=schemas.Page[schemas.StationOut], summary="搜尋 / 列出站點（分頁）")
def list_stations(
    q: str | None = Query(None, description="關鍵字（站名、英文站名、地址模糊比對）", examples=["捷運"]),
    area_id: int | None = Query(None, description="行政區 id"),
    is_active: bool | None = Query(None, description="是否營運中"),
    min_bikes: int | None = Query(None, ge=0, description="可借車輛數下限"),
    min_docks: int | None = Query(None, ge=0, description="可還空位數下限"),
    sort: Literal["sno", "name_zh", "available_bikes", "available_docks", "total_docks", "updated_at"] = "sno",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = crud.list_stations(
        db, q=q, area_id=area_id, is_active=is_active, min_bikes=min_bikes, min_docks=min_docks,
        sort=sort, order=order, limit=limit, offset=offset,
    )
    return schemas.Page(total=total, limit=limit, offset=offset, items=[station_out(s) for s in items])


@router.get("/nearby", response_model=list[schemas.StationNearbyOut], summary="查詢座標附近的站點")
def nearby(
    lat: float = Query(..., ge=-90, le=90, examples=[25.0418]),
    lng: float = Query(..., ge=-180, le=180, examples=[121.5436]),
    radius: float = Query(500, gt=0, le=5000, description="半徑（公尺）"),
    limit: int = Query(10, ge=1, le=100),
    only_with_bikes: bool = Query(False, description="只回傳目前有車可借的營運站點"),
    db: Session = Depends(get_db),
):
    rows = crud.nearby_stations(db, lat, lng, radius, limit, only_with_bikes)
    return [schemas.StationNearbyOut(**station_out(s).model_dump(), distance_m=d) for s, d in rows]


@router.post("", response_model=schemas.StationOut, status_code=status.HTTP_201_CREATED, summary="新增站點",
             responses={409: {"model": schemas.Message, "description": "sno 重複"}, 422: {"model": schemas.Message}})
def create_station(data: schemas.StationCreate, db: Session = Depends(get_db)):
    if crud.get_station(db, data.sno):
        raise HTTPException(status.HTTP_409_CONFLICT, f"站點 sno={data.sno} 已存在")
    _check_area(db, data.area_id)
    return station_out(crud.create_station(db, data))


@router.get("/{sno}", response_model=schemas.StationOut, summary="取得單一站點",
            responses={404: {"model": schemas.Message}})
def get_station(sno: str, db: Session = Depends(get_db)):
    return station_out(_get_or_404(db, sno))


@router.put("/{sno}", response_model=schemas.StationOut, summary="完整更新站點（PUT）",
            responses={404: {"model": schemas.Message}, 422: {"model": schemas.Message}})
def replace_station(sno: str, data: schemas.StationBase, db: Session = Depends(get_db)):
    station = _get_or_404(db, sno)
    _check_area(db, data.area_id)
    update = schemas.StationUpdate(**data.model_dump())
    return station_out(crud.update_station(db, station, update, partial=False))


@router.patch("/{sno}", response_model=schemas.StationOut, summary="部分更新站點（PATCH）",
              responses={404: {"model": schemas.Message}, 422: {"model": schemas.Message}})
def patch_station(sno: str, data: schemas.StationUpdate, db: Session = Depends(get_db)):
    station = _get_or_404(db, sno)
    _check_area(db, data.area_id)
    return station_out(crud.update_station(db, station, data, partial=True))


@router.patch("/{sno}/availability", response_model=schemas.StationOut, summary="回報即時車況（可借 / 可還）",
              responses={404: {"model": schemas.Message}, 422: {"model": schemas.Message}})
def report_availability(sno: str, data: schemas.AvailabilityUpdate, db: Session = Depends(get_db)):
    station = _get_or_404(db, sno)
    if data.available_bikes + data.available_docks > station.total_docks:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"可借 + 可還 ({data.available_bikes + data.available_docks}) 超過總車位 {station.total_docks}",
        )
    return station_out(crud.update_availability(db, station, data))


@router.delete("/{sno}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除站點",
               responses={404: {"model": schemas.Message}})
def delete_station(sno: str, db: Session = Depends(get_db)):
    crud.delete_station(db, _get_or_404(db, sno))
