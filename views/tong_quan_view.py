import tkinter as tk
from tkinter import ttk

from controllers.tong_quan_controller import TongQuanController
from utils.formatters import dinh_dang_gio, dinh_dang_so, dinh_dang_tien
from utils.session import ROLE_ADMIN, ROLE_THU_KHO
from views.bao_cao_view import BieuDo, _tao_bang
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke

THU = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
CHU_KY_LAM_MOI_MS = 60000


class TongQuanView(ttk.Frame):
    """Màn hình đầu tiên sau khi đăng nhập. Nội dung thay đổi theo vai trò (xem Controller)."""

    def __init__(self, master):
        super().__init__(master, padding=16)
        self._job = None
        self._da_dung = False          # các khung bên trái đã được dựng theo vai trò chưa
        self.bd = None
        self.bang_trai = None
        self._xay_khung()
        self.bind("<Destroy>", self._huy_cong_viec)

    # ---------- dựng giao diện ----------
    def _xay_khung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        dau = ttk.Frame(self)
        dau.grid(row=0, column=0, sticky="ew")
        dau.grid_columnconfigure(0, weight=1)
        self.lbl_chao = ttk.Label(dau, text="", style="TieuDe.TLabel")
        self.lbl_chao.grid(row=0, column=0, sticky="w")
        self.lbl_ngay = ttk.Label(dau, text="", style="Phu.TLabel")
        self.lbl_ngay.grid(row=1, column=0, sticky="w")
        ttk.Button(dau, text="Làm mới", command=self._tai).grid(row=0, column=1, rowspan=2)

        self.khung_the = ttk.Frame(self)
        self.khung_the.grid(row=1, column=0, sticky="ew", pady=(14, 14))

        self.khung_than = ttk.Frame(self)
        self.khung_than.grid(row=2, column=0, sticky="nsew")
        self.khung_than.grid_columnconfigure((0, 1), weight=1, uniform="cot")
        self.khung_than.grid_rowconfigure(0, weight=1)

        # Khung bên phải giống nhau ở mọi vai trò: sản phẩm sắp hết hàng
        phai = ttk.LabelFrame(self.khung_than, text="Sản phẩm sắp hết hàng", padding=10)
        phai.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        phai.grid_columnconfigure(0, weight=1)
        phai.grid_rowconfigure(0, weight=1)
        khung, self.bang_het = _tao_bang(
            phai, ("ma_sp", "ten_sp", "ton_kho", "ton_toi_thieu"),
            {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "ton_kho": "Tồn", "ton_toi_thieu": "Tối thiểu"},
            {"ma_sp": 80, "ten_sp": 190, "ton_kho": 50, "ton_toi_thieu": 80},
            {"ton_kho", "ton_toi_thieu"}, chieu_cao=8)
        khung.grid(row=0, column=0, sticky="nsew")
        self.lbl_du_hang = ttk.Label(phai, text="Tất cả sản phẩm đều đủ hàng.",
                                     foreground=MAU["thanh_cong"])
        self.lbl_con_lai = ttk.Label(phai, text="", style="Phu.TLabel")
        self.lbl_con_lai.grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _dung_khung_trai(self, vai_tro):
        """Dựng khung bên trái MỘT lần, tùy vai trò: biểu đồ (Admin) hoặc bảng hoạt động gần đây."""
        if vai_tro == ROLE_ADMIN:
            trai = ttk.LabelFrame(self.khung_than, text="Doanh thu thuần 7 ngày qua", padding=8)
            trai.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            trai.grid_columnconfigure(0, weight=1)
            trai.grid_rowconfigure(0, weight=1)
            self.bd = BieuDo(trai, rong=4.2, cao=3.2)
            self.bd.grid(row=0, column=0, sticky="nsew")
        else:
            if vai_tro == ROLE_THU_KHO:
                tieu_de, cot = "Phiếu nhập gần đây", ("ma", "gio", "ben", "tong")
                nhan = {"ma": "Mã phiếu", "gio": "Thời gian", "ben": "Nhà cung cấp", "tong": "Tổng tiền"}
                rong = {"ma": 130, "gio": 115, "ben": 110, "tong": 85}
            else:
                tieu_de, cot = "Hóa đơn gần đây của bạn", ("ma", "gio", "tong", "trang_thai")
                nhan = {"ma": "Mã hóa đơn", "gio": "Thời gian", "tong": "Tổng tiền", "trang_thai": "Trạng thái"}
                rong = {"ma": 130, "gio": 115, "tong": 85, "trang_thai": 100}
            trai = ttk.LabelFrame(self.khung_than, text=tieu_de, padding=10)
            trai.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            trai.grid_columnconfigure(0, weight=1)
            trai.grid_rowconfigure(0, weight=1)
            khung, self.bang_trai = _tao_bang(trai, cot, nhan, rong, {"tong"}, chieu_cao=8)
            khung.grid(row=0, column=0, sticky="nsew")
        self._da_dung = True

    # ---------- dữ liệu ----------
    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: tính lại số liệu, rồi tự làm mới mỗi 60 giây."""
        self._tai()

    def _hen_lam_moi(self):
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(CHU_KY_LAM_MOI_MS, self._tai)

    def _tai(self):
        kq = goi_controller(self, TongQuanController.tong_quan)
        if kq is None:
            return
        ok, thong_diep, dl = kq
        if not ok:
            return
        if not self._da_dung:
            self._dung_khung_trai(dl["vai_tro"])
        self.lbl_chao.config(text=f"Xin chào, {dl['ho_ten']}")
        self.lbl_ngay.config(text=f"{THU[dl['ngay'].weekday()]}, {dl['ngay']:%d/%m/%Y}")
        self._ve_the(dl["the"])
        self._ve_sap_het(dl["sap_het"])
        if dl["bieu_do"] is not None:
            self._ve_bieu_do(dl["bieu_do"])
        if dl["gan_day"] is not None:
            self._ve_gan_day(dl["gan_day"])
        self._hen_lam_moi()

    def _ve_the(self, cac_the):
        for w in self.khung_the.winfo_children():
            w.destroy()
        self.khung_the.grid_columnconfigure(tuple(range(len(cac_the))), weight=1, uniform="the")
        for i, t in enumerate(cac_the):
            khung = ttk.Frame(self.khung_the, style="The.TFrame", padding=(14, 10))
            khung.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            ttk.Label(khung, text=t["nhan"], style="The.TLabel").pack(anchor="w")
            if t["kieu"] == "tien":
                chu = dinh_dang_tien(t["gia_tri"])
            elif t["kieu"] == "san_pham":
                chu = f"{t['gia_tri']} sản phẩm"
            else:
                chu = str(t["gia_tri"])
            mau = MAU["chu"]
            if t["kieu"] == "tien" and t["gia_tri"] < 0:
                mau = MAU["nguy_hiem"]
            elif t["canh_bao"] == "do":
                mau = MAU["nguy_hiem"]
            elif t["canh_bao"] == "cam":
                mau = MAU["canh_bao"]
            ttk.Label(khung, text=chu, style="TheSo.TLabel", foreground=mau).pack(anchor="w")

    def _ve_sap_het(self, sap_het):
        self.bang_het.delete(*self.bang_het.get_children())
        for r in sap_het["dong"]:
            self.bang_het.insert("", "end", tags=("sap_het",) if r["ton_kho"] <= 0 else ("cham",),
                                 values=(r["ma_sp"], r["ten_sp"], r["ton_kho"], r["ton_toi_thieu"]))
        to_mau_xen_ke(self.bang_het)
        if sap_het["tong"] == 0:
            self.lbl_du_hang.grid(row=1, column=0, sticky="w", pady=(6, 0))
            self.lbl_con_lai.config(text="")
        else:
            self.lbl_du_hang.grid_remove()
            con_lai = sap_het["tong"] - len(sap_het["dong"])
            self.lbl_con_lai.config(
                text=f"và {con_lai} sản phẩm khác, xem đầy đủ ở màn hình Sản phẩm." if con_lai > 0
                else f"Tổng cộng {sap_het['tong']} sản phẩm.")

    def _ve_bieu_do(self, dong):
        def ve(ax):
            x = list(range(len(dong)))
            thuan = [d["thuan"] for d in dong]
            ax.bar(x, thuan, width=0.6,
                   color=[MAU["chinh"] if v >= 0 else MAU["nguy_hiem"] for v in thuan])
            ax.axhline(0, color=MAU["chu_phu"], linewidth=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels([f"{d['ky'][8:10]}/{d['ky'][5:7]}" for d in dong])
            BieuDo.lam_dep(ax)
        self.bd.ve(ve)

    def _ve_gan_day(self, gan_day):
        self.bang_trai.delete(*self.bang_trai.get_children())
        for r in gan_day["dong"]:
            if gan_day["loai"] == "phieu_nhap":
                gia_tri, tag = (r["ma"], dinh_dang_gio(r["thoi_gian"]), r["ben_thu_ba"],
                                dinh_dang_so(r["tong"])), ()
            else:
                huy = r["trang_thai"] == "da_huy"
                gia_tri = (r["ma"], dinh_dang_gio(r["thoi_gian"]), dinh_dang_so(r["tong"]),
                           "Đã hủy" if huy else "Hoàn thành")
                tag = ("ngung",) if huy else ()
            self.bang_trai.insert("", "end", values=gia_tri, tags=tag)
        to_mau_xen_ke(self.bang_trai)

    def _huy_cong_viec(self, event):
        if event.widget is self and self._job is not None:
            self.after_cancel(self._job)
            self._job = None