import tkinter as tk
from tkinter import ttk

from controllers.san_pham_controller import SanPhamController
from views.chung import goi_controller


class SanPhamForm(tk.Toplevel):
    """Hộp thoại dùng chung cho THÊM (san_pham_id=None) và SỬA."""

    def __init__(self, master, san_pham_id=None, on_saved=None):
        super().__init__(master)
        self.san_pham_id = san_pham_id
        self.on_saved = on_saved            # hàm gọi khi lưu thành công: on_saved(thông điệp)
        self.title("Sửa sản phẩm" if san_pham_id else "Thêm sản phẩm")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())

        self.var = {k: tk.StringVar() for k in
                    ("ma_sp", "ten_sp", "danh_muc", "don_vi",
                     "gia_nhap", "gia_ban", "ton_toi_thieu", "mo_ta")}
        self.ds_danh_muc, self.ds_don_vi = {}, {}

        self._xay_dung()
        if not self._nap_du_lieu():
            self.destroy()
            return
        self._can_giua(master)
        self.wait_visibility()
        self.grab_set()                     # chặn thao tác cửa sổ phía sau khi form đang mở
        self.entry_ma.focus_set()

    def _xay_dung(self):
        khung = ttk.Frame(self, padding=16)
        khung.pack()

        def hang(r, nhan, widget):
            lbl = ttk.Label(khung, text=nhan)
            lbl.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 12))
            widget.grid(row=r, column=1, sticky="ew", pady=4)
            return lbl

        self.entry_ma = ttk.Entry(khung, textvariable=self.var["ma_sp"], width=34)
        hang(0, "Mã sản phẩm *", self.entry_ma)
        hang(1, "Tên sản phẩm *", ttk.Entry(khung, textvariable=self.var["ten_sp"], width=34))
        self.cbo_dm = ttk.Combobox(khung, textvariable=self.var["danh_muc"],
                                   state="readonly", width=32)
        hang(2, "Danh mục *", self.cbo_dm)
        self.cbo_dv = ttk.Combobox(khung, textvariable=self.var["don_vi"],
                                   state="readonly", width=32)
        hang(3, "Đơn vị tính *", self.cbo_dv)
        self.entry_gia_nhap = ttk.Entry(khung, textvariable=self.var["gia_nhap"], width=34)
        self.lbl_gia_nhap = hang(4, "Giá nhập dự kiến (đ) *", self.entry_gia_nhap)
        hang(5, "Giá bán (đ) *", ttk.Entry(khung, textvariable=self.var["gia_ban"], width=34))
        hang(6, "Tồn tối thiểu", ttk.Entry(khung, textvariable=self.var["ton_toi_thieu"], width=34))
        hang(7, "Mô tả", ttk.Entry(khung, textvariable=self.var["mo_ta"], width=34))

        # Chỉ hiện khi sửa: nhắc rằng số tồn KHÔNG sửa được ở đây
        self.lbl_ton = ttk.Label(khung, foreground="#555555", wraplength=340, justify="left")
        self.lbl_loi = ttk.Label(khung, foreground="#c0392b", wraplength=340, justify="left")
        self.lbl_loi.grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 0))

        nut = ttk.Frame(khung)
        nut.grid(row=10, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(nut, text="Hủy", command=self.destroy).pack(side="right")
        ttk.Button(nut, text="Lưu", command=self._luu, style="Accent.TButton").pack(side="right", padx=8)

        self.bind("<Return>", lambda e: self._luu())
        self.bind("<Escape>", lambda e: self.destroy())

    def _nap_du_lieu(self):
        """Nạp danh sách chọn (+ dữ liệu cũ nếu đang sửa). Trả về False nếu không nạp được."""
        dm = goi_controller(self, SanPhamController.danh_sach_danh_muc)
        dv = goi_controller(self, SanPhamController.danh_sach_don_vi)
        if dm is None or dv is None:
            return False
        self.ds_danh_muc = {d["ten_danh_muc"]: d["id"] for d in dm}
        self.ds_don_vi = {d["ten"]: d["id"] for d in dv}
        self.cbo_dm["values"] = list(self.ds_danh_muc)
        self.cbo_dv["values"] = list(self.ds_don_vi)

        if self.san_pham_id is not None:
            ct = goi_controller(self, SanPhamController.chi_tiet, self.san_pham_id)
            if ct is None:
                return False
            ten_dm = next((t for t, i in self.ds_danh_muc.items() if i == ct["danh_muc_id"]), "")
            ten_dv = next((t for t, i in self.ds_don_vi.items() if i == ct["don_vi_tinh_id"]), "")
            self.var["ma_sp"].set(ct["ma_sp"])
            self.var["ten_sp"].set(ct["ten_sp"])
            self.var["danh_muc"].set(ten_dm)
            self.var["don_vi"].set(ten_dv)
            self.var["gia_nhap"].set(str(int(ct["gia_nhap"])))
            self.var["gia_ban"].set(str(int(ct["gia_ban"])))
            self.var["ton_toi_thieu"].set(str(ct["ton_toi_thieu"]))
            self.var["mo_ta"].set(ct["mo_ta"] or "")
            # Khi sửa: giá nhập là GIÁ VỐN BÌNH QUÂN do hệ thống tự tính lúc nhập kho
            self.lbl_gia_nhap.config(text="Giá vốn bình quân (đ)")
            self.entry_gia_nhap.config(state="readonly")
            self.lbl_ton.config(
                text=f"Tồn kho hiện tại: {ct['ton_kho']} (chỉ thay đổi qua "
                     f"nhập kho, bán hàng hoặc kiểm kê)")
            self.lbl_ton.grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 0))
        return True

    def _can_giua(self, master):
        self.update_idletasks()
        goc = master.winfo_toplevel()
        x = goc.winfo_rootx() + (goc.winfo_width() - self.winfo_width()) // 2
        y = goc.winfo_rooty() + (goc.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _thu_thap(self):
        """Gom giá trị THÔ từ các ô nhập. Việc kiểm tra là của Controller."""
        return {
            "ma_sp": self.var["ma_sp"].get(),
            "ten_sp": self.var["ten_sp"].get(),
            "danh_muc_id": self.ds_danh_muc.get(self.var["danh_muc"].get()),
            "don_vi_tinh_id": self.ds_don_vi.get(self.var["don_vi"].get()),
            "gia_nhap": self.var["gia_nhap"].get(),
            "gia_ban": self.var["gia_ban"].get(),
            "ton_toi_thieu": self.var["ton_toi_thieu"].get(),
            "mo_ta": self.var["mo_ta"].get(),
        }

    def _luu(self):
        du_lieu = self._thu_thap()
        if self.san_pham_id is None:
            kq = goi_controller(self, SanPhamController.them, du_lieu)
        else:
            kq = goi_controller(self, SanPhamController.sua, self.san_pham_id, du_lieu)
        if kq is None:
            return
        ok, thong_diep = kq
        if ok:
            if self.on_saved:
                self.on_saved(thong_diep)
            self.destroy()
        else:
            self.lbl_loi.config(text=thong_diep)    # lỗi hiện ngay trong form, form không đóng