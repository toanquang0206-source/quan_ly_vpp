import os
import subprocess
import sys
from tkinter import filedialog, messagebox

from utils.permissions import PermissionDenied
from utils.session import Session


def goi_controller(widget, ham, *args, **kwargs):
    """
    Gọi một hàm Controller. Nếu bị chặn quyền thì báo cho người dùng;
    nếu phiên đã hết (bị khóa) thì phát tín hiệu để App đưa về màn hình đăng nhập.
    Trả về kết quả của hàm, hoặc None nếu bị chặn.
    """
    try:
        return ham(*args, **kwargs)
    except PermissionDenied as loi:
        messagebox.showwarning("Không đủ quyền", str(loi), parent=widget)
        if not Session.is_logged_in():
            widget.nametowidget(".").event_generate("<<PhienHetHan>>", when="tail")
        return None


def mo_tep(duong_dan):
    """Mở file bằng chương trình mặc định của hệ điều hành (trình xem PDF)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(duong_dan)
        elif sys.platform == "darwin":
            subprocess.run(["open", duong_dan], check=False)
        else:
            subprocess.run(["xdg-open", duong_dan], check=False)
    except Exception:
        pass                                      # không mở được thì thôi, file vẫn đã lưu


def xuat_pdf(widget, ten_goi_y, ham_xuat):
    """
    Hỏi người dùng nơi lưu, gọi ham_xuat(duong_dan) để tạo file, báo kết quả và hỏi có mở file không.
    Trả về True nếu đã xuất xong.
    """
    duong_dan = filedialog.asksaveasfilename(
        parent=widget, title="Lưu file PDF", defaultextension=".pdf",
        initialfile=ten_goi_y, filetypes=[("Tệp PDF", "*.pdf")])
    if not duong_dan:                             # người dùng bấm Hủy
        return False
    try:
        ham_xuat(duong_dan)
    except PermissionError:
        messagebox.showerror(
            "Không lưu được file",
            "Không ghi được file. Có thể file đang được mở trong trình xem PDF.\n"
            "Hãy đóng file đó rồi thử lại.", parent=widget)
        return False
    except Exception as loi:
        messagebox.showerror("Không xuất được PDF", str(loi), parent=widget)
        return False
    if messagebox.askyesno("Đã xuất PDF", f"Đã lưu file:\n{duong_dan}\n\nMở file ngay bây giờ?",
                           parent=widget):
        mo_tep(duong_dan)
    return True