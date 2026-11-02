from tkinter import messagebox

from utils.permissions import PermissionDenied
from utils.session import Session

def goi_controller(widget, ham, *args, **kwargs):
    """
    Gọi một hàm Controller. Nếu bị chặn quyền thì báo cho người dùng;
    nếu phiên đã hết ( bị khóa) thì phát tín hiệu để App đưa về màn hình đăng nhập.
    Trả về kết quả của hàm, hoặc None nếu bị chặn
    """
    try:
        return ham(*args, **kwargs)
    except PermissionDenied as loi:
        messagebox.showwarning("Không đủ quyền", str(loi), parent=widget)
        if not Session.is_logged_in():
            widget.nametowidget(".").event_generate("<<PhienHetHan>>", when="tail")
        return None