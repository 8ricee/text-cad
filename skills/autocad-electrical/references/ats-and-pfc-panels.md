# Quy chuẩn Thiết kế Tủ Chuyển Nguồn Tự Động (ATS) & Tủ Tụ Bù (PFC)

Áp dụng cho **Tủ chuyển nguồn tự động (ATS)** và **Tủ tụ bù công suất phản kháng (PFC / Capacitor Bank)**.

---

## 1. Tủ Chuyển Nguồn Tự Động (ATS - Automatic Transfer Switch)

### A. Lựa chọn Cơ cấu Chuyển mạch
1. **Dùng Bộ chuyển nguồn tích hợp (PC-Class / CB-Class ATS Switch):** Tích hợp sẵn khóa liên động cơ khí bên trong (khuyên dùng cho công trình tiêu chuẩn, độ tin cậy cao).
2. **Dùng cặp MCCB có Motor (Motorized MCCB) hoặc cặp Contactor 3P/4P:** Bắt buộc phải lắp **bộ khóa liên động cơ khí (Mechanical Interlock)** giữa nguồn Lưới (Mains) và nguồn Máy phát (Generator).

### B. Nguyên tắc Khóa chéo & Điều khiển (Interlocking & Logic)
1. **Liên động kép (Double Interlock):**
   - **Liên động cơ khí (Mechanical):** Ngăn không cho 2 thiết bị đóng đồng thời về mặt vật lý.
   - **Liên động điện (Electrical):** Đấu nối tiếp tiếp điểm thường đóng (`NC`) của Contactor/MCCB bên này vào mạch cuộn đóng của bên kia.
2. **Bộ điều khiển ATS & Mạch trễ:**
   - Trang bị bộ điều khiển ATS chuyên dụng (hoặc PLC/Rơ-le bảo vệ mất pha, thấp áp, quá áp, sai thứ tự pha).
   - Thiết lập thời gian trễ xác nhận mất lưới (`T1`), thời gian trễ ổn định máy phát trước khi đóng tải (`T2`), thời gian trễ chuyển lại lưới (`T3`) và thời gian chạy làm mát máy phát không tải (`Cool-down time`).
   - Có ngõ ra tiếp điểm khô **`Remote Start`** gửi xuống tủ điều khiển máy phát điện.
3. **Chế độ vận hành:** Có công tắc chọn `AUTO / MANUAL` và tay quay thao tác cơ khí khẩn cấp bên ngoài.

---

## 2. Tủ Tụ Bù Công Suất Phản Kháng (PFC - Capacitor Bank)

### A. Cấu hình & Thiết bị Chuyên dụng
1. **Bộ điều khiển tụ bù (`APFC`):**
   - Lấy tín hiệu dòng từ **1 biến dòng (CT)** đặt tại thanh cái **tổng đầu vào** (phía trước cả điểm đấu nhánh tụ bù và phụ tải) và tín hiệu áp từ 2 pha còn lại (đúng thứ tự pha theo tài liệu hãng).
2. **Thiết bị đóng cắt tụ:**
   - **Bắt buộc** dùng **Contactor chuyên dụng đóng cắt tụ (Capacitor Duty Contactor)** có điện trở hạn dòng nạp đỉnh, hoặc dùng **Thyristor (Đóng cắt nhanh không tiếp điểm)** cho tải biến thiên nhanh (máy hàn, cẩu trục, thang máy).
   - **Cấm** dùng Contactor động lực thông thường vì dòng xung nạp tụ lớn sẽ làm dính tiếp điểm.
3. **Bảo vệ, Tính chọn & Lọc sóng hài (IEC 60831-1):**
   - Dòng định mức nhánh tụ: $I_c = \frac{Q_c\ (\text{VA})}{\sqrt{3} \cdot U}$.
   - **MCCB / Cầu chì nhánh tụ:** $I_{n\_\text{MCCB}} \ge (1.35 \div 1.5) \times I_c$.
   - **Contactor chuyên dụng & Cáp nhánh tụ:** $I_z \ge (1.43 \div 1.5) \times I_c$.
   - Với hệ thống có nhiều biến tần, nguồn xung ($THD_u > 3\%$ hoặc $THD_i > 15\%$): Bắt buộc mắc nối tiếp **Cuộn kháng lọc sóng hài (Detuned Reactor $p = 7\%$ hoặc $14\%$)**. Vì điện áp đầu cực tụ tăng lên $\frac{U}{1 - p}$, trên lưới $400\text{VAC}$ **bắt buộc chọn tụ `440VAC` (với $p=7\%$) hoặc `480–525VAC` (với $p=14\%$)**; tuyệt đối không dùng tụ `400VAC` ghép cuộn kháng.

### B. Quy chuẩn Tản nhiệt & An toàn Xả tụ
1. **Tản nhiệt bắt buộc:** Tụ bù và cuộn kháng tỏa nhiệt rất lớn và cực kỳ nhạy cảm với nhiệt độ cao (làm giảm tuổi thọ nhanh chóng).
   - Khoảng hở giữa các bình tụ tối thiểu `20–30 mm`, phía trên cuộn kháng cách ít nhất `100 mm`.
   - **Bắt buộc lắp quạt hút cưỡng bức** điều khiển qua bộ **Thermostat** cài đặt ở $35^\circ\text{C} - 40^\circ\text{C}$ (kèm cửa gió lọc bụi).
2. **An toàn xả tụ:** Đảm bảo điện trở xả (Discharge Resistor) gắn trên bình tụ hoạt động tốt, dán tem cảnh báo **"CHỜ XẢ ĐIỆN TỤ 3–5 PHÚT TRƯỚC KHI MỞ TỦ / WAIT 5 MINS FOR CAPACITOR DISCHARGE"**.
