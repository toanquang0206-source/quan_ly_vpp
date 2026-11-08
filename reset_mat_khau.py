"""
CỬA SAU CỨU HỘ khi quên mật khẩu (kể cả khi đó là Admin duy nhất).

Chạy NGOÀI ứng dụng, tại máy có cài MySQL của dự án:
    python reset_mat_khau.py

Lý do nằm ngoài app: bằng chứng "tôi là chủ" ở đây là QUYỀN TRUY CẬP VÀO MÁY CHỨA DỮ LIỆU.
Một nút "Quên mật khẩu" trong giao diện thì ai cũng bấm được.
"""
import getpass

from database.connection import fetch_all, transaction
from models.nhat_ky import NhatKy
from utils.security import hash_password, kiem_tra_mat_khau


def dat_lai(ten_dang_nhap, mat_khau_moi):
    """Trả về (True/False, thông điệp). Đồng thời mở khóa tài khoản và xóa cờ bắt buộc đổi mật khẩu."""
    ten = (ten_dang_nhap or "").strip().lower()
    rows = fetch_all("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = %s", (ten,))
    if not rows:
        return False, f"Không có tài khoản nào tên '{ten}'."
    loi = kiem_tra_mat_khau(mat_khau_moi, ten)
    if loi:
        return False, loi
    user_id = rows[0]["id"]
    with transaction() as conn:
        conn.cursor().execute(
            """UPDATE nguoi_dung SET mat_khau_hash = %s, trang_thai = 'hoat_dong',
                      bat_buoc_doi_mat_khau = 0 WHERE id = %s""",
            (hash_password(mat_khau_moi), user_id))
        NhatKy.ghi(conn, user_id, "DAT_LAI_MAT_KHAU_NGOAI_UNG_DUNG", "nguoi_dung", user_id,
                   "Đặt lại bằng reset_mat_khau.py (cần quyền truy cập máy chứa CSDL)")
    return True, f"Đã đặt lại mật khẩu cho '{ten}' và mở khóa tài khoản."


def main():
    print("=== ĐẶT LẠI MẬT KHẨU (chạy ngoài ứng dụng) ===")
    ten = input("Tên đăng nhập cần đặt lại mật khẩu: ")
    mat_khau = getpass.getpass("Mật khẩu mới (ít nhất 8 ký tự, có chữ và số): ")
    if mat_khau != getpass.getpass("Nhập lại mật khẩu mới: "):
        print("Hai lần nhập không khớp.")
        return
    print(dat_lai(ten, mat_khau)[1])


if __name__ == "__main__":
    main()