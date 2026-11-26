# Quy chuẩn Thiết kế Tủ Điều Khiển (MCC / PLC) & Tủ Chiếu Sáng (LP)

Áp dụng cho **Tủ điện điều khiển trung tâm & động cơ (MCC / PLC Control Panel)** và **Tủ điện chiếu sáng (Lighting Panel - LP)**.

---

## 1. Tủ Điều Khiển Trung Tâm & Động Cơ (MCC / PLC Panel)

### A. Phân vùng & Chống nhiễu EMC (Electromagnetic Compatibility)
1. **Tách biệt đường đi dây & Thiết bị:**
   - **Vùng "Bẩn" (Nhiễu cao):** Biến tần (VFD), Servo Drive, Khởi động mềm, Contactor động lực, Điện trở xả.
   - **Vùng "Sạch" (Nhạy nhiễu):** PLC, Module I/O, Switch Ethernet/Profinet, Bộ nguồn 24VDC, Thiết bị đo Analog (`4-20mA`, `0-10V`).
   - Đặt máng cáp động lực (380VAC/Motor) tách biệt với máng cáp tín hiệu (24VDC/Analog/Truyền thông). Nếu bắt buộc giao cắt, phải cắt **vuông góc $90^\circ$**.
2. **Tiếp địa & Quy tắc Nối đất Vỏ giáp Chống nhiễu (`Shield Grounding` – Chống Ground Loop):**
   - Vỏ biến tần, bộ lọc EMI và tấm lắp thiết bị (mạ kẽm không sơn) phải tiếp địa tốt về thanh `PE`.
   - **Phân biệt bắt buộc 2 chế độ nối đất giáp cáp (`Shielded Cable`):**
     1. **Cáp động lực Biến tần / Servo (`VFD Motor Cable` – Nhiễu tần số cao):** Bắt buộc nối đất vỏ giáp **ở cả 2 đầu $360^\circ$** (kẹp cổ dê EMC tại đáy biến tần trong tủ **VÀ** tại hộp cực động cơ/ốc siết cáp EMC) để dẫn dòng nhiễu tần số cao (`Common-mode HF current`) quay về biến tần.
     2. **Cáp tín hiệu Analog (`4–20mA`, `0–10V`), Load cell, RTD/TC, RS-485:** Bắt buộc **chỉ nối đất vỏ giáp ở 1 đầu duy nhất tại phía tủ điều khiển** (qua thanh kẹp Shield/PE), **đầu phía cảm biến ngoài hiện trường phải cắt gọn và bọc ống co nhiệt cách điện hoàn toàn** để ngăn dòng điện chênh lệch điện thế đất chạy qua vỏ giáp (**Ground Loop**) làm trôi số đo.
     3. **Cáp Encoder tốc độ cao / PROFINET:** Kẹp giáp $360^\circ$ tại đầu vào module đếm xung / vỏ giắc RJ45 kim loại kết hợp dây tiếp địa đẳng thế (`Equipotential Bonding ≥ 10 mm²`) giữa khung máy và tủ điện.

### B. Phương pháp Khởi động & Bảo vệ Động cơ
- **Khởi động trực tiếp (DOL):** Mặc định dùng cho động cơ công suất nhỏ ($\le 5.5\text{–}7.5\text{ kW}$; chỉ cho phép tới `11–15 kW` khi trạm biến áp nguồn đủ lớn không bị sụt áp lưới), gồm: MCB/MCCB bảo vệ ngắn mạch + Contactor + Rơ-le nhiệt (hoặc MPCB - Motor Protection Circuit Breaker).
- **Khởi động Sao – Tam giác (Star-Delta):** Động cơ trung bình/lớn cần giảm dòng khởi động, dùng 3 Contactor (`K_Main`, `K_Delta`, `K_Star`) + Timer chuyển mạch (`50-100 ms` trễ chuyển tiếp để tránh ngắn mạch pha) + **Khóa chéo điện/cơ khí** giữa `K_Delta` và `K_Star`.
- **Biến tần (VFD) / Khởi động mềm (Soft Starter):**
  - Chừa khoảng hở tản nhiệt phía trên/dưới biến tần tối thiểu `50–100 mm` (theo Datasheet).
  - Không đặt PLC hoặc bộ nguồn ngay phía trên luồng khí nóng thoát ra từ biến tần.

### C. Bố trí Cánh tủ (Door Layout)
- Mặt ngoài cánh tủ bố trí: Màn hình HMI (cao độ tầm mắt `1400–1600 mm` với tủ đứng), đèn báo trạng thái (`RUN` - Xanh lá, `STOP` - Đỏ/Trắng, `FAULT/TRIP` - Vàng), nút nhấn `START/STOP`, công tắc chuyển mạch `MAN - OFF - AUTO`, nút dừng khẩn cấp `E-STOP` (nấm đỏ nền vàng, đặt ở độ cao `1000–1300 mm` dễ thao tác).

### D. Mạch An toàn Máy (Safety Circuit - ISO 13849-1 / IEC 62061)
1. **Máy đơn giản (`PLa / PLb`):** Nút dừng khẩn cấp `E-STOP` tiếp điểm `NC` cắt trực tiếp nguồn điều khiển cuộn hút Contactor động lực chính.
2. **Máy công nghiệp / Dây chuyền tự động (`PLc / PLd / PLe` – Category 3/4):**
   - **Bắt buộc** dùng **Safety Relay** (`PNOZ` / `Sirius 3SK` / `XPS`) hoặc **Safety PLC** giám sát 2 kênh (`Dual-channel E-Stop S11-S12 / S21-S22`, công tắc cửa an toàn).
   - Phải có **mạch hồi tiếp (`Feedback Loop Y1–Y2`)** mắc nối tiếp qua tiếp điểm `NC` của cặp Contactor tổng mắc nối tiếp (`-KM1`, `-KM2`) để phát hiện lỗi dính tiếp điểm (Welded Contact) và ngăn khởi động lại ngoài ý muốn.

### E. Nối đất Hệ thống & Phân vùng Nguồn 24VDC (IEC 60204-1)
1. **Chế độ nối đất & Nguồn PELV 24VDC:**
   - Tuân thủ nối đất hệ thống (`TN-S`, `TN-C-S`, `TT`) theo thiết kế nhà xưởng.
   - Cực **`0VDC`** của bộ nguồn xung 24VDC **bắt buộc nối xuống thanh `PE`** (**Grounded PELV** theo IEC 60204-1) để triệt tiêu điện áp trôi nổi làm hỏng ngõ vào PLC và đảm bảo MCB phía 24VDC tác động cắt ngay khi xảy ra chạm vỏ.
2. **Tách nhánh bảo vệ 24VDC & Dập xung:**
   - Tách **MCB 24VDC riêng biệt** cho từng nhóm tải: (1) Nguồn nuôi CPU PLC & HMI, (2) Nguồn nuôi Cảm biến / Ngõ vào `DI`, (3) Nguồn nuôi Cuộn hút Relay / Van điện từ `DO`.
   - Mọi tải cảm (cuộn hút Relay trung gian, van điện từ DC) bắt buộc có **Diode dập xung ngược (`Flyback Diode`)** song song cuộn dây (hoặc **RC Snubber** cho cuộn hút AC) để bảo vệ tiếp điểm Relay/Transistor PLC.

### F. Quy chuẩn Thiết kế Mạch Tín hiệu Tinh xảo (Analog `4–20mA`, Load Cell, Encoder & Shield)
1. **Thể hiện Cáp Chống nhiễu trên Sơ đồ Nguyên lý (`AESHIELD`):**
   - Dùng công cụ *Schematic tab → Insert Wires/Wire Numbers → Cable Markers → **Shield*** (`AESHIELD`) vẽ vòng ôm quanh các lõi dây của cáp chống nhiễu, gắn mã cáp (`-W_AI1`, `-W_ENC1`...).
   - Trên bản vẽ, vẽ rõ 1 đầu dây dẫn từ ký hiệu Shield về cầu đấu tiếp địa (`-X_PE` / `SHIELD BAR`) tại tủ (`+MAIN_PNL`), đầu ngoài hiện trường (`+FIELD`) để hở kèm ghi chú `SHIELD ISOLATED AT FIELD END / BỌC CÁCH ĐIỆN GIÁP ĐẦU HIỆN TRƯỜNG`.
2. **Mạch Tín hiệu Analog (`4–20mA` / `0–10V`) & Bộ Cách ly (`Signal Isolator`):**
   - **Cảm biến 2 dây (`2-Wire Loop-Powered Transmitter`):** Nguồn `+24VDC` $\rightarrow$ Chân `+` cảm biến $\rightarrow$ Chân `-` cảm biến $\rightarrow$ Chân `AI+` của PLC; chân `AI-` của PLC nối về `0VDC (MANA)`.
   - **Cảm biến 4 dây (`4-Wire Active Transmitter`):** Cấp `+24VDC` và `0VDC` nuôi riêng cảm biến; cặp ngõ ra dòng `Iout+ / Iout-` đấu thẳng vào `AI+ / AI-` của module AI (chú ý cấu hình phần cứng module AI ở chế độ `2DMU` hay `4DMU` khớp sơ đồ).
   - **Bộ cách ly tín hiệu (`Galvanic Signal Isolator 4–20mA`):** Bắt buộc lắp khi nhận tín hiệu `4–20mA` từ tủ điện khác hoặc từ thiết bị hiện trường đi cáp dài $> 50\text{ m}$ gần cáp động lực.
3. **Mạch Cảm biến Lực (`Load Cell 4-Wire vs 6-Wire`):**
   - **Load Cell 6 dây (Chuẩn công nghiệp chính xác cao):** Vẽ đủ 3 cặp dây xoắn đôi bọc giáp: `EXC+ / EXC-` (Nguồn kích thích `5–10VDC`), `SIG+ / SIG-` (Tín hiệu vi sai `mV/V`), và **`SENSE+ (S+) / SENSE- (S-)`** (Hồi tiếp bù sụt áp trên cáp theo nhiệt độ).
   - **Load Cell 4 dây:** Nếu dùng Load cell 4 dây hoặc qua hộp nối (`Junction Box / Summing Box`), phải kéo cáp 6 dây từ hộp nối về module cân (`SIWAREX` / `Weighing Indicator`), hoặc nối cầu `EXC+ ↔ S+` và `EXC- ↔ S-` ngay tại cầu đấu của module cân. **Tuyệt đối ghi chú trên bản vẽ: `DO NOT CUT LOAD CELL CABLE / CẤM CẮT NGẮN CÁP LOAD CELL`.**
4. **Mạch Đếm xung Tốc độ cao (`Incremental / Absolute Encoder`):**
   - Phân biệt rõ điện áp nuôi và chuẩn giao tiếp: **`HTL (10–30VDC Push-Pull)`** cho khoảng cách vừa và **`TTL / RS-422 (5VDC Differential)`** cho tần số cao / cáp dài.
   - Với Encoder vi sai (`Differential`): Vẽ đúng 3 cặp xoắn đôi `A / A- (A_bar)`, `B / B- (B_bar)`, `Z / Z- (Z_bar)` cộng cặp nguồn `+V / 0V` vào đúng chân của module đếm xung tốc độ cao (`TM Count` / `HSC`).

### G. Quy chuẩn Kiến trúc Mạng Truyền thông Công nghiệp (`PROFINET`, `Modbus RTU / TCP`)
1. **Mạng `PROFINET` / `Industrial Ethernet` (`Modbus TCP`):**
   - **Sơ đồ Topology:** Trên trang `06_plc_io_wiring.dwg` (hoặc trang Network riêng), vẽ rõ cấu trúc mạng (Hình sao `Star` qua Switch công nghiệp `SCALANCE`, đường thẳng `Line` qua 2 cổng tích hợp `X1 P1 / X1 P2`, hoặc mạch vòng dự phòng `MRP Ring`).
   - **Chuẩn Cáp & Đầu nối:** Chỉ định rõ cáp xanh công nghiệp **`PROFINET Type A/B/C Cat5e/Cat6a Shielded (2×2×AWG22)`** và đầu cắm kim loại `RJ45 FastConnect` ($180^\circ$ hoặc $90^\circ$).
   - **Thông tin bắt buộc trên mỗi Node thiết bị (PLC, HMI, VFD, Remote I/O ET200SP):**
     `TAG (-A1, -U1...) | PROFINET DEVICE NAME (chữ thường ASCII) | IP ADDRESS & SUBNET MASK | PORT CONNECTION (From X1.P1 → To -A2:X1.P2)`.
2. **Mạng `Modbus RTU` / `PROFIBUS DP` (`RS-485 2-Wire`):**
   - **Cấu trúc chuỗi (`Daisy-Chain Topology`):** Bắt buộc đi dây nối tiếp từ thiết bị này sang thiết bị kế tiếp bằng cáp xoắn đôi bọc chống nhiễu có **trở kháng đặc tính `120 Ω`** (`1 Pair AWG22/24`: dây `D+ (A)`, dây `D- (B)`, kèm dây tham chiếu **`SG / Signal Ground`**). **Cấm tuyệt đối** đấu rẽ nhánh hình sao (`Star`) hoặc dây nhánh (`Stub`) dài.
   - **Điện trở đầu cuối (`Termination Resistor 120 Ω, 1/2 W`):**
     - Bắt buộc vẽ và ghi chú bật **`ON` (hoặc mắc điện trở `120 Ω` giữa `D+` và `D-`) tại đúng 2 thiết bị ở 2 đầu mút vật lý xa nhất của tuyến bus** (thường là PLC Master ở đầu tuyến và thiết bị Slave cuối cùng).
     - Toàn bộ các thiết bị nằm giữa tuyến bus bắt buộc để công tắc Termination ở vị trí **`OFF`**.
   - **Nối đất giáp cáp RS-485:** Giáp chống nhiễu nối liền mạch qua các trạm và nối đất tại 1 điểm duy nhất ở tủ PLC chính (hoặc qua tụ lọc cao tần theo khuyến cáo hãng).

---

## 2. Tủ Điện Chiếu Sáng (LP - Lighting Panel)

1. **Cấu trúc mạch:**
   - Aptomat tổng + Thiết bị bảo vệ dòng rò (RCCB/RCBO) đảm bảo an toàn điện chiếu sáng.
   - Chia nhiều lộ MCB nhánh cân bằng trên 3 pha `L1, L2, L3`.
2. **Chế độ điều khiển linh hoạt:**
   - Sử dụng **Contactor** đóng cắt các nhóm lộ đèn kết hợp **Timer (Đồng hồ hẹn giờ)**, **Cảm biến ánh sáng (Photocell)** hoặc ngõ ra điều khiển từ hệ thống **BMS / PLC**.
   - Bắt buộc có công tắc xoay **`AUTO - OFF - MAN`** (hoặc `TIMER - OFF - BYPASS`) trên mặt tủ để vận hành bằng tay khi bảo trì hoặc sự cố bộ hẹn giờ.
3. **Đánh nhãn lộ đèn:**
   - Gắn sơ đồ chỉ dẫn lộ đèn (Panel Schedule) ở mặt trong cánh tủ ghi rõ: `Lộ số | Tên khu vực | Công suất | Pha | Tiết diện dây`.
