from database.connection import fetch_all

class DonViTinh:
    @staticmethod
    def tat_ca():
        return fetch_all("SELECT id, ten FROM don_vi_tinh ORDER BY ten")