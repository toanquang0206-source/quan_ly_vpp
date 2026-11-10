from datetime import date, datetime, timedelta

from controllers.bao_cao_controller import SO_NGAY_CHAM_BAN
from models.bao_cao import BaoCao
from models.tong_quan import TongQuan
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_NHAN_VIEN, ROLE_THU_KHO, Session

TAT_CA = (ROLE_ADMIN, ROLE_THU_KHO, ROLE_NHAN_VIEN)
QUAN_LY_KHO = (ROLE_ADMIN, ROLE_THU_KHO)


def _dau_ngay(ngay):
    return datetime.combine(ngay, datetime.min.time())


def _the(nhan, gia_tri, kieu, canh_bao=None):
    """Một thẻ số liệu. kieu: 'tien' | 'so' | 'san_pham'. canh_bao: None | 'do' | 'cam'."""
    return {"nhan": nhan, "gia_tri": gia_tri, "kieu": kieu, "canh_bao": canh_bao}


class TongQuanController:
    @staticmethod
    @require_roles(*TAT_CA)
    def tong_quan():
        """
        Dữ liệu màn hình Tổng quan, KHÁC NHAU theo vai trò.
        Nhân viên bán hàng không bao giờ nhận được giá vốn hay lãi gộp.
        Trả về (True/False, thông điệp, dữ liệu). Số liệu là số thô để View định dạng.
        """
        user = Session.get_user()
        vai_tro = user["vai_tro"]
        hom_nay = date.today()
        tu_hom_nay, ngay_mai = _dau_ngay(hom_nay), _dau_ngay(hom_nay + timedelta(days=1))
        tu_thang = _dau_ngay(hom_nay.replace(day=1))

        tong_sap_het = TongQuan.dem_sap_het()
        du_lieu = {
            "vai_tro": vai_tro, "ho_ten": user["ho_ten"], "ngay": hom_nay,
            "sap_het": {"tong": tong_sap_het,
                        "dong": [{"ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"], "ton_kho": r["ton_kho"],
                                  "ton_toi_thieu": r["ton_toi_thieu"]} for r in TongQuan.sap_het(8)]},
            "the": [], "bieu_do": None, "gan_day": None,
        }
        canh_bao_het = "do" if tong_sap_het else None

        if vai_tro == ROLE_ADMIN:
            tu_7_ngay = hom_nay - timedelta(days=6)
            co_so_lieu = {r["ky"]: r for r in BaoCao.doanh_thu_theo_ky(
                "ngay", _dau_ngay(tu_7_ngay), ngay_mai)}
            bieu_do = []
            for k in range(7):                                   # ngày không có giao dịch vẫn hiện số 0
                ky = (tu_7_ngay + timedelta(days=k)).isoformat()
                r = co_so_lieu.get(ky)
                bieu_do.append({"ky": ky,
                                "so_hoa_don": int(r["so_hoa_don"]) if r else 0,
                                "thuan": int(r["thuan"]) if r else 0,
                                "loi_nhuan": int(r["loi_nhuan"]) if r else 0})
            thang = BaoCao.doanh_thu_theo_ky("thang", tu_thang, ngay_mai)
            hom_nay_so = bieu_do[-1]
            du_lieu["bieu_do"] = bieu_do
            du_lieu["the"] = [
                _the("Doanh thu thuần hôm nay", hom_nay_so["thuan"], "tien"),
                _the("Doanh thu thuần tháng này", sum(int(r["thuan"]) for r in thang), "tien"),
                _the("Lãi gộp tháng này", sum(int(r["loi_nhuan"]) for r in thang), "tien"),
                _the("Hóa đơn đã lập hôm nay", hom_nay_so["so_hoa_don"], "so"),
            ]

        elif vai_tro == ROLE_THU_KHO:
            cham = TongQuan.dem_cham_luan_chuyen(datetime.now() - timedelta(days=SO_NGAY_CHAM_BAN))
            du_lieu["the"] = [
                _the("Sản phẩm sắp hết hàng", tong_sap_het, "san_pham", canh_bao_het),
                _the(f"Chậm luân chuyển (≥ {SO_NGAY_CHAM_BAN} ngày)", cham, "san_pham",
                     "cam" if cham else None),
                _the("Giá trị tồn kho (theo giá vốn)", int(TongQuan.tong_gia_tri_ton()), "tien"),
                _the("Phiếu nhập tháng này", TongQuan.dem_phieu_nhap(tu_thang, ngay_mai), "so"),
            ]
            du_lieu["gan_day"] = {"loai": "phieu_nhap", "dong": [
                {"ma": r["ma_phieu"], "thoi_gian": r["ngay_nhap"], "ben_thu_ba": r["ten_ncc"],
                 "tong": int(r["tong_tien"])} for r in TongQuan.phieu_nhap_gan_day(6)]}

        else:                                                    # nhân viên bán hàng
            cua_toi = TongQuan.doanh_so_cua_toi(user["id"], tu_hom_nay, ngay_mai)
            du_lieu["the"] = [
                _the("Doanh số bán của bạn hôm nay", int(cua_toi["tong"]), "tien"),
                _the("Hóa đơn bạn đã lập hôm nay", int(cua_toi["so"]), "so"),
                _the("Sản phẩm sắp hết hàng", tong_sap_het, "san_pham", canh_bao_het),
            ]
            du_lieu["gan_day"] = {"loai": "hoa_don", "dong": [
                {"ma": r["ma_hoa_don"], "thoi_gian": r["ngay_lap"], "tong": int(r["tong_thanh_toan"]),
                 "trang_thai": r["trang_thai"]} for r in TongQuan.hoa_don_gan_day(user["id"], 6)]}
        return True, "OK", du_lieu

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def canh_bao_het_hang(gioi_han=10):
        """Dữ liệu cho hộp thoại cảnh báo khi vừa đăng nhập (chỉ Admin và Thủ kho)."""
        tong = TongQuan.dem_sap_het()
        dong = [{"ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"], "ton_kho": r["ton_kho"],
                 "ton_toi_thieu": r["ton_toi_thieu"]} for r in TongQuan.sap_het(gioi_han)] if tong else []
        return True, "OK", {"tong": tong, "dong": dong}