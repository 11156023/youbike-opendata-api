"""Pydantic schemas：定義 API 的輸入 / 輸出資料格式（同時產生 Swagger 文件）。"""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ---------- 共用 ----------
class Page(BaseModel, Generic[T]):
    """分頁回應格式。"""
    total: int = Field(description="符合條件的總筆數")
    limit: int
    offset: int
    items: list[T]


class Message(BaseModel):
    detail: str


# ---------- Area ----------
class AreaBase(BaseModel):
    name_zh: str = Field(min_length=1, max_length=50, examples=["大安區"])
    name_en: str | None = Field(default=None, max_length=100, examples=["Daan Dist."])


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    name_zh: str | None = Field(default=None, min_length=1, max_length=50)
    name_en: str | None = Field(default=None, max_length=100)


class AreaOut(AreaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_count: int = Field(default=0, description="該行政區站點數")


# ---------- Station ----------
class StationBase(BaseModel):
    name_zh: str = Field(min_length=1, max_length=100, examples=["YouBike2.0_捷運科技大樓站"])
    name_en: str | None = Field(default=None, max_length=150, examples=["YouBike2.0_MRT Technology Bldg. Sta."])
    area_id: int = Field(description="所屬行政區 id（參考 /areas）", examples=[1])
    address_zh: str | None = Field(default=None, max_length=200, examples=["復興南路二段235號前"])
    address_en: str | None = Field(default=None, max_length=200, examples=["No.235， Sec. 2， Fuxing S. Rd."])
    latitude: float = Field(ge=-90, le=90, examples=[25.02605])
    longitude: float = Field(ge=-180, le=180, examples=[121.5436])
    total_docks: int = Field(ge=0, description="總車位數", examples=[28])
    available_bikes: int = Field(ge=0, description="可借車輛數", examples=[5])
    available_docks: int = Field(ge=0, description="可還空位數", examples=[22])
    is_active: bool = Field(default=True, description="站點是否營運中")
    info_time: datetime | None = Field(default=None, description="站點資料回報時間")


class StationCreate(StationBase):
    sno: str = Field(min_length=1, max_length=20, description="站點代號（主鍵）", examples=["500199999"])


class StationUpdate(BaseModel):
    """PUT / PATCH 共用；所有欄位皆可省略。"""
    name_zh: str | None = Field(default=None, min_length=1, max_length=100)
    name_en: str | None = Field(default=None, max_length=150)
    area_id: int | None = None
    address_zh: str | None = Field(default=None, max_length=200)
    address_en: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    total_docks: int | None = Field(default=None, ge=0)
    available_bikes: int | None = Field(default=None, ge=0)
    available_docks: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    info_time: datetime | None = None


class AvailabilityUpdate(BaseModel):
    """即時車況回報（模擬站點 IoT 裝置上傳）。"""
    available_bikes: int = Field(ge=0, examples=[12])
    available_docks: int = Field(ge=0, examples=[16])
    info_time: datetime | None = Field(default=None, description="未提供則使用伺服器時間")


class StationOut(StationBase):
    model_config = ConfigDict(from_attributes=True)
    sno: str
    area_name: str = Field(description="行政區中文名稱")
    updated_at: datetime


class StationNearbyOut(StationOut):
    distance_m: float = Field(description="與查詢座標的距離（公尺）")


# ---------- Stats ----------
class AreaStats(BaseModel):
    area_id: int
    area_name: str
    station_count: int
    active_station_count: int
    total_docks: int
    available_bikes: int
    available_docks: int
    bike_ratio: float = Field(description="可借車輛 / 總車位")


class SummaryStats(BaseModel):
    area_count: int
    station_count: int
    active_station_count: int
    total_docks: int
    available_bikes: int
    available_docks: int
    bike_ratio: float
    empty_stations: int = Field(description="無車可借的站點數")
    full_stations: int = Field(description="無位可還的站點數")
    last_info_time: datetime | None


class ReloadResult(BaseModel):
    source: str
    areas: int
    stations: int
    inserted: int
    updated: int
