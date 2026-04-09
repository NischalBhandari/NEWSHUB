from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.db import engine
from sqlalchemy.orm import sessionmaker
from models.economic_indicator import EconomicIndicator

Session = sessionmaker(bind=engine)


def upsert_indicators(rows: list[dict]):
    """Insert or update economic indicators.

    On conflict (same indicator + year + month + country), updates all value
    columns so re-running the scraper always reflects the latest published data.
    """
    if not rows:
        return

    # Deduplicate within the batch — same indicator+year+month+country appearing
    # in multiple category sections would cause a CardinalityViolation. Last one wins.
    seen = {}
    for row in rows:
        key = (row["indicator"], row.get("year"), row.get("month"), row.get("country"))
        seen[key] = row
    rows = list(seen.values())

    session = Session()
    try:
        stmt = pg_insert(EconomicIndicator).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_indicator_period_country",
            set_={
                "value":     stmt.excluded.value,
                "previous":  stmt.excluded.previous,
                "highest":   stmt.excluded.highest,
                "lowest":    stmt.excluded.lowest,
                "unit":      stmt.excluded.unit,
                "reference": stmt.excluded.reference,
                "category":  stmt.excluded.category,
                "source":    stmt.excluded.source,
            },
        )
        session.execute(stmt)
        session.commit()
        print(f"Upserted {len(rows)} economic indicators.")
    except Exception as e:
        session.rollback()
        print("Error upserting indicators:", e)
    finally:
        session.close()
