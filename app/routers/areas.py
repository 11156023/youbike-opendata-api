"""Area（行政區）Resource：CRUD。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/areas", tags=["Areas"])


def _to_out(area, count: int) -> schemas.AreaOut:
    return schemas.AreaOut(id=area.id, name_zh=area.name_zh, name_en=area.name_en, station_count=count)


@router.get("", response_model=list[schemas.AreaOut], summary="列出所有行政區")
def list_areas(db: Session = Depends(get_db)):
    return [_to_out(a, c) for a, c in crud.list_areas(db)]


@router.post("", response_model=schemas.AreaOut, status_code=status.HTTP_201_CREATED, summary="新增行政區",
             responses={409: {"model": schemas.Message, "description": "名稱重複"}})
def create_area(data: schemas.AreaCreate, db: Session = Depends(get_db)):
    if crud.get_area_by_name(db, data.name_zh):
        raise HTTPException(status.HTTP_409_CONFLICT, f"行政區 '{data.name_zh}' 已存在")
    area = crud.create_area(db, data)
    return _to_out(area, 0)


@router.get("/{area_id}", response_model=schemas.AreaOut, summary="取得單一行政區",
            responses={404: {"model": schemas.Message}})
def get_area(area_id: int, db: Session = Depends(get_db)):
    area = crud.get_area(db, area_id)
    if not area:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到行政區 id={area_id}")
    return _to_out(area, crud.station_count_of_area(db, area_id))


@router.put("/{area_id}", response_model=schemas.AreaOut, summary="更新行政區",
            responses={404: {"model": schemas.Message}, 409: {"model": schemas.Message}})
def update_area(area_id: int, data: schemas.AreaUpdate, db: Session = Depends(get_db)):
    area = crud.get_area(db, area_id)
    if not area:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到行政區 id={area_id}")
    if data.name_zh and data.name_zh != area.name_zh and crud.get_area_by_name(db, data.name_zh):
        raise HTTPException(status.HTTP_409_CONFLICT, f"行政區 '{data.name_zh}' 已存在")
    area = crud.update_area(db, area, data)
    return _to_out(area, crud.station_count_of_area(db, area_id))


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除行政區",
               responses={404: {"model": schemas.Message}, 409: {"model": schemas.Message}})
def delete_area(area_id: int, db: Session = Depends(get_db)):
    area = crud.get_area(db, area_id)
    if not area:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到行政區 id={area_id}")
    count = crud.station_count_of_area(db, area_id)
    if count:
        raise HTTPException(status.HTTP_409_CONFLICT, f"行政區仍有 {count} 個站點，請先刪除或移轉站點")
    crud.delete_area(db, area)


@router.get("/{area_id}/stations", response_model=schemas.Page[schemas.StationOut], summary="列出行政區內的站點",
            responses={404: {"model": schemas.Message}})
def list_area_stations(area_id: int, limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    if not crud.get_area(db, area_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到行政區 id={area_id}")
    total, items = crud.list_stations(db, area_id=area_id, limit=limit, offset=offset)
    return schemas.Page(total=total, limit=limit, offset=offset, items=[station_out(s) for s in items])


def station_out(s) -> schemas.StationOut:
    """共用轉換：ORM Station -> StationOut（補上 area_name）。"""
    return schemas.StationOut(
        sno=s.sno, name_zh=s.name_zh, name_en=s.name_en, area_id=s.area_id, area_name=s.area.name_zh,
        address_zh=s.address_zh, address_en=s.address_en, latitude=s.latitude, longitude=s.longitude,
        total_docks=s.total_docks, available_bikes=s.available_bikes, available_docks=s.available_docks,
        is_active=s.is_active, info_time=s.info_time, updated_at=s.updated_at,
    )
