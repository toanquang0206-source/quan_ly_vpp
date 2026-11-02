def gia_von_binh_quan(ton_cu, gia_von_cu, so_luong_nhap, gia_nhap_moi):
    """
    Bình quân gia quyền:
        (tồn cũ x giá vốn cũ + số mới x giá mới) / (tồn cũ + số mới)
    Làm tròn đến đồng (nửa đồng thì làm tròn lên), tính bằng số nguyên nên không sai số.
    Nếu kho đang trống thì giá vốn chính là giá của lô vừa nhập.
    """
    if ton_cu <= 0:
        return int(gia_nhap_moi)
    tong_so_luong = int(ton_cu) + int(so_luong_nhap)
    tong_gia_tri = int(ton_cu) * int(gia_von_cu) + int(so_luong_nhap) * int(gia_nhap_moi)
    return (2 * tong_gia_tri + tong_so_luong) // (2 * tong_so_luong)