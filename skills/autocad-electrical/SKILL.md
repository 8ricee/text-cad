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

## ⛔ 10 RÀNG BUỘC CẤM TUYỆT ĐỐI CHO AGENT (HARD GUARDRAILS — FAIL-CLOSED)

1. **Cấm đặt Khung tên / Viền A3 trong `Model Space`:** `TITLE_BLOCK_A3_BILINGUAL` và viền ISO 5457 bắt buộc nằm 100% ở `Paper Space Layout ISO_A3` (`$TILEMODE=0`).
2. **Cấm cắt thiếu pha 3P+N+PE:** Mọi động cơ/biến tần 3 pha bắt buộc dùng `poles=3` (kèm nét đứt cơ khí `LINK`) hoặc `acade_insert_verified_circuit`; cấm lắp CB 1 cực trên `L1`.
3. **Cấm nối tắt AC ↔ DC hoặc chạm đất PE:** Tuyệt đối cách ly `L/N` với `+24VDC/0VDC` (chỉ qua PSU); chỉ điểm `0VDC` PELV được nối đất `PE` đúng 1 điểm.
4. **Cấm điền sai họ Block ACADE (`Family`):** `U/G/A` (VFD, PSU, PLC/Transmitter) chỉ dùng `VU1_VFD_3P` / `VG1_PSU_24V` / `VA1_*` / `HP1*`, cấm dùng `VCR1`/`HCR1`.
5. **Cấm dùng `Child` thay `Parent`:** Thiết bị độc lập bắt buộc dùng `V*1*`/`H*1*` (Parent `PAR1_CHLD2=1`), cấm dùng `V*2*`/`H*2*` nếu không có Parent cùng `TAG1`.
6. **Cấm để hở tải 1 chân hoặc đâm dây xuyên ký hiệu:** Luôn vẽ dây trước, chèn ký hiệu sau để ACADE tự cắt dây; tải `DO`/cuộn hút phải khép kín về `0VDC` (`CTRL_0VDC_BUWH_0.75`).
7. **Cấm dùng `ezdxf` vẽ Sơ đồ nguyên lý hoặc gõ cứng `BOM`/`Wire List`:** `ezdxf` chỉ dùng cho CAM Busbar DXF (`08_busbar_fabrication`); bảng biểu phải sinh từ `.mdb`.
8. **Cấm bịa kích thước Footprint hoặc để trống `MFG`/`CAT`:** Footprint phải tồn tại trong `Libs\panel\CUSTOM` hoặc `verified_footprints_catalog.csv` (Fail-Closed).
9. **Cấm bỏ qua `SPARE` / Dự phòng (20–30%):** Mọi tủ PLC bắt buộc chừa tối thiểu 20% kênh `SPARE` kéo sẵn ra cầu đấu dự phòng, và 1–2 nhánh MCB/feeder dự phòng trên Sơ đồ động lực.
10. **Cấm xuất bản nếu Gatekeeper `v3.2` (`acade_electrical_audit`) trả về bất kỳ lỗi nào (`passed = false`):** Bắt buộc sửa sạch 17 chỉ số về `0` trước khi bàn giao.

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
   - **Tách bạch Mạch Động lực (3P), Mạch Điều khiển (`Parent/Child` — Ký tự thứ 4 `1` vs `2`) & Cấm mượn Cuộn Rơ-le `VCR1`/`HCR1` sai họ thiết bị:**
     - **Ký tự thứ 4 của tên Block ACADE quyết định `Parent` (`1` -> `TAG1`) hay `Child` (`2` -> `TAG2`):** Cấm tuyệt đối truyền `TAG1` vào block `Child` (VD: cấm dùng `VMS2NA13F` cho MPCB chính vì ký tự thứ 4 là `2`; bắt buộc dùng `Parent` như `VCB11Q13` hoặc `VMS1NA21F`).
     - **Cấm tuyệt đối dùng cuộn rơ-le `VCR1`/`HCR1` để giả làm Biến tần (`-U*`), Bộ nguồn (`-G*`) hoặc PLC/Switch/HMI (`-A*`):** Bắt buộc dùng symbol chuyên dụng đúng họ IEC 60617 đã biên dịch sẵn trong `Libs\iec-60617\`: **`VU1_VFD_3P`** cho Biến tần (`-U*`), **`VG1_PSU_24V`** cho Bộ nguồn 24VDC (`-G*`), **`VA4_NET_BOX`** cho Switch PROFINET / HMI (`-A*`), **`VA1_WEIGH_TRANS`** cho bộ cân Load cell, và **`HP1W--L` / `HP1WA-D`** cho PLC I/O.
     - **Tách bạch Mạch Động lực Đa cực (`2P / 3P / 4P` — Cắt đủ mọi dây pha!) & Mạch Điều khiển (`Parent/Child`):**
       - **Cấm tuyệt đối vẽ MPCB/MCCB/MCB/Cầu chì/Contactor 3 pha chỉ gắn vào 1 dây pha `L1` rồi để `L2, L3` nối thẳng tắt từ lưới xuống động cơ!** Khi dùng `acade_insert_schematic_symbol`, bắt buộc truyền **`poles=3, pole_spacing=10.0`** cho thiết bị 3 pha (`VCB11Q13` -> tự ghép 3 cực `VCB11Q13 + 2×VCB21Q13` kèm nét đứt cơ khí `LINK` cắt đứt cả 3 dây `L1, L2, L3`; `VCR21` -> tự ghép 3 cực động lực; `VFU1` -> tự ghép `VFU1 + 2×VFU2`), và **`poles=2`** cho MCB 2P bảo vệ nguồn `L+N` (`-Q3`). Khuyến nghị ưu tiên gọi **`acade_insert_verified_circuit`** (`BUS_3PH_N_PE`, `DOL_3P`, `VFD_3P`, `PSU_24VDC_PELV`) để dựng mạch chuẩn không thể sai nguyên lý.
       - **Đấu nối đúng chân Động cơ 3 pha (`VMO13`) & Nguồn `24VDC PELV` (`VG1_PSU_24V`):**
         - `VMO13` có 3 chân pha ở phía trên (`(-6.4, +3.9)`, `(0, +7.5)`, `(+6.4, +3.9)`) và **chân thứ 4 ở đáy `(0, -7.5)` (`X8TERM04`) là chân tiếp địa vỏ `PE`!** Cấm tuyệt đối đặt cầu đấu hay đấu dây `PE` chạm vào đường dây pha `L3`!
         - Bộ nguồn `24VDC` (`VG1_PSU_24V`) bắt buộc nhận `L1 + N` qua `MCB 2P` ở chân trên (`L1, N`) + `PE`, và xuất `+24VDC` / `0VDC` cách ly hoàn toàn ở chân dưới, kèm cầu nối đất bảo vệ **`0VDC -> PE` (`Grounded PELV` theo IEC 60204-1)**. **Cấm tuyệt đối kéo thẳng dây Trung tính xoay chiều `N (PWR_N_*)` sang làm dây `0VDC (CTRL_0VDC_*)`!**

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
   - Trong file CSV của **`Spreadsheet to PLC I/O Utility`** (`AEPLCIO` / `acade_build_plc_from_csv`), vì các nhánh dây PLC I/O nằm ngang (`Horizontal Rungs`), linh kiện ngoại vi trên nhánh ngang dùng họ **`H*` ngang** (`HPB11`, `HSW11`, `HSW12`, `HPX1`, `HCR1`, `HLT1A`, `HSV1`; công cụ MCP tự động ánh xạ `V* -> H*`), bắt buộc đi qua cầu đấu trung gian `ht0001` (`-X2`/`-X3`) và **khép kín mạch 100% về thanh nguồn chung bên trái** (`+24VDC` cho ngõ vào `DI`, **`0VDC` `CTRL_0VDC_BUWH_0.75` kèm mũi tên `HA1D3`** cho ngõ ra `DO` nuôi tải 2 đầu dây) — **tuyệt đối không để hở 1 chân tải hoặc điền tên giả `PLC_DI_16` vào cột `BLOCK`**.
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
   - **Quy chuẩn Bắt buộc Tách biệt `Model Space` vs `Paper Space Layout (ISO_A3)` cho TOÀN BỘ Bản vẽ (`01..09` — Cấm đặt Khung tên trong Model Space!):**
     - **Model Space (`1:1 mm` sạch tuyệt đối):** Trên **tất cả mọi bản vẽ** (kể cả Sơ đồ nguyên lý `01..06`, `09` lẫn Panel Layout `07` và Busbar `08`), `Model Space` **chỉ chứa mạch điện / hình học thiết kế tỷ lệ thật `1:1 mm`** (`$INSUNITS = 4`) cùng duy nhất block cấu hình ẩn **`WD_M`** (`DATUMX=20, DATUMY=287, DISTH=39.5`). **TUYỆT ĐỐI CẤM vẽ Khung viền A3 hoặc chèn Khung tên `TITLE_BLOCK_A3_BILINGUAL` vào `Model Space`!**
     - **Paper Space (`Layout ISO_A3`, `420 × 297 mm`, `$TILEMODE = 0`):** **100% Khung viền ISO 5457 (`20 mm` lề trái, `5 mm` 3 lề còn lại), Thanh chia cột `X-Zones (0..9)`, Bảng biểu và Khung tên `TITLE_BLOCK_A3_BILINGUAL` (`WD_TB`) phải đặt trong tab `Layout ISO_A3`**, đi kèm cửa sổ **`VIEWPORT` đã khóa cứng (`Display Locked = ON`)**:
       - **Trang Sơ đồ nguyên lý, SLD, PLC I/O & Terminal (`01..06`, `09` — [templates/TEMPLATE_IEC_A3.dwt](templates/TEMPLATE_IEC_A3.dwt)):** `VIEWPORT` khóa cứng tỷ lệ **`1:1`** khớp tọa độ `(20..415, 5..287)` giữa Paper Space và Model Space (vừa giữ nguyên chuẩn Layout chuyên nghiệp, vừa khớp chính xác tuyệt đối 100% cột tham chiếu `/Trang.Cột` với `WD_M`!). Mọi linh kiện và chữ trong Model Space bắt buộc nằm gọn trong **Safe Zone `X ∈ [25..405]`, `Y ∈ [12..276]`** (và tránh góc dưới phải `[235..415, 5..45]` nơi có Khung tên).
       - **Trang Bố trí Mặt tủ & Gia công Thanh cái (`07_panel_layout`, `08_busbar_fabrication` — [templates/TEMPLATE_PANEL_LAYOUT_A3.dwt](templates/TEMPLATE_PANEL_LAYOUT_A3.dwt)):** `Model Space` dựng hình học cơ khí `1:1 mm` kèm thực thể **`DIMENSION` gốc AutoCAD** (`dimlfac = 1.0`, cấm vẽ tay `LINE` + `TEXT`); `Layout ISO_A3` chứa Khung tên và `VIEWPORT` khóa đúng tỷ lệ chuẩn ISO 5455 (`1:10`, `1:20`, `1:2.5`).
   - **Ký hiệu Đánh dấu Chuẩn Quốc tế (ISO 128 / ISO 6433 / ISO 5456-2):** Balloon dùng `ACI 7` kèm **chấm tròn đặc (`•`)** hoặc **mũi tên (`→`)**; hình cắt (`A-A`, `B-B`) có **Cutting Plane Line + mũi tên hướng nhìn**; chi tiết trích (`DETAIL A..D`) có **vòng tròn khoanh vùng**; Khung tên có **biểu tượng Góc chiếu (`ISO 5456-2`)**.
   - **Quy chuẩn Thực chiến Tủ điều khiển & Tấm lắp (`panel-sizing-and-busbar.md`):**
     - **Đủ mạch `3P+N+PE`, Cầu chì báo pha 3P (`-F1`, `2A`) & MCB 2P (`-Q3` cấp nguồn 230VAC cho bộ nguồn 24VDC/quạt):** Không bỏ quên dây `N` hoặc đấu đèn báo pha không qua cầu chì.
     - **Tủ nhỏ ($\le 63\text{A}–100\text{A}$) dùng Cầu đấu động lực / Domino (`-X0: L1, L2, L3, N, PE`) + 1 thanh đồng `PE` nhỏ:** Không lắp hệ thanh cái đồng 3 pha + sứ đỡ cồng kềnh cho tủ điều khiển nhỏ.
     - **Tách biệt Thiết bị Gài Ray (`DIN Rail TS35`) vs Thiết bị Bắt Vít vào Tấm lắp (`Base-Mounted`):** Không vẽ thanh DIN Rail `TS35` chạy xuyên dưới đáy MCCB khối, Biến tần VFD hay PLC S7-1500 (dùng ray nhôm S7-1500 riêng).
     - **Máng cáp nhựa (`Wire Duct`) ghép chữ T sát mép (`Butt-Joint`):** Máng ngang cắt dừng ở mép trong máng dọc.
   - **Liên kết Cơ–Điện 3D (`Autodesk Inventor Electromechanical Link` - `.emx`):** Khi dự án kết nối Inventor, khởi tạo file `.emx` thật bằng lệnh **`AEEMLINK`** của ACADE nối `.wdp` ↔ `.iam` (`RefDes ↔ TAG`, `Harness Pin ↔ TERMxx`). **Cấm tuyệt đối tự chế thẻ XML `.emx` giả lập bằng Python `ElementTree`.**
   - **Giới hạn đúng vai trò của `ezdxf` ([scripts/generate_busbar_dxf.py](scripts/generate_busbar_dxf.py)):** Chỉ dùng `ezdxf` cho **bản vẽ gia công cơ khí thanh cái 2D CAM (`08_busbar_fabrication`)** (tính `Bend Allowance` + lỗ `DIN 43673`), **tuyệt đối không bao giờ dùng `ezdxf` để dựng Sơ đồ nguyên lý (`01..06`, `09`) hay gõ cứng bảng `BOM` / `Wire List` / `Cross-Ref`.**
3. **Tự động hóa Native ACADE qua MCP `autocad-direct` (`v3.0.0` — Named Pipe → In-Process `.NET 10` Add-in `Agy.AutoCadBridge` + `c:wd_*` AutoLISP API), Chống lỗi Font `?` Tiếng Việt & Xuất PDF**:
   - **Khởi tạo & Dựng mạch 100% Native Database (`.wdp` + `.dwg` + Scratch `.mdb`):**
     - Mọi bản vẽ điện quản lý bằng định dạng **`.dwg`** nằm trong file dự án **`.wdp`** (copy từ [templates/TEMPLATE_IEC_A3.dwt](templates/TEMPLATE_IEC_A3.dwt) đã nhúng sẵn `WD_M` và `TITLE_BLOCK_A3_BILINGUAL`).
     - Sử dụng trực tiếp bộ tool chuyên biệt của MCP **`autocad-direct`** gọi thẳng AutoLISP API gốc của AutoCAD Electrical (nạp qua `wdload.lsp` → `(c:wd_load)`):
       1. **`acade_project_init`**: Sinh `.wdp` chuẩn IEC-60617, khởi tạo toàn bộ `.dwg` với `$TILEMODE=0` (Khung viền + `TITLE_BLOCK_A3_BILINGUAL` nằm 100% bên `Layout ISO_A3`, `Model Space` chỉ chứa `WD_M`: dùng `TEMPLATE_IEC_A3.dwt` `Viewport 1:1` cho trang nguyên lý và `TEMPLATE_PANEL_LAYOUT_A3.dwt` `Viewport 1:10` cho trang Panel Layout), ghi ngay `WD_M.SHEET` (`01..N`) + thuộc tính Khung tên và chạy `_AEREBUILDDB`.
       2. **`acade_insert_schematic_symbol`**: Hỗ trợ **`poles=1|2|3|4`** + `pole_spacing` (ghép tự động cực 1 `Parent` + cực 2..N `Child` kèm nét đứt cơ khí `LINK` cắt đủ cả 3 dây pha `L1,L2,L3`), kiểm tra **Safe Zone `[25..405, 12..276]`** chống tràn chữ, chặn `Child/Parent` & cấm `VCR1`/`HCR1` cho họ `U/G/A`, và tự cắt dây đâm xuyên linh kiện.
       3. **`acade_insert_verified_circuit`**: Dựng sẵn các cụm mạch công nghiệp chuẩn 100% DRC (`BUS_3PH_N_PE`, `DOL_3P`, `VFD_3P`, `PSU_24VDC_PELV`, `STAR_DELTA_3P`, `SAFETY_3SK1_2CH`).
       4. **`acade_draw_smart_wires_and_arrows`**: Vẽ dây thông minh qua `(c:wd_wire_quik)`, chống trùng `WDDOT` và chèn cặp `Source/Destination Signal Arrows` (`HA1S1` / `HA1D3`).
       5. **`acade_build_plc_from_csv`**: Chèn block `PLCIO` thật (`HP1W--L` + `HP1WA-D`, phân trang tự động 2 cột/trang qua `page_index` / `slot_filter` tại `my=256` không tràn khung A3, trả về `has_more_pages`), đổi `V* -> H*` cho nhánh ngang, thêm `ht0001` và khép kín mạch `+24VDC`/`0VDC`.
       6. **`acade_sync_panel_footprints`**: Truy vấn `+MAIN_PNL` & `+DOOR` từ `.mdb`, chuẩn hóa `MFG`, biên dịch Footprint `1:1 mm` từ `verified_footprints_catalog.csv` (**Fail-Closed** nếu mã chưa xác thực), hỗ trợ `enclosure_size` / `placements`, ép Layer `PNL_FOOTPRINT` và trả về `Layout ISO_A3` (`TILEMODE=0`).
       7. **`acade_run_reports_and_retag`**: Đánh số dây nút đẳng thế `%S%N`, đồng bộ `WD_M.SHEET` + `TITLE_BLOCK_A3_BILINGUAL` trong `PaperSpace` trên mọi trang và chạy `_AEREBUILDDB`.
       8. **`acade_place_db_reports_on_drawing`**: Truy vấn Scratch `.mdb` đặt bảng `AcDbTable` động trực tiếp lên `PaperSpace` (`TILEMODE=0`).
       9. **`acade_insert_cable_and_jumper`**: Chèn `Cable Marker` (`VW01`/`VW02`) và cầu đấu `ht0001` kèm XDATA Jumper.
       10. **`acade_electrical_audit`**: Thực thi **Gatekeeper v3.2 (Electrical Netlist DRC + PINLIST Quota & Dup Pins + Cross-Sheet SIGCODE Domain DRC + Terminal + Layout Gatekeeper)** kiểm toán đồng thời `.mdb` và toàn bộ `.dwg`.
   - **Bắt buộc cấu hình Font TrueType Unicode (`arial.ttf`, `isocpeur.ttf` hoặc `tahoma.ttf`) trên chuẩn `R2018 (UTF-8)`** cho Textstyle `Standard` / `WD_IEC` / `VN_ARIAL` (cấm để `txt.shx` gây lỗi `?` Tiếng Việt).
   - Ánh xạ Title Block bằng mẫu [templates/default_iec_bilingual.wdt](templates/default_iec_bilingual.wdt), chạy **`Title Block Update` (`AEUPDATETITLEBLOCK`)** đồng bộ toàn dự án và xuất gộp bằng **Publish → Plot Project to PDF**.

---

## 7. Checklist Chốt chặn Kiểm toán Điện (`Database Gatekeeper`) & Tài nguyên Thực thi

1. **Quản trị & Nạp tự động Cơ sở dữ liệu (`seed_acade_databases.py` & `AECATALOG`)**:
   - Trước khi dựng mạch, chạy [scripts/seed_acade_databases.py](scripts/seed_acade_databases.py) để nạp tự động dữ liệu `MFG` (viết IN HOA 100%), `CAT`, `_PINLIST` (Form C `4,...`), `ASSYCODE` vào `default_cat.mdb`, ánh xạ Footprint vào `footprint_lookup.mdb`, và mã module Siemens S7-1500/S7-1200 vào `ace_plc.mdb`.
2. **Gatekeeper Kiểm toán Điện & Bố cục v3.2 Bắt buộc (`acade_electrical_audit` — Fail-Closed nếu vi phạm)**:
   - Cuối mọi dự án, bắt buộc chạy `acade_electrical_audit` kèm `project_dir` (hoặc [scripts/acade_electrical_audit.py](scripts/acade_electrical_audit.py) `--mdb ... --project-dir ...`) truy vấn đồng thời **Scratch Database (`<project>.mdb`)** và dựng **Đồ thị Mạng điện (`Electrical Netlist DRC`)** trên từng file `.dwg` qua `accoreconsole.exe`, chặn cứng xuất bản (`exit 2`) nếu bất kỳ chỉ số nào `> 0`:
     - **`modelspace_titleblock_violations > 0`**: Đặt nhầm `TITLE_BLOCK_A3_BILINGUAL` trong `Model Space` hoặc lưu file ở `TILEMODE=1` thay vì tab `Layout ISO_A3` (`TILEMODE=0`).
     - **`short_circuit_nets > 0`**: Ngắn mạch chạm đất **`PE` chạm vào Pha `L1/L2/L3` / `N` / `+24VDC`**, chạm chập giữa các pha xoay chiều, hoặc **vi phạm cách ly nối thẳng `AC (L/N)` sang `DC (+24V/0VDC)`** không qua bộ nguồn!
     - **`unprotected_3phase_poles > 0`**: Động cơ 3 pha (`VMO13`) hoặc Biến tần (`VU1_VFD_3P`) có bất kỳ pha nào (`L1, L2, L3`) nối thẳng về thanh cái nguồn tổng mà không đi qua cực thiết bị đóng cắt bảo vệ (chặn lỗi chỉ lắp CB 1 cực trên `L1`).
     - **`text_or_attr_overflows > 0`**: Chữ hoặc thuộc tính tràn ra ngoài khung `[20..415, 5..287]` hoặc đè vào vùng Khung tên `[235..415, 5..41]`.
     - **`family_block_misuse > 0`**, **`unupdated_titleblocks > 0`**, **`wires_piercing_symbols > 0`**, **`open_circuit_loads > 0`**, **`panel_layout_violations > 0`**, **`pinlist_overuse_or_dup_pins > 0`**, **`cross_sheet_sigcode_mismatch > 0`**, **`duplicate_terminal_numbers > 0`**, **`missing_catalog > 0`**, **`duplicate_tags > 0`**, **`orphaned_child_contacts > 0`**, **`wire_errors > 0`**, **`schematic_vs_panel_discrepancy > 0`**.
3. **Đầy đủ 12 Bảng Chú thích & Báo cáo Tự động qua `.rgf` (`AEREPORTGROUP` -> `Put on Drawing`)**:
   - Sinh tự động từ Database qua [templates/project_master_reports.rgf](templates/project_master_reports.rgf) và `AEREPORT` (**cấm tuyệt đối** kẻ bảng `draw_grid_table()` gõ mảng chuỗi cứng cho BOM/Device Schedule/Wire List/Terminal Plan) theo [references/legends-and-schedules.md](references/legends-and-schedules.md) và [references/deliverables-and-fat.md](references/deliverables-and-fat.md).
4. **Tài nguyên Mẫu & Script Tự động hóa (`templates/` & `scripts/`):**
   - Cặp bản vẽ mẫu `.dwt` chuẩn **100% Paper Space `Layout ISO_A3` (`$TILEMODE=0`, `Model Space` sạch chỉ chứa `WD_M`, `VIEWPORT` khóa cứng)**: [templates/TEMPLATE_IEC_A3.dwt](templates/TEMPLATE_IEC_A3.dwt) (`1:1` cho Sơ đồ nguyên lý) & [templates/TEMPLATE_PANEL_LAYOUT_A3.dwt](templates/TEMPLATE_PANEL_LAYOUT_A3.dwt) (`1:10` cho Panel Layout)
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
   - Orchestrator khởi tạo dự án `.wdp`/`.dwg` thực trên AutoCAD Electrical 2027 qua Named Pipe In-Process `.NET 10` Add-in (`Agy.AutoCadBridge` + `c:wd_*`, hỗ trợ `Transaction` / `UndoMark` rollback nguyên tử) + kiểm tra va chạm 3D tủ điện: [scripts/build_project_drawings.py](scripts/build_project_drawings.py) & MCP **`autocad-direct`** (`C:\Users\Gaadz\.gemini\config\mcp_servers\autocad_mcp_server.py`)
