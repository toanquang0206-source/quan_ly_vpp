from models.nguoi_dung import NguoiDung
from utils.permissions import require_roles
from utils.session import ROLE_AMIN, Session

class NguoiDungController:
    @staticmethod
    @require_roles(ROLE_AMIN)
    def khoa_tai_khoan(user_id):
        """Trả về (True/False, thông điệp)."""
        user = NguoiDung.tim_theo_id(user_id)
        if user is None:
            return False, "Không tìm thấy người dùng."
        if user["trang_thai"] == "khoa":
            return False, "Tài khoản này đã bị khóa rồi."

        # không tự khóa tài khoản của chính mình
        if user_id == Session.get_user()["id"]:
            return False, "Bạn không thể tự khóa tài khoản của chính mình."

        # không khóa Admin cuối cùng
        if ((user["ten_vai_tro"]) == ROLE_AMIN and NguoiDung.dem_theo_vai_tro_hoat_dong(ROLE_AMIN) <=1):
            return False, "Không thể khóa Admin cuối cùng của hệ thống."

        NguoiDung.cap_nhat_trang_thai(user_id, "khoa")
        return True, f"Đã khóa tài khoản {user['ten_dang_nhap']}."