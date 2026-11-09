from contextlib import contextmanager

import mysql.connector

from config import DB_CONFIG
from utils.errors import DuLieuTrung, RangBuocLienKet


def get_connection():
    """Mở một kết nối mới (một 'cuộc gọi')."""
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def transaction():
    """
    Chạy hết không lỗi -> commit. Có lỗi giữa chừng -> rollback.
    Lỗi trùng UNIQUE (1062) -> DuLieuTrung; lỗi xóa dòng đang được tham chiếu (1451) -> RangBuocLienKet.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except mysql.connector.IntegrityError as e:
        conn.rollback()
        if e.errno == 1062:
            raise DuLieuTrung(e.msg) from e
        if e.errno == 1451:
            raise RangBuocLienKet(e.msg) from e
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql, params=None):
    """Truy vấn đọc nhanh, trả về danh sách dict."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        conn.close()