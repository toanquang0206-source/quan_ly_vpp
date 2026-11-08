from database.connection import fetch_all, transaction


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class NguoiDung:
    # ---------- đọc ----------
    @staticmethod
    def tim_theo_ten_dang_nhap(ten_dang_nhap):
        sql = """
            SELECT nd.id, nd.ten_dang_nhap, nd.mat_khau_hash, nd.ho_ten,
                   nd.trang_thai, nd.bat_buoc_doi_mat_khau, vt.ten_vai_tro
            FROM nguoi_dung nd
            JOIN vai_tro vt ON vt.id = nd.vai_tro_id
            WHERE nd.ten_dang_nhap = %s
        """
        rows = fetch_all(sql, (ten_dang_nhap,))
        return rows[0] if rows else None

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
    def danh_sach(tu_khoa=None):
        """Danh sách người dùng để hiển thị. KHÔNG bao giờ trả về chuỗi băm mật khẩu."""
        dieu_kien, tham_so = "", []
        if tu_khoa:
            mau = f"%{_escape_like(tu_khoa)}%"
            dieu_kien, tham_so = "WHERE nd.ten_dang_nhap LIKE %s OR nd.ho_ten LIKE %s", [mau, mau]
        return fetch_all(
            f"""SELECT nd.id, nd.ten_dang_nhap, nd.ho_ten, nd.trang_thai, nd.bat_buoc_doi_mat_khau,
                       nd.ngay_tao, nd.vai_tro_id, vt.ten_vai_tro
                FROM nguoi_dung nd JOIN vai_tro vt ON vt.id = nd.vai_tro_id
                {dieu_kien}
                ORDER BY vt.id, nd.ten_dang_nhap""",
            tham_so,
        )

    # ---------- ghi độc lập (giữ nguyên chữ ký cũ cho các script create_admin.py, create_user.py) ----------
    @staticmethod
    def them(ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id):
        with transaction() as conn:
            return NguoiDung.them_voi_conn(conn, ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id, 0)

    # ---------- trong transaction ----------
    @staticmethod
    def them_voi_conn(conn, ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id, bat_buoc_doi_mat_khau=1):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO nguoi_dung
               (ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id, bat_buoc_doi_mat_khau)
               VALUES (%s, %s, %s, %s, %s)""",
            (ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro_id, bat_buoc_doi_mat_khau),
        )
        return cur.lastrowid

    @staticmethod
    def khoa_admin_hoat_dong(conn):
        """
        Khóa (FOR UPDATE) mọi Admin đang hoạt động rồi trả về danh sách id của họ.
        Hai Admin cùng lúc khóa/hạ quyền nhau sẽ phải xếp hàng, nên hệ thống không bao giờ
        tự để mình không còn Admin nào. 'OF nd' để chỉ khóa bảng nguoi_dung, không khóa vai_tro.
        """
        cur = conn.cursor()
        cur.execute(
            """SELECT nd.id FROM nguoi_dung nd JOIN vai_tro vt ON vt.id = nd.vai_tro_id
               WHERE vt.ten_vai_tro = 'Admin' AND nd.trang_thai = 'hoat_dong'
               ORDER BY nd.id FOR UPDATE OF nd"""
        )
        return [r[0] for r in cur.fetchall()]

    @staticmethod
    def khoa_dong(conn, user_id):
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT nd.id, nd.ten_dang_nhap, nd.trang_thai, vt.ten_vai_tro
               FROM nguoi_dung nd JOIN vai_tro vt ON vt.id = nd.vai_tro_id
               WHERE nd.id = %s FOR UPDATE OF nd""",
            (user_id,),
        )
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def lay_hash(conn, user_id):
        cur = conn.cursor()
        cur.execute("SELECT mat_khau_hash FROM nguoi_dung WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return row[0] if row else None

    @staticmethod
    def cap_nhat_trang_thai(conn, user_id, trang_thai):
        conn.cursor().execute("UPDATE nguoi_dung SET trang_thai = %s WHERE id = %s", (trang_thai, user_id))

    @staticmethod
    def cap_nhat_vai_tro(conn, user_id, vai_tro_id):
        conn.cursor().execute("UPDATE nguoi_dung SET vai_tro_id = %s WHERE id = %s", (vai_tro_id, user_id))

    @staticmethod
    def cap_nhat_mat_khau(conn, user_id, mat_khau_hash, bat_buoc_doi):
        conn.cursor().execute(
            "UPDATE nguoi_dung SET mat_khau_hash = %s, bat_buoc_doi_mat_khau = %s WHERE id = %s",
            (mat_khau_hash, 1 if bat_buoc_doi else 0, user_id))