from datetime import date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select
from database.db import engine
from models.share_price import SharePrice, MarketCalendar

Session = sessionmaker(bind=engine)


# ---------------------------------------------------------------------------
# Market calendar
# ---------------------------------------------------------------------------

def get_calendar_entry(trade_date: date) -> MarketCalendar | None:
    session = Session()
    try:
        return session.get(MarketCalendar, trade_date)
    finally:
        session.close()


def mark_trading_day(trade_date: date):
    """Record that NEPSE was open on this date."""
    _upsert_calendar(trade_date, is_trading_day=True, holiday_name=None)


def mark_holiday(trade_date: date, holiday_name: str):
    """Record that NEPSE was closed on this date and why."""
    _upsert_calendar(trade_date, is_trading_day=False, holiday_name=holiday_name)


def _upsert_calendar(trade_date: date, is_trading_day: bool, holiday_name: str | None):
    session = Session()
    try:
        stmt = (
            pg_insert(MarketCalendar)
            .values(date=trade_date, is_trading_day=is_trading_day, holiday_name=holiday_name)
            .on_conflict_do_update(
                index_elements=["date"],
                set_={"is_trading_day": is_trading_day, "holiday_name": holiday_name},
            )
        )
        session.execute(stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating market calendar for {trade_date}: {e}")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Share prices
# ---------------------------------------------------------------------------

def upsert_share_prices(rows: list[dict]):
    """Batch upsert share prices. On duplicate (symbol, trade_date) updates price fields."""
    if not rows:
        return

    session = Session()
    try:
        stmt = pg_insert(SharePrice).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_share_price_symbol_date",
            set_={
                "ltp":                      stmt.excluded.ltp,
                "change_percent":           stmt.excluded.change_percent,
                "quality":                  stmt.excluded.quality,
                "stars":                    stmt.excluded.stars,
                "sector":                   stmt.excluded.sector,
                "pe":                       stmt.excluded.pe,
                "pb":                       stmt.excluded.pb,
                "roe":                      stmt.excluded.roe,
                "roa":                      stmt.excluded.roa,
                "peg":                      stmt.excluded.peg,
                "graham_distance":          stmt.excluded.graham_distance,
                "dividend_yield":           stmt.excluded.dividend_yield,
                "payout_ratio":             stmt.excluded.payout_ratio,
                "pe_vs_sector":             stmt.excluded.pe_vs_sector,
                "pb_vs_sector":             stmt.excluded.pb_vs_sector,
                "peg_vs_sector":            stmt.excluded.peg_vs_sector,
                "dividend_yield_vs_sector": stmt.excluded.dividend_yield_vs_sector,
                "roe_vs_sector":            stmt.excluded.roe_vs_sector,
                "yoy_growth_vs_sector":     stmt.excluded.yoy_growth_vs_sector,
                "qoq_growth_vs_sector":     stmt.excluded.qoq_growth_vs_sector,
                "roa_vs_sector":            stmt.excluded.roa_vs_sector,
            },
        )
        session.execute(stmt)
        session.commit()
        print(f"Upserted {len(rows)} share price records for {rows[0]['trade_date']}.")
    except Exception as e:
        session.rollback()
        print(f"Error upserting share prices: {e}")
    finally:
        session.close()
