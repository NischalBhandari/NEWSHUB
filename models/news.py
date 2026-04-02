from sqlalchemy import Column, Integer, Text, TIMESTAMP, UniqueConstraint
from datetime import datetime
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
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("link", name="uq_news_link"),  # 👈 important for ON CONFLICT
    )