import getpass

from models.nguoi_dung import NguoiDung
from utils.security import hash_password

TEN = "admin"
VAI_TRO_ADMIN_ID = 1

if NguoiDung.tim_theo_ten_dang_nhap(TEN):
    print("Tài khoản đã tồn tại !")
else:
    mat_khau = getpass.getpass("Đặt mật khẩu cho admin (tối thiểu 6 ký tự):")
    if len(mat_khau) <6:
        print("Mật khẩu quá ngắn, chưa tạo tài khoản.")
    else:
        NguoiDung.them(TEN, hash_password(mat_khau), "Quản trị viên", VAI_TRO_ADMIN_ID)
        print("Đã tạo tài khoản admin")