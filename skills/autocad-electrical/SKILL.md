---
name: autocad-electrical
description: >-
  Engineering standards, schematic workflow, Icon Menu discipline, IEC 60617 /
  IEC 81346 tagging, wire types, Title Block mapping (WD_TB), panel sizing,
  busbar calculation, and audit checks for AutoCAD Electrical (ACADE) schematic
  and panel layout projects (MSB, DB, MCC/PLC, ATS, PFC, Lighting, PCCC). Use
  when designing, configuring, reviewing, auditing, or documenting electrical
  schematics, control cabinets, power distribution panels, PLC I/O wiring,
  BOMs, or wire lists in AutoCAD Electrical.
---

# AutoCAD Electrical (ACADE) & Control Panel Standards

Skill quy chuẩn toàn diện cho **Thiết kế Sơ đồ Nguyên lý Điện** và **Cấu hình Tủ điện Công nghiệp** trên AutoCAD Electrical. Kết hợp chặt chẽ với **Quy chuẩn Toàn cục (Mục 7 – Khung bản vẽ, Tỷ lệ 1:1 vs Layout & Song ngữ EN/VI)**.

---

## 🧭 Tài liệu Chuyên sâu theo Nhiệm vụ (References)

Khi thực hiện thiết kế, tính toán hoặc kiểm tra từng loại tủ điện cụ thể, **đọc thêm tài liệu tương ứng** dưới đây:

| Khi làm việc với... | Đọc tài liệu tham khảo |
| :--- | :--- |
| **Tính dòng, chọn ACB/MCCB/MCB, cáp điện, Busbar, tụ bù, khởi động động cơ** | [references/electrical-calculations.md](references/electrical-calculations.md) |
| **Tính kích thước vỏ tủ, tấm lắp, Busbar đồng, CT, Sứ đỡ, tản nhiệt, Mica IP2X** | [references/panel-sizing-and-busbar.md](references/panel-sizing-and-busbar.md) |
| **Gia công Kim loại tấm (`K-Factor`, `Corner Relief`, `Door Gap`) & Kết cấu Hàn (`ISO 2553`, `ISO 273`)** | [references/sheet-metal-and-weldment-dfm.md](references/sheet-metal-and-weldment-dfm.md) |
| **Quy chuẩn Đồ họa CAD (Layer, Màu sắc Line, Nét in `.ctb`, Cỡ chữ)** | [references/cad-layers-and-colors.md](references/cad-layers-and-colors.md) |
| **Quy chuẩn 12 Bảng Chú thích, Danh mục & Lệnh Xuất Báo cáo Tự động (`Put on Drawing`)** | [references/legends-and-schedules.md](references/legends-and-schedules.md) |
| **Quản lý Vòng đời Dự án (`.dwt`/ECO/Retag), CSDL (`Catalog`/`Pin List`), Đồng bộ PLC 2 chiều (TIA Portal) & Liên kết 3D Inventor** | [references/project-lifecycle-plc-and-3d-sync.md](references/project-lifecycle-plc-and-3d-sync.md) |
| **Khai thác Block Chính hãng, `FLATSHOT` từ `.stp` sang 2D & Ánh xạ `footprint_lookup.mdb`** | [references/manufacturer-blocks-and-flatshot.md](references/manufacturer-blocks-and-flatshot.md) |
| **Cấu trúc Bộ hồ sơ hoàn chỉnh & Checklist Nghiệm thu xuất xưởng (FAT)** | [references/deliverables-and-fat.md](references/deliverables-and-fat.md) |
| **Tủ phân phối tổng (MSB), Tủ nhánh (DB/SDB), Tủ tổng hợp** | [references/power-distribution-panels.md](references/power-distribution-panels.md) |
| **Tủ điều khiển trung tâm & động cơ (MCC/PLC), Tủ chiếu sáng (LP)** | [references/control-and-lighting-panels.md](references/control-and-lighting-panels.md) |
| **Tủ chuyển nguồn tự động (ATS), Tủ tụ bù (PFC)** | [references/ats-and-pfc-panels.md](references/ats-and-pfc-panels.md) |
| **Tủ phòng cháy chữa cháy (PCCC / Fire Pump)** | [references/fire-fighting-pccc-panels.md](references/fire-fighting-pccc-panels.md) |

---

## 1. Cấu trúc Dự án, Tham chiếu Vị trí & Quản lý Trang (Project Manager)

1. **Nguyên tắc `1 Sheet = 1 File .dwg` & Dự án Mẫu (`Copy Project`)**: Quản lý tập trung qua file `.wdp` trong **Project Manager**; khởi tạo dự án mới bằng **`Copy Project` (`AECOPYPROJECT`)** từ dự án mẫu chuẩn và bản vẽ mẫu `.dwt` theo [references/project-lifecycle-plc-and-3d-sync.md](references/project-lifecycle-plc-and-3d-sync.md).
2. **Đặt tên file `.dwg` chuẩn ASCII (đồng bộ 100% với danh mục hồ sơ & `cad-project-naming`):** Không gắn hậu tố `_R00` lên file đang làm việc; dùng tiền tố số trang + mã dự án (`01_cover_and_index.dwg` hoặc `[SheetNo]_[ProjectCode]-[Discipline]-[DocType]-[Description].dwg`, VD: `07_BW500-EL-LAY-MainControlPanel.dwg`). Chỉ gắn `_R[XX]` lên bản phát hành tĩnh trong `03_Issued_PDF/`.
3. **Hệ thống Tham chiếu Vị trí (`X-Zones` chuẩn IEC) & Quản lý Thay đổi (`ECO / Mark-Verify / Retag`)**:
   - Trong *Drawing Properties → Drawing Format*, chọn **X-Zones** (chia cột `0..9` hoặc `1..8` theo chiều ngang chuẩn IEC) để **Cross-Reference** hiển thị chuẩn `/Trang.Cột` (VD: `/04.3`).
   - Khi thay đổi thiết kế hoặc thêm/xóa trang, bắt buộc tuân thủ quy trình **`Mark/Verify DWGs` → `Project-wide Update/Retag` (`AERETAG`) → `Title Block Update` (`AEUPDATETITLEBLOCK`)** theo [references/project-lifecycle-plc-and-3d-sync.md](references/project-lifecycle-plc-and-3d-sync.md).

---

## 2. Tiêu chuẩn Thư viện & Icon Menu (IEC 60617)

1. **Thống nhất chuẩn ký hiệu**: Dùng duy nhất **1 hệ tiêu chuẩn** cho toàn dự án (mặc định **IEC-60617** hoặc **IEC** theo chiều dọc). Cấm trộn lẫn JIC và IEC.
2. **Tuân thủ Block từ Icon Menu, API `c:wd_*` & Cấm Tuyệt đối Giả lập bằng `ezdxf`:**
   - 100% thiết bị sơ đồ nguyên lý phải chèn từ thư viện thật **`Libs\iec-60617\*.dwg`** qua **Icon Menu** (`AEINSERTCOMPONENT`) hoặc API AutoLISP **`(c:wd_insym2)`** (`acade_insert_schematic_symbol`). **Cấm `EXPLODE`** block thiết bị và **cấm tuyệt đối** dùng `ezdxf` / `autocad_draw_entities` vẽ hình chữ nhật giả lập (`ACADE_DEV_*`), vẽ `CIRCLE` trần làm Motor/Đèn/Cầu đấu, hoặc gộp 2 thiết bị (`-Q2` & `-K1`) vào chung 1 block (`1 Thiết bị = 1 Tag` chuẩn IEC 81346).
   - **Tự động hóa dựng mạch & sửa hàng loạt:** Sử dụng **`Circuit Builder` (`AECIRCUITBUILDER`)**, **5 cụm mạch mẫu `User Circuits`** (`DOL`, `Y-Δ`, `VFD`, `24VDC PELV`, `Safety 3SK1`), **`Copy Circuit` (`AECOPYCIRCUIT`)**, **`Scoot` (`AESCOOT`)**, **`Swap/Update Block` (`AESWAPBLOCK`)** và chu trình **`Export / Update from Spreadsheet` (`AEEXPORT` / `AEIMPORT`)** theo [references/project-lifecycle-plc-and-3d-sync.md](references/project-lifecycle-plc-and-3d-sync.md).
   - Liên kết chặt chẽ cặp **Parent (`TAG1`) ↔ Child (`TAG2`)** giữa cuộn dây và tiếp điểm phụ; kiểm tra số lượng tiếp điểm thực tế qua `_PINLIST` và hiển thị tự động bảng **`Graphical Cross-Reference`** (`AECROSSREF`) ngay dưới cuộn dây (cấm kẻ bảng Cross-Ref giả bằng `TEXT` cứng).
   - **Tách bạch Mạch Động lực (3P) và Mạch Điều khiển (Parent/Child):** Không bao giờ đặt cuộn dây `VCR1` vào mạch động lực 3 pha. Mạch động lực 3 pha dùng symbol 3 cực (`VCB11Q13`, `VMS2NA13F`, `VFU1_S00371`...) và cụm tiếp điểm động lực `Child` (`TAG2 = -K1`); mạch điều khiển 24VDC đặt cuộn dây `Parent` (`VCR1`, `TAG1 = -K1`) và các tiếp điểm phụ `Child` (`VCR21` NO / `VCR22` NC, `TAG2 = -K1`) để ACADE tự tra `_PINLIST` điền chân `1-2, 3-4, 5-6, 13-14, 21-22`.

---

## 3. Quy chuẩn Đặt tên & Phân cấp Vị trí Thiết bị (IEC 81346: `=INST +LOC -TAG`)

1. **Tag Format (`-TAG`):** Thiết lập thống nhất trong *Project Properties → Components* (`%F%N` hoặc `%S%F%N` theo số trang, VD: `-1Q1`, `-2K1`).
2. **Mã lắp đặt (`=INST`) & Mã vị trí (`+LOC`):** Bắt buộc gắn thuộc tính `LOC` cho mọi thiết bị để ACADE tự động phân tách dây đi qua Cầu đấu (`-X`) và tự động lọc thiết bị hiện trường khỏi Panel Layout Footprint:
   - `+MAIN_PNL`: Thiết bị lắp trên tấm lắp bên trong tủ.
   - `+DOOR`: Thiết bị gắn trên mặt cánh tủ (HMI, nút nhấn, đèn báo, đồng hồ).
   - `+FIELD`: Thiết bị ngoài hiện trường (Motor, Cảm biến, Van điện từ, Công tắc hành trình).

| Tiền tố (`FAMILY`) | Nhóm thiết bị | Ví dụ |
| :--- | :--- | :--- |
| **`Q`** | Thiết bị đóng cắt mạch động lực | MCB, MCCB, ACB, Dao cách ly (`-Q1`) |
| **`F`** | Thiết bị bảo vệ | Cầu chì, Rơ-le nhiệt, SPD (`-F1`) |
| **`K`** | Rơ-le, Contactor | Contactor, Rơ-le trung gian, Timer (`-K1`, `-KA1`) |
| **`S`** | Chuyển mạch điều khiển / Cảm biến | Nút nhấn, Công tắc xoay, E-Stop, Sensor (`-S1`, `-SQ1`) |
| **`M`** | Động cơ điện | Motor 3 pha, Servo motor, Quạt làm mát (`-M1`) |
| **`T` / `G`** | Biến áp / Bộ nguồn | Biến áp cách ly (`-T1`), Nguồn 24VDC (`-G1`) |
| **`A` / `U`** | Cụm điều khiển / Biến đổi | PLC, Module I/O, Biến tần VFD, HMI (`-A1`, `-U1`) |
| **`X`** | Cầu đấu dây / Ổ cắm | Terminal Strip (`-X1`, `-X2`) |
| **`H`** | Thiết bị báo hiệu | Đèn báo, Còi báo (`-H1`) |
| **`Y`** | Cơ cấu chấp hành điện từ | Van điện từ (Solenoid Valve), Phanh từ (`-Y1`) |

---

## 4. Quy chuẩn Vẽ dây, Cáp nhiều lõi, Tín hiệu Xuyên trang & PLC I/O

1. **Lệnh Wire (`AEWIRE` / `c:wd_wire_quik`) & Đăng ký Wire Type (`AEWIRETYPE`)**: Bắt buộc vẽ dây qua lệnh/API dây của ACADE trên Layer đã khai báo trong `WD_M` (`WIRELAYS=PWR_*,CTRL_*,SIG_*,SAFE_*`, đủ **`Color`** + **`Size`**, VD: `PWR_L1_BK_2.5`, `CTRL_24VDC_DBU_0.75`; dây `PE` vẽ nét liền `CONTINUOUS`) theo [references/cad-layers-and-colors.md](references/cad-layers-and-colors.md). **Cấm dùng `LINE`/`LWPOLYLINE` thường, và cấm vẽ dây đâm xuyên thủng qua cầu chì/thiết bị mà không ngắt tại chân `X?TERM??` (`Break Wire` / `c:wd_trimwire`).**
2. **Định dạng Đánh số dây (`AEWIRENO` / Block `WD_WN*`) & Điểm nối nhánh (`WD_DOT`)**:
   - Đánh số dây tự động bằng lệnh **`AEWIRENO`** (sinh block `WD_WN*`, **cấm gõ số dây bằng `TEXT` tĩnh**) theo định dạng Trang + Số thứ tự (`%S%N` hoặc `%S.%N`, VD: `0401`, `0402`).
   - Dùng **Fixed Wire Numbers** cho các thanh nguồn chung xuyên trang (`L1`, `L2`, `L3`, `N`, `PE`, `+24VDC`, `0VDC`, `L_220VAC`, `N_220VAC`). Mọi ngã ba đấu nối bắt buộc chèn block **`WD_DOT`** hoặc **Angled Tee**.
3. **Cáp nhiều lõi & Giáp chống nhiễu (`Cable Markers` – `AEMARKER` & `AESHIELD`)**:
   - Gắn Cable Marker (`-W1`, `-W2`) cho cáp động lực và cáp điều khiển đi từ cầu đấu tủ ra thiết bị ngoài hiện trường (`+FIELD`) để xuất **Cable From/To Report**.
   - Dùng ký hiệu **Shield (`AESHIELD`)** cho cáp bọc giáp; tuân thủ nghiêm ngặt quy tắc **nối đất giáp 2 đầu $360^\circ$ cho cáp động cơ VFD** vs **nối đất giáp 1 đầu duy nhất tại tủ cho cáp Analog `4–20mA` / Load cell / RS-485** (tránh Ground Loop) theo [references/control-and-lighting-panels.md](references/control-and-lighting-panels.md).
4. **Liên kết xuyên trang**: Bắt buộc chèn cặp **Source Arrow (`HA1S1` / `AESRCARROW`)** và **Destination Arrow (`HA1D3` / `AEDESTARROW`)** khớp `SIGCODE` (cấm vẽ thanh nguồn cụt 2 đầu chỉ ghi `TEXT`).
5. **PLC I/O, Tín hiệu Tinh xảo (Load cell, Encoder, 4–20mA) & Mạng Truyền thông (`PROFINET`, `Modbus RTU`)**:
   - Với S7-1500: `Slot 0` = PS, `Slot 1` = CPU, module I/O bắt đầu từ **`Slot 2`**; mã module phải tồn tại trong **`ace_plc.mdb`** (nạp trước bằng [scripts/seed_acade_databases.py](scripts/seed_acade_databases.py)). Mạch dừng khẩn `E-STOP` 2 kênh qua **Safety Relay** hoặc module **F-DI (`PROFIsafe` dùng nguồn xung kiểm tra `VS0/VS1`)** theo [templates/plc_io_import_template.csv](templates/plc_io_import_template.csv).
   - Trong file CSV của **`Spreadsheet to PLC I/O Utility`** (`AEPLCIO`, ánh xạ `BLK_NAME = B`), cột **`BLOCK`** phải là **tên symbol thiết bị ngoại vi thật trong `Libs\iec-60617`** (VD: `VSW11`, `VSW12`, `VLT1A`, `VCR1`, `VY1`, `VPX1`...) hoặc để trống cho đầu dây chờ — **tuyệt đối không điền tên giả của module PLC** (`PLC_DI_16`...) vào cột `BLOCK`.
   - Thiết kế mạch Analog `4–20mA` (2-wire/4-wire), Load cell (6 dây có `SENSE+/S-`), Encoder vi sai và mạng `PROFINET` / `Modbus RTU RS-485` (Daisy-chain, điện trở đầu cuối `120 Ω` ở 2 đầu mút) theo [references/control-and-lighting-panels.md](references/control-and-lighting-panels.md).
   - Đồng bộ 2 chiều qua bảng `I/O Assignment` dùng chung (`AEPLCIO` / `acade_build_plc_from_csv`) theo [references/project-lifecycle-plc-and-3d-sync.md](references/project-lifecycle-plc-and-3d-sync.md).

---

## 5. Xử lý Thiết bị Ngoài Thư viện (`Custom Symbols`, `X?TERM??` & `ASSYCODE`)

**Cấm tuyệt đối** vẽ chay bằng `LINE`/`RECTANGLE`/`TEXT` thường. Chọn 1 trong 3 cách chuẩn:
1. **`PLC Parametric` / `Black Box` (`AEPLCDB`)**: Nhanh nhất cho Biến tần, Servo, Nguồn, Đồng hồ nhiệt, Bộ cân Load cell.
2. **`Symbol Builder` (`AESYMBUILDER` – Chuẩn Chân đấu nối `X?TERM??` & Tên file IEC)**:
   - Gắn đủ Attributes bắt buộc (`TAG1`/`TAG2`, `DESC1-3`, `MFG`, `CAT`, `FAMILY`) và các chân hiển thị số cực `TERM01`, `TERM02`...
   - **Bắt buộc gán đúng hướng điểm bắt dây (`Wire Connection Direction` – `X?TERM??`)** để khi chèn symbol vào dây `AEWIRE`, phần mềm tự động cắt dây và bắt đúng hướng:
     - `X1TERMxx`: Dây đi vào từ **Bên Phải (`0°`)**
     - `X2TERMxx`: Dây đi vào từ **Phía Trên (`90°`)**
     - `X4TERMxx`: Dây đi vào từ **Bên Trái (`180°`)**
     - `X8TERMxx`: Dây đi vào từ **Phía Dưới (`270°`)**
   - Đặt tên file block theo quy ước chuẩn ACADE: `[V(Dọc)/H(Ngang)] + [FAMILY 1–2 ký tự] + [1(Parent)/2(Child)] + _<mo_ta>.dwg` (VD: `VK1_SAFETY_RELAY_3SK1.dwg`, `VQ1_MPCB_3RV2.dwg`) và đưa vào menu qua `AEMENUWIZ`.
3. **Thư viện hãng & Phụ kiện Ghép (`Manufacturer Content` & `ASSYCODE` / `Multiple Catalog`)**:
   - Ưu tiên dùng gói **Manufacturer Content** (`Libs\panel\...`) hoặc tải `.dwg`/`.dxf`/`.stp` từ cổng chính hãng (**Siemens SiePortal**, **Schneider**, **ABB**, **Rittal**, **Phoenix Contact**, **TraceParts**); chuẩn hóa qua `OVERKILL` + `AESYMBUILDER` + `footprint_lookup.mdb` theo [references/manufacturer-blocks-and-flatshot.md](references/manufacturer-blocks-and-flatshot.md).
   - Dùng `ASSYCODE` hoặc `Multiple Catalog` để gán các phụ kiện ghép kèm (tiếp điểm phụ, đế rơ-le, bộ dập xung) vào thiết bị chính theo [references/project-lifecycle-plc-and-3d-sync.md](references/project-lifecycle-plc-and-3d-sync.md).

---

## 6. Cầu đấu, Panel Layout, Tích hợp 3D Inventor, Gia công Busbar & Xuất PDF

1. **Cầu đấu (`AETSE`)**: Chèn cầu đấu bằng block chuẩn **`HT0*` (không đổi số dây)** hoặc **`HT1*` / `VT1*` (cầu chì/dao cách ly có đổi số dây)** với thuộc tính `TAGSTRIP` + `TERM01` (**cấm vẽ vòng tròn `CIRCLE` + `TEXT` giả cầu đấu**); quản lý trong **Terminal Strip Editor** (`AETSE`), gộp tầng `Associate Terminals`, thiết lập Jumper/End Clamp và xuất **Terminal Plan** (`AETSP`).
2. **Panel Layout (`AEFOOTPRINT`), Liên kết Schematic List, Liên kết 3D Inventor & Gia công Busbar**:
   - **Đồng bộ bắt buộc từ `Schematic List` (`AEFOOTPRINT` / `acade_sync_panel_footprints`):** Mọi thiết bị có `LOC = +MAIN_PNL` và `+DOOR` trong Scratch Database `.mdb` của dự án phải được chèn Footprint 1:1 lên trang `07_panel_layout.dwg` qua ánh xạ `footprint_lookup.mdb` (mang thuộc tính `P_TAG1` liên kết trực tiếp với `TAG1` sơ đồ nguyên lý) và gắn **`AEBALLOON`** động (đảm bảo `Schematic vs Panel Discrepancy = 0`).
   - **Không vẽ hình chữ nhật trống rỗng đại khái làm Footprint thiết bị:** Bắt buộc lấy block/model thật `1:1 mm` của hãng theo [references/manufacturer-blocks-and-flatshot.md](references/manufacturer-blocks-and-flatshot.md):
     - **Dự án vẽ 2D trên ACADE:** Dùng `.dwg`/`.dxf` hãng (`Libs\panel\...` hoặc làm sạch bằng `OVERKILL`/`PURGE`) hoặc **`IMPORT` file `.stp`/`.step` → `FLATSHOT` (tắt nét khuất) → xóa khối 3D gốc → `OVERKILL` → `AESYMBUILDER` (*Panel Footprint*) → ánh xạ `footprint_lookup.mdb`**.
     - **Dự án hỗ trợ kiểm tra va chạm 3D (`Scene3D`):** Dùng kích thước thật từ `verified_footprints_catalog.csv` / `.step` để kiểm tra `3D Z-Clearance` và `AABB Clash`, nhưng bản vẽ `.dwg` phát hành vẫn phải chèn block Panel Footprint mang `P_TAG1`/`MFG`/`CAT` cho ACADE quản lý BOM.
   - **Quy tắc Phân tách Không gian `Model Space` vs `Paper Space` Chuẩn Kiến trúc Autodesk ACADE:**
     - **Nhóm 1 — Bản vẽ Sơ đồ nguyên lý, SLD, PLC I/O & Bảng Đấu nối (`01..06`, `09` — Tỷ lệ `1:1`):** Đặt Khung bản vẽ ISO A3 (`420 × 297 mm`), Khung tên `TITLE_BLOCK_A3_BILINGUAL` (`WD_TB`), và Lưới chia cột **`X-Zones (0..9)` ngay trong `Model Space` ở tỷ lệ `1:1 mm`**, đồng bộ tuyệt đối tọa độ gốc `XY Grid Origin` với thuộc tính của block ẩn **`WD_M`** (từ mẫu [templates/TEMPLATE_IEC_A3.dwt](templates/TEMPLATE_IEC_A3.dwt)). Nhờ đó phép đặt tên `%S%F%N` và tham chiếu chéo `/Trang.Cột` luôn chính xác tuyệt đối 100%, không bị lệch cột khi trượt Viewport.
     - **Nhóm 2 — Bản vẽ Bố trí Mặt tủ & Gia công Cơ khí Thanh cái (`07_panel_layout`, `08_busbar_fabrication` — Tỷ lệ thu phóng `1:20`, `1:10`, `1:2.5`):** Tuân thủ chuẩn Cơ khí ISO 128: **100% hình học thiết kế & chi tiết trích (`Detail A..D`) vẽ ở kích thước thật `1:1 mm` trong `Model Space`** (`$INSUNITS = 4`) kèm thực thể **`DIMENSION` gốc AutoCAD** (`dimlfac = 1.0`, cấm vẽ tay `LINE` + `TEXT`); còn **`Paper Space (Layout ISO_A3)`** đặt Khung bản vẽ A3, Khung tên `WD_TB`, các bảng thống kê và cửa sổ **`VIEWPORT`** khóa đúng tỷ lệ chuẩn ISO 5455 (`1:1`, `1:2`, `1:2.5`, `1:5`, `1:10`, `1:20`, `1:25`).
   - **Ký hiệu Đánh dấu Chuẩn Quốc tế (ISO 128 / ISO 6433 / ISO 5456-2):** Balloon dùng `ACI 7` kèm **chấm tròn đặc (`•`)** hoặc **mũi tên (`→`)**; hình cắt (`A-A`, `B-B`) có **Cutting Plane Line + mũi tên hướng nhìn**; chi tiết trích (`DETAIL A..D`) có **vòng tròn khoanh vùng**; Khung tên có **biểu tượng Góc chiếu (`ISO 5456-2`)**.
   - **Quy chuẩn Thực chiến Tủ điều khiển & Tấm lắp (`panel-sizing-and-busbar.md`):**
     - **Đủ mạch `3P+N+PE`, Cầu chì báo pha 3P (`-F1`, `2A`) & MCB 2P (`-Q3` cấp nguồn 230VAC cho bộ nguồn 24VDC/quạt):** Không bỏ quên dây `N` hoặc đấu đèn báo pha không qua cầu chì.
     - **Tủ nhỏ ($\le 63\text{A}–100\text{A}$) dùng Cầu đấu động lực / Domino (`-X0: L1, L2, L3, N, PE`) + 1 thanh đồng `PE` nhỏ:** Không lắp hệ thanh cái đồng 3 pha + sứ đỡ cồng kềnh cho tủ điều khiển nhỏ.
     - **Tách biệt Thiết bị Gài Ray (`DIN Rail TS35`) vs Thiết bị Bắt Vít vào Tấm lắp (`Base-Mounted`):** Không vẽ thanh DIN Rail `TS35` chạy xuyên dưới đáy MCCB khối, Biến tần VFD hay PLC S7-1500 (dùng ray nhôm S7-1500 riêng).
     - **Máng cáp nhựa (`Wire Duct`) ghép chữ T sát mép (`Butt-Joint`):** Máng ngang cắt dừng ở mép trong máng dọc.
   - **Liên kết Cơ–Điện 3D (`Autodesk Inventor Electromechanical Link` - `.emx`):** Khi dự án kết nối Inventor, khởi tạo file `.emx` thật bằng lệnh **`AEEMLINK`** của ACADE nối `.wdp` ↔ `.iam` (`RefDes ↔ TAG`, `Harness Pin ↔ TERMxx`). **Cấm tuyệt đối tự chế thẻ XML `.emx` giả lập bằng Python `ElementTree`.**
   - **Giới hạn đúng vai trò của `ezdxf` ([scripts/generate_busbar_dxf.py](scripts/generate_busbar_dxf.py)):** Chỉ dùng `ezdxf` cho **bản vẽ gia công cơ khí thanh cái 2D CAM (`08_busbar_fabrication`)** (tính `Bend Allowance` + lỗ `DIN 43673`), **tuyệt đối không bao giờ dùng `ezdxf` để dựng Sơ đồ nguyên lý (`01..06`, `09`) hay gõ cứng bảng `BOM` / `Wire List` / `Cross-Ref`.**
3. **Tự động hóa Native ACADE qua MCP `autocad-direct` (`c:wd_*` AutoLISP API), Chống lỗi Font `?` Tiếng Việt & Xuất PDF**:
   - **Khởi tạo & Dựng mạch 100% Native Database (`.wdp` + `.dwg` + Scratch `.mdb`):**
     - Mọi bản vẽ điện quản lý bằng định dạng **`.dwg`** nằm trong file dự án **`.wdp`** (copy từ [templates/TEMPLATE_IEC_A3.dwt](templates/TEMPLATE_IEC_A3.dwt) đã nhúng sẵn `WD_M` và `TITLE_BLOCK_A3_BILINGUAL`).
     - Sử dụng trực tiếp bộ tool chuyên biệt của MCP **`autocad-direct`** gọi thẳng AutoLISP API gốc của AutoCAD Electrical (nạp qua `wdload.lsp` → `(c:wd_load)`):
       1. **`acade_project_init`**: Sinh `.wdp` chuẩn IEC-60617, khởi tạo bộ `.dwg` từ `TEMPLATE_IEC_A3.dwt`, kích hoạt dự án (`_AEOPENPROJECT` / `c:ace_add_dwg_to_project`) và chạy `_AEREBUILDDB` tạo Project Scratch Database `<project>.mdb`.
       2. **`acade_insert_schematic_symbol`**: Gọi `(c:wd_insym2)` chèn symbol thật từ `Libs\iec-60617\` (tự cắt dây `AEWIRE` tại chân `X?TERM??`) và `(c:wd_modattrval)` gán `MFG`, `CAT`, `LOC`, `INST`, `DESC1..3`, `TAGSTRIP`/`TERM01`.
       3. **`acade_draw_smart_wires_and_arrows`**: Vẽ dây thông minh qua `(c:wd_wire_quik)`, đặt `WDDOT` tại ngã rẽ T và chèn cặp `Source/Destination Signal Arrows` (`HA1S1` / `HA1D3`) theo `SIGCODE`.
       4. **`acade_build_plc_from_csv`**: Chèn block `PLCIO` thật (`HP1W--L` + `HP1WA-D` từ `Libs\iec-60617\`), nối dây `c:wd_wire_quik` và thả linh kiện ngoại vi (`VCR1`, `VPB11`, `VLT1A`, `VSW12`) lên dây.
       5. **`acade_sync_panel_footprints`**: Truy vấn thiết bị `+MAIN_PNL` & `+DOOR` từ Scratch DB `.mdb` (`COMP` với `PAR1_CHLD2='1'`), chèn Panel Footprint `.dwg` tại tọa độ thực tế trong vỏ tủ kèm XDATA `VIA_WD_FP`.
       6. **`acade_run_reports_and_retag`**: Gắn block số dây `WD_WNH`/`WD_WNV` không hộp thoại, chạy `_AEREBUILDDB` → `c:wd_retag_update_noprompts` → lặp `c:wd_tb_process_one` qua mọi trang `.dwg`.
       7. **`acade_place_db_reports_on_drawing`**: Truy vấn trực tiếp Scratch `.mdb` (`COMP`, `WFRM2ALL`, `PLCIO`, `TERMS`) đặt bảng `AcDbTable` động (`BOM`, `WIRE_FROM_TO`, `PLCIO`, `TERMINAL_PLAN`) lên bản vẽ không vướng hộp thoại DCL.
       8. **`acade_insert_cable_and_jumper`**: Chèn `Cable Marker` (`VWO1`) cho cáp hiện trường (`+FIELD`) và gán thuộc tính cầu đấu nhiều tầng / cầu nối (`LEVEL`, `LNUMBER`, `LTOTAL`, `JUMPER_ID`).
       9. **`acade_electrical_audit`**: Thực thi Gatekeeper Fail-Closed kiểm toán trực tiếp trên Project Scratch Database `<project>.mdb` (`COMP`, `PNLCOMP`, `WIRE_ERR`, `WFRM2ALL`).
   - **Bắt buộc cấu hình Font TrueType Unicode (`arial.ttf`, `isocpeur.ttf` hoặc `tahoma.ttf`) trên chuẩn `R2018 (UTF-8)`** cho Textstyle `Standard` / `WD_IEC` / `VN_ARIAL` (cấm để `txt.shx` gây lỗi `?` Tiếng Việt).
   - Ánh xạ Title Block bằng mẫu [templates/default_iec_bilingual.wdt](templates/default_iec_bilingual.wdt), chạy **`Title Block Update` (`AEUPDATETITLEBLOCK`)** đồng bộ toàn dự án và xuất gộp bằng **Publish → Plot Project to PDF**.

---

## 7. Checklist Chốt chặn Kiểm toán Điện (`Database Gatekeeper`) & Tài nguyên Thực thi

1. **Quản trị & Nạp tự động Cơ sở dữ liệu (`seed_acade_databases.py` & `AECATALOG`)**:
   - Trước khi dựng mạch, chạy [scripts/seed_acade_databases.py](scripts/seed_acade_databases.py) để nạp tự động dữ liệu `MFG` (viết IN HOA 100%), `CAT`, `_PINLIST` (Form C `4,...`), `ASSYCODE` vào `default_cat.mdb`, ánh xạ Footprint vào `footprint_lookup.mdb`, và mã module Siemens S7-1500/S7-1200 vào `ace_plc.mdb`.
2. **Gatekeeper Kiểm toán Điện Bắt buộc (`acade_electrical_audit` — Fail-Closed nếu vi phạm)**:
   - Cuối mọi dự án, bắt buộc chạy `acade_electrical_audit` (hoặc [scripts/acade_electrical_audit.py](scripts/acade_electrical_audit.py)) truy vấn trực tiếp các bảng của **Project Scratch Database (`<project>.mdb`: `COMP`, `PNLCOMP`, `WIRE_ERR`, `WFRM2ALL`)** kết hợp `AEAUDIT`, chặn cứng xuất bản nếu `COMP` rỗng hoặc bất kỳ chỉ số nào `> 0`:
     - **`Bogus Wires / Unconnected Wire Stubs > 0`** (Dây hở hoặc vẽ `LINE` không bắt vào chân `X?TERM??`).
     - **`Orphaned Child Contacts > 0` hoặc `Pinlist Overflow > 0`** (Tiếp điểm `Child` không có cuộn dây `Parent`, hoặc vượt số tiếp điểm khai báo trong `_PINLIST`).
     - **`Duplicate Component Tags > 0`** (Trùng mã `TAG` trong cùng `INST + LOC`).
     - **`Missing Catalog (MFG/CAT empty) > 0`** hoặc **`Schematic vs Panel Discrepancy > 0`** (Thiết bị có trên sơ đồ `+MAIN_PNL`/`+DOOR` nhưng thiếu mặt tủ Panel Layout, như lỗi bỏ quên `-S1`).
3. **Đầy đủ 12 Bảng Chú thích & Báo cáo Tự động qua `.rgf` (`AEREPORTGROUP` -> `Put on Drawing`)**:
   - Sinh tự động từ Database qua [templates/project_master_reports.rgf](templates/project_master_reports.rgf) và `AEREPORT` (**cấm tuyệt đối** kẻ bảng `draw_grid_table()` gõ mảng chuỗi cứng cho BOM/Device Schedule/Wire List/Terminal Plan) theo [references/legends-and-schedules.md](references/legends-and-schedules.md) và [references/deliverables-and-fat.md](references/deliverables-and-fat.md).
4. **Tài nguyên Mẫu & Script Tự động hóa (`templates/` & `scripts/`):**
   - Bản vẽ mẫu `.dwt` chuẩn IEC-60617 (nhúng sẵn `WD_M`, Wire Layers XDATA, `X-Zones 0..9` Model Space & `TITLE_BLOCK_A3_BILINGUAL`): [templates/TEMPLATE_IEC_A3.dwt](templates/TEMPLATE_IEC_A3.dwt)
   - Khung dự án mẫu `.wdp` chuẩn ACADE: [templates/TEMPLATE_PROJECT.wdp](templates/TEMPLATE_PROJECT.wdp)
   - Nhóm báo cáo tự động `.rgf` (`Automatic Reports`): [templates/project_master_reports.rgf](templates/project_master_reports.rgf)
   - Ánh xạ khung tên song ngữ: [templates/default_iec_bilingual.wdt](templates/default_iec_bilingual.wdt)
   - Định dạng cột báo cáo Panel BOM song ngữ: [templates/panel_bom_bilingual.set](templates/panel_bom_bilingual.set)
   - Danh mục chữ viết tắt chuẩn EN/VI: [templates/abbreviations_bilingual.csv](templates/abbreviations_bilingual.csv)
   - Dữ liệu gốc Catalog & Footprint chuẩn hãng: [templates/catalog_master_seed.csv](templates/catalog_master_seed.csv) & [templates/verified_footprints_catalog.csv](templates/verified_footprints_catalog.csv)
   - Bảng biển tên khắc Laser (`Nameplate Schedule`): [templates/nameplate_schedule.csv](templates/nameplate_schedule.csv)
   - Cấu hình ánh xạ cột PLC I/O (`.wdi`) & CSV mẫu (cột `BLOCK` dùng symbol ngoại vi thật `VSW11`, `VLT1A`, `VCR1`...): [templates/default_plc_io.wdi](templates/default_plc_io.wdi) & [templates/plc_io_import_template.csv](templates/plc_io_import_template.csv)
   - Nạp tự động Catalog, Footprint & PLC S7-1500 vào Access `.mdb` của ACADE qua ODBC: [scripts/seed_acade_databases.py](scripts/seed_acade_databases.py)
   - Kiểm toán điện trực tiếp trên Project Scratch Database `<project>.mdb` (`Database Gatekeeper`): [scripts/acade_electrical_audit.py](scripts/acade_electrical_audit.py)
   - Đồng bộ 2 chiều ACADE ↔ TIA Portal PLC Tags & xuất `AutomationML (.aml)`: [scripts/sync_tia_tags.py](scripts/sync_tia_tags.py)
   - Tự động sinh bản vẽ gia công cơ khí Busbar 2D CAM DXF (`1:1`, lỗ `DIN 43673`, `--from-csv`): [scripts/generate_busbar_dxf.py](scripts/generate_busbar_dxf.py)
   - Orchestrator khởi tạo dự án `.wdp`/`.dwg` thực trên AutoCAD Electrical 2027 qua COM/`c:wd_*` + kiểm tra va chạm 3D tủ điện: [scripts/build_project_drawings.py](scripts/build_project_drawings.py) & MCP **`autocad-direct`** (`C:\Users\Gaadz\.gemini\config\mcp_servers\autocad_mcp_server.py`)
