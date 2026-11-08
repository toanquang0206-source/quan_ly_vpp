import secrets

import bcrypt

DO_DAI_TOI_THIEU = 8
_BANG_KY_TU_TAM = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"   # bỏ I l 1 O 0 dễ nhầm


def hash_password(plain: str) -> str:
    """Băm mật khẩu thô -> chuỗi lưu vào cột mat_khau_hash."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Kiểm tra mật khẩu người dùng gõ có khớp chuỗi băm đã lưu không."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def kiem_tra_mat_khau(mat_khau: str, ten_dang_nhap: str = ""):
    """Trả về thông báo lỗi nếu mật khẩu quá yếu, ngược lại trả về None."""
    if len(mat_khau) < DO_DAI_TOI_THIEU:
        return f"Mật khẩu phải có ít nhất {DO_DAI_TOI_THIEU} ký tự."
    if len(mat_khau.encode("utf-8")) > 72:                  # giới hạn của thuật toán bcrypt
        return "Mật khẩu quá dài (tối đa 72 byte)."
    if not any(c.isalpha() for c in mat_khau) or not any(c.isdigit() for c in mat_khau):
        return "Mật khẩu phải có cả chữ và số."
    if ten_dang_nhap and mat_khau.lower() == ten_dang_nhap.lower():
        return "Mật khẩu không được trùng tên đăng nhập."
    return None


def tao_mat_khau_tam(do_dai: int = 10) -> str:
    """Sinh mật khẩu tạm ngẫu nhiên (dùng module secrets, an toàn về mặt mật mã)."""
    while True:
        mat_khau = "".join(secrets.choice(_BANG_KY_TU_TAM) for _ in range(do_dai))
        if kiem_tra_mat_khau(mat_khau) is None:
            return mat_khau