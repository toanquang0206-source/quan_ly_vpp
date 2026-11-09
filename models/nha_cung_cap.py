from database.connection import fetch_all


class NhaCungCap:
    @staticmethod
    def tat_ca(chi_hop_tac=True):
        dieu_kien = "WHERE trang_thai = 'hop_tac'" if chi_hop_tac else ""
        return fetch_all(f"SELECT id, ten_ncc, so_dien_thoai, trang_thai "
                         f"FROM nha_cung_cap {dieu_kien} ORDER BY ten_ncc")

    @staticmethod
    def tim_theo_id(conn, ncc_id):
        """Đọc trên CÙNG kết nối với transaction đang chạy."""
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, ten_ncc, trang_thai FROM nha_cung_cap WHERE id = %s", (ncc_id,))
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def danh_sach_day_du():
        return fetch_all(
            """SELECT n.id, n.ten_ncc, n.so_dien_thoai, n.email, n.dia_chi, n.trang_thai,
                      (SELECT COUNT(*) FROM phieu_nhap p WHERE p.nha_cung_cap_id = n.id) AS so_phieu_nhap
               FROM nha_cung_cap n ORDER BY n.trang_thai, n.ten_ncc""")

    @staticmethod
    def tim_theo_ten(ten):
        rows = fetch_all("SELECT id, ten_ncc FROM nha_cung_cap WHERE ten_ncc = %s", (ten,))
        return rows[0] if rows else None

    # ---------- trong transaction ----------
    @staticmethod
    def khoa_dong(conn, ncc_id):
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT id, ten_ncc, so_dien_thoai, email, dia_chi, trang_thai
               FROM nha_cung_cap WHERE id = %s FOR UPDATE""", (ncc_id,))
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def them(conn, ten, so_dien_thoai, email, dia_chi):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO nha_cung_cap (ten_ncc, so_dien_thoai, email, dia_chi)
               VALUES (%s, %s, %s, %s)""", (ten, so_dien_thoai, email, dia_chi))
        return cur.lastrowid

    @staticmethod
    def sua(conn, ncc_id, ten, so_dien_thoai, email, dia_chi):
        conn.cursor().execute(
            """UPDATE nha_cung_cap SET ten_ncc = %s, so_dien_thoai = %s, email = %s, dia_chi = %s
               WHERE id = %s""", (ten, so_dien_thoai, email, dia_chi, ncc_id))

    @staticmethod
    def doi_trang_thai(conn, ncc_id, trang_thai):
        conn.cursor().execute("UPDATE nha_cung_cap SET trang_thai = %s WHERE id = %s",
                              (trang_thai, ncc_id))