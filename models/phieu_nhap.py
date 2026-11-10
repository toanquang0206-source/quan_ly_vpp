from database.connection import fetch_all


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class PhieuNhap:
    # ---------- ghi (giữ nguyên) ----------
    @staticmethod
    def them_phieu(conn, ma_tam, nha_cung_cap_id, nguoi_dung_id, ngay_nhap, tong_tien, ghi_chu):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO phieu_nhap
               (ma_phieu, nha_cung_cap_id, nguoi_dung_id, ngay_nhap, tong_tien, ghi_chu)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (ma_tam, nha_cung_cap_id, nguoi_dung_id, ngay_nhap, tong_tien, ghi_chu),
        )
        return cur.lastrowid

    @staticmethod
    def dat_ma(conn, phieu_id, ma_phieu):
        cur = conn.cursor()
        cur.execute("UPDATE phieu_nhap SET ma_phieu = %s WHERE id = %s", (ma_phieu, phieu_id))

    @staticmethod
    def them_dong(conn, phieu_id, san_pham_id, so_luong, gia_nhap):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chi_tiet_phieu_nhap (phieu_nhap_id, san_pham_id, so_luong, gia_nhap)
               VALUES (%s, %s, %s, %s)""",
            (phieu_id, san_pham_id, so_luong, gia_nhap),
        )

    # ---------- đọc (lịch sử phiếu nhập) ----------
    @staticmethod
    def _dieu_kien(tu_khoa, ncc_id, tu, den):
        dieu_kien, tham_so = [], []
        if tu_khoa:
            dieu_kien.append("p.ma_phieu LIKE %s")
            tham_so.append(f"%{_escape_like(tu_khoa)}%")
        if ncc_id:
            dieu_kien.append("p.nha_cung_cap_id = %s")
            tham_so.append(ncc_id)
        if tu:
            dieu_kien.append("p.ngay_nhap >= %s")
            tham_so.append(tu)
        if den:                                   # den = 0h của NGÀY KẾ TIẾP (khoảng nửa mở)
            dieu_kien.append("p.ngay_nhap < %s")
            tham_so.append(den)
        return ("WHERE " + " AND ".join(dieu_kien)) if dieu_kien else "", tham_so

    @staticmethod
    def dem(tu_khoa=None, ncc_id=None, tu=None, den=None):
        where, tham_so = PhieuNhap._dieu_kien(tu_khoa, ncc_id, tu, den)
        return fetch_all(f"SELECT COUNT(*) AS so FROM phieu_nhap p {where}", tham_so)[0]["so"]

    @staticmethod
    def danh_sach(tu_khoa, ncc_id, tu, den, trang=1, so_dong=8):
        where, tham_so = PhieuNhap._dieu_kien(tu_khoa, ncc_id, tu, den)
        offset = (max(trang, 1) - 1) * so_dong
        return fetch_all(
            f"""SELECT p.id, p.ma_phieu, p.ngay_nhap, p.tong_tien, n.ten_ncc, nd.ho_ten AS nguoi_lap,
                       (SELECT COUNT(*) FROM chi_tiet_phieu_nhap c WHERE c.phieu_nhap_id = p.id) AS so_mat_hang
                FROM phieu_nhap p
                JOIN nha_cung_cap n ON n.id = p.nha_cung_cap_id
                JOIN nguoi_dung nd ON nd.id = p.nguoi_dung_id
                {where}
                ORDER BY p.ngay_nhap DESC, p.id DESC
                LIMIT %s OFFSET %s""",
            tham_so + [so_dong, offset],
        )

    @staticmethod
    def tim_theo_id(phieu_id):
        rows = fetch_all(
            """SELECT p.id, p.ma_phieu, p.ngay_nhap, p.tong_tien, p.ghi_chu, n.ten_ncc,
                      nd.ho_ten AS nguoi_lap
               FROM phieu_nhap p
               JOIN nha_cung_cap n ON n.id = p.nha_cung_cap_id
               JOIN nguoi_dung nd ON nd.id = p.nguoi_dung_id
               WHERE p.id = %s""",
            (phieu_id,))
        return rows[0] if rows else None

    @staticmethod
    def dong_theo_phieu(phieu_id):
        return fetch_all(
            """SELECT c.san_pham_id, sp.ma_sp, sp.ten_sp, c.so_luong, c.gia_nhap
               FROM chi_tiet_phieu_nhap c JOIN san_pham sp ON sp.id = c.san_pham_id
               WHERE c.phieu_nhap_id = %s ORDER BY c.id""",
            (phieu_id,))