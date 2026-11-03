from database.connection import fetch_all

# Cách gom kỳ: chuỗi CỐ ĐỊNH do ta viết (không bao giờ ghép dữ liệu người dùng vào SQL)
_KY = {
    "ngay": "CAST(DATE(e.thoi_diem) AS CHAR)",
    "thang": "CONCAT(YEAR(e.thoi_diem), '-', LPAD(MONTH(e.thoi_diem), 2, '0'))",
    "nam": "CAST(YEAR(e.thoi_diem) AS CHAR)",
}

# Mỗi giao dịch là một SỰ KIỆN mang dấu, ghi vào đúng NGÀY XẢY RA của nó:
#   bán  -> +tiền tại ngày lập hóa đơn
#   hủy  -> -tiền tại ngày hủy        (không sửa lại ngày bán đã chốt)
#   trả  -> -tiền tại ngày trả hàng
_VON_HOA_DON = "(SELECT COALESCE(SUM(c.so_luong * c.gia_von), 0) FROM chi_tiet_hoa_don c WHERE c.hoa_don_id = hd.id)"
_SU_KIEN_TONG = f"""
    SELECT hd.ngay_lap AS thoi_diem, 1 AS la_ban, hd.tong_thanh_toan AS tien, {_VON_HOA_DON} AS von
    FROM hoa_don hd WHERE hd.ngay_lap >= %s AND hd.ngay_lap < %s
    UNION ALL
    SELECT hd.ngay_huy, 0, -hd.tong_thanh_toan, -{_VON_HOA_DON}
    FROM hoa_don hd
    WHERE hd.trang_thai = 'da_huy' AND hd.ngay_huy IS NOT NULL AND hd.ngay_huy >= %s AND hd.ngay_huy < %s
    UNION ALL
    SELECT p.ngay_tra, 0, -p.tong_tien_hoan,
           -(SELECT COALESCE(SUM(t.so_luong * c.gia_von), 0)
             FROM chi_tiet_tra_hang t
             JOIN chi_tiet_hoa_don c ON c.hoa_don_id = p.hoa_don_id AND c.san_pham_id = t.san_pham_id
             WHERE t.phieu_tra_hang_id = p.id)
    FROM phieu_tra_hang p WHERE p.ngay_tra >= %s AND p.ngay_tra < %s
"""

# Cùng ý tưởng nhưng theo TỪNG DÒNG hàng để gom theo danh mục / sản phẩm
_SU_KIEN_DONG = """
    SELECT {nhom}, hd.ngay_lap AS thoi_diem, ct.so_luong AS sl,
           ct.so_luong * ct.don_gia AS tien, ct.so_luong * ct.gia_von AS von
    FROM chi_tiet_hoa_don ct
    JOIN hoa_don hd ON hd.id = ct.hoa_don_id
    JOIN san_pham sp ON sp.id = ct.san_pham_id
    JOIN danh_muc dm ON dm.id = sp.danh_muc_id
    WHERE hd.ngay_lap >= %s AND hd.ngay_lap < %s
    UNION ALL
    SELECT {nhom}, hd.ngay_huy, -ct.so_luong, -ct.so_luong * ct.don_gia, -ct.so_luong * ct.gia_von
    FROM chi_tiet_hoa_don ct
    JOIN hoa_don hd ON hd.id = ct.hoa_don_id
    JOIN san_pham sp ON sp.id = ct.san_pham_id
    JOIN danh_muc dm ON dm.id = sp.danh_muc_id
    WHERE hd.trang_thai = 'da_huy' AND hd.ngay_huy IS NOT NULL
      AND hd.ngay_huy >= %s AND hd.ngay_huy < %s
    UNION ALL
    SELECT {nhom}, p.ngay_tra, -t.so_luong, -t.so_luong * t.don_gia, -t.so_luong * c.gia_von
    FROM chi_tiet_tra_hang t
    JOIN phieu_tra_hang p ON p.id = t.phieu_tra_hang_id
    JOIN chi_tiet_hoa_don c ON c.hoa_don_id = p.hoa_don_id AND c.san_pham_id = t.san_pham_id
    JOIN san_pham sp ON sp.id = t.san_pham_id
    JOIN danh_muc dm ON dm.id = sp.danh_muc_id
    WHERE p.ngay_tra >= %s AND p.ngay_tra < %s
"""
_NHOM_DANH_MUC = "dm.id AS nhom_id, '' AS ma, dm.ten_danh_muc AS ten"
_NHOM_SAN_PHAM = "sp.id AS nhom_id, sp.ma_sp AS ma, sp.ten_sp AS ten"


class BaoCao:
    @staticmethod
    def doanh_thu_theo_ky(kieu, tu, den):
        """tu, den: datetime, khoảng nửa mở [tu, den). kieu: 'ngay' | 'thang' | 'nam'."""
        ky = _KY[kieu]
        return fetch_all(
            f"""SELECT {ky} AS ky,
                       SUM(e.la_ban) AS so_hoa_don,
                       SUM(CASE WHEN e.la_ban = 1 THEN e.tien ELSE 0 END) AS ban,
                       -SUM(CASE WHEN e.la_ban = 0 THEN e.tien ELSE 0 END) AS hoan,
                       SUM(e.tien) AS thuan,
                       SUM(e.tien - e.von) AS loi_nhuan
                FROM ({_SU_KIEN_TONG}) e
                GROUP BY ky ORDER BY ky""",
            [tu, den] * 3,
        )

    @staticmethod
    def _theo_nhom(nhom, tu, den):
        return fetch_all(
            f"""SELECT e.nhom_id, e.ma, e.ten, SUM(e.sl) AS sl_thuan,
                       SUM(e.tien) AS thuan, SUM(e.tien - e.von) AS loi_nhuan
                FROM ({_SU_KIEN_DONG.format(nhom=nhom)}) e
                GROUP BY e.nhom_id, e.ma, e.ten
                ORDER BY thuan DESC, e.ten""",
            [tu, den] * 3,
        )

    @staticmethod
    def theo_danh_muc(tu, den):
        return BaoCao._theo_nhom(_NHOM_DANH_MUC, tu, den)

    @staticmethod
    def theo_san_pham(tu, den):
        return BaoCao._theo_nhom(_NHOM_SAN_PHAM, tu, den)

    @staticmethod
    def ton_kho():
        return fetch_all(
            """SELECT sp.id, sp.ma_sp, sp.ten_sp, dm.ten_danh_muc, sp.ton_kho, sp.ton_toi_thieu,
                      sp.gia_nhap, sp.trang_thai,
                      (SELECT MAX(hd.ngay_lap)
                       FROM chi_tiet_hoa_don ct JOIN hoa_don hd ON hd.id = ct.hoa_don_id
                       WHERE ct.san_pham_id = sp.id AND hd.trang_thai = 'hoan_thanh') AS ban_gan_nhat
               FROM san_pham sp JOIN danh_muc dm ON dm.id = sp.danh_muc_id
               ORDER BY dm.ten_danh_muc, sp.ten_sp"""
        )