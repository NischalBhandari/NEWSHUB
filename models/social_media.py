from sqlalchemy import Column, Integer, Text, TIMESTAMP, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base


class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"

    id             = Column(Integer, primary_key=True)
    group_name     = Column(Text)                        # Facebook group label set by user
    author         = Column(Text)                        # Best-effort, may be None
    text           = Column(Text, nullable=False)        # Full post text
    reactions      = Column(Text)                        # Raw aria-label string e.g. "45 reactions"
    url            = Column(Text)                        # Group URL at time of scrape
    scraped_at     = Column(TIMESTAMP)                   # Timestamp from extension
    created_at     = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Analysis — populated by social_media_analyzer.py
    sentiment        = Column(Text)              # "positive" | "negative" | "neutral" | "skipped"
    sentiment_score  = Column(Numeric(4, 3))     # -1.000 to 1.000
    relevance_score  = Column(Numeric(4, 3))     # 0.000 to 1.000
    impact_level     = Column(Text)              # "high" | "medium" | "low"
    market_signal    = Column(Text)              # "bullish" | "bearish" | "neutral"
    affected_sectors = Column(Text)              # JSON array
    entities         = Column(Text)              # JSON array
    keywords         = Column(Text)              # JSON array

    comments = relationship("SocialMediaComment", back_populates="post", cascade="all, delete-orphan")


class SocialMediaComment(Base):
    __tablename__ = "social_media_comments"

    id       = Column(Integer, primary_key=True)
    post_id  = Column(Integer, ForeignKey("social_media_posts.id", ondelete="CASCADE"), nullable=False)
    author   = Column(Text)
    text     = Column(Text, nullable=False)
    scraped_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Analysis — same schema as posts for consistent ranking
    sentiment        = Column(Text)
    sentiment_score  = Column(Numeric(4, 3))
    relevance_score  = Column(Numeric(4, 3))
    impact_level     = Column(Text)
    market_signal    = Column(Text)
    affected_sectors = Column(Text)
    entities         = Column(Text)
    keywords         = Column(Text)

    post = relationship("SocialMediaPost", back_populates="comments")
