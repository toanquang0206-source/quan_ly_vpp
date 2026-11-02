import re
from decimal import Decimal

from database.connection import transaction
from models.danh_muc import DanhMuc
from models.don_vi_tinh import DonViTinh
from models.nhat_ky import NhatKy
from models.san_pham import SanPham
from utils.errors import DuLieuTrung
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_THU_KHO, ROLE_NHAN_VIEN, Session

TAT_CA = (ROLE_ADMIN, ROLE_THU_KHO, ROLE_NHAN_VIEN)
QUAN_LY_KHO = (ROLE_ADMIN, ROLE_THU_KHO)
MAU_MA_SP = re.compile(r"^[A-Z0-9_-]{2,30}$")

NHAN_TRUONG = {
    "ma_sp": "mã", "ten_sp": "tên", "danh_muc_id": "danh mục",
    "don_vi_tinh_id": "đơn vị tính", "gia_nhap": "giá nhập", "gia_ban": "giá bán",
    "ton_toi_thieu": "tồn tối thiểu", "mo_ta": "mô tả",
}


# ---------- hàm hỗ trợ (luật nghiệp vụ, không dính tkinter) ----------
def _doc_so(gia_tri, ten_truong, mac_dinh=None):
    """'12.000' / '12,000 đ' / 12000 -> (12000, None). Sai -> (None, thông báo lỗi)."""
    if gia_tri is None or str(gia_tri).strip() == "":
        if mac_dinh is not None:
            return mac_dinh, None
        return None, f"Vui lòng nhập {ten_truong}."
    chuoi = re.sub(r"[.,\sđĐ]", "", str(gia_tri))
    if not chuoi.isdigit():
        return None, f"{ten_truong.capitalize()} phải là số nguyên không âm."
    return int(chuoi), None


def _chuan_hoa(du_lieu):
    """Chuẩn hóa + kiểm tra dữ liệu form. Trả về (dict sạch, None) hoặc (None, lỗi)."""
    ma = (du_lieu.get("ma_sp") or "").strip().upper()
    if not MAU_MA_SP.match(ma):
        return None, ("Mã sản phẩm gồm 2-30 ký tự: chữ không dấu, số, gạch ngang "
                      "hoặc gạch dưới, không có khoảng trắng.")
    ten = (du_lieu.get("ten_sp") or "").strip()
    if not ten:
        return None, "Vui lòng nhập tên sản phẩm."
    if len(ten) > 150:
        return None, "Tên sản phẩm tối đa 150 ký tự."
    if not du_lieu.get("danh_muc_id"):
        return None, "Vui lòng chọn danh mục."
    if not du_lieu.get("don_vi_tinh_id"):
        return None, "Vui lòng chọn đơn vị tính."

    gia_nhap, loi = _doc_so(du_lieu.get("gia_nhap"), "giá nhập")
    if loi:
        return None, loi
    gia_ban, loi = _doc_so(du_lieu.get("gia_ban"), "giá bán")
    if loi:
        return None, loi
    ton_toi_thieu, loi = _doc_so(du_lieu.get("ton_toi_thieu"), "tồn tối thiểu", mac_dinh=0)
    if loi:
        return None, loi
    if gia_ban < gia_nhap:
        return None, "Giá bán không được thấp hơn giá vốn."

    return {
        "ma_sp": ma, "ten_sp": ten,
        "danh_muc_id": int(du_lieu["danh_muc_id"]),
        "don_vi_tinh_id": int(du_lieu["don_vi_tinh_id"]),
        "gia_nhap": gia_nhap, "gia_ban": gia_ban, "ton_toi_thieu": ton_toi_thieu,
        "mo_ta": (du_lieu.get("mo_ta") or "").strip(),
    }, None


def _so_sanh_duoc(v):
    if v is None:
        return ""
    if isinstance(v, (int, Decimal)):
        return int(v)
    return str(v)


def _mo_ta_thay_doi(cu, moi):
    """Ví dụ: 'giá bán: 10000 -> 12000; tên: A -> B' (rỗng nếu không đổi gì)."""
    ds = []
    for khoa, nhan in NHAN_TRUONG.items():
        a, b = _so_sanh_duoc(cu[khoa]), _so_sanh_duoc(moi[khoa])
        if a != b:
            ds.append(f"{nhan}: {a} -> {b}")
    return "; ".join(ds)


def _doi_trang_thai(san_pham_id, trang_thai_moi):
    sp = SanPham.tim_theo_id(san_pham_id)
    if sp is None:
        return False, "Không tìm thấy sản phẩm."
    if sp["trang_thai"] == trang_thai_moi:
        return False, "Sản phẩm đã ở trạng thái này rồi."

    dung = trang_thai_moi == "ngung_kinh_doanh"
    with transaction() as conn:
        SanPham.doi_trang_thai(conn, san_pham_id, trang_thai_moi)
        NhatKy.ghi(conn, Session.get_user()["id"],
                   "NGUNG_KINH_DOANH" if dung else "KINH_DOANH_LAI",
                   "san_pham", san_pham_id, f"{sp['ma_sp']} - {sp['ten_sp']}")
    if dung:
        thong_diep = f"Đã ngừng kinh doanh {sp['ten_sp']}."
        if sp["ton_kho"] > 0:
            thong_diep += f" Lưu ý: trong kho vẫn còn {sp['ton_kho']}."
        return True, thong_diep
    return True, f"Đã cho {sp['ten_sp']} kinh doanh trở lại."


# ---------- Controller ----------
class SanPhamController:
    @staticmethod
    @require_roles(*TAT_CA)
    def tim_kiem(tu_khoa="", danh_muc_id=None, sap_xep="ten", giam_dan=False,
                 trang=1, so_dong=20, ca_ngung_kd=False):
        tu_khoa = (tu_khoa or "").strip()
        quan_ly = Session.has_role(*QUAN_LY_KHO)
        # Chỉ Admin/Thủ kho mới được xem cả sản phẩm đã ngừng kinh doanh
        chi_kinh_doanh = not (ca_ngung_kd and quan_ly)

        tong = SanPham.dem(tu_khoa, danh_muc_id, chi_kinh_doanh)
        so_trang = max(1, -(-tong // so_dong))
        trang = min(max(trang, 1), so_trang)
        dong = SanPham.tim_kiem(tu_khoa, danh_muc_id, chi_kinh_doanh,
                                sap_xep, giam_dan, trang, so_dong)

        # Nhân viên bán hàng không được thấy giá nhập (giá vốn)
        if not quan_ly:
            for d in dong:
                d.pop("gia_nhap", None)

        return {"dong": dong, "tong": tong, "trang": trang, "so_trang": so_trang}

    @staticmethod
    @require_roles(*TAT_CA)
    def goi_y(tu_khoa, gioi_han=8):
        tu_khoa = (tu_khoa or "").strip()
        if len(tu_khoa) < 2:
            return []
        return SanPham.goi_y_ten(tu_khoa, gioi_han)

    @staticmethod
    @require_roles(*TAT_CA)
    def danh_sach_danh_muc():
        return DanhMuc.tat_ca()

    @staticmethod
    @require_roles(*TAT_CA)
    def danh_sach_don_vi():
        return DonViTinh.tat_ca()

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def chi_tiet(san_pham_id):
        """Dữ liệu đầy đủ để đổ vào form sửa."""
        return SanPham.tim_theo_id(san_pham_id)

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def them(du_lieu):
        """du_lieu: dict giá trị thô từ form. Trả về (True/False, thông điệp)."""
        d, loi = _chuan_hoa(du_lieu)
        if loi:
            return False, loi
        # Kiểm tra trước: cho thông báo thân thiện ở trường hợp thường gặp
        if SanPham.tim_theo_ma(d["ma_sp"]):
            return False, f"Mã sản phẩm {d['ma_sp']} đã tồn tại."
        try:
            with transaction() as conn:
                id_moi = SanPham.them(conn, d)
                NhatKy.ghi(conn, Session.get_user()["id"], "THEM", "san_pham",
                           id_moi, f"{d['ma_sp']} - {d['ten_sp']}")
        except DuLieuTrung:
            # Chốt chặn cuối: có người vừa tạo trùng mã đúng lúc ta lưu
            return False, f"Mã sản phẩm {d['ma_sp']} vừa được người khác tạo. Vui lòng chọn mã khác."
        return True, f"Đã thêm sản phẩm {d['ma_sp']}."

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def sua(san_pham_id, du_lieu):
        cu = SanPham.tim_theo_id(san_pham_id)
        if cu is None:
            return False, "Không tìm thấy sản phẩm."
        # Giá nhập là GIÁ VỐN BÌNH QUÂN do hệ thống tự tính khi nhập kho:
        # luôn giữ giá trị hiện có, bỏ qua mọi giá trị gửi lên.
        du_lieu = {**du_lieu, "gia_nhap": cu["gia_nhap"]}
        d, loi = _chuan_hoa(du_lieu)
        if loi:
            return False, loi
        trung = SanPham.tim_theo_ma(d["ma_sp"])
        if trung and trung["id"] != san_pham_id:
            return False, f"Mã sản phẩm {d['ma_sp']} đã được dùng cho sản phẩm khác."

        thay_doi = _mo_ta_thay_doi(cu, d)
        if not thay_doi:
            return True, "Không có thay đổi nào."
        try:
            with transaction() as conn:
                SanPham.sua(conn, san_pham_id, d)
                NhatKy.ghi(conn, Session.get_user()["id"], "SUA", "san_pham",
                           san_pham_id, thay_doi)
        except DuLieuTrung:
            return False, f"Mã sản phẩm {d['ma_sp']} vừa được người khác dùng. Vui lòng chọn mã khác."
        return True, "Đã cập nhật sản phẩm."

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def ngung_kinh_doanh(san_pham_id):
        return _doi_trang_thai(san_pham_id, "ngung_kinh_doanh")

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def kinh_doanh_lai(san_pham_id):
        return _doi_trang_thai(san_pham_id, "kinh_doanh")