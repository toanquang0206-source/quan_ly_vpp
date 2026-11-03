from database.connection import fetch_all
for row in fetch_all("SELECT ma_sp, ten_sp, ton_kho FROM san_pham"):
    print(row)