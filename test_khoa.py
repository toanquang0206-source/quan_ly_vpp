import getpass
from controllers.auth_controller import AuthController
from controllers.nguoi_dung_controller import NguoiDungController
from utils.session import Session

AuthController.dang_nhap("admin", getpass.getpass("Mật khẩu admin:"))
my_id = Session.get_user()["id"]

print(NguoiDungController.khoa_tai_khoan(my_id))   # phải bị chặn: tự khóa mình
print(NguoiDungController.khoa_tai_khoan(9999))    # phải báo: không tìm thấy