class NhatKy:
    @staticmethod
    def ghi(conn, nguoi_dung_id, hanh_dong, bang_tac_dong, ban_ghi_id=None, chi_tiet=None):
        """Ghi nhật ký TRÊN CÙNG kết nối/transaction với thao tác chính."""
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO nhat_ky_hoat_dong
               (nguoi_dung_id, hanh_dong, bang_tac_dong, ban_ghi_id, chi_tiet)
               VALUES (%s, %s, %s, %s, %s)""",
            (nguoi_dung_id, hanh_dong, bang_tac_dong, ban_ghi_id,
             (chi_tiet or "")[:500]),
        )