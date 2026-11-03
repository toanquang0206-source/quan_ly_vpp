from datetime import date, datetime, timedelta

from models.bao_cao import BaoCao
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN
from utils.validators import doc_ngay

CHI_ADMIN = (ROLE_ADMIN,)
TOI_DA_NGAY = 3660              # tối đa khoảng 10 năm cho một báo cáo
SO_NGAY_CHAM_BAN = 30           # còn tồn mà quá ngần ngày không bán -> "chậm luân chuyển"


def _khoang_thoi_gian(tu_ngay, den_ngay, kieu="ngay"):
    """Đọc khoảng ngày; thiếu thì lấy mặc định. Trả về (tu: date, den: date, lỗi)."""
    tu, loi = doc_ngay(tu_ngay, "Từ ngày")
    if loi:
        return None, None, loi
    den, loi = doc_ngay(den_ngay, "Đến ngày")
    if loi:
        return None, None, loi
    hom_nay = date.today()
    den = den or hom_nay
    if tu is None:
        if kieu == "thang":
            thang = den.month - 11
            nam = den.year + (thang - 1) // 12
            tu = date(nam, (thang - 1) % 12 + 1, 1)
        elif kieu == "nam":
            tu = date(den.year - 4, 1, 1)
        else:
            tu = den - timedelta(days=29)
    if tu > den:
        return None, None, "Từ ngày phải trước hoặc bằng Đến ngày."
    if (den - tu).days > TOI_DA_NGAY:
        return None, None, "Khoảng thời gian quá dài (tối đa khoảng 10 năm)."
    return tu, den, None


def _sang_datetime(tu, den):
    return (datetime.combine(tu, datetime.min.time()),
            datetime.combine(den + timedelta(days=1), datetime.min.time()))


def _cac_ky(kieu, tu, den):
    """Danh sách khóa kỳ liên tục từ tu đến den, để ngày/tháng không có giao dịch vẫn hiện số 0."""
    ds = []
    if kieu == "ngay":
        d = tu
        while d <= den:
            ds.append(d.isoformat())
            d += timedelta(days=1)
    elif kieu == "thang":
        y, m = tu.year, tu.month
        while (y, m) <= (den.year, den.month):
            ds.append(f"{y}-{m:02d}")
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    else:
        ds = [str(y) for y in range(tu.year, den.year + 1)]
    return ds


class BaoCaoController:
    @staticmethod
    @require_roles(*CHI_ADMIN)
    def doanh_thu(kieu="ngay", tu_ngay="", den_ngay=""):
        """
        Doanh thu THUẦN theo ngày/tháng/năm: tiền bán trong kỳ trừ tiền hoàn trả và hủy
        xảy ra trong kỳ. Trả về (True/False, thông điệp, dữ liệu).
        """
        if kieu not in ("ngay", "thang", "nam"):
            return False, "Kiểu báo cáo không hợp lệ.", None
        tu, den, loi = _khoang_thoi_gian(tu_ngay, den_ngay, kieu)
        if loi:
            return False, loi, None
        tu_dt, den_dt = _sang_datetime(tu, den)

        co_so_lieu = {r["ky"]: r for r in BaoCao.doanh_thu_theo_ky(kieu, tu_dt, den_dt)}
        dong = []
        tong = {"so_hoa_don": 0, "ban": 0, "hoan": 0, "thuan": 0, "loi_nhuan": 0}
        for ky in _cac_ky(kieu, tu, den):
            r = co_so_lieu.get(ky)
            d = {"ky": ky, "so_hoa_don": 0, "ban": 0, "hoan": 0, "thuan": 0, "loi_nhuan": 0}
            if r:
                for k in d:
                    if k != "ky":
                        d[k] = int(r[k])
            for k in tong:
                tong[k] += d[k]
            dong.append(d)
        return True, "OK", {"kieu": kieu, "tu": tu, "den": den, "dong": dong, "tong": tong}

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def theo_danh_muc(tu_ngay="", den_ngay=""):
        tu, den, loi = _khoang_thoi_gian(tu_ngay, den_ngay)
        if loi:
            return False, loi, None
        rows = BaoCao.theo_danh_muc(*_sang_datetime(tu, den))
        dong = [{"id": r["nhom_id"], "ten": r["ten"], "sl_thuan": int(r["sl_thuan"]),
                 "thuan": int(r["thuan"]), "loi_nhuan": int(r["loi_nhuan"])} for r in rows]
        tong = sum(d["thuan"] for d in dong)
        for d in dong:
            d["ty_trong"] = round(d["thuan"] * 100 / tong, 1) if tong > 0 else 0.0
        return True, "OK", {"tu": tu, "den": den, "dong": dong, "tong": tong,
                            "tong_loi_nhuan": sum(d["loi_nhuan"] for d in dong)}

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def theo_san_pham(tu_ngay="", den_ngay="", gioi_han=10):
        tu, den, loi = _khoang_thoi_gian(tu_ngay, den_ngay)
        if loi:
            return False, loi, None
        rows = BaoCao.theo_san_pham(*_sang_datetime(tu, den))
        dong = [{"id": r["nhom_id"], "ma_sp": r["ma"], "ten_sp": r["ten"],
                 "sl_thuan": int(r["sl_thuan"]), "thuan": int(r["thuan"]),
                 "loi_nhuan": int(r["loi_nhuan"])} for r in rows]
        return True, "OK", {"tu": tu, "den": den, "dong": dong[:gioi_han],
                            "tong_thuan": sum(d["thuan"] for d in dong),
                            "so_san_pham": len(dong)}

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def ton_kho():
        """Giá trị tồn kho (theo giá vốn bình quân), hàng sắp hết và hàng chậm luân chuyển."""
        bay_gio = datetime.now()
        dong, tong_gia_tri, sap_het, cham = [], 0, 0, 0
        for r in BaoCao.ton_kho():
            ton, gia_von = r["ton_kho"], int(r["gia_nhap"])
            dang_kd = r["trang_thai"] == "kinh_doanh"
            so_ngay = (bay_gio - r["ban_gan_nhat"]).days if r["ban_gan_nhat"] else None
            thieu = dang_kd and ton <= r["ton_toi_thieu"]
            cham_ban = ton > 0 and (so_ngay is None or so_ngay >= SO_NGAY_CHAM_BAN)
            d = {"ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"], "danh_muc": r["ten_danh_muc"],
                 "ton_kho": ton, "ton_toi_thieu": r["ton_toi_thieu"], "gia_von": gia_von,
                 "gia_tri_ton": ton * gia_von, "ban_gan_nhat": r["ban_gan_nhat"],
                 "so_ngay_khong_ban": so_ngay, "dang_kinh_doanh": dang_kd,
                 "sap_het": thieu, "cham_luan_chuyen": cham_ban}
            tong_gia_tri += d["gia_tri_ton"]
            sap_het += thieu
            cham += cham_ban
            dong.append(d)
        return True, "OK", {"dong": dong, "tong_gia_tri": tong_gia_tri, "so_sap_het": sap_het,
                            "so_cham": cham, "so_ngay_cham": SO_NGAY_CHAM_BAN}