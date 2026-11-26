# Quy chuẩn Khai thác, `FLATSHOT` từ `.stp` & Chuẩn hóa Block Chính hãng (ACADE)

Tài liệu hướng dẫn quy trình thực tế để lấy **dữ liệu hình học thật 1:1 của nhà sản xuất** (`.dwg`, `.dxf`, `.stp`/`.step`) và biến chúng thành **Smart ACADE Block** (Schematic Symbol & Panel Footprint) dùng tự động trong AutoCAD Electrical — **tuyệt đối không tự vẽ khối chữ nhật đại khái** và **không để 3D Solid làm nặng bản vẽ 2D**.

---

## 1. Nguồn Lấy Block & Dữ liệu CAx Chính hãng

Ưu tiên lấy theo thứ tự từ có sẵn trong máy đến cổng chính hãng:

1. **Gói Manufacturer Content đi kèm AutoCAD Electrical:**
   - Đường dẫn thư viện mặc định trên Windows:
     - Schematic (IEC-60617): `C:\Users\Public\Documents\Autodesk\Acade <ver>\Libs\iec-60617\`
     - Panel Footprint hãng (Siemens, Schneider, ABB, Eaton, Rittal, Phoenix Contact, Panduit...): `C:\Users\Public\Documents\Autodesk\Acade <ver>\Libs\panel\`
   - Cơ sở dữ liệu ánh xạ: `AeData\<lang>\Catalogs\default_cat.mdb` (Catalog) và `footprint_lookup.mdb` (ánh xạ `MFG + CAT → Footprint .dwg`).
   - *Lưu ý:* Nếu thiếu hãng khi cài đặt ban đầu, chạy lại bộ cài ACADE (*Add or Remove Features → Manufacturer Content*) để bổ sung.

2. **Cổng dữ liệu chính hãng & Thư viện mở:**
   - **Siemens:** SiePortal / CAx Download Manager (`https://sieportal.siemens.com/`) — tải được cả 2D Dimension Drawing (`.dxf`) lẫn 3D Model (`.stp`/`.step`).
   - **Schneider Electric / ABB / Eaton / Omron:** Trang Product Datasheet / CAD Downloads của từng mã hàng (`.dwg`, `.dxf`, `.stp`).
   - **Rittal (Vỏ tủ, Quạt, Điều hòa):** Rittal RiCAD 3D / Portal (`.dwg`, `.step`).
   - **Phoenix Contact / Weidmüller (Cầu đấu, Nguồn, Relay):** E-Catalog / CAE Data (`.dxf`, `.stp`).
   - **Cổng tổng hợp:** TraceParts, 3DfindIT, Cadenas, hoặc dùng skill `$step-parts` tải từ `step.parts`.

---

## 2. Luồng A — Chuẩn hóa khi Hãng đã cung cấp sẵn 2D (`.dwg` / `.dxf`)

File `.dwg`/`.dxf` tải từ web hãng thường là **hình học tĩnh (Dumb CAD)**, nhiều nét thừa, hatch nặng hoặc sai đơn vị. Bắt buộc làm sạch trước khi dùng:

1. Mở file `.dwg`/`.dxf` của hãng trong một **bản vẽ nháp riêng** (không mở thẳng vào bản vẽ dự án).
2. Kiểm tra đơn vị (`UNITS`): Chuyển về **`Millimeters`**, đo kiểm tra lại 1 kích thước chuẩn theo Datasheet (nếu file hãng xuất theo `cm` hoặc `m` thì `SCALE` về đúng `1:1 mm`).
3. Xóa bỏ khung tên hãng, đường kích thước thừa, text ghi chú không cần thiết và các lớp `HATCH` đặc gây nặng file.
4. Chạy **`OVERKILL`** để gộp các đoạn thẳng trùng lặp → **`PURGE`** để dọn sạch layer/block rác.
5. Chuyển toàn bộ nét về Layer `0` (hoặc Layer chuẩn `PNL_DEVICE` theo [cad-layers-and-colors.md](cad-layers-and-colors.md)) với màu `ByBlock` / `ByLayer`.
6. Đặt **`BASE`** (`Base Point`) chuẩn tại vị trí gá lắp thực tế (tâm rãnh gài `DIN Rail TS35` hoặc tâm lỗ bắt vít trên cùng bên trái).

---

## 3. Luồng B — Chiếu 2D từ File 3D `.stp` / `.step` bằng `FLATSHOT` (Dự án vẽ 2D)

Khi hãng **chỉ cung cấp file 3D (`.stp`, `.step`, `.iges`, `.sat`)** hoặc thiếu mặt chiếu hông (`Side View`) để kiểm tra chiều sâu tủ, thực hiện quy trình `FLATSHOT` trong chính AutoCAD Electrical:

1. **Nạp 3D vào bản vẽ nháp:**
   - Tạo 1 file `.dwg` trống (`UNITS = Millimeters`).
   - Gõ lệnh **`IMPORT`** → chọn file `.stp` / `.step` chính hãng (đợi AutoCAD chuyển thành `3D Solid`).
2. **Đặt góc nhìn chuẩn cần lấy hình chiếu:**
   - **Mặt trước (`Front View`):** Dùng để gắn lên tấm lắp (`+MAIN_PNL`) hoặc mặt cánh tủ (`+DOOR`).
   - **Mặt hông (`Left / Right View`):** Dùng cho *Mặt cắt hông (Side Section A-A)* để kiểm tra chiều sâu tủ và khoảng hở đóng cánh.
   - *(Mẹo: Nếu mô hình hãng xoay lệch trục, dùng `3DROTATE` chỉnh đúng hướng trước khi chiếu).*
3. **Chạy lệnh `FLATSHOT` tạo hình chiếu 2D:**
   - Gõ **`FLATSHOT`** trong không gian Model (ở chế độ *Orthographic / Parallel*, **tắt Perspective**).
   - Thiết lập hộp thoại `Flatshot`:
     - **Destination:** Chọn `Insert as new block` (hoặc `Export to a file`).
     - **Foreground lines:** Giữ nguyên nét thấy (`Color: ByBlock` hoặc `White`).
     - **Obscured lines (Nét khuất):** **Bỏ tích `Show`** để không xuất nét khuất bên trong linh kiện — giúp block 2D nhẹ, sạch và rõ nét khi in.
   - Nhấn **`Create`** và đặt block 2D vừa sinh ra cạnh mô hình 3D.
4. **Xóa khối 3D Solid gốc & Dọn nét trùng:**
   - **BẮT BUỘC xóa ngay khối `3D Solid` gốc** sau khi `FLATSHOT` xong (tuyệt đối không để `3D Solid` tồn tại trong `07_panel_layout.dwg` vì sẽ làm dung lượng file tăng hàng chục MB và gây giật lag Project Manager).
   - Chọn block 2D vừa tạo → **`EXPLODE`** → chạy **`OVERKILL`** để xóa các đường trùng đè lên nhau sinh ra từ mặt cong 3D → kiểm tra lại kích thước `W × H` khớp `1:1 mm` với Datasheet.
   - Đưa về Layer chuẩn (`0` / `PNL_DEVICE`) và đặt **`Base Point`** chuẩn.

---

## 4. "Thông minh hóa" thành Smart ACADE Block & Ánh xạ Database

Block 2D sau Luồng A hoặc Luồng B vẫn chưa có dữ liệu thông minh của ACADE. Cần gắn Attributes tùy theo mục đích sử dụng:

### A. Biến thành Smart Panel Footprint (cho `07_panel_layout.dwg`)
1. Mở **Symbol Builder (`AESYMBUILDER`)**:
   - Chọn hình học đã làm sạch ở Bước 2/3, chọn `Select Objects` và `Pick Point` (Base Point).
   - Trong mục **Attribute Template**, chọn **`Panel Footprint`** (hoặc `Panel Terminal` nếu là cầu đấu).
2. Gắn tối thiểu các Attribute bắt buộc:
   - `P_TAG1` (Tag thiết bị, khớp `TAG1` bên Schematic)
   - `MFG` (Tên hãng IN HOA: `SIEMENS`, `SCHNEIDER`, `ABB`...)
   - `CAT` (Mã đặt hàng chính xác)
   - `DESC1`, `DESC2`, `DESC3` (Mô tả song ngữ)
   - `ASSYCODE` (Mã phụ kiện ghép kèm nếu có)
   - `LOC` (Mã vị trí `+MAIN_PNL` / `+DOOR`)
3. Lưu file `.dwg` vào thư mục thư viện Panel của bạn (ví dụ: `Libs\panel\CUSTOM\SIEMENS\3VA1163_FRONT.dwg`).
4. **Ánh xạ vào `footprint_lookup.mdb`:**
   - Mở *Panel tab → Other Tools → **Footprint Database File Editor*** (hoặc chỉnh trực tiếp trong `footprint_lookup.mdb` theo bảng hãng `SIEMENS`, `SCHNEIDER`...).
   - Thêm dòng ánh xạ: `MFG = SIEMENS`, `CAT = 3VA1163-6GF42-0AA0` → trỏ tới file `3VA1163_FRONT.dwg` vừa tạo.
   - Từ đây, khi dùng *Panel tab → Insert Component (Icon Menu) → **Schematic List*** (`AEFOOTPRINT`), ACADE sẽ tự động chèn đúng block hãng `1:1`, đánh số `AEBALLOON` và xuất `Panel BOM` tự động.

### B. Biến thành Smart Schematic Symbol (nếu chuyển block hãng sang Sơ đồ nguyên lý)
1. Mở **`AESYMBUILDER`** → chọn loại Symbol (`Vertical` / `Horizontal`, nhóm `FAMILY` như `Q1`, `K1`, `A1`).
2. Gắn đủ: `TAG1` (hoặc `TAG2` nếu là Child), `DESC1-3`, `MFG`, `CAT`, `FAMILY`, `WDBLKNAM`.
3. Gắn chân đấu nối `TERM01`, `TERM02`... kèm **điểm bắt dây đúng hướng `X?TERM??`** (`X1`: Phải `0°`, `X2`: Trên `90°`, `X4`: Trái `180°`, `X8`: Dưới `270°`) để `AEWIRE` tự cắt dây khi chèn.
4. Lưu đúng quy ước tên file `[V/H][FAMILY][1/2]_<mo_ta>.dwg` và đưa vào Icon Menu qua **`AEMENUWIZ`**.
