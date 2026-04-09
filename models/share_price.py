from sqlalchemy import Column, Integer, Text, Numeric, Date, Boolean, TIMESTAMP, UniqueConstraint
from datetime import datetime, timezone
from .base import Base


class MarketCalendar(Base):
    """One row per calendar date. Tracks whether NEPSE was open or closed that day."""
    __tablename__ = "market_calendar"

    date           = Column(Date, primary_key=True)
    is_trading_day = Column(Boolean, nullable=False)
    holiday_name   = Column(Text, nullable=True)   # e.g. "Dashain", "Saturday", "Public Holiday"
    created_at     = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))


class SharePrice(Base):
    """
    Daily fundamental + price snapshot per symbol.
    Join to the stock table via: JOIN stock ON share_prices.symbol = stock.symbol

    Column source: https://nepsealpha.com/trading-signals/funda (22 columns)
    """
    __tablename__ = "share_prices"

    id           = Column(Integer, primary_key=True)
    symbol       = Column(Text, nullable=False)   # logical FK → stock.symbol
    trade_date   = Column(Date, nullable=False)

    # --- Price ---
    ltp             = Column(Numeric)   # Last Traded Price          [col 5]
    change_percent  = Column(Numeric)   # Daily gain %               [col 4]

    # --- Fundamental quality ---
    quality         = Column(Text)      # Ratios Summary: Strong/Weak [col 1]
    stars           = Column(Integer)   # Financial Strength 0–5      [col 2]
    sector          = Column(Text)      #                              [col 3]

    # --- Valuation ratios ---
    pe              = Column(Numeric)   # Price / Earnings            [col 6]
    pb              = Column(Numeric)   # Price / Book                [col 7]
    roe             = Column(Numeric)   # Return on Equity %          [col 8]
    roa             = Column(Numeric)   # Return on Assets %          [col 9]
    peg             = Column(Numeric)   # Price/Earnings to Growth    [col 10]
    graham_distance = Column(Text)      # Discount from Graham Number [col 11] — stored as text in DB
    dividend_yield  = Column(Numeric)   # Dividend Yield %            [col 20]
    payout_ratio    = Column(Numeric)   # Dividend Payout Ratio %     [col 21]

    # --- vs Sector comparisons (Overvalued / Undervalued / "--") ---
    pe_vs_sector              = Column(Text)   # [col 12]
    pb_vs_sector              = Column(Text)   # [col 13]
    peg_vs_sector             = Column(Text)   # [col 14]
    dividend_yield_vs_sector  = Column(Text)   # [col 15]
    roe_vs_sector             = Column(Text)   # [col 16]
    yoy_growth_vs_sector      = Column(Text)   # [col 17]
    qoq_growth_vs_sector      = Column(Text)   # [col 18]
    roa_vs_sector             = Column(Text)   # [col 19]

    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uq_share_price_symbol_date"),
    )
