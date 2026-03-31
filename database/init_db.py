from database.db import engine
from database.models.stock import Base

def init_db():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()