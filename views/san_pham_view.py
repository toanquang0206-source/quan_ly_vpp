import tkinter as tk
from tkinter import ttk, messagebox

from controllers.san_pham_controller import SanPhamController
from utils.formatters import dinh_dang_tien
from utils.session import ROLE_ADMIN, ROLE_THU_KHO, Session
from views.chung import goi_controller
from views.san_pham_form import SanPhamForm
from views.theme import MAU, to_mau_xen_ke

SO_DONG = 20            # số dòng mỗi trang
DO_TRE_GOI_Y_MS = 300   # chờ người dùng ngừng gõ rồi mới gợi ý (debounce)
THOI_GIAN_THONG_BAO_MS = 6000
TAT_CA_DANH_MUC = "Tất cả danh mục"

TIEU_DE = {
    "ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "danh_muc": "Danh mục",
    "don_vi": "ĐVT", "gia_nhap": "Giá nhập", "gia_ban": "Giá bán",
    "ton_kho": "Tồn kho", "ton_toi_thieu": "Tồn tối thiểu",
}
# Cột nào bấm vào tiêu đề thì sắp xếp được -> khóa sắp xếp mà Model chấp nhận
SAP_XEP_THEO_COT = {"ma_sp": "ma", "ten_sp": "ten", "gia_ban": "gia_ban", "ton_kho": "ton_kho"}
CAN_PHAI = {"gia_nhap", "gia_ban", "ton_kho", "ton_toi_thieu"}
DO_RONG = {"ma_sp": 90, "ten_sp": 260, "danh_muc": 150, "don_vi": 60,
           "gia_nhap": 110, "gia_ban": 110, "ton_kho": 80, "ton_toi_thieu": 110}


class SanPhamView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_tim = tk.StringVar()
        self.var_danh_muc = tk.StringVar(value=TAT_CA_DANH_MUC)
        self.var_ca_ngung = tk.BooleanVar(value=False)
        self.ds_danh_muc = {TAT_CA_DANH_MUC: None}    # tên -> id
        self.ngung_ids = set()                        # iid các dòng đang ngừng kinh doanh
        self.trang, self.so_trang = 1, 1
        self.sap_xep, self.giam_dan = "ten", False
        self._job_goi_y = None
        self._job_thong_bao = None

        # Admin và Thủ kho: thấy giá nhập + có nút Thêm/Sửa/Ngừng kinh doanh
        self.quan_ly = Session.has_role(ROLE_ADMIN, ROLE_THU_KHO)
        self.co_gia_nhap = self.quan_ly
        self.cac_cot = [c for c in TIEU_DE if c != "gia_nhap" or self.co_gia_nhap]
        self.chk_ngung = self.btn_them = self.btn_sua = self.btn_trang_thai = None

        self._xay_dung_giao_dien()
        self.bind("<Destroy>", self._huy_cong_viec)
        # Không tự nạp dữ liệu ở đây: MainWindow.hien() sẽ gọi lam_moi() ngay sau khi tạo

    # ---------- dựng giao diện ----------
    def _xay_dung_giao_dien(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Hàng 0: ô tìm kiếm + lọc danh mục (+ ô tích hiện hàng ngừng kinh doanh)
        thanh_tim = ttk.Frame(self)
        thanh_tim.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(thanh_tim, text="Tìm:").pack(side="left")
        self.entry_tim = ttk.Entry(thanh_tim, textvariable=self.var_tim, width=30)
        self.entry_tim.pack(side="left", padx=6)
        ttk.Button(thanh_tim, text="Tìm", command=self._tim).pack(side="left")
        self.cbo_danh_muc = ttk.Combobox(
            thanh_tim, textvariable=self.var_danh_muc, state="readonly", width=22)
        self.cbo_danh_muc.pack(side="left", padx=12)
        self.cbo_danh_muc.bind("<<ComboboxSelected>>", lambda e: self._tim())
        if self.quan_ly:
            self.chk_ngung = ttk.Checkbutton(
                thanh_tim, text="Hiện cả sản phẩm ngừng kinh doanh",
                variable=self.var_ca_ngung, command=self._tim)
            self.chk_ngung.pack(side="left")

        # Hàng 1: bảng + thanh cuộn
        self.tree = ttk.Treeview(self, columns=self.cac_cot, show="headings", height=15)
        for cot in self.cac_cot:
            self.tree.column(cot, width=DO_RONG[cot],
                             anchor="e" if cot in CAN_PHAI else "w")
        self.tree.tag_configure("sap_het", foreground="#c0392b")   # dưới mức tồn tối thiểu
        self.tree.tag_configure("ngung", foreground="#9CA3AF")     # đã ngừng kinh doanh
        self.tree.grid(row=1, column=0, sticky="nsew")
        thanh_cuon = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        thanh_cuon.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=thanh_cuon.set)
        self.tree.bind("<Button-1>", lambda e: self._an_goi_y(), add="+")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._cap_nhat_nut())
        if self.quan_ly:
            self.tree.bind("<Double-1>", self._khi_nhan_doi)

        # Hàng 2: phân trang (trái) + các nút thao tác (phải)
        thanh_duoi = ttk.Frame(self)
        thanh_duoi.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.btn_truoc = ttk.Button(thanh_duoi, text="‹ Trước",
                                    command=lambda: self._chuyen_trang(-1))
        self.btn_truoc.pack(side="left")
        self.lbl_trang = ttk.Label(thanh_duoi, text="")
        self.lbl_trang.pack(side="left", padx=12)
        self.btn_sau = ttk.Button(thanh_duoi, text="Sau ›",
                                  command=lambda: self._chuyen_trang(1))
        self.btn_sau.pack(side="left")
        if self.quan_ly:
            # pack side="right": nút gắn trước nằm ngoài cùng bên phải
            self.btn_trang_thai = ttk.Button(thanh_duoi, text="Ngừng kinh doanh",
                                             command=self._doi_trang_thai, state="disabled")
            self.btn_trang_thai.pack(side="right")
            self.btn_sua = ttk.Button(thanh_duoi, text="Sửa",
                                      command=self._sua, state="disabled")
            self.btn_sua.pack(side="right", padx=6)
            self.btn_them = ttk.Button(thanh_duoi, text="Thêm", command=self._them, style="Accent.TButton")
            self.btn_them.pack(side="right")

        # Hàng 3: dòng thông báo kết quả thao tác
        self.lbl_thong_bao = ttk.Label(self, text="")
        self.lbl_thong_bao.grid(row=3, column=0, sticky="w", pady=(6, 0))

        # Danh sách gợi ý: nằm đè lên bảng, ngay dưới ô tìm kiếm
        self.lb_goi_y = tk.Listbox(self, height=6, activestyle="dotbox")
        self.lb_goi_y.bind("<ButtonRelease-1>", self._chon_goi_y)
        self.lb_goi_y.bind("<Return>", self._chon_goi_y)
        self.lb_goi_y.bind("<Escape>", lambda e: self._an_goi_y())

        self.entry_tim.bind("<KeyRelease>", self._khi_go_phim)
        self.entry_tim.bind("<Return>", lambda e: self._tim())
        self.entry_tim.bind("<Down>", self._xuong_goi_y)
        self.entry_tim.bind("<Escape>", lambda e: self._an_goi_y())

        self._cap_nhat_tieu_de()

    def _cap_nhat_tieu_de(self):
        """Đặt lại tiêu đề cột, có mũi tên ở cột đang sắp xếp."""
        for cot in self.cac_cot:
            text = TIEU_DE[cot]
            if SAP_XEP_THEO_COT.get(cot) == self.sap_xep:
                text += " ▼" if self.giam_dan else " ▲"
            lenh = (lambda c=cot: self._doi_sap_xep(c)) if cot in SAP_XEP_THEO_COT else ""
            self.tree.heading(cot, text=text, command=lenh,
                    anchor="e" if cot in CAN_PHAI else "w")

    def _cap_nhat_nut(self):
        """Bật/tắt nút Sửa, Ngừng kinh doanh theo dòng đang chọn."""
        if not self.quan_ly:
            return
        chon = self.tree.selection()
        trang_thai = "normal" if chon else "disabled"
        self.btn_sua.config(state=trang_thai)
        self.btn_trang_thai.config(state=trang_thai)
        dang_ngung = bool(chon) and chon[0] in self.ngung_ids
        self.btn_trang_thai.config(text="Kinh doanh lại" if dang_ngung else "Ngừng kinh doanh")

    def _bao(self, thong_diep, loi=False):
        self.lbl_thong_bao.config(text=thong_diep,
                                  foreground="#c0392b" if loi else "#1e8449")
        if self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
        self._job_thong_bao = self.after(
            THOI_GIAN_THONG_BAO_MS, lambda: self.lbl_thong_bao.config(text=""))

    def _goi(self, ham, *args, **kwargs):
        return goi_controller(self, ham, *args, **kwargs)

    # ---------- dữ liệu ----------
    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: nạp lại dữ liệu từ CSDL, GIỮ NGUYÊN bộ lọc/trang đang xem."""
        self._nap_danh_muc()
        self._tai_du_lieu()

    def _nap_danh_muc(self):
        ds = self._goi(SanPhamController.danh_sach_danh_muc)
        if ds is None:
            return
        self.ds_danh_muc = {TAT_CA_DANH_MUC: None}
        self.ds_danh_muc.update({d["ten_danh_muc"]: d["id"] for d in ds})
        self.cbo_danh_muc["values"] = list(self.ds_danh_muc)
        if self.var_danh_muc.get() not in self.ds_danh_muc:   # danh mục đã bị xóa/đổi tên
            self.var_danh_muc.set(TAT_CA_DANH_MUC)

    def _tai_du_lieu(self):
        kq = self._goi(
            SanPhamController.tim_kiem,
            tu_khoa=self.var_tim.get(),
            danh_muc_id=self.ds_danh_muc.get(self.var_danh_muc.get()),
            sap_xep=self.sap_xep, giam_dan=self.giam_dan,
            trang=self.trang, so_dong=SO_DONG,
            ca_ngung_kd=self.var_ca_ngung.get(),
        )
        if kq is None:
            return
        self.trang, self.so_trang = kq["trang"], kq["so_trang"]

        chon_truoc = self.tree.selection()          # nhớ dòng đang chọn để chọn lại sau khi nạp
        self.tree.delete(*self.tree.get_children())
        self.ngung_ids = set()
        for d in kq["dong"]:
            to_mau_xen_ke(self.tree)
            iid = str(d["id"])
            gia_tri = [d["ma_sp"], d["ten_sp"], d["ten_danh_muc"], d["don_vi"]]
            if self.co_gia_nhap:
                gia_tri.append(dinh_dang_tien(d["gia_nhap"]))      # định dạng ở VIEW
            gia_tri += [dinh_dang_tien(d["gia_ban"]), d["ton_kho"], d["ton_toi_thieu"]]
            if d["trang_thai"] == "ngung_kinh_doanh":
                tag = ("ngung",)
                self.ngung_ids.add(iid)
            elif d["ton_kho"] <= d["ton_toi_thieu"]:
                tag = ("sap_het",)
            else:
                tag = ()
            self.tree.insert("", "end", iid=iid, values=gia_tri, tags=tag)
        if chon_truoc and self.tree.exists(chon_truoc[0]):
            self.tree.selection_set(chon_truoc[0])

        self.lbl_trang.config(
            text=f"Trang {self.trang}/{self.so_trang}  —  {kq['tong']} sản phẩm")
        self.btn_truoc.config(state="normal" if self.trang > 1 else "disabled")
        self.btn_sau.config(state="normal" if self.trang < self.so_trang else "disabled")
        self._cap_nhat_tieu_de()
        self._cap_nhat_nut()

    # ---------- hành động của người dùng ----------
    def _tim(self):
        self._an_goi_y()
        self.trang = 1                      # tìm mới thì về trang đầu
        self._tai_du_lieu()

    def _chuyen_trang(self, huong):
        self.trang += huong
        self._tai_du_lieu()

    def _doi_sap_xep(self, cot):
        khoa = SAP_XEP_THEO_COT[cot]
        if self.sap_xep == khoa:
            self.giam_dan = not self.giam_dan
        else:
            self.sap_xep, self.giam_dan = khoa, False
        self.trang = 1
        self._tai_du_lieu()

    def _them(self):
        SanPhamForm(self, None, self._sau_khi_luu)

    def _sua(self):
        chon = self.tree.selection()
        if chon:
            SanPhamForm(self, int(chon[0]), self._sau_khi_luu)

    def _khi_nhan_doi(self, event):
        if self.tree.identify_row(event.y):          # nhấp đúp vào một dòng (không phải tiêu đề)
            self._sua()

    def _sau_khi_luu(self, thong_diep):
        self._tai_du_lieu()
        self._bao(thong_diep)

    def _doi_trang_thai(self):
        chon = self.tree.selection()
        if not chon:
            return
        san_pham_id = int(chon[0])
        if chon[0] in self.ngung_ids:
            kq = self._goi(SanPhamController.kinh_doanh_lai, san_pham_id)
        else:
            ten = self.tree.item(chon[0])["values"][1]
            if not messagebox.askyesno(
                    "Ngừng kinh doanh",
                    f"Ngừng kinh doanh '{ten}'?\n\nSản phẩm sẽ không còn xuất hiện khi "
                    f"bán hàng, nhưng số tồn trong kho vẫn được giữ.", parent=self):
                return
            kq = self._goi(SanPhamController.ngung_kinh_doanh, san_pham_id)
        if kq is None:
            return
        ok, thong_diep = kq
        self._tai_du_lieu()
        self._bao(thong_diep, loi=not ok)

    # ---------- gợi ý khi gõ (debounce) ----------
    def _khi_go_phim(self, event):
        if event.keysym in ("Return", "Up", "Down", "Escape", "Tab"):
            return
        if self._job_goi_y is not None:               # còn đang gõ -> hủy lần hẹn trước
            self.after_cancel(self._job_goi_y)
        self._job_goi_y = self.after(DO_TRE_GOI_Y_MS, self._cap_nhat_goi_y)

    def _cap_nhat_goi_y(self):
        self._job_goi_y = None
        ds = self._goi(SanPhamController.goi_y, self.var_tim.get()) or []
        if not ds:
            self._an_goi_y()
            return
        self.lb_goi_y.delete(0, "end")
        for ten in ds:
            self.lb_goi_y.insert("end", ten)
        self.lb_goi_y.place(in_=self.entry_tim, relx=0, rely=1.0, relwidth=1.0)
        self.lb_goi_y.lift()

    def _an_goi_y(self):
        self.lb_goi_y.place_forget()

    def _xuong_goi_y(self, event):
        if self.lb_goi_y.winfo_ismapped():
            self.lb_goi_y.focus_set()
            self.lb_goi_y.selection_clear(0, "end")
            self.lb_goi_y.selection_set(0)
            self.lb_goi_y.activate(0)
        return "break"

    def _chon_goi_y(self, event=None):
        chon = self.lb_goi_y.curselection()
        if not chon:
            return
        self.var_tim.set(self.lb_goi_y.get(chon[0]))
        self.entry_tim.focus_set()
        self._tim()

    def _huy_cong_viec(self, event):
        if event.widget is not self:
            return
        for ten in ("_job_goi_y", "_job_thong_bao"):
            job = getattr(self, ten)
            if job is not None:
                self.after_cancel(job)
                setattr(self, ten, None)