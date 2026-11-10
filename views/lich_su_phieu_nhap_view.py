import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

from controllers.kho_controller import LichSuPhieuNhapController
from utils.formatters import dinh_dang_gio, dinh_dang_so, dinh_dang_tien
from views.bao_cao_view import _tao_bang
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke

SO_DONG = 6
TAT_CA_NCC = "Tất cả nhà cung cấp"
KHOANG_NHANH = ["Tất cả", "Hôm nay", "7 ngày qua", "30 ngày qua"]


class LichSuPhieuNhapView(ttk.Frame):
    """Tìm lại các phiếu nhập đã lập và xem từng dòng hàng của phiếu."""

    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_ma = tk.StringVar()
        self.var_ncc = tk.StringVar(value=TAT_CA_NCC)
        self.var_tu, self.var_den = tk.StringVar(), tk.StringVar()
        self.var_nhanh = tk.StringVar(value="Tất cả")
        self.ds_ncc = {TAT_CA_NCC: None}          # tên -> id
        self.trang, self.so_trang = 1, 1
        self._xay_dung()

    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tim = ttk.Frame(self)
        tim.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(tim, text="Mã phiếu").pack(side="left")
        o_ma = ttk.Entry(tim, textvariable=self.var_ma, width=14)
        o_ma.pack(side="left", padx=(6, 10))
        ttk.Label(tim, text="Nhà cung cấp").pack(side="left")
        self.cbo_ncc = ttk.Combobox(tim, textvariable=self.var_ncc, state="readonly", width=20)
        self.cbo_ncc.pack(side="left", padx=(6, 10))
        ttk.Label(tim, text="Từ").pack(side="left")
        o_tu = ttk.Entry(tim, textvariable=self.var_tu, width=10)
        o_tu.pack(side="left", padx=(6, 8))
        ttk.Label(tim, text="Đến").pack(side="left")
        o_den = ttk.Entry(tim, textvariable=self.var_den, width=10)
        o_den.pack(side="left", padx=(6, 8))
        cbo = ttk.Combobox(tim, textvariable=self.var_nhanh, values=KHOANG_NHANH,
                           state="readonly", width=11)
        cbo.pack(side="left", padx=(0, 8))
        cbo.bind("<<ComboboxSelected>>", lambda e: self._ap_dung_nhanh())
        ttk.Button(tim, text="Tìm", command=self._tim, style="Accent.TButton").pack(side="left")
        for o in (o_ma, o_tu, o_den):
            o.bind("<Return>", lambda e: self._tim())

        khung, self.bang = _tao_bang(
            self, ("ma", "gio", "ncc", "nguoi", "so_mat_hang", "tong"),
            {"ma": "Mã phiếu", "gio": "Thời gian", "ncc": "Nhà cung cấp", "nguoi": "Người lập",
             "so_mat_hang": "Số mặt hàng", "tong": "Tổng tiền"},
            {"ma": 150, "gio": 140, "ncc": 190, "nguoi": 140, "so_mat_hang": 100, "tong": 110},
            {"so_mat_hang", "tong"}, chieu_cao=5)
        khung.grid(row=1, column=0, sticky="nsew")
        self.bang.bind("<<TreeviewSelect>>", self._khi_chon)

        trang = ttk.Frame(self)
        trang.grid(row=2, column=0, sticky="ew", pady=(6, 8))
        self.btn_truoc = ttk.Button(trang, text="‹ Trước", command=lambda: self._chuyen_trang(-1))
        self.btn_truoc.pack(side="left")
        self.lbl_trang = ttk.Label(trang, text="")
        self.lbl_trang.pack(side="left", padx=12)
        self.btn_sau = ttk.Button(trang, text="Sau ›", command=lambda: self._chuyen_trang(1))
        self.btn_sau.pack(side="left")
        self.lbl_thong_bao = ttk.Label(trang, text="", foreground=MAU["nguy_hiem"])
        self.lbl_thong_bao.pack(side="right")

        ct = ttk.LabelFrame(self, text="Chi tiết phiếu nhập", padding=10)
        ct.grid(row=3, column=0, sticky="ew")
        ct.grid_columnconfigure(0, weight=1)
        self.lbl_ma = ttk.Label(ct, text="Chọn một phiếu ở bảng trên", style="TieuDe.TLabel")
        self.lbl_ma.grid(row=0, column=0, sticky="w")
        self.lbl_tt = ttk.Label(ct, text="", style="Phu.TLabel")
        self.lbl_tt.grid(row=1, column=0, sticky="w", pady=(0, 6))
        khung_dong, self.bang_dong = _tao_bang(
            ct, ("ma_sp", "ten_sp", "so_luong", "gia_nhap", "thanh_tien"),
            {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "so_luong": "Số lượng",
             "gia_nhap": "Giá nhập (giá lô)", "thanh_tien": "Thành tiền"},
            {"ma_sp": 90, "ten_sp": 300, "so_luong": 90, "gia_nhap": 140, "thanh_tien": 130},
            {"so_luong", "gia_nhap", "thanh_tien"}, chieu_cao=4)
        khung_dong.grid(row=2, column=0, sticky="ew")

    # ---------- dữ liệu ----------
    def lam_moi(self):
        """Mỗi lần tab hiện lên: nạp lại danh sách nhà cung cấp và danh sách phiếu, GIỮ NGUYÊN bộ lọc."""
        ds = goi_controller(self, LichSuPhieuNhapController.danh_sach_nha_cung_cap)
        if ds is not None:
            self.ds_ncc = {TAT_CA_NCC: None}
            self.ds_ncc.update({d["ten_ncc"]: d["id"] for d in ds})
            self.cbo_ncc["values"] = list(self.ds_ncc)
            if self.var_ncc.get() not in self.ds_ncc:
                self.var_ncc.set(TAT_CA_NCC)
        self._tai()

    def _ap_dung_nhanh(self):
        hom_nay, chon = date.today(), self.var_nhanh.get()
        if chon == "Hôm nay":
            tu = den = hom_nay
        elif chon == "7 ngày qua":
            tu, den = hom_nay - timedelta(days=6), hom_nay
        elif chon == "30 ngày qua":
            tu, den = hom_nay - timedelta(days=29), hom_nay
        else:
            tu = den = None
        self.var_tu.set(tu.strftime("%d/%m/%Y") if tu else "")
        self.var_den.set(den.strftime("%d/%m/%Y") if den else "")
        self._tim()

    def _tim(self):
        self.trang = 1
        self._tai()

    def _chuyen_trang(self, huong):
        self.trang += huong
        self._tai()

    def _tai(self):
        kq = goi_controller(self, LichSuPhieuNhapController.tim_kiem, self.var_ma.get(),
                            self.ds_ncc.get(self.var_ncc.get()), self.var_tu.get(),
                            self.var_den.get(), self.trang, SO_DONG)
        if kq is None:
            return
        ok, thong_diep, dl = kq
        if not ok:
            self.lbl_thong_bao.config(text=thong_diep)
            return
        self.lbl_thong_bao.config(text="")
        self.trang, self.so_trang = dl["trang"], dl["so_trang"]

        chon_truoc = self.bang.selection()
        self.bang.delete(*self.bang.get_children())
        for r in dl["dong"]:
            self.bang.insert("", "end", iid=str(r["id"]), values=(
                r["ma_phieu"], dinh_dang_gio(r["ngay_nhap"]), r["ten_ncc"], r["nguoi_lap"],
                r["so_mat_hang"], dinh_dang_so(r["tong_tien"])))
        to_mau_xen_ke(self.bang)
        self.lbl_trang.config(text=f"Trang {self.trang}/{self.so_trang}  —  {dl['tong']} phiếu")
        self.btn_truoc.config(state="normal" if self.trang > 1 else "disabled")
        self.btn_sau.config(state="normal" if self.trang < self.so_trang else "disabled")
        if chon_truoc and self.bang.exists(chon_truoc[0]):
            self.bang.selection_set(chon_truoc[0])
            self._hien_chi_tiet(int(chon_truoc[0]))
        else:
            self._xoa_chi_tiet()

    def _khi_chon(self, event=None):
        chon = self.bang.selection()
        if chon:
            self._hien_chi_tiet(int(chon[0]))

    def _xoa_chi_tiet(self):
        self.lbl_ma.config(text="Chọn một phiếu ở bảng trên")
        self.lbl_tt.config(text="")
        self.bang_dong.delete(*self.bang_dong.get_children())

    def _hien_chi_tiet(self, phieu_id):
        kq = goi_controller(self, LichSuPhieuNhapController.chi_tiet, phieu_id)
        if kq is None:
            return
        ok, thong_diep, dl = kq
        if not ok:
            self.lbl_thong_bao.config(text=thong_diep)
            return
        p = dl["phieu"]
        self.lbl_ma.config(text=f"Phiếu {p['ma_phieu']}")
        thong_tin = (f"{dinh_dang_gio(p['ngay_nhap'])}  ·  {p['ten_ncc']}  ·  Người lập: {p['nguoi_lap']}"
                     f"  ·  Tổng {dinh_dang_tien(p['tong_tien'])}")
        if p["ghi_chu"]:
            thong_tin += f"  ·  Ghi chú: {p['ghi_chu']}"
        self.lbl_tt.config(text=thong_tin)
        self.bang_dong.delete(*self.bang_dong.get_children())
        for r in dl["dong"]:
            self.bang_dong.insert("", "end", values=(
                r["ma_sp"], r["ten_sp"], r["so_luong"], dinh_dang_so(r["gia_nhap"]),
                dinh_dang_so(r["thanh_tien"])))
        to_mau_xen_ke(self.bang_dong)