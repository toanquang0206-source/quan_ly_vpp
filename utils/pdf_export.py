"""
Xuất PDF: hóa đơn bán hàng, báo cáo doanh thu, báo cáo tồn kho.

Module này CHỈ nhận dữ liệu đã tính sẵn từ Controller rồi dàn trang, không truy cập CSDL.
Phông chữ được NHÚNG vào file PDF nên mở ở máy nào cũng đúng tiếng Việt.
"""
import io
import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.formatters import dinh_dang_gio, dinh_dang_ngay, dinh_dang_so, dinh_dang_tien

# ===== Thông tin cửa hàng in trên hóa đơn và báo cáo: SỬA CHO ĐÚNG CỬA HÀNG CỦA BẠN =====
TEN_CUA_HANG = "CỬA HÀNG VĂN PHÒNG PHẨM"
DIA_CHI_CUA_HANG = "Địa chỉ: 123 Đường ABC, Hà Nội"
DIEN_THOAI_CUA_HANG = "Điện thoại: 0900 000 000"

NHAN_PHUONG_THUC = {"tien_mat": "Tiền mặt", "chuyen_khoan": "Chuyển khoản", "the": "Thẻ"}
XANH = colors.HexColor("#2563EB")
DO = colors.HexColor("#DC2626")
CAM = colors.HexColor("#B45309")
XAM = colors.HexColor("#6B7280")
NEN_DAU = colors.HexColor("#E8EEF9")
NEN_XEN_KE = colors.HexColor("#F8FAFC")
VIEN = colors.HexColor("#CBD5E1")


# ---------------------------------------------------------------- phông chữ
def _tim_phong():
    """Tìm file phông hỗ trợ tiếng Việt. Ưu tiên DejaVu Sans để kết quả giống nhau trên mọi máy."""
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ung_vien = [(os.path.join(goc, "assets", "fonts", "DejaVuSans.ttf"),
                 os.path.join(goc, "assets", "fonts", "DejaVuSans-Bold.ttf"))]   # nếu bạn tự đặt vào dự án
    try:
        import matplotlib
        thu_muc = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")        # đi kèm matplotlib
        ung_vien.append((os.path.join(thu_muc, "DejaVuSans.ttf"),
                         os.path.join(thu_muc, "DejaVuSans-Bold.ttf")))
    except ImportError:
        pass
    phong_win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")    # phương án cuối
    ung_vien.append((os.path.join(phong_win, "arial.ttf"), os.path.join(phong_win, "arialbd.ttf")))
    for thuong, dam in ung_vien:
        if os.path.isfile(thuong) and os.path.isfile(dam):
            return thuong, dam
    raise FileNotFoundError(
        "Không tìm thấy phông chữ hỗ trợ tiếng Việt. Hãy chạy: pip install matplotlib")


_DA_DANG_KY = []


def _dang_ky_phong():
    if _DA_DANG_KY:
        return
    thuong, dam = _tim_phong()
    pdfmetrics.registerFont(TTFont("VN", thuong))        # TTFont tự NHÚNG phần chữ được dùng vào PDF
    pdfmetrics.registerFont(TTFont("VN-Bold", dam))
    pdfmetrics.registerFontFamily("VN", normal="VN", bold="VN-Bold", italic="VN", boldItalic="VN-Bold")
    _DA_DANG_KY.append(True)


# ---------------------------------------------------------------- tiện ích dàn trang
def _p(noi_dung, phong="VN", co=9, can=TA_LEFT, mau=colors.black):
    kieu = ParagraphStyle("p", fontName=phong, fontSize=co, leading=co * 1.35,
                          alignment=can, textColor=mau)
    return Paragraph(escape(str(noi_dung)), kieu)


def _bang(dong, rong, can_phai=(), co=8.5, mau_dong=None):
    """dong[0] là hàng tiêu đề. mau_dong(i) trả về màu chữ cho dòng dữ liệu thứ i (hoặc None)."""
    du_lieu = []
    for i, hang in enumerate(dong):
        cac_o = []
        for j, o in enumerate(hang):
            mau = colors.black
            if i > 0 and mau_dong:
                mau = mau_dong(i - 1) or colors.black
            cac_o.append(_p(o, "VN-Bold" if i == 0 else "VN", co,
                            TA_RIGHT if j in can_phai else TA_LEFT, mau))
        du_lieu.append(cac_o)
    bang = Table(du_lieu, colWidths=rong, repeatRows=1)
    bang.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NEN_DAU),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, NEN_XEN_KE]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, VIEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return bang


def _canvas_co_chan_trang(chan_trai):
    """Canvas vẽ chân trang 'Trang x/y' (cần biết tổng số trang nên vẽ sau cùng)."""
    class _Canvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._cac_trang = []

        def showPage(self):
            self._cac_trang.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            tong = len(self._cac_trang)
            for trang in self._cac_trang:
                self.__dict__.update(trang)
                rong = self._pagesize[0]
                self.setFont("VN", 8)
                self.setFillColor(XAM)
                self.drawString(15 * mm, 9 * mm, chan_trai)
                self.drawRightString(rong - 15 * mm, 9 * mm, f"Trang {self._pageNumber}/{tong}")
                super().showPage()
            super().save()
    return _Canvas


def _dau_bao_cao(tieu_de, phu_de):
    return [_p(TEN_CUA_HANG, "VN-Bold", 11, TA_CENTER, XANH),
            _p(f"{DIA_CHI_CUA_HANG}  ·  {DIEN_THOAI_CUA_HANG}", "VN", 8, TA_CENTER, XAM),
            Spacer(1, 8 * mm),
            _p(tieu_de, "VN-Bold", 15, TA_CENTER),
            _p(phu_de, "VN", 9, TA_CENTER, XAM),
            Spacer(1, 6 * mm)]


def _the_tom_tat(cac_the):
    """cac_the: [(tiêu đề, giá trị, màu)] -> một hàng thẻ số liệu."""
    tieu_de = [_p(t, "VN", 8, TA_LEFT, XAM) for t, _, _ in cac_the]
    gia_tri = [_p(v, "VN-Bold", 12, TA_LEFT, m) for _, v, m in cac_the]
    rong = [(180 * mm) / len(cac_the)] * len(cac_the)
    bang = Table([tieu_de, gia_tri], colWidths=rong)
    bang.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, VIEN), ("INNERGRID", (0, 0), (-1, -1), 0.5, VIEN),
        ("BACKGROUND", (0, 0), (-1, -1), NEN_XEN_KE),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    return bang


def _nhan_ky(ky, kieu):
    if kieu == "ngay":
        y, m, d = ky.split("-")
        return f"{d}/{m}/{y}"
    if kieu == "thang":
        y, m = ky.split("-")
        return f"{m}/{y}"
    return ky


def _mau_so(gia_tri):
    return DO if gia_tri < 0 else colors.black


def _chan_trai(nguoi_in):
    return f"In lúc {datetime.now():%d/%m/%Y %H:%M} bởi {nguoi_in}"


# ---------------------------------------------------------------- 1) HÓA ĐƠN
def xuat_hoa_don(duong_dan, chi_tiet):
    """chi_tiet: dữ liệu trả về từ HoaDonController.chi_tiet (không có giá vốn)."""
    _dang_ky_phong()
    hd, dong = chi_tiet["hoa_don"], chi_tiet["dong"]
    tai_lieu = SimpleDocTemplate(
        duong_dan, pagesize=A5, leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=16 * mm,
        title=f"Hóa đơn {hd['ma_hoa_don']}", author=TEN_CUA_HANG)

    pt = [_p(TEN_CUA_HANG, "VN-Bold", 13, TA_CENTER, XANH),
          _p(DIA_CHI_CUA_HANG, "VN", 8, TA_CENTER, XAM),
          _p(DIEN_THOAI_CUA_HANG, "VN", 8, TA_CENTER, XAM),
          Spacer(1, 5 * mm),
          _p("HÓA ĐƠN BÁN HÀNG", "VN-Bold", 13, TA_CENTER)]
    if hd["trang_thai"] == "da_huy":
        pt.append(_p("— ĐÃ HỦY —", "VN-Bold", 13, TA_CENTER, DO))
    pt.append(Spacer(1, 4 * mm))

    thong_tin = [
        ("Số hóa đơn:", hd["ma_hoa_don"]),
        ("Ngày lập:", dinh_dang_gio(hd["ngay_lap"])),
        ("Nhân viên:", hd["nhan_vien"]),
        ("Thanh toán:", NHAN_PHUONG_THUC.get(hd["phuong_thuc_thanh_toan"], "")),
    ]
    bang_tt = Table([[_p(a, "VN", 9, TA_LEFT, XAM), _p(b, "VN-Bold", 9)] for a, b in thong_tin],
                    colWidths=[28 * mm, 96 * mm])
    bang_tt.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    pt += [bang_tt, Spacer(1, 4 * mm)]

    hang = [["STT", "Tên sản phẩm", "SL", "Đơn giá", "Thành tiền"]]
    for i, d in enumerate(dong, start=1):
        hang.append([i, d["ten_sp"], d["so_luong"], dinh_dang_so(d["don_gia"]), dinh_dang_so(d["thanh_tien"])])
    pt.append(_bang(hang, [10 * mm, 50 * mm, 12 * mm, 24 * mm, 28 * mm], can_phai=(2, 3, 4), co=9))
    pt.append(Spacer(1, 3 * mm))

    tong = [["Tổng cộng:", dinh_dang_tien(hd["tong_thanh_toan"])]]
    if hd["da_hoan"]:
        tong.append(["Đã hoàn trả:", "-" + dinh_dang_tien(hd["da_hoan"])])
        tong.append(["Thực thu:", dinh_dang_tien(hd["tong_thanh_toan"] - hd["da_hoan"])])
    bang_tong = Table([[_p(a, "VN-Bold", 10, TA_RIGHT), _p(b, "VN-Bold", 10, TA_RIGHT)] for a, b in tong],
                      colWidths=[84 * mm, 40 * mm])
    bang_tong.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    pt.append(bang_tong)

    if hd["trang_thai"] != "da_huy":
        so_ngay = (chi_tiet["han_doi_tra"] - hd["ngay_lap"]).days
        pt += [Spacer(1, 8 * mm),
               _p("Cảm ơn quý khách!", "VN-Bold", 10, TA_CENTER),
               _p(f"Hàng được đổi trả trong {so_ngay} ngày kể từ ngày mua, kèm hóa đơn này.",
                  "VN", 8, TA_CENTER, XAM)]
    tai_lieu.build(pt)


# ---------------------------------------------------------------- 2) BÁO CÁO DOANH THU
def _anh_bieu_do(dong, kieu):
    """Vẽ biểu đồ doanh thu bằng matplotlib (không cần cửa sổ) rồi trả về bytes ảnh PNG."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter

    fig = Figure(figsize=(7.2, 3.0), dpi=200)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    x = list(range(len(dong)))
    thuan = [d["thuan"] for d in dong]
    ax.bar(x, thuan, width=0.7, color=["#2563EB" if v >= 0 else "#DC2626" for v in thuan],
           label="Doanh thu thuần")
    ax.plot(x, [d["loi_nhuan"] for d in dong], color="#15803D", linewidth=1.6,
            marker="o" if len(dong) <= 31 else None, markersize=3, label="Lợi nhuận gộp")
    ax.axhline(0, color="#6B7280", linewidth=0.8)
    buoc = max(1, len(dong) // 8)
    ax.set_xticks(x[::buoc])
    ax.set_xticklabels([_nhan_ky(d["ky"], kieu) for d in dong][::buoc], fontsize=7)
    ax.tick_params(labelsize=7, colors="#6B7280")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: dinh_dang_so(v)))
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.7)
    ax.set_axisbelow(True)
    for canh in ("top", "right"):
        ax.spines[canh].set_visible(False)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.tight_layout()
    bo_dem = io.BytesIO()
    fig.savefig(bo_dem, format="png")
    return bo_dem.getvalue()


def xuat_bao_cao_doanh_thu(duong_dan, doanh_thu, danh_muc, san_pham, nguoi_in):
    """Dữ liệu lấy từ BaoCaoController.doanh_thu / theo_danh_muc / theo_san_pham."""
    _dang_ky_phong()
    kieu, dong, tong = doanh_thu["kieu"], doanh_thu["dong"], doanh_thu["tong"]
    ten_kieu = {"ngay": "theo ngày", "thang": "theo tháng", "nam": "theo năm"}[kieu]
    tai_lieu = SimpleDocTemplate(duong_dan, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                                 topMargin=14 * mm, bottomMargin=16 * mm,
                                 title="Báo cáo doanh thu", author=TEN_CUA_HANG)
    pt = _dau_bao_cao(
        "BÁO CÁO DOANH THU",
        f"Từ {dinh_dang_ngay(doanh_thu['tu'])} đến {dinh_dang_ngay(doanh_thu['den'])}  ·  Hiển thị {ten_kieu}")
    pt.append(_the_tom_tat([
        ("Doanh thu thuần", dinh_dang_tien(tong["thuan"]), _mau_so(tong["thuan"])),
        ("Lợi nhuận gộp", dinh_dang_tien(tong["loi_nhuan"]), _mau_so(tong["loi_nhuan"])),
        ("Số hóa đơn đã lập", str(tong["so_hoa_don"]), colors.black),
        ("Hoàn trả và hủy", dinh_dang_tien(tong["hoan"]), colors.black)]))
    pt += [Spacer(1, 5 * mm),
           Image(io.BytesIO(_anh_bieu_do(dong, kieu)), width=180 * mm, height=180 * mm * 3.0 / 7.2),
           Spacer(1, 4 * mm),
           _p("Doanh thu thuần = tiền bán trong kỳ trừ tiền hoàn trả và hủy phát sinh trong kỳ. "
              "Lãi gộp = doanh thu thuần trừ giá vốn hàng bán.", "VN", 8, TA_LEFT, XAM),
           Spacer(1, 5 * mm), _p("Chi tiết theo kỳ", "VN-Bold", 11), Spacer(1, 2 * mm)]

    co_giao_dich = [d for d in dong if d["ban"] or d["hoan"]]      # bỏ qua các kỳ trống cho gọn
    if co_giao_dich:
        hang = [["Kỳ", "Bán", "Hoàn/hủy", "Thuần", "Lãi gộp"]]
        hang += [[_nhan_ky(d["ky"], kieu), dinh_dang_so(d["ban"]), dinh_dang_so(d["hoan"]),
                  dinh_dang_so(d["thuan"]), dinh_dang_so(d["loi_nhuan"])] for d in co_giao_dich]
        pt.append(_bang(hang, [40 * mm, 35 * mm, 35 * mm, 35 * mm, 35 * mm], can_phai=(1, 2, 3, 4),
                        mau_dong=lambda i: DO if co_giao_dich[i]["thuan"] < 0 else None))
        if len(co_giao_dich) < len(dong):
            pt += [Spacer(1, 2 * mm), _p("Chỉ liệt kê các kỳ có giao dịch.", "VN", 8, TA_LEFT, XAM)]
    else:
        pt.append(_p("Không có giao dịch nào trong khoảng thời gian này.", "VN", 9, TA_LEFT, XAM))

    pt += [Spacer(1, 7 * mm), _p("Theo loại sản phẩm", "VN-Bold", 11), Spacer(1, 2 * mm)]
    hang = [["Loại sản phẩm", "Doanh thu thuần", "Tỷ trọng", "Lãi gộp"]]
    hang += [[d["ten"], dinh_dang_so(d["thuan"]), f"{d['ty_trong']:.1f}%".replace(".", ","),
              dinh_dang_so(d["loi_nhuan"])] for d in danh_muc["dong"]]
    pt.append(_bang(hang, [70 * mm, 40 * mm, 30 * mm, 40 * mm], can_phai=(1, 2, 3),
                    mau_dong=lambda i: DO if danh_muc["dong"][i]["thuan"] < 0 else None))

    pt += [Spacer(1, 7 * mm),
           _p(f"Top {len(san_pham['dong'])} sản phẩm theo doanh thu thuần", "VN-Bold", 11), Spacer(1, 2 * mm)]
    hang = [["Mã SP", "Tên sản phẩm", "SL thuần", "Doanh thu thuần", "Lãi gộp"]]
    hang += [[d["ma_sp"], d["ten_sp"], d["sl_thuan"], dinh_dang_so(d["thuan"]),
              dinh_dang_so(d["loi_nhuan"])] for d in san_pham["dong"]]
    pt.append(_bang(hang, [28 * mm, 66 * mm, 24 * mm, 32 * mm, 30 * mm], can_phai=(2, 3, 4),
                    mau_dong=lambda i: DO if san_pham["dong"][i]["thuan"] < 0 else None))
    tai_lieu.build(pt, canvasmaker=_canvas_co_chan_trang(_chan_trai(nguoi_in)))


# ---------------------------------------------------------------- 3) BÁO CÁO TỒN KHO
def _ghi_chu_ton(d):
    if not d["dang_kinh_doanh"]:
        return "Ngừng kinh doanh", XAM
    if d["sap_het"]:
        return "Sắp hết hàng", DO
    if d["cham_luan_chuyen"]:
        return (f"Chậm bán ({d['so_ngay_khong_ban']} ngày)" if d["so_ngay_khong_ban"] is not None
                else "Chưa từng bán"), CAM
    return "", None


def xuat_bao_cao_ton_kho(duong_dan, ton_kho, nguoi_in):
    """Dữ liệu lấy từ BaoCaoController.ton_kho."""
    _dang_ky_phong()
    tai_lieu = SimpleDocTemplate(duong_dan, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                                 topMargin=14 * mm, bottomMargin=16 * mm,
                                 title="Báo cáo tồn kho", author=TEN_CUA_HANG)
    pt = _dau_bao_cao("BÁO CÁO TỒN KHO", f"Tại thời điểm {datetime.now():%d/%m/%Y %H:%M}")
    pt.append(_the_tom_tat([
        ("Giá trị tồn kho (theo giá vốn)", dinh_dang_tien(ton_kho["tong_gia_tri"]), colors.black),
        ("Sản phẩm sắp hết hàng", f"{ton_kho['so_sap_het']} sản phẩm", DO if ton_kho["so_sap_het"] else colors.black),
        (f"Chậm luân chuyển (≥ {ton_kho['so_ngay_cham']} ngày)", f"{ton_kho['so_cham']} sản phẩm",
         CAM if ton_kho["so_cham"] else colors.black)]))
    pt.append(Spacer(1, 6 * mm))

    dong = ton_kho["dong"]
    ghi_chu = [_ghi_chu_ton(d) for d in dong]
    hang = [["Mã SP", "Tên sản phẩm", "Loại", "Tồn", "Tối thiểu", "Giá vốn", "Giá trị tồn", "Ghi chú"]]
    hang += [[d["ma_sp"], d["ten_sp"], d["danh_muc"], d["ton_kho"], d["ton_toi_thieu"],
              dinh_dang_so(d["gia_von"]), dinh_dang_so(d["gia_tri_ton"]), ghi_chu[i][0]]
             for i, d in enumerate(dong)]
    pt.append(_bang(hang, [18 * mm, 38 * mm, 26 * mm, 11 * mm, 15 * mm, 18 * mm, 22 * mm, 32 * mm],
                    can_phai=(3, 4, 5, 6), co=7.5, mau_dong=lambda i: ghi_chu[i][1]))
    tai_lieu.build(pt, canvasmaker=_canvas_co_chan_trang(_chan_trai(nguoi_in)))