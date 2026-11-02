import tkinter as tk
from tkinter import ttk


class PlaceholderView(ttk.Frame):
    """Màn hình giữ chỗ cho các chức năng chưa làm."""

    def __init__(self, master, tieu_de):
        super().__init__(master, padding=24)
        ttk.Label(self, text=tieu_de, style="TieuDe.TLabel").pack(anchor="w")
        ttk.Label(self, text="Chức năng đang được xây dựng.", style="Phu.TLabel").pack(anchor="w", pady=8)