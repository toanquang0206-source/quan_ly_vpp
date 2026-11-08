import tkinter as tk
from tkinter import ttk

from controllers.nguoi_dung_controller import NguoiDungController
from views.chung import goi_controller
from views.theme import MAU


class _HopThoai(tk.Toplevel):
    """Khung chung cho các hộp thoại nhỏ: modal, căn giữa, Esc để đóng."""

    def __init__(self, master, tieu_de):
        super().__init__(master)
        self.title(tieu_de)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.master_goc = master

    def _hien(self, o_dau=None):
        self.update_idletasks()
        goc = self.master_goc.winfo_toplevel()
        x = goc.winfo_rootx() + (goc.winfo_width() - self.winfo_width()) // 2
        y = goc.winfo_rooty() + (goc.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()
        if o_dau is not None:
            o_dau.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())


class NguoiDungForm(_HopThoai):
    """Thêm người dùng mới."""

    def __init__(self, master, ds_vai_tro, on_saved):
        super().__init__(master, "Thêm người dùng")
        self.ds_vai_tro = {v["ten_vai_tro"]: v["id"] for v in ds_vai_tro}
        self.on_saved = on_saved
        self.var = {k: tk.StringVar() for k in ("ten", "ho_ten", "vai_tro", "mk", "lai")}
        khung = ttk.Frame(self, padding=22)
        khung.pack()
        ttk.Label(khung, text="Thêm người dùng", style="TieuDe.TLabel").grid(row=0, column=0, sticky="w")

        def o(nhan, khoa, r, an=False):
            ttk.Label(khung, text=nhan).grid(row=r, column=0, sticky="w", pady=(12, 0))
            e = ttk.Entry(khung, textvariable=self.var[khoa], width=38, show="•" if an else "")
            e.grid(row=r + 1, column=0, sticky="ew", pady=(4, 0))
            return e

        self.entry_ten = o("Tên đăng nhập *", "ten", 1)
        o("Họ tên *", "ho_ten", 3)
        ttk.Label(khung, text="Vai trò *").grid(row=5, column=0, sticky="w", pady=(12, 0))
        self.cbo = ttk.Combobox(khung, textvariable=self.var["vai_tro"], values=list(self.ds_vai_tro),
                                state="readonly", width=36)
        self.cbo.grid(row=6, column=0, sticky="ew", pady=(4, 0))
        o("Mật khẩu ban đầu *", "mk", 7, an=True)
        o("Nhập lại mật khẩu *", "lai", 9, an=True)
        ttk.Label(khung, wraplength=360, justify="left", style="Phu.TLabel",
                  text="Tên đăng nhập: chữ thường không dấu, số, dấu chấm, gạch dưới. "
                       "Mật khẩu: ít nhất 8 ký tự, có chữ và số. Người dùng sẽ phải đổi mật khẩu "
                       "ở lần đăng nhập đầu tiên.").grid(row=11, column=0, sticky="w", pady=(10, 0))
        self.lbl_loi = ttk.Label(khung, foreground=MAU["nguy_hiem"], wraplength=360, justify="left")
        self.lbl_loi.grid(row=12, column=0, sticky="w", pady=(6, 0))
        nut = ttk.Frame(khung)
        nut.grid(row=13, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(nut, text="Tạo tài khoản", command=self._luu, style="Accent.TButton").pack(side="right")
        ttk.Button(nut, text="Hủy", command=self.destroy).pack(side="right", padx=8)
        self.bind("<Return>", lambda e: self._luu())
        self._hien(self.entry_ten)

    def _luu(self):
        kq = goi_controller(
            self, NguoiDungController.them, self.var["ten"].get(), self.var["ho_ten"].get(),
            self.ds_vai_tro.get(self.var["vai_tro"].get()), self.var["mk"].get(), self.var["lai"].get())
        if kq is None:
            return
        ok, thong_diep, _ = kq
        if ok:
            self.on_saved(thong_diep)
            self.destroy()
        else:
            self.lbl_loi.config(text=thong_diep)


class DoiVaiTroForm(_HopThoai):
    """Đổi vai trò của một người dùng."""

    def __init__(self, master, nguoi_dung, ds_vai_tro, on_saved):
        super().__init__(master, "Đổi vai trò")
        self.nguoi_dung = nguoi_dung
        self.ds_vai_tro = {v["ten_vai_tro"]: v["id"] for v in ds_vai_tro}
        self.on_saved = on_saved
        self.var_vt = tk.StringVar(value=nguoi_dung["ten_vai_tro"])
        khung = ttk.Frame(self, padding=22)
        khung.pack()
        ttk.Label(khung, text="Đổi vai trò", style="TieuDe.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(khung, text=f"{nguoi_dung['ho_ten']} ({nguoi_dung['ten_dang_nhap']})",
                  style="Phu.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 12))
        ttk.Label(khung, text="Vai trò mới").grid(row=2, column=0, sticky="w")
        self.cbo = ttk.Combobox(khung, textvariable=self.var_vt, values=list(self.ds_vai_tro),
                                state="readonly", width=30)
        self.cbo.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        ttk.Label(khung, wraplength=300, justify="left", style="Phu.TLabel",
                  text="Quyền mới có hiệu lực ngay ở thao tác tiếp theo của người đó; "
                       "menu sẽ cập nhật ở lần đăng nhập sau.").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.lbl_loi = ttk.Label(khung, foreground=MAU["nguy_hiem"], wraplength=300, justify="left")
        self.lbl_loi.grid(row=5, column=0, sticky="w", pady=(6, 0))
        nut = ttk.Frame(khung)
        nut.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(nut, text="Lưu", command=self._luu, style="Accent.TButton").pack(side="right")
        ttk.Button(nut, text="Hủy", command=self.destroy).pack(side="right", padx=8)
        self.bind("<Return>", lambda e: self._luu())
        self._hien(self.cbo)

    def _luu(self):
        kq = goi_controller(self, NguoiDungController.doi_vai_tro, self.nguoi_dung["id"],
                            self.ds_vai_tro.get(self.var_vt.get()))
        if kq is None:
            return
        ok, thong_diep, _ = kq
        if ok:
            self.on_saved(thong_diep)
            self.destroy()
        else:
            self.lbl_loi.config(text=thong_diep)


class MatKhauTamForm(_HopThoai):
    """Hiển thị mật khẩu tạm đúng MỘT lần sau khi đặt lại."""

    def __init__(self, master, ten_dang_nhap, mat_khau_tam):
        super().__init__(master, "Mật khẩu tạm")
        self.mat_khau_tam = mat_khau_tam
        khung = ttk.Frame(self, padding=22)
        khung.pack()
        ttk.Label(khung, text="Đã đặt lại mật khẩu", style="TieuDe.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(khung, text=f"Mật khẩu tạm của {ten_dang_nhap}:", style="Phu.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 4))
        self.var = tk.StringVar(value=mat_khau_tam)
        o = ttk.Entry(khung, textvariable=self.var, state="readonly", width=22, justify="center",
                      font=("Consolas", 16, "bold"))
        o.grid(row=2, column=0, sticky="ew")
        self.btn_chep = ttk.Button(khung, text="Sao chép", command=self._sao_chep)
        self.btn_chep.grid(row=2, column=1, padx=(8, 0))
        ttk.Label(khung, wraplength=380, justify="left", foreground=MAU["canh_bao"],
                  text="Mật khẩu này chỉ hiện MỘT lần duy nhất và không được lưu ở đâu cả. "
                       "Hãy đưa cho người dùng; họ sẽ phải tự đặt mật khẩu mới khi đăng nhập."
                  ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))
        ttk.Button(khung, text="Đã ghi lại, đóng", command=self.destroy,
                   style="Accent.TButton").grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        self._hien()

    def _sao_chep(self):
        self.clipboard_clear()
        self.clipboard_append(self.mat_khau_tam)
        self.btn_chep.config(text="Đã sao chép")