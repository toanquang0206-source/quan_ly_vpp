from database.connection import fetch_all, transaction

class NguoiDung:

    @staticmethod
    def tim_theo_ten_dang_nhap(ten_dang_nhap):
        sql = """
            SELECT nd.id, nd.ten_dang_nhap, nd.mat_khau_hash, nd.ho_ten, nd.trang_thai, vt.ten_vai_tro
            FROM nguoi_dung nd
            JOIN vai_tro vt ON vt.id = nd.vai_tro_id
            WHERE nd.ten_dang_nhap = %s
        """
        rows = fetch_all(sql, (ten_dang_nhap,))
        return rows[0] if rows else None
    @staticmethod
    def them(ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id):
        sql = """
            INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id)
            VALUES (%s, %s, %s, %s)
        """
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id))
            return cur.lastrowid

    @staticmethod
    def tim_theo_id(user_id):
        sql = """
            SELECT nd.id, nd.ten_dang_nhap, nd.ho_ten, nd.trang_thai, vt.ten_vai_tro
            FROM nguoi_dung nd
            JOIN vai_tro vt ON vt.id = nd.vai_tro_id
            WHERE nd.id = %s
            """
        rows = fetch_all(sql, (user_id,))
        return rows[0] if rows else None

    @staticmethod
    def dem_theo_vai_tro_hoat_dong(ten_vai_tro):
        sql = """
            SELECT COUNT(*) AS so
            FROM nguoi_dung nd
            JOIN vai_tro vt ON vt.id = nd.vai_tro_id
            WHERE vt.ten_vai_tro = %s AND nd.trang_thai = 'hoat_dong'
        """
        return fetch_all(sql, (ten_vai_tro,))[0]["so"]

    @staticmethod
    def cap_nhat_trang_thai(user_id, trang_thai):
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE nguoi_dung SET trang_thai = %s WHERE id = %s",
                (trang_thai, user_id), 
            )
            return cur.rowcount
