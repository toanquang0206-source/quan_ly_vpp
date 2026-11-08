# Tên vai trò, phải khớp với bảng vai_tro trong CSDL
ROLE_ADMIN = "Admin"
ROLE_THU_KHO = "Thủ kho"
ROLE_NHAN_VIEN = "Nhân viên bán hàng"


class Session:
    """'Thẻ nhân viên': nhớ ai đang đăng nhập (một bản dùng chung cho cả app)."""
    _user = None

    @classmethod
    def login(cls, user: dict):
        # Chỉ chép những gì cần dùng, cố ý KHÔNG chép mat_khau_hash
        cls._user = {
            "id": user["id"],
            "ten_dang_nhap": user["ten_dang_nhap"],
            "ho_ten": user["ho_ten"],
            "vai_tro": user["ten_vai_tro"],
            "phai_doi_mat_khau": bool(user.get("bat_buoc_doi_mat_khau", 0)),
        }

    @classmethod
    def logout(cls):
        cls._user = None

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._user is not None

    @classmethod
    def get_user(cls):
        return cls._user

    @classmethod
    def cap_nhat_vai_tro(cls, vai_tro):
        if cls._user is not None:
            cls._user["vai_tro"] = vai_tro

    @classmethod
    def phai_doi_mat_khau(cls) -> bool:
        return cls._user is not None and cls._user.get("phai_doi_mat_khau", False)

    @classmethod
    def da_doi_mat_khau(cls):
        if cls._user is not None:
            cls._user["phai_doi_mat_khau"] = False

    @classmethod
    def has_role(cls, *roles) -> bool:
        """vd: Session.has_role(ROLE_ADMIN, ROLE_THU_KHO)"""
        return cls._user is not None and cls._user["vai_tro"] in roles