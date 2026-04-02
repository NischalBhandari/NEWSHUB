from database.db import SessionLocal
from models import Stock

def insert_stock(stockData):
    session = SessionLocal()
    try:
        stock = Stock(
            symbol=stockData["symbol"],
            description=stockData["description"],
            full_name=stockData["full_name"],
            sector=stockData.get("sector", "none"),
            logo_urls=stockData.get("logo_urls"),
            type = stockData.get("type", "stock"),
            exchange_logo=stockData.get("exchange_logo", "none"),
            exchange = stockData.get("exchange", "NEPSE"),
            is_master=stockData.get("is_master", False)
        )

        session.add(stock)
        session.commit()
    except Exception as e:
        session.rollback()
        print("Error:", e)
    finally:
        session.close()