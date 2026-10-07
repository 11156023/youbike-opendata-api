"""統計與管理端點：全市摘要、各行政區統計、重新匯入 Open Data。"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, importer, schemas
from app.config import DATA_FILE, OPEN_DATA_URL
from app.database import get_db

router = APIRouter(tags=["Stats & Admin"])


@router.get("/stats/summary", response_model=schemas.SummaryStats, summary="全市車況摘要")
def summary(db: Session = Depends(get_db)):
    return crud.summary_stats(db)


@router.get("/stats/areas", response_model=list[schemas.AreaStats], summary="各行政區車況統計")
def by_area(db: Session = Depends(get_db)):
    return crud.area_stats(db)


@router.post("/admin/reload", response_model=schemas.ReloadResult, summary="重新匯入 Open Data（upsert）",
             responses={502: {"model": schemas.Message}})
def reload_data(
    refresh: bool = Query(False, description="true：先從臺北市 Open Data 來源重新下載並覆寫本地資料檔"),
    db: Session = Depends(get_db),
):
    if refresh:
        try:
            import requests

            resp = requests.get(OPEN_DATA_URL, timeout=30)
            resp.raise_for_status()
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_bytes(resp.content)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"下載 Open Data 失敗：{exc}") from exc
    if not DATA_FILE.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"資料檔不存在：{DATA_FILE}")
    return importer.import_file(db, DATA_FILE)
