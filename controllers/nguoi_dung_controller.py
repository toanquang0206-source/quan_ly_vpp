import re

from database.connection import transaction
from models.nguoi_dung import NguoiDung
from models.nhat_ky import NhatKy
from models.vai_tro import VaiTro
from utils.errors import DuLieuTrung, LoiNghiepVu
from utils.permissions import require_roles
from utils.security import hash_password, kiem_tra_mat_khau, tao_mat_khau_tam, verify_password
from utils.session import ROLE_ADMIN, ROLE_NHAN_VIEN, ROLE_THU_KHO, Session

CHI_ADMIN = (ROLE_ADMIN,)
TAT_CA = (ROLE_ADMIN, ROLE_THU_KHO, ROLE_NHAN_VIEN)
MAU_TEN_DANG_NHAP = re.compile(r"^[a-z0-9_.]{3,30}$")


# ---------------------------------------------------------------------------------------------
# Hai thao tác nhạy cảm nhận id NGƯỜI THỰC HIỆN làm tham số (không đọc Session bên trong),
# nên kiểm thử được cả tình huống hai Admin thao tác đồng thời.
# ---------------------------------------------------------------------------------------------
def doi_trang_thai_trong_txn(nguoi_thuc_hien_id, user_id, trang_thai_moi):
    khoa = trang_thai_moi == "khoa"
    if khoa and user_id == nguoi_thuc_hien_id:
        return False, "Bạn không thể tự khóa tài khoản của chính mình.", None
    ten = ""
    try:
        with transaction() as conn:
            admins = NguoiDung.khoa_admin_hoat_dong(conn)        # khóa các Admin trước
            nd = NguoiDung.khoa_dong(conn, user_id)
            if nd is None:
                raise LoiNghiepVu("Không tìm thấy người dùng.")
            ten = nd["ten_dang_nhap"]
            if nd["trang_thai"] == trang_thai_moi:
                raise LoiNghiepVu("Tài khoản này đã bị khóa rồi." if khoa
                                  else "Tài khoản này đang hoạt động.")
            if khoa and nd["ten_vai_tro"] == ROLE_ADMIN and len(admins) <= 1:
                raise LoiNghiepVu("Không thể khóa Admin cuối cùng của hệ thống.")
            NguoiDung.cap_nhat_trang_thai(conn, user_id, trang_thai_moi)
            NhatKy.ghi(conn, nguoi_thuc_hien_id, "KHOA_TAI_KHOAN" if khoa else "MO_KHOA_TAI_KHOAN",
                       "nguoi_dung", user_id, ten)
    except LoiNghiepVu as loi:
        return False, str(loi), None
    return True, (f"Đã khóa tài khoản {ten}." if khoa else f"Đã mở khóa tài khoản {ten}."), None


def doi_vai_tro_trong_txn(nguoi_thuc_hien_id, user_id, vai_tro_id):
    if user_id == nguoi_thuc_hien_id:
        return False, "Bạn không thể tự đổi vai trò của chính mình.", None
    ten = ""
    try:
        with transaction() as conn:
            admins = NguoiDung.khoa_admin_hoat_dong(conn)
            nd = NguoiDung.khoa_dong(conn, user_id)
            if nd is None:
                raise LoiNghiepVu("Không tìm thấy người dùng.")
            vt = VaiTro.tim_theo_id(conn, vai_tro_id)
            if vt is None:
                raise LoiNghiepVu("Vai trò không hợp lệ.")
            ten = nd["ten_dang_nhap"]
            if nd["ten_vai_tro"] == vt["ten_vai_tro"]:
                raise LoiNghiepVu("Người dùng đã có vai trò này rồi.")
            la_admin_dang_hoat_dong = nd["ten_vai_tro"] == ROLE_ADMIN and nd["trang_thai"] == "hoat_dong"
            if la_admin_dang_hoat_dong and len(admins) <= 1:
                raise LoiNghiepVu("Không thể hạ vai trò của Admin cuối cùng của hệ thống.")
            NguoiDung.cap_nhat_vai_tro(conn, user_id, vai_tro_id)
            NhatKy.ghi(conn, nguoi_thuc_hien_id, "DOI_VAI_TRO", "nguoi_dung", user_id,
                       f"{ten}: {nd['ten_vai_tro']} -> {vt['ten_vai_tro']}")
    except LoiNghiepVu as loi:
        return False, str(loi), None
    return True, f"Đã đổi vai trò của {ten} thành {vt['ten_vai_tro']}.", None


class NguoiDungController:
    # ---------- xem ----------
    @staticmethod
    @require_roles(*CHI_ADMIN)
    def danh_sach(tu_khoa=""):
        ban_than = Session.get_user()["id"]
        dong = NguoiDung.danh_sach((tu_khoa or "").strip())
        for d in dong:
            d["la_toi"] = d["id"] == ban_than
            d["cho_doi_mat_khau"] = bool(d["bat_buoc_doi_mat_khau"])
        return True, "OK", dong

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def danh_sach_vai_tro():
        return VaiTro.tat_ca()

    # ---------- thêm ----------
    @staticmethod
    @require_roles(*CHI_ADMIN)
    def them(ten_dang_nhap, ho_ten, vai_tro_id, mat_khau, nhap_lai):
        ten = (ten_dang_nhap or "").strip().lower()
        if not MAU_TEN_DANG_NHAP.match(ten):
            return False, ("Tên đăng nhập gồm 3-30 ký tự: chữ thường không dấu, số, "
                           "dấu chấm hoặc gạch dưới."), None
        ho_ten = (ho_ten or "").strip()
        if not ho_ten:
            return False, "Vui lòng nhập họ tên.", None
        if len(ho_ten) > 100:
            return False, "Họ tên tối đa 100 ký tự.", None
        if not vai_tro_id:
            return False, "Vui lòng chọn vai trò.", None
        if (mat_khau or "") != (nhap_lai or ""):
            return False, "Hai lần nhập mật khẩu không khớp.", None
        loi = kiem_tra_mat_khau(mat_khau or "", ten)
        if loi:
            return False, loi, None
        if NguoiDung.tim_theo_ten_dang_nhap(ten):
            return False, f"Tên đăng nhập {ten} đã tồn tại.", None

        hash_mk = hash_password(mat_khau)               # băm NGOÀI transaction vì khá chậm
        try:
            with transaction() as conn:
                vt = VaiTro.tim_theo_id(conn, int(vai_tro_id))
                if vt is None:
                    raise LoiNghiepVu("Vai trò không hợp lệ.")
                user_id = NguoiDung.them_voi_conn(conn, ten, hash_mk, ho_ten, vt["id"], 1)
                NhatKy.ghi(conn, Session.get_user()["id"], "THEM_NGUOI_DUNG", "nguoi_dung",
                           user_id, f"{ten} - {vt['ten_vai_tro']}")
        except LoiNghiepVu as e:
            return False, str(e), None
        except DuLieuTrung:
            return False, f"Tên đăng nhập {ten} vừa được người khác tạo. Vui lòng chọn tên khác.", None
        return True, (f"Đã tạo tài khoản {ten}. Người dùng sẽ phải đổi mật khẩu "
                      f"ở lần đăng nhập đầu tiên."), {"id": user_id}

    # ---------- đổi vai trò, khóa, mở khóa ----------
    @staticmethod
    @require_roles(*CHI_ADMIN)
    def doi_vai_tro(user_id, vai_tro_id):
        return doi_vai_tro_trong_txn(Session.get_user()["id"], user_id, vai_tro_id)

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def khoa_tai_khoan(user_id):
        return doi_trang_thai_trong_txn(Session.get_user()["id"], user_id, "khoa")

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def mo_khoa(user_id):
        return doi_trang_thai_trong_txn(Session.get_user()["id"], user_id, "hoat_dong")

    # ---------- mật khẩu ----------
    @staticmethod
    @require_roles(*CHI_ADMIN)
    def dat_lai_mat_khau(user_id):
        """
        Đặt mật khẩu TẠM ngẫu nhiên cho người khác và bắt họ đổi ở lần đăng nhập tới.
        Mật khẩu tạm chỉ được trả về MỘT lần này, không lưu ở đâu (kể cả nhật ký).
        """
        nguoi_id = Session.get_user()["id"]
        if user_id == nguoi_id:
            return False, "Muốn đổi mật khẩu của chính mình, hãy dùng nút Đổi mật khẩu.", None
        mat_khau_tam = tao_mat_khau_tam()
        hash_mk = hash_password(mat_khau_tam)
        try:
            with transaction() as conn:
                nd = NguoiDung.khoa_dong(conn, user_id)
                if nd is None:
                    raise LoiNghiepVu("Không tìm thấy người dùng.")
                NguoiDung.cap_nhat_mat_khau(conn, user_id, hash_mk, True)
                NhatKy.ghi(conn, nguoi_id, "DAT_LAI_MAT_KHAU", "nguoi_dung", user_id, nd["ten_dang_nhap"])
        except LoiNghiepVu as loi:
            return False, str(loi), None
        return True, f"Đã đặt lại mật khẩu cho {nd['ten_dang_nhap']}.", {
            "ten_dang_nhap": nd["ten_dang_nhap"], "mat_khau_tam": mat_khau_tam}

    @staticmethod
    @require_roles(*TAT_CA)
    def doi_mat_khau_cua_toi(mat_khau_cu, mat_khau_moi, nhap_lai):
        """Mọi vai trò đều tự đổi được mật khẩu của chính mình (phải biết mật khẩu hiện tại)."""
        user = Session.get_user()
        if not mat_khau_cu:
            return False, "Vui lòng nhập mật khẩu hiện tại.", None
        if (mat_khau_moi or "") != (nhap_lai or ""):
            return False, "Hai lần nhập mật khẩu mới không khớp.", None
        loi = kiem_tra_mat_khau(mat_khau_moi or "", user["ten_dang_nhap"])
        if loi:
            return False, loi, None
        if mat_khau_moi == mat_khau_cu:
            return False, "Mật khẩu mới phải khác mật khẩu hiện tại.", None
        try:
            with transaction() as conn:
                hash_cu = NguoiDung.lay_hash(conn, user["id"])
                if hash_cu is None or not verify_password(mat_khau_cu, hash_cu):
                    raise LoiNghiepVu("Mật khẩu hiện tại không đúng.")
                NguoiDung.cap_nhat_mat_khau(conn, user["id"], hash_password(mat_khau_moi), False)
                NhatKy.ghi(conn, user["id"], "DOI_MAT_KHAU", "nguoi_dung", user["id"], user["ten_dang_nhap"])
        except LoiNghiepVu as e:
            return False, str(e), None
        Session.da_doi_mat_khau()
        return True, "Đã đổi mật khẩu.", None