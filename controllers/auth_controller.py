from models.nguoi_dung import NguoiDung
from utils.security import verify_password
from utils.session import Session

THONG_BAO_SAI = "Tên đăng nhập hoặc mật khẩu không đúng"

class AuthController:
    @staticmethod
    def dang_nhap(ten_dang_nhap, mat_khau):
        """Trả về (True/False, thông điệp để View hiển thị)."""
        ten_dang_nhap = (ten_dang_nhap or "").strip()

        #1. Ô trống
        if not ten_dang_nhap or not mat_khau:
            return False, "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."

        #2. Tìm người dùng
        user = NguoiDung.tim_theo_ten_dang_nhap(ten_dang_nhap)
        #3. Không có người dùng hoặc sai mật khẩu: cùng 1 thông báo chung
        if user is None or not verify_password(mat_khau, user["mat_khau_hash"]):
            return False, THONG_BAO_SAI
        #4. Chỉ mật khẩu đúng =>
        if user["trang_thai"] != "hoat_dong":
            return False, "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên !"
        # ghi lại
        Session.login(user)
        return True, f"Xin chào, {user['ho_ten']}!"
    @staticmethod
    def dang_xuat():
        Session.logout()