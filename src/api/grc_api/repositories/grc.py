"""Measured values of KPI."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import KpiMeasurement


async def measurements(db: AsyncSession, kpi_id: str) -> list[KpiMeasurement]:
    stmt = select(KpiMeasurement).where(KpiMeasurement.kpi_id == kpi_id)
    return list((await db.execute(stmt.order_by(KpiMeasurement.date))).scalars())


async def measurement_at(db: AsyncSession, kpi_id: str, day: date) -> KpiMeasurement | None:
    stmt = select(KpiMeasurement).where(KpiMeasurement.kpi_id == kpi_id, KpiMeasurement.date == day)
    return (await db.execute(stmt)).scalar_one_or_none()


async def last_values(db: AsyncSession) -> dict[str, float]:
    """kpi id → latest measured value."""
    out: dict[str, float] = {}
    for m in (await db.execute(select(KpiMeasurement).order_by(KpiMeasurement.date))).scalars():
        out[m.kpi_id] = m.value
    return out
