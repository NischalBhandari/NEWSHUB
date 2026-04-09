from sqlalchemy import Column, Integer, Text, Numeric, TIMESTAMP, UniqueConstraint
from datetime import datetime, timezone
from .base import Base


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"

    id          = Column(Integer, primary_key=True)
    indicator   = Column(Text, nullable=False)   # e.g. "GDP Growth Rate", "Inflation Rate"
    category    = Column(Text)                   # e.g. "GDP", "Labour", "Trade", "Prices"
    value       = Column(Numeric)                # most recent value
    previous    = Column(Numeric)                # previous period value
    highest     = Column(Numeric)                # historical maximum
    lowest      = Column(Numeric)                # historical minimum
    unit        = Column(Text)                   # e.g. "%", "NPR Million", "USD"
    reference   = Column(Text)                   # raw reference string e.g. "Dec/24"
    year        = Column(Integer)                # extracted year e.g. 2024
    month       = Column(Integer, nullable=True) # extracted month 1–12, null if annual/quarterly
    country     = Column(Text, default="Nepal")
    source      = Column(Text)
    created_at  = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # one row per indicator per period per country — updates replace via upsert
        UniqueConstraint("indicator", "year", "month", "country", name="uq_indicator_period_country"),
    )
