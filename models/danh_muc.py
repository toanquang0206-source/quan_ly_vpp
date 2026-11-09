from database.connection import fetch_all


class DanhMuc:
    @staticmethod
    def tat_ca():
        return fetch_all("SELECT id, ten_danh_muc FROM danh_muc ORDER BY ten_danh_muc")

    @staticmethod
    def danh_sach_day_du():
        return fetch_all(
            """SELECT dm.id, dm.ten_danh_muc, dm.mo_ta,
                      (SELECT COUNT(*) FROM san_pham sp WHERE sp.danh_muc_id = dm.id) AS so_san_pham
               FROM danh_muc dm ORDER BY dm.ten_danh_muc""")

    @staticmethod
    def tim_theo_ten(ten):
        rows = fetch_all("SELECT id, ten_danh_muc FROM danh_muc WHERE ten_danh_muc = %s", (ten,))
        return rows[0] if rows else None

    # ---------- trong transaction ----------
    @staticmethod
    def khoa_dong(conn, danh_muc_id):
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, ten_danh_muc, mo_ta FROM danh_muc WHERE id = %s FOR UPDATE",
                    (danh_muc_id,))
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def dem_san_pham(conn, danh_muc_id):
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM san_pham WHERE danh_muc_id = %s", (danh_muc_id,))
        return cur.fetchone()[0]

    @staticmethod
    def them(conn, ten, mo_ta):
        cur = conn.cursor()
        cur.execute("INSERT INTO danh_muc (ten_danh_muc, mo_ta) VALUES (%s, %s)", (ten, mo_ta or None))
        return cur.lastrowid

    @staticmethod
    def sua(conn, danh_muc_id, ten, mo_ta):
        conn.cursor().execute("UPDATE danh_muc SET ten_danh_muc = %s, mo_ta = %s WHERE id = %s",
                              (ten, mo_ta or None, danh_muc_id))

    @staticmethod
    def xoa(conn, danh_muc_id):
        conn.cursor().execute("DELETE FROM danh_muc WHERE id = %s", (danh_muc_id,))