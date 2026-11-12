-- =====================================================================
--  CẬP NHẬT CƠ SỞ DỮ LIỆU: thêm các cột và chỉ mục bổ sung
--
--  Chạy SAU file quan_ly_kho_vpp.sql. AN TOÀN KHI CHẠY LẠI: phần nào đã có
--  sẵn sẽ được bỏ qua và chỉ in một dòng ghi chú.
--
--  Dòng lệnh:
--    mysql -u root -p --default-character-set=utf8mb4 < database\cap_nhat_csdl.sql
--  Hoặc mở file trong MySQL Workbench rồi bấm Execute.
-- =====================================================================
USE quan_ly_kho_vpp;

-- ---------------------------------------------------------------------
-- 1) hoa_don.ngay_huy: ngày hủy hóa đơn (khoản hủy được báo cáo vào NGÀY HỦY)
-- ---------------------------------------------------------------------
SET @co = (SELECT COUNT(*) FROM information_schema.columns
           WHERE table_schema = DATABASE() AND table_name = 'hoa_don' AND column_name = 'ngay_huy');
SET @lenh = IF(@co = 0,
    'ALTER TABLE hoa_don ADD COLUMN ngay_huy DATETIME NULL AFTER trang_thai',
    'SELECT ''hoa_don.ngay_huy da co, bo qua'' AS ghi_chu');
PREPARE thuc_thi FROM @lenh;
EXECUTE thuc_thi;
DEALLOCATE PREPARE thuc_thi;

-- Điền ngày hủy cho các hóa đơn đã bị hủy từ trước (lấy từ nhật ký; không có thì lấy ngày lập)
SET SQL_SAFE_UPDATES = 0;
UPDATE hoa_don hd
SET hd.ngay_huy = COALESCE(
        (SELECT MAX(n.thoi_gian) FROM nhat_ky_hoat_dong n
         WHERE n.hanh_dong = 'HUY_HOA_DON' AND n.ban_ghi_id = hd.id),
        hd.ngay_lap)
WHERE hd.trang_thai = 'da_huy' AND hd.ngay_huy IS NULL;
SET SQL_SAFE_UPDATES = 1;

-- ---------------------------------------------------------------------
-- 2) nguoi_dung.bat_buoc_doi_mat_khau: 1 = phải đổi mật khẩu ở lần đăng nhập tới
-- ---------------------------------------------------------------------
SET @co = (SELECT COUNT(*) FROM information_schema.columns
           WHERE table_schema = DATABASE() AND table_name = 'nguoi_dung'
             AND column_name = 'bat_buoc_doi_mat_khau');
SET @lenh = IF(@co = 0,
    'ALTER TABLE nguoi_dung ADD COLUMN bat_buoc_doi_mat_khau TINYINT(1) NOT NULL DEFAULT 0 AFTER trang_thai',
    'SELECT ''nguoi_dung.bat_buoc_doi_mat_khau da co, bo qua'' AS ghi_chu');
PREPARE thuc_thi FROM @lenh;
EXECUTE thuc_thi;
DEALLOCATE PREPARE thuc_thi;

-- ---------------------------------------------------------------------
-- 3) nha_cung_cap: tên nhà cung cấp không được trùng nhau
--    (nếu lệnh báo lỗi trùng dữ liệu, hãy đổi tên một trong hai nhà cung cấp trùng rồi chạy lại)
-- ---------------------------------------------------------------------
SET @co = (SELECT COUNT(*) FROM information_schema.statistics
           WHERE table_schema = DATABASE() AND table_name = 'nha_cung_cap' AND index_name = 'uq_ncc_ten');
SET @lenh = IF(@co = 0,
    'ALTER TABLE nha_cung_cap ADD UNIQUE KEY uq_ncc_ten (ten_ncc)',
    'SELECT ''Chi muc uq_ncc_ten da co, bo qua'' AS ghi_chu');
PREPARE thuc_thi FROM @lenh;
EXECUTE thuc_thi;
DEALLOCATE PREPARE thuc_thi;

-- =====================================================================
--  TÙY CHỌN: cân bằng thẻ kho cho dữ liệu mẫu.
--
--  Sản phẩm mẫu có sẵn số tồn nhưng chưa có dòng nào trong thẻ kho, nên màn hình
--  Thẻ kho sẽ báo "Lệch sổ" cho chúng. Chạy đoạn dưới (bỏ dấu "-- " ở đầu mỗi dòng)
--  SAU KHI đã tạo tài khoản tên "admin" bằng: python create_admin.py
-- =====================================================================
-- INSERT INTO the_kho (san_pham_id, loai_giao_dich, so_luong_thay_doi, ton_sau_giao_dich,
--                      nguoi_dung_id, ghi_chu)
-- SELECT sp.id, 'kiem_ke',
--        sp.ton_kho - COALESCE((SELECT SUM(t.so_luong_thay_doi) FROM the_kho t WHERE t.san_pham_id = sp.id), 0),
--        sp.ton_kho,
--        (SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'admin' LIMIT 1),
--        'Tồn đầu kỳ (cân bằng dữ liệu mẫu)'
-- FROM san_pham sp
-- WHERE sp.ton_kho <> COALESCE((SELECT SUM(t.so_luong_thay_doi) FROM the_kho t WHERE t.san_pham_id = sp.id), 0);