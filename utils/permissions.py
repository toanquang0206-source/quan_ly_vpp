from functools import wraps
from models.nguoi_dung import NguoiDung
from utils.session import Session

class PermissionDenied(Exception):
    """Ném ra khi người dùng không đủ quyền. View sẽ bắt và hiển thị."""

def require_roles(*roles):
    """Chỉ cho các vai trò trong 'roles' chạy hàm này."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not Session.is_logged_in():
                raise PermissionDenied("Bạn chưa đăng nhập.")
            # Hỏi lại CSDL: trạng thái và vai trò Hiện Tại,
            # không tin "thẻ" cũ nằm trong bộ nhớ
            
            hien_tai = NguoiDung.tim_theo_id(Session.get_user()["id"])
            Session.cap_nhat_vai_tro(hien_tai["ten_vai_tro"])
            if hien_tai is None or hien_tai["trang_thai"] != "hoat_dong":
                Session.logout()
                raise PermissionDenied("Tài khoản bị khóa hoặc không tồn tại")
            if hien_tai["ten_vai_tro"] not in roles:
                raise PermissionDenied("Bạn không có quyền thực hiện chức năng này.")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
