import tkinter as tk

from controllers.auth_controller import AuthController
from views.dang_nhap_view import DangNhapView
from views.main_window import MainWindow
from views.theme import ap_dung_theme


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý kho văn phòng phẩm")
        ap_dung_theme(self)                       # màu sắc + kiểu chữ cho toàn ứng dụng
        self.bind("<<PhienHetHan>>", lambda e: self.dang_xuat())
        self.hien_dang_nhap()

    def _xoa_man_hinh(self):
        for widget in self.winfo_children():
            widget.destroy()

    def hien_dang_nhap(self):
        self._xoa_man_hinh()
        self.geometry("")                 # để cửa sổ tự co lại vừa form đăng nhập
        self.resizable(False, False)
        DangNhapView(self, on_success=self.hien_man_hinh_chinh).pack()

    def hien_man_hinh_chinh(self):
        self._xoa_man_hinh()
        self.resizable(True, True)
        self.geometry("1180x680")
        self.minsize(980, 560)
        MainWindow(self, on_logout=self.dang_xuat).pack(fill="both", expand=True)

    def dang_xuat(self):
        AuthController.dang_xuat()
        self.hien_dang_nhap()


if __name__ == "__main__":
    App().mainloop()