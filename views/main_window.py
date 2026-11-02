import tkinter as tk
from tkinter import ttk, messagebox

from utils.permissions import PermissionDenied
from utils.session import ROLE_ADMIN, ROLE_THU_KHO, ROLE_NHAN_VIEN, Session
from views.nhap_kho_view import NhapKhoView
from views.placeholder_view import PlaceholderView
from views.san_pham_view import SanPhamView
from views.ban_hang_view import BanHangView
from views.hoa_don_view import HoaDonView

TAT_CA = (ROLE_ADMIN, ROLE_THU_KHO, ROLE_NHAN_VIEN)

# (khóa, nhãn hiển thị, các vai trò được THẤY mục này)
MENU = [
    ("tong_quan",  "Tổng quan",  TAT_CA),
    ("san_pham",   "Sản phẩm",   TAT_CA),
    ("ban_hang",   "Bán hàng",   (ROLE_ADMIN, ROLE_NHAN_VIEN)),
    ("kho",        "Kho",        (ROLE_ADMIN, ROLE_THU_KHO)),
    ("bao_cao",    "Báo cáo",    (ROLE_ADMIN,)),
    ("nguoi_dung", "Người dùng", (ROLE_ADMIN,)),
    ("hoa_don",    "Hóa đơn",    (ROLE_ADMIN, ROLE_NHAN_VIEN)),
]

# Màn hình thật làm xong đến đâu thì đăng ký vào đây.
# Mục nào chưa đăng ký sẽ dùng PlaceholderView.
MAN_HINH_THAT = {"san_pham": SanPhamView, "ban_hang": BanHangView,
                 "kho": NhapKhoView, "hoa_don": HoaDonView}


class MainWindow(ttk.Frame):
    def __init__(self, master, on_logout):
        super().__init__(master)
        self.on_logout = on_logout
        self.man_hinh = {}          # các "tờ giấy" đã tạo: khóa -> Frame
        self.nut_menu = {}          # khóa -> nút trên cột menu
        self._xay_dung_giao_dien()
        self.hien(self._menu_cho_phep()[0][0])   # mở mục đầu tiên được phép

    def _menu_cho_phep(self):
        return [m for m in MENU if Session.has_role(*m[2])]

    def _xay_dung_giao_dien(self):
        user = Session.get_user()

        # Cột menu bên trái (nền tối)
        menu = ttk.Frame(self, style="SideBar.TFrame", width=210)
        menu.grid(row=0, column=0, rowspan=2, sticky="ns")
        menu.grid_propagate(False)
        ttk.Label(menu, text="Kho VPP", style="SideBar.TLabel",
                  padding=(18, 20)).pack(anchor="w")
        for khoa, nhan, _ in self._menu_cho_phep():
            nut = ttk.Button(menu, text=nhan, style="Menu.TButton",
                             command=lambda k=khoa: self.hien(k))
            nut.pack(fill="x")
            self.nut_menu[khoa] = nut

        # Thanh trên (nền trắng): tiêu đề màn hình + người dùng + đăng xuất
        thanh_tren = ttk.Frame(self, style="Header.TFrame", padding=(22, 14))
        thanh_tren.grid(row=0, column=1, sticky="ew")
        self.lbl_tieu_de = ttk.Label(thanh_tren, text="", style="HeaderTieuDe.TLabel")
        self.lbl_tieu_de.pack(side="left")
        ttk.Button(thanh_tren, text="Đăng xuất", command=self.on_logout).pack(side="right")
        ttk.Label(thanh_tren, text=f"{user['ho_ten']}  ·  {user['vai_tro']}",
                  style="HeaderPhu.TLabel").pack(side="right", padx=16)

        # Khung nội dung: nơi các "tờ giấy" xếp chồng lên nhau
        self.khung_noi_dung = ttk.Frame(self)
        self.khung_noi_dung.grid(row=1, column=1, sticky="nsew")
        self.khung_noi_dung.grid_rowconfigure(0, weight=1)
        self.khung_noi_dung.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def hien(self, khoa):
        nhan = next(m[1] for m in MENU if m[0] == khoa)

        if khoa not in self.man_hinh:                 # lần đầu: tạo rồi GIỮ LẠI
            lop = MAN_HINH_THAT.get(khoa)
            frame = lop(self.khung_noi_dung) if lop else PlaceholderView(self.khung_noi_dung, nhan)
            frame.grid(row=0, column=0, sticky="nsew")
            self.man_hinh[khoa] = frame

        frame = self.man_hinh[khoa]
        frame.tkraise()                               # rút tờ này lên trên
        self.lbl_tieu_de.config(text=nhan)
        for k, nut in self.nut_menu.items():          # tô sáng mục menu đang chọn
            nut.config(style="MenuChon.TButton" if k == khoa else "Menu.TButton")

        if hasattr(frame, "lam_moi"):                 # mỗi lần hiện: nạp lại dữ liệu
            try:
                frame.lam_moi()
            except PermissionDenied as loi:
                messagebox.showwarning("Không đủ quyền", str(loi))
                if not Session.is_logged_in():        # bị khóa -> đưa về đăng nhập
                    self.on_logout()