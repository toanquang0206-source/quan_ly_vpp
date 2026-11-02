-- =====================================================================
--  CSDL: ỨNG DỤNG QUẢN LÝ KHO VĂN PHÒNG PHẨM
--  MySQL 8.0+  |  utf8mb4  |  InnoDB
--
--  Cách đọc file này:
--   - Mỗi NHÓM ứng với một module của dự án.
--   - Bảng DANH MỤC = "thứ tồn tại" (sản phẩm, nhà cung cấp...).
--   - Bảng GIAO DỊCH = "sự kiện xảy ra" (hóa đơn, phiếu nhập...), luôn có
--     ngày giờ + người thực hiện, không sửa/xóa tùy tiện.
--   - Mỗi bảng giao dịch chia 2 tầng: PHẦN ĐẦU (header) + CÁC DÒNG (chi tiết),
--     giống tờ hóa đơn giấy.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS quan_ly_kho_vpp
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE quan_ly_kho_vpp;

-- =====================================================================
-- NHÓM 1: HỆ THỐNG (Module 1)
-- =====================================================================

-- Vai trò: Admin / Thủ kho / Nhân viên bán hàng
CREATE TABLE vai_tro (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ten_vai_tro  VARCHAR(30)  NOT NULL UNIQUE,
    mo_ta        VARCHAR(200)
) ENGINE=InnoDB;

-- Người dùng: 1 vai trò có nhiều người dùng (1-nhiều)
-- Lưu mật khẩu đã BĂM (bcrypt), tuyệt đối không lưu mật khẩu thô.
CREATE TABLE nguoi_dung (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ten_dang_nhap  VARCHAR(50)  NOT NULL UNIQUE,
    mat_khau_hash  VARCHAR(255) NOT NULL,
    ho_ten         VARCHAR(100) NOT NULL,
    email          VARCHAR(100),
    so_dien_thoai  VARCHAR(15),
    vai_tro_id     INT UNSIGNED NOT NULL,
    trang_thai     ENUM('hoat_dong','khoa') NOT NULL DEFAULT 'hoat_dong',
    ngay_tao       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id)
) ENGINE=InnoDB;

-- Nhật ký hoạt động: "ai đã làm gì, lúc nào"
CREATE TABLE nhat_ky_hoat_dong (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nguoi_dung_id INT UNSIGNED NOT NULL,
    hanh_dong     VARCHAR(50)  NOT NULL,   -- vd: 'THEM', 'SUA', 'XOA', 'DANG_NHAP'
    bang_tac_dong VARCHAR(50),             -- vd: 'san_pham'
    ban_ghi_id    INT UNSIGNED,            -- id của dòng bị tác động
    chi_tiet      VARCHAR(500),
    thoi_gian     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id),
    INDEX idx_nk_thoi_gian (thoi_gian)
) ENGINE=InnoDB;

-- =====================================================================
-- NHÓM 2: DANH MỤC & SẢN PHẨM (Module 2)
-- =====================================================================

CREATE TABLE don_vi_tinh (
    id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ten  VARCHAR(30) NOT NULL UNIQUE          -- cái, hộp, ram, cuộn...
) ENGINE=InnoDB;

CREATE TABLE danh_muc (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ten_danh_muc VARCHAR(100) NOT NULL UNIQUE, -- Bút, Vở, Giấy in...
    mo_ta      VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE nha_cung_cap (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ten_ncc       VARCHAR(150) NOT NULL,
    so_dien_thoai VARCHAR(15),
    email         VARCHAR(100),
    dia_chi       VARCHAR(255),
    trang_thai    ENUM('hop_tac','ngung') NOT NULL DEFAULT 'hop_tac'
) ENGINE=InnoDB;

CREATE TABLE khach_hang (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ten_kh        VARCHAR(100) NOT NULL,
    so_dien_thoai VARCHAR(15),
    email         VARCHAR(100),
    dia_chi       VARCHAR(255),
    ngay_tao      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Sản phẩm: mỗi sản phẩm thuộc 1 danh mục, 1 đơn vị tính (1-nhiều).
--  * gia_nhap / gia_ban ở đây là GIÁ HIỆN TẠI (có thể đổi sau này).
--  * ton_kho là số tồn HIỆN TẠI, được cập nhật mỗi khi có nhập/bán/trả...
--    CHECK (ton_kho >= 0) là "chốt chặn" cuối: DB từ chối bán quá số đang có.
--  * ngung_kinh_doanh = xóa mềm (không xóa hẳn vì còn nằm trong hóa đơn cũ).
CREATE TABLE san_pham (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ma_sp           VARCHAR(30)  NOT NULL UNIQUE,
    ten_sp          VARCHAR(150) NOT NULL,
    danh_muc_id     INT UNSIGNED NOT NULL,
    don_vi_tinh_id  INT UNSIGNED NOT NULL,
    gia_nhap        DECIMAL(15,0) NOT NULL DEFAULT 0,
    gia_ban         DECIMAL(15,0) NOT NULL DEFAULT 0,
    ton_kho         INT NOT NULL DEFAULT 0,
    ton_toi_thieu   INT NOT NULL DEFAULT 0,
    mo_ta           TEXT,
    hinh_anh        VARCHAR(255),
    trang_thai      ENUM('kinh_doanh','ngung_kinh_doanh') NOT NULL DEFAULT 'kinh_doanh',
    ngay_tao        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_sp_gia  CHECK (gia_nhap >= 0 AND gia_ban >= 0),
    CONSTRAINT chk_sp_ton  CHECK (ton_kho >= 0 AND ton_toi_thieu >= 0),
    FOREIGN KEY (danh_muc_id)    REFERENCES danh_muc(id),
    FOREIGN KEY (don_vi_tinh_id) REFERENCES don_vi_tinh(id),
    INDEX idx_sp_ten (ten_sp)
) ENGINE=InnoDB;

-- =====================================================================
-- NHÓM 3: NHẬP KHO & TỒN KHO (Module 3)
-- =====================================================================

-- PHIẾU NHẬP (phần đầu): 1 nhà cung cấp có nhiều phiếu nhập
CREATE TABLE phieu_nhap (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ma_phieu        VARCHAR(30) NOT NULL UNIQUE,     -- vd: PN20261020-001
    nha_cung_cap_id INT UNSIGNED NOT NULL,
    nguoi_dung_id   INT UNSIGNED NOT NULL,           -- thủ kho lập phiếu
    ngay_nhap       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tong_tien       DECIMAL(15,0) NOT NULL DEFAULT 0,
    ghi_chu         VARCHAR(255),
    FOREIGN KEY (nha_cung_cap_id) REFERENCES nha_cung_cap(id),
    FOREIGN KEY (nguoi_dung_id)   REFERENCES nguoi_dung(id),
    INDEX idx_pn_ngay (ngay_nhap)
) ENGINE=InnoDB;

-- PHIẾU NHẬP (các dòng): bảng trung gian giải quyết quan hệ NHIỀU-NHIỀU
-- giữa phiếu nhập và sản phẩm. Lưu giá nhập TẠI LÚC nhập.
CREATE TABLE chi_tiet_phieu_nhap (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phieu_nhap_id  INT UNSIGNED NOT NULL,
    san_pham_id    INT UNSIGNED NOT NULL,
    so_luong       INT NOT NULL,
    gia_nhap       DECIMAL(15,0) NOT NULL,
    CONSTRAINT chk_ctpn CHECK (so_luong > 0 AND gia_nhap >= 0),
    FOREIGN KEY (phieu_nhap_id) REFERENCES phieu_nhap(id) ON DELETE CASCADE,
    FOREIGN KEY (san_pham_id)   REFERENCES san_pham(id),
    UNIQUE KEY uq_ctpn (phieu_nhap_id, san_pham_id)   -- 1 sản phẩm chỉ 1 dòng/phiếu
) ENGINE=InnoDB;

-- PHIẾU XUẤT KHO NỘI BỘ: hàng hỏng, hết hạn, dùng nội bộ (không phải bán)
CREATE TABLE phieu_xuat (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ma_phieu      VARCHAR(30) NOT NULL UNIQUE,
    nguoi_dung_id INT UNSIGNED NOT NULL,
    ngay_xuat     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ly_do         ENUM('hang_hong','het_han','dung_noi_bo','khac') NOT NULL,
    ghi_chu       VARCHAR(255),
    FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id)
) ENGINE=InnoDB;

CREATE TABLE chi_tiet_phieu_xuat (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phieu_xuat_id  INT UNSIGNED NOT NULL,
    san_pham_id    INT UNSIGNED NOT NULL,
    so_luong       INT NOT NULL,
    CONSTRAINT chk_ctpx CHECK (so_luong > 0),
    FOREIGN KEY (phieu_xuat_id) REFERENCES phieu_xuat(id) ON DELETE CASCADE,
    FOREIGN KEY (san_pham_id)   REFERENCES san_pham(id),
    UNIQUE KEY uq_ctpx (phieu_xuat_id, san_pham_id)
) ENGINE=InnoDB;

-- PHIẾU KIỂM KÊ: đếm hàng thực tế, so với số trên hệ thống
CREATE TABLE phieu_kiem_ke (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nguoi_dung_id  INT UNSIGNED NOT NULL,
    ngay_kiem_ke   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ghi_chu        VARCHAR(255),
    FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id)
) ENGINE=InnoDB;

CREATE TABLE chi_tiet_kiem_ke (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phieu_kiem_ke_id  INT UNSIGNED NOT NULL,
    san_pham_id       INT UNSIGNED NOT NULL,
    so_luong_he_thong INT NOT NULL,
    so_luong_thuc_te  INT NOT NULL,
    -- cột tự tính: dương = thừa, âm = thiếu
    chenh_lech        INT GENERATED ALWAYS AS (so_luong_thuc_te - so_luong_he_thong) STORED,
    FOREIGN KEY (phieu_kiem_ke_id) REFERENCES phieu_kiem_ke(id) ON DELETE CASCADE,
    FOREIGN KEY (san_pham_id)      REFERENCES san_pham(id),
    UNIQUE KEY uq_ctkk (phieu_kiem_ke_id, san_pham_id)
) ENGINE=InnoDB;

-- THẺ KHO: mỗi lần số tồn thay đổi là MỘT dòng, giống sổ cái ngân hàng.
-- Nhờ bảng này mới xem được "lịch sử xuất nhập" của từng sản phẩm.
--   so_luong_thay_doi: số DƯƠNG = hàng vào, số ÂM = hàng ra
--   chung_tu_*: chỉ về phiếu/hóa đơn gây ra thay đổi (để truy ngược)
CREATE TABLE the_kho (
    id                 BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    san_pham_id        INT UNSIGNED NOT NULL,
    loai_giao_dich     ENUM('nhap_kho','ban_hang','tra_hang','xuat_kho',
                            'kiem_ke','huy_hoa_don') NOT NULL,
    so_luong_thay_doi  INT NOT NULL,
    ton_sau_giao_dich  INT NOT NULL,
    chung_tu_id        INT UNSIGNED,
    nguoi_dung_id      INT UNSIGNED NOT NULL,
    thoi_gian          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ghi_chu            VARCHAR(255),
    FOREIGN KEY (san_pham_id)   REFERENCES san_pham(id),
    FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id),
    INDEX idx_tk_sp_tg (san_pham_id, thoi_gian)
) ENGINE=InnoDB;

-- =====================================================================
-- NHÓM 4: BÁN HÀNG & HÓA ĐƠN (Module 4)
-- =====================================================================

CREATE TABLE khuyen_mai (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ma_khuyen_mai  VARCHAR(30) NOT NULL UNIQUE,
    loai           ENUM('phan_tram','so_tien') NOT NULL,
    gia_tri        DECIMAL(15,0) NOT NULL,        -- 10 (%) hoặc 20000 (đ)
    ngay_bat_dau   DATE NOT NULL,
    ngay_ket_thuc  DATE NOT NULL,
    trang_thai     ENUM('hoat_dong','tat') NOT NULL DEFAULT 'hoat_dong',
    CONSTRAINT chk_km CHECK (gia_tri > 0 AND ngay_ket_thuc >= ngay_bat_dau)
) ENGINE=InnoDB;

-- HÓA ĐƠN (phần đầu). khach_hang_id và khuyen_mai_id cho phép NULL
-- (khách vãng lai, không dùng mã).
-- Hủy hóa đơn = đổi trang_thai sang 'da_huy', KHÔNG xóa dòng.
CREATE TABLE hoa_don (
    id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ma_hoa_don            VARCHAR(30) NOT NULL UNIQUE,   -- vd: HD20261020-001
    khach_hang_id         INT UNSIGNED NULL,
    nguoi_dung_id         INT UNSIGNED NOT NULL,         -- nhân viên bán
    khuyen_mai_id         INT UNSIGNED NULL,
    ngay_lap              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tong_tien_hang        DECIMAL(15,0) NOT NULL DEFAULT 0,
    giam_gia              DECIMAL(15,0) NOT NULL DEFAULT 0,
    tong_thanh_toan       DECIMAL(15,0) NOT NULL DEFAULT 0,
    phuong_thuc_thanh_toan ENUM('tien_mat','chuyen_khoan','the') NOT NULL DEFAULT 'tien_mat',
    trang_thai            ENUM('hoan_thanh','da_huy') NOT NULL DEFAULT 'hoan_thanh',
    ghi_chu               VARCHAR(255),
    FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
    FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (khuyen_mai_id) REFERENCES khuyen_mai(id),
    INDEX idx_hd_ngay (ngay_lap),
    INDEX idx_hd_trang_thai (trang_thai)
) ENGINE=InnoDB;

-- HÓA ĐƠN (các dòng). Câu trả lời cho câu hỏi "giá đổi thì hóa đơn cũ sao?":
--   don_gia = giá bán TẠI THỜI ĐIỂM bán (chụp lại, không tham chiếu giá hiện tại)
--   gia_von = giá nhập TẠI THỜI ĐIỂM bán (để tính lợi nhuận chính xác)
CREATE TABLE chi_tiet_hoa_don (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    hoa_don_id   INT UNSIGNED NOT NULL,
    san_pham_id  INT UNSIGNED NOT NULL,
    so_luong     INT NOT NULL,
    don_gia      DECIMAL(15,0) NOT NULL,
    gia_von      DECIMAL(15,0) NOT NULL,
    CONSTRAINT chk_cthd CHECK (so_luong > 0 AND don_gia >= 0 AND gia_von >= 0),
    FOREIGN KEY (hoa_don_id)  REFERENCES hoa_don(id) ON DELETE CASCADE,
    FOREIGN KEY (san_pham_id) REFERENCES san_pham(id),
    UNIQUE KEY uq_cthd (hoa_don_id, san_pham_id)
) ENGINE=InnoDB;

-- TRẢ HÀNG: gắn với 1 hóa đơn gốc
CREATE TABLE phieu_tra_hang (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    hoa_don_id     INT UNSIGNED NOT NULL,
    nguoi_dung_id  INT UNSIGNED NOT NULL,
    ngay_tra       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ly_do          VARCHAR(255),
    tong_tien_hoan DECIMAL(15,0) NOT NULL DEFAULT 0,
    FOREIGN KEY (hoa_don_id)    REFERENCES hoa_don(id),
    FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id)
) ENGINE=InnoDB;

CREATE TABLE chi_tiet_tra_hang (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phieu_tra_hang_id INT UNSIGNED NOT NULL,
    san_pham_id      INT UNSIGNED NOT NULL,
    so_luong         INT NOT NULL,
    don_gia          DECIMAL(15,0) NOT NULL,
    CONSTRAINT chk_cttr CHECK (so_luong > 0),
    FOREIGN KEY (phieu_tra_hang_id) REFERENCES phieu_tra_hang(id) ON DELETE CASCADE,
    FOREIGN KEY (san_pham_id)       REFERENCES san_pham(id),
    UNIQUE KEY uq_cttr (phieu_tra_hang_id, san_pham_id)
) ENGINE=InnoDB;

-- =====================================================================
-- NHÓM 5: VIEW PHỤC VỤ BÁO CÁO (Module 5)
-- View = "câu SELECT được đặt tên", Python chỉ cần SELECT * FROM view.
-- =====================================================================

-- Sản phẩm dưới mức tồn tối thiểu -> cảnh báo + gợi ý nhập hàng
CREATE OR REPLACE VIEW v_canh_bao_ton_kho AS
SELECT sp.id, sp.ma_sp, sp.ten_sp, dm.ten_danh_muc,
       sp.ton_kho, sp.ton_toi_thieu,
       (sp.ton_toi_thieu - sp.ton_kho) AS thieu_so_voi_toi_thieu
FROM san_pham sp
JOIN danh_muc dm ON dm.id = sp.danh_muc_id
WHERE sp.trang_thai = 'kinh_doanh'
  AND sp.ton_kho <= sp.ton_toi_thieu;

-- Doanh thu theo ngày (chỉ tính hóa đơn hoàn thành)
-- Muốn theo tháng/năm: GROUP BY DATE_FORMAT(ngay, '%Y-%m') hoặc YEAR(ngay)
CREATE OR REPLACE VIEW v_doanh_thu_theo_ngay AS
SELECT DATE(hd.ngay_lap) AS ngay,
       COUNT(*)           AS so_hoa_don,
       SUM(hd.tong_thanh_toan) AS doanh_thu
FROM hoa_don hd
WHERE hd.trang_thai = 'hoan_thanh'
GROUP BY DATE(hd.ngay_lap);

-- Doanh thu + lợi nhuận gộp theo danh mục và ngày (cho biểu đồ tròn/cột)
CREATE OR REPLACE VIEW v_doanh_thu_theo_danh_muc AS
SELECT DATE(hd.ngay_lap) AS ngay,
       dm.id             AS danh_muc_id,
       dm.ten_danh_muc,
       SUM(ct.so_luong * ct.don_gia)                AS doanh_thu,
       SUM(ct.so_luong * (ct.don_gia - ct.gia_von)) AS loi_nhuan_gop
FROM chi_tiet_hoa_don ct
JOIN hoa_don  hd ON hd.id = ct.hoa_don_id
JOIN san_pham sp ON sp.id = ct.san_pham_id
JOIN danh_muc dm ON dm.id = sp.danh_muc_id
WHERE hd.trang_thai = 'hoan_thanh'
GROUP BY DATE(hd.ngay_lap), dm.id, dm.ten_danh_muc;

-- Top sản phẩm bán chạy (dùng thêm ORDER BY ... LIMIT ở tầng Python)
CREATE OR REPLACE VIEW v_ban_chay AS
SELECT sp.id, sp.ma_sp, sp.ten_sp,
       SUM(ct.so_luong)               AS tong_so_luong_ban,
       SUM(ct.so_luong * ct.don_gia)  AS doanh_thu
FROM chi_tiet_hoa_don ct
JOIN hoa_don  hd ON hd.id = ct.hoa_don_id
JOIN san_pham sp ON sp.id = ct.san_pham_id
WHERE hd.trang_thai = 'hoan_thanh'
GROUP BY sp.id, sp.ma_sp, sp.ten_sp;

-- =====================================================================
-- DỮ LIỆU MẪU (để có cái mà thử nghiệm ngay từ tuần 1)
-- Lưu ý: tài khoản Admin đầu tiên sẽ được tạo bằng code Python (băm mật
-- khẩu bằng bcrypt) ở tuần 1, nên KHÔNG chèn user ở đây.
-- =====================================================================

INSERT INTO vai_tro (ten_vai_tro, mo_ta) VALUES
 ('Admin',     'Toàn quyền, quản lý người dùng, xem lợi nhuận'),
 ('Thủ kho',   'Nhập kho, xuất kho, kiểm kê, quản lý sản phẩm'),
 ('Nhân viên bán hàng', 'Lập hóa đơn, tra cứu sản phẩm');

INSERT INTO don_vi_tinh (ten) VALUES
 ('Cái'), ('Cây'), ('Quyển'), ('Hộp'), ('Ram'), ('Cuộn');

INSERT INTO danh_muc (ten_danh_muc, mo_ta) VALUES
 ('Bút viết',      'Bút bi, bút chì, bút highlight...'),
 ('Vở - Sổ',       'Vở học sinh, sổ tay'),
 ('Giấy in',       'Giấy A4, A3, giấy note'),
 ('Dụng cụ văn phòng', 'Kẹp, ghim, băng keo, kéo...');

INSERT INTO nha_cung_cap (ten_ncc, so_dien_thoai, dia_chi) VALUES
 ('Công ty VPP Hà Nội',   '0900000001', 'Hà Nội'),
 ('Đại lý giấy Thăng Long','0900000002', 'Hà Nội');

INSERT INTO san_pham
 (ma_sp, ten_sp, danh_muc_id, don_vi_tinh_id, gia_nhap, gia_ban, ton_kho, ton_toi_thieu)
VALUES
 ('BUT001', 'Bút bi xanh 0.5mm',   1, 2, 3000,   5000,   120, 30),
 ('BUT002', 'Bút chì 2B',          1, 2, 2000,   4000,   8,   20),
 ('VO001',  'Vở kẻ ngang 96 trang',2, 3, 7000,   12000,  60,  20),
 ('GIAY01', 'Giấy A4 70gsm',       3, 5, 65000,  82000,  15,  10),
 ('DC001',  'Băng keo trong',      4, 6, 6000,   10000,  5,   10),
 ('DC002',  'Kẹp bướm 32mm (hộp)', 4, 4, 14000,  22000,  25,  8);
