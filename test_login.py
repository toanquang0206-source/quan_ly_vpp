import getpass

from controllers.auth_controller import AuthController
from utils.session import Session

print(AuthController.dang_nhap("", ""))
print(AuthController.dang_nhap("admin", "abc1234"))
print(AuthController.dang_nhap("khong_ton_tai", "abcdef"))

mk = getpass.getpass("Mật khẩu admin thật:")
print(AuthController.dang_nhap("admin", mk))
print(Session.get_user())