# Quy chuẩn Thiết kế Tủ Điện Phòng Cháy Chữa Cháy (PCCC)

Áp dụng cho **Tủ điều khiển hệ thống bơm chữa cháy, bơm tăng áp cầu thang, quạt hút khói** theo quy chuẩn **QCVN 06 / TCVN 7336 / NFPA 20**.

---

## 1. Yêu cầu Vỏ tủ & Nguồn cấp Ưu tiên

1. **Nhận diện Vỏ tủ:**
   - Vỏ tủ bắt buộc sơn tĩnh điện **màu đỏ tiêu chuẩn (`RAL 3000`)**, mặt trước có dòng chữ cảnh báo song ngữ rõ ràng: **`FIRE PUMP CONTROL PANEL / TỦ ĐIỀU KHIỂN BƠM CHỮA CHÁY`**.
   - Độ kín tối thiểu `IP54` (hoặc `IP55`/`IP65` tùy vị trí lắp đặt phòng bơm ẩm ướt).
   - Trang bị đèn báo nguồn, đồng hồ Ampe/Volt và khóa tủ bảo vệ chống thao tác nhầm.
2. **Nguồn cấp Ưu tiên & Cáp chống cháy (Dedicated Fire Power Supply):**
   - Nguồn cấp cho tủ PCCC phải lấy **trước cầu dao tổng** của công trình (để khi cắt điện toàn tòa nhà lúc có cháy, hệ thống PCCC vẫn có điện hoạt động).
   - Đối với hệ thống yêu cầu độ tin cậy cao: Tích hợp **ATS chuyển nguồn tự động** giữa điện lưới và máy phát ngay trong tủ hoặc cấp từ nguồn ưu tiên riêng.
   - **Cáp chống cháy (`Fire Resistant Cable - FR / LSZH`):** Nguồn cấp vào tủ PCCC và cáp động lực/điều khiển đi từ tủ ra động cơ bơm chữa cháy bắt buộc dùng cáp chống cháy chịu nhiệt **`750^\circ\text{C} – 950^\circ\text{C}` trong `90 – 180 phút`** (theo QCVN 06 / TCVN).

---

## 2. Cấu hình Điều khiển Cụm 3 Bơm Tiêu chuẩn

Một hệ thống bơm PCCC tiêu chuẩn gồm 3 cụm điều khiển độc lập nhưng liên động chặt chẽ theo áp lực đường ống:

1. **Bơm Bù áp (Jockey Pump):**
   - Công suất nhỏ, khởi động trực tiếp (DOL).
   - Tự động chạy khi áp lực đường ống rò rỉ giảm xuống ngưỡng $P_1$, tự động ngắt khi đạt áp $P_{\text{max}}$.
2. **Bơm Điện Chính (Main Electric Fire Pump):**
   - Công suất lớn: Khởi động **Sao–Tam giác (Star-Delta)** hoặc **Khởi động mềm (Soft Starter)** (hạn chế dùng Biến tần cho bơm chữa cháy trừ khi có thiết kế bypass chuyên dụng).
   - Tự động chạy khi áp lực tụt sâu xuống ngưỡng $P_2$ ($P_2 < P_1$) hoặc nhận tín hiệu kích hoạt từ **Trung tâm Báo cháy (FACP)**.
   - **Quy chuẩn bảo vệ ("Run-to-destruction" theo NFPA 20 / TCVN):**
     - CB đầu vào của Bơm chữa cháy chính chỉ dùng cơ cấu **cắt từ bảo vệ ngắn mạch (`Magnetic-only` / `Instantaneous trip`)** hoặc MCCB chỉnh ngưỡng bảo vệ quá tải rất cao.
     - Tiếp điểm thường mở **`97–98`** của Rơ-le nhiệt chỉ đấu vào mạch còi/đèn cảnh báo lỗi (`FAULT ALARM`), **TUYỆT ĐỐI KHÔNG** đấu tiếp điểm thường đóng **`95–96`** cắt mạch cuộn hút Contactor khi đang ở chế độ chữa cháy tự động (đảm bảo bơm chạy tối đa khi có hỏa hoạn).
3. **Bơm Chữa cháy Diesel (Diesel Fire Pump):**
   - Khởi động tự động khi mất điện lưới hoặc áp lực đường ống tụt xuống ngưỡng $P_3$ ($P_3 < P_2$) mà bơm điện không lên áp.
   - Tích hợp **2 bộ sạc ắc quy tự động (Dual Battery Chargers)**, mạch đề máy tự động theo chu kỳ (Crank cycle, tối đa 3–6 lần đề), cảm biến nhiệt độ nước/áp lực dầu nhớt và van điện từ tắt máy.

---

## 3. Liên động & Tín hiệu Giám sát Bắt buộc

- **Công tắc áp lực (Pressure Switches):** Đấu nối độc lập cho từng bơm (hoặc cảm biến áp suất kết hợp công tắc áp lực dự phòng).
- **Chế độ vận hành:**
  - `AUTO - OFF - MANUAL` (hoặc `TEST`). Khi ở chế độ `OFF` hoặc `MANUAL`, phải có đèn/còi cảnh báo trạng thái bất thường gửi về phòng trực PCCC.
- **Tín hiệu gửi về Trung tâm Báo cháy (FACP - Dry Contacts):**
  - Trạng thái Đang chạy (Pump Running) cho từng bơm.
  - Trạng thái Lỗi / Mất nguồn / Mất pha (Power Fail / Phase Reversal / Fault).
  - Trạng thái Công tắc không ở vị trí `AUTO` (Selector Not in Auto).
