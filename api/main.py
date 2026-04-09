"""
FastAPI ingestion server.

Start with:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    POST /ingest-facebook       — receives posts (+ optional comments) from the Chrome extension
    GET  /share-prices          — paginated share price table, filterable by date/sector/symbol
    GET  /share-prices/dates    — list of all distinct trade_dates that have data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from sqlalchemy import select, distinct
from sqlalchemy.orm import sessionmaker
from database.social_media_utils import insert_post_with_comments
from database.db import engine
from models.share_price import SharePrice
import os

app = FastAPI(title="AIHub Ingestion API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Serve static dashboard files from api/static/
_static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

Session = sessionmaker(bind=engine)


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class CommentIn(BaseModel):
    text: str
    author: Optional[str] = None
    scraped_at: Optional[str] = None


class PostIn(BaseModel):
    text: str
    author: Optional[str] = None
    reactions: Optional[str] = None
    url: Optional[str] = None
    scraped_at: Optional[str] = None
    comments: list[CommentIn] = []

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v.strip()


class FacebookIngestRequest(BaseModel):
    group: str                  # Group label set by user in the extension popup
    posts: list[PostIn]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@app.post("/ingest-facebook")
def ingest_facebook(payload: FacebookIngestRequest):
    if not payload.posts:
        raise HTTPException(status_code=400, detail="No posts provided.")

    inserted = 0
    skipped  = 0

    for post in payload.posts:
        post_dict = post.model_dump()
        post_dict["group"] = payload.group

        post_id = insert_post_with_comments(post_dict)
        if post_id is not None:
            inserted += 1
        else:
            skipped += 1

    return {
        "status": "ok",
        "group": payload.group,
        "received": len(payload.posts),
        "inserted": inserted,
        "skipped": skipped,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def _to_float(v):
    """Safely cast a value (Numeric or text) to float, returning None on failure."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Share prices dashboard
# ---------------------------------------------------------------------------

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(_static_dir, "share_prices.html"))


@app.get("/share-prices/dates")
def share_price_dates():
    """Return all distinct trade_dates that have data, newest first."""
    session = Session()
    try:
        rows = session.execute(
            select(distinct(SharePrice.trade_date)).order_by(SharePrice.trade_date.desc())
        ).scalars().all()
        return [str(d) for d in rows]
    finally:
        session.close()


@app.get("/share-prices")
def share_prices(
    date:   Optional[str] = Query(None, description="trade_date filter YYYY-MM-DD"),
    sector: Optional[str] = Query(None, description="Sector filter (partial match)"),
    symbol: Optional[str] = Query(None, description="Symbol filter (partial match)"),
):
    session = Session()
    try:
        stmt = select(SharePrice).order_by(SharePrice.trade_date.desc(), SharePrice.symbol)

        if date:
            stmt = stmt.where(SharePrice.trade_date == date)
        if sector:
            stmt = stmt.where(SharePrice.sector.ilike(f"%{sector}%"))
        if symbol:
            stmt = stmt.where(SharePrice.symbol.ilike(f"%{symbol}%"))

        rows = session.execute(stmt).scalars().all()
        return [
            {
                "id":                       r.id,
                "symbol":                   r.symbol,
                "trade_date":               str(r.trade_date),
                "ltp":                      _to_float(r.ltp),
                "change_percent":           _to_float(r.change_percent),
                "sector":                   r.sector,
                "quality":                  r.quality,
                "stars":                    r.stars,
                "pe":                       _to_float(r.pe),
                "pb":                       _to_float(r.pb),
                "roe":                      _to_float(r.roe),
                "roa":                      _to_float(r.roa),
                "graham_distance":          _to_float(r.graham_distance),
                "dividend_yield":           _to_float(r.dividend_yield),
                "pe_vs_sector":             r.pe_vs_sector,
                "pb_vs_sector":             r.pb_vs_sector,
                "roe_vs_sector":            r.roe_vs_sector,
            }
            for r in rows
        ]
    finally:
        session.close()
