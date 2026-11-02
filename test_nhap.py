import getpass

from controllers.auth_controller import AuthController
from controllers.nhap_kho_controller import NhapKhoController as NK
from controllers.san_pham_controller import SanPhamController as SP
from models.san_pham import SanPham

AuthController.dang_nhap("admin", getpass.getpass("Mật khẩu admin: "))

SP.them({"ma_sp": "TESTBUT", "ten_sp": "Bút thử", "danh_muc_id": 1,
         "don_vi_tinh_id": 1, "gia_nhap": "3000", "gia_ban": "5000"})
sp = SanPham.tim_theo_ma("TESTBUT")

print(NK.tao_phieu_nhap(1, [{"san_pham_id": sp["id"], "so_luong": 100, "gia_nhap": 3000}]))
print(NK.tao_phieu_nhap(1, [{"san_pham_id": sp["id"], "so_luong": 100, "gia_nhap": 3500}]))

sp = SanPham.tim_theo_ma("TESTBUT")
print("Tồn:", sp["ton_kho"], "| Giá vốn bình quân:", int(sp["gia_nhap"]))   # phải ra 200 và 3250