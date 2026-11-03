from database.connection import fetch_all


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _sql_dong(kem_gia_von):
    """Các dòng của một hóa đơn kèm số lượng ĐÃ TRẢ. Giá vốn chỉ lấy khi Controller cần tính kho."""
    cot_von = "ct.gia_von," if kem_gia_von else ""
    return f"""
        SELECT ct.san_pham_id, sp.ma_sp, sp.ten_sp, ct.so_luong, ct.don_gia, {cot_von}
               COALESCE((SELECT SUM(t.so_luong)
                         FROM chi_tiet_tra_hang t
                         JOIN phieu_tra_hang p ON p.id = t.phieu_tra_hang_id
                         WHERE p.hoa_don_id = ct.hoa_don_id
                           AND t.san_pham_id = ct.san_pham_id), 0) AS da_tra
        FROM chi_tiet_hoa_don ct
        JOIN san_pham sp ON sp.id = ct.san_pham_id
        WHERE ct.hoa_don_id = %s
        ORDER BY ct.san_pham_id"""


class HoaDon:
    # ---------- ghi (lập hóa đơn) ----------
    @staticmethod
    def them_hoa_don(conn, ma_tam, nguoi_dung_id, ngay_lap, tong_tien, phuong_thuc, ghi_chu):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO hoa_don
               (ma_hoa_don, nguoi_dung_id, ngay_lap, tong_tien_hang, giam_gia,
                tong_thanh_toan, phuong_thuc_thanh_toan, ghi_chu)
               VALUES (%s, %s, %s, %s, 0, %s, %s, %s)""",
            (ma_tam, nguoi_dung_id, ngay_lap, tong_tien, tong_tien, phuong_thuc, ghi_chu),
        )
        return cur.lastrowid

    @staticmethod
    def dat_ma(conn, hoa_don_id, ma_hoa_don):
        cur = conn.cursor()
        cur.execute("UPDATE hoa_don SET ma_hoa_don = %s WHERE id = %s", (ma_hoa_don, hoa_don_id))

    @staticmethod
    def them_dong(conn, hoa_don_id, san_pham_id, so_luong, don_gia, gia_von):
        """don_gia và gia_von là giá CHỤP LẠI tại lúc bán, không đổi dù sau này giá đổi."""
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chi_tiet_hoa_don (hoa_don_id, san_pham_id, so_luong, don_gia, gia_von)
               VALUES (%s, %s, %s, %s, %s)""",
            (hoa_don_id, san_pham_id, so_luong, don_gia, gia_von),
        )

    # ---------- đọc (tìm kiếm, xem chi tiết) ----------
    @staticmethod
    def _dieu_kien(tu_khoa, tu_ngay, den_ngay):
        dieu_kien, tham_so = [], []
        if tu_khoa:
            dieu_kien.append("hd.ma_hoa_don LIKE %s")
            tham_so.append(f"%{_escape_like(tu_khoa)}%")
        if tu_ngay:
            dieu_kien.append("hd.ngay_lap >= %s")
            tham_so.append(tu_ngay)
        if den_ngay:                                  # den_ngay = 0h của NGÀY KẾ TIẾP (khoảng nửa mở)
            dieu_kien.append("hd.ngay_lap < %s")
            tham_so.append(den_ngay)
        return ("WHERE " + " AND ".join(dieu_kien)) if dieu_kien else "", tham_so

    @staticmethod
    def dem(tu_khoa=None, tu_ngay=None, den_ngay=None):
        where, tham_so = HoaDon._dieu_kien(tu_khoa, tu_ngay, den_ngay)
        return fetch_all(f"SELECT COUNT(*) AS so FROM hoa_don hd {where}", tham_so)[0]["so"]

    @staticmethod
    def tim_kiem(tu_khoa=None, tu_ngay=None, den_ngay=None, trang=1, so_dong=10):
        where, tham_so = HoaDon._dieu_kien(tu_khoa, tu_ngay, den_ngay)
        offset = (max(trang, 1) - 1) * so_dong
        return fetch_all(
            f"""SELECT hd.id, hd.ma_hoa_don, hd.ngay_lap, hd.tong_thanh_toan,
                       hd.phuong_thuc_thanh_toan, hd.trang_thai, nd.ho_ten AS nhan_vien,
                       COALESCE((SELECT SUM(p.tong_tien_hoan) FROM phieu_tra_hang p
                                 WHERE p.hoa_don_id = hd.id), 0) AS da_hoan
                FROM hoa_don hd
                JOIN nguoi_dung nd ON nd.id = hd.nguoi_dung_id
                {where}
                ORDER BY hd.ngay_lap DESC, hd.id DESC
                LIMIT %s OFFSET %s""",
            tham_so + [so_dong, offset],
        )

    @staticmethod
    def tim_theo_id(hoa_don_id):
        rows = fetch_all(
            """SELECT hd.id, hd.ma_hoa_don, hd.ngay_lap, hd.tong_thanh_toan,
                      hd.phuong_thuc_thanh_toan, hd.trang_thai, hd.ghi_chu,
                      nd.ho_ten AS nhan_vien,
                      COALESCE((SELECT SUM(p.tong_tien_hoan) FROM phieu_tra_hang p
                                WHERE p.hoa_don_id = hd.id), 0) AS da_hoan
               FROM hoa_don hd JOIN nguoi_dung nd ON nd.id = hd.nguoi_dung_id
               WHERE hd.id = %s""",
            (hoa_don_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def dong_theo_hoa_don(hoa_don_id):
        """Các dòng hóa đơn để HIỂN THỊ: không có giá vốn."""
        return fetch_all(_sql_dong(False), (hoa_don_id,))

    # ---------- trong transaction (trả hàng, hủy hóa đơn) ----------
    @staticmethod
    def khoa(conn, hoa_don_id):
        """Khóa dòng hóa đơn đến hết transaction: hai người không thể cùng trả/hủy một hóa đơn."""
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT id, ma_hoa_don, ngay_lap, trang_thai, tong_thanh_toan
               FROM hoa_don WHERE id = %s FOR UPDATE""",
            (hoa_don_id,),
        )
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def dong_de_tra(conn, hoa_don_id):
        """Các dòng hóa đơn KÈM giá vốn lúc bán và số lượng đã trả (dùng để tính kho)."""
        cur = conn.cursor(dictionary=True)
        cur.execute(_sql_dong(True), (hoa_don_id,))
        rows = cur.fetchall()
        for r in rows:
            r["da_tra"] = int(r["da_tra"])
        return rows

    @staticmethod
    def doi_trang_thai(conn, hoa_don_id, trang_thai):
        cur = conn.cursor()
        cur.execute("UPDATE hoa_don SET trang_thai = %s WHERE id = %s", (trang_thai, hoa_don_id))
    @staticmethod
    def danh_dau_huy(conn, hoa_don_id, ngay_huy):
        """Đánh dấu đã hủy VÀ ghi ngày hủy: khoản hủy được báo cáo vào đúng ngày này."""
        cur = conn.cursor()
        cur.execute("UPDATE hoa_don SET trang_thai = 'da_huy', ngay_huy = %s WHERE id = %s",
                    (ngay_huy, hoa_don_id))
    @staticmethod
    def da_co_tra_hang(conn, hoa_don_id):
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM phieu_tra_hang WHERE hoa_don_id = %s", (hoa_don_id,))
        return cur.fetchone()[0] > 0

    