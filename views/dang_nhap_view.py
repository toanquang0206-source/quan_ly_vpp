import tkinter as tk
from tkinter import ttk, messagebox

from controllers.auth_controller import AuthController


class DangNhapView(ttk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master, padding=(44, 34))
        self.on_success = on_success   # hàm sẽ chạy khi đăng nhập thành công
        self.var_ten = tk.StringVar()
        self.var_mk = tk.StringVar()
        self._xay_dung_giao_dien()

    def _xay_dung_giao_dien(self):
        self.grid_columnconfigure(0, weight=1)
        ttk.Label(self, text="Kho VPP", style="TieuDe.TLabel").grid(row=0, column=0)
        ttk.Label(self, text="Quản lý kho văn phòng phẩm", style="Phu.TLabel").grid(
            row=1, column=0, pady=(0, 24))

        ttk.Label(self, text="Tên đăng nhập").grid(row=2, column=0, sticky="w")
        self.entry_ten = ttk.Entry(self, textvariable=self.var_ten, width=34)
        self.entry_ten.grid(row=3, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(self, text="Mật khẩu").grid(row=4, column=0, sticky="w")
        self.entry_mk = ttk.Entry(self, textvariable=self.var_mk, show="•", width=34)
        self.entry_mk.grid(row=5, column=0, sticky="ew", pady=(4, 22))

        ttk.Button(self, text="Đăng nhập", command=self._xu_ly_dang_nhap,
                   style="Accent.TButton").grid(row=6, column=0, sticky="ew")

        # Nhấn Enter ở ô nào cũng đăng nhập được
        self.entry_ten.bind("<Return>", lambda e: self._xu_ly_dang_nhap())
        self.entry_mk.bind("<Return>", lambda e: self._xu_ly_dang_nhap())
        self.entry_ten.focus()

    def _xu_ly_dang_nhap(self):
        ok, thong_diep = AuthController.dang_nhap(self.var_ten.get(), self.var_mk.get())
        if ok:
            self.on_success()
        else:
            messagebox.showerror("Đăng nhập thất bại", thong_diep)
            self.var_mk.set("")      # xóa mật khẩu đã gõ sai
            self.entry_mk.focus()