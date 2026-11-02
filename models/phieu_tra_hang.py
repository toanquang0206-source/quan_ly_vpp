class PhieuTraHang:
    @staticmethod
    def them(conn, hoa_don_id, nguoi_dung_id, ngay_tra, ly_do, tong_tien_hoan):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO phieu_tra_hang
               (hoa_don_id, nguoi_dung_id, ngay_tra, ly_do, tong_tien_hoan)
               VALUES (%s, %s, %s, %s, %s)""",
            (hoa_don_id, nguoi_dung_id, ngay_tra, ly_do, tong_tien_hoan),
        )
        return cur.lastrowid

    @staticmethod
    def them_dong(conn, phieu_id, san_pham_id, so_luong, don_gia):
        """don_gia = giá trên HÓA ĐƠN GỐC (số tiền khách đã trả), không phải giá hiện tại."""
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chi_tiet_tra_hang (phieu_tra_hang_id, san_pham_id, so_luong, don_gia)
               VALUES (%s, %s, %s, %s)""",
            (phieu_id, san_pham_id, so_luong, don_gia),
        )