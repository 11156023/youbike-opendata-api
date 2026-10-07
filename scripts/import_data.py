"""將 Open Data JSON 匯入 SQLite。

用法：
    python scripts/import_data.py              # 匯入 data/youbike_stations.json
    python scripts/import_data.py --refresh    # 先從 Open Data 來源重新下載再匯入
    python scripts/import_data.py --reset      # 先清空資料庫再匯入
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import importer, models  # noqa: E402,F401
from app.config import DATA_FILE, OPEN_DATA_URL  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402


def download() -> None:
    import requests

    print(f"下載 Open Data：{OPEN_DATA_URL}")
    resp = requests.get(OPEN_DATA_URL, timeout=30)
    resp.raise_for_status()
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_bytes(resp.content)
    print(f"已儲存至 {DATA_FILE}（{len(resp.content):,} bytes）")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="先重新下載 Open Data")
    parser.add_argument("--reset", action="store_true", help="先刪除所有資料表再匯入")
    args = parser.parse_args()

    if args.refresh:
        download()
    if args.reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        result = importer.import_file(db, DATA_FILE)
    print(f"匯入完成：行政區 {result['areas']} 筆、站點 {result['stations']} 筆 "
          f"（新增 {result['inserted']}、更新 {result['updated']}）")


if __name__ == "__main__":
    main()
