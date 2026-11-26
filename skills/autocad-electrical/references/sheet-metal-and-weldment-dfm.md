# Quy chuẩn Gia công Kim loại tấm (Sheet Metal) & Kết cấu Hàn (Weldment DFM)

Tài liệu tham chiếu bắt buộc cho **Vỏ tủ điện kim loại tấm**, **Tấm lắp thiết bị**, **Thanh cái đồng uốn** và **Khung kết cấu hàn cơ khí** (áp dụng cho cả AutoCAD và Autodesk Inventor).

---

## 1. Thông số Chấn Uốn Kim Loại Tấm (`K-Factor` & `R_in` theo Dao Xưởng)

| Vật liệu | Độ dày $T$ (mm) | Bán kính trong $R_{\text{in}}$ tối thiểu | `K-Factor` chuẩn | Lưu ý dao chấn (V-Die) |
| :--- | :---: | :---: | :---: | :--- |
| **Thép tấm CT3 / SPCC (Sơn tĩnh điện)** | `1.0 – 3.0` | $1.0 \times T$ | `0.40 – 0.44` | Chọn khe V-die $\approx 8 \times T$ |
| **Inox SUS304 / SUS316** | `1.2 – 3.0` | $1.5 \times T$ | `0.44` | Chọn khe V-die $\approx 10 \times T$ để tránh nứt mép ngoài |
| **Nhôm hợp kim (AL5052 / AL6061)** | `1.5 – 3.0` | $1.0 – 1.5 \times T$ | `0.42` | Chấn vuông góc thớ cán; không chấn gập $180^\circ$ trên AL6061-T6 |
| **Đồng thanh cái E-Cu 99.9%** | `3.0 – 10.0` | $1.0 \times T$ | `0.42` | Mài sạch cạnh cắt trước khi uốn để chống rạn |

---

## 2. Rãnh Thoát Góc (`Corner Relief`), Gờ Chấn & Khe Hở Cánh Tủ

1. **Rãnh thoát góc (`Corner Relief`):**
   - Tại mọi góc giao của 2 hoặc 3 mép chấn (góc vỏ tủ, nắp nóc, tấm lắp chấn gờ chữ C), bắt buộc cắt rãnh thoát góc có:
     - **Bề rộng rãnh:** $W_{\text{relief}} \ge T$ (tối thiểu **`1.5 mm`**).
     - **Chiều sâu rãnh:** Vượt qua hết vùng biến dạng uốn ($D_{\text{relief}} \ge R_{\text{in}} + T + 0.5\text{ mm}$).
   - Không có `Corner Relief` chuẩn sẽ gây rách tôn khi chấn thực tế hoặc lỗi `FlatPattern` trên Inventor.
2. **Chiều cao gờ chấn tối thiểu (`Minimum Flange Length`):**
   - $L_{\text{flange\_min}} \ge 4T + R_{\text{in}}$ (tối thiểu `12–15 mm` với tôn `2.0 mm`) để gờ tựa vững lên mép cối V-die.
3. **Khoảng cách từ lỗ đến đường tiếp tuyến uốn (`Minimum Hole-to-Bend Distance`):**
   - Tâm lỗ đột bất kỳ phải cách mép đường uốn tối thiểu:
     $$d_{\text{min}} \ge 1.5T + R_{\text{in}} + \frac{D_{\text{hole}}}{2}$$
   - Vi phạm khoảng cách này lỗ sẽ bị kéo méo thành hình oval khi chấn.
4. **Khe hở lắp ghép cánh cửa âm (`Door Gap`) & Bù dày lớp sơn:**
   - Khe hở tiêu chuẩn giữa mép cánh tủ âm và khung vỏ tủ: **`2.0 – 2.5 mm`** mỗi phía (đã tính bù chiều dày lớp sơn tĩnh điện `0.10 – 0.15 mm/mặt`).
   - Vỏ tủ ngoài trời (`IP55 / IP65`): Bắt buộc thiết kế **gờ máng nước chống hắt mưa vát $45^\circ$ hoặc chữ U** chạy quanh miệng mở thân tủ để ép khít vào gioăng cao su cánh cửa.
   - Đinh tán cấy tiếp địa (`Earth Weld Studs`): Bắt buộc bố trí đinh tán **`M6 × 20 mm`** hàn chập trên cả thân tủ và mặt trong cánh tủ để đấu dây đồng bện tiếp địa `≥ 6 mm²`.

---

## 3. Kết Cấu Hàn (Weldments), Lỗ Bu-lông & Ký Hiệu Kỹ Thuật

1. **Dãy lỗ thông suốt chuẩn `ISO 273 (Medium)` vs Lỗ ren Taro:**
   | Cỡ Bu-lông | Lỗ thông suốt (`ISO 273 Medium`) | Lỗ khoan trước taro | Ký hiệu ren chuẩn trên bản vẽ |
   | :---: | :---: | :---: | :--- |
   | `M4` | `Ø4.5 mm` | `Ø3.3 mm` | `M4 × 0.7 - 6H` |
   | `M5` | `Ø5.5 mm` | `Ø4.2 mm` | `M5 × 0.8 - 6H` |
   | `M6` | `Ø6.6 mm` | `Ø5.0 mm` | `M6 × 1.0 - 6H` |
   | `M8` | `Ø9.0 mm` | `Ø6.8 mm` | `M8 × 1.25 - 6H` |
   | `M10` | `Ø11.0 mm` | `Ø8.5 mm` | `M10 × 1.5 - 6H` |
   | `M12` | `Ø13.5 mm` | `Ø10.2 mm` | `M12 × 1.75 - 6H` |
   | `M16` | `Ø17.5 mm` | `Ø14.0 mm` | `M16 × 2.0 - 6H` |
2. **Khung thép hộp & Cắt vát:**
   - Góc khung chịu lực dùng **cắt vát $45^\circ$ (Miter)**; thanh giằng ngang giữa dùng **cắt phẳng / cắt ngàm chữ T (Butt / Cope)** và xuất đầy đủ bảng **`Cut List`** ghi chiều dài cắt thật + góc cắt hai đầu.
   - Kết cấu ống/hộp kín đi **mạ kẽm nhúng nóng**: Bắt buộc có **lỗ thoát khí/thoát kẽm (`Ø8–Ø12 mm`)** ở góc khuất hai đầu mỗi khoang kín (tránh nổ áp suất trong bể kẽm nóng $450^\circ\text{C}$).
3. **Ký hiệu Mối hàn (`ISO 2553`), Nhám bề mặt (`ISO 1302`) & Dung sai hình học (`ISO 1101`):**
   - Mọi mối hàn kết cấu phải ghi rõ loại mối hàn (Fillet `△`, Butt `V`/`X`), chiều cao cạnh hàn $a$ hoặc $z$ (`a4`, `z5`), hàn liên tục hay hàn đứt quãng (`n × l (e)`), và hàn xung quanh (`○`) hay hàn công trường (`⚑`).
   - Mặt bích lắp động cơ, gối bi, thanh dẫn hướng bắt buộc chỉ định nhám bề mặt (`Ra 3.2` / `Ra 1.6` theo `ISO 1302`) và dung sai độ phẳng/vuông góc/đồng tâm theo `ISO 1101`.
