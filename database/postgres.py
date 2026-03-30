import psycopg2
import os
from psycopg2.extras import RealDictCursor

DB_NAME = os.getenv("DB_NAME", "newsdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "fiberoptics12")
DB_HOST = os.getenv("DB_HOST", "localhost")

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        cursor_factory=RealDictCursor
    )