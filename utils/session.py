ROLE_ADMIN = "Admin"
ROLE_THU_KHO = "Thủ kho"
ROLE_NHAN_VIEN = "Nhân viên bán hàng"

class Session:
    _user = None

    @classmethod
    def login(cls, user: dict):
        # những thông tin cần lưu
        cls._user = {
            "id": user["id"],
            "ten_dang_nhap": user["ten_dang_nhap"],
            "ho_ten": user["ho_ten"],
            "vai_tro": user["ten_vai_tro"]
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
    def has_role(cls, *roles) -> bool:
        """"""
        return cls._user is not None and cls._user["vai_tro"] in roles
    @classmethod
    def cap_nhat_vai_tro(cls, vai_tro):
        if cls._user is not None:
            cls._user["vai_tro"] = vai_tro