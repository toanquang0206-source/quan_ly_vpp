import tkinter as tk
from tkinter import ttk

from controllers.kho_controller import TheKhoController
from utils.formatters import dinh_dang_gio, dinh_dang_so, dinh_dang_tien
from views.bao_cao_view import _tao_bang
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke

DO_TRE_GOI_Y_MS = 300
SO_DONG = 10
NHAN_LOAI = {"nhap_kho": "Nhập kho", "ban_hang": "Bán hàng", "tra_hang": "Khách trả hàng",
             "xuat_kho": "Xuất kho", "kiem_ke": "Kiểm kê / cân bằng", "huy_hoa_don": "Hủy hóa đơn"}
TAT_CA_LOAI = "Tất cả loại"
BO_QUA_PHIM = {"Return", "Up", "Down", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L",
               "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Home", "End"}


class TheKhoView(ttk.Frame):
    """Lịch sử xuất nhập của MỘT sản phẩm, kèm đối chiếu sổ (tồn kho = tổng thẻ kho)."""

    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_sp = tk.StringVar()
        self.var_loai = tk.StringVar(value=TAT_CA_LOAI)
        self.var_tu, self.var_den = tk.StringVar(), tk.StringVar()
        self.sp_id = None
        self.trang, self.so_trang = 1, 1
        self._ds_goi_y = []
        self._job_goi_y = None
        self._xay_dung()
        self.bind("<Destroy>", self._huy_cong_viec)

    # ---------- dựng giao diện ----------
    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        loc = ttk.Frame(self)
        loc.grid(row=0, column=0, sticky="ew")
        ttk.Label(loc, text="Sản phẩm").pack(side="left")
        self.entry_sp = ttk.Entry(loc, textvariable=self.var_sp, width=34)
        self.entry_sp.pack(side="left", padx=(6, 12))
        ttk.Label(loc, text="Loại").pack(side="left")
        self.cbo_loai = ttk.Combobox(loc, textvariable=self.var_loai, state="readonly", width=17,
                                     values=[TAT_CA_LOAI] + list(NHAN_LOAI.values()))
        self.cbo_loai.pack(side="left", padx=(6, 12))
        self.cbo_loai.bind("<<ComboboxSelected>>", lambda e: self._xem())
        ttk.Label(loc, text="Từ").pack(side="left")
        o_tu = ttk.Entry(loc, textvariable=self.var_tu, width=10)
        o_tu.pack(side="left", padx=(6, 8))
        ttk.Label(loc, text="Đến").pack(side="left")
        o_den = ttk.Entry(loc, textvariable=self.var_den, width=10)
        o_den.pack(side="left", padx=(6, 10))
        for o in (o_tu, o_den):
            o.bind("<Return>", lambda e: self._xem())
        ttk.Button(loc, text="Xem", command=self._xem, style="Accent.TButton").pack(side="left")

        # Ba thẻ thông tin của sản phẩm đang xem
        self.khung_the = ttk.Frame(self)
        self.khung_the.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        self.khung_the.grid_columnconfigure((0, 1, 2), weight=1, uniform="the")
        self.the = {}
        for i, (khoa, tieu_de) in enumerate([("ton", "Tồn kho hiện tại"), ("von", "Giá vốn bình quân"),
                                              ("so", "Đối chiếu sổ")]):
            khung = ttk.Frame(self.khung_the, style="The.TFrame", padding=(14, 10))
            khung.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            ttk.Label(khung, text=tieu_de, style="The.TLabel").pack(anchor="w")
            nhan = ttk.Label(khung, text="—", style="TheSo.TLabel")
            nhan.pack(anchor="w")
            self.the[khoa] = nhan
        self.lbl_so_phu = ttk.Label(self.khung_the, text="", style="Phu.TLabel")

        khung, self.bang = _tao_bang(
            self, ("gio", "loai", "thay_doi", "ton_sau", "chung_tu", "nguoi"),
            {"gio": "Thời gian", "loai": "Loại giao dịch", "thay_doi": "Thay đổi", "ton_sau": "Tồn sau",
             "chung_tu": "Chứng từ", "nguoi": "Người thực hiện"},
            {"gio": 140, "loai": 150, "thay_doi": 90, "ton_sau": 90, "chung_tu": 170, "nguoi": 150},
            {"thay_doi", "ton_sau"}, chieu_cao=10)
        khung.grid(row=2, column=0, sticky="nsew")
        self.bang.tag_configure("tang", foreground=MAU["thanh_cong"])
        self.bang.tag_configure("giam", foreground=MAU["nguy_hiem"])

        duoi = ttk.Frame(self)
        duoi.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.btn_truoc = ttk.Button(duoi, text="‹ Trước", command=lambda: self._chuyen_trang(-1))
        self.btn_truoc.pack(side="left")
        self.lbl_trang = ttk.Label(duoi, text="Hãy chọn một sản phẩm để xem thẻ kho.")
        self.lbl_trang.pack(side="left", padx=12)
        self.btn_sau = ttk.Button(duoi, text="Sau ›", command=lambda: self._chuyen_trang(1))
        self.btn_sau.pack(side="left")
        self.lbl_thong_bao = ttk.Label(duoi, text="", foreground=MAU["nguy_hiem"])
        self.lbl_thong_bao.pack(side="right")

        self.lb_goi_y = tk.Listbox(self, height=6, activestyle="dotbox")
        self.lb_goi_y.bind("<ButtonRelease-1>", self._chon_goi_y)
        self.lb_goi_y.bind("<Return>", self._chon_goi_y)
        self.lb_goi_y.bind("<Escape>", lambda e: self._an_goi_y())
        self.entry_sp.bind("<KeyRelease>", self._khi_go_phim)
        self.entry_sp.bind("<Return>", self._enter_o_tim)
        self.entry_sp.bind("<Down>", self._xuong_goi_y)
        self.entry_sp.bind("<Escape>", lambda e: self._an_goi_y())
        self.bang.bind("<Button-1>", lambda e: self._an_goi_y(), add="+")

    # ---------- dữ liệu ----------
    def lam_moi(self):
        """Mỗi lần tab hiện lên: nạp lại thẻ kho của sản phẩm đang xem (nếu có), GIỮ NGUYÊN bộ lọc."""
        if self.sp_id is not None:
            self._tai()

    def _loai_dang_chon(self):
        nhan = self.var_loai.get()
        return next((ma for ma, ten in NHAN_LOAI.items() if ten == nhan), "")

    def _xem(self):
        self.trang = 1
        self._tai()

    def _chuyen_trang(self, huong):
        self.trang += huong
        self._tai()

    def _tai(self):
        if self.sp_id is None:
            self.lbl_thong_bao.config(text="Hãy chọn sản phẩm từ danh sách gợi ý.")
            return
        kq = goi_controller(self, TheKhoController.thong_tin, self.sp_id)
        if kq is None:
            return
        ok, thong_diep, tt = kq
        if not ok:
            self.lbl_thong_bao.config(text=thong_diep)
            return
        kq = goi_controller(self, TheKhoController.lich_su, self.sp_id, self._loai_dang_chon(),
                            self.var_tu.get(), self.var_den.get(), self.trang, SO_DONG)
        if kq is None:
            return
        ok, thong_diep, ls = kq
        if not ok:
            self.lbl_thong_bao.config(text=thong_diep)
            return
        self.lbl_thong_bao.config(text="")
        self.trang, self.so_trang = ls["trang"], ls["so_trang"]
        self._ve_the(tt)

        self.bang.delete(*self.bang.get_children())
        for r in ls["dong"]:
            self.bang.insert("", "end", tags=("tang",) if r["thay_doi"] > 0 else ("giam",), values=(
                dinh_dang_gio(r["thoi_gian"]), NHAN_LOAI.get(r["loai"], r["loai"]),
                f"{r['thay_doi']:+d}", r["ton_sau"], r["chung_tu"], r["nguoi"]))
        to_mau_xen_ke(self.bang)
        self.lbl_trang.config(text=f"Trang {self.trang}/{self.so_trang}  —  {ls['tong']} dòng")
        self.btn_truoc.config(state="normal" if self.trang > 1 else "disabled")
        self.btn_sau.config(state="normal" if self.trang < self.so_trang else "disabled")

    def _ve_the(self, tt):
        self.the["ton"].config(text=str(tt["ton_kho"]) + (" (ngừng KD)" if tt["ngung"] else ""))
        self.the["von"].config(text=dinh_dang_tien(tt["gia_von"]))
        if tt["khop"]:
            self.the["so"].config(text="Khớp sổ", foreground=MAU["thanh_cong"])
        else:
            self.the["so"].config(text=f"Lệch {tt['chenh_lech']:+d}", foreground=MAU["nguy_hiem"])

    # ---------- chọn sản phẩm (gợi ý khi gõ) ----------
    def _khi_go_phim(self, event):
        if event.keysym in BO_QUA_PHIM:
            return
        self.sp_id = None
        if self._job_goi_y is not None:
            self.after_cancel(self._job_goi_y)
        self._job_goi_y = self.after(DO_TRE_GOI_Y_MS, self._cap_nhat_goi_y)

    def _cap_nhat_goi_y(self):
        self._job_goi_y = None
        ds = goi_controller(self, TheKhoController.goi_y_san_pham, self.var_sp.get()) or []
        if not ds:
            self._an_goi_y()
            return
        self._ds_goi_y = ds
        self.lb_goi_y.delete(0, "end")
        for sp in ds:
            self.lb_goi_y.insert("end", f"{sp['ma_sp']}  —  {sp['ten_sp']}   (tồn {sp['ton_kho']})"
                                        + ("  [ngừng KD]" if sp["ngung"] else ""))
        self.lb_goi_y.place(in_=self.entry_sp, relx=0, rely=1.0, relwidth=1.0)
        self.lb_goi_y.lift()

    def _an_goi_y(self):
        self.lb_goi_y.place_forget()

    def _xuong_goi_y(self, event):
        if self.lb_goi_y.winfo_ismapped():
            self.lb_goi_y.focus_set()
            self.lb_goi_y.selection_clear(0, "end")
            self.lb_goi_y.selection_set(0)
            self.lb_goi_y.activate(0)
        return "break"

    def _enter_o_tim(self, event):
        if self.lb_goi_y.winfo_ismapped() and self._ds_goi_y:
            self._chon_theo_vi_tri(0)
        else:
            self._xem()

    def _chon_goi_y(self, event=None):
        chon = self.lb_goi_y.curselection()
        if chon:
            self._chon_theo_vi_tri(chon[0])

    def _chon_theo_vi_tri(self, i):
        sp = self._ds_goi_y[i]
        self.sp_id = sp["id"]
        self.var_sp.set(f"{sp['ma_sp']} - {sp['ten_sp']}")
        self._an_goi_y()
        self._xem()

    def _huy_cong_viec(self, event):
        if event.widget is self and self._job_goi_y is not None:
            self.after_cancel(self._job_goi_y)
            self._job_goi_y = None