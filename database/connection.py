from contextlib import contextmanager

import mysql.connector

from config import DB_CONFIG
from utils.errors import DuLieuTrung

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

@contextmanager
def transaction():
    "chạy hết không lỗi ->commit. Có lỗi -> rollback"
    "Lỗi trùng UNIQUE (mã 1062) được dịch thành DuLieuTrung Để controller xử lý" 
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except mysql.connector.IntegrityError as e:
        conn.rollback()
        if e.errno == 1062:
            raise DuLieuTrung(e.msg) from e
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def fetch_all(sql, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or())
        return cur.fetchall()
    finally:
        conn.close()
        
