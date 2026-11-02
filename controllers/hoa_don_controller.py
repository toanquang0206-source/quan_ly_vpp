from datetime import datetime, timedelta

from database.connection import transaction
from models.hoa_don import HoaDon
from models.nhat_ky import NhatKy
from models.phieu_tra_hang import PhieuTraHang
from models.san_pham import SanPham
from models.the_kho import TheKho
from utils.errors import LoiNghiepVu
from utils.gia_von import gia_von_binh_quan
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_NHAN_VIEN, Session
from utils.validators import doc_so

XEM_VA_TRA = (ROLE_ADMIN, ROLE_NHAN_VIEN)
CHI_ADMIN = (ROLE_ADMIN,)
THOI_HAN_DOI_TRA = timedelta(days=3)          # chỉ đổi trả trong vòng 3 ngày kể từ lúc lập hóa đơn


def _doc_ngay(chuoi, ten_truong):
    """'25/10/2026' -> (date, None); rỗng -> (None, None); sai định dạng -> (None, lỗi)."""
    chuoi = (chuoi or "").strip()
    if not chuoi:
        return None, None
    try:
        return datetime.strptime(chuoi, "%d/%m/%Y").date(), None
    except ValueError:
        return None, f"{ten_truong} không đúng định dạng (ví dụ 25/10/2026)."


def _doc_dong_tra(dong_tra):
    """[{"san_pham_id": 5, "so_luong": "2"}] -> ({5: 2}, None). Dòng số lượng 0 bị bỏ qua."""
    sach = {}
    for d in dong_tra or []:
        so_luong, loi = doc_so(d.get("so_luong"), "số lượng trả", mac_dinh=0)
        if loi:
            return None, loi
        if so_luong == 0:
            continue
        sp_id = int(d["san_pham_id"])
        if sp_id in sach:
            return None, "Sản phẩm bị trùng trong phiếu trả."
        sach[sp_id] = so_luong
    if not sach:
        return None, "Hãy nhập số lượng trả cho ít nhất một mặt hàng."
    return sach, None


class HoaDonController:
    @staticmethod
    @require_roles(*XEM_VA_TRA)
    def tim_kiem(tu_khoa="", tu_ngay="", den_ngay="", trang=1, so_dong=10):
        """Trả về (True/False, thông điệp, dữ liệu). Ngày nhập theo dạng dd/mm/yyyy."""
        tu, loi = _doc_ngay(tu_ngay, "Từ ngày")
        if loi:
            return False, loi, None
        den, loi = _doc_ngay(den_ngay, "Đến ngày")
        if loi:
            return False, loi, None
        if tu and den and tu > den:
            return False, "Từ ngày phải trước hoặc bằng Đến ngày.", None

        tu_dt = datetime.combine(tu, datetime.min.time()) if tu else None
        den_dt = datetime.combine(den + timedelta(days=1), datetime.min.time()) if den else None
        tu_khoa = (tu_khoa or "").strip()

        tong = HoaDon.dem(tu_khoa, tu_dt, den_dt)
        so_trang = max(1, -(-tong // so_dong))
        trang = min(max(trang, 1), so_trang)
        dong = HoaDon.tim_kiem(tu_khoa, tu_dt, den_dt, trang, so_dong)
        for d in dong:
            d["tong_thanh_toan"] = int(d["tong_thanh_toan"])
            d["da_hoan"] = int(d["da_hoan"])
        return True, "OK", {"dong": dong, "tong": tong, "trang": trang, "so_trang": so_trang}

    @staticmethod
    @require_roles(*XEM_VA_TRA)
    def chi_tiet(hoa_don_id):
        """Chi tiết hóa đơn + những gì được phép làm tiếp (trả hàng, hủy). Không có giá vốn."""
        hd = HoaDon.tim_theo_id(hoa_don_id)
        if hd is None:
            return False, "Không tìm thấy hóa đơn.", None
        dong = HoaDon.dong_theo_hoa_don(hoa_don_id)
        for d in dong:
            d["so_luong"], d["da_tra"] = int(d["so_luong"]), int(d["da_tra"])
            d["don_gia"] = int(d["don_gia"])
            d["thanh_tien"] = d["so_luong"] * d["don_gia"]
            d["con_tra_duoc"] = d["so_luong"] - d["da_tra"]
        hd["tong_thanh_toan"], hd["da_hoan"] = int(hd["tong_thanh_toan"]), int(hd["da_hoan"])

        han = hd["ngay_lap"] + THOI_HAN_DOI_TRA
        con_han = datetime.now() <= han
        con_hang_de_tra = any(d["con_tra_duoc"] > 0 for d in dong)
        co_tra_hang = any(d["da_tra"] > 0 for d in dong)

        ly_do_khong_tra = None
        if hd["trang_thai"] != "hoan_thanh":
            ly_do_khong_tra = "Hóa đơn đã bị hủy."
        elif not con_han:
            ly_do_khong_tra = f"Đã quá hạn đổi trả ({THOI_HAN_DOI_TRA.days} ngày)."
        elif not con_hang_de_tra:
            ly_do_khong_tra = "Đã trả hết các mặt hàng."

        ly_do_khong_huy = None
        if hd["trang_thai"] != "hoan_thanh":
            ly_do_khong_huy = "Hóa đơn đã bị hủy."
        elif co_tra_hang:
            ly_do_khong_huy = "Hóa đơn đã có trả hàng, không thể hủy."

        return True, "OK", {
            "hoa_don": hd, "dong": dong, "han_doi_tra": han, "con_han": con_han,
            "co_the_tra": ly_do_khong_tra is None, "ly_do_khong_tra": ly_do_khong_tra,
            "co_the_huy": Session.has_role(ROLE_ADMIN) and ly_do_khong_huy is None,
            "ly_do_khong_huy": ly_do_khong_huy,
        }

    @staticmethod
    @require_roles(*XEM_VA_TRA)
    def tra_hang(hoa_don_id, dong_tra, ly_do=""):
        """
        dong_tra: [{"san_pham_id": 5, "so_luong": "2"}, ...]
        Hàng trả nhập lại kho theo GIÁ VỐN GHI TRÊN HÓA ĐƠN GỐC; tiền hoàn theo GIÁ TRÊN HÓA ĐƠN GỐC.
        Trả về (True/False, thông điệp, dữ liệu).
        """
        yeu_cau, loi = _doc_dong_tra(dong_tra)
        if loi:
            return False, loi, None
        ly_do = (ly_do or "").strip()[:255] or None
        nguoi_id = Session.get_user()["id"]
        bay_gio = datetime.now()

        try:
            with transaction() as conn:
                hd = HoaDon.khoa(conn, hoa_don_id)           # khóa hóa đơn trước, rồi mới khóa sản phẩm
                if hd is None:
                    raise LoiNghiepVu("Không tìm thấy hóa đơn.")
                if hd["trang_thai"] != "hoan_thanh":
                    raise LoiNghiepVu("Hóa đơn đã bị hủy, không thể trả hàng.")
                if bay_gio > hd["ngay_lap"] + THOI_HAN_DOI_TRA:
                    raise LoiNghiepVu(
                        f"Đã quá hạn đổi trả ({THOI_HAN_DOI_TRA.days} ngày kể từ khi lập hóa đơn).")

                dong_hd = {d["san_pham_id"]: d for d in HoaDon.dong_de_tra(conn, hoa_don_id)}
                cac_dong = []
                for sp_id in sorted(yeu_cau):                # khóa theo thứ tự id cố định
                    d = dong_hd.get(sp_id)
                    if d is None:
                        raise LoiNghiepVu("Sản phẩm không thuộc hóa đơn này.")
                    con = d["so_luong"] - d["da_tra"]
                    if yeu_cau[sp_id] > con:
                        raise LoiNghiepVu(f"{d['ten_sp']}: chỉ còn trả được {con}.")
                    cac_dong.append((d, yeu_cau[sp_id]))

                tong_hoan = sum(sl * int(d["don_gia"]) for d, sl in cac_dong)
                phieu_id = PhieuTraHang.them(conn, hoa_don_id, nguoi_id, bay_gio, ly_do, tong_hoan)
                for d, sl in cac_dong:
                    sp = SanPham.khoa_dong(conn, d["san_pham_id"])      # không chặn SP đã ngừng KD
                    gia_von_moi = gia_von_binh_quan(
                        sp["ton_kho"], sp["gia_nhap"], sl, d["gia_von"])
                    PhieuTraHang.them_dong(conn, phieu_id, sp["id"], sl, int(d["don_gia"]))
                    SanPham.cap_nhat_sau_nhap(conn, sp["id"], sl, gia_von_moi)
                    TheKho.ghi(conn, sp["id"], "tra_hang", sl, sp["ton_kho"] + sl,
                               phieu_id, nguoi_id, hd["ma_hoa_don"])
                NhatKy.ghi(conn, nguoi_id, "TRA_HANG", "hoa_don", hoa_don_id,
                           f"{hd['ma_hoa_don']}: hoàn {tong_hoan}" + (f" - {ly_do}" if ly_do else ""))
        except LoiNghiepVu as loi:
            return False, str(loi), None
        return True, f"Đã ghi nhận trả hàng cho hóa đơn {hd['ma_hoa_don']}.", {
            "ma_hoa_don": hd["ma_hoa_don"], "tien_hoan": tong_hoan}

    @staticmethod
    @require_roles(*CHI_ADMIN)
    def huy_hoa_don(hoa_don_id, ly_do):
        """Chỉ Admin. Hàng quay về kho theo giá vốn ghi trên hóa đơn. Không xóa dòng nào."""
        ly_do = (ly_do or "").strip()
        if not ly_do:
            return False, "Vui lòng nhập lý do hủy hóa đơn.", None
        ly_do = ly_do[:200]
        nguoi_id = Session.get_user()["id"]

        try:
            with transaction() as conn:
                hd = HoaDon.khoa(conn, hoa_don_id)
                if hd is None:
                    raise LoiNghiepVu("Không tìm thấy hóa đơn.")
                if hd["trang_thai"] != "hoan_thanh":
                    raise LoiNghiepVu("Hóa đơn đã bị hủy từ trước.")
                if HoaDon.da_co_tra_hang(conn, hoa_don_id):
                    raise LoiNghiepVu("Hóa đơn đã có trả hàng, không thể hủy.")

                for d in HoaDon.dong_de_tra(conn, hoa_don_id):     # đã sắp theo san_pham_id
                    sp = SanPham.khoa_dong(conn, d["san_pham_id"])
                    gia_von_moi = gia_von_binh_quan(
                        sp["ton_kho"], sp["gia_nhap"], d["so_luong"], d["gia_von"])
                    SanPham.cap_nhat_sau_nhap(conn, sp["id"], d["so_luong"], gia_von_moi)
                    TheKho.ghi(conn, sp["id"], "huy_hoa_don", d["so_luong"],
                               sp["ton_kho"] + d["so_luong"], hoa_don_id, nguoi_id, hd["ma_hoa_don"])
                HoaDon.doi_trang_thai(conn, hoa_don_id, "da_huy")
                NhatKy.ghi(conn, nguoi_id, "HUY_HOA_DON", "hoa_don", hoa_don_id,
                           f"{hd['ma_hoa_don']}: {ly_do}")
        except LoiNghiepVu as loi:
            return False, str(loi), None
        return True, f"Đã hủy hóa đơn {hd['ma_hoa_don']}.", {
            "ma_hoa_don": hd["ma_hoa_don"], "tien_hoan": int(hd["tong_thanh_toan"])}