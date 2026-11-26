# Quy chuẩn Tính toán Kích thước Tủ, Thanh cái & Tản nhiệt

Tài liệu tham khảo cho việc lên cấu hình vỏ tủ, tấm lắp thiết bị (Mounting Plate), thanh cái đồng (Busbar) và giải pháp tản nhiệt.

---

## 1. Quy trình 5 Bước Lên Cấu Hình Tủ Điện từ BOM

### Bước 1: Phân nhóm Thiết bị từ Sơ đồ nguyên lý (BOM)
Xuất danh sách thiết bị kèm kích thước thực tế (`W × H × D` theo Datasheet/CAD hãng) và phân thành 4 vùng:
1. **Vùng Động lực:** MCCB tổng, MCB nhánh, Contactor, Biến tần (VFD), Servo Drive, Bộ lọc EMI.
2. **Vùng Điều khiển & Truyền thông:** Nguồn 24VDC, PLC, Module I/O, Relay trung gian, Switch mạng.
3. **Vùng Cầu đấu & Tiếp địa:** Cầu đấu động lực/điều khiển (`-X1`, `-X2`), thanh `PE`, thanh `N`.
4. **Vùng Cánh tủ:** HMI, Đồng hồ đo, Đèn báo, Nút nhấn, Công tắc xoay, Quạt hút/Lọc gió.

### Bước 2: Tính Kích thước Tấm lắp (Mounting Plate)
- **Chiều rộng ($W$):**
  $$W_{\text{tấm lắp}} \ge \max(\text{Tổng bề rộng thiết bị trên 1 hàng}) \times (1.2 \div 1.3) + 2 \times \text{Lề mép tủ}$$
  *(Luôn chừa **20%–30% không gian dự phòng (Spare space)** trên mỗi hàng DIN Rail).*
- **Chiều cao ($H$) & Bán kính Uốn Cáp Tối thiểu (`Minimum Cable Bending Radius`):**
  $$H_{\text{tấm lắp}} \ge \sum H_{\text{hàng thiết bị}} + \sum H_{\text{máng cáp}} + \sum H_{\text{khe hở thao tác}} + \sum H_{\text{tản nhiệt}} + H_{\text{uốn cáp đáy/đỉnh}}$$
  - Máng cáp (Wire Duct): Rộng `40–80 mm`, sâu `60–80 mm`.
  - Khe hở thao tác cho dây điều khiển nhỏ ($\le 6\text{ mm}^2$): Tối thiểu `25–40 mm` giữa thiết bị và máng cáp ($R_{\text{min}} \approx 4 \div 6 \times OD$).
  - **Không gian uốn cáp động lực lớn (`Cable Bending Space`, $R_{\text{min}} = 8 \div 12 \times OD$ cho cáp đồng XLPE/PVC và $12 \div 15 \times OD$ cho cáp ngầm có giáp `DSTA/SWA`):** Khoảng cách từ đầu cực ACB/MCCB tổng hoặc thanh cái xuống tấm bích đáy (`Gland Plate`) bắt buộc chừa tối thiểu:
    - Cáp `25 – 50 mm²`: $\ge 150 – 200\text{ mm}$
    - Cáp `70 – 120 mm²`: $\ge 250 – 350\text{ mm}$
    - Cáp `150 – 240 mm²`: $\ge 400 – 550\text{ mm}$ (kết hợp chân đế tủ `Base Plinth 100–200 mm`).
  - Khoảng hở tản nhiệt của Biến tần / Servo / Nguồn: Theo đúng Datasheet (thường `50–100 mm` phía trên và dưới).
- **Quy chuẩn Bố trí Máng cáp Nhựa (`Wire Duct`), Thanh cài (`DIN Rail`) & Thiết bị Bắt Vít Trực tiếp (`Base-Plate Mounting`):**
  1. **Cấm vẽ máng cáp nhựa đè chồng lên nhau tại ngã ba / ngã tư (`Butt-Joint T-Intersection`):**
     - Hai thanh máng cáp dọc ở hai biên trái/phải chạy suốt chiều cao tấm lắp; các thanh máng cáp ngang ở giữa **chỉ cắt từ mép trong của máng dọc trái đến mép trong của máng dọc phải** (ghép chữ T sát mép), tuyệt đối không vẽ 2 lớp máng nhựa đè xuyên qua nhau tại góc giao cắt.
  2. **Phân biệt rõ Thiết bị Gài Ray (`DIN Rail TS35`) và Thiết bị Bắt Vít vào Tấm lắp (`Base-Mounted`):**
     - **Thiết bị bắt ốc vít trực tiếp vào tấm lắp (`M4 / M5 / M6`):** MCCB khối (`3VA1`...), Biến tần công suất (`SINAMICS G120C` FSB trở lên), Biến áp, Bộ lọc EMI, hoặc PLC `S7-1500` (dùng thanh ray nhôm chuyên dụng `S7-1500 Mounting Rail` bắt vít riêng). Trên bản vẽ phải thể hiện rõ **tai lỗ bắt vít ở các góc đế thiết bị** và **tuyệt đối KHÔNG vẽ thanh DIN Rail `TS35` chạy xuyên qua dưới đáy các thiết bị bắt vít này**.
     - **Thiết bị gài thanh DIN Rail (`TS35×7.5 mm`):** Cầu chì báo pha 3P (`-F1`), MCB/MPCB nhỏ, Contactor nhỏ, Nguồn xung 24VDC, Rơ-le an toàn, Bộ cân, Cầu đấu. Thanh DIN Rail **chỉ cắt vừa đúng chiều dài của cụm thiết bị gài ray (+ `15%–20%` dự phòng)**, không để dư thanh ray trống trải dài vô nghĩa, và phải khóa 2 đầu bằng chặn cuối ray (`CLIPFIX 35`).
  3. **Kiến trúc Tấm lắp ghép phân đoạn & Chia tủ 2 lớp Trong / Ngoài (`Dual-Layer Segmented Modular Mounting Plates`):**
     - Đối với tủ động lực tổng / tủ điều khiển lớn (VD: `2000 × 1200 × 800 mm`) hoặc khi yêu cầu kết cấu lắp ghép module: **Không sử dụng 1 tấm lắp liền khổ lớn** nặng nề khó tháo lắp, mà chia thành **các tấm lắp ghép phân đoạn độc lập** (VD: `6 tấm Phần Trong 510 × 540 × 20 mm` + `6 tấm Phần Ngoài 510 × 420 × 20 mm`, tôn dày `2.5 mm` chấn gấp 4 cạnh chữ C cao `20 mm` kèm gân tăng cứng), bắt bằng tán cài lò xo `M8 (Cage Nut)` lên hệ trụ đứng đột lỗ bước `25 mm`.
     - **Chia chiều sâu tủ (`D = 800 mm`) thành 2 phần đều gá được thiết bị:**
       - **Phần Trong (`Inner Mounting Zone` tại `Z ≈ 135 mm`):** Gá các thiết bị động lực/cầu đấu/thanh cái với khoảng không gian sâu `350 mm` đến lớp ngoài.
       - **Phần Ngoài (`Outer Swing/Modular Mounting Zone` tại `Z ≈ 485 mm`):** Gá trên hệ khung trụ đứng trung gian, khoảng không gian sâu `290–315 mm` đến mặt cánh cửa trước. Mỗi tấm lắp ghép Phần Ngoài có **bản lề xoay mở `120°`** ở biên ngoài và **ốc khóa nhanh `M8`** ở trụ giữa để vừa gá thiết bị lớp ngoài vừa mở ra thao tác dễ dàng với thiết bị Phần Trong.
  4. **Tự động hóa 100% Vẽ Trực Tiếp Trên Tab AutoCAD Đang Mở (`Zero-Touch Live In-Tab AutoCAD Sync`):**
     - Khi người dùng đang mở trực tiếp file `.dxf` / `.dwg` trên AutoCAD, **cấm tạo thêm thư mục phụ** (`DXF_Updated/`, `01_Drawings_Updated/`). Sử dụng hàm `save_dxf_zero_touch_in_place(doc, out_path)` trong `scripts/live_autocad_sync.py` để tự động kết nối vào `Default` Desktop (`OpenDesktopW` + `SetThreadDesktop`), tìm cửa sổ `AfxMDIFrame140u` của AutoCAD và bắn lệnh `WM_COPYDATA` nạp `_DXFIN`, `ZOOM Extents`, `REGENALL` và `_SAVEAS` đè trực tiếp ngay bên trong tab đang mở.
- **Chiều sâu ($D$):**
  $$D_{\text{vỏ tủ}} \ge D_{\text{thiết bị sâu nhất}} + \text{Khoảng hở tấm lắp đến lưng} + D_{\text{thiết bị gắn cánh}} + 30\text{ mm dự phòng}$$

### Bước 3: Chọn Vỏ tủ Chuẩn Thương mại & Cấp Bảo vệ (IP)
Quy tròn lên kích thước vỏ tủ thương mại chuẩn:
- **Tủ treo tường / cỡ vừa (`W×H×D` mm):** `400×300×200`, `500×400×250`, `600×400×250`, `800×600×300`, `1000×800×300`, `1200×800×350`.
- **Tủ đứng công nghiệp (`W×H×D` mm):** Cao `1800 / 2000 / 2200 mm`, Rộng `600 / 800 / 1000 / 1200 mm`, Sâu `500 / 600 / 800 / 1000 mm` (ghép module nếu là tủ tổng hợp).
- **Cấp bảo vệ (IP) & Vật liệu:**
  - Trong nhà (Indoor, phòng điện sạch): Tối thiểu `IP42` – `IP54`, thép sơn tĩnh điện `RAL 7035`.
  - Nhà xưởng nhiều bụi/ẩm hoặc ngoài trời (Outdoor có mái che): `IP55` – `IP65`.
  - Môi trường hóa chất / thực phẩm / ven biển: Inox `SUS304` hoặc `SUS316`.
  - Tủ PCCC: Bắt buộc sơn màu đỏ **`RAL 3000`**.

---

## 2. Quy chuẩn Đầu vào Nguồn (`3P+N+PE`), Cầu chì Báo pha & Thanh cái Đồng (Busbar)

### A. Khi nào dùng Cầu đấu Động lực / Domino (`≤ 63A–100A`) vs Thanh cái Đồng (`≥ 100A`)
1. **Tủ điều khiển nhỏ / ít lộ tải ($\le 63\text{A}–100\text{A}$):**
   - **Không dùng hệ thống thanh cái đồng 3 pha + sứ đỡ cồng kềnh cho đầu vào.**
   - Sử dụng **Cầu đấu động lực / Domino khối (`-X0: L1, L2, L3, N, PE`)** hoặc **Khối chia nguồn (`Distribution Block 4P` gắn DIN rail)** để đấu cáp nguồn tổng và chia ra các nhánh, kết hợp **1 thanh đồng Tiếp địa `PE` nhỏ (`Cu 20×3` hoặc `25×5 mm` dài `180–250 mm`)** bắt ở góc dưới tấm lắp để nối đất vỏ tủ và kẹp giáp chống nhiễu `SK 14`.
2. **Bắt buộc có Đường Trung tính (`N`), Cầu chì Báo pha 3P (`-F1`) & MCB Nguồn điều khiển (`-Q3`):**
   - Mọi tủ điện có thiết bị 1 pha `220/230VAC` (Bộ nguồn xung 24VDC `-G1`, Đèn báo pha `L1-L2-L3`, Quạt hút làm mát, Ổ cắm/Đèn soi tủ) **bắt buộc phải có đường Trung tính (`N` – dây/cầu đấu màu xanh dương `BU`)** đi kèm 3 pha (`3P+N+PE`).
   - **Bắt buộc lắp Bộ 3 Cầu chì Bảo vệ Đèn báo pha (`-F1`, `3P Cylindrical Fuse Holder 10×38 mm 2A`)** trích ngay sau đầu vào tổng để bảo vệ ngắn mạch cho 3 đèn báo pha trên cánh tủ.
   - **Bắt buộc có MCB 2P (`L-N`, `6A–10A`, `-Q3`)** bảo vệ riêng nhánh cấp nguồn `230VAC` cho Bộ nguồn 24VDC (`-G1`) và Quạt làm mát tủ.

### B. Tính toán Thanh cái Đồng (Áp dụng cho tủ MSB, DB lớn, ATS, Tụ bù có $I_n \ge 100\text{ A}$)

1. **Mật độ dòng điện cho phép (Đồng thanh cái $E-Cu$):**
   - Trong môi trường tủ kín thông thường ($T_{\text{ambient}} = 35^\circ\text{C} - 40^\circ\text{C}$): Chọn mật độ dòng thiết kế an toàn **$1.2 \div 1.6\text{ A/mm}^2$** (tùy tiết diện và số thanh ghép song song).
   - *Ví dụ tham khảo nhanh (1 thanh/pha):*
     - `20×3 mm` ($60\text{ mm}^2$) $\rightarrow \sim 100\text{ A}$
     - `30×5 mm` ($150\text{ mm}^2$) $\rightarrow \sim 250\text{ A}$
     - `40×5 mm` ($200\text{ mm}^2$) $\rightarrow \sim 320\text{ A}$
     - `50×10 mm` ($500\text{ mm}^2$) $\rightarrow \sim 630\text{–}800\text{ A}$
     - `80×10 mm` hoặc `2 × (60×10) mm` $\rightarrow \sim 1250\text{–}1600\text{ A}$
2. **Thanh Trung tính (`N`) & Tiếp địa (`PE`):**
   - Thanh `N`: Tối thiểu bằng **50%–100%** tiết diện thanh pha (bắt buộc **100%** nếu tải có nhiều sóng hài/biến tần/đèn LED).
   - Thanh `PE`: Tối thiểu **50%** tiết diện thanh pha (hoặc tính theo công thức chịu dòng sự cố ngắn mạch).
3. **Đánh dấu màu pha & Cách điện (Tách rõ 2 hệ tiêu chuẩn):**
   | Pha / Dây | Hệ TCVN / Nhà máy VN | Hệ Quốc tế IEC 60445 |
   | :---: | :--- | :--- |
   | **`L1`** | Đỏ (Red) | Nâu (Brown) |
   | **`L2`** | Vàng (Yellow) | Đen (Black) |
   | **`L3`** | Xanh dương (Blue) | Xám (Grey) |
   | **`N`** | Đen (Black) hoặc Trắng | Xanh dương (Blue) |
   | **`PE`** | Vàng sọc Xanh lá (Yellow-Green) | Xanh lá sọc Vàng (Green-Yellow) |
   *(Thống nhất chọn 1 hệ màu duy nhất trong suốt dự án và ghi chú rõ trên trang `Legend`).*
4. **Khoảng cách cách điện (Clearance & Creepage):**
   - Đảm bảo khoảng cách không khí pha–pha và pha–đất $\ge 15\text{–}20\text{ mm}$ cho điện áp $400/690\text{VAC}$; sử dụng sứ đỡ (Insulator) chịu lực ngắn mạch ($I_{\text{pk}}$).

---

## 3. Tính toán Nhiệt Định lượng & Giải pháp Làm mát (IEC 60890)

1. Cộng tổng công suất tỏa nhiệt ($P_{\text{loss}}$, đơn vị `W`) của tất cả thiết bị sinh nhiệt trong tủ (Biến tần ~ 3–5% công suất định mức, Nguồn DC, PLC, Contactor, Thanh cái, Tụ bù).
2. Xác định chênh lệch nhiệt độ cho phép: $\Delta T = T_{\text{trong\_tủ\_max}} - T_{\text{môi\_trường\_ngoài}}$ ($\text{K}$ hoặc $^\circ\text{C}$).
3. Tính diện tích tản nhiệt hiệu dụng vỏ tủ ($A_e$, $\text{m}^2$ theo IEC 60890) và chọn giải pháp làm mát:
   - **Tản nhiệt tự nhiên:** Khi $P_{\text{loss}} \le k \cdot A_e \cdot \Delta T$ (với $k \approx 5.5\text{ W/m}^2\text{K}$ cho thép sơn tĩnh điện) và nhiệt độ bên trong tính toán $\le 40^\circ\text{C}$.
   - **Quạt hút + Lọc gió (Filter Fan + Exhaust Filter):** Khi cần cưỡng bức đối lưu, tính lưu lượng gió cần thiết theo công thức định lượng:
     $$V_{\text{fan}}\ (\text{m}^3/\text{h}) \approx \frac{3.1 \times P_{\text{loss}}\ (\text{W})}{\Delta T\ (\text{K})}$$
     *(Gợi ý chọn cỡ quạt theo lưu lượng có xét tổn thất qua tấm lọc: `120×120 mm` $\sim 35\text{–}55\text{ m}^3/\text{h}$, `150×150 mm` $\sim 100\text{–}150\text{ m}^3/\text{h}$, `250×250 mm` $\sim 250\text{–}500\text{ m}^3/\text{h}$).* Đặt lọc gió hút ở **cạnh dưới** và quạt đẩy khí nóng ở **cạnh trên**.
   - **Điều hòa tủ điện (Enclosure Air Conditioner):** Khi $T_{\text{môi\_trường}} \ge T_{\text{trong\_tủ\_max}}$ (xưởng nóng $\ge 40^\circ\text{C}$), môi trường nhiều bụi/hơi dầu bắt buộc đóng kín tủ (`IP54/IP55`), hoặc tổng $P_{\text{loss}}$ quá lớn.

---

## 4. Phân cấp Busbar Tổng & Busbar Nhánh cho MCB

Tuyệt đối **không đục lỗ chi chít lên thanh cái chính** để kéo dây vào từng MCB nhánh. Trên bản vẽ thiết kế tủ điện, phân chia rõ thành **3 cấp Busbar**:

1. **Busbar Tổng (Main Busbar, $\ge 250\text{A}$ – ACB / MCCB lớn):**
   - Dùng thanh đồng dày (`30×5` đến `2×100×10` mm), gia công cắt – đột lỗ `M8 – M16` theo chuẩn `DIN 43673` và uốn định hình tỷ lệ `1:1` để nối trực tiếp vào đầu cực ACB/MCCB tổng và các MCCB nhánh lớn ($\ge 100\text{A}$).
2. **Busbar Nhánh đục lỗ / Khối chia nguồn (Sub-busbar / Distribution Block, $80\text{A}–250\text{A}$):**
   - Dùng khi cấp nguồn từ thanh chính ra nhiều nhánh MCB/MCCB nhỏ:
     - **Phương án A (Khuyên dùng):** Dùng **Khối chia nguồn (Distribution Block)** gắn DIN rail (1 đầu vào lớn từ thanh chính, nhiều đầu ra `M4/M5/M6` cho từng MCB).
     - **Phương án B (Gia công thanh đồng nhánh):** Dùng thanh đồng nhỏ (`15×3`, `20×3`, `20×5` mm) đột sẵn dãy lỗ **`M5 / M6` cách đều theo bước module `18 mm` (bước MCB 1P) hoặc `27 mm`**, bắt dây đầu cosse (`Pin / Fork / Ring`) vào từng MCB.
3. **Thanh cái lược (Comb Busbar, $\le 100\text{A}$ – Dãy MCB liền kề):**
   - Dùng cho dãy MCB 1P/2P/3P/4P lắp cạnh nhau trên cùng 1 thanh DIN rail.
   - **Không gia công đục lỗ**, chọn đúng mã thanh cái lược chuẩn hãng (chân `Pin` hoặc `Fork`), bắt buộc kèm **nắp bịt đầu cách điện (`End Cap`)** và **kẹp cấp nguồn (`Feed-in Terminal`)** trong Panel BOM.

---

## 5. Quy chuẩn Gia công Đục lỗ Busbar (DIN 43673), Bu-lông & Bắt đầu Cosse

### A. Bảng tra Đục lỗ & Cỡ Bu-lông theo Bề rộng Thanh cái
| Bề rộng thanh cái ($W$) | Cỡ Bu-lông chuẩn | Đường kính lỗ đột ($D$) | Số lỗ & Bố trí | Ứng dụng phổ biến |
| :---: | :---: | :---: | :--- | :--- |
| `15 – 20 mm` | **M6** / **M8** | `Ø6.8` / `Ø9.0 mm` | 1 lỗ chính giữa | Thanh nhánh, thanh `N`/`PE` bắt cosse `≤ 35 mm²` |
| `25 – 30 mm` | **M8** / **M10** | `Ø9.0` / `Ø11.0 mm` | 1 lỗ chính giữa | Thanh cái `160A–250A`, bắt cosse `35–95 mm²` |
| `40 – 50 mm` | **M10** / **M12** | `Ø11.0` / `Ø13.5 mm` | 1 hoặc 2 lỗ (thẳng / so le) | Thanh cái `320A–630A`, đầu cực MCCB |
| `60 – 80 mm` | **M10** / **M12** | `Ø11.0` / `Ø13.5 mm` | 2 lỗ dọc hoặc 4 lỗ (ghép nối) | Thanh cái `800A–1250A` |
| `100 mm` | **M12** / **M16** | `Ø13.5` / `Ø17.5 mm` | 4 lỗ (ô vuông nối thanh chính) | Thanh cái tổng `1600A–3200A`, đầu cực ACB |

### B. Nguyên tắc Cơ khí & Độ bền Thanh cái
- **Khoảng cách mép lỗ:** Tâm lỗ đến mép thanh tối thiểu $\ge 1.5 \times D_{\text{lỗ}}$ (thường $\ge 12\text{–}15\text{ mm}$) để tránh xé đồng khi siết lực hoặc khi có lực điện động ngắn mạch.
- **Giới hạn tiết diện mất đi:** Tổng đường kính các lỗ trên cùng một mặt cắt ngang không vượt quá **20%–25% bề rộng thanh cái** để tránh phát nóng cục bộ.
- **Chiều dài chồng mép nối thanh (Overlap Joint):** Tối thiểu bằng bề rộng thanh cái ($L_{\text{chồng}} \ge W_{\text{busbar}}$).

### C. Quy chuẩn Bắt đầu Cosse (Cable Lug) & Siết lực (Torque)
- **Giới hạn xếp chồng Cosse:** Không chồng 3–4 đầu cosse về cùng một phía. Tối đa chỉ bắt **2 đầu cosse đấu lưng vào nhau (Back-to-back)** ở 2 mặt trước/sau của thanh cái.
- **Phụ kiện bu-lông & Lực siết:** Dùng bu-lông thép cường độ cao **8.8 mạ kẽm** hoặc **Inox A2-70**, bắt buộc có **Long đền phẳng cỡ lớn + Long đền vênh (Spring/Belleville Washer)**. Siết bằng cờ-lê lực (`M6: 9 Nm`, `M8: 22 Nm`, `M10: 42 Nm`, `M12: 72 Nm`) và đánh dấu vạch sơn (`Torque Seal`).
- **Mặt tiếp xúc:** Sạch oxit đồng, không dính sơn cách điện hay ống co nhiệt đè vào bề mặt ép cosse.

---

## 6. Ranh giới Thể hiện trên Bản vẽ 2D (Schematic vs Fabrication)

1. **Bản vẽ Sơ đồ Nguyên lý (Schematic 2D):**
   - **Không** vẽ lỗ đột hay chi tiết bu-lông/cosse. Chỉ ghi chú quy cách thanh cái (VD: `BUSBAR L1,L2,L3: Cu 50×10mm`, `N: Cu 40×5mm`, `PE: Cu 30×5mm`) và loại thanh chia / thanh cái lược nếu có.
2. **Bản vẽ Thiết kế Tủ & Gia công Đồng (Panel Layout & Busbar Fabrication Drawing 2D):**
   - **Model Space bắt buộc `1:1 mm` tuyệt đối (`$INSUNITS = 4`) + Paper Space `Layout` (`Viewport`) + `DIMENSION` gốc AutoCAD:**
     - **Cấm co nhỏ hình học trong Model Space và cấm vẽ tay kích thước bằng `LINE` + `TEXT`.** Mọi chi tiết vỏ tủ, tấm lắp, thiết bị, thanh cái, lỗ đột, CT, sứ đỡ đều vẽ `1:1 mm` trong Model Space, dùng `DIMENSION` thật của AutoCAD (`dimlfac = 1.0`), và trình bày khung tên/bảng biểu trên Paper Space `Layout` qua `Viewport` tỷ lệ chuẩn.
     - **Bản vẽ bố trí tủ (Panel Layout):** Mặt cánh tủ, tấm lắp bên trong, mặt cắt hông, vị trí thanh cái chính, thanh cái nhánh/khối chia nguồn, thanh cái lược MCB và đánh số `Balloon`.
     - **Bản vẽ chi tiết gia công đồng (Busbar Detail):** Khai triển thanh đồng `1:1 mm` kèm **kích thước `DIMENSION` thật đo tọa độ tâm lỗ, đường kính lỗ đột (`Ø`), chiều rộng, độ dày, bán kính/góc uốn** và bảng tổng hợp phụ kiện (bu-lông, long đền, sứ đỡ, co nhiệt) phục vụ xưởng cắt – đột – uốn chính xác.

---

## 7. Quy chuẩn Bố trí Busbar cho Biến dòng (CT - Current Transformer)

Khi tủ có lắp đặt **Biến dòng đo lường / bảo vệ (CT)**, khoảng cách và hình học thanh cái **bắt buộc** phải thiết kế theo kích thước thực tế (Datasheet) của CT:

1. **Khoảng cách tâm pha ($P_{\text{phase}}$) theo Bề rộng vỏ ngoài CT:**
   - Khi lắp 3 CT thẳng hàng ngang nhau:
     $$P_{\text{tâm pha}} \ge W_{\text{vỏ ngoài CT}} + (10 \div 20\text{ mm khe hở lắp đặt})$$
   - Nếu bước cực của MCCB/ACB nhỏ hơn bề rộng vỏ CT: Bắt buộc **uốn xòe thanh cái (Fan-out / Offset Busbar)** tại đoạn lắp CT hoặc **bố trí 3 CT so le (Staggered)** theo chiều dọc thanh cái.
2. **Kích thước Cửa sổ CT (CT Window Size):**
   - Lỗ cửa sổ của CT phải lớn hơn kích thước phủ bì của thanh cái (đã bao gồm trường hợp **ghép nhiều thanh song song + khe hở đệm + ống co nhiệt**), đồng thời chừa khoảng trống cho ốc kẹp cố định CT mà không làm rách co nhiệt.
3. **Hướng cực tính & An toàn mạch thứ cấp:**
   - Ghi chú rõ trên bản vẽ bố trí 2D chiều lắp CT: Mặt **`P1` (`K`)** hướng về phía **Nguồn (Incomer)**, mặt **`P2` (`L`)** hướng về phía **Tải (Load)**.
   - Chừa không gian đấu dây thứ cấp (`S1`, `S2`) và nối đất 1 đầu `S2` (hoặc qua cầu đấu ngắn mạch CT Test Block) để tránh nguy hiểm hở mạch thứ cấp CT.

---

## 8. Thiết kế & Lựa chọn Sứ đỡ Thanh cái (Busbar Insulators & Supports)

1. **Phân loại & Ứng dụng:**
   - **Sứ đỡ đơn trụ (`Standoff Insulator` – `SM25`, `SM30`, `SM35`, `SM40`, `SM51`, `SM76`):** Dùng đỡ từng thanh pha đơn lẻ, thanh `N`, thanh `PE` hoặc làm chân cách điện đỡ tấm che/thanh chia. Chọn chiều cao `H` (`25–76 mm`) và cỡ ren (`M6–M12`) theo khoảng cách cách điện pha–đất ($\ge 20\text{ mm}$) và chiều cao đầu cực thiết bị.
   - **Sứ đỡ bậc thang (`Step Insulator`):** Dùng đỡ cụm 3 hoặc 4 thanh xếp tầng lệch nhau để dễ luồn dây và bắt đầu cosse từng pha mà không bị thanh trên che khuất.
   - **Thanh kẹp giữ đa pha (`Busbar Holder / SMC Support`):** Bắt buộc dùng cho tủ MSB / Tủ tổng hợp dòng lớn (`400A–3200A`, ghép 2–3 thanh/pha) bằng vật liệu nhựa kỹ thuật SMC/PA66 chịu nhiệt và chịu lực điện động ngắn mạch cao ($I_{cw} / I_{pk}$ kA).
2. **Khoảng cách Bố trí Sứ đỡ (Support Span):**
   - Bố trí sứ đỡ dọc theo thanh cái dựa trên tiết diện thanh và dòng ngắn mạch tính toán:
     - Thanh nhỏ (`20×3` đến `30×5` mm), vùng dòng ngắn mạch thấp: Khoảng cách giữa 2 sứ đỡ từ **`300 – 400 mm`**.
     - Thanh lớn (`50×10` đến `100×10` mm) hoặc vùng gần ACB/MCCB tổng có $I_{sc} \ge 35\text{–}50\text{ kA}$: Bố trí sứ dày hơn, khoảng **`200 – 350 mm`** (tăng cường sứ ở các điểm rẽ nhánh chữ T và góc uốn $90^\circ$).
   - **Đoạn đầu mút vươn tự do (Cantilever):** Không để đầu thanh cái vươn quá **`100 – 150 mm`** tính từ sứ đỡ cuối cùng mà không có điểm tựa.

---

## 9. Che chắn Bảo vệ Tiếp xúc Trực tiếp (Mica / Polycarbonate IP2X)

- Mọi vùng mang điện hở (khoang thanh cái tổng, đầu cực ACB/MCCB tổng, thanh cái nhánh, khối chia nguồn) bắt buộc phải có **tấm che bảo vệ bằng Mica / Polycarbonate trong suốt (dày `3 – 5 mm`)** đạt tối thiểu cấp bảo vệ ngón tay **`IP2X`** khi mở cửa tủ kiểm tra.
- Tấm che được bắt cố định lên trụ đồng/sứ đỡ chuyên dụng (dễ tháo lắp bằng tay hoặc dụng cụ khi bảo trì) và có **tem cảnh báo tia chớp điện** (`DANGER HIGH VOLTAGE / NGUY HIỂM ĐIỆN ÁP CAO`).

---

## 10. Quy chuẩn Đánh nhãn Đầu dây, Đầu Cosse & Biển tên Thiết bị

1. **Đánh nhãn Đầu dây (Wire Ferrules / Markers):**
   - 100% dây điều khiển và tín hiệu phải bấm đầu cosse kim/chĩa đúng tiết diện và lồng **ống đánh số đầu dây (Ferrule)** ở cả 2 đầu dây.
   - Mã số trên ống lồng phải **trùng khớp 100%** với số dây (`Wire Number`) được đánh tự động trên Sơ đồ nguyên lý (`AEWIRENO`).
2. **Chọn đúng loại Đầu Cosse (Cable Lugs):**
   - Dây điều khiển đấu vào MCB/PLC/Cầu đấu lò xo: Dùng đầu cosse kim rỗng (**Pin / Bootlace Ferrule `E`**, có loại đôi `TE` cho 2 dây chung chân).
   - Dây điều khiển đấu vào vít kẹp Contactor/Relay/Terminal vít: Dùng đầu cosse chĩa (**Fork `SV`**) hoặc tròn (**Ring `RV`**).
   - Cáp động lực ($\ge 10\text{ mm}^2$): Dùng đầu cosse đồng ép thủy lực (`SC` / `DT`), bọc ống co nhiệt màu pha trùm kín cổ cosse.
3. **Biển tên Thiết bị & Nhãn Tủ (Nameplates & Tags):**
   - Mặt ngoài cánh tủ (nút nhấn, đèn báo, công tắc, đồng hồ) và bên trong tấm lắp (từng MCB, MCCB, Contactor, VFD, PLC) phải dán/gắn nhãn **khớp chính xác với `TAG` trên Sơ đồ nguyên lý** (VD: `-Q1`, `-K1`, `-S1`).
   - Nhãn mặt ngoài tủ ưu tiên làm bằng **Mica 2 lớp khắc Laser** hoặc nhôm ăn mòn, chữ viết rõ ràng theo chuẩn **Song ngữ EN / VI** (hoặc ngôn ngữ dự án).



