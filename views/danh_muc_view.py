import tkinter as tk
from tkinter import ttk, messagebox

from controllers.danh_muc_controller import (DanhMucController, DonViTinhController,
                                             NhaCungCapController)
from views.chung import goi_controller
from views.danh_muc_form import FormThuocTinh
from views.theme import MAU, to_mau_xen_ke

THOI_GIAN_THONG_BAO_MS = 6000


class TabQuanLy(ttk.Frame):
    """
    Một bảng quản lý dùng chung: liệt kê, thêm, sửa và một thao tác cuối (xóa hoặc đổi trạng thái).
    Mỗi tab chỉ khác nhau ở phần cấu hình truyền vào.
      cot:        [(khóa, tiêu đề, độ rộng, căn)]
      truong:     các ô nhập của hộp thoại thêm/sửa
      tai/them/sua/xoa: các hàm Controller tương ứng
      dinh_dang:  hàm dòng dữ liệu -> tuple giá trị hiển thị (đúng thứ tự cột)
      nut_trang_thai: (hàm nhãn nút theo dòng, hàm thực hiện), dùng cho nhà cung cấp
    """

    def __init__(self, master, *, doi_tuong, cot, truong, tai, them, sua, dinh_dang,
                 xoa=None, nut_trang_thai=None, gan_tag=None, ghi_chu=""):
        super().__init__(master, padding=10)
        self.doi_tuong, self.truong, self.ghi_chu = doi_tuong, truong, ghi_chu
        self.tai, self.them, self.sua, self.xoa = tai, them, sua, xoa
        self.nut_trang_thai, self.dinh_dang, self.gan_tag = nut_trang_thai, dinh_dang, gan_tag
        self._ds = {}
        self._job_thong_bao = None
        self._xay_dung(cot)
        self.bind("<Destroy>", self._huy_cong_viec)

    def _xay_dung(self, cot):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(self, columns=[c[0] for c in cot], show="headings",
                                 height=10, selectmode="browse")
        for khoa, tieu_de, rong, can in cot:
            self.tree.heading(khoa, text=tieu_de, anchor=can)
            self.tree.column(khoa, width=rong, anchor=can)
        self.tree.tag_configure("ngung", foreground="#9CA3AF")
        self.tree.grid(row=0, column=0, sticky="nsew")
        cuon = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        cuon.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=cuon.set)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._cap_nhat_nut())
        self.tree.bind("<Double-1>", lambda e: self._sua() if self.tree.identify_row(e.y) else None)

        duoi = ttk.Frame(self)
        duoi.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(duoi, text=f"Thêm {self.doi_tuong}", command=self._them,
                   style="Accent.TButton").pack(side="left")
        self.btn_sua = ttk.Button(duoi, text="Sửa...", command=self._sua, state="disabled")
        self.btn_sua.pack(side="left", padx=(8, 0))
        self.btn_xoa = self.btn_trang_thai = None
        if self.xoa:
            self.btn_xoa = ttk.Button(duoi, text="Xóa", command=self._xoa, state="disabled",
                                      style="Danger.TButton")
            self.btn_xoa.pack(side="left", padx=(8, 0))
        if self.nut_trang_thai:
            self.btn_trang_thai = ttk.Button(duoi, text="Ngừng hợp tác", command=self._doi_trang_thai,
                                             state="disabled")
            self.btn_trang_thai.pack(side="left", padx=(8, 0))

        self.lbl_thong_bao = ttk.Label(self, text="")
        self.lbl_thong_bao.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _bao(self, thong_diep, loi=False):
        self.lbl_thong_bao.config(text=thong_diep,
                                  foreground=MAU["nguy_hiem"] if loi else MAU["thanh_cong"])
        if self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
        self._job_thong_bao = self.after(
            THOI_GIAN_THONG_BAO_MS, lambda: self.lbl_thong_bao.config(text=""))

    # ---------- dữ liệu ----------
    def nap_lai(self):
        """Nạp lại danh sách, GIỮ NGUYÊN dòng đang chọn."""
        kq = goi_controller(self, self.tai)
        if kq is None:
            return
        ok, thong_diep, dong = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return
        chon_truoc = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        self._ds = {}
        for r in dong:
            iid = str(r["id"])
            self._ds[iid] = r
            self.tree.insert("", "end", iid=iid, values=self.dinh_dang(r),
                             tags=self.gan_tag(r) if self.gan_tag else ())
        to_mau_xen_ke(self.tree)
        if chon_truoc and self.tree.exists(chon_truoc[0]):
            self.tree.selection_set(chon_truoc[0])
        self._cap_nhat_nut()

    def _dong_chon(self):
        chon = self.tree.selection()
        return self._ds.get(chon[0]) if chon else None

    def _cap_nhat_nut(self):
        r = self._dong_chon()
        trang_thai = "normal" if r else "disabled"
        self.btn_sua.config(state=trang_thai)
        if self.btn_xoa:
            self.btn_xoa.config(state=trang_thai)
        if self.btn_trang_thai:
            self.btn_trang_thai.config(state=trang_thai)
            if r:
                self.btn_trang_thai.config(text=self.nut_trang_thai[0](r))

    # ---------- hành động ----------
    def _sau_khi_luu(self, thong_diep):
        self.nap_lai()
        self._bao(thong_diep)

    def _them(self):
        FormThuocTinh(self, f"Thêm {self.doi_tuong}", self.truong, {},
                      lambda d: self.them(**d), self._sau_khi_luu, self.ghi_chu)

    def _sua(self):
        r = self._dong_chon()
        if r is None:
            return
        FormThuocTinh(self, f"Sửa {self.doi_tuong}", self.truong, r,
                      lambda d: self.sua(r["id"], **d), self._sau_khi_luu, self.ghi_chu)

    def _xoa(self):
        r = self._dong_chon()
        if r is None or not messagebox.askyesno(
                "Xác nhận xóa", f"Xóa {self.doi_tuong} '{r['ten']}'?", parent=self, icon="warning"):
            return
        kq = goi_controller(self, self.xoa, r["id"])
        if kq is None:
            return
        ok, thong_diep, _ = kq
        self.nap_lai()
        self._bao(thong_diep, loi=not ok)

    def _doi_trang_thai(self):
        r = self._dong_chon()
        if r is None:
            return
        kq = goi_controller(self, self.nut_trang_thai[1], r["id"], r)
        if kq is None:
            return
        ok, thong_diep, _ = kq
        self.nap_lai()
        self._bao(thong_diep, loi=not ok)

    def _huy_cong_viec(self, event):
        if event.widget is self and self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
            self._job_thong_bao = None


class DanhMucView(ttk.Frame):
    """Quản lý loại sản phẩm, đơn vị tính, nhà cung cấp. Admin và Thủ kho dùng được."""

    def __init__(self, master):
        super().__init__(master, padding=12)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.nb = ttk.Notebook(self)
        self.nb.grid(row=0, column=0, sticky="nsew")

        self.tab_danh_muc = TabQuanLy(
            self.nb, doi_tuong="loại sản phẩm",
            cot=[("ten", "Tên loại", 260, "w"), ("mo_ta", "Mô tả", 340, "w"),
                 ("so_san_pham", "Số sản phẩm", 110, "e")],
            truong=[{"khoa": "ten", "nhan": "Tên loại sản phẩm *", "rong": 42},
                    {"khoa": "mo_ta", "nhan": "Mô tả", "rong": 42}],
            tai=DanhMucController.danh_sach, them=DanhMucController.them,
            sua=DanhMucController.sua, xoa=DanhMucController.xoa,
            dinh_dang=lambda r: (r["ten"], r["mo_ta"], r["so_san_pham"]),
            ghi_chu="Chỉ xóa được loại không còn sản phẩm nào.")

        self.tab_don_vi = TabQuanLy(
            self.nb, doi_tuong="đơn vị tính",
            cot=[("ten", "Tên đơn vị", 300, "w"), ("so_san_pham", "Số sản phẩm đang dùng", 190, "e")],
            truong=[{"khoa": "ten", "nhan": "Tên đơn vị tính *", "rong": 30}],
            tai=DonViTinhController.danh_sach, them=DonViTinhController.them,
            sua=DonViTinhController.sua, xoa=DonViTinhController.xoa,
            dinh_dang=lambda r: (r["ten"], r["so_san_pham"]),
            ghi_chu="Ví dụ: cái, cây, quyển, hộp, ram. Chỉ xóa được đơn vị không còn sản phẩm nào dùng.")

        self.tab_ncc = TabQuanLy(
            self.nb, doi_tuong="nhà cung cấp",
            cot=[("ten", "Tên nhà cung cấp", 190, "w"), ("sdt", "Điện thoại", 110, "w"),
                 ("email", "Email", 160, "w"), ("dia_chi", "Địa chỉ", 170, "w"),
                 ("trang_thai", "Trạng thái", 100, "w"), ("so_phieu", "Số phiếu nhập", 100, "e")],
            truong=[{"khoa": "ten", "nhan": "Tên nhà cung cấp *", "rong": 42},
                    {"khoa": "so_dien_thoai", "nhan": "Số điện thoại", "rong": 42},
                    {"khoa": "email", "nhan": "Email", "rong": 42},
                    {"khoa": "dia_chi", "nhan": "Địa chỉ", "rong": 42}],
            tai=NhaCungCapController.danh_sach, them=NhaCungCapController.them,
            sua=NhaCungCapController.sua,
            nut_trang_thai=(
                lambda r: "Ngừng hợp tác" if r["trang_thai"] == "hop_tac" else "Hợp tác lại",
                lambda ncc_id, r: NhaCungCapController.doi_trang_thai(
                    ncc_id, "ngung" if r["trang_thai"] == "hop_tac" else "hop_tac")),
            dinh_dang=lambda r: (r["ten"], r["so_dien_thoai"], r["email"], r["dia_chi"],
                                 "Hợp tác" if r["trang_thai"] == "hop_tac" else "Ngừng hợp tác",
                                 r["so_phieu_nhap"]),
            gan_tag=lambda r: ("ngung",) if r["trang_thai"] == "ngung" else (),
            ghi_chu="Nhà cung cấp ngừng hợp tác sẽ không còn xuất hiện khi lập phiếu nhập kho. "
                    "Không xóa được vì đã có phiếu nhập tham chiếu.")

        self.nb.add(self.tab_danh_muc, text="Loại sản phẩm")
        self.nb.add(self.tab_don_vi, text="Đơn vị tính")
        self.nb.add(self.tab_ncc, text="Nhà cung cấp")

    def lam_moi(self):
        """Mỗi lần màn hình hiện lên: nạp lại cả ba bảng, GIỮ NGUYÊN tab và dòng đang chọn."""
        for tab in (self.tab_danh_muc, self.tab_don_vi, self.tab_ncc):
            tab.nap_lai()