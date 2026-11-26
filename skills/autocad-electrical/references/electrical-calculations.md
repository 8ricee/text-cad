# Bảng tra & Công thức Tính toán Thiết bị, Dây dẫn, Busbar (IEC 60364 / 60947)

Tài liệu chuẩn hóa các công thức và bảng tra nhanh để AI lên phương án chọn thiết bị đóng cắt (ACB, MCCB, MCB), cáp điện, thanh cái đồng (Busbar), bộ khởi động động cơ và dung lượng tụ bù.

---

## 1. Tính Dòng Làm Việc ($I_b$) & Hệ Số Đồng Thời ($K_{dt}$)

- **Mạch 1 pha ($220\text{–}230\text{VAC}$):**
  $$I_b = \frac{P}{U \cdot \cos\varphi \cdot \eta}$$
- **Mạch 3 pha ($380\text{–}400\text{VAC}$):**
  $$I_b = \frac{P}{\sqrt{3} \cdot U \cdot \cos\varphi \cdot \eta}$$
  *(Với tải thuần trở $\cos\varphi = 1, \eta = 1$; chiếu sáng/tổng hợp thường lấy $\cos\varphi \approx 0.85\text{–}0.9$; động cơ $\cos\varphi \approx 0.8\text{–}0.88, \eta \approx 0.85\text{–}0.94$).*
- **Dòng tính toán tổng cho tủ (có xét Hệ số đồng thời $K_{dt}$):**
  $$I_{\text{tổng}} = K_{dt} \cdot \sum I_{b\_i}$$
  *(Tham khảo $K_{dt}$: Tủ có 2–3 lộ nhánh $\approx 0.9$; 4–5 lộ $\approx 0.8$; 6–9 lộ $\approx 0.7$; $\ge 10$ lộ $\approx 0.6\text{–}0.7$ tùy tính chất dây chuyền).*

---

## 2. Nguyên tắc Chọn ACB / MCCB / MCB & Phối hợp Bảo vệ

1. **Điều kiện dòng định mức:**
   $$I_b \le I_n \le I_z$$
   - $I_b$: Dòng làm việc của tải.
   - $I_n$ (hoặc dòng chỉnh định $I_r$): Dòng định mức của CB. Thường chọn $I_n \approx (1.15 \div 1.25) \cdot I_b$ với tải thông thường.
   - $I_z$: Dòng mang tải cho phép lâu dài của dây dẫn/cáp điện (sau hiệu chỉnh).
2. **Phân cấp Thiết bị đóng cắt theo dòng:**
   - **MCB:** $6\text{A} \div 63\text{A}$ (hoặc tới $125\text{A}$), dòng cắt $6\text{ kA} \div 10\text{ kA}$ (dùng cho nhánh chiếu sáng, ổ cắm, điều khiển, động cơ nhỏ).
   - **MCCB:** $16\text{A} \div 1600\text{A}$, dòng cắt $18\text{ kA} \div 70\text{ kA}$ (dùng cho tủ nhánh DB, tổng phân phối vừa, động cơ lớn).
   - **ACB:** $630\text{A} \div 6300\text{A}$, dòng cắt $50\text{ kA} \div 100\text{ kA}$ (dùng cho tổng MSB, trạm biến áp lớn).
3. **Chọn dòng cắt ngắn mạch ($I_{cu}$ / $I_{cs}$) theo vị trí tủ:**
   - Tủ tổng **MSB** sát trạm biến áp ($\ge 630\text{ kVA}$): Tối thiểu `36 kA – 50 kA – 65 kA`.
   - Tủ phân phối nhánh **DB / MCC** cách xa MSB: `15 kA – 25 kA – 36 kA`.
   - Tủ nhánh cuối / chiếu sáng **LP**: `6 kA – 10 kA`.
   - **Tính chọn lọc (Selectivity):** Đảm bảo cấp trên (ACB/MCCB tổng) có thời gian trễ cắt hoặc dòng cắt lớn hơn cấp dưới để khi sự cố nhánh chỉ nhảy CB nhánh, không mất điện toàn xưởng.

---

## 3. Bảng tra Nhanh Tiết diện Cáp đồng ($S_{\text{cable}}$) & Sụt áp

### A. Dòng cho phép tham khảo ($I_{z0}$, đi trong máng/khay cáp, $T_{\text{amb}} = 30^\circ\text{C}$, cáp đa lõi đồng)
*(Khi nhiệt độ môi trường là $35\text{–}40^\circ\text{C}$ tại VN hoặc đi nhiều cáp bó sát nhau, nhân thêm hệ số hiệu chỉnh $K = K_t \cdot K_g \approx 0.75 \div 0.88$ để ra $I_z$ thực tế).*

| Tiết diện ($\text{mm}^2$) | Cáp PVC 450/750V ($I_{z0}$, A) | Cáp XLPE 0.6/1kV ($I_{z0}$, A) | Gợi ý MCB / MCCB bảo vệ tối đa |
| :---: | :---: | :---: | :---: |
| `1.5` | ~ 15 A | ~ 20 A | MCB 10A – 16A (Điều khiển / Đèn) |
| `2.5` | ~ 21 A | ~ 27 A | MCB 16A – 20A (Ổ cắm / Đèn) |
| `4.0` | ~ 28 A | ~ 36 A | MCB 25A – 32A |
| `6.0` | ~ 36 A | ~ 46 A | MCB 32A – 40A |
| `10` | ~ 50 A | ~ 63 A | MCB/MCCB 40A – 50A |
| `16` | ~ 68 A | ~ 85 A | MCCB 63A |
| `25` | ~ 89 A | ~ 112 A | MCCB 80A – 100A |
| `35` | ~ 110 A | ~ 138 A | MCCB 100A – 125A |
| `50` | ~ 134 A | ~ 168 A | MCCB 125A – 160A |
| `70` | ~ 171 A | ~ 213 A | MCCB 160A – 200A |
| `95` | ~ 207 A | ~ 258 A | MCCB 200A – 250A |
| `120` | ~ 239 A | ~ 299 A | MCCB 250A |
| `150` | ~ 275 A | ~ 344 A | MCCB 300A – 320A |
| `185` | ~ 314 A | ~ 392 A | MCCB 350A – 400A |
| `240` | ~ 370 A | ~ 461 A | MCCB 400A |

*(Với dòng $> 400\text{A}$: Dùng nhiều sợi cáp 1 lõi hoặc đa lõi đi song song trên mỗi pha, VD: `2×(3×185 + 1×95)` hoặc chuyển sang **Busway / Thanh cái**).*

### B. Kiểm tra Sụt áp ($\Delta U\%$)
$$\Delta U\% = \frac{b \cdot I_b \cdot L \cdot (R \cos\varphi + X \sin\varphi)}{U_n} \times 100\%$$
*(Trong đó: $b = 2$ cho mạch 1 pha, $b = \sqrt{3}$ cho mạch 3 pha; $L$ tính bằng km; $R \approx \frac{22.5}{S}\ (\Omega/\text{km})$ cho đồng; $X \approx 0.08\ \Omega/\text{km}$).*
- **Giới hạn cho phép (IEC 60364):** Chiếu sáng **$\le 3\%$**; Động lực / Tải khác **$\le 5\%$**. Nếu vượt ngưỡng $\rightarrow$ tăng lên 1 cấp tiết diện cáp.

---

## 4. Bảng tra Thanh cái Đồng (Copper Busbar E-Cu, Tủ kín $35^\circ\text{C} - 40^\circ\text{C}$)

| Dòng định mức $I_n$ (A) | Quy cách Thanh Pha (`L1, L2, L3`) | Tổng tiết diện ($\text{mm}^2$) | Thanh Trung tính (`N`) / Tiếp địa (`PE`) |
| :---: | :---: | :---: | :--- |
| `100 A` | `1 × (20 × 3)` mm | 60 | `20 × 3` mm |
| `160 A` | `1 × (20 × 5)` mm | 100 | `20 × 3` mm |
| `250 A` | `1 × (30 × 5)` mm | 150 | `20 × 5` hoặc `30 × 5` mm |
| `400 A` | `1 × (40 × 6)` hoặc `1 × (30 × 10)` mm | 240–300 | `30 × 5` hoặc `40 × 5` mm |
| `630 A` | `1 × (50 × 10)` mm | 500 | `40 × 5` hoặc `50 × 5` mm |
| `800 A` | `1 × (60 × 10)` mm | 600 | `50 × 5` hoặc `60 × 5` mm |
| `1000 A` | `1 × (80 × 10)` mm | 800 | `60 × 5` hoặc `50 × 10` mm |
| `1250 A` | `1 × (100 × 10)` hoặc `2 × (50 × 10)` mm | 1000 | `60 × 10` mm |
| `1600 A` | `2 × (60 × 10)` mm | 1200 | `80 × 10` mm |
| `2000 A` | `2 × (80 × 10)` mm | 1600 | `100 × 10` mm |
| `2500 A` | `2 × (100 × 10)` mm | 2000 | `2 × (60 × 10)` mm |
| `3200 A` | `3 × (100 × 10)` mm | 3000 | `2 × (80 × 10)` mm |

*(Lưu ý: Nếu tải có nhiều sóng hài như Biến tần, LED, UPS $\rightarrow$ bắt buộc chọn thanh `N` bằng **100%** tiết diện thanh pha).*

---

## 5. Bảng chọn nhanh Khởi động Động cơ 3 Pha ($380/400\text{VAC}$, Loại 2 - Type 2 Coordination)

| Công suất ($P$) | $I_n$ động cơ ($\approx$ A) | Khởi động Trực tiếp (DOL) *(CB + Contactor AC-3 + OLR)* | Khởi động Sao – Tam giác (Star-Delta) *(CB + $K_{\text{Main}}/K_{\Delta}$ + $K_Y$ + OLR)* |
| :---: | :---: | :--- | :--- |
| `0.75 kW` | 1.9 A | CB `6A` + K `9A` + OLR `1.6–2.5A` | — |
| `1.5 kW` | 3.6 A | CB `10A` + K `9A` + OLR `2.5–4A` | — |
| `2.2 kW` | 5.0 A | CB `16A` + K `9A` + OLR `4–6A` | — |
| `4.0 kW` | 8.5 A | CB `20A–25A` + K `12A` + OLR `7–10A` | — |
| `5.5 kW` | 11.5 A | CB `25A–32A` + K `18A` + OLR `9–13A` | — |
| `7.5 kW` | 15.5 A | CB `32A–40A` + K `25A` + OLR `12–18A` | MCCB `32A` + K `12A / 9A` + OLR `7–10A` |
| `11 kW` | 22 A | MCCB `50A` + K `32A` + OLR `18–25A` *(Chỉ khi nguồn khỏe)* | MCCB `50A` + K `18A / 12A` + OLR `12–18A` *(Khuyên dùng)* |
| `15 kW` | 29 A | MCCB `63A` + K `40A` + OLR `23–32A` *(Chỉ khi nguồn khỏe)* | MCCB `63A` + K `25A / 18A` + OLR `16–24A` *(Khuyên dùng)* |
| `18.5 kW` | 35 A | — (Bắt buộc dùng Y-Δ / Soft Start / VFD) | MCCB `80A` + K `25A / 18A` + OLR `17–25A` |
| `22 kW` | 41 A | — | MCCB `100A` + K `32A / 25A` + OLR `23–32A` |
| `30 kW` | 55 A | — | MCCB `125A` + K `40A / 25A` + OLR `28–36A` |
| `37 kW` | 67 A | — | MCCB `160A` + K `50A / 32A` + OLR `37–50A` |
| `45 kW` | 81 A | — | MCCB `160A` + K `65A / 40A` + OLR `48–65A` |
| `55 kW` | 98 A | — | MCCB `200A` + K `80A / 50A` + OLR `55–70A` |
| `75 kW` | 133 A | — | MCCB `250A` + K `95A / 65A` + OLR `63–80A` |

*(Ghi chú: Với mạch **Sao – Tam giác**, Rơ-le nhiệt đặt trong nhánh dây pha nên chỉnh định ở mức $I_{\text{OLR}} \approx 0.58 \times I_n$; dòng qua $K_{\text{Main}}$ và $K_{\Delta}$ là $0.58 \times I_n$, dòng qua $K_Y$ là $0.33 \times I_n$).*

### Quy tắc chọn Biến tần (VFD) & MCCB đầu vào
1. **Chọn Biến tần theo dòng định mức ($I_{n\_\text{VFD}} \ge I_{n\_\text{motor}}$):** Không chỉ chọn theo `kW`, bắt buộc kiểm tra dòng định mức đầu ra của VFD lớn hơn hoặc bằng dòng định mức động cơ và phân biệt đúng chế độ tải:
   - **Heavy Duty (`HD`):** Quá tải `150% / 60s` — dùng cho tải mô-men không đổi (băng tải, máy nén, cẩu trục, máy nghiền).
   - **Normal Duty (`ND`):** Quá tải `110–120% / 60s` — dùng cho tải mô-men biến thiên (bơm ly tâm, quạt thông gió).
2. **Chọn MCCB & Phụ kiện lọc cho VFD:**
   - Chọn MCCB đầu vào theo dòng vào định mức của biến tần ($I_{n\_\text{MCCB}} \ge 1.25 \times I_{\text{in\_VFD}}$), không cần Rơ-le nhiệt ở đầu ra động cơ.
   - Bổ sung **Cuộn kháng AC/DC (AC/DC Choke)** để giảm méo sóng hài đầu vào (khi công suất lớn hoặc lưới yếu) và **Bộ lọc EMC / Cuộn kháng đầu ra (`Output Reactor` / `dV/dt filter`)** khi chiều dài cáp từ VFD đến động cơ lớn (thường $\ge 30\text{–}50\text{ m}$).

---

## 6. Tính Dung lượng & Chọn Thiết bị Nhánh Tụ bù ($Q_c$, IEC 60831-1)

1. **Tính tổng dung lượng bù ($Q_c$, kVAR):**
   $$Q_c = P_{\text{tổng\_kW}} \times (\tan\varphi_1 - \tan\varphi_2)$$
   - $\cos\varphi_1$: Hệ số công suất trước bù ($0.7 \div 0.8$); $\cos\varphi_2$: Mục tiêu sau bù (**$0.92 \div 0.95$**).
   - *Ước lượng nhanh:* Với $\cos\varphi_1 \approx 0.78 \rightarrow 0.95$, cần dung lượng bù khoảng **$45\% \div 50\% P_{\text{kW}}$**, chia nhiều cấp (VD: `10 + 20 + 20 + 50 kVAR`) cho bộ điều khiển `APFC`.
2. **Tính Dòng nhánh tụ ($I_c$) & Chọn Thiết bị (xét sóng hài & dung sai IEC 60831-1):**
   $$I_c = \frac{Q_c\ (\text{VA})}{\sqrt{3} \cdot U}$$
   - **MCCB nhánh tụ:** $I_{n\_\text{MCCB}} \ge (1.35 \div 1.5) \times I_c$.
   - **Contactor đóng cắt tụ & Cáp nhánh tụ:** $I_z \ge (1.43 \div 1.5) \times I_c$.
3. **Chọn Điện áp định mức Bình tụ khi có Cuộn kháng lọc sóng hài ($p = 7\%$ hoặc $14\%$):**
   - Khi ghép cuộn kháng nối tiếp trên lưới $400\text{VAC}$, điện áp đặt lên đầu cực bình tụ tăng lên thành $\frac{U}{1 - p}$.
   - **Bắt buộc:** Dùng tụ định mức **`440VAC`** (cho cuộn kháng $p=7\%$) hoặc **`480–525VAC`** (cho cuộn kháng $p=14\%$). **Tuyệt đối không** dùng bình tụ `400VAC` ghép với cuộn kháng vì sẽ gây quá áp, phồng hoặc nổ tụ.
