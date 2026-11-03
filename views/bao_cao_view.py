import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from controllers.bao_cao_controller import BaoCaoController
from utils.formatters import dinh_dang_ngay, dinh_dang_so, dinh_dang_tien
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke

KHOANG_NHANH = ["7 ngày qua", "30 ngày qua", "Tháng này", "Tháng trước", "Năm nay", "Tùy chọn"]
KIEU_HIEN_THI = {"Theo ngày": "ngay", "Theo tháng": "thang", "Theo năm": "nam"}
BANG_MAU = ["#2563EB", "#16A34A", "#F59E0B", "#DC2626", "#7C3AED", "#0891B2", "#DB2777", "#65A30D"]


def _nhan_ky(ky, kieu, ngan=False):
    """'2026-11-02' -> '02/11/2026' (hoặc '02/11' khi ngắn); '2026-11' -> '11/2026'."""
    if kieu == "ngay":
        y, m, d = ky.split("-")
        return f"{d}/{m}" if ngan else f"{d}/{m}/{y}"
    if kieu == "thang":
        y, m = ky.split("-")
        return f"{m}/{y}"
    return ky


class BieuDo(ttk.Frame):
    """Khung vẽ biểu đồ matplotlib nhúng trong Tkinter."""

    def __init__(self, master, rong=4.2, cao=3.4):
        super().__init__(master)
        self.fig = Figure(figsize=(rong, cao), dpi=100, facecolor=MAU["the"])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def ve(self, ham_ve):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(MAU["the"])
        ham_ve(ax)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    @staticmethod
    def lam_dep(ax):
        for canh in ("top", "right"):
            ax.spines[canh].set_visible(False)
        for canh in ("left", "bottom"):
            ax.spines[canh].set_color(MAU["vien"])
        ax.tick_params(colors=MAU["chu_phu"], labelsize=8)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: dinh_dang_so(v)))
        ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
        ax.set_axisbelow(True)


def _tao_bang(cha, cot, tieu_de, rong, can_phai, chieu_cao=9):
    khung = ttk.Frame(cha)
    cay = ttk.Treeview(khung, columns=cot, show="headings", height=chieu_cao, selectmode="browse")
    for c in cot:
        can = "e" if c in can_phai else "w"
        cay.heading(c, text=tieu_de[c], anchor=can)
        cay.column(c, width=rong[c], anchor=can)
    cuon = ttk.Scrollbar(khung, orient="vertical", command=cay.yview)
    cay.configure(yscrollcommand=cuon.set)
    cay.pack(side="left", fill="both", expand=True)
    cuon.pack(side="right", fill="y")
    cay.tag_configure("am", foreground=MAU["nguy_hiem"])
    cay.tag_configure("sap_het", foreground=MAU["nguy_hiem"])
    cay.tag_configure("cham", foreground=MAU["canh_bao"])
    cay.tag_configure("ngung", foreground="#9CA3AF")
    return khung, cay


def _the_so(cha, tieu_de):
    """Một thẻ số liệu: tiêu đề nhỏ phía trên, con số lớn phía dưới. Trả về (khung, nhãn số)."""
    khung = ttk.Frame(cha, style="The.TFrame", padding=(14, 10))
    ttk.Label(khung, text=tieu_de, style="The.TLabel").pack(anchor="w")
    so = ttk.Label(khung, text="—", style="TheSo.TLabel")
    so.pack(anchor="w")
    return khung, so


class BaoCaoView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_nhanh = tk.StringVar(value="30 ngày qua")
        self.var_tu = tk.StringVar()
        self.var_den = tk.StringVar()
        self.var_kieu = tk.StringVar(value="Theo ngày")
        self._xay_dung()
        self._ap_dung_nhanh(tu_xem=False)

    # ---------- dựng giao diện ----------
    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        loc = ttk.Frame(self)
        loc.grid(row=0, column=0, sticky="ew")
        ttk.Label(loc, text="Thời gian").pack(side="left")
        cbo = ttk.Combobox(loc, textvariable=self.var_nhanh, values=KHOANG_NHANH,
                           state="readonly", width=12)
        cbo.pack(side="left", padx=(6, 10))
        cbo.bind("<<ComboboxSelected>>", lambda e: self._ap_dung_nhanh())
        ttk.Label(loc, text="Từ").pack(side="left")
        o_tu = ttk.Entry(loc, textvariable=self.var_tu, width=10)
        o_tu.pack(side="left", padx=(6, 8))
        ttk.Label(loc, text="Đến").pack(side="left")
        o_den = ttk.Entry(loc, textvariable=self.var_den, width=10)
        o_den.pack(side="left", padx=(6, 10))
        for o in (o_tu, o_den):
            o.bind("<KeyRelease>", lambda e: self.var_nhanh.set("Tùy chọn"))
            o.bind("<Return>", lambda e: self._xem())
        ttk.Label(loc, text="Hiển thị").pack(side="left")
        cbo2 = ttk.Combobox(loc, textvariable=self.var_kieu, values=list(KIEU_HIEN_THI),
                            state="readonly", width=10)
        cbo2.pack(side="left", padx=(6, 10))
        cbo2.bind("<<ComboboxSelected>>", lambda e: self._xem())
        ttk.Button(loc, text="Xem báo cáo", command=self._xem, style="Accent.TButton").pack(side="left")

        self.lbl_thong_bao = ttk.Label(self, text="", foreground=MAU["nguy_hiem"])
        self.lbl_thong_bao.grid(row=1, column=0, sticky="w", pady=(4, 4))

        self.nb = ttk.Notebook(self)
        self.nb.grid(row=2, column=0, sticky="nsew")
        self._tab_doanh_thu()
        self._tab_danh_muc()
        self._tab_san_pham()
        self._tab_ton_kho()

    def _tab_doanh_thu(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="Doanh thu")
        tab.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="the")
        tab.grid_rowconfigure(1, weight=1)
        self.the = {}
        for i, (khoa, tieu_de) in enumerate([("thuan", "Doanh thu thuần"), ("loi_nhuan", "Lợi nhuận gộp"),
                                              ("so_hoa_don", "Số hóa đơn đã lập"), ("hoan", "Hoàn trả và hủy")]):
            khung, so = _the_so(tab, tieu_de)
            khung.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(0, 10))
            self.the[khoa] = so
        self.bd_doanh_thu = BieuDo(tab)
        self.bd_doanh_thu.grid(row=1, column=0, columnspan=2, sticky="nsew")
        cot = ("ky", "ban", "hoan", "thuan", "loi_nhuan")
        khung, self.bang_dt = _tao_bang(
            tab, cot,
            {"ky": "Kỳ", "ban": "Bán", "hoan": "Hoàn/hủy", "thuan": "Thuần", "loi_nhuan": "Lãi gộp"},
            {"ky": 95, "ban": 78, "hoan": 86, "thuan": 80, "loi_nhuan": 82},
            {"ban", "hoan", "thuan", "loi_nhuan"})
        khung.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=(10, 0))

    def _tab_danh_muc(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="Theo loại sản phẩm")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.bd_danh_muc = BieuDo(tab)
        self.bd_danh_muc.grid(row=0, column=0, sticky="nsew")
        cot = ("ten", "thuan", "ty_trong", "loi_nhuan")
        khung, self.bang_dm = _tao_bang(
            tab, cot,
            {"ten": "Loại sản phẩm", "thuan": "Doanh thu", "ty_trong": "Tỷ trọng", "loi_nhuan": "Lãi gộp"},
            {"ten": 130, "thuan": 115, "ty_trong": 70, "loi_nhuan": 95},
            {"thuan", "ty_trong", "loi_nhuan"})
        khung.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    def _tab_san_pham(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="Sản phẩm bán chạy")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.bd_san_pham = BieuDo(tab)
        self.bd_san_pham.grid(row=0, column=0, sticky="nsew")
        cot = ("ma_sp", "ten_sp", "sl_thuan", "thuan", "loi_nhuan")
        khung, self.bang_sp = _tao_bang(
            tab, cot,
            {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "sl_thuan": "SL",
             "thuan": "Doanh thu", "loi_nhuan": "Lãi gộp"},
            {"ma_sp": 78, "ten_sp": 130, "sl_thuan": 50, "thuan": 90, "loi_nhuan": 82},
            {"sl_thuan", "thuan", "loi_nhuan"})
        khung.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    def _tab_ton_kho(self):
        tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(tab, text="Tồn kho")
        tab.grid_columnconfigure((0, 1, 2), weight=1, uniform="the")
        tab.grid_rowconfigure(1, weight=1)
        self.the_kho = {}
        for i, (khoa, tieu_de) in enumerate([("gia_tri", "Giá trị tồn kho (theo giá vốn)"),
                                              ("sap_het", "Sản phẩm sắp hết hàng"),
                                              ("cham", "Chậm luân chuyển")]):
            khung, so = _the_so(tab, tieu_de)
            khung.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(0, 10))
            self.the_kho[khoa] = so
        cot = ("ma_sp", "ten_sp", "danh_muc", "ton_kho", "ton_toi_thieu", "gia_von",
               "gia_tri_ton", "ban_gan_nhat", "ghi_chu")
        khung, self.bang_tk = _tao_bang(
            tab, cot,
            {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "danh_muc": "Loại", "ton_kho": "Tồn",
             "ton_toi_thieu": "Tối thiểu", "gia_von": "Giá vốn", "gia_tri_ton": "Giá trị tồn",
             "ban_gan_nhat": "Bán gần nhất", "ghi_chu": "Ghi chú"},
            {"ma_sp": 70, "ten_sp": 160, "danh_muc": 115, "ton_kho": 50, "ton_toi_thieu": 85,
             "gia_von": 80, "gia_tri_ton": 95, "ban_gan_nhat": 105, "ghi_chu": 125},
            {"ton_kho", "ton_toi_thieu", "gia_von", "gia_tri_ton"})
        khung.grid(row=1, column=0, columnspan=3, sticky="nsew")

    # ---------- bộ lọc ----------
    def _ap_dung_nhanh(self, tu_xem=True):
        hom_nay, chon = date.today(), self.var_nhanh.get()
        if chon == "7 ngày qua":
            tu, den = hom_nay - timedelta(days=6), hom_nay
        elif chon == "Tháng này":
            tu, den = hom_nay.replace(day=1), hom_nay
        elif chon == "Tháng trước":
            den = hom_nay.replace(day=1) - timedelta(days=1)
            tu = den.replace(day=1)
        elif chon == "Năm nay":
            tu, den = hom_nay.replace(month=1, day=1), hom_nay
        elif chon == "Tùy chọn":
            return
        else:
            tu, den = hom_nay - timedelta(days=29), hom_nay
        self.var_tu.set(tu.strftime("%d/%m/%Y"))
        self.var_den.set(den.strftime("%d/%m/%Y"))
        if tu_xem:
            self._xem()

    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: tính lại báo cáo, GIỮ NGUYÊN bộ lọc đang chọn."""
        self._xem()

    # ---------- nạp dữ liệu ----------
    def _goi(self, ham, *args, **kwargs):
        return goi_controller(self, ham, *args, **kwargs)

    def _xem(self):
        tu, den = self.var_tu.get(), self.var_den.get()
        kieu = KIEU_HIEN_THI[self.var_kieu.get()]
        kq = self._goi(BaoCaoController.doanh_thu, kieu, tu, den)
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self.lbl_thong_bao.config(text=thong_diep)
            return
        self.lbl_thong_bao.config(text="")
        self._ve_doanh_thu(du_lieu)

        kq = self._goi(BaoCaoController.theo_danh_muc, tu, den)
        if kq and kq[0]:
            self._ve_danh_muc(kq[2])
        kq = self._goi(BaoCaoController.theo_san_pham, tu, den, 10)
        if kq and kq[0]:
            self._ve_san_pham(kq[2])
        kq = self._goi(BaoCaoController.ton_kho)
        if kq and kq[0]:
            self._ve_ton_kho(kq[2])

    # ---------- vẽ từng tab ----------
    def _ve_doanh_thu(self, dl):
        kieu, dong, tong = dl["kieu"], dl["dong"], dl["tong"]
        for khoa, nhan in self.the.items():
            gia_tri = tong[khoa]
            nhan.config(text=str(gia_tri) if khoa == "so_hoa_don" else dinh_dang_tien(gia_tri),
                        foreground=MAU["nguy_hiem"] if khoa in ("thuan", "loi_nhuan") and gia_tri < 0
                        else MAU["chu"])

        self.bang_dt.delete(*self.bang_dt.get_children())
        for d in reversed(dong):                     # kỳ mới nhất lên trên
            self.bang_dt.insert("", "end", tags=("am",) if d["thuan"] < 0 else (), values=(
                _nhan_ky(d["ky"], kieu), dinh_dang_so(d["ban"]), dinh_dang_so(d["hoan"]),
                dinh_dang_so(d["thuan"]), dinh_dang_so(d["loi_nhuan"])))
        to_mau_xen_ke(self.bang_dt)

        def ve(ax):
            x = list(range(len(dong)))
            thuan = [d["thuan"] for d in dong]
            ax.bar(x, thuan, width=0.7,
                   color=[MAU["chinh"] if v >= 0 else MAU["nguy_hiem"] for v in thuan],
                   label="Doanh thu thuần")
            ax.plot(x, [d["loi_nhuan"] for d in dong], color=MAU["thanh_cong"], linewidth=1.8,
                    marker="o" if len(dong) <= 31 else None, markersize=3.5, label="Lợi nhuận gộp")
            ax.axhline(0, color=MAU["chu_phu"], linewidth=0.8)
            buoc = max(1, len(dong) // 8)
            ax.set_xticks(x[::buoc])
            ax.set_xticklabels([_nhan_ky(d["ky"], kieu, ngan=True) for d in dong][::buoc])
            BieuDo.lam_dep(ax)
            ax.legend(fontsize=8, frameon=False, loc="upper left")
        self.bd_doanh_thu.ve(ve)

    def _ve_danh_muc(self, dl):
        self.bang_dm.delete(*self.bang_dm.get_children())
        for d in dl["dong"]:
            self.bang_dm.insert("", "end", tags=("am",) if d["thuan"] < 0 else (), values=(
                d["ten"], dinh_dang_so(d["thuan"]), f"{d['ty_trong']:.1f}%".replace(".", ","),
                dinh_dang_so(d["loi_nhuan"])))
        to_mau_xen_ke(self.bang_dm)

        co_so = [d for d in dl["dong"] if d["thuan"] > 0]

        def ve(ax):
            if not co_so:
                ax.axis("off")
                ax.text(0.5, 0.5, "Chưa có doanh thu trong khoảng này", ha="center", va="center",
                        color=MAU["chu_phu"])
                return
            ax.pie([d["thuan"] for d in co_so], colors=BANG_MAU[:len(co_so)], startangle=90,
                   counterclock=False, autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
                   textprops={"color": "white", "fontsize": 9, "fontweight": "bold"},
                   wedgeprops={"edgecolor": "white", "linewidth": 1.5})
            ax.legend([d["ten"] for d in co_so], loc="center left", bbox_to_anchor=(0.95, 0.5),
                      fontsize=8, frameon=False)
            ax.set_title("Doanh thu thuần theo loại sản phẩm", fontsize=10, color=MAU["chu"])
        self.bd_danh_muc.ve(ve)

    def _ve_san_pham(self, dl):
        dong = dl["dong"]
        self.bang_sp.delete(*self.bang_sp.get_children())
        for d in dong:
            self.bang_sp.insert("", "end", tags=("am",) if d["thuan"] < 0 else (), values=(
                d["ma_sp"], d["ten_sp"], d["sl_thuan"], dinh_dang_so(d["thuan"]),
                dinh_dang_so(d["loi_nhuan"])))
        to_mau_xen_ke(self.bang_sp)

        def ve(ax):
            if not dong:
                ax.axis("off")
                ax.text(0.5, 0.5, "Chưa có doanh thu trong khoảng này", ha="center", va="center",
                        color=MAU["chu_phu"])
                return
            ten = [(d["ten_sp"][:22] + "…") if len(d["ten_sp"]) > 22 else d["ten_sp"] for d in dong]
            vi_tri = list(range(len(dong)))[::-1]
            ax.barh(vi_tri, [d["thuan"] for d in dong], height=0.65,
                    color=[MAU["chinh"] if d["thuan"] >= 0 else MAU["nguy_hiem"] for d in dong])
            ax.set_yticks(vi_tri)
            ax.set_yticklabels(ten)
            BieuDo.lam_dep(ax)
            ax.grid(axis="y", visible=False)
            ax.grid(axis="x", color="#E5E7EB", linewidth=0.8)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: dinh_dang_so(v)))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: ""))
            ax.set_yticklabels(ten)
            ax.set_title(f"Top {len(dong)} sản phẩm theo doanh thu thuần", fontsize=10, color=MAU["chu"])
        self.bd_san_pham.ve(ve)

    def _ve_ton_kho(self, dl):
        self.the_kho["gia_tri"].config(text=dinh_dang_tien(dl["tong_gia_tri"]))
        self.the_kho["sap_het"].config(text=f"{dl['so_sap_het']} sản phẩm",
                                       foreground=MAU["nguy_hiem"] if dl["so_sap_het"] else MAU["chu"])
        self.the_kho["cham"].config(text=f"{dl['so_cham']} sản phẩm",
                                    foreground=MAU["canh_bao"] if dl["so_cham"] else MAU["chu"])
        self.bang_tk.delete(*self.bang_tk.get_children())
        for d in dl["dong"]:
            if not d["dang_kinh_doanh"]:
                ghi_chu, tag = "Ngừng kinh doanh", ("ngung",)
            elif d["sap_het"]:
                ghi_chu, tag = "Sắp hết hàng", ("sap_het",)
            elif d["cham_luan_chuyen"]:
                ghi_chu, tag = (f"Chậm bán ({d['so_ngay_khong_ban']} ngày)" if d["so_ngay_khong_ban"] is not None
                                else "Chưa từng bán"), ("cham",)
            else:
                ghi_chu, tag = "", ()
            self.bang_tk.insert("", "end", tags=tag, values=(
                d["ma_sp"], d["ten_sp"], d["danh_muc"], d["ton_kho"], d["ton_toi_thieu"],
                dinh_dang_so(d["gia_von"]), dinh_dang_so(d["gia_tri_ton"]),
                dinh_dang_ngay(d["ban_gan_nhat"]) if d["ban_gan_nhat"] else "—", ghi_chu))
        to_mau_xen_ke(self.bang_tk)