from database.connection import fetch_all


class TheKho:
    @staticmethod
    def ghi(conn, san_pham_id, loai, so_luong_thay_doi, ton_sau, chung_tu_id,
            nguoi_dung_id, ghi_chu=None):
        """Mỗi lần số tồn đổi là MỘT dòng. so_luong_thay_doi: dương = vào, âm = ra."""
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO the_kho
               (san_pham_id, loai_giao_dich, so_luong_thay_doi, ton_sau_giao_dich,
                chung_tu_id, nguoi_dung_id, ghi_chu)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (san_pham_id, loai, so_luong_thay_doi, ton_sau, chung_tu_id,
             nguoi_dung_id, ghi_chu),
        )

    @staticmethod
    def dem(san_pham_id):
        return fetch_all("SELECT COUNT(*) AS so FROM the_kho WHERE san_pham_id = %s",
                         (san_pham_id,))[0]["so"]

    @staticmethod
    def lich_su(san_pham_id, trang=1, so_dong=20):
        offset = (max(trang, 1) - 1) * so_dong
        return fetch_all(
            """SELECT tk.id, tk.thoi_gian, tk.loai_giao_dich, tk.so_luong_thay_doi,
                      tk.ton_sau_giao_dich, tk.ghi_chu, nd.ho_ten
               FROM the_kho tk
               JOIN nguoi_dung nd ON nd.id = tk.nguoi_dung_id
               WHERE tk.san_pham_id = %s
               ORDER BY tk.id DESC
               LIMIT %s OFFSET %s""",
            (san_pham_id, so_dong, offset),
        )