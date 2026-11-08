import tkinter as tk
from tkinter import ttk, messagebox

from controllers.nguoi_dung_controller import NguoiDungController
from utils.formatters import dinh_dang_gio
from views.chung import goi_controller
from views.nguoi_dung_form import DoiVaiTroForm, MatKhauTamForm, NguoiDungForm
from views.theme import MAU, to_mau_xen_ke

THOI_GIAN_THONG_BAO_MS = 6000
COT = ("ten_dang_nhap", "ho_ten", "vai_tro", "trang_thai", "ngay_tao")
TIEU_DE = {"ten_dang_nhap": "Tên đăng nhập", "ho_ten": "Họ tên", "vai_tro": "Vai trò",
           "trang_thai": "Trạng thái", "ngay_tao": "Ngày tạo"}
DO_RONG = {"ten_dang_nhap": 150, "ho_ten": 210, "vai_tro": 160, "trang_thai": 190, "ngay_tao": 130}


class NguoiDungView(ttk.Frame):
    """Quản lý người dùng. Chỉ Admin vào được (menu ẩn với vai trò khác; Controller cũng chặn)."""

    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_tim = tk.StringVar()
        self._ds = {}                       # iid -> dòng dữ liệu của người dùng đó
        self._job_thong_bao = None
        self._xay_dung()
        self.bind("<Destroy>", self._huy_cong_viec)

    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tim = ttk.Frame(self)
        tim.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(tim, text="Tìm").pack(side="left")
        o = ttk.Entry(tim, textvariable=self.var_tim, width=32)
        o.pack(side="left", padx=8)
        o.bind("<Return>", lambda e: self._tai())
        ttk.Button(tim, text="Tìm", command=self._tai).pack(side="left")

        self.tree = ttk.Treeview(self, columns=COT, show="headings", height=10, selectmode="browse")
        for c in COT:
            self.tree.heading(c, text=TIEU_DE[c], anchor="w")
            self.tree.column(c, width=DO_RONG[c], anchor="w")
        self.tree.tag_configure("khoa", foreground="#9CA3AF")
        self.tree.tag_configure("cho_doi", foreground=MAU["canh_bao"])
        self.tree.grid(row=1, column=0, sticky="nsew")
        cuon = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        cuon.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=cuon.set)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._cap_nhat_nut())

        duoi = ttk.Frame(self)
        duoi.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(duoi, text="Thêm người dùng", command=self._them, style="Accent.TButton").pack(side="left")
        self.btn_vai_tro = ttk.Button(duoi, text="Đổi vai trò...", command=self._doi_vai_tro, state="disabled")
        self.btn_vai_tro.pack(side="left", padx=(8, 0))
        self.btn_mat_khau = ttk.Button(duoi, text="Đặt lại mật khẩu...", command=self._dat_lai_mat_khau, state="disabled")
        self.btn_mat_khau.pack(side="left", padx=(8, 0))
        self.btn_khoa = ttk.Button(duoi, text="Khóa tài khoản", command=self._khoa_hoac_mo, state="disabled")
        self.btn_khoa.pack(side="left", padx=(8, 0))

        self.lbl_thong_bao = ttk.Label(self, text="")
        self.lbl_thong_bao.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _goi(self, ham, *args, **kwargs):
        return goi_controller(self, ham, *args, **kwargs)

    def _bao(self, thong_diep, loi=False):
        self.lbl_thong_bao.config(text=thong_diep,
                                  foreground=MAU["nguy_hiem"] if loi else MAU["thanh_cong"])
        if self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
        self._job_thong_bao = self.after(
            THOI_GIAN_THONG_BAO_MS, lambda: self.lbl_thong_bao.config(text=""))

    # ---------- dữ liệu ----------
    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: nạp lại danh sách, GIỮ NGUYÊN ô tìm kiếm và dòng đang chọn."""
        self._tai()

    def _tai(self):
        kq = self._goi(NguoiDungController.danh_sach, self.var_tim.get())
        if kq is None:
            return
        ok, thong_diep, dong = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return
        chon_truoc = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        self._ds = {}
        for d in dong:
            iid = str(d["id"])
            self._ds[iid] = d
            trang_thai = "Hoạt động" if d["trang_thai"] == "hoat_dong" else "Đã khóa"
            tag = ()
            if d["trang_thai"] == "khoa":
                tag = ("khoa",)
            elif d["cho_doi_mat_khau"]:
                trang_thai += "  ·  chờ đổi mật khẩu"
                tag = ("cho_doi",)
            ten = d["ten_dang_nhap"] + ("  (bạn)" if d["la_toi"] else "")
            self.tree.insert("", "end", iid=iid, tags=tag, values=(
                ten, d["ho_ten"], d["ten_vai_tro"], trang_thai, dinh_dang_gio(d["ngay_tao"])))
        to_mau_xen_ke(self.tree)
        if chon_truoc and self.tree.exists(chon_truoc[0]):
            self.tree.selection_set(chon_truoc[0])
        self._cap_nhat_nut()

    def _dong_chon(self):
        chon = self.tree.selection()
        return self._ds.get(chon[0]) if chon else None

    def _cap_nhat_nut(self):
        d = self._dong_chon()
        co_the = d is not None and not d["la_toi"]        # không thao tác lên chính mình
        trang_thai = "normal" if co_the else "disabled"
        for nut in (self.btn_vai_tro, self.btn_mat_khau, self.btn_khoa):
            nut.config(state=trang_thai)
        self.btn_khoa.config(text="Mở khóa" if d and d["trang_thai"] == "khoa" else "Khóa tài khoản")

    # ---------- hành động ----------
    def _sau_khi_luu(self, thong_diep):
        self._tai()
        self._bao(thong_diep)

    def _them(self):
        ds_vt = self._goi(NguoiDungController.danh_sach_vai_tro)
        if ds_vt is not None:
            NguoiDungForm(self, ds_vt, self._sau_khi_luu)

    def _doi_vai_tro(self):
        d = self._dong_chon()
        if d is None:
            return
        ds_vt = self._goi(NguoiDungController.danh_sach_vai_tro)
        if ds_vt is not None:
            DoiVaiTroForm(self, d, ds_vt, self._sau_khi_luu)

    def _khoa_hoac_mo(self):
        d = self._dong_chon()
        if d is None:
            return
        if d["trang_thai"] == "khoa":
            kq = self._goi(NguoiDungController.mo_khoa, d["id"])
        else:
            if not messagebox.askyesno(
                    "Khóa tài khoản",
                    f"Khóa tài khoản {d['ten_dang_nhap']} ({d['ho_ten']})?\n\n"
                    f"Người này sẽ không đăng nhập được nữa, và nếu đang dùng app thì sẽ bị "
                    f"đưa ra ở thao tác tiếp theo.", parent=self, icon="warning"):
                return
            kq = self._goi(NguoiDungController.khoa_tai_khoan, d["id"])
        if kq is None:
            return
        ok, thong_diep, _ = kq
        self._tai()
        self._bao(thong_diep, loi=not ok)

    def _dat_lai_mat_khau(self):
        d = self._dong_chon()
        if d is None:
            return
        if not messagebox.askyesno(
                "Đặt lại mật khẩu",
                f"Đặt lại mật khẩu của {d['ten_dang_nhap']} ({d['ho_ten']})?\n\n"
                f"Mật khẩu hiện tại của họ sẽ không còn dùng được. Hệ thống sẽ tạo một mật khẩu "
                f"tạm để bạn đưa cho họ.", parent=self, icon="warning"):
            return
        kq = self._goi(NguoiDungController.dat_lai_mat_khau, d["id"])
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return
        self._tai()
        self._bao(thong_diep)
        MatKhauTamForm(self, du_lieu["ten_dang_nhap"], du_lieu["mat_khau_tam"])

    def _huy_cong_viec(self, event):
        if event.widget is self and self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
            self._job_thong_bao = None