import tkinter as tk
from tkinter import ttk, messagebox

from controllers.nguoi_dung_controller import NguoiDungController
from views.chung import goi_controller
from views.theme import MAU


class DoiMatKhauForm(tk.Toplevel):
    """
    Đổi mật khẩu của CHÍNH MÌNH (mọi vai trò đều dùng được).
    bat_buoc=True: dùng khi tài khoản vừa được tạo/đặt lại mật khẩu; không có nút Hủy,
    người dùng chỉ có thể đổi mật khẩu xong hoặc đăng xuất.
    """

    def __init__(self, master, bat_buoc=False, on_logout=None):
        super().__init__(master)
        self.bat_buoc = bat_buoc
        self.on_logout = on_logout
        self.title("Đổi mật khẩu")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.var_cu, self.var_moi, self.var_lai = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self._xay_dung()
        self._can_giua(master)
        self.wait_visibility()
        self.grab_set()
        self.entry_cu.focus_set()
        if bat_buoc:
            self.protocol("WM_DELETE_WINDOW", self._dang_xuat)     # đóng cửa sổ = đăng xuất

    def _xay_dung(self):
        khung = ttk.Frame(self, padding=22)
        khung.pack()
        ttk.Label(khung, text="Đổi mật khẩu", style="TieuDe.TLabel").grid(
            row=0, column=0, sticky="w")
        hang = 1
        if self.bat_buoc:
            ttk.Label(khung, wraplength=360, justify="left", foreground=MAU["canh_bao"],
                      text="Tài khoản của bạn vừa được tạo hoặc được đặt lại mật khẩu. "
                           "Hãy tự đặt một mật khẩu mới của riêng bạn trước khi tiếp tục."
                      ).grid(row=1, column=0, sticky="w", pady=(6, 0))
            hang = 2

        def o_nhap(nhan, bien, r):
            ttk.Label(khung, text=nhan).grid(row=r, column=0, sticky="w", pady=(14, 0))
            o = ttk.Entry(khung, textvariable=bien, show="•", width=38)
            o.grid(row=r + 1, column=0, sticky="ew", pady=(4, 0))
            return o

        self.entry_cu = o_nhap("Mật khẩu hiện tại" + (" (mật khẩu tạm được cấp)" if self.bat_buoc else ""),
                               self.var_cu, hang)
        o_nhap("Mật khẩu mới", self.var_moi, hang + 2)
        o_nhap("Nhập lại mật khẩu mới", self.var_lai, hang + 4)
        ttk.Label(khung, text="Ít nhất 8 ký tự, gồm cả chữ và số.", style="Phu.TLabel").grid(
            row=hang + 6, column=0, sticky="w", pady=(8, 0))
        self.lbl_loi = ttk.Label(khung, foreground=MAU["nguy_hiem"], wraplength=360, justify="left")
        self.lbl_loi.grid(row=hang + 7, column=0, sticky="w", pady=(6, 0))

        nut = ttk.Frame(khung)
        nut.grid(row=hang + 8, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(nut, text="Đổi mật khẩu", command=self._luu, style="Accent.TButton").pack(side="right")
        if self.bat_buoc:
            ttk.Button(nut, text="Đăng xuất", command=self._dang_xuat).pack(side="right", padx=8)
        else:
            ttk.Button(nut, text="Hủy", command=self.destroy).pack(side="right", padx=8)
            self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._luu())

    def _can_giua(self, master):
        self.update_idletasks()
        goc = master.winfo_toplevel()
        x = goc.winfo_rootx() + (goc.winfo_width() - self.winfo_width()) // 2
        y = goc.winfo_rooty() + (goc.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _dang_xuat(self):
        self.destroy()
        if self.on_logout:
            self.on_logout()

    def _luu(self):
        kq = goi_controller(self, NguoiDungController.doi_mat_khau_cua_toi,
                            self.var_cu.get(), self.var_moi.get(), self.var_lai.get())
        if kq is None:
            return
        ok, thong_diep, _ = kq
        if ok:
            messagebox.showinfo("Đổi mật khẩu", "Đã đổi mật khẩu thành công.", parent=self)
            self.destroy()
        else:
            self.lbl_loi.config(text=thong_diep)
            if "hiện tại" in thong_diep:
                self.var_cu.set("")                 # sai mật khẩu hiện tại: xóa ô để gõ lại