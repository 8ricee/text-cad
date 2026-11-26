# Cấu trúc Bộ Hồ sơ Hoàn chỉnh & Checklist Nghiệm thu Xuất xưởng (FAT)

Quy chuẩn đóng gói đầy đủ các trang bản vẽ trong một bộ hồ sơ tủ điện công nghiệp và quy trình kiểm tra nghiệm thu nguội/nóng tại xưởng (**FAT - Factory Acceptance Test**).

---

## 1. Cấu trúc Thứ tự Trang Chuẩn của 1 Bộ Bản vẽ Tủ Điện

Trong **Project Manager (`.wdp`)**, các trang bản vẽ `.dwg` được sắp xếp theo trình tự logic sau:

| STT File | Tên trang đề xuất (ASCII) | Nội dung bắt buộc |
| :---: | :--- | :--- |
| `01` | `01_cover_and_index.dwg` | Trang bìa, Bảng danh mục bản vẽ (`Drawing Index`), Thông số kỹ thuật tổng của tủ ($U_n$, $f$, $I_n$, $I_{cu}$, `IP`, Màu sơn, Kích thước). |
| `02` | `02_legend_and_abbreviations.dwg` | Bắt buộc có đủ 3 bảng chuẩn theo [legends-and-schedules.md](legends-and-schedules.md): (1) Bảng Ký hiệu Thiết bị (`Symbols Legend` lấy từ Icon Menu), (2) Bảng Chữ viết tắt song ngữ (`Abbreviations Table` từ `abbreviations_bilingual.csv`), (3) Bảng Quy ước Màu dây & Tiết diện (`Wire Color & Size Legend`). |
| `03` | `03_single_line_diagram.dwg` | Sơ đồ đơn tuyến (`SLD` - Bắt buộc cho tủ MSB, DB lớn, Tủ tổng hợp). |
| `04` | `04_power_distribution.dwg` | Sơ đồ nguyên lý mạch động lực 3 pha + Bảng Danh mục Thiết bị theo trang (`Per-Sheet Device Schedule` ở góc dưới trái qua `AEREPORT`). |
| `05` | `05_control_schematic.dwg` | Sơ đồ nguyên lý mạch điều khiển, liên động + Bảng Tiếp điểm `Graphical Format` dưới cuộn dây + Bảng Trạng thái Công tắc xoay (`Selector Switch Truth Table`). |
| `06` | `06_plc_io_wiring.dwg` | Sơ đồ đấu nối các module PLC DI/DO/AI/AO và mạng truyền thông (nếu có). |
| `07` | `07_panel_layout.dwg` | Bản vẽ bố trí tủ 2D dựng **`1:1 mm` trong Model Space** + trình bày qua **Paper Space `Layout Viewport`**, gắn 100% **`DIMENSION` gốc AutoCAD** (cấm vẽ tay `LINE`+`TEXT`) cho Mặt cánh tủ, Tấm lắp trong, Mặt cắt hông kèm số `Balloon` + **5 bảng bắt buộc**: (1) `Panel BOM` (`panel_bom_bilingual.set`), (2) `Nameplate Schedule` (`nameplate_schedule.csv`), (3) `Door Cutout & Indicator Legend`, (4) `Enclosure Data Block`, (5) `General Panel Notes` song ngữ. |
| `08` | `08_busbar_fabrication.dwg` | Bản vẽ chi tiết gia công thanh cái đồng dựng **`1:1 mm` trong Model Space** + **Paper Space `Layout Viewport`**, gắn 100% **`DIMENSION` gốc AutoCAD** cho chiều dài khai triển, bề rộng, độ dày, tọa độ & đường kính lỗ `DIN 43673`, bước pha CT, sứ đỡ, tấm che Mica `IP2X` + **2 bảng bắt buộc**: (1) `Busbar Cut List`, (2) `Busbar Hardware & Torque Schedule` (Bu-lông, Sứ đỡ, Lực siết `N·m`). |
| `09` | `09_terminal_and_cable_list.dwg` | Bảng cầu đấu (`Terminal Plan`) & Bảng danh sách cáp/dây (`From-To Wire List`). |
| `10` | `10_load_schedule_and_bom.xlsx` | Bảng phân tải (`Load Schedule` - cân pha) & Bảng tổng hợp vật tư (`BOM` đầy đủ `MFG`, `CAT`, `QTY`). |

---

## 2. Checklist Nghiệm thu Xuất xưởng (FAT Checklist)

Trước khi đóng gói xuất xưởng tủ điện, bắt buộc kiểm tra qua **4 nhóm hạng mục**:

### A. Kiểm tra Cơ khí & Hoàn thiện (Mechanical & Visual)
- [ ] Kích thước phủ bì vỏ tủ, độ dày tôn, màu sơn (`RAL 7035` / `RAL 3000` cho PCCC) và cấp bảo vệ `IP` đúng bản vẽ duyệt.
- [ ] Cửa tủ đóng mở êm, có dây tiếp địa mềm nối giữa cánh tủ và thân tủ.
- [ ] Tấm che bảo vệ **Mica / Polycarbonate `IP2X`** lắp đầy đủ trước thanh cái tổng và đầu cực ACB/MCCB, có tem cảnh báo điện áp cao.
- [ ] Đầy đủ biển tên thiết bị mặt ngoài (Mica 2 lớp khắc Laser song ngữ) và nhãn `TAG` bên trong khớp 100% với Sơ đồ nguyên lý.
- [ ] **Đối chiếu thực tế 100% với Bảng Biển tên (`Nameplate Schedule`):** Kiểm tra từng biển tên về nội dung chữ Tiếng Anh / Tiếng Việt, kích thước (`W×H mm`), màu nền/màu chữ và cỡ chữ đúng theo bảng thiết kế.

### B. Kiểm tra Lực siết & Đấu nối (Terminations & Torque)
- [ ] Toàn bộ bu-lông thanh cái đồng (Busbar) đã siết đúng lực chuẩn (`Torque Wrench`) và **đánh dấu vạch sơn (`Torque Seal`)**.
- [ ] Không có hiện tượng chồng quá 2 đầu cosse lên 1 điểm bắt trên thanh cái; khoảng cách pha–pha đạt chuẩn ($\ge 15\text{–}20\text{ mm}$).
- [ ] 100% dây điều khiển bấm đúng loại cosse (`Pin/Fork/Ring`) và lồng **ống đánh số đầu dây (`Ferrule`)** khớp số dây `AEWIRENO` trên bản vẽ.

### C. Kiểm tra Điện nguội (Dead Tests - Không cấp nguồn)
- [ ] **Đo thông mạch (`Continuity Test`):** Kiểm tra từng mạch động lực và điều khiển theo đúng sơ đồ nguyên lý, đảm bảo không đấu nhầm chân, không chạm chập.
- [ ] **Đo điện trở cách điện (`Insulation / Megger Test`):** Đo giữa Pha–Pha và Pha–Đất ở điện áp thử $500\text{VDC}$ hoặc $1000\text{VDC}$ (đạt chuẩn $\ge 1\text{–}100\text{ M}\Omega$).
  - *Lưu ý an toàn:* **Bắt buộc tháo/cách ly** PLC, Biến tần, Bộ nguồn 24VDC, Đồng hồ MFM, Bộ chống sét SPD trước khi bấm máy đo Megger.

### D. Kiểm tra Có điện không tải (Live Functional Tests)
- [ ] Kiểm tra đúng thứ tự pha `L1-L2-L3`, điện áp nguồn điều khiển (`220VAC`, `24VDC`).
- [ ] Kiểm tra chiều cực tính biến dòng CT (`P1→P2`) và giá trị hiển thị trên đồng hồ MFM / bộ điều khiển tụ bù APFC.
- [ ] Thử nghiệm thực tế toàn bộ logic liên động: Nút dừng khẩn `E-Stop`, khóa liên động cơ/điện (ATS, Sao–Tam giác), trạng thái `AUTO - OFF - MAN`, tín hiệu báo cháy FACP (với tủ PCCC) và giả lập I/O trên PLC.
