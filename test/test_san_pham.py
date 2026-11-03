import getpass

from controllers.auth_controller import AuthController
from controllers.san_pham_controller import SanPhamController

AuthController.dang_nhap("admin", getpass.getpass("Mật khẩu admin: "))

kq = SanPhamController.tim_kiem("but")
print("Tổng:", kq["tong"], "| Trang", kq["trang"], "/", kq["so_trang"])
for d in kq["dong"]:
    print(d["ma_sp"], d["ten_sp"], d["gia_ban"], d["ton_kho"])

print(SanPhamController.goi_y("bú"))