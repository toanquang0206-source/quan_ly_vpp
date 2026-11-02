from database.connection import fetch_all


class NhaCungCap:
    @staticmethod
    def tat_ca(chi_hop_tac=True):
        dieu_kien = "WHERE trang_thai = 'hop_tac'" if chi_hop_tac else ""
        return fetch_all(f"SELECT id, ten_ncc, so_dien_thoai, trang_thai "
                         f"FROM nha_cung_cap {dieu_kien} ORDER BY ten_ncc")

    @staticmethod
    def tim_theo_id(conn, ncc_id):
        """Đọc trên CÙNG kết nối với transaction đang chạy."""
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, ten_ncc, trang_thai FROM nha_cung_cap WHERE id = %s", (ncc_id,))
        rows = cur.fetchall()
        return rows[0] if rows else None