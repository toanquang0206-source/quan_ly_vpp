import re

from database.connection import transaction
from models.danh_muc import DanhMuc
from models.don_vi_tinh import DonViTinh
from models.nha_cung_cap import NhaCungCap
from models.nhat_ky import NhatKy
from utils.errors import DuLieuTrung, LoiNghiepVu, RangBuocLienKet
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_THU_KHO, Session

QUAN_LY_KHO = (ROLE_ADMIN, ROLE_THU_KHO)
MAU_SO_DIEN_THOAI = re.compile(r"^[0-9 .+()\-]{8,15}$")
MAU_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _doc_ten(ten, ten_truong, toi_da):
    """Chuẩn hóa tên (bỏ khoảng trắng thừa ở đầu, cuối, giữa). Trả về (tên, lỗi)."""
    ten = " ".join((ten or "").split())
    if not ten:
        return None, f"Vui lòng nhập {ten_truong}."
    if len(ten) > toi_da:
        return None, f"{ten_truong.capitalize()} tối đa {toi_da} ký tự."
    return ten, None


# =====================================================================================
# LOẠI SẢN PHẨM
# =====================================================================================
class DanhMucController:
    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def danh_sach():
        dong = [{"id": r["id"], "ten": r["ten_danh_muc"], "mo_ta": r["mo_ta"] or "",
                 "so_san_pham": r["so_san_pham"]} for r in DanhMuc.danh_sach_day_du()]
        return True, "OK", dong

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def them(ten, mo_ta=""):
        ten, loi = _doc_ten(ten, "tên loại sản phẩm", 100)
        if loi:
            return False, loi, None
        mo_ta = (mo_ta or "").strip()
        if len(mo_ta) > 255:
            return False, "Mô tả tối đa 255 ký tự.", None
        if DanhMuc.tim_theo_ten(ten):
            return False, f"Loại sản phẩm '{ten}' đã tồn tại.", None
        try:
            with transaction() as conn:
                dm_id = DanhMuc.them(conn, ten, mo_ta)
                NhatKy.ghi(conn, Session.get_user()["id"], "THEM_DANH_MUC", "danh_muc", dm_id, ten)
        except DuLieuTrung:
            return False, f"Loại sản phẩm '{ten}' vừa được người khác tạo.", None
        return True, f"Đã thêm loại sản phẩm '{ten}'.", {"id": dm_id}

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def sua(danh_muc_id, ten, mo_ta=""):
        ten, loi = _doc_ten(ten, "tên loại sản phẩm", 100)
        if loi:
            return False, loi, None
        mo_ta = (mo_ta or "").strip()
        if len(mo_ta) > 255:
            return False, "Mô tả tối đa 255 ký tự.", None
        trung = DanhMuc.tim_theo_ten(ten)
        if trung and trung["id"] != danh_muc_id:
            return False, f"Đã có loại sản phẩm khác tên '{ten}'.", None
        try:
            with transaction() as conn:
                cu = DanhMuc.khoa_dong(conn, danh_muc_id)
                if cu is None:
                    raise LoiNghiepVu("Không tìm thấy loại sản phẩm.")
                thay_doi = []
                if cu["ten_danh_muc"] != ten:
                    thay_doi.append(f"tên: {cu['ten_danh_muc']} -> {ten}")
                if (cu["mo_ta"] or "") != mo_ta:
                    thay_doi.append("mô tả đã đổi")
                if not thay_doi:
                    return True, "Không có thay đổi nào.", None
                DanhMuc.sua(conn, danh_muc_id, ten, mo_ta)
                NhatKy.ghi(conn, Session.get_user()["id"], "SUA_DANH_MUC", "danh_muc",
                           danh_muc_id, "; ".join(thay_doi))
        except LoiNghiepVu as e:
            return False, str(e), None
        except DuLieuTrung:
            return False, f"Đã có loại sản phẩm khác tên '{ten}'.", None
        return True, "Đã cập nhật loại sản phẩm.", None

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def xoa(danh_muc_id):
        try:
            with transaction() as conn:
                dm = DanhMuc.khoa_dong(conn, danh_muc_id)
                if dm is None:
                    raise LoiNghiepVu("Không tìm thấy loại sản phẩm.")
                so = DanhMuc.dem_san_pham(conn, danh_muc_id)
                if so:
                    raise LoiNghiepVu(
                        f"Không thể xóa: còn {so} sản phẩm thuộc loại '{dm['ten_danh_muc']}'. "
                        f"Hãy chuyển các sản phẩm đó sang loại khác trước.")
                DanhMuc.xoa(conn, danh_muc_id)
                NhatKy.ghi(conn, Session.get_user()["id"], "XOA_DANH_MUC", "danh_muc",
                           danh_muc_id, dm["ten_danh_muc"])
        except LoiNghiepVu as e:
            return False, str(e), None
        except RangBuocLienKet:
            return False, "Không thể xóa vì loại này vừa được gán cho sản phẩm khác.", None
        return True, f"Đã xóa loại sản phẩm '{dm['ten_danh_muc']}'.", None


# =====================================================================================
# ĐƠN VỊ TÍNH
# =====================================================================================
class DonViTinhController:
    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def danh_sach():
        dong = [{"id": r["id"], "ten": r["ten"], "so_san_pham": r["so_san_pham"]}
                for r in DonViTinh.danh_sach_day_du()]
        return True, "OK", dong

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def them(ten):
        ten, loi = _doc_ten(ten, "tên đơn vị tính", 30)
        if loi:
            return False, loi, None
        if DonViTinh.tim_theo_ten(ten):
            return False, f"Đơn vị tính '{ten}' đã tồn tại.", None
        try:
            with transaction() as conn:
                dv_id = DonViTinh.them(conn, ten)
                NhatKy.ghi(conn, Session.get_user()["id"], "THEM_DON_VI_TINH", "don_vi_tinh", dv_id, ten)
        except DuLieuTrung:
            return False, f"Đơn vị tính '{ten}' vừa được người khác tạo.", None
        return True, f"Đã thêm đơn vị tính '{ten}'.", {"id": dv_id}

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def sua(don_vi_id, ten):
        ten, loi = _doc_ten(ten, "tên đơn vị tính", 30)
        if loi:
            return False, loi, None
        trung = DonViTinh.tim_theo_ten(ten)
        if trung and trung["id"] != don_vi_id:
            return False, f"Đã có đơn vị tính khác tên '{ten}'.", None
        try:
            with transaction() as conn:
                cu = DonViTinh.khoa_dong(conn, don_vi_id)
                if cu is None:
                    raise LoiNghiepVu("Không tìm thấy đơn vị tính.")
                if cu["ten"] == ten:
                    return True, "Không có thay đổi nào.", None
                DonViTinh.sua(conn, don_vi_id, ten)
                NhatKy.ghi(conn, Session.get_user()["id"], "SUA_DON_VI_TINH", "don_vi_tinh",
                           don_vi_id, f"{cu['ten']} -> {ten}")
        except LoiNghiepVu as e:
            return False, str(e), None
        except DuLieuTrung:
            return False, f"Đã có đơn vị tính khác tên '{ten}'.", None
        return True, "Đã cập nhật đơn vị tính.", None

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def xoa(don_vi_id):
        try:
            with transaction() as conn:
                dv = DonViTinh.khoa_dong(conn, don_vi_id)
                if dv is None:
                    raise LoiNghiepVu("Không tìm thấy đơn vị tính.")
                so = DonViTinh.dem_san_pham(conn, don_vi_id)
                if so:
                    raise LoiNghiepVu(
                        f"Không thể xóa: còn {so} sản phẩm đang dùng đơn vị '{dv['ten']}'. "
                        f"Hãy đổi đơn vị của các sản phẩm đó trước.")
                DonViTinh.xoa(conn, don_vi_id)
                NhatKy.ghi(conn, Session.get_user()["id"], "XOA_DON_VI_TINH", "don_vi_tinh",
                           don_vi_id, dv["ten"])
        except LoiNghiepVu as e:
            return False, str(e), None
        except RangBuocLienKet:
            return False, "Không thể xóa vì đơn vị này vừa được gán cho sản phẩm khác.", None
        return True, f"Đã xóa đơn vị tính '{dv['ten']}'.", None


# =====================================================================================
# NHÀ CUNG CẤP
# =====================================================================================
def _doc_lien_he(so_dien_thoai, email, dia_chi):
    """Kiểm tra thông tin liên hệ (đều không bắt buộc). Trả về (dict, lỗi)."""
    sdt = (so_dien_thoai or "").strip()
    if sdt and not MAU_SO_DIEN_THOAI.match(sdt):
        return None, "Số điện thoại gồm 8-15 ký tự: chữ số, khoảng trắng và các dấu + . ( ) -"
    email = (email or "").strip()
    if email and (len(email) > 100 or not MAU_EMAIL.match(email)):
        return None, "Email không hợp lệ."
    dia_chi = (dia_chi or "").strip()
    if len(dia_chi) > 255:
        return None, "Địa chỉ tối đa 255 ký tự."
    return {"so_dien_thoai": sdt or None, "email": email or None, "dia_chi": dia_chi or None}, None


class NhaCungCapController:
    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def danh_sach():
        dong = [{"id": r["id"], "ten": r["ten_ncc"], "so_dien_thoai": r["so_dien_thoai"] or "",
                 "email": r["email"] or "", "dia_chi": r["dia_chi"] or "",
                 "trang_thai": r["trang_thai"], "so_phieu_nhap": r["so_phieu_nhap"]}
                for r in NhaCungCap.danh_sach_day_du()]
        return True, "OK", dong

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def them(ten, so_dien_thoai="", email="", dia_chi=""):
        ten, loi = _doc_ten(ten, "tên nhà cung cấp", 150)
        if loi:
            return False, loi, None
        lien_he, loi = _doc_lien_he(so_dien_thoai, email, dia_chi)
        if loi:
            return False, loi, None
        if NhaCungCap.tim_theo_ten(ten):
            return False, f"Nhà cung cấp '{ten}' đã tồn tại.", None
        try:
            with transaction() as conn:
                ncc_id = NhaCungCap.them(conn, ten, lien_he["so_dien_thoai"], lien_he["email"],
                                         lien_he["dia_chi"])
                NhatKy.ghi(conn, Session.get_user()["id"], "THEM_NHA_CUNG_CAP", "nha_cung_cap",
                           ncc_id, ten)
        except DuLieuTrung:
            return False, f"Nhà cung cấp '{ten}' vừa được người khác tạo.", None
        return True, f"Đã thêm nhà cung cấp '{ten}'.", {"id": ncc_id}

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def sua(ncc_id, ten, so_dien_thoai="", email="", dia_chi=""):
        ten, loi = _doc_ten(ten, "tên nhà cung cấp", 150)
        if loi:
            return False, loi, None
        lien_he, loi = _doc_lien_he(so_dien_thoai, email, dia_chi)
        if loi:
            return False, loi, None
        trung = NhaCungCap.tim_theo_ten(ten)
        if trung and trung["id"] != ncc_id:
            return False, f"Đã có nhà cung cấp khác tên '{ten}'.", None
        try:
            with transaction() as conn:
                cu = NhaCungCap.khoa_dong(conn, ncc_id)
                if cu is None:
                    raise LoiNghiepVu("Không tìm thấy nhà cung cấp.")
                moi = {"ten_ncc": ten, **lien_he}
                thay_doi = [f"{k}: {cu[k] or ''} -> {v or ''}" for k, v in moi.items()
                            if (cu[k] or "") != (v or "")]
                if not thay_doi:
                    return True, "Không có thay đổi nào.", None
                NhaCungCap.sua(conn, ncc_id, ten, lien_he["so_dien_thoai"], lien_he["email"],
                               lien_he["dia_chi"])
                NhatKy.ghi(conn, Session.get_user()["id"], "SUA_NHA_CUNG_CAP", "nha_cung_cap",
                           ncc_id, "; ".join(thay_doi))
        except LoiNghiepVu as e:
            return False, str(e), None
        except DuLieuTrung:
            return False, f"Đã có nhà cung cấp khác tên '{ten}'.", None
        return True, "Đã cập nhật nhà cung cấp.", None

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def doi_trang_thai(ncc_id, trang_thai):
        """trang_thai: 'hop_tac' hoặc 'ngung'. Nhà cung cấp ngừng hợp tác không còn xuất hiện khi nhập kho."""
        if trang_thai not in ("hop_tac", "ngung"):
            return False, "Trạng thái không hợp lệ.", None
        try:
            with transaction() as conn:
                ncc = NhaCungCap.khoa_dong(conn, ncc_id)
                if ncc is None:
                    raise LoiNghiepVu("Không tìm thấy nhà cung cấp.")
                if ncc["trang_thai"] == trang_thai:
                    raise LoiNghiepVu("Nhà cung cấp đã ở trạng thái này rồi.")
                NhaCungCap.doi_trang_thai(conn, ncc_id, trang_thai)
                NhatKy.ghi(conn, Session.get_user()["id"],
                           "NGUNG_HOP_TAC" if trang_thai == "ngung" else "HOP_TAC_LAI",
                           "nha_cung_cap", ncc_id, ncc["ten_ncc"])
        except LoiNghiepVu as e:
            return False, str(e), None
        if trang_thai == "ngung":
            return True, f"Đã ngừng hợp tác với '{ncc['ten_ncc']}'.", None
        return True, f"Đã hợp tác lại với '{ncc['ten_ncc']}'.", None