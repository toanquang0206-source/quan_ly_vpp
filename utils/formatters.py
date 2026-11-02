"""Định dạng hiển thị. Không phụ thuộc tkinter nên dùng được cho cả PDF/Excel"""

def dinh_dang_tien(so):
    """12000 (hoặc Decimal('12000')) -> '12.000 đ'"""
    if so is None:
        return ""
    return f"{int(so):,}".replace(",", ".") + "đ"

def dinh_dang_ngay(ngay):
    """datetime/date -> '26/10/2026'"""
    return ngay.strftime("%d/%m/%Y") if ngay else ""

def dinh_dang_gio(thoi_diem):
    """datetime -> '26/10/2026 14:05'"""
    return thoi_diem.strftime("%d/%m/%Y %H:%M") if thoi_diem else ""