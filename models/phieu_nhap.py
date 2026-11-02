class PhieuNhap:
    @staticmethod
    def them_phieu(conn, ma_tam, nha_cung_cap_id, nguoi_dung_id, ngay_nhap, tong_tien, ghi_chu):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO phieu_nhap
               (ma_phieu, nha_cung_cap_id, nguoi_dung_id, ngay_nhap, tong_tien, ghi_chu)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (ma_tam, nha_cung_cap_id, nguoi_dung_id, ngay_nhap, tong_tien, ghi_chu),
        )
        return cur.lastrowid

    @staticmethod
    def dat_ma(conn, phieu_id, ma_phieu):
        cur = conn.cursor()
        cur.execute("UPDATE phieu_nhap SET ma_phieu = %s WHERE id = %s", (ma_phieu, phieu_id))

    @staticmethod
    def them_dong(conn, phieu_id, san_pham_id, so_luong, gia_nhap):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chi_tiet_phieu_nhap (phieu_nhap_id, san_pham_id, so_luong, gia_nhap)
               VALUES (%s, %s, %s, %s)""",
            (phieu_id, san_pham_id, so_luong, gia_nhap),
        )