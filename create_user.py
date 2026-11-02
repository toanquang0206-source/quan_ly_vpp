import getpass

from models.nguoi_dung import NguoiDung
from utils.security import hash_password

print("Vai trò : 1 = Admin, 2 = Thủ kho, 3 = Nhân viên bán hàng")
vai_tro_id = int(input("Chọn vai trò(1-3): "))
ten = input("Tên đăng nhập: ").strip()
ho_ten = input("Họ tên:").strip()
mat_khau = getpass.getpass("Mật khẩu( tối thiểu 6 ký tự):")

if vai_tro_id not in (1, 2, 3) or not ten or not ho_ten:
    print("Thông tin chưa hợp lệ.")
elif len(mat_khau) < 6:
    print("Mật khẩu quá ngắn.")
elif NguoiDung.tim_theo_ten_dang_nhap(ten):
    print("Tên đăng nhập đã tồn tại.")
else:
    NguoiDung.them(ten, hash_password(mat_khau), ho_ten, vai_tro_id)
    print("Đã tạo tài khoản.")