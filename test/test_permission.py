from controllers.auth_controller import AuthController
from utils.permissions import require_roles, PermissionDenied
from utils.session import ROLE_AMIN, Session

@require_roles(ROLE_AMIN)
def xem_loi_nhuan():
    return "Lợi nhuận:..."
def thu():
    try:
        print(xem_loi_nhuan())
    except PermissionDenied as loi:
        print("CHẶN", loi)
thu()
Session._user = {"id": 99, "ten_dang_nhap": "x", "ho_ten": "X", "vai_tro": "Nhân viên bán hàng"}

thu()
Session.logout()

import getpass
AuthController.dang_nhap("admin", getpass.getpass("Mật khẩu admin:"))
thu()