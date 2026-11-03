import getpass
from controllers.auth_controller import AuthController
from controllers.san_pham_controller import SanPhamController as C
from models.san_pham import SanPham

AuthController.dang_nhap("admin", getpass.getpass("Mật khẩu admin: "))
form = {"ma_sp": "test01", "ten_sp": "Sản phẩm thử", "danh_muc_id": 1,
        "don_vi_tinh_id": 1, "gia_nhap": "3.000", "gia_ban": "5000",
        "ton_toi_thieu": "", "mo_ta": ""}
print(C.them(form))
print(C.them(form))

sp=SanPham.tim_theo_ma("TEST01")

print(C.sua(sp["id"], {**form, "ma_sp": "TEST01", "gia_ban": "6000"}))
print(C.ngung_kinh_doanh(sp["id"]))
print(C.kinh_doanh_lai(sp["id"]))
