import tkinter as tk
from tkinter import ttk

from controllers.hoa_don_controller import HoaDonController
from utils.formatters import dinh_dang_gio, dinh_dang_tien
from utils.validators import doc_so
from views.chung import goi_controller


class TraHangForm(tk.Toplevel):
    """Hộp thoại trả hàng: nhập số lượng trả cho từng mặt hàng của một hóa đơn."""

    def __init__(self, master, chi_tiet, on_saved):
        super().__init__(master)
        hd = chi_tiet["hoa_don"]
        self.hoa_don_id = hd["id"]
        self.dong = chi_tiet["dong"]
        self.on_saved = on_saved                  # on_saved(thông điệp, dữ liệu) khi trả hàng thành công
        self.title(f"Trả hàng — {hd['ma_hoa_don']}")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())

        self.var_sl = {d["san_pham_id"]: tk.StringVar(value="0") for d in self.dong}
        self.var_ly_do = tk.StringVar()
        self._xay_dung(hd, chi_tiet["han_doi_tra"])
        self._can_giua(master)
        self.wait_visibility()
        self.grab_set()
        self.entry_dau.focus_set()

    def _xay_dung(self, hd, han):
        khung = ttk.Frame(self, padding=18)
        khung.pack()
        ttk.Label(khung, text=f"Trả hàng cho hóa đơn {hd['ma_hoa_don']}",
                  style="TieuDe.TLabel").grid(row=0, column=0, columnspan=5, sticky="w")
        ttk.Label(khung, text=f"Hạn đổi trả: {dinh_dang_gio(han)}   ·   Hoàn tiền theo giá ghi trên hóa đơn gốc",
                  style="Phu.TLabel").grid(row=1, column=0, columnspan=5, sticky="w", pady=(2, 14))

        for c, (chu, can) in enumerate([("Sản phẩm", "w"), ("Đơn giá", "e"), ("Đã mua", "e"),
                                         ("Đã trả", "e"), ("Trả lần này", "e")]):
            ttk.Label(khung, text=chu, font=("", 10, "bold")).grid(
                row=2, column=c, sticky=can, padx=(0, 14), pady=(0, 6))

        self.entry_dau = None
        for i, d in enumerate(self.dong, start=3):
            ttk.Label(khung, text=f"{d['ma_sp']} — {d['ten_sp']}").grid(
                row=i, column=0, sticky="w", padx=(0, 14), pady=3)
            ttk.Label(khung, text=dinh_dang_tien(d["don_gia"])).grid(
                row=i, column=1, sticky="e", padx=(0, 14))
            ttk.Label(khung, text=str(d["so_luong"])).grid(row=i, column=2, sticky="e", padx=(0, 14))
            ttk.Label(khung, text=str(d["da_tra"])).grid(row=i, column=3, sticky="e", padx=(0, 14))
            o = ttk.Entry(khung, textvariable=self.var_sl[d["san_pham_id"]], width=7, justify="right")
            o.grid(row=i, column=4, sticky="e")
            o.bind("<KeyRelease>", lambda e: self._cap_nhat_tien())
            if d["con_tra_duoc"] <= 0:
                o.config(state="disabled")        # đã trả hết mặt hàng này
            elif self.entry_dau is None:
                self.entry_dau = o
        if self.entry_dau is None:
            self.entry_dau = khung
        h = 3 + len(self.dong)

        ttk.Label(khung, text="Lý do (không bắt buộc)").grid(
            row=h, column=0, sticky="w", pady=(14, 0))
        ttk.Entry(khung, textvariable=self.var_ly_do, width=46).grid(
            row=h + 1, column=0, columnspan=5, sticky="ew", pady=(4, 0))
        self.lbl_tien = ttk.Label(khung, text="Hoàn trả khách: 0 đ", style="Tong.TLabel")
        self.lbl_tien.grid(row=h + 2, column=0, columnspan=5, sticky="w", pady=(14, 0))
        self.lbl_loi = ttk.Label(khung, foreground="#DC2626", wraplength=480, justify="left")
        self.lbl_loi.grid(row=h + 3, column=0, columnspan=5, sticky="w", pady=(6, 0))

        nut = ttk.Frame(khung)
        nut.grid(row=h + 4, column=0, columnspan=5, sticky="e", pady=(12, 0))
        ttk.Button(nut, text="Đóng", command=self.destroy).pack(side="right")
        ttk.Button(nut, text="Xác nhận trả hàng", command=self._luu,
                   style="Accent.TButton").pack(side="right", padx=8)
        self.bind("<Return>", lambda e: self._luu())
        self.bind("<Escape>", lambda e: self.destroy())

    def _cap_nhat_tien(self):
        """Ước tính số tiền hoàn để người bán biết trước. Số tiền thật do hệ thống tính khi lưu."""
        tong = 0
        for d in self.dong:
            so_luong, loi = doc_so(self.var_sl[d["san_pham_id"]].get(), "số lượng", mac_dinh=0)
            if loi:
                self.lbl_tien.config(text="Hoàn trả khách: —")
                return
            tong += so_luong * d["don_gia"]
        self.lbl_tien.config(text=f"Hoàn trả khách: {dinh_dang_tien(tong)}")

    def _can_giua(self, master):
        self.update_idletasks()
        goc = master.winfo_toplevel()
        x = goc.winfo_rootx() + (goc.winfo_width() - self.winfo_width()) // 2
        y = goc.winfo_rooty() + (goc.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _luu(self):
        dong_tra = [{"san_pham_id": d["san_pham_id"], "so_luong": self.var_sl[d["san_pham_id"]].get()}
                    for d in self.dong]
        kq = goi_controller(self, HoaDonController.tra_hang, self.hoa_don_id,
                            dong_tra, self.var_ly_do.get())
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if ok:
            self.on_saved(thong_diep, du_lieu)
            self.destroy()
        else:
            self.lbl_loi.config(text=thong_diep)      # lỗi hiện ngay trong hộp thoại, không mất dữ liệu đã gõ