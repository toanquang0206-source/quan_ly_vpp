from database.connection import fetch_all

class DanhMuc:
    @staticmethod
    def tat_ca():
        return fetch_all("SELECT id, ten_danh_muc FROM danh_muc ORDER BY ten_danh_muc")
    