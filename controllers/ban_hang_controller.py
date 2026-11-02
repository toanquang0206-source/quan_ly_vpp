import uuid
from datetime import datetime

from database.connection import transaction
from models.hoa_don import HoaDon
from models.nhat_ky import NhatKy
from models.san_pham import SanPham
from models.the_kho import TheKho
from utils.errors import LoiNghiepVu, TongThayDoi
from utils.permissions import require_roles
from utils.session import ROLE_ADMIN, ROLE_NHAN_VIEN, Session
from utils.validators import doc_so

BAN_HANG = (ROLE_ADMIN, ROLE_NHAN_VIEN)
TOI_DA_SO_LUONG = 100_000
TOI_DA_MAT_HANG = 100
PHUONG_THUC = ("tien_mat", "chuyen_khoan", "the")


def _ly_do_khong_ban(sp, so_luong):
    """Trả về lý do không bán được dòng này, hoặc None nếu bán được."""
    if sp is None:
        return "Sản phẩm không còn tồn tại."
    if sp["trang_thai"] != "kinh_doanh":
        return "Đã ngừng kinh doanh."
    if sp["ton_kho"] <= 0:
        return "Đã hết hàng."
    if sp["ton_kho"] < so_luong:
        return f"Chỉ còn {sp['ton_kho']}."
    return None


def _kiem_tra_gio_hang(gio_hang):
    """gio_hang: [{"san_pham_id": 5, "so_luong": 2}]. Trả về (dòng sạch, None) hoặc (None, lỗi)."""
    if not gio_hang:
        return None, "Giỏ hàng đang trống."
    if len(gio_hang) > TOI_DA_MAT_HANG:
        return None, f"Mỗi hóa đơn tối đa {TOI_DA_MAT_HANG} mặt hàng."
    sach, da_co = [], set()
    for i, d in enumerate(gio_hang, start=1):
        if not d.get("san_pham_id"):
            return None, f"Dòng {i}: chưa chọn sản phẩm."
        sp_id = int(d["san_pham_id"])
        if sp_id in da_co:
            return None, f"Dòng {i}: sản phẩm bị trùng trong giỏ."
        da_co.add(sp_id)
        so_luong, loi = doc_so(d.get("so_luong"), "số lượng")
        if loi:
            return None, f"Dòng {i}: {loi}"
        if not 1 <= so_luong <= TOI_DA_SO_LUONG:
            return None, f"Dòng {i}: số lượng phải từ 1 đến 100.000."
        # CỐ Ý không nhận giá từ giao diện: giá luôn lấy từ CSDL
        sach.append({"san_pham_id": sp_id, "so_luong": so_luong})
    sach.sort(key=lambda x: x["san_pham_id"])      # khóa theo thứ tự cố định, tránh deadlock
    return sach, None


class BanHangController:
    @staticmethod
    @require_roles(*BAN_HANG)
    def goi_y_san_pham(tu_khoa, gioi_han=8):
        tu_khoa = (tu_khoa or "").strip()
        if len(tu_khoa) < 2:
            return []
        return [{"id": r["id"], "ma_sp": r["ma_sp"], "ten_sp": r["ten_sp"],
                 "ton_kho": r["ton_kho"], "gia_ban": int(r["gia_ban"])}
                for r in SanPham.goi_y_cho_ban(tu_khoa, gioi_han)]

    @staticmethod
    @require_roles(*BAN_HANG)
    def xem_truoc(gio_hang):
        """
        Tính lại giỏ hàng theo GIÁ HIỆN TẠI trong CSDL (không ghi gì). View gọi hàm này
        định kỳ nên giá trong giỏ luôn bám theo giá quản lý vừa cập nhật.
        Trả về (True/False, thông điệp, dữ liệu). Không có giá vốn trong dữ liệu trả về.
        """
        dong, loi = _kiem_tra_gio_hang(gio_hang)
        if loi:
            return False, loi, None
        sp_theo_id = SanPham.tim_nhieu_theo_id([d["san_pham_id"] for d in dong])

        ket_qua, tong, co_loi = [], 0, False
        for d in dong:
            sp = sp_theo_id.get(d["san_pham_id"])
            if sp is None:
                return False, "Có sản phẩm không còn tồn tại.", None
            ly_do = _ly_do_khong_ban(sp, d["so_luong"])
            co_loi = co_loi or ly_do is not None
            don_gia = int(sp["gia_ban"])
            thanh_tien = don_gia * d["so_luong"]
            tong += thanh_tien
            ket_qua.append({"san_pham_id": sp["id"], "ma_sp": sp["ma_sp"], "ten_sp": sp["ten_sp"],
                            "so_luong": d["so_luong"], "don_gia": don_gia,
                            "thanh_tien": thanh_tien, "ton_kho": sp["ton_kho"],
                            "khong_ban_duoc": ly_do})
        return True, "OK", {"dong": ket_qua, "tong_tien": tong, "co_loi_hang": co_loi}

    @staticmethod
    @require_roles(*BAN_HANG)
    def lap_hoa_don(gio_hang, phuong_thuc, tong_dang_hien, ghi_chu=""):
        """
        tong_dang_hien: tổng tiền ĐANG HIỆN trên màn hình lúc bấm thanh toán.
        Trả về (True/False, thông điệp, dữ liệu).
        """
        if phuong_thuc not in PHUONG_THUC:
            return False, "Vui lòng chọn hình thức thanh toán.", None
        dong, loi = _kiem_tra_gio_hang(gio_hang)
        if loi:
            return False, loi, None

        ghi_chu = (ghi_chu or "").strip()[:255] or None
        nguoi_id = Session.get_user()["id"]
        bay_gio = datetime.now()

        try:
            with transaction() as conn:           # MỘT transaction: hóa đơn + dòng + trừ kho + thẻ kho
                # Bước 1: khóa từng sản phẩm (theo thứ tự id) và chốt giá + tồn tại thời điểm này
                chot, tong = [], 0
                for d in dong:
                    sp = SanPham.khoa_dong(conn, d["san_pham_id"])
                    ly_do = _ly_do_khong_ban(sp, d["so_luong"])
                    if ly_do:
                        ten = sp["ten_sp"] if sp else "Sản phẩm"
                        raise LoiNghiepVu(f"{ten}: {ly_do[0].lower()}{ly_do[1:]}")
                    don_gia = int(sp["gia_ban"])
                    chot.append({"sp": sp, "so_luong": d["so_luong"], "don_gia": don_gia})
                    tong += don_gia * d["so_luong"]

                # Chốt chặn: tổng khác tổng khách đang thấy -> không lưu, để giao diện làm mới
                if int(tong_dang_hien) != tong:
                    raise TongThayDoi(tong)

                # Bước 2: ghi
                hoa_don_id = HoaDon.them_hoa_don(
                    conn, "TAM-" + uuid.uuid4().hex[:20], nguoi_id, bay_gio, tong,
                    phuong_thuc, ghi_chu)
                ma = f"HD{bay_gio:%Y%m%d}-{hoa_don_id:05d}"
                HoaDon.dat_ma(conn, hoa_don_id, ma)

                for x in chot:
                    sp = x["sp"]
                    HoaDon.them_dong(conn, hoa_don_id, sp["id"], x["so_luong"],
                                     x["don_gia"], int(sp["gia_nhap"]))      # chụp giá bán + giá vốn
                    if not SanPham.tru_ton(conn, sp["id"], x["so_luong"]):    # chốt chặn cuối
                        raise LoiNghiepVu(f"{sp['ten_sp']}: không đủ hàng.")
                    TheKho.ghi(conn, sp["id"], "ban_hang", -x["so_luong"],
                               sp["ton_kho"] - x["so_luong"], hoa_don_id, nguoi_id, ma)

                NhatKy.ghi(conn, nguoi_id, "BAN_HANG", "hoa_don", hoa_don_id,
                           f"{ma}: {len(chot)} mặt hàng, tổng {tong}")
        except LoiNghiepVu as loi:
            return False, str(loi), None
        except TongThayDoi as e:
            return False, ("Giá vừa được cập nhật. Giỏ hàng đã được làm mới, "
                           "hãy kiểm tra lại tổng tiền rồi thanh toán."), \
                {"ma_loi": "TONG_THAY_DOI", "tong_moi": e.tong_moi}

        return True, f"Đã lập hóa đơn {ma}.", {
            "ma_hoa_don": ma, "tong_thanh_toan": tong, "phuong_thuc": phuong_thuc,
            "thoi_gian": bay_gio,
            "dong": [{"ma_sp": x["sp"]["ma_sp"], "ten_sp": x["sp"]["ten_sp"],
                      "so_luong": x["so_luong"], "don_gia": x["don_gia"],
                      "thanh_tien": x["don_gia"] * x["so_luong"]} for x in chot]}