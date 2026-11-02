import tkinter as tk
from tkinter import ttk, messagebox

from controllers.ban_hang_controller import BanHangController
from utils.formatters import dinh_dang_tien
from utils.validators import doc_so
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke

DO_TRE_GOI_Y_MS = 300
CHU_KY_CAP_NHAT_GIA_MS = 20000       # giá trong giỏ tự cập nhật theo giá quản lý mỗi 20 giây
THOI_GIAN_THONG_BAO_MS = 6000
BO_QUA_PHIM = {"Return", "Up", "Down", "Escape", "Tab", "Shift_L", "Shift_R",
               "Control_L", "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Home", "End"}
PHUONG_THUC = {"Tiền mặt": "tien_mat", "Chuyển khoản": "chuyen_khoan", "Thẻ": "the"}

COT = ("ma_sp", "ten_sp", "so_luong", "don_gia", "thanh_tien", "ton_kho", "ghi_chu")
TIEU_DE = {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "so_luong": "Số lượng",
           "don_gia": "Đơn giá", "thanh_tien": "Thành tiền", "ton_kho": "Tồn kho",
           "ghi_chu": "Lưu ý"}
DO_RONG = {"ma_sp": 90, "ten_sp": 300, "so_luong": 95, "don_gia": 110, "thanh_tien": 120,
           "ton_kho": 80, "ghi_chu": 160}
CAN_PHAI = {"so_luong", "don_gia", "thanh_tien", "ton_kho"}


class BanHangView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_tim = tk.StringVar()
        self.var_so_luong = tk.StringVar(value="1")
        self.var_pt = tk.StringVar(value="Tiền mặt")
        self.gio_hang = []            # [{"san_pham_id", "so_luong"}] — KHÔNG lưu giá: giá luôn lấy mới từ CSDL
        self.tong_dang_hien = 0       # tổng tiền đang hiện trên màn hình
        self.co_loi_hang = False
        self.sp_dang_chon = None
        self._ds_goi_y = []
        self._job_goi_y = self._job_thong_bao = self._job_cap_nhat = None
        self._xay_dung()
        self.bind("<Destroy>", self._huy_cong_viec)

    # ---------- dựng giao diện ----------
    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        them = ttk.LabelFrame(self, text="Thêm sản phẩm vào giỏ", padding=8)
        them.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(them, text="Sản phẩm (gõ mã hoặc tên)").grid(row=0, column=0, sticky="w")
        self.entry_tim = ttk.Entry(them, textvariable=self.var_tim, width=50)
        self.entry_tim.grid(row=1, column=0, padx=(0, 10))
        ttk.Label(them, text="Số lượng").grid(row=0, column=1, sticky="w")
        self.entry_sl = ttk.Entry(them, textvariable=self.var_so_luong, width=8)
        self.entry_sl.grid(row=1, column=1, padx=(0, 10))
        ttk.Button(them, text="Thêm vào giỏ", command=self._them_vao_gio,
                   style="Accent.TButton").grid(row=1, column=2)
        self.lbl_thong_tin_sp = ttk.Label(them, text="", style="Phu.TLabel")
        self.lbl_thong_tin_sp.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        self.tree = ttk.Treeview(self, columns=COT, show="headings", height=12)
        for cot in COT:
            self.tree.heading(cot, text=TIEU_DE[cot], anchor="e" if cot in CAN_PHAI else "w")
            self.tree.column(cot, width=DO_RONG[cot], anchor="e" if cot in CAN_PHAI else "w")
        self.tree.tag_configure("loi_hang", foreground=MAU["nguy_hiem"])
        self.tree.grid(row=1, column=0, sticky="nsew")
        thanh_cuon = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        thanh_cuon.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=thanh_cuon.set)
        self.tree.bind("<Button-1>", lambda e: self._an_goi_y(), add="+")

        duoi = ttk.Frame(self)
        duoi.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(duoi, text="Xóa dòng đã chọn", command=self._xoa_dong).pack(side="left")
        ttk.Button(duoi, text="Xóa giỏ", command=self._xoa_gio,
                   style="Danger.TButton").pack(side="left", padx=6)
        ttk.Button(duoi, text="Thanh toán", command=self._thanh_toan,
                   style="Accent.TButton").pack(side="right")
        self.lbl_tong = ttk.Label(duoi, text="0 đ", style="TongLon.TLabel")
        self.lbl_tong.pack(side="right", padx=(18, 18))
        ttk.Label(duoi, text="Tổng:").pack(side="right")
        cbo = ttk.Combobox(duoi, textvariable=self.var_pt, values=list(PHUONG_THUC),
                           state="readonly", width=14)
        cbo.pack(side="right", padx=(6, 24))
        ttk.Label(duoi, text="Hình thức:").pack(side="right")

        self.lbl_thong_bao = ttk.Label(self, text="")
        self.lbl_thong_bao.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.lb_goi_y = tk.Listbox(self, height=6, activestyle="dotbox")
        self.lb_goi_y.bind("<ButtonRelease-1>", self._chon_goi_y)
        self.lb_goi_y.bind("<Return>", self._chon_goi_y)
        self.lb_goi_y.bind("<Escape>", lambda e: self._an_goi_y())

        self.entry_tim.bind("<KeyRelease>", self._khi_go_phim)
        self.entry_tim.bind("<Return>", self._enter_o_tim)
        self.entry_tim.bind("<Down>", self._xuong_goi_y)
        self.entry_tim.bind("<Escape>", lambda e: self._an_goi_y())
        self.entry_sl.bind("<Return>", lambda e: self._them_vao_gio())

    def _goi(self, ham, *args, **kwargs):
        return goi_controller(self, ham, *args, **kwargs)

    def _bao(self, thong_diep, loi=False):
        self.lbl_thong_bao.config(text=thong_diep,
                                  foreground=MAU["nguy_hiem"] if loi else MAU["thanh_cong"])
        if self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
        self._job_thong_bao = self.after(
            THOI_GIAN_THONG_BAO_MS, lambda: self.lbl_thong_bao.config(text=""))

    # ---------- cập nhật giá trong giỏ ----------
    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: lấy lại giá/tồn mới nhất. Giỏ đang soạn được GIỮ NGUYÊN."""
        self._hen_cap_nhat()
        if self.gio_hang:
            self._tinh_lai()

    def _hen_cap_nhat(self):
        if self._job_cap_nhat is not None:
            self.after_cancel(self._job_cap_nhat)
        self._job_cap_nhat = self.after(CHU_KY_CAP_NHAT_GIA_MS, self._tu_cap_nhat)

    def _tu_cap_nhat(self):
        self._job_cap_nhat = None
        if self.gio_hang:
            self._tinh_lai(im_lang=True)         # cập nhật lặng lẽ, không hiện thông báo
        self._hen_cap_nhat()

    def _tinh_lai(self, im_lang=False):
        kq = self._goi(BanHangController.xem_truoc, self._gio_gui())
        if kq is None:
            return False
        ok, thong_diep, du_lieu = kq
        if not ok:
            if not im_lang:
                self._bao(thong_diep, loi=True)
            return False
        self._ve_lai_bang(du_lieu)
        return True

    def _gio_gui(self):
        return [dict(d) for d in self.gio_hang]

    def _ve_lai_bang(self, du_lieu):
        theo_id = {r["san_pham_id"]: r for r in du_lieu["dong"]}
        chon_truoc = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for d in self.gio_hang:
            r = theo_id.get(d["san_pham_id"])
            if r is None:
                continue
            tag = ("loi_hang",) if r["khong_ban_duoc"] else ()
            self.tree.insert("", "end", iid=str(r["san_pham_id"]), tags=tag, values=(
                r["ma_sp"], r["ten_sp"], r["so_luong"], dinh_dang_tien(r["don_gia"]),
                dinh_dang_tien(r["thanh_tien"]), r["ton_kho"], r["khong_ban_duoc"] or ""))
        if chon_truoc and self.tree.exists(chon_truoc[0]):
            self.tree.selection_set(chon_truoc[0])
        to_mau_xen_ke(self.tree)
        self.tong_dang_hien = du_lieu["tong_tien"]
        self.co_loi_hang = du_lieu["co_loi_hang"]
        self.lbl_tong.config(text=dinh_dang_tien(self.tong_dang_hien))

    # ---------- giỏ hàng ----------
    def _them_vao_gio(self):
        sp = self.sp_dang_chon
        if sp is None:
            self._bao("Hãy chọn sản phẩm từ danh sách gợi ý.", loi=True)
            return
        so_luong, loi = doc_so(self.var_so_luong.get(), "số lượng")
        if loi:
            self._bao(loi, loi=True)
            return
        gio_moi = [dict(d) for d in self.gio_hang]
        dong = next((d for d in gio_moi if d["san_pham_id"] == sp["id"]), None)
        if dong:
            dong["so_luong"] += so_luong         # thêm lại cùng sản phẩm thì cộng dồn số lượng
        else:
            gio_moi.append({"san_pham_id": sp["id"], "so_luong": so_luong})

        kq = self._goi(BanHangController.xem_truoc, gio_moi)
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)      # giữ nguyên các ô đang gõ
            return
        dong_kq = next(r for r in du_lieu["dong"] if r["san_pham_id"] == sp["id"])
        if dong_kq["khong_ban_duoc"]:
            self._bao(f"{sp['ten_sp']}: {dong_kq['khong_ban_duoc'][0].lower()}"
                      f"{dong_kq['khong_ban_duoc'][1:]}", loi=True)
            return
        self.gio_hang = gio_moi
        self._ve_lai_bang(du_lieu)
        self.sp_dang_chon = None                 # chuẩn bị món kế tiếp
        self.var_tim.set("")
        self.var_so_luong.set("1")
        self.lbl_thong_tin_sp.config(text="")
        self.entry_tim.focus_set()

    def _xoa_dong(self):
        chon = self.tree.selection()
        if not chon:
            return
        self.gio_hang = [d for d in self.gio_hang if d["san_pham_id"] != int(chon[0])]
        self._lam_trong_hoac_tinh_lai()

    def _xoa_gio(self):
        if self.gio_hang and not messagebox.askyesno(
                "Xóa giỏ", "Xóa toàn bộ giỏ hàng?", parent=self):
            return
        self.gio_hang = []
        self._lam_trong_hoac_tinh_lai()

    def _lam_trong_hoac_tinh_lai(self):
        if self.gio_hang:
            self._tinh_lai()
        else:
            self._ve_lai_bang({"dong": [], "tong_tien": 0, "co_loi_hang": False})

    # ---------- thanh toán ----------
    def _thanh_toan(self):
        if not self.gio_hang:
            self._bao("Giỏ hàng đang trống.", loi=True)
            return
        if not self._tinh_lai():                 # lấy giá mới nhất ngay trước khi thanh toán
            return
        if self.co_loi_hang:
            self._bao("Có sản phẩm không đủ hàng, xem các dòng màu đỏ.", loi=True)
            return
        hinh_thuc = self.var_pt.get()
        if not messagebox.askyesno(
                "Thanh toán", f"Thanh toán {dinh_dang_tien(self.tong_dang_hien)} "
                              f"bằng {hinh_thuc.lower()}?", parent=self):
            return
        kq = self._goi(BanHangController.lap_hoa_don, self._gio_gui(),
                       PHUONG_THUC[hinh_thuc], self.tong_dang_hien)
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if ok:
            self.gio_hang = []
            self._ve_lai_bang({"dong": [], "tong_tien": 0, "co_loi_hang": False})
            self._bao(f"{thong_diep} Thu {dinh_dang_tien(du_lieu['tong_thanh_toan'])}.")
        else:
            if du_lieu and du_lieu.get("ma_loi") == "TONG_THAY_DOI":
                self._tinh_lai()                 # giá vừa đổi đúng lúc lưu: làm mới giỏ
            self._bao(thong_diep, loi=True)

    # ---------- gợi ý sản phẩm (debounce) ----------
    def _khi_go_phim(self, event):
        if event.keysym in BO_QUA_PHIM:
            return
        self.sp_dang_chon = None
        self.lbl_thong_tin_sp.config(text="")
        if self._job_goi_y is not None:
            self.after_cancel(self._job_goi_y)
        self._job_goi_y = self.after(DO_TRE_GOI_Y_MS, self._cap_nhat_goi_y)

    def _cap_nhat_goi_y(self):
        self._job_goi_y = None
        ds = self._goi(BanHangController.goi_y_san_pham, self.var_tim.get()) or []
        if not ds:
            self._an_goi_y()
            return
        self._ds_goi_y = ds
        self.lb_goi_y.delete(0, "end")
        for sp in ds:
            self.lb_goi_y.insert(
                "end", f"{sp['ma_sp']}  —  {sp['ten_sp']}   {dinh_dang_tien(sp['gia_ban'])}"
                       f"   (tồn {sp['ton_kho']})")
        self.lb_goi_y.place(in_=self.entry_tim, relx=0, rely=1.0, relwidth=1.0)
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
            self._chon_theo_vi_tri(0)            # Enter = chọn gợi ý đầu tiên (gõ mã + Enter như quét mã)
        elif self.sp_dang_chon is not None:
            self.entry_sl.focus_set()

    def _chon_goi_y(self, event=None):
        chon = self.lb_goi_y.curselection()
        if chon:
            self._chon_theo_vi_tri(chon[0])

    def _chon_theo_vi_tri(self, i):
        sp = self._ds_goi_y[i]
        self.sp_dang_chon = sp
        self.var_tim.set(f"{sp['ma_sp']} - {sp['ten_sp']}")
        self._an_goi_y()
        self.lbl_thong_tin_sp.config(
            text=f"Giá bán: {dinh_dang_tien(sp['gia_ban'])}   |   Tồn kho: {sp['ton_kho']}")
        self.entry_sl.focus_set()
        self.entry_sl.selection_range(0, "end")

    def _huy_cong_viec(self, event):
        if event.widget is not self:
            return
        for ten in ("_job_goi_y", "_job_thong_bao", "_job_cap_nhat"):
            job = getattr(self, ten)
            if job is not None:
                self.after_cancel(job)
                setattr(self, ten, None)