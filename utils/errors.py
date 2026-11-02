class DuLieuTrung(Exception):
    """Vi phạm ràng buộc UNIQUE của CSDL (vd: trùng mã sản phẩm)."""


class LoiNghiepVu(Exception):
    """Vi phạm luật nghiệp vụ phát hiện GIỮA CHỪNG transaction.
    Ném ra để transaction tự rollback; thông điệp dùng để hiển thị cho người dùng."""
class TongThayDoi(Exception):
    """Tổng tiền tính lúc lưu khác tổng đang hiện trên màn hình (giá vừa được cập nhật)."""

    def __init__(self, tong_moi):
        super().__init__("Tổng tiền đã thay đổi.")
        self.tong_moi = tong_moi