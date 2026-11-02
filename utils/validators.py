import re


def doc_so(gia_tri, ten_truong, mac_dinh=None):
    """'12.000' / '12,000 đ' / 12000 -> (12000, None). Sai -> (None, thông báo lỗi)."""
    if gia_tri is None or str(gia_tri).strip() == "":
        if mac_dinh is not None:
            return mac_dinh, None
        return None, f"Vui lòng nhập {ten_truong}."
    chuoi = re.sub(r"[.,\sđĐ]", "", str(gia_tri))
    if not chuoi.isdigit():
        return None, f"{ten_truong.capitalize()} phải là số nguyên không âm."
    return int(chuoi), None