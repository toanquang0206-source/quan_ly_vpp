from database.connection import fetch_all


class VaiTro:
    @staticmethod
    def tat_ca():
        return fetch_all("SELECT id, ten_vai_tro FROM vai_tro ORDER BY id")

    @staticmethod
    def tim_theo_id(conn, vai_tro_id):
        """Đọc trên CÙNG kết nối với transaction đang chạy."""
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, ten_vai_tro FROM vai_tro WHERE id = %s", (vai_tro_id,))
        rows = cur.fetchall()
        return rows[0] if rows else None