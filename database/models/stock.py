from sqlalchemy import Column, Integer, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()
class stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    symbol = Column(Text)
    sector = Column(Text)
    full_name = Column(Text)
    logo_urls = Column(Text)
    exchange_logo = Column(Text)
    exchange = Column(Text)
    is_master = Column(bool)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

