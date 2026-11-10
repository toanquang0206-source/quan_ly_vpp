from database.connection import fetch_all


class TongQuan:
    """Các truy vấn nhỏ phục vụ màn hình Tổng quan và cảnh báo hết hàng."""

    @staticmethod
    def dem_sap_het():
        return fetch_all(
            """SELECT COUNT(*) AS so FROM san_pham
               WHERE trang_thai = 'kinh_doanh' AND ton_kho <= ton_toi_thieu""")[0]["so"]

    @staticmethod
    def sap_het(gioi_han=8):
        """Sản phẩm thiếu nhiều nhất (tồn so với mức tối thiểu) lên đầu."""
        return fetch_all(
            """SELECT ma_sp, ten_sp, ton_kho, ton_toi_thieu FROM san_pham
               WHERE trang_thai = 'kinh_doanh' AND ton_kho <= ton_toi_thieu
               ORDER BY (ton_kho - ton_toi_thieu), ten_sp LIMIT %s""", (gioi_han,))

    @staticmethod
    def dem_cham_luan_chuyen(tu_ngay):
        """Sản phẩm còn tồn nhưng không bán được cái nào từ tu_ngay đến nay."""
        return fetch_all(
            """SELECT COUNT(*) AS so FROM san_pham sp
               WHERE sp.ton_kho > 0 AND NOT EXISTS (
                   SELECT 1 FROM chi_tiet_hoa_don ct JOIN hoa_don hd ON hd.id = ct.hoa_don_id
                   WHERE ct.san_pham_id = sp.id AND hd.trang_thai = 'hoan_thanh'
                     AND hd.ngay_lap >= %s)""", (tu_ngay,))[0]["so"]

    @staticmethod
    def tong_gia_tri_ton():
        return fetch_all(
            "SELECT COALESCE(SUM(ton_kho * gia_nhap), 0) AS tong FROM san_pham")[0]["tong"]

    @staticmethod
    def doanh_so_cua_toi(nguoi_dung_id, tu, den):
        """Số hóa đơn và tổng tiền bán của MỘT nhân viên trong khoảng [tu, den)."""
        return fetch_all(
            """SELECT COUNT(*) AS so, COALESCE(SUM(tong_thanh_toan), 0) AS tong FROM hoa_don
               WHERE nguoi_dung_id = %s AND trang_thai = 'hoan_thanh'
                 AND ngay_lap >= %s AND ngay_lap < %s""", (nguoi_dung_id, tu, den))[0]

    @staticmethod
    def hoa_don_gan_day(nguoi_dung_id, gioi_han=6):
        return fetch_all(
            """SELECT ma_hoa_don, ngay_lap, tong_thanh_toan, trang_thai FROM hoa_don
               WHERE nguoi_dung_id = %s ORDER BY ngay_lap DESC, id DESC LIMIT %s""",
            (nguoi_dung_id, gioi_han))

    @staticmethod
    def phieu_nhap_gan_day(gioi_han=6):
        return fetch_all(
            """SELECT p.ma_phieu, p.ngay_nhap, n.ten_ncc, p.tong_tien
               FROM phieu_nhap p JOIN nha_cung_cap n ON n.id = p.nha_cung_cap_id
               ORDER BY p.ngay_nhap DESC, p.id DESC LIMIT %s""", (gioi_han,))

    @staticmethod
    def dem_phieu_nhap(tu, den):
        return fetch_all(
            "SELECT COUNT(*) AS so FROM phieu_nhap WHERE ngay_nhap >= %s AND ngay_nhap < %s",
            (tu, den))[0]["so"]