"""
Giao diện dùng chung cho toàn ứng dụng: màu sắc, phông chữ, kiểu nút, kiểu bảng.
Gọi ap_dung_theme(root) MỘT LẦN khi khởi động App; mọi màn hình đều được hưởng.
"""
import sys
import tkinter as tk
from tkinter import ttk

MAU = {
    "nen": "#F3F5F9",          # nền cửa sổ
    "the": "#FFFFFF",          # nền ô nhập, bảng, thẻ
    "chu": "#1F2937",          # chữ chính
    "chu_phu": "#6B7280",      # chữ phụ, gợi ý
    "vien": "#CBD5E1",         # đường viền
    "chinh": "#2563EB",        # màu nhấn chính (xanh dương)
    "chinh_dam": "#1D4ED8",
    "chinh_nhat": "#DBEAFE",
    "thanh_ben": "#1E293B",    # nền cột menu bên trái
    "thanh_ben_hover": "#334155",
    "nguy_hiem": "#DC2626",
    "thanh_cong": "#15803D",
    "canh_bao": "#B45309",
    "dong_chan": "#F8FAFC",    # màu dòng xen kẽ trong bảng
    "dong_chon": "#BFDBFE",
}


def _chon_phong():
    return "Segoe UI" if sys.platform.startswith("win") else "DejaVu Sans"


PHONG = _chon_phong()
CO_CHU = 10


def ap_dung_theme(root):
    f = PHONG
    root.configure(bg=MAU["nen"])
    # Các widget Tk thuần (Listbox, Toplevel...) không đi theo ttk nên cấu hình riêng
    root.option_add("*Toplevel.background", MAU["nen"])
    root.option_add("*Listbox.font", (f, CO_CHU))
    root.option_add("*Listbox.background", MAU["the"])
    root.option_add("*Listbox.foreground", MAU["chu"])
    root.option_add("*Listbox.selectBackground", MAU["chinh"])
    root.option_add("*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*Listbox.relief", "solid")
    root.option_add("*Listbox.borderWidth", 1)
    root.option_add("*Listbox.highlightThickness", 0)

    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=MAU["nen"], foreground=MAU["chu"], font=(f, CO_CHU),
                bordercolor=MAU["vien"], focuscolor=MAU["nen"])
    s.configure("TFrame", background=MAU["nen"])
    s.configure("TLabel", background=MAU["nen"], foreground=MAU["chu"])
    s.configure("Phu.TLabel", foreground=MAU["chu_phu"])
    s.configure("TieuDe.TLabel", font=(f, 15, "bold"))
    s.configure("Tong.TLabel", font=(f, 12, "bold"), foreground=MAU["chinh_dam"])
    s.configure("TongLon.TLabel", font=(f, 16, "bold"), foreground=MAU["chinh_dam"])
        # ----- Thẻ số liệu (báo cáo) và các tab -----
    s.configure("The.TFrame", background=MAU["the"], relief="solid", borderwidth=1,
                bordercolor=MAU["vien"])
    s.configure("The.TLabel", background=MAU["the"], foreground=MAU["chu_phu"])
    s.configure("TheSo.TLabel", background=MAU["the"], foreground=MAU["chu"],
                font=(f, 16, "bold"))
    s.configure("TNotebook", background=MAU["nen"], borderwidth=0)
    s.configure("TNotebook.Tab", padding=(20, 9), background="#E2E8F0", foreground=MAU["chu"])
    s.map("TNotebook.Tab", background=[("selected", MAU["the"])],
          foreground=[("selected", MAU["chinh_dam"])])
    
    # ----- Nút -----
    s.configure("TButton", padding=(14, 7), relief="flat", borderwidth=0,
                background="#E2E8F0", foreground=MAU["chu"])
    s.map("TButton",
          background=[("disabled", "#EEF1F5"), ("pressed", "#CBD5E1"), ("active", "#D5DEEA")],
          foreground=[("disabled", "#9CA3AF")])
    s.configure("Accent.TButton", background=MAU["chinh"], foreground="#FFFFFF",
                font=(f, CO_CHU, "bold"))
    s.map("Accent.TButton",
          background=[("disabled", "#93B4F0"), ("pressed", "#1E40AF"), ("active", MAU["chinh_dam"])],
          foreground=[("disabled", "#F1F5F9")])
    s.configure("Danger.TButton", background="#FEE2E2", foreground=MAU["nguy_hiem"])
    s.map("Danger.TButton",
          background=[("disabled", "#F5EEEE"), ("active", "#FCA5A5")],
          foreground=[("disabled", "#D1A5A5")])

    # ----- Ô nhập -----
    s.configure("TEntry", fieldbackground=MAU["the"], padding=6, bordercolor=MAU["vien"],
                lightcolor=MAU["vien"], darkcolor=MAU["vien"])
    s.map("TEntry", bordercolor=[("focus", MAU["chinh"])], lightcolor=[("focus", MAU["chinh"])],
          darkcolor=[("focus", MAU["chinh"])], fieldbackground=[("readonly", "#EEF1F5")])
    s.configure("TCombobox", fieldbackground=MAU["the"], padding=6, arrowsize=14,
                bordercolor=MAU["vien"], lightcolor=MAU["vien"], darkcolor=MAU["vien"])
    s.map("TCombobox", fieldbackground=[("readonly", MAU["the"])],
          bordercolor=[("focus", MAU["chinh"])], lightcolor=[("focus", MAU["chinh"])],
          darkcolor=[("focus", MAU["chinh"])])
    root.option_add("*TCombobox*Listbox.font", (f, CO_CHU))
    root.option_add("*TCombobox*Listbox.selectBackground", MAU["chinh"])
    s.configure("TCheckbutton", background=MAU["nen"])
    s.configure("TLabelframe", background=MAU["nen"], bordercolor=MAU["vien"], relief="solid")
    s.configure("TLabelframe.Label", background=MAU["nen"], foreground=MAU["chinh_dam"],
                font=(f, CO_CHU, "bold"))

    # ----- Bảng -----
    s.configure("Treeview", background=MAU["the"], fieldbackground=MAU["the"],
                foreground=MAU["chu"], rowheight=30, borderwidth=1, bordercolor=MAU["vien"],
                lightcolor=MAU["vien"], darkcolor=MAU["vien"])
    s.map("Treeview", background=[("selected", MAU["dong_chon"])],
          foreground=[("selected", MAU["chu"])])
    s.configure("Treeview.Heading", background="#E8EEF9", foreground=MAU["chu"],
                font=(f, CO_CHU, "bold"), padding=(8, 8), relief="flat", borderwidth=0)
    s.map("Treeview.Heading", background=[("active", MAU["chinh_nhat"])])
    s.configure("Vertical.TScrollbar", background="#E2E8F0", troughcolor=MAU["nen"],
                bordercolor=MAU["nen"], arrowcolor=MAU["chu_phu"], relief="flat")

    # ----- Khung đầu trang và cột menu (MainWindow) -----
    s.configure("Header.TFrame", background=MAU["the"])
    s.configure("Header.TLabel", background=MAU["the"], foreground=MAU["chu"])
    s.configure("HeaderTieuDe.TLabel", background=MAU["the"], foreground=MAU["chu"],
                font=(f, 15, "bold"))
    s.configure("HeaderPhu.TLabel", background=MAU["the"], foreground=MAU["chu_phu"])
    s.configure("SideBar.TFrame", background=MAU["thanh_ben"])
    s.configure("SideBar.TLabel", background=MAU["thanh_ben"], foreground="#F8FAFC",
                font=(f, 12, "bold"))
    s.configure("Menu.TButton", background=MAU["thanh_ben"], foreground="#CBD5E1",
                anchor="w", padding=(18, 11), font=(f, CO_CHU))
    s.map("Menu.TButton", background=[("active", MAU["thanh_ben_hover"])],
          foreground=[("active", "#FFFFFF")])
    s.configure("MenuChon.TButton", background=MAU["chinh"], foreground="#FFFFFF",
                anchor="w", padding=(18, 11), font=(f, CO_CHU, "bold"))
    s.map("MenuChon.TButton", background=[("active", MAU["chinh_dam"])])
    return s


def to_mau_xen_ke(tree):
    """Tô màu xen kẽ các dòng của bảng cho dễ đọc. Gọi SAU khi đổ dữ liệu vào bảng."""
    tree.tag_configure("dong_chan", background=MAU["dong_chan"])
    for i, iid in enumerate(tree.get_children()):
        tags = [t for t in tree.item(iid, "tags") if t != "dong_chan"]
        if i % 2 == 1:
            tags.append("dong_chan")
        tree.item(iid, tags=tags)