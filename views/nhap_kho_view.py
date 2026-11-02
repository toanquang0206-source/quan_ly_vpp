import tkinter as tk
from tkinter import ttk, messagebox

from controllers.nhap_kho_controller import NhapKhoController
from utils.formatters import dinh_dang_tien
from views.chung import goi_controller
from views.theme import MAU, to_mau_xen_ke

DO_TRE_GOI_Y_MS = 300
THOI_GIAN_THONG_BAO_MS = 6000
BO_QUA_PHIM = {"Return", "Up", "Down", "Escape", "Tab", "Shift_L", "Shift_R",
               "Control_L", "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Home", "End"}

COT = ("ma_sp", "ten_sp", "so_luong", "gia_nhap", "thanh_tien",
       "gv_hien_tai", "gv_sau", "ghi_chu")
TIEU_DE = {"ma_sp": "Mã SP", "ten_sp": "Tên sản phẩm", "so_luong": "Số lượng",
           "gia_nhap": "Giá nhập", "thanh_tien": "Thành tiền",
           "gv_hien_tai": "Giá vốn hiện tại", "gv_sau": "Giá vốn sau nhập",
           "ghi_chu": "Lưu ý"}
DO_RONG = {"ma_sp": 80, "ten_sp": 160, "so_luong": 75, "gia_nhap": 95, "thanh_tien": 105,
              "gv_hien_tai": 150, "gv_sau": 150, "ghi_chu": 170}
CAN_PHAI = {"so_luong", "gia_nhap", "thanh_tien", "gv_hien_tai", "gv_sau"}


class NhapKhoView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.var_ncc = tk.StringVar()
        self.var_ghi_chu = tk.StringVar()
        self.var_tim = tk.StringVar()
        self.var_so_luong = tk.StringVar()
        self.var_gia = tk.StringVar()
        self.ds_ncc = {}              # tên nhà cung cấp -> id
        self.dong_hang = []           # các dòng ĐANG SOẠN của phiếu (thứ tự người dùng thêm)
        self.sp_dang_chon = None      # sản phẩm vừa chọn từ gợi ý, chưa thêm vào phiếu
        self._ds_goi_y = []
        self._job_goi_y = None
        self._job_thong_bao = None
        self._xay_dung()
        self.bind("<Destroy>", self._huy_cong_viec)

    # ---------- dựng giao diện ----------
    def _xay_dung(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        tren = ttk.Frame(self)
        tren.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(tren, text="Nhà cung cấp *").pack(side="left")
        self.cbo_ncc = ttk.Combobox(tren, textvariable=self.var_ncc, state="readonly", width=32)
        self.cbo_ncc.pack(side="left", padx=(6, 16))
        ttk.Label(tren, text="Ghi chú").pack(side="left")
        ttk.Entry(tren, textvariable=self.var_ghi_chu, width=40).pack(side="left", padx=6)

        them = ttk.LabelFrame(self, text="Thêm mặt hàng vào phiếu", padding=8)
        them.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(them, text="Sản phẩm (gõ mã hoặc tên)").grid(row=0, column=0, sticky="w")
        self.entry_tim = ttk.Entry(them, textvariable=self.var_tim, width=44)
        self.entry_tim.grid(row=1, column=0, padx=(0, 10))
        ttk.Label(them, text="Số lượng").grid(row=0, column=1, sticky="w")
        self.entry_so_luong = ttk.Entry(them, textvariable=self.var_so_luong, width=10)
        self.entry_so_luong.grid(row=1, column=1, padx=(0, 10))
        ttk.Label(them, text="Giá nhập (đ)").grid(row=0, column=2, sticky="w")
        self.entry_gia = ttk.Entry(them, textvariable=self.var_gia, width=14)
        self.entry_gia.grid(row=1, column=2, padx=(0, 10))
        ttk.Button(them, text="Thêm vào phiếu", command=self._them_dong, style="Accent.TButton").grid(row=1, column=3)
        self.lbl_thong_tin_sp = ttk.Label(them, text="", foreground="#555555")
        self.lbl_thong_tin_sp.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        self.tree = ttk.Treeview(self, columns=COT, show="headings", height=10)
        for cot in COT:
            self.tree.heading(cot, text=TIEU_DE[cot], anchor="e" if cot in CAN_PHAI else "w")
            self.tree.column(cot, width=DO_RONG[cot], anchor="e" if cot in CAN_PHAI else "w")
        self.tree.tag_configure("bat_thuong", foreground="#c0392b")
        self.tree.tag_configure("luu_y", foreground="#b9770e")
        self.tree.grid(row=2, column=0, sticky="nsew")
        thanh_cuon = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        thanh_cuon.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=thanh_cuon.set)
        self.tree.bind("<Button-1>", lambda e: self._an_goi_y(), add="+")

        duoi = ttk.Frame(self)
        duoi.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(duoi, text="Xóa dòng đã chọn", command=self._xoa_dong).pack(side="left")
        ttk.Button(duoi, text="Xóa hết", command=self._xoa_het, style="Danger.TButton").pack(side="left", padx=6)
        ttk.Button(duoi, text="Lưu phiếu nhập", command=self._luu, style="Accent.TButton").pack(side="right")
        self.lbl_tong = ttk.Label(duoi, text="Tổng tiền: 0 đ", font=("Segoe UI", 11, "bold"))
        self.lbl_tong.pack(side="right", padx=16)

        self.lbl_thong_bao = ttk.Label(self, text="")
        self.lbl_thong_bao.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.lb_goi_y = tk.Listbox(self, height=6, activestyle="dotbox")
        self.lb_goi_y.bind("<ButtonRelease-1>", self._chon_goi_y)
        self.lb_goi_y.bind("<Return>", self._chon_goi_y)
        self.lb_goi_y.bind("<Escape>", lambda e: self._an_goi_y())

        self.entry_tim.bind("<KeyRelease>", self._khi_go_phim)
        self.entry_tim.bind("<Return>", self._enter_o_tim)
        self.entry_tim.bind("<Down>", self._xuong_goi_y)
        self.entry_tim.bind("<Escape>", lambda e: self._an_goi_y())
        self.entry_so_luong.bind("<Return>", lambda e: self.entry_gia.focus_set())
        self.entry_gia.bind("<Return>", lambda e: self._them_dong())

    def _goi(self, ham, *args, **kwargs):
        return goi_controller(self, ham, *args, **kwargs)

    def _bao(self, thong_diep, loi=False):
        self.lbl_thong_bao.config(text=thong_diep,
                                  foreground="#c0392b" if loi else "#1e8449")
        if self._job_thong_bao is not None:
            self.after_cancel(self._job_thong_bao)
        self._job_thong_bao = self.after(
            THOI_GIAN_THONG_BAO_MS, lambda: self.lbl_thong_bao.config(text=""))

    # ---------- dữ liệu ----------
    def lam_moi(self):
        """Nạp lại danh sách NCC. Các dòng ĐANG SOẠN được giữ nguyên, chỉ tính lại giá vốn."""
        ds = self._goi(NhapKhoController.danh_sach_nha_cung_cap)
        if ds is None:
            return
        self.ds_ncc = {d["ten_ncc"]: d["id"] for d in ds}
        self.cbo_ncc["values"] = list(self.ds_ncc)
        if self.var_ncc.get() not in self.ds_ncc:
            self.var_ncc.set("")
        if self.dong_hang:
            self._tinh_lai()

    def _tinh_lai(self):
        kq = self._goi(NhapKhoController.xem_truoc, self.dong_hang)
        if kq is None:
            return False
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return False
        self._ve_lai_bang(du_lieu)
        return True

    def _ve_lai_bang(self, du_lieu):
        theo_id = {d["san_pham_id"]: d for d in du_lieu["dong"]}
        self.tree.delete(*self.tree.get_children())
        for dong in self.dong_hang:
            r = theo_id.get(dong["san_pham_id"])
            if r is None:
                continue
            luu_y, tag = [], ()
            if r["bat_thuong"]:
                luu_y.append(f"⚠ lệch {r['lech_phan_tram']:+d}% so với giá vốn")
                tag = ("bat_thuong",)
            if r["vuot_gia_ban"]:
                luu_y.append("giá vốn mới vượt giá bán")
                tag = tag or ("luu_y",)
            self.tree.insert("", "end", iid=str(r["san_pham_id"]), tags=tag, values=(
                r["ma_sp"], r["ten_sp"], r["so_luong"], dinh_dang_tien(r["gia_nhap"]),
                dinh_dang_tien(r["thanh_tien"]), dinh_dang_tien(r["gia_von_hien_tai"]),
                dinh_dang_tien(r["gia_von_sau"]), "; ".join(luu_y)))
        self.lbl_tong.config(text=f"Tổng tiền: {dinh_dang_tien(du_lieu['tong_tien'])}")

    # ---------- thêm / xóa dòng ----------
    def _them_dong(self):
        sp = self.sp_dang_chon
        if sp is None:
            self._bao("Hãy chọn sản phẩm từ danh sách gợi ý.", loi=True)
            return
        if any(d["san_pham_id"] == sp["id"] for d in self.dong_hang):
            self._bao(f"{sp['ma_sp']} đã có trong phiếu. Hãy xóa dòng cũ nếu muốn nhập lại.", loi=True)
            return
        dong_moi = {"san_pham_id": sp["id"], "so_luong": self.var_so_luong.get(),
                    "gia_nhap": self.var_gia.get()}
        kq = self._goi(NhapKhoController.xem_truoc, self.dong_hang + [dong_moi])
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)     # KHÔNG xóa các ô đang gõ: người dùng chỉ sửa chỗ sai
            return
        self.dong_hang.append(dong_moi)
        self._ve_lai_bang(du_lieu)
        self.sp_dang_chon = None                # chuẩn bị nhập dòng kế tiếp
        for v in (self.var_tim, self.var_so_luong, self.var_gia):
            v.set("")
        self.lbl_thong_tin_sp.config(text="")
        self.entry_tim.focus_set()

    def _xoa_dong(self):
        chon = self.tree.selection()
        if not chon:
            return
        sp_id = int(chon[0])
        self.dong_hang = [d for d in self.dong_hang if d["san_pham_id"] != sp_id]
        self._lam_trong_hoac_tinh_lai()

    def _xoa_het(self):
        if self.dong_hang and not messagebox.askyesno(
                "Xóa hết", "Xóa toàn bộ các dòng đang soạn trong phiếu?", parent=self):
            return
        self.dong_hang = []
        self._lam_trong_hoac_tinh_lai()

    def _lam_trong_hoac_tinh_lai(self):
        if self.dong_hang:
            self._tinh_lai()
        else:
            self._ve_lai_bang({"dong": [], "tong_tien": 0})

    # ---------- lưu phiếu ----------
    def _luu(self):
        if not self.dong_hang:
            self._bao("Phiếu chưa có mặt hàng nào.", loi=True)
            return
        kq = self._goi(NhapKhoController.xem_truoc, self.dong_hang)
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)
            return
        self._ve_lai_bang(du_lieu)

        bat_thuong = [d for d in du_lieu["dong"] if d["bat_thuong"]]
        if bat_thuong:
            ds = "\n".join(
                f"• {d['ma_sp']}: nhập {dinh_dang_tien(d['gia_nhap'])}, giá vốn hiện tại "
                f"{dinh_dang_tien(d['gia_von_hien_tai'])} ({d['lech_phan_tram']:+d}%)"
                for d in bat_thuong)
            if not messagebox.askyesno(
                    "Giá nhập bất thường",
                    f"Có {len(bat_thuong)} dòng lệch hơn {du_lieu['nguong_lech']}% so với giá vốn "
                    f"hiện tại:\n\n{ds}\n\nBạn đã đối chiếu hóa đơn của nhà cung cấp và vẫn muốn lưu?",
                    parent=self, icon="warning"):
                return

        kq = self._goi(NhapKhoController.tao_phieu_nhap, self.ds_ncc.get(self.var_ncc.get()),
                       self.dong_hang, self.var_ghi_chu.get())
        if kq is None:
            return
        ok, thong_diep, du_lieu = kq
        if not ok:
            self._bao(thong_diep, loi=True)     # giữ nguyên các dòng đã soạn
            return

        self.dong_hang = []
        self._ve_lai_bang({"dong": [], "tong_tien": 0})
        self.var_ghi_chu.set("")
        self._bao(f"{thong_diep} Tổng tiền {dinh_dang_tien(du_lieu['tong_tien'])}.")
        if du_lieu["canh_bao"]:
            ds = "\n".join(f"• {c['ma_sp']} - {c['ten_sp']}: giá vốn mới {dinh_dang_tien(c['gia_von'])}"
                           f" cao hơn giá bán {dinh_dang_tien(c['gia_ban'])}"
                           for c in du_lieu["canh_bao"])
            messagebox.showwarning("Kiểm tra lại giá bán",
                                   f"Các sản phẩm sau đang có giá bán thấp hơn giá vốn:\n\n{ds}",
                                   parent=self)

    # ---------- gợi ý sản phẩm (debounce) ----------
    def _khi_go_phim(self, event):
        if event.keysym in BO_QUA_PHIM:
            return
        self.sp_dang_chon = None                # đã gõ lại thì phải chọn lại từ gợi ý
        self.lbl_thong_tin_sp.config(text="")
        if self._job_goi_y is not None:
            self.after_cancel(self._job_goi_y)
        self._job_goi_y = self.after(DO_TRE_GOI_Y_MS, self._cap_nhat_goi_y)

    def _cap_nhat_goi_y(self):
        self._job_goi_y = None
        ds = self._goi(NhapKhoController.goi_y_san_pham, self.var_tim.get()) or []
        if not ds:
            self._an_goi_y()
            return
        self._ds_goi_y = ds
        self.lb_goi_y.delete(0, "end")
        for sp in ds:
            self.lb_goi_y.insert("end", f"{sp['ma_sp']}  —  {sp['ten_sp']}   (tồn {sp['ton_kho']})")
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

    def _enter_o_tim(self, event):
        if self.lb_goi_y.winfo_ismapped() and self._ds_goi_y:
            self._chon_theo_vi_tri(0)            # Enter = chọn gợi ý đầu tiên (nhập nhanh)
        elif self.sp_dang_chon is not None:
            self.entry_so_luong.focus_set()

    def _chon_goi_y(self, event=None):
        chon = self.lb_goi_y.curselection()
        if chon:
            self._chon_theo_vi_tri(chon[0])

    def _chon_theo_vi_tri(self, i):
        sp = self._ds_goi_y[i]
        self.sp_dang_chon = sp
        self.var_tim.set(f"{sp['ma_sp']} - {sp['ten_sp']}")
        self._an_goi_y()
        self.lbl_thong_tin_sp.config(
            text=f"Tồn hiện tại: {sp['ton_kho']}   |   Giá vốn hiện tại: "
                 f"{dinh_dang_tien(sp['gia_von'])}   (chỉ để tham khảo, hãy nhập giá ghi "
                 f"trên hóa đơn của nhà cung cấp)")
        self.entry_so_luong.focus_set()

    def _huy_cong_viec(self, event):
        if event.widget is not self:
            return
        for ten in ("_job_goi_y", "_job_thong_bao"):
            job = getattr(self, ten)
            if job is not None:
                self.after_cancel(job)
                setattr(self, ten, None)