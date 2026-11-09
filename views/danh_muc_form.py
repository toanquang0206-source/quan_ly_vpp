import tkinter as tk
from tkinter import ttk

from views.chung import goi_controller
from views.theme import MAU


class FormThuocTinh(tk.Toplevel):
    """
    Hộp thoại thêm/sửa dùng chung. `truong` là danh sách ô nhập:
        [{"khoa": "ten", "nhan": "Tên loại *", "rong": 40}, ...]
    ham_luu(du_lieu: dict) trả về (ok, thông điệp, dữ liệu) như mọi hàm Controller.
    """

    def __init__(self, master, tieu_de, truong, gia_tri, ham_luu, on_saved, ghi_chu=""):
        super().__init__(master)
        self.title(tieu_de)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.master_goc = master
        self.ham_luu = ham_luu
        self.on_saved = on_saved
        self.var = {t["khoa"]: tk.StringVar(value=gia_tri.get(t["khoa"], "") or "") for t in truong}

        khung = ttk.Frame(self, padding=22)
        khung.pack()
        ttk.Label(khung, text=tieu_de, style="TieuDe.TLabel").grid(row=0, column=0, sticky="w")
        o_dau = None
        for i, t in enumerate(truong):
            ttk.Label(khung, text=t["nhan"]).grid(row=1 + 2 * i, column=0, sticky="w", pady=(12, 0))
            o = ttk.Entry(khung, textvariable=self.var[t["khoa"]], width=t.get("rong", 40))
            o.grid(row=2 + 2 * i, column=0, sticky="ew", pady=(4, 0))
            o_dau = o_dau or o
        h = 1 + 2 * len(truong)
        if ghi_chu:
            ttk.Label(khung, text=ghi_chu, style="Phu.TLabel", wraplength=380, justify="left").grid(
                row=h, column=0, sticky="w", pady=(10, 0))
        self.lbl_loi = ttk.Label(khung, foreground=MAU["nguy_hiem"], wraplength=380, justify="left")
        self.lbl_loi.grid(row=h + 1, column=0, sticky="w", pady=(6, 0))
        nut = ttk.Frame(khung)
        nut.grid(row=h + 2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(nut, text="Lưu", command=self._luu, style="Accent.TButton").pack(side="right")
        ttk.Button(nut, text="Hủy", command=self.destroy).pack(side="right", padx=8)
        self.bind("<Return>", lambda e: self._luu())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        goc = master.winfo_toplevel()
        x = goc.winfo_rootx() + (goc.winfo_width() - self.winfo_width()) // 2
        y = goc.winfo_rooty() + (goc.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()
        o_dau.focus_set()

    def _luu(self):
        du_lieu = {khoa: bien.get() for khoa, bien in self.var.items()}
        kq = goi_controller(self, self.ham_luu, du_lieu)
        if kq is None:
            return
        ok, thong_diep, _ = kq
        if ok:
            self.on_saved(thong_diep)
            self.destroy()
        else:
            self.lbl_loi.config(text=thong_diep)       # lỗi hiện ngay trong hộp thoại, không mất dữ liệu đã gõ