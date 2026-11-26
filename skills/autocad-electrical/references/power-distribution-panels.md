# Quy chuẩn Thiết kế Tủ Phân Phối (MSB, DB/SDB & Tủ Tổng hợp)

Áp dụng cho **Tủ điện phân phối tổng (MSB)**, **Tủ điện phân phối nhánh (DB / SDB)** và **Tủ tổng hợp (Combined Switchboard)** theo tiêu chuẩn **IEC 61439-1 / 61439-2**.

---

## 1. Tủ Điện Phân Phối Tổng (MSB - Main Switchboard)

1. **Cấu hình mạch chính (Main Incomer & Feeders):**
   - Thiết bị đóng cắt tổng: **ACB** (Air Circuit Breaker) hoặc **MCCB** công suất lớn, kèm bảo vệ quá tải, ngắn mạch, chạm đất (LSIG), cắt thấp áp/cắt khẩn (`UVT` / `Shunt Trip`).
   - Hệ thống đo lường: **Đồng hồ đa năng (MFM)** đo `V, A, kW, kVA, cosφ, Hz, kWh` qua **3 biến dòng (CT)** và cầu chì bảo vệ áp đo lường (`2A–6A`).
   - Thiết bị chống sét lan truyền (**SPD Type 1+2**) đấu ngay sau tổng kèm cầu chì/MCB bảo vệ nhánh SPD.
   - Đèn báo pha `L1, L2, L3` (Đỏ/Vàng/Xanh hoặc chuẩn IEC) có cầu chì bảo vệ riêng.
2. **Phân ngăn cách ly (Forms of Separation - IEC 61439):**
   - Chỉ định rõ **Form 1, Form 2a/2b, Form 3a/3b hoặc Form 4a/4b** trong yêu cầu thiết kế (tùy mức độ an toàn bảo trì khi tủ đang mang điện).
   - Thiết kế khoang đấu cáp riêng (Cable Compartment) có thanh kẹp giữ cáp lực, tấm bích đáy (Gland Plate) bằng nhôm hoặc thép chia mảnh để đi cáp động lực lớn.

---

## 2. Tủ Điện Phân Phối Nhánh (DB / SDB - Distribution Board)

1. **Cấu trúc phân tầng:**
   - Ngăn tổng dùng MCCB hoặc Isolator (Cầu dao cách ly) hoặc RCCB/RCBO tổng.
   - Các lộ nhánh dùng MCB 1P/2P/3P/4P hoặc RCBO cho các lộ ổ cắm / thiết bị có nguy cơ rò điện.
2. **Cân bằng pha (Phase Balancing):**
   - Phân bổ đều tải 1 pha lên 3 pha `L1`, `L2`, `L3` trên sơ đồ nguyên lý và bảng phân tải (Load Schedule) để tránh lệch pha quá 10–15%.
3. **Thanh cái nhánh & Trung tính/Tiếp địa:**
   - Dùng thanh cái đồng nhỏ hoặc thanh cái lược (Comb Busbar) cho các hàng MCB để gọn, đẹp, giảm điểm tiếp xúc lỏng.
   - Bố trí thanh trung tính (`N`) và thanh tiếp địa (`PE`) đủ số lỗ bắt dây cho toàn bộ các lộ nhánh + **20% lỗ dự phòng**.

---

## 3. Tủ Tổng Hợp (Combined / Integrated Switchboard)

Khi gộp nhiều chức năng vào một dãy tủ (Ví dụ: **Khoang MSB + Khoang ATS + Khoang Tụ bù + Khoang Điều khiển**):

1. **Kết cấu ghép module:**
   - Chia thành các khoang đứng độc lập (Modular Bays) ghép nối bằng bu-lông khung, có **vách ngăn thép hoặc tấm cách điện (Bakelite/Polycarbonate)** giữa các khoang khác chức năng (đặc biệt tách khoang tụ bù và khoang điều khiển PLC).
2. **Thanh cái ngang liên khoang (Main Horizontal Busbar):**
   - Đặt ở khoang trên cùng (Top Busbar Chamber) hoặc phía sau (Rear Busbar Chamber), chạy xuyên suốt các khoang để cấp nguồn cho từng khoang nhánh.
   - Trên bản vẽ Panel Layout, bắt buộc có **Mặt cắt hông (Side Section)** thể hiện rõ vị trí thanh cái chính, thanh cái đứng (Dropper Busbar) và khoảng hở thao tác đấu cáp.
