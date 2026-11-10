from database.connection import fetch_all


def _dieu_kien(san_pham_id, loai, tu, den):
    dieu_kien, tham_so = ["tk.san_pham_id = %s"], [san_pham_id]
    if loai:
        dieu_kien.append("tk.loai_giao_dich = %s")
        tham_so.append(loai)
    if tu:
        dieu_kien.append("tk.thoi_gian >= %s")
        tham_so.append(tu)
    if den:                                    # den = 0h của NGÀY KẾ TIẾP (khoảng nửa mở)
        dieu_kien.append("tk.thoi_gian < %s")
        tham_so.append(den)
    return "WHERE " + " AND ".join(dieu_kien), tham_so


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

    # ---------- có bộ lọc (loại giao dịch, khoảng thời gian) ----------
    @staticmethod
    def dem_loc(san_pham_id, loai=None, tu=None, den=None):
        where, tham_so = _dieu_kien(san_pham_id, loai, tu, den)
        return fetch_all(f"SELECT COUNT(*) AS so FROM the_kho tk {where}", tham_so)[0]["so"]

    @staticmethod
    def lich_su_loc(san_pham_id, loai, tu, den, trang, so_dong):
        where, tham_so = _dieu_kien(san_pham_id, loai, tu, den)
        offset = (max(trang, 1) - 1) * so_dong
        return fetch_all(
            f"""SELECT tk.id, tk.thoi_gian, tk.loai_giao_dich, tk.so_luong_thay_doi,
                       tk.ton_sau_giao_dich, tk.ghi_chu, nd.ho_ten
                FROM the_kho tk
                JOIN nguoi_dung nd ON nd.id = tk.nguoi_dung_id
                {where}
                ORDER BY tk.id DESC
                LIMIT %s OFFSET %s""",
            tham_so + [so_dong, offset],
        )

    @staticmethod
    def tong_thay_doi(san_pham_id):
        """Tổng mọi thay đổi của sản phẩm: phải bằng đúng san_pham.ton_kho (đối chiếu sổ)."""
        return fetch_all(
            "SELECT COALESCE(SUM(so_luong_thay_doi), 0) AS tong FROM the_kho WHERE san_pham_id = %s",
            (san_pham_id,))[0]["tong"]