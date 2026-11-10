from datetime import datetime, timedelta

from models.nha_cung_cap import NhaCungCap
from models.phieu_nhap import PhieuNhap
from models.san_pham import SanPham
from models.the_kho import TheKho
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_THU_KHO
from utils.validators import doc_ngay

QUAN_LY_KHO = (ROLE_ADMIN, ROLE_THU_KHO)
LOAI_GIAO_DICH = ("nhap_kho", "ban_hang", "tra_hang", "xuat_kho", "kiem_ke", "huy_hoa_don")


def _khoang(tu_ngay, den_ngay):
    """'dd/mm/yyyy' -> (từ: datetime, đến: datetime nửa mở, lỗi)."""
    tu, loi = doc_ngay(tu_ngay, "Từ ngày")
    if loi:
        return None, None, loi
    den, loi = doc_ngay(den_ngay, "Đến ngày")
    if loi:
        return None, None, loi
    if tu and den and tu > den:
        return None, None, "Từ ngày phải trước hoặc bằng Đến ngày."
    tu_dt = datetime.combine(tu, datetime.min.time()) if tu else None
    den_dt = datetime.combine(den + timedelta(days=1), datetime.min.time()) if den else None
    return tu_dt, den_dt, None


class TheKhoController:
    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def goi_y_san_pham(tu_khoa, gioi_han=8):
        tu_khoa = (tu_khoa or "").strip()
        if len(tu_khoa) < 2:
            return []
        return [{"id": r["id"], "ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"], "ton_kho": r["ton_kho"],
                 "ngung": r["trang_thai"] != "kinh_doanh"}
                for r in SanPham.goi_y_the_kho(tu_khoa, gioi_han)]

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def thong_tin(san_pham_id):
        """Thông tin sản phẩm + ĐỐI CHIẾU SỔ: tồn kho phải bằng tổng mọi thay đổi trong thẻ kho."""
        sp = SanPham.tim_theo_id(san_pham_id)
        if sp is None:
            return False, "Không tìm thấy sản phẩm.", None
        tong_the_kho = int(TheKho.tong_thay_doi(san_pham_id))
        ton_kho = int(sp["ton_kho"])
        return True, "OK", {
            "id": sp["id"], "ma_sp": sp["ma_sp"], "ten_sp": sp["ten_sp"], "ton_kho": ton_kho,
            "gia_von": int(sp["gia_nhap"]), "ngung": sp["trang_thai"] != "kinh_doanh",
            "tong_the_kho": tong_the_kho, "khop": tong_the_kho == ton_kho,
            "chenh_lech": ton_kho - tong_the_kho,
        }

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def lich_su(san_pham_id, loai="", tu_ngay="", den_ngay="", trang=1, so_dong=10):
        """Từng lần tồn thay đổi của một sản phẩm, mới nhất lên đầu."""
        if loai and loai not in LOAI_GIAO_DICH:
            return False, "Loại giao dịch không hợp lệ.", None
        if SanPham.tim_theo_id(san_pham_id) is None:
            return False, "Không tìm thấy sản phẩm.", None
        tu, den, loi = _khoang(tu_ngay, den_ngay)
        if loi:
            return False, loi, None
        tong = TheKho.dem_loc(san_pham_id, loai or None, tu, den)
        so_trang = max(1, -(-tong // so_dong))
        trang = min(max(trang, 1), so_trang)
        dong = [{"thoi_gian": r["thoi_gian"], "loai": r["loai_giao_dich"],
                 "thay_doi": int(r["so_luong_thay_doi"]), "ton_sau": int(r["ton_sau_giao_dich"]),
                 "chung_tu": r["ghi_chu"] or "", "nguoi": r["ho_ten"]}
                for r in TheKho.lich_su_loc(san_pham_id, loai or None, tu, den, trang, so_dong)]
        return True, "OK", {"dong": dong, "tong": tong, "trang": trang, "so_trang": so_trang}


class LichSuPhieuNhapController:
    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def danh_sach_nha_cung_cap():
        """Gồm cả nhà cung cấp đã ngừng hợp tác, vì phiếu cũ vẫn thuộc về họ."""
        return NhaCungCap.tat_ca(chi_hop_tac=False)

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def tim_kiem(tu_khoa="", ncc_id=None, tu_ngay="", den_ngay="", trang=1, so_dong=8):
        tu, den, loi = _khoang(tu_ngay, den_ngay)
        if loi:
            return False, loi, None
        tu_khoa = (tu_khoa or "").strip()
        tong = PhieuNhap.dem(tu_khoa, ncc_id, tu, den)
        so_trang = max(1, -(-tong // so_dong))
        trang = min(max(trang, 1), so_trang)
        dong = [{"id": r["id"], "ma_phieu": r["ma_phieu"], "ngay_nhap": r["ngay_nhap"],
                 "ten_ncc": r["ten_ncc"], "nguoi_lap": r["nguoi_lap"],
                 "so_mat_hang": int(r["so_mat_hang"]), "tong_tien": int(r["tong_tien"])}
                for r in PhieuNhap.danh_sach(tu_khoa, ncc_id, tu, den, trang, so_dong)]
        return True, "OK", {"dong": dong, "tong": tong, "trang": trang, "so_trang": so_trang}

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def chi_tiet(phieu_id):
        p = PhieuNhap.tim_theo_id(phieu_id)
        if p is None:
            return False, "Không tìm thấy phiếu nhập.", None
        dong = [{"ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"], "so_luong": int(r["so_luong"]),
                 "gia_nhap": int(r["gia_nhap"]), "thanh_tien": int(r["so_luong"]) * int(r["gia_nhap"])}
                for r in PhieuNhap.dong_theo_phieu(phieu_id)]
        return True, "OK", {
            "phieu": {"ma_phieu": p["ma_phieu"], "ngay_nhap": p["ngay_nhap"], "ten_ncc": p["ten_ncc"],
                      "nguoi_lap": p["nguoi_lap"], "ghi_chu": p["ghi_chu"] or "",
                      "tong_tien": int(p["tong_tien"])},
            "dong": dong}