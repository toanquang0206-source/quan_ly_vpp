from tkinter import ttk

from views.lich_su_phieu_nhap_view import LichSuPhieuNhapView
from views.nhap_kho_view import NhapKhoView
from views.the_kho_view import TheKhoView


class KhoView(ttk.Frame):
    """Menu Kho: nhập kho, lịch sử phiếu nhập, thẻ kho."""

    def __init__(self, master):
        super().__init__(master, padding=8)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.nb = ttk.Notebook(self)
        self.nb.grid(row=0, column=0, sticky="nsew")
        self.tab_nhap = NhapKhoView(self.nb)
        self.tab_lich_su = LichSuPhieuNhapView(self.nb)
        self.tab_the_kho = TheKhoView(self.nb)
        self.nb.add(self.tab_nhap, text="Nhập kho")
        self.nb.add(self.tab_lich_su, text="Lịch sử phiếu nhập")
        self.nb.add(self.tab_the_kho, text="Thẻ kho")
        # Gắn sự kiện SAU KHI thêm đủ tab để không bị gọi lúc đang dựng
        self.nb.bind("<<NotebookTabChanged>>", self._lam_moi_tab_dang_chon)

    def _lam_moi_tab_dang_chon(self, event=None):
        tab = self.nb.nametowidget(self.nb.select())
        if hasattr(tab, "lam_moi"):
            tab.lam_moi()

    def lam_moi(self):
        """Mỗi lần menu Kho hiện lên: làm mới tab đang mở (các tab khác làm mới khi được chọn)."""
        self._lam_moi_tab_dang_chon()