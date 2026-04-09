from sqlalchemy import Column, Integer, Text, TIMESTAMP, UniqueConstraint, Numeric
from datetime import datetime, timezone
from .base import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    link = Column(Text, nullable=False)
    description = Column(Text)
    content = Column(Text)
    published_at = Column(TIMESTAMP)
    source = Column(Text)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Analysis columns — populated by AI pipeline after scraping
    sentiment = Column(Text)                      # "positive" | "negative" | "neutral"
    sentiment_score = Column(Numeric(4, 3))       # -1.000 to 1.000
    relevance_score = Column(Numeric(4, 3))       # 0.000 to 1.000 — relevance to Nepal/NEPSE
    impact_level = Column(Text)                   # "high" | "medium" | "low"
    market_signal = Column(Text)                  # "bullish" | "bearish" | "neutral"
    affected_sectors = Column(Text)               # JSON array e.g. '["banking","hydropower"]'
    entities = Column(Text)                       # JSON array of named entities extracted
    keywords = Column(Text)                       # JSON array of key terms

    __table_args__ = (
        UniqueConstraint("link", name="uq_news_link"),
    )