from database.connection import fetch_all


class DonViTinh:
    @staticmethod
    def tat_ca():
        return fetch_all("SELECT id, ten FROM don_vi_tinh ORDER BY ten")

    @staticmethod
    def danh_sach_day_du():
        return fetch_all(
            """SELECT dv.id, dv.ten,
                      (SELECT COUNT(*) FROM san_pham sp WHERE sp.don_vi_tinh_id = dv.id) AS so_san_pham
               FROM don_vi_tinh dv ORDER BY dv.ten""")

    @staticmethod
    def tim_theo_ten(ten):
        rows = fetch_all("SELECT id, ten FROM don_vi_tinh WHERE ten = %s", (ten,))
        return rows[0] if rows else None

    # ---------- trong transaction ----------
    @staticmethod
    def khoa_dong(conn, don_vi_id):
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, ten FROM don_vi_tinh WHERE id = %s FOR UPDATE", (don_vi_id,))
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def dem_san_pham(conn, don_vi_id):
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM san_pham WHERE don_vi_tinh_id = %s", (don_vi_id,))
        return cur.fetchone()[0]

    @staticmethod
    def them(conn, ten):
        cur = conn.cursor()
        cur.execute("INSERT INTO don_vi_tinh (ten) VALUES (%s)", (ten,))
        return cur.lastrowid

    @staticmethod
    def sua(conn, don_vi_id, ten):
        conn.cursor().execute("UPDATE don_vi_tinh SET ten = %s WHERE id = %s", (ten, don_vi_id))

    @staticmethod
    def xoa(conn, don_vi_id):
        conn.cursor().execute("DELETE FROM don_vi_tinh WHERE id = %s", (don_vi_id,))