import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk, messagebox, simpledialog

from controllers.hoa_don_controller import HoaDonController
from utils.formatters import dinh_dang_gio, dinh_dang_tien
from utils.session import ROLE_ADMIN, Session
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke
from views.tra_hang_form import TraHangForm

SO_DONG = 6
THOI_GIAN_THONG_BAO_MS = 6000
NHAN_PHUONG_THUC = {"tien_mat": "Tiền mặt", "chuyen_khoan": "Chuyển khoản", "the": "Thẻ"}
KHOANG_NHANH = ["Tất cả", "Hôm nay", "7 ngày qua", "30 ngày qua"]

COT = ("ma", "gio", "nhan_vien", "hinh_thuc", "tong", "da_hoan", "trang_thai")
TIEU_DE = {"ma": "Mã hóa đơn", "gio": "Thời gian", "nhan_vien": "Nhân viên",
           "hinh_thuc": "Hình thức", "tong": "Tổng tiền", "da_hoan": "Đã hoàn", "trang_thai": "Trạng thái"}
DO_RONG = {"ma": 150, "gio": 140, "nhan_vien": 140, "hinh_thuc": 110, "tong": 120,
           "da_hoan": 110, "trang_thai": 110}
CAN_PHAI = {"tong", "da_hoan"}

COT_DONG = ("ma_sp", "ten_sp", "so_luong", "don_gia", "thanh_tien", "da_tra")
TIEU_DE_DONG = {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "so_luong": "Số lượng",
                "don_gia": "Đơn giá", "thanh_tien": "Thành tiền", "da_tra": "Đã trả"}
DO_RONG_DONG = {"ma_sp": 100, "ten_sp": 320, "so_luong": 90, "don_gia": 120, "thanh_tien": 130, "da_tra": 90}
CAN_PHAI_DONG = {"so_luong", "don_gia", "thanh_tien", "da_tra"}


class HoaDonView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_ma = tk.StringVar()
        self.var_tu = tk.StringVar()
        self.var_den = tk.StringVar()
        self.var_nhanh = tk.StringVar(value="Tất cả")
        self.trang, self.so_trang = 1, 1
        self.hd_dang_chon = None
        self._ct = None                         # chi tiết hóa đơn đang xem (dữ liệu từ Controller)
        self._job_thong_bao = None
        self.btn_huy = None
        self._xay_dung()
        self.bind("<Destroy>", self._huy_cong_viec)

    # ---------- dựng giao diện ----------
    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tim = ttk.Frame(self)
        tim.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(tim, text="Mã hóa đơn").pack(side="left")
        o_ma = ttk.Entry(tim, textvariable=self.var_ma, width=18)
        o_ma.pack(side="left", padx=(6, 14))
        ttk.Label(tim, text="Từ ngày").pack(side="left")
        o_tu = ttk.Entry(tim, textvariable=self.var_tu, width=11)
        o_tu.pack(side="left", padx=(6, 10))
        ttk.Label(tim, text="Đến ngày").pack(side="left")
        o_den = ttk.Entry(tim, textvariable=self.var_den, width=11)
        o_den.pack(side="left", padx=(6, 10))
        cbo = ttk.Combobox(tim, textvariable=self.var_nhanh, values=KHOANG_NHANH,
                           state="readonly", width=13)
        cbo.pack(side="left", padx=(0, 10))
        cbo.bind("<<ComboboxSelected>>", lambda e: self._ap_dung_nhanh())
        ttk.Button(tim, text="Tìm", command=self._tim, style="Accent.TButton").pack(side="left")
        for o in (o_ma, o_tu, o_den):
            o.bind("<Return>", lambda e: self._tim())
        ttk.Label(tim, text="Ngày nhập dạng 25/10/2026", style="Phu.TLabel").pack(side="right")

        self.tree = ttk.Treeview(self, columns=COT, show="headings", height=5, selectmode="browse")
        for cot in COT:
            can = "e" if cot in CAN_PHAI else "w"
            self.tree.heading(cot, text=TIEU_DE[cot], anchor=can)
            self.tree.column(cot, width=DO_RONG[cot], anchor=can)
        self.tree.tag_configure("da_huy", foreground="#9CA3AF")
        self.tree.tag_configure("co_tra", foreground=MAU["canh_bao"])
        self.tree.grid(row=1, column=0, sticky="nsew")
        cuon = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        cuon.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=cuon.set)
        self.tree.bind("<<TreeviewSelect>>", self._khi_chon)

        trang = ttk.Frame(self)
        trang.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 8))
        self.btn_truoc = ttk.Button(trang, text="‹ Trước", command=lambda: self._chuyen_trang(-1))
        self.btn_truoc.pack(side="left")
        self.lbl_trang = ttk.Label(trang, text="")
        self.lbl_trang.pack(side="left", padx=12)
        self.btn_sau = ttk.Button(trang, text="Sau ›", command=lambda: self._chuyen_trang(1))
        self.btn_sau.pack(side="left")

        # ----- Chi tiết hóa đơn đang chọn -----
        ct = ttk.LabelFrame(self, text="Chi tiết hóa đơn", padding=10)
        ct.grid(row=3, column=0, columnspan=2, sticky="ew")
        ct.grid_columnconfigure(0, weight=1)
        self.lbl_ma = ttk.Label(ct, text="Chọn một hóa đơn ở bảng trên", style="TieuDe.TLabel")
        self.lbl_ma.grid(row=0, column=0, sticky="w")
        self.lbl_thong_tin = ttk.Label(ct, text="", style="Phu.TLabel")
        self.lbl_thong_tin.grid(row=1, column=0, sticky="w")
        self.lbl_han = ttk.Label(ct, text="")
        self.lbl_han.grid(row=2, column=0, sticky="w", pady=(0, 6))

        self.tree_dong = ttk.Treeview(ct, columns=COT_DONG, show="headings", height=3,
                                      selectmode="none")
        for cot in COT_DONG:
            can = "e" if cot in CAN_PHAI_DONG else "w"
            self.tree_dong.heading(cot, text=TIEU_DE_DONG[cot], anchor=can)
            self.tree_dong.column(cot, width=DO_RONG_DONG[cot], anchor=can)
        self.tree_dong.grid(row=3, column=0, sticky="ew")

        nut = ttk.Frame(ct)
        nut.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.btn_tra = ttk.Button(nut, text="Trả hàng...", command=self._tra_hang,
                                  style="Accent.TButton", state="disabled")
        self.btn_tra.pack(side="left")
        if Session.has_role(ROLE_ADMIN):          # chỉ Admin mới có nút hủy hóa đơn
            self.btn_huy = ttk.Button(nut, text="Hủy hóa đơn", command=self._huy,
                                      style="Danger.TButton", state="disabled")
            self.btn_huy.pack(side="left", padx=8)
        self.lbl_ly_do = ttk.Label(nut, text="", style="Phu.TLabel")
        self.lbl_ly_do.pack(side="left", padx=8)

        self.lbl_thong_bao = ttk.Label(self, text="")
        self.lbl_thong_bao.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _goi(self, ham, *args, **kwargs):
        return goi_controller(self, ham, *args, **kwargs)

    def _bao(self, thong_diep, loi=False):
        self.lbl_thong_bao.config(text=thong_diep,
                                  foreground=MAU["nguy_hiem"] if loi else MAU["thanh_cong"])
        if self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
        self._job_thong_bao = self.after(
            THOI_GIAN_THONG_BAO_MS, lambda: self.lbl_thong_bao.config(text=""))

    # ---------- danh sách + tìm kiếm ----------
    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: nạp lại danh sách, GIỮ NGUYÊN bộ lọc, trang và hóa đơn đang chọn."""
        self._tai_du_lieu()

    def _ap_dung_nhanh(self):
        hom_nay, chon = date.today(), self.var_nhanh.get()
        dinh_dang = "%d/%m/%Y"
        if chon == "Hôm nay":
            tu, den = hom_nay, hom_nay
        elif chon == "7 ngày qua":
            tu, den = hom_nay - timedelta(days=6), hom_nay
        elif chon == "30 ngày qua":
            tu, den = hom_nay - timedelta(days=29), hom_nay
        else:
            tu = den = None
        self.var_tu.set(tu.strftime(dinh_dang) if tu else "")
        self.var_den.set(den.strftime(dinh_dang) if den else "")
        self._tim()

    def _tim(self):
        self.trang = 1
        self._tai_du_lieu()

    def _chuyen_trang(self, huong):
        self.trang += huong
        self._tai_du_lieu()

    def _tai_du_lieu(self):
        kq = self._goi(HoaDonController.tim_kiem, self.var_ma.get(), self.var_tu.get(),
                       self.var_den.get(), self.trang, SO_DONG)
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return
        self.trang, self.so_trang = du_lieu["trang"], du_lieu["so_trang"]

        chon_truoc = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for d in du_lieu["dong"]:
            if d["trang_thai"] == "da_huy":
                nhan, tag = "Đã hủy", ("da_huy",)
            elif d["da_hoan"] > 0:
                nhan, tag = "Có trả hàng", ("co_tra",)
            else:
                nhan, tag = "Hoàn thành", ()
            self.tree.insert("", "end", iid=str(d["id"]), tags=tag, values=(
                d["ma_hoa_don"], dinh_dang_gio(d["ngay_lap"]), d["nhan_vien"],
                NHAN_PHUONG_THUC.get(d["phuong_thuc_thanh_toan"], ""),
                dinh_dang_tien(d["tong_thanh_toan"]),
                dinh_dang_tien(d["da_hoan"]) if d["da_hoan"] else "", nhan))
        to_mau_xen_ke(self.tree)

        self.lbl_trang.config(text=f"Trang {self.trang}/{self.so_trang}  —  {du_lieu['tong']} hóa đơn")
        self.btn_truoc.config(state="normal" if self.trang > 1 else "disabled")
        self.btn_sau.config(state="normal" if self.trang < self.so_trang else "disabled")

        if chon_truoc and self.tree.exists(chon_truoc[0]):
            self.tree.selection_set(chon_truoc[0])
            self._hien_chi_tiet(int(chon_truoc[0]))     # làm mới chi tiết của hóa đơn đang xem
        else:
            self._xoa_chi_tiet()

    # ---------- chi tiết một hóa đơn ----------
    def _khi_chon(self, event=None):
        chon = self.tree.selection()
        if chon:
            self._hien_chi_tiet(int(chon[0]))

    def _xoa_chi_tiet(self):
        self.hd_dang_chon, self._ct = None, None
        self.lbl_ma.config(text="Chọn một hóa đơn ở bảng trên")
        for lbl in (self.lbl_thong_tin, self.lbl_han, self.lbl_ly_do):
            lbl.config(text="")
        self.tree_dong.delete(*self.tree_dong.get_children())
        self.btn_tra.config(state="disabled")
        if self.btn_huy:
            self.btn_huy.config(state="disabled")

    def _hien_chi_tiet(self, hoa_don_id):
        kq = self._goi(HoaDonController.chi_tiet, hoa_don_id)
        if kq is None:
            return
        ok, thong_diep, ct = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return
        self.hd_dang_chon, self._ct = hoa_don_id, ct
        hd = ct["hoa_don"]

        self.lbl_ma.config(text=f"Hóa đơn {hd['ma_hoa_don']}")
        thong_tin = (f"Lập lúc {dinh_dang_gio(hd['ngay_lap'])}  ·  {hd['nhan_vien']}  ·  "
                     f"{NHAN_PHUONG_THUC.get(hd['phuong_thuc_thanh_toan'], '')}  ·  "
                     f"Tổng {dinh_dang_tien(hd['tong_thanh_toan'])}")
        if hd["da_hoan"]:
            thong_tin += f"  ·  Đã hoàn {dinh_dang_tien(hd['da_hoan'])}"
        self.lbl_thong_tin.config(text=thong_tin)

        if hd["trang_thai"] == "da_huy":
            self.lbl_han.config(text="Hóa đơn đã bị hủy", foreground=MAU["nguy_hiem"])
        elif ct["con_han"]:
            self.lbl_han.config(text=f"Còn hạn đổi trả đến {dinh_dang_gio(ct['han_doi_tra'])}",
                                foreground=MAU["thanh_cong"])
        else:
            self.lbl_han.config(text=f"Đã hết hạn đổi trả từ {dinh_dang_gio(ct['han_doi_tra'])}",
                                foreground=MAU["canh_bao"])

        self.tree_dong.delete(*self.tree_dong.get_children())
        for d in ct["dong"]:
            self.tree_dong.insert("", "end", values=(
                d["ma_sp"], d["ten_sp"], d["so_luong"], dinh_dang_tien(d["don_gia"]),
                dinh_dang_tien(d["thanh_tien"]), d["da_tra"] or ""))
        to_mau_xen_ke(self.tree_dong)

        self.btn_tra.config(state="normal" if ct["co_the_tra"] else "disabled")
        if self.btn_huy:
            self.btn_huy.config(state="normal" if ct["co_the_huy"] else "disabled")
        ly_do = ct["ly_do_khong_tra"] or ""
        if self.btn_huy and not ct["co_the_huy"] and ct["ly_do_khong_huy"] and not ly_do:
            ly_do = ct["ly_do_khong_huy"]
        self.lbl_ly_do.config(text=ly_do)

    # ---------- trả hàng, hủy hóa đơn ----------
    def _tra_hang(self):
        if self._ct is not None and self._ct["co_the_tra"]:
            TraHangForm(self, self._ct, self._sau_khi_tra)

    def _sau_khi_tra(self, thong_diep, du_lieu):
        self._tai_du_lieu()
        self._bao(f"{thong_diep} Hoàn trả khách {dinh_dang_tien(du_lieu['tien_hoan'])}.")

    def _huy(self):
        if self._ct is None or not self._ct["co_the_huy"]:
            return
        hd = self._ct["hoa_don"]
        ly_do = simpledialog.askstring("Hủy hóa đơn", f"Lý do hủy hóa đơn {hd['ma_hoa_don']}:",
                                       parent=self)
        if ly_do is None:
            return
        if not ly_do.strip():
            self._bao("Vui lòng nhập lý do hủy hóa đơn.", loi=True)
            return
        if not messagebox.askyesno(
                "Hủy hóa đơn",
                f"Hủy hóa đơn {hd['ma_hoa_don']} ({dinh_dang_tien(hd['tong_thanh_toan'])})?\n\n"
                f"Hàng sẽ được nhập lại kho và hóa đơn không còn tính vào doanh thu.",
                parent=self, icon="warning"):
            return
        kq = self._goi(HoaDonController.huy_hoa_don, hd["id"], ly_do)
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if ok:
            self._tai_du_lieu()
            self._bao(f"{thong_diep} Hoàn trả khách {dinh_dang_tien(du_lieu['tien_hoan'])}.")
        else:
            self._bao(thong_diep, loi=True)

    def _huy_cong_viec(self, event):
        if event.widget is self and self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
            self._job_thong_bao = None