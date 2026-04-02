from sqlalchemy import Column, Integer, Text, TIMESTAMP,  Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .base import Base


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    symbol = Column(Text)
    sector = Column(Text)
    full_name = Column(Text)
    logo_urls = Column(Text)
    type = Column(Text)
    exchange_logo = Column(Text)
    exchange = Column(Text)
    is_master = Column(Boolean)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    description = Column(Text)

