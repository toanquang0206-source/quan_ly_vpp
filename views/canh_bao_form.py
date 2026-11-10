import tkinter as tk
from tkinter import ttk

from views.bao_cao_view import _tao_bang


class CanhBaoHetHangForm(tk.Toplevel):
    """
    Hộp thoại cảnh báo hết hàng khi vừa đăng nhập. CỐ Ý không chặn thao tác phía sau
    (không grab): người dùng có thể để đó và làm việc tiếp.
    """

    def __init__(self, master, du_lieu, on_den_kho):
        super().__init__(master)
        self.title("Cảnh báo hết hàng")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.on_den_kho = on_den_kho
        dong = du_lieu["dong"]

        khung = ttk.Frame(self, padding=20)
        khung.pack()
        ttk.Label(khung, text=f"Có {du_lieu['tong']} sản phẩm sắp hết hàng",
                  style="TieuDe.TLabel").pack(anchor="w")
        phu = (f"Đang hiển thị {len(dong)} sản phẩm thiếu nhiều nhất."
               if du_lieu["tong"] > len(dong)
               else "Số tồn đang bằng hoặc thấp hơn mức tối thiểu đã đặt.")
        ttk.Label(khung, text=phu, style="Phu.TLabel").pack(anchor="w", pady=(2, 10))

        khung_bang, cay = _tao_bang(
            khung, ("ma_sp", "ten_sp", "ton_kho", "ton_toi_thieu"),
            {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "ton_kho": "Tồn", "ton_toi_thieu": "Tối thiểu"},
            {"ma_sp": 90, "ten_sp": 240, "ton_kho": 60, "ton_toi_thieu": 90},
            {"ton_kho", "ton_toi_thieu"}, chieu_cao=min(max(len(dong), 3), 8))
        khung_bang.pack(fill="x")
        for r in dong:
            cay.insert("", "end", tags=("sap_het",) if r["ton_kho"] <= 0 else ("cham",),
                       values=(r["ma_sp"], r["ten_sp"], r["ton_kho"], r["ton_toi_thieu"]))

        nut = ttk.Frame(khung)
        nut.pack(fill="x", pady=(14, 0))
        ttk.Button(nut, text="Đến màn hình Kho", command=self._den_kho,
                   style="Accent.TButton").pack(side="right")
        ttk.Button(nut, text="Để sau", command=self.destroy).pack(side="right", padx=8)
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        goc = master.winfo_toplevel()
        x = goc.winfo_rootx() + (goc.winfo_width() - self.winfo_width()) // 2
        y = goc.winfo_rooty() + (goc.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _den_kho(self):
        self.destroy()
        self.on_den_kho()