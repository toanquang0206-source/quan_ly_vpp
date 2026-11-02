import uuid
from datetime import datetime

from database.connection import transaction
from models.nha_cung_cap import NhaCungCap
from models.nhat_ky import NhatKy
from models.phieu_nhap import PhieuNhap
from models.san_pham import SanPham
from models.the_kho import TheKho
from utils.errors import LoiNghiepVu
from utils.gia_von import gia_von_binh_quan
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_THU_KHO, Session
from utils.validators import doc_so

QUAN_LY_KHO = (ROLE_ADMIN, ROLE_THU_KHO)
TOI_DA_SO_LUONG = 1_000_000
TOI_DA_MAT_HANG = 200
LECH_BAT_THUONG_PHAN_TRAM = 30     # giá nhập lệch quá mức này so với giá vốn hiện tại -> cảnh báo


def _loi_neu_khong_nhap_duoc(sp):
    """Trả về thông báo lỗi nếu sản phẩm không thể nhập kho, ngược lại trả về None."""
    if sp is None:
        return "Có sản phẩm không còn tồn tại."
    if sp["trang_thai"] != "kinh_doanh":
        return (f"Sản phẩm {sp['ma_sp']} đang ngừng kinh doanh. "
                f"Hãy cho kinh doanh lại trước khi nhập kho.")
    return None


def _kiem_tra_dong_hang(dong_hang):
    """Trả về (danh sách dòng sạch, None) hoặc (None, lỗi)."""
    if not dong_hang:
        return None, "Phiếu nhập chưa có mặt hàng nào."
    if len(dong_hang) > TOI_DA_MAT_HANG:
        return None, f"Mỗi phiếu nhập tối đa {TOI_DA_MAT_HANG} mặt hàng."

    sach, da_co = [], set()
    for i, d in enumerate(dong_hang, start=1):
        if not d.get("san_pham_id"):
            return None, f"Dòng {i}: chưa chọn sản phẩm."
        sp_id = int(d["san_pham_id"])
        if sp_id in da_co:
            return None, f"Dòng {i}: sản phẩm bị trùng trong phiếu, hãy gộp thành một dòng."
        da_co.add(sp_id)

        so_luong, loi = doc_so(d.get("so_luong"), "số lượng")
        if loi:
            return None, f"Dòng {i}: {loi}"
        if not 1 <= so_luong <= TOI_DA_SO_LUONG:
            return None, f"Dòng {i}: số lượng phải từ 1 đến 1.000.000."
        gia_nhap, loi = doc_so(d.get("gia_nhap"), "giá nhập")
        if loi:
            return None, f"Dòng {i}: {loi}"
        sach.append({"san_pham_id": sp_id, "so_luong": so_luong, "gia_nhap": gia_nhap})

    # Luôn khóa các dòng sản phẩm theo MỘT thứ tự cố định: hai phiếu nhập chạy cùng lúc
    # sẽ không thể khóa chéo nhau (deadlock).
    sach.sort(key=lambda x: x["san_pham_id"])
    return sach, None


class NhapKhoController:
    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def danh_sach_nha_cung_cap():
        return NhaCungCap.tat_ca(chi_hop_tac=True)

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def goi_y_san_pham(tu_khoa, gioi_han=8):
        tu_khoa = (tu_khoa or "").strip()
        if len(tu_khoa) < 2:
            return []
        return [{"id": r["id"], "ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"],
                 "ton_kho": r["ton_kho"], "gia_von": int(r["gia_nhap"])}
                for r in SanPham.goi_y_cho_nhap(tu_khoa, gioi_han)]

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def xem_truoc(dong_hang):
        """
        Tính THỬ, không ghi gì: giá vốn mới và cờ cảnh báo cho từng dòng.
        Trả về (True/False, thông điệp, dữ liệu). Số liệu là số thô để View định dạng.
        """
        dong, loi = _kiem_tra_dong_hang(dong_hang)
        if loi:
            return False, loi, None
        sp_theo_id = SanPham.tim_nhieu_theo_id([d["san_pham_id"] for d in dong])

        ket_qua, tong_tien = [], 0
        for d in dong:
            sp = sp_theo_id.get(d["san_pham_id"])
            loi_sp = _loi_neu_khong_nhap_duoc(sp)
            if loi_sp:
                return False, loi_sp, None

            gia_von = int(sp["gia_nhap"])
            gia_von_sau = gia_von_binh_quan(sp["ton_kho"], gia_von, d["so_luong"], d["gia_nhap"])
            lech, bat_thuong = None, False
            if gia_von > 0:
                lech = round((d["gia_nhap"] - gia_von) * 100 / gia_von)
                bat_thuong = abs(d["gia_nhap"] - gia_von) * 100 > LECH_BAT_THUONG_PHAN_TRAM * gia_von
            thanh_tien = d["so_luong"] * d["gia_nhap"]
            tong_tien += thanh_tien
            ket_qua.append({
                "san_pham_id": d["san_pham_id"], "ma_sp": sp["ma_sp"], "ten_sp": sp["ten_sp"],
                "so_luong": d["so_luong"], "gia_nhap": d["gia_nhap"], "thanh_tien": thanh_tien,
                "gia_von_hien_tai": gia_von, "gia_von_sau": gia_von_sau,
                "lech_phan_tram": lech, "bat_thuong": bat_thuong,
                "vuot_gia_ban": gia_von_sau > sp["gia_ban"],
            })
        return True, "OK", {"dong": ket_qua, "tong_tien": tong_tien,
                            "nguong_lech": LECH_BAT_THUONG_PHAN_TRAM}

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def tao_phieu_nhap(nha_cung_cap_id, dong_hang, ghi_chu=""):
        """
        dong_hang: [{"san_pham_id": 5, "so_luong": "100", "gia_nhap": "3.000"}, ...]
        Trả về (True/False, thông điệp, dữ liệu). Dữ liệu là SỐ THÔ, View tự định dạng.
        """
        if not nha_cung_cap_id:
            return False, "Vui lòng chọn nhà cung cấp.", None
        dong, loi = _kiem_tra_dong_hang(dong_hang)
        if loi:
            return False, loi, None

        ghi_chu = (ghi_chu or "").strip()[:255] or None
        nguoi_id = Session.get_user()["id"]
        bay_gio = datetime.now()
        tong_tien = sum(d["so_luong"] * d["gia_nhap"] for d in dong)
        canh_bao = []

        try:
            # MỘT transaction cho cả phiếu: ghi phiếu + các dòng + cộng tồn + giá vốn
            # + thẻ kho + nhật ký, hoặc không gì cả.
            with transaction() as conn:
                ncc = NhaCungCap.tim_theo_id(conn, nha_cung_cap_id)
                if ncc is None or ncc["trang_thai"] != "hop_tac":
                    raise LoiNghiepVu("Nhà cung cấp không hợp lệ hoặc đã ngừng hợp tác.")

                phieu_id = PhieuNhap.them_phieu(
                    conn, "TAM-" + uuid.uuid4().hex[:20], nha_cung_cap_id,
                    nguoi_id, bay_gio, tong_tien, ghi_chu)
                ma_phieu = f"PN{bay_gio:%Y%m%d}-{phieu_id:05d}"
                PhieuNhap.dat_ma(conn, phieu_id, ma_phieu)

                for d in dong:
                    sp = SanPham.khoa_dong(conn, d["san_pham_id"])
                    loi_sp = _loi_neu_khong_nhap_duoc(sp)
                    if loi_sp:
                        raise LoiNghiepVu(loi_sp)

                    gia_von_moi = gia_von_binh_quan(
                        sp["ton_kho"], sp["gia_nhap"], d["so_luong"], d["gia_nhap"])
                    ton_sau = sp["ton_kho"] + d["so_luong"]

                    PhieuNhap.them_dong(conn, phieu_id, d["san_pham_id"],
                                        d["so_luong"], d["gia_nhap"])       # giá của LÔ này
                    SanPham.cap_nhat_sau_nhap(conn, d["san_pham_id"],
                                              d["so_luong"], gia_von_moi)   # giá vốn bình quân
                    TheKho.ghi(conn, d["san_pham_id"], "nhap_kho", d["so_luong"],
                               ton_sau, phieu_id, nguoi_id, ma_phieu)

                    if gia_von_moi > sp["gia_ban"]:
                        canh_bao.append({"ma_sp": sp["ma_sp"], "ten_sp": sp["ten_sp"],
                                         "gia_von": gia_von_moi, "gia_ban": int(sp["gia_ban"])})

                NhatKy.ghi(conn, nguoi_id, "NHAP_KHO", "phieu_nhap", phieu_id,
                           f"{ma_phieu}: {len(dong)} mặt hàng, tổng {tong_tien}")
        except LoiNghiepVu as loi:
            return False, str(loi), None

        return True, f"Đã lập phiếu nhập {ma_phieu}.", {
            "ma_phieu": ma_phieu, "tong_tien": tong_tien, "canh_bao": canh_bao}

    @staticmethod
    @require_roles(*QUAN_LY_KHO)
    def the_kho(san_pham_id, trang=1, so_dong=20):
        tong = TheKho.dem(san_pham_id)
        so_trang = max(1, -(-tong // so_dong))
        trang = min(max(trang, 1), so_trang)
        return {"dong": TheKho.lich_su(san_pham_id, trang, so_dong),
                "tong": tong, "trang": trang, "so_trang": so_trang}