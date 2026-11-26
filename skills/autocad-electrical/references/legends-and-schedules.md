# Quy chuẩn 12 Bảng Chú thích, Danh mục & Lệnh Xuất Báo cáo Tự động (ACADE)

Tài liệu chuẩn hóa **cấu trúc cột**, **vị trí đặt trên trang giấy A3 (`420×297 mm`)**, **cỡ chữ** và **đường dẫn Ribbon / lệnh AutoCAD Electrical (`AEREPORT` → `Put on Drawing`)** cho toàn bộ 12 bảng chú thích trên **Sơ đồ Nguyên lý (Schematic)** và **Bản vẽ Thiết kế Tủ & Gia công Đồng (Panel Layout & Busbar)**.

> **Nguyên tắc cốt lõi:** Tuyệt đối **không vẽ chay bằng `TABLE`/`TEXT` thủ công rời rạc** cho các bảng dữ liệu thiết bị, dây dẫn, cầu đấu và BOM. Phải sinh tự động từ cơ sở dữ liệu dự án thông qua lệnh Report của ACADE kèm file định dạng `.set` để tự động cập nhật khi sửa bản vẽ.

---

## PHẦN A: 6 BẢNG & CHÚ THÍCH TRÊN SƠ ĐỒ NGUYÊN LÝ (SCHEMATIC 2D)

### 1. Bảng Ký hiệu Thiết bị (`Symbols Legend`)
- **Trang đặt:** `02_legend_and_abbreviations.dwg` (Nửa bên trái của bản vẽ).
- **Cỡ chữ:** Tiêu đề bảng `3.5 mm`, tiêu đề cột `2.5 mm`, nội dung `2.0–2.5 mm`.
- **Cấu trúc cột chuẩn:**
  | Cột | Tên cột (Song ngữ EN / VI) | Nội dung mẫu |
  | :---: | :--- | :--- |
  | 1 | `SYMBOL / KÝ HIỆU` | Block đồ họa lấy trực tiếp từ **Icon Menu** (`IEC-60617`) |
  | 2 | `FAMILY / MÃ NHÓM` | `Q`, `F`, `K`, `S`, `M`, `T`, `G`, `A`, `U`, `X`, `H`, `Y` |
  | 3 | `DESCRIPTION (EN)` | `MOLDED CASE CIRCUIT BREAKER (MCCB)` |
  | 4 | `MÔ TẢ (VI)` | `ÁPTÔMÁT KHỐI (MCCB)` |
  | 5 | `STANDARD / TIÊU CHUẨN` | `IEC 60617 / IEC 81346-2` |
- **Cách dựng chuẩn trong ACADE:**
  1. Mở *Reports tab → Schematic → Reports* (`AEREPORT`) → chọn báo cáo `Components` để lọc ra đúng các nhóm `FAMILY` thực tế có xuất hiện trong dự án.
  2. Chèn block tương ứng từ **Icon Menu** vào cột `SYMBOL` và **xóa/ẩn giá trị `TAG1`** (hoặc chuyển thành block tĩnh chỉ trên trang Legend để không bị tính lặp vào BOM).

### 2. Bảng Chữ viết tắt (`Abbreviations Table`) & Bảng Quy ước Màu dây (`Wire Color Legend`)
- **Trang đặt:** `02_legend_and_abbreviations.dwg` (Nửa bên phải của bản vẽ).
- **Cấu trúc Bảng Chữ viết tắt (nạp từ [templates/abbreviations_bilingual.csv](../templates/abbreviations_bilingual.csv) qua lệnh `TABLE` → *From a data link*):**
  - Cột: `ABBR | ENGLISH FULL NAME | NGHĨA TIẾNG VIỆT | APPLICATION / GHI CHÚ`
  - Bao gồm đầy đủ: `ACB, MCCB, MCB, RCCB, RCBO, MPCB, OLR, VFD, SPD, MFM, CT, VT, APFC, ATS, PLC, HMI, DI, DO, AI, AO, PELV, FACP, DOL, E-STOP, NO, NC`.
- **Cấu trúc Bảng Quy ước Màu dây & Tiết diện (`Wire Color & Size Legend`):**
  - Cột: `WIRE TYPE / LAYER | CIRCUIT / MẠCH | COLOR (IEC 60445 / TCVN) | MIN. SIZE (mm²) | VOLTAGE`

### 3. Danh mục Thiết bị theo Từng Trang (`Per-Sheet Device Schedule`)
- **Trang đặt:** Góc dưới bên trái (sát lề đóng gáy `20 mm`, phía trên đường viền dưới) hoặc ngay phía trên Khung tên của mỗi trang sơ đồ động lực/điều khiển (`04_...`, `05_...`).
- **Cấu trúc cột chuẩn:**
  `TAG | DESCRIPTION (EN / VI) | RATING / SPEC (In, Icu, Coil V) | MFG | CAT | LOC`
- **Đường dẫn & Lệnh ACADE sinh tự động:**
  - Mở *Reports tab → Schematic → Reports* (`AEREPORT`) → chọn `Bill of Materials` → tích chọn **`Do current drawing only`** → nhấn **`Put on Drawing`** để đặt bảng tự động lên góc bản vẽ hiện hành.

### 4. Bảng Chú thích Tiếp điểm Dưới Cuộn dây (`Contact Cross-Reference Table`)
- **Vị trí đặt:** Tự động xuất hiện ngay **phía dưới mỗi cuộn dây** Contactor (`-K`), Rơ-le trung gian (`-KA`), Rơ-le thời gian (`-KT`).
- **Định dạng hiển thị bắt buộc (`Graphical Format` chuẩn IEC):**
  - Cấu hình trong *Project tab → Project Tools → Properties → **Project Properties** (hoặc **Drawing Properties** → Tab `Cross-References` → chọn `Graphical Format`)*: Tự động vẽ ký hiệu tiếp điểm thường mở `NO`, thường đóng `NC`, tiếp điểm động lực và tọa độ `/Trang.Cột`.
  - Cấu trúc hiển thị:
    ```text
      NO   |   NC
    /04.2  | /05.6
    /04.3  |
    ```

### 5. Bảng Trạng thái Chuyển mạch (`Selector Switch Truth Table / Cam Chart`)
- **Vị trí đặt:** Đặt ngay cạnh hoặc phía dưới ký hiệu công tắc xoay (`MAN - OFF - AUTO`, công tắc chuyển mạch Volt `VS`, Ampe `AS`) trên trang `05_control_schematic.dwg`.
- **Cấu trúc bảng (`X` = Đóng / Closed, `-` = Mở / Open):**
  | CONTACT / TIẾP ĐIỂM | `TERM` | `MAN (1)` | `OFF (0)` | `AUTO (2)` |
  | :---: | :---: | :---: | :---: | :---: |
  | `S1:A` (Chạy tay) | `13 – 14` | **`X`** | `-` | `-` |
  | `S1:B` (Chạy tự động) | `23 – 24` | `-` | `-` | **`X`** |

### 6. Chú thích Cơ cấu Cơ khí (`Mechanical Interlock & Actuator Callouts`)
- **Khóa chéo cơ khí (`Mechanical Interlock` cho ATS, Sao–Tam giác):**
  - Vẽ đường nét đứt (`Layer DASHED_BOX`, `0.15 mm`) nối giữa 2 cuộn dây hoặc 2 cực đóng cắt kèm ký hiệu **hai tam giác đối đỉnh (`▷◁`)** ở giữa và chữ chú thích `MECH. INTERLOCK / KHÓA CHÉO CƠ KHÍ` (dùng lệnh `AEINSERTCOMPONENT` → `Mechanical Interlock`).
- **Cơ cấu thao tác đặc biệt:**
  - Tay quay kéo dài qua cửa tủ: Ghi chú `ROTARY HANDLE WITH DOOR INTERLOCK / TAY QUAY KHÓA LIÊN ĐỘNG CỬA`.
  - Nút dừng khẩn cấp: Ký hiệu đầu nấm có chốt giữ kèm ghi chú `LATCHING MUSHROOM HEAD, TURN TO RELEASE / NÚT NẤM ĐỎ CÓ CHỐT, XOAY NHẢ`.

---

## PHẦN B: 6 BẢNG & CHÚ THÍCH TRÊN BẢN VẼ TỦ & GIA CÔNG ĐỒNG (`07_panel_layout` & `08_busbar`)

### 7. Bảng Vật tư Tủ / Bảng Balloon (`Panel BOM / Balloon Schedule`)
- **Trang đặt:** Góc trên bên phải (phía dưới Revision Block) của trang `07_panel_layout.dwg`.
- **Cấu trúc cột chuẩn (lưu trong file mẫu [templates/panel_bom_bilingual.set](../templates/panel_bom_bilingual.set)):**
  | `ITEM` | `TAG` | `DESCRIPTION (EN)` | `MÔ TẢ (VI)` | `MFG` | `CAT` | `QTY` | `LOC` |
  | :---: | :---: | :--- | :--- | :---: | :--- | :---: | :---: |
  | `1` | `-Q1` | `MCCB 3P 250A 36kA` | `ÁPTÔMÁT KHỐI 3P 250A` | `SCHNEIDER` | `LV525333` | `1` | `+MAIN_PNL` |
- **Đường dẫn & Lệnh ACADE sinh tự động:**
  - Mở *Reports tab → Panel → Reports* → chọn `Bill of Materials` → bấm **`Format`** (`AEREPORTFORMAT`) nạp file [templates/panel_bom_bilingual.set](../templates/panel_bom_bilingual.set) → bấm **`Put on Drawing`**. Số thứ tự `ITEM` trong bảng sẽ tự động đồng bộ 100% với số `Balloon` (`AEBALLOON`) gắn trên hình chiếu thiết bị.

### 8. Bảng Biển tên & Nhãn Khắc Laser (`Nameplate Schedule`)
- **Trang đặt:** Đặt ở góc dưới bên trái trang `07_panel_layout.dwg` (hoặc xuất kèm file [templates/nameplate_schedule.csv](../templates/nameplate_schedule.csv) gửi xưởng khắc Laser).
- **Cấu trúc cột chuẩn:**
  | `NP NO.` | `TAG` | `LOC` | `LINE 1 (ENGLISH)` | `LINE 2 (TIẾNG VIỆT)` | `SIZE (W×H mm)` | `COLOR (BG / TEXT)` | `FONT HEIGHT` | `QTY` |
  | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
  | `NP-01` | `PANEL` | `+DOOR` | `MAIN SWITCHBOARD (MSB)` | `TỦ ĐIỆN PHÂN PHỐI TỔNG` | `150 × 50` | `WHITE / BLACK` (hoặc `RED / WHITE` cho PCCC) | `8.0 / 6.0 mm` | `1` |
  | `NP-02` | `-S10` | `+DOOR` | `EMERGENCY STOP` | `DỪNG KHẨN CẤP` | `Ø60 Ring` | `YELLOW / BLACK` | `4.0 mm` | `1` |
  | `NP-03` | `-H1` | `+DOOR` | `POWER ON` | `BÁO NGUỒN` | `45 × 15` | `WHITE / BLACK` | `3.0 mm` | `1` |
- **Cách trích xuất:** Mở *Reports tab → Panel → Reports* → chọn `Nameplate` (lọc theo `LOC = +DOOR` và `+MAIN_PNL`), xuất ra CSV theo mẫu [templates/nameplate_schedule.csv](../templates/nameplate_schedule.csv) và đặt lên bản vẽ bằng `Put on Drawing`.

### 9. Chú thích Mặt Cánh Tủ & Khoét Lỗ (`Door Cutout & Indicator Legend`)
- **Vị trí đặt:** Đặt ngay dưới hình chiếu **Mặt cánh tủ (`FRONT DOOR VIEW`)** và hình chiếu **Khoét lỗ cánh tủ (`DOOR CUTOUT VIEW`)** trên trang `07_panel_layout.dwg`.
- **Nội dung bắt buộc:**
  1. **Kích thước khoét lỗ chuẩn (`Cutout Dimensions`):**
     - Đèn báo, nút nhấn, công tắc xoay chuẩn Ø22: Khoét lỗ **`Ø22.5 +0.4/-0.0 mm`** có rãnh chống xoay `3.2 × 24.1 mm`, khoảng cách tâm ngang tối thiểu `50–60 mm`, tâm dọc `60–70 mm`.
     - Màn hình HMI, Đồng hồ MFM, Bộ điều khiển APFC, Quạt lọc gió: Ghi rõ kích thước khoét chữ nhật `W × H (mm)` theo đúng Datasheet hãng.
  2. **Cao độ lắp đặt tính từ đáy tủ đứng (`Mounting Height from Base`):**
     - Màn hình HMI / Đồng hồ đo: Tâm ở cao độ `1450 – 1600 mm`.
     - Nút nhấn vận hành / Nút dừng khẩn `E-STOP`: Cao độ `1050 – 1300 mm`.
  3. **Quy ước màu Đèn báo & Nút nhấn (`IEC 60073`):**
     - `GREEN (Xanh lá)`: Đang chạy / Bình thường (`RUN / NORMAL`) — Nút `START`.
     - `RED (Đỏ)`: Dừng / Sự cố khẩn (`STOP / EMERGENCY / FIRE`) — Nút `STOP / E-STOP` (hoặc Báo nguồn 3 pha theo chuẩn VN nếu quy định rõ trong Legend).
     - `YELLOW / AMBER (Vàng)`: Cảnh báo quá tải / Lỗi (`FAULT / TRIP / OVERLOAD`).
     - `WHITE / BLUE (Trắng / Xanh dương)`: Có nguồn điều khiển / Xóa lỗi (`CONTROL POWER ON / RESET`).

### 10. Bảng Thông số Kỹ thuật Vỏ Tủ (`Enclosure Data Block`)
- **Vị trí đặt:** Đặt ngay phía trên Khung tên (`Title Block`) của trang `07_panel_layout.dwg`.
- **Cấu trúc khung thông số chuẩn (Song ngữ EN / VI):**
  | THÔNG SỐ / PARAMETER | GIÁ TRỊ TIÊU CHUẨN / SPECIFICATION |
  | :--- | :--- |
  | `OVERALL DIMENSIONS / KÍCH THƯỚC PHỦ BÌ (W×H×D)` | VD: `800 × 1800 × 600 mm` (Chưa tính đế tủ `Base Plinth H=100 mm`) |
  | `SHEET METAL THICKNESS / ĐỘ DÀY TÔN` | Thân tủ `1.5–2.0 mm`, Cánh tủ `2.0 mm`, Tấm lắp `2.0–2.5 mm` (Mạ kẽm / Sơn tĩnh điện) |
  | `INGRESS PROTECTION & FORM / CẤP BẢO VỆ & FORM` | `IP54` (Trong nhà) / `IP65` (Ngoài trời) — `IEC 61439 Form 2b / 3b / 4b` |
  | `FINISH & COLOR / SƠN HOÀN THIỆN & MÀU SẮC` | Sơn tĩnh điện nhẵn/sần `RAL 7035` (hoặc Đỏ `RAL 3000` cho tủ PCCC) |
  | `CABLE ENTRY / HƯỚNG CÁP VÀO - RA` | Đi đáy (`BOTTOM ENTRY`) qua tấm bích rời (`Removable Gland Plate`) |
  | `ESTIMATED WEIGHT / KHỐI LƯỢNG DỰ KIẾN` | VD: `~ 185 kg` (Có 4 tai cẩu `M12/M16 Lifting Eyebolts` trên nóc tủ) |

### 11. Bảng Cắt & Gia công Thanh cái + Phụ kiện (`Busbar Cut List & Fastener Schedule`)
- **Trang đặt:** Đặt ở góc phải trên trang `08_busbar_fabrication.dwg`.
- **Bảng 11A – Danh mục Cắt & Gia công Thanh cái đồng (`Busbar Cut List`):**
  | `MARK` | `PHASE` | `SPEC (W×T mm)` | `MATERIAL` | `DEVELOPED LENGTH (mm)` | `HOLES (QTY × Ø)` | `BENDS` | `SLEEVE / INSULATION` | `QTY` |
  | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
  | `BB-01` | `L1` | `50 × 10` | `E-Cu 99.9%` | `1450` | `6 × Ø11 + 2 × Ø13.5` | `2 × 90° (R10)` | `RED / BROWN HEAT-SHRINK` | `1` |
- **Bảng 11B – Phụ kiện Bắt đồng, Sứ đỡ & Lực siết (`Busbar Hardware & Torque Schedule`):**
  | `ITEM` | `DESCRIPTION (EN / VI)` | `SPEC / MODEL` | `GRADE / MAT.` | `TORQUE (N·m)` | `QTY` |
  | :---: | :--- | :--- | :---: | :---: | :---: |
  | `HW-01` | `HEX BOLT SET (BOLT + 2 FLAT + 1 SPRING WASHER + NUT) / BỘ BU-LÔNG BẮT ĐỒNG` | `M10 × 35 mm` | `Steel 8.8 Zn` / `A2-70` | **`42 N·m`** | `24` |
  | `HW-02` | `BUSBAR STANDOFF INSULATOR / SỨ ĐỠ THANH CÁI` | `SM-40 (M8/M10)` | `DMC / Polyester` | `20 N·m` | `12` |
  | `HW-03` | `PROTECTIVE SHROUD / TẤM CHE AN TOÀN IP2X` | `Polycarbonate T=3mm` | `Clear PC` | — | `1` |

### 12. Ghi chú Kỹ thuật Chung Bản vẽ Tủ & Gia công (`General Panel & Fabrication Notes`)
- **Vị trí đặt:** Đặt ngay trên `Enclosure Data Block` ở góc dưới bên phải trang `07_panel_layout.dwg` và `08_busbar_fabrication.dwg`.
- **Mẫu 6 dòng Ghi chú Song ngữ Chuẩn (truyền vào `notes=[...]` hoặc khung Text chuẩn):**
  1. `ALL DIMENSIONS ARE IN MILLIMETERS (TẤT CẢ KÍCH THƯỚC ĐO BẰNG MM).`
  2. `GENERAL FABRICATION TOLERANCE PER ISO 2768-m (DUNG SAI GIA CÔNG CHUNG THEO ISO 2768-m).`
  3. `DEBURR ALL SHARP EDGES AND CUTOUTS BEFORE PAINTING/ASSEMBLY (LÀM SẠCH BAVIA CẠNH SẮC VÀ LỖ KHOÉT TRƯỚC KHI SƠN/LẮP RÁP).`
  4. `ALL BUSBAR JOINTS MUST BE CLEANED, TORQUED TO SPEC AND MARKED WITH TORQUE SEAL (MẶT TIẾP XÚC THANH CÁI PHẢI LÀM SẠCH, SIẾT ĐÚNG LỰC VÀ ĐÁNH DẤU SƠN KIỂM TRA).`
  5. `PROVIDE FLEXIBLE EARTH STRAP (≥ 6 mm²) BETWEEN ENCLOSURE BODY AND HINGED DOOR (ĐẤU DÂY ĐỒNG BỆN TIẾP ĐỊA ≥ 6 mm² GIỮA THÂN TỦ VÀ CÁNH TỦ).`
  6. `INSTALL IP2X CLEAR POLYCARBONATE SHROUD OVER ALL LIVE BUSBARS AND INCOMER TERMINALS (LẮP TẤM CHE MICA/PC TRONG SUỐT IP2X CHE CHẮN TOÀN BỘ THANH CÁI VÀ ĐẦU CỰC TỔNG).`

---

## PHẦN C: BẢNG TỔNG HỢP LỆNH & ĐƯỜNG DẪN RIBBON AUTOCAD ELECTRICAL SINH BẢNG TỰ ĐỘNG

| Loại Bảng / Báo cáo | Đường dẫn Ribbon / Lệnh ACADE | Tùy chọn Báo cáo (`Report Name`) | File Định dạng / Tùy chọn Chèn |
| :--- | :--- | :--- | :--- |
| **Danh mục thiết bị từng trang** | *Reports tab → Schematic → Reports* (`AEREPORT`) | `Bill of Materials` (`Current drawing only`) | `Put on Drawing` (Góc dưới trái) |
| **Bảng Tổng hợp Vật tư (Schematic BOM)** | *Reports tab → Schematic → Reports* (`AEREPORT`) | `Bill of Materials` (`Project-wide`) | Xuất `.xlsx` + `Put on Drawing` |
| **Kiểm tra thiếu mã vật tư** | *Reports tab → Schematic → Reports* (`AEREPORT`) | `Missing Catalog Data` | Kiểm tra đạt `0 missing` trước khi xuất BOM |
| **Bảng Vật tư Tủ / Balloon (`Panel BOM`)** | *Reports tab → Panel → Reports* | `Bill of Materials` | Nạp `templates/panel_bom_bilingual.set` qua `Report Format Setup` (`AEREPORTFORMAT`) → `Put on Drawing` |
| **Bảng Biển tên (`Nameplate Schedule`)** | *Reports tab → Panel → Reports* | `Nameplate` | Xuất CSV theo `templates/nameplate_schedule.csv` + `Put on Drawing` |
| **Bảng Đấu nối Cầu đấu (`Terminal Plan`)** | *Panel tab → Terminal Footprints → Editor* (`AETSE`) | `Terminal Plan` / `Terminal Numbers` | `Insert` (Tabular Terminal Strip) trên trang `09_terminal_and_cable_list.dwg` |
| **Danh sách Dây đấu nối (`Wire List`)** | *Reports tab → Schematic → Reports* (`AEREPORT`) | `From/To` (Lọc theo `+MAIN_PNL` / `+DOOR`) | `Put on Drawing` hoặc xuất `.xlsx` (hiện đủ `Color` + `Size`) |
| **Danh sách Cáp hiện trường (`Cable List`)** | *Reports tab → Schematic → Reports* (`AEREPORT`) | `Cable Summary` / `Cable From/To` | `Put on Drawing` trên trang `09_terminal_and_cable_list.dwg` |
| **Xuất hàng loạt mọi báo cáo** | *Reports tab → Schematic → Automatic Reports* | Nhóm báo cáo `.rgf` | Tự động cập nhật/xuất toàn bộ báo cáo 1 lượt |
| **Bảng Tiếp điểm dưới cuộn dây** | *Project Properties → Cross-References → Graphical Format* | `Component Cross-Reference` (`AECROSSREF`) | Tự động cập nhật qua *Project-Wide Update/Retag* (`AERETAG`) |
