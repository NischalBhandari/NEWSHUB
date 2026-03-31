from database.db import SessionLocal
from database.models import stock

def insert_stock(stockData):
    session = SessionLocal()
    try:
        stock = stock(
            symbol=stockData["symbol"],
            sector=stockData["link"],
            full_name=stockData["full_name"],
            exchange_=stockData.get("exchange", "NEPSE"),
            logo_urls=stockData.get("logo_urls"),
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