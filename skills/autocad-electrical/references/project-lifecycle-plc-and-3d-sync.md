# Quản lý Vòng đời Dự án, CSDL ACADE, Đồng bộ PLC 2 Chiều & Tích hợp Cơ–Điện 3D (Inventor)

Tài liệu chuẩn hóa cấp **Senior / Lead Engineer** cho 4 trụ cột nâng cao:
1. Quản lý Template dự án (`.dwt` / `Copy Project`), Quản lý thay đổi (`ECO`, `Mark/Verify`, `Retag`, `Title Block Update`).
2. Quản trị Cơ sở dữ liệu ACADE (`Catalog Browser`, `Pin List`, `Footprint Lookup`, `Missing Catalog Data`, `Automatic Reports`).
3. Đồng bộ 2 chiều giữa **AutoCAD Electrical ↔ TIA Portal / GX Works** (`Single Source of Truth I/O Assignment`, `F-I/O PROFIsafe`).
4. Liên kết Cơ–Điện 3D (**Autodesk Inventor Electromechanical Link**, `Sheet Metal Busbar`, `Cable & Harness`).

---

## 1. Khởi tạo Dự án Mẫu (`.dwt` & `Copy Project`) & Quản lý Thay đổi (ECO / Revision)

### A. Khởi tạo Dự án Mới từ Template Chuẩn (Không cấu hình tay từ đầu)
1. **File Bản vẽ Mẫu ([templates/TEMPLATE_IEC_A3.dwt](../templates/TEMPLATE_IEC_A3.dwt)):**
   - **Đối với Trang Sơ đồ nguyên lý, SLD, PLC I/O & Terminal (`01..06`, `09` — Tỷ lệ `1:1`):** Đặt block cấu hình ẩn **`WD_M`** (chuẩn `IEC-60617`, `X-Zones 0..9`, Tag `%S%F%N`, Wire Number `%S%N`), Khung bản vẽ ISO 5457 A3 (`420 × 297 mm`), Lưới chia cột `X-Zones (0..9)` và block Khung tên **`TITLE_BLOCK_A3_BILINGUAL`** (thuộc tính `WD_TB` khớp 100% với [templates/default_iec_bilingual.wdt](../templates/default_iec_bilingual.wdt)) **ngay trong `Model Space` ở tỷ lệ `1:1 mm`** (`$INSUNITS = 4`). Toàn bộ Wire Layers (`PWR_L1_BK_2.5`, `CTRL_24VDC_DBU_0.75`...) đã được đăng ký sẵn XDATA (`Color` + `Size`) trong `WD_M`.
   - **Đối với Trang Bố trí Mặt tủ & Gia công Thanh cái (`07_panel_layout`, `08_busbar_fabrication` — Tỷ lệ `1:20`, `1:10`, `1:2.5`):** `Model Space` chứa hình học cơ khí `1:1 mm` + `DIMENSION` gốc AutoCAD (`ISO_MM`, `dimlfac = 1.0`); `Paper Space (Layout ISO_A3)` chứa Khung bản vẽ A3, `TITLE_BLOCK_A3_BILINGUAL` (`WD_TB`) và `VIEWPORT` khóa đúng tỷ lệ ISO 5455.
2. **Quy trình `Copy Project` (`AECOPYPROJECT` / `acade_project_init`):**
   - Khi bắt đầu dự án mới, khởi tạo từ dự án mẫu chuẩn ([templates/TEMPLATE_PROJECT.wdp](../templates/TEMPLATE_PROJECT.wdp)) kèm [scripts/seed_acade_databases.py](../scripts/seed_acade_databases.py) để kế thừa toàn bộ thiết lập *Project Properties*, đường dẫn thư viện `iec-60617`, nhóm báo cáo [templates/project_master_reports.rgf](../templates/project_master_reports.rgf) và Scratch Database `<project>.mdb`.

### B. Quy trình Cập nhật Khung tên (`Title Block Update` – `AEUPDATETITLEBLOCK`)
1. Vào *Project Manager → Chuột phải vào tên Project → Descriptions*: Nhập các dòng `LINE1..LINE10` (Tên dự án, Khách hàng, Tên tủ, Điện áp, Người vẽ, Người kiểm, Phê duyệt, Phiên bản `REV`).
2. Chạy *Project tab → Other Tools → Title Block Update* (`AEUPDATETITLEBLOCK`):
   - Tích chọn các trường `LINE1..LINE10`, `Sheet (%S)`, `Sheet Maximum (%N)`, `Drawing (%D)` và `Plot Date`.
   - Chọn **`Do All`** (Cập nhật toàn bộ dự án) và tích **`Resequence sheet %S values`** từ `1` mỗi khi thêm, bớt hoặc đổi thứ tự trang.

### C. Quy trình 10 Bước Xử lý Thay đổi Kỹ thuật (ECO / Revision B → C) Chuẩn Lead Engineer
> **Cấm tuyệt đối:** Khi đổi dòng module PLC (VD: thay 4 module DI16 bằng 2 module DI32) hoặc đổi thiết bị nhiều cực, **cấm dùng `Edit Component` sửa mã `CAT` bằng tay trên từng trang** (sẽ làm sai lệch số kênh parametric, nhân đôi dòng BOM, lệch địa chỉ PLC và dư cầu đấu).

| Bước | Hành động trong ACADE & Quản lý Dự án | Mục đích Kỹ thuật |
| :---: | :--- | :--- |
| **0** | **Phát lệnh Dừng thi công vùng ảnh hưởng (Hold Notification)** tại xưởng + Lập phiếu **ECO** (`REV C`) + **Backup dự án** (`Zip Project` hoặc `git tag rev-b`). | Ngăn xưởng đi dây sai tiếp; lưu mốc chuẩn để diff báo cáo. |
| **1** | Chạy **Mark/Verify DWGs (`AEMARK` / `AEVERIFY`)** (*Project tab → Other Tools → Mark/Verify Drawings*): Chạy `Mark` trước khi sửa (hoặc `Verify` trên bản snapshot `REV B` để phát hiện mọi chỉnh sửa tự phát trên bản vẽ). | Khoanh vùng chính xác các trang/thiết bị thay đổi để khoanh mây Revision (`REVCLOUD`). |
| **2** | Mở **PLC Database File Editor (`AEPLCDB`)** và **Catalog Browser (`AECATALOG`)**: Kiểm tra/thêm mã module mới (VD: `6ES7521-1BL00-0AB0` DI32) với đủ số kênh, `Pin List` và kích thước `Footprint`. | Đảm bảo dữ liệu gốc trong CSDL đúng trước khi sinh hình học. |
| **3** | **Xóa module Parametric cũ** (`AEDELCOMP`) trên bản vẽ và **chèn lại bằng `Insert PLC (Parametric)`** hoặc chạy lại **`Spreadsheet to PLC I/O Utility`** từ bảng `I/O Assignment` đã cập nhật. | Đồng bộ cấu trúc chân, địa chỉ `%I/%Q` và thuộc tính `CAT` từ CSDL. |
| **4** | Đấu nối lại dây vào kênh mới → Chạy **Project-wide Update/Retag (`AERETAG`)** (*Project tab → Project Tools → Update/Retag*): Tích chọn `Component Retag`, `Wire Number Update` (giữ Fixed Wires) và `Cross-Reference Update`. | Triệt tiêu lỗi trùng số dây, đánh lại tag và cập nhật tham chiếu chéo toàn dự án. |
| **5** | Mở **Terminal Strip Editor (`AETSE`)**: Xóa các chân cầu đấu dư (VD: giảm từ 64 xuống 32 chân trên `-X2`), đánh số lại, cập nhật Jumper và nhấn **Rebuild** bảng `Terminal Plan` trên trang `09`. | Đồng bộ cầu đấu thực tế với sơ đồ mới. |
| **6** | Chạy **`AEAUDIT` + `AEDWGAUDIT` + báo cáo `Missing Catalog Data`** cho đến khi `0 Errors`. Xuất BOM `REV B` và `REV C` ra `.xlsx` để **diff định lượng** (đảm bảo module cũ = `0`, module mới = đúng số lượng). | Kiểm chứng dữ liệu BOM bằng con số trước khi phát hành. |
| **7** | **Đồng bộ 2 chiều với TIA Portal / GX Works** (theo Mục 3 bên dưới): Xuất bảng `PLC I/O Address & Description` từ ACADE → cập nhật `Hardware Configuration` và `PLC Tag Table` trong TIA Portal → Đối chiếu khớp 100% số lượng tag. | Duy trì một nguồn sự thật duy nhất (Single Source of Truth) giữa Điện và Lập trình. |
| **8** | Khoanh mây **Revision Cloud** tại các vị trí thay đổi, ghi dòng lịch sử vào `Revision Block`, chạy **`Title Block Update`** nâng lên `REV C` và chạy **`Automatic Reports`** để cập nhật toàn bộ các bảng `Put on Drawing` (chọn `Update Existing Table`, không chèn đè bảng thứ 2). | Hồ sơ phát hành đồng bộ, truy vết rõ ràng. |
| **9** | Xuất **Bảng đối chiếu thay đổi đấu dây (`From/To Wire List Diff REV B → REV C`)** gửi xưởng (liệt kê rõ: *Dây cần tháo* vs *Dây đấu lại*) + Cập nhật `FAT Checklist` + Commit & gắn tag `rev-c`. | Giảm tối đa thời gian sửa tủ tại xưởng, tránh tháo nhầm dây đúng. |

---

## 2. Quản trị Cơ sở Dữ liệu (`Catalog`, `Pin List`, `Footprint` & `Automatic Reports`)

1. **Chuẩn hóa Tên Hãng (`MFG`), `_PINLIST` Nâng cao (`Form C / SPDT`), `WDBLKNAM` & `ASSYCODE` ([templates/catalog_master_seed.csv](../templates/catalog_master_seed.csv)):**
   - Tên hãng trong cột `MFG` **bắt buộc viết IN HOA thống nhất 100%** (`SIEMENS`, `SCHNEIDER`, `ABB`, `MITSUBISHI`, `OMRON`, `PHOENIX CONTACT`, `WEIDMULLER`, `RITTAL`).
   - **Cấu hình `_PINLIST` chuẩn (bao gồm tiếp điểm chuyển mạch `Form C` mã `4`):**
     - `1` = Thường mở (`NO`, VD: `1,13,14`)
     - `2` = Thường đóng (`NC`, VD: `2,21,22`)
     - `4` = **Tiếp điểm chuyển mạch chung chân (`Form C / SPDT`, cú pháp `4,COM,NC,NO`, VD: `4,11,12,14` hoặc `4,9,1,5;4,10,2,6`)** — bắt buộc dùng mã `4` cho Relay trung gian, tiếp điểm báo lỗi Biến tần / Transmitter cân để ACADE hiểu chung chân `COM` (`11`) và tự động chặn lỗi khi vẽ vượt số cặp tiếp điểm.
   - **Khóa bảng tra cứu bằng `WDBLKNAM` & Mô tả chân `TERMDESCxx`:**
     - Trên các Custom Symbol đặc thù (VD: `VA1_WEIGH_TRANS.dwg`), khai báo thuộc tính **`WDBLKNAM`** để khóa đúng bảng Catalog khi tra cứu, và gắn **`TERMDESC01`, `TERMDESC02`...** (`EXC+`, `EXC-`, `S+`, `S-`, `SIG+`, `SIG-`, `IOUT+`, `IOUT-`) đi kèm `TERM01..` để bản vẽ và báo cáo Terminal tự động hiển thị tên chức năng chân.
   - **Tự động trích xuất `Load Schedule` từ `RATING1..12`:**
     - Điền sẵn thông số điện vào thuộc tính **`RATING1` (`kW/W`), `RATING2` (`In A`), `RATING3` (`3P/1P/24VDC`), `RATING4` (`cosφ`)** trong Catalog ([templates/catalog_master_seed.csv](../templates/catalog_master_seed.csv)) để xuất tự động bảng **Load Schedule** qua `AEREPORT` → `Components` (`Put on Drawing` / `.xlsx`) thay vì tính tay trên Excel rời.
   - **Linh kiện ghép nhiều phần (`Multi-part Sub-assemblies` – `ASSYCODE` & `Multiple Catalog`):**
     - Gán mã ghép **`ASSYCODE`** trong Catalog Database (VD: Transmitter cân đi kèm `EMC_GLAND_M16_SKINTOP;SHIELD_CLAMP_SK14`; Contactor đi kèm tiếp điểm phụ + Diode) để **1 ký hiệu trên sơ đồ tự động xuất ra đầy đủ tất cả các mã phụ kiện đi kèm trong BOM và Footprint**.
2. **Cầu đấu Nhiều tầng (`Multi-level`), Phân cực `Internal/External` & `Wire Number Change` trong `AETSE`:**
   - **Gộp tầng (`Associate Terminals`) & Phụ kiện:** Dùng `Associate Terminals` trong `AETSE` gộp 3 tầng (`+24VDC`, `0VDC`, `Signal/Shield`) vào 1 thân cầu đấu vật lý (`-X3`); chèn đủ `End Cover Plate`, `End Clamp`, `Partition Plate`, `Jumper Bridge`.
   - **Phân định phía đấu dây `Internal (+MAIN_PNL)` vs `External (+FIELD)`:** Trong `AETSE` (*Wire Destination*), ấn định rõ cực trong tủ (`Internal`: nối về PLC/Transmitter `+MAIN_PNL`) và cực ngoài hiện trường (`External`: nối ra cáp cảm biến `+FIELD`) để bảng `Terminal Plan` chỉ dẫn chính xác hai phía của hàng cầu đấu.
   - **Cầu đấu Cầu chì / Dao cách ly có Đổi số dây (`Terminal with Wire Number Change`):** Với cầu đấu cầu chì (`Fuse Terminal` cấp nguồn 24VDC) hoặc cầu đấu ngắt mạch (`Disconnect Terminal`), bắt buộc dùng symbol cầu đấu loại **`Wire Number Change` (`HT1_...` / `VT1_...`)** để ACADE tự động cấp số dây mới phía sau cầu chì.
3. **Cơ sở dữ liệu Hình chiếu Thiết bị (`Footprint Lookup`) & Quy chuẩn Bắt buộc Lấy Dữ liệu CAx Chính hãng (1:1 Manufacturer Data):**
   - **❌ CẤM TUYỆT ĐỐI VẼ HÌNH CHỮ NHẬT TRỐNG RỖNG / TỰ CHẾ ĐẠI KHÁI LÀM FOOTPRINT:**
     - Các khối hộp chữ nhật (Bounding box) hoặc hình khối ước lượng tự tạo chỉ được dùng ở bước phác thảo ý tưởng sơ bộ (Concept Study). Khi lập hồ sơ thiết kế chi tiết (Detailed Design) và bản vẽ chế tạo tủ (Panel Layout), **tất cả Footprint thiết bị phải khớp 1:1 với kích thước cơ khí thật của nhà sản xuất**.
     - Vẽ sai hoặc ước lượng kích thước sẽ dẫn đến thảm họa chế tạo: đột dập sai lỗ ốc bắt plate, sai biên dạng khoét mặt tủ (escutcheon cut-out), nắp che cánh tủ bị cấn tay gạt, không đủ khoảng hở cách điện / thoát khí (arc chute clearance) hoặc không đủ bán kính uốn cáp.
   - **Nguồn Lấy Dữ liệu CAx Chính hãng Chuẩn Quốc tế:**
     - **Siemens SiePortal / CAx Download Manager (https://sieportal.siemens.com/):** Tải trực tiếp file **2D Dimension Drawing (`.dxf`)** (gồm đủ 3 góc nhìn: Mặt trước Front, Mặt cắt bên Side, và Tọa độ đột lỗ Drilling Plan) hoặc file **3D Model (`.stp` / `.step`)** cho từng mã Part Number (VD: `3VA1163-6GF42-0AA0`, `6SL3210-1KE18-8UF2`, `6ES7511-1AK02-0AB0`).
     - **Cổng dữ liệu mở:** *EPLAN Data Portal*, *TraceParts*, *3DfindIT*, *Cadenas*, *Ultra Librarian*, hoặc skill `$step-parts` tải từ `step.parts`.
   - **Quy trình Chi tiết cho Dự án 2D (`IMPORT .stp` → `FLATSHOT` → `OVERKILL` → `AESYMBUILDER` → `footprint_lookup.mdb`):** Xem hướng dẫn từng bước tại [manufacturer-blocks-and-flatshot.md](manufacturer-blocks-and-flatshot.md).
   - **Quy chuẩn 5 Chi tiết Bắt buộc Phải thể hiện trên 2D Footprint:**
     1. **Biên dạng Thân vỏ (Outer Dimensions & Escutcheon):** Đúng chiều rộng $W$, chiều cao $H$, chiều sâu $D$, và gờ nổi luồn qua mặt che tủ (escutcheon collar, VD: $70 \times 92\text{ mm}$ cho MCCB 3VA1).
     2. **Cơ cấu Vận hành (Operating Mechanism):** Tay gạt đóng/cắt (Toggle lever / Rotary handle), nút ấn thử cơ khí (Push-to-trip), núm chỉnh dòng (Thermal/Magnetic dials $I_r, I_i$), màn hình LCD (BOP-2, CPU display).
     3. **Cực Đấu dây & Vách Ngăn (Terminals & Phase Barriers):** Thể hiện đúng số cực (3P hay 4P), khoảng cách bước cực ($25.4\text{ mm}$ cho 3VA1 160A), nắp che chống chạm giật IP2X (Terminal covers).
     4. **Điểm Bắt Vít Định vị (Mounting Screw Hole Pattern):** Tọa độ chính xác các lỗ khoan bắt ốc tấm plate (VD: 4 lỗ $\varnothing 4.5\text{ mm}$ tại khoảng cách $76.2 \times 111\text{ mm}$ cho 3VA11 4P).
     5. **Phân định Rạch ròi Phương thức Gá lắp (Mounting Method):**
        - **Bắt vít trực tiếp lên Plate (Base / Screw Mounting):** MCCB tổng công suất lớn (3VA1/3VA2), Biến tần nặng (G120C), Khối Domino công suất lớn.
        - **Gài thanh ray DIN rail 35mm (DIN Rail Mounting):** MPCB (3RV), Contactor (3RT), Cầu chì (3NW), Bộ nguồn (SITOP), Rơ-le an toàn (3SK1), Cầu đấu tín hiệu/cảm biến (Phoenix Contact).
        - **Ray nhôm định hình chuyên dụng của hãng:** Ray nhôm S7-1500 / S7-1200 của Siemens.
   - **Nguyên tắc "1 Mô hình 3D Gốc → Chiếu 3 Hình chiếu 2D (`Front / Mounting Plate / Side Section`)":**
     - Khi dựng tủ bằng công cụ CAD/Python, mọi thiết bị trên tấm lắp (`+MAIN_PNL`) và trên cánh tủ (`+DOOR`), thanh DIN rail (`35×7.5 mm` có lỗ đột), máng cáp xẻ rãnh (`Wire Duct`), thanh cái đồng, sứ đỡ `SM-40` và tấm che `IP2X` phải được định nghĩa trong **cùng một không gian tọa độ 3D $(X, Y, Z)$ duy nhất** với đầy đủ chi tiết hình học.
     - Bản vẽ 2D `07_panel_layout.dxf` phải được **chiếu trực giao (Orthographic Projection)** trực tiếp từ mô hình 3D đó ra 3 hình chiếu (`Front Door`, `Mounting Plate`, `Side Section A-A`) ở **tỷ lệ thật `1:1 mm` (`scale = 1.0`) trong Model Space** (trình bày khung A3 qua Paper Space `Viewport` và dùng 100% thực thể `DIMENSION` gốc của AutoCAD) để **tọa độ, số đo Dim và hình dáng thiết bị giữa 2D và 3D khớp nhau tuyệt đối 100%**.
   - Sử dụng công cụ **DIN Rail** và **Wire Duct** trong `AEFOOTPRINT` để vẽ thanh ray và máng cáp có thuộc tính catalog (tự động tính tổng chiều dài thanh ray/máng vào `Panel BOM`).
   - Sử dụng **Panel Wire Annotation** (*Panel tab → Other Tools → Wire Annotation*) khi cần in thông tin điểm đấu nối dây trực tiếp cạnh từng Footprint thiết bị.
4. **Báo cáo Kiểm tra Thiếu Mã (`Missing Catalog Data`) & Xuất Báo cáo Hàng loạt (`Automatic Reports`):**
   - Trước khi xuất BOM, chạy *Reports tab → Schematic → Reports* (`AEREPORT`) → chọn **`Missing Catalog Data`** để liệt kê mọi thiết bị trên sơ đồ còn trống cột `MFG`/`CAT`.
   - Thiết lập **Report Grouping (`.rgf`)** trong **Automatic Reports** (*Reports tab → Schematic → Automatic Reports*) gồm: `Bill of Materials`, `Missing Catalog Data`, `From/To Wire List`, `Cable Summary`, `PLC I/O Component Connection` để xuất/cập nhật toàn bộ báo cáo chỉ bằng 1 lệnh duy nhất.
5. **Tự động hóa Sơ đồ Nguyên lý (`Circuit Builder`, `User Circuits`, `Copy Circuit` & `Scoot`):**
   - **Không chèn rời từng symbol cho các mạch lặp lại:** Sử dụng **Circuit Builder (`AECIRCUITBUILDER` – *Schematic tab → Insert Components → Circuit Builder*)** kết hợp bảng cơ sở dữ liệu `ace_circuit_builder.xls` để phần mềm tự động dựng mạch động lực + điều khiển, tự tra mã `MCCB / Contactor / OLR` và tiết diện dây theo công suất động cơ (`kW`, `400VAC`).
   - **Đóng gói 5 Cụm Mạch Mẫu (`Save Circuit to Icon Menu` / `WBlock Circuit`):**
     1. `CIR_01_MOTOR_DOL`: Khởi động trực tiếp DOL + Bảo vệ quá tải MPCB/OLR.
     2. `CIR_02_MOTOR_YD`: Khởi động Sao–Tam giác (`K_Main`, `K_Delta`, `K_Star` + Timer + Khóa chéo cơ/điện).
     3. `CIR_03_VFD_G120`: Biến tần + Bộ lọc EMI + Cuộn kháng AC/DC + Điện trở xả + Cáp động cơ bọc giáp nối đất 2 đầu $360^\circ$.
     4. `CIR_04_PSU_24VDC_PELV`: Bộ nguồn 24VDC nối đất `0VDC -> PE` (`Grounded PELV`) + 3 nhánh MCB riêng (`CPU/HMI`, `DI/Sensor`, `DO/Relay`).
     5. `CIR_05_SAFETY_3SK1`: Safety Relay 2 kênh (`3SK1`/`PNOZ`) + Nút dừng khẩn `E-Stop` + Mạch hồi tiếp `Feedback Loop Y1–Y2`.
   - **Thao tác nhanh trên mạch (`AECOPYCIRCUIT`, `AESCOOT` & Bó dây `AEMULTIWIRE` / `AEFANIN`):**
     - Dùng **`Copy Circuit`** (`AECOPYCIRCUIT`) để nhân bản nhanh các nhánh tải tương tự kèm tự động đánh lại `TAG` và số dây mới; dùng **`Scoot`** (`AESCOOT`) để trượt thiết bị dọc theo dây dẫn.
     - Với bó dây mật độ cao (Encoder vi sai 8–10 lõi, Load cell 6 dây, bus truyền thông), dùng **`Multi-Wire` (`AEMULTIWIRE`)** và **`Fan In/Out` (`AEFANIN` / `AEFANOUT`)** (*Schematic tab → Insert Wires/Wire Numbers → Fan In/Out*) để gom các lõi dây thành 1 đường bus gọn gàng có nhãn giữa các cụm và bung ra tại đầu cầu đấu.
6. **Sửa Dữ liệu Hàng loạt qua Excel (`AEEXPORT` / `AEIMPORT`) & Thay thế Block (`AESWAPBLOCK`):**
   - **Chu trình Sửa Hàng loạt (`Export to Spreadsheet → Excel → Update from Spreadsheet`):**
     - Khi cần đổi hàng loạt hãng thiết bị (VD: đổi 40 MCB từ Schneider sang Siemens) hoặc dịch hàng loạt mô tả `DESC1/DESC2`, `LOC`: Chạy *Import/Export Data tab → Export → **To Spreadsheet*** (`AEEXPORT`) → chọn `Components` → sửa nhanh trong Excel bằng công thức/Find-Replace → chạy *Import/Export Data tab → Import → **From Spreadsheet*** (`AEIMPORT`) để cập nhật tự động toàn bộ các trang `.dwg` mà không cần mở từng bản vẽ.
   - **Cập nhật / Thay thế Block Hàng loạt (`Swap/Update Block` – `AESWAPBLOCK`):**
     - Khi nâng cấp đồ họa của 1 Custom Symbol (thêm chân, đổi vị trí chữ) hoặc cập nhật khung tên `Title Block`, dùng *Schematic tab → Edit Components → **Swap/Update Block*** (`AESWAPBLOCK`) → chọn `Update a Block` (Project-wide) để thay thế đồng loạt trên mọi trang mà **giữ nguyên 100% giá trị `TAG`, `CAT`, `DESC`, `TERM` hiện có**.

---

## 3. Quy trình Đồng bộ 2 Chiều AutoCAD Electrical ↔ TIA Portal / GX Works

### A. Kiến trúc Phần cứng & Quy tắc Slot S7-1500 / S7-1200
- **Siemens S7-1500:**
  - `Slot 0`: Bộ nguồn hệ thống (`PS`, nếu dùng).
  - `Slot 1`: **CPU** (`CPU 1511-1 PN` .. `CPU 1518F-4 PN/DP`).
  - `Slot 2 trở đi`: Các module mở rộng (`DI`, `DQ`, `AI`, `AQ`, `F-DI`, `F-DQ`, `CM/CP`). **Tuyệt đối không** khai báo module I/O vào `Slot 1` trong file import CSV/Excel của ACADE.
- **Mạch An toàn (`Safety / PROFIsafe`):**
  - Với PLC tiêu chuẩn (Standard CPU): Nút dừng khẩn `E-STOP` 2 kênh phải đấu vào **Safety Relay** (`3SK1` / `PNOZ`); ngõ vào `DI` thường của PLC chỉ nhận **tiếp điểm phụ báo trạng thái (`Auxiliary Feedback`)** từ Safety Relay.
  - Với Fail-Safe PLC (`CPU 151xF`): Nút `E-STOP` 2 kênh đấu vào module **Fail-Safe Digital Input (`F-DI`, VD: `6ES7526-1BH00-0AB0`)** sử dụng ngõ ra xung kiểm tra chập dây (`VS0`, `VS1`), dây vẽ trên Layer `SAFE_24VDC_YE_0.75`.

### B. Quy trình Đồng bộ Hai Chiều Tự động 1-Click & AutomationML (`default_plc_io.wdi` & `sync_tia_tags.py`)
1. **Chiều từ TIA Portal sang AutoCAD Electrical (`tia-to-acade` & `Spreadsheet to PLC I/O Utility`):**
   - Chuyển đổi bảng `PLC Tags` xuất từ TIA Portal sang CSV chuẩn của ACADE bằng lệnh:
     ```powershell
     python scripts/sync_tia_tags.py --mode tia-to-acade --in tia_plc_tags.csv --out acade_plc_import.csv
     ```
   - Mở *Schematic tab → Insert Components → PLC → **Spreadsheet to PLC I/O Utility***, nạp trực tiếp file cấu hình [templates/default_plc_io.wdi](../templates/default_plc_io.wdi) để ACADE tự động sinh toàn bộ các trang sơ đồ module PLC.
2. **Chiều từ AutoCAD Electrical sang TIA Portal & `AutomationML (.aml)` (`acade-to-tia` & `export-aml`):**
   - Đọc trực tiếp file CSV/AEEXPORT từ ACADE để xuất bảng `PLC Tags` cho TIA Portal (tự lọc bỏ kênh phụ `1oo2 F-DI` như `:CH2` / `%I11.0`, tự suy luận `Bool`/`Int`/`DInt`) hoặc xuất cấu hình phần cứng Rack/Slot sang chuẩn mở **`AutomationML (.aml)`** cho TIA Selection Tool / TIA Portal Openness:
     ```powershell
     python scripts/sync_tia_tags.py --mode acade-to-tia --in templates/plc_io_import_template.csv --out tia_plc_tags.csv
     python scripts/sync_tia_tags.py --mode export-aml --in templates/plc_io_import_template.csv --out plc_hardware.aml
     ```

---

## 4. Liên kết Cơ–Điện 3D (Autodesk Inventor Electromechanical Link) & Phạm vi Công cụ

Tuỳ theo quy mô dự án và công cụ sẵn có trong workspace, áp dụng 1 trong 2 luồng chuẩn sau:

### Luồng 1: Liên kết Cơ–Điện 3D Chuẩn Hãng (`AutoCAD Electrical ↔ Autodesk Inventor Professional`)
Khi dự án yêu cầu thiết kế khung/vỏ tủ 3D, trải phẳng tôn chấn (Sheet Metal), uốn thanh cái 3D và đi dây 3D:
1. **Định tuyến Thứ tự Đi dây (`Wire Sequence` – `AEWIRESEQ`), Thiết lập `.emx` (`AEEMLINK`) & Khớp chân `Pin Mapping`:**
   - Dùng *Schematic tab → Edit Wires/Wire Numbers → **Edit Wire Sequence*** (`AEWIRESEQ`) để ấn định thứ tự đấu dây điểm-nối-điểm (`DirectTo`).
   - Tạo file liên kết chung `.emx` bằng lệnh **`AEEMLINK` thật của Autodesk** nối trực tiếp Project `.wdp` của ACADE với Assembly `.iam` của Inventor (**cấm tuyệt đối** dùng Python `ElementTree` tự chế thẻ XML `.emx` giả lập với chiều dài cắt dây bịa sẵn).
   - **Quy tắc Vàng "Khớp chân 3D" (`RefDes ↔ TAG` & `Harness Pin ↔ TERMxx`):** Trong mỗi file part 3D (`.ipt`) trên Inventor, thuộc tính **`RefDes`** phải trùng khớp 100% với `TAG` của ACADE (VD: `-K1`, `-A1`, `-X3`) và tên các điểm **`Place Pin` (`Harness Pin Name`)** trên mô hình 3D phải trùng khớp chính xác từng ký tự với giá trị thuộc tính **`TERM01`, `TERM02`...** trên symbol ACADE (VD: `13`, `14`, `EXC+`, `S+`, `11`, `12`).
2. **Thiết kế Khung Vỏ tủ (`Frame Generator`), Busbar 3D (`Sheet Metal`) & Liên kết `iProperties`:**
   - Dùng **Inventor Frame Generator** dựng hệ khung xương tủ đứng ghép module; dùng **Inventor Sheet Metal** dựng vỏ tủ và thanh cái đồng (`Copper E-Cu`, `K-Factor = 0.42`), đột lỗ đồng trục với đầu cực ACB/MCCB/CT/Sứ đỡ và chạy **`Create Flat Pattern`** xuất `.dxf`.
   - Liên kết tham số `iProperties` (`W×H×D`, `Mass`, tọa độ lỗ khoét cánh tủ) từ Assembly 3D sang bảng `Enclosure Data Block` và `Door Cutout View` trên trang `07_panel_layout.dwg`.
3. **Đi dây 3D (`Inventor Cable & Harness`), `Harness Segments` & `Virtual Parts`:**
   - Định nghĩa các đoạn đường dẫn **`Harness Segments`** dọc theo lòng máng cáp (`Wire Duct`) 3D để khi chạy `Auto Route` từ file `.emx`, phần mềm tính chính xác độ đầy máng cáp (**`Duct Fill % ≤ 60–65%`**) và chiều dài cắt dây (`Wire Cut Length`).
   - Gán **`Virtual Parts`** (Đầu cosse kim/chĩa, Ống lồng đánh số `Ferrule`, Ốc siết cáp `EMC Cable Gland`, Kẹp giáp `Shield Clamp`) vào các sợi dây/cáp trong `.emx` để bản vẽ trải bộ dây (**Harness Nailboard Drawing**) và `BOM` xuất ra đầy đủ 100% phụ kiện thi công.

### Luồng 2: Quy trình 2D / Code-CAD Tự động Hàng loạt (`--from-csv`)
Khi làm việc thuần trên AutoCAD Electrical kết hợp bộ công cụ Python/CAD trong workspace:
1. Sử dụng script [scripts/generate_busbar_dxf.py](../scripts/generate_busbar_dxf.py) ở chế độ **chạy hàng loạt từ CSV (`--from-csv`)** để tự động đọc bảng `Busbar Cut List` (không cần gõ tay từng tọa độ lỗ trên CLI), tự tính chiều dài khai triển uốn (`Sheet Metal Bend Allowance` DIN 6935, `K-factor = 0.42`, `OSSB`) và xuất toàn bộ các file `.dxf` tỷ lệ `1:1`.
2. Nếu cần kiểm tra lắp ghép 3D vỏ tủ & thanh cái trong môi trường không có Inventor: Kết hợp với skill `$cad` (`build123d` xuất `.step`) và `$engineering-drawing` (`cadgen.eng_drawing` xuất `.pdf`).

---

## 5. Runbook Thực chiến Khép kín 5 Bước (Mastery End-to-End Workflow)

Quy trình chuẩn khi triển khai một trạm hỗn hợp Động lực + Đo lường tinh xảo (VD: **Biến tần SINAMICS G120C + Bộ Transmitter cân Load cell 6 dây `4–20mA` + Module S7-1200 `SM 1231 AI` + Cầu đấu 3 tầng `-X3`**):

1. **Database & Custom Symbol (`VA1_WEIGH_TRANS.dwg`):** Dùng `AESYMBUILDER` tạo block `VA1_WEIGH_TRANS.dwg` với đủ chân `X1/X2/X4/X8TERMxx`, `TERMDESCxx` (`EXC+/EXC-/S+/S-/SIG+/SIG-`), khóa `WDBLKNAM = VA1_WEIGH_TRANS`; trong `AECATALOG` ([templates/catalog_master_seed.csv](../templates/catalog_master_seed.csv)), khai báo `PINLIST = 4,11,12,14` (tiếp điểm báo lỗi `Form C`) và `ASSYCODE = EMC_GLAND_M16_SKINTOP;SHIELD_CLAMP_SK14`.
2. **Schematic Automation, Fuse Terminal & Shielding:** Chèn cụm Biến tần từ `Circuit Builder` / `User Circuit` (`CIR_03_VFD_G120`), nối cáp động cơ bọc giáp `AESHIELD` **nối đất 2 đầu $360^\circ$**; cấp nguồn 24VDC cho Transmitter qua **Cầu đấu cầu chì có đổi số dây (`HT1_...` Wire Number Change)**; nối Load cell 6 dây (dùng `AEMULTIWIRE` / `AEFANIN`) qua cầu đấu 3 tầng `-X3` và đường `4–20mA` về `SM 1231 AI` (`%IW64`) với giáp `AESHIELD` **nối đất 1 đầu duy nhất tại tủ**; chèn tiếp điểm phụ `Child` của Transmitter vào mạch DI báo lỗi (tự điền chân `11–14`).
3. **Multi-level Terminal (`Internal/External`) & Bulk Excel Sync:** Mở `AETSE` cấu hình cầu đấu 3 tầng `-X3` bằng `Associate Terminals`, ấn định rõ phía `Internal (+MAIN_PNL)` và `External (+FIELD)`, chèn `Partition Plate`, `End Cover`, `End Clamp` và xuất `Terminal Plan` (`Put on Drawing`); dùng `AEEXPORT` → sửa hàng loạt `DESC2` Tiếng Việt Unicode trên Excel → `AEIMPORT` cập nhật ngược lại bản vẽ.
4. **3D Mechanical Pin Mapping & Busbar:** Chèn `AEFOOTPRINT` lên `07_panel_layout.dwg` kèm `DIN Rail` + `Wire Duct`, chạy `AEWIRESEQ`, đồng bộ `.emx` sang Inventor (khớp `RefDes ↔ TAG` và `Harness Pin ↔ TERMxx`, gán `Virtual Parts`), chạy `Auto Route` qua `Harness Segments` kiểm tra `Duct Fill < 65%` và xuất chiều dài cắt dây + Flat Pattern `.dxf`.
5. **1-Click PLC Sync & Audit:** Chạy `AEAUDIT` + `Missing Catalog Data` đạt `0 errors`, chạy `Automatic Reports (.rgf)` xuất toàn bộ BOM (tự tách đủ Transmitter + EMC Gland + Shield Clamp + phụ kiện `-X3`) + `Load Schedule` (từ `RATING1..4`), và chạy `scripts/sync_tia_tags.py` xuất bảng tag `%IW64` chuẩn import thẳng vào TIA Portal.
