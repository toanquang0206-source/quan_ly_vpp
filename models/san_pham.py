from database.connection import fetch_all

def _escape_like(text):
    """Vô hiệu hóa % và _ do người dùng gõ"""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

class SanPham:
    #Danh sách cột được phép sắp xếp, Tên cột Không thể truyền bằng %s
    # nên ta chỉ cho chọn trong danh sách này, không bao giờ ghép chuỗi người dùng.
    SAP_XEP ={
        "ten": "sp.ten_sp",
        "ma": "sp.ma",
        "gia_ban": "sp.gia_ban",
        "ton_kho": "sp.ton_kho", 
    }

    @staticmethod
    def _dieu_kien(tu_khoa, danh_muc_id, chi_kinh_doanh):
        dieu_kien, tham_so =[], []
        if tu_khoa:
            mau = f"%{_escape_like(tu_khoa)}%"
            dieu_kien.append("(sp.ten_sp LIKE %s OR sp.ma_sp LIKE %s)")
            tham_so += [mau, mau]
        if danh_muc_id:
            dieu_kien.append("sp.danh_muc_id = %s")
            tham_so.append(danh_muc_id)
        if chi_kinh_doanh:
            dieu_kien.append("sp.trang_thai = 'kinh_doanh'")
        where = (" WHERE " + " AND ".join(dieu_kien)) if dieu_kien else ""
        return where, tham_so

    @staticmethod
    def dem(tu_khoa=None, danh_muc_id=None, chi_kinh_doanh=True):
        where, tham_so = SanPham._dieu_kien(tu_khoa, danh_muc_id, chi_kinh_doanh)
        return fetch_all(f"SELECT COUNT(*) AS so FROM san_pham sp {where}", tham_so)[0]["so"]

    @staticmethod
    def tim_kiem(tu_khoa=None, danh_muc_id=None, chi_kinh_doanh=True,
                 sap_xep="ten", giam_dan=False, trang=1, so_dong=20):
        where, tham_so = SanPham._dieu_kien(tu_khoa, danh_muc_id, chi_kinh_doanh)
        cot = SanPham.SAP_XEP.get(sap_xep, "sp.ten_sp") # ngoai danh sach -> mac dinh
        huong = "DESC" if giam_dan else "ASC"
        offset = (max(trang, 1) -1) * so_dong
        sql = f"""
            SELECT sp.id, sp.ma_sp, sp.ten_sp, dm.ten_danh_muc, dv.ten AS don_vi, 
            sp.gia_nhap, sp.gia_ban, sp.ton_kho, sp.ton_toi_thieu, sp.trang_thai
            FROM san_pham sp
            JOIN danh_muc dm ON dm.id = sp.danh_muc_id
            JOIN don_vi_tinh dv ON dv.id = sp.don_vi_tinh_id
            {where}
            ORDER BY {cot} {huong}, sp.id
            LIMIT %s OFFSET %s
        """
        return fetch_all(sql, tham_so + [so_dong, offset])

    @staticmethod
    def goi_y_ten(tu_khoa, gioi_han=8):
        sql = """
            SELECT ten_sp FROM san_pham
            WHERE trang_thai = 'kinh_doanh' AND ten_sp LIKE %s
            ORDER BY ten_sp LIMIT %s
        """
        rows = fetch_all(sql, (f"%{_escape_like(tu_khoa)}%", gioi_han))
        return [r["ten_sp"] for r in rows]

    # ĐỌC 1 DÒNG
    @staticmethod
    def tim_theo_id(san_pham_id):
        rows = fetch_all("SELECT * FROM san_pham WHERE id = %s", (san_pham_id,))
        return rows[0] if rows else None
    @staticmethod
    def tim_theo_ma(ma_sp):
        rows = fetch_all("SELECT * FROM san_pham WHERE ma_sp = %s", (ma_sp,))
        return rows[0] if rows else None


    # ghi : nhận conn để Controller gom nhiều bước vào 1 transaction
    # Cố ý KHÔNG có cột ton_kho: tồn kho chỉ đổi qua nhập/bán/trả/kiểm kê.

    @staticmethod
    def them(conn, d):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO san_pham
                (ma_sp, ten_sp, danh_muc_id, don_vi_tinh_id, gia_nhap, gia_ban, ton_toi_thieu, mo_ta)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (d["ma_sp"], d["ten_sp"], d["danh_muc_id"], d["don_vi_tinh_id"],
            d["gia_nhap"], d["gia_ban"], d["ton_toi_thieu"], d["mo_ta"] or None),
        )
        return cur.lastrowid

    @staticmethod
    def sua(conn, san_pham_id, d):
        cur = conn.cursor()
        cur.execute(
            """UPDATE san_pham
                SET ma_sp=%s, ten_sp=%s, danh_muc_id=%s, don_vi_tinh_id=%s,
                    gia_nhap=%s, gia_ban=%s, ton_toi_thieu=%s, mo_ta=%s
                WHERE id=%s""",
            (d["ma_sp"], d["ten_sp"], d["danh_muc_id"], d["don_vi_tinh_id"],
             d["gia_nhap"], d["gia_ban"], d["ton_toi_thieu"], d["mo_ta"] or None,
             san_pham_id),
        )

    @staticmethod
    def doi_trang_thai(conn, san_pham_id, trang_thai):
        cur = conn.cursor()
        cur.execute("UPDATE san_pham SET trang_thai=%s WHERE id=%s", 
                    (trang_thai, san_pham_id))

        # ---------- phục vụ nhập kho ----------
    @staticmethod
    def khoa_dong(conn, san_pham_id):
        """
        Đọc một sản phẩm và KHÓA dòng đó đến hết transaction (SELECT ... FOR UPDATE).
        Dùng khi bắt buộc phải 'đọc rồi mới tính rồi mới ghi' (tính giá vốn bình quân):
        ai khác muốn sửa dòng này phải xếp hàng chờ ta xong.
        """
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT id, ma_sp, ten_sp, trang_thai, ton_kho, gia_nhap, gia_ban
               FROM san_pham WHERE id = %s FOR UPDATE""",
            (san_pham_id,),
        )
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def cap_nhat_sau_nhap(conn, san_pham_id, so_luong, gia_von_moi):
        """Cộng tồn và cập nhật giá vốn bình quân (cột gia_nhap) trong một câu lệnh."""
        cur = conn.cursor()
        cur.execute(
            "UPDATE san_pham SET ton_kho = ton_kho + %s, gia_nhap = %s WHERE id = %s",
            (so_luong, gia_von_moi, san_pham_id),
        )
        # ---------- phục vụ màn hình nhập kho ----------
    @staticmethod
    def goi_y_cho_nhap(tu_khoa, gioi_han=8):
        """Gợi ý sản phẩm ĐANG KINH DOANH theo mã hoặc tên, kèm tồn và giá vốn hiện tại."""
        mau = f"%{_escape_like(tu_khoa)}%"
        return fetch_all(
            """SELECT id, ma_sp, ten_sp, ton_kho, gia_nhap FROM san_pham
               WHERE trang_thai = 'kinh_doanh' AND (ten_sp LIKE %s OR ma_sp LIKE %s)
               ORDER BY ten_sp LIMIT %s""",
            (mau, mau, gioi_han),
        )

    @staticmethod
    def tim_nhieu_theo_id(ds_id):
        """Đọc nhiều sản phẩm bằng MỘT truy vấn. Trả về dict id -> dòng."""
        if not ds_id:
            return {}
        cho = ", ".join(["%s"] * len(ds_id))          # chỉ ghép các dấu %s, không ghép dữ liệu
        rows = fetch_all(
            f"""SELECT id, ma_sp, ten_sp, trang_thai, ton_kho, gia_nhap, gia_ban
                FROM san_pham WHERE id IN ({cho})""",
            tuple(ds_id),
        )
        return {r["id"]: r for r in rows}

        # ---------- phục vụ bán hàng ----------
    @staticmethod
    def goi_y_cho_ban(tu_khoa, gioi_han=8):
        """Gợi ý cho quầy bán: KHÔNG trả về giá nhập/giá vốn. Mã khớp đúng được xếp lên đầu."""
        mau = f"%{_escape_like(tu_khoa)}%"
        return fetch_all(
            """SELECT id, ma_sp, ten_sp, ton_kho, gia_ban FROM san_pham
               WHERE trang_thai = 'kinh_doanh' AND (ten_sp LIKE %s OR ma_sp LIKE %s)
               ORDER BY (ma_sp = %s) DESC, ten_sp LIMIT %s""",
            (mau, mau, tu_khoa, gioi_han),
        )

    @staticmethod
    def tru_ton(conn, san_pham_id, so_luong):
        """Trừ tồn CÓ ĐIỀU KIỆN trong một câu lệnh. Trả về False nếu không đủ hàng."""
        cur = conn.cursor()
        cur.execute(
            "UPDATE san_pham SET ton_kho = ton_kho - %s WHERE id = %s AND ton_kho >= %s",
            (so_luong, san_pham_id, so_luong),
        )
        return cur.rowcount == 1
    # ---------- phục vụ màn hình thẻ kho ----------
    @staticmethod
    def goi_y_the_kho(tu_khoa, gioi_han=8):
        """Gợi ý cho Thẻ kho: gồm CẢ sản phẩm đã ngừng kinh doanh (lịch sử vẫn còn nguyên)."""
        mau = f"%{_escape_like(tu_khoa)}%"
        return fetch_all(
            """SELECT id, ma_sp, ten_sp, ton_kho, trang_thai FROM san_pham
               WHERE ten_sp LIKE %s OR ma_sp LIKE %s
               ORDER BY (ma_sp = %s) DESC, ten_sp LIMIT %s""",
            (mau, mau, tu_khoa, gioi_han),
        )