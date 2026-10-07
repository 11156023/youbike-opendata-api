"""ORM 模型：Area（行政區）與 Station（YouBike 站點）。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_zh: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(100))

    stations: Mapped[list["Station"]] = relationship(back_populates="area")


class Station(Base):
    __tablename__ = "stations"

    sno: Mapped[str] = mapped_column(String(20), primary_key=True)  # 站點代號，來源資料的 sno
    name_zh: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(150))
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    address_zh: Mapped[str | None] = mapped_column(String(200))
    address_en: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    total_docks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Quantity
    available_bikes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # available_rent_bikes
    available_docks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # available_return_bikes
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # act
    info_time: Mapped[datetime | None] = mapped_column(DateTime)  # infoTime：站點回報時間
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    area: Mapped["Area"] = relationship(back_populates="stations")
