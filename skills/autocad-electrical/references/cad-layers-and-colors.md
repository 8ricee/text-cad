# Quy chuẩn Đồ họa CAD: Layer, Wire Type (Màu + Tiết diện), Nét in & Chữ viết

Quy chuẩn phân bổ **Layer**, **Thuộc tính Wire Type (`COLOR` + `SIZE`)**, **Mã màu (ACI Color)**, **Độ dày nét in (Lineweight)** và **Plot Style (`.ctb`)** áp dụng đồng bộ cho cả **Sơ đồ Nguyên lý (Schematic 2D)** và **Bản vẽ Thiết kế Tủ & Gia công Đồng (Panel Layout 2D)**.

---

## 1. Bảng Layer & Wire Type trên Sơ đồ Nguyên lý (Schematic 2D)

### A. Layer Dây điện (`Create/Edit Wire Type` – Lệnh `AEWIRETYPE`)
> **Quy tắc bắt buộc:** Trong hộp thoại `Create/Edit Wire Type`, **không được chỉ đặt tên Layer chung chung** (như `PWR_L1` hay `CTRL_24VDC`). Bắt buộc phải khai báo đầy đủ 2 cột thuộc tính **`Color`** và **`Size`** cho từng loại dây (và đặt tên Layer theo cú pháp `<MẠCH>_<MÀU>_<TIẾT_DIỆN>`) để báo cáo **From/To Wire List** xuất ra chính xác màu dây và tiết diện cho thợ đấu tủ.

| Tên Layer (`Wire Type`) | Cột `Color` (ACADE) | Cột `Size` (ACADE) | Ý nghĩa mạch | Mã màu CAD (ACI) | Độ dày nét in | Kiểu nét (`Linetype`) |
| :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| `PWR_L1_BK_2.5` *(hoặc 4.0..240)* | `BK` (IEC) / `RD` (TCVN) | `2.5mm²` *(theo tải)* | Pha L1 động lực | `1` (Red) hoặc `32` (Brown) | `0.35 mm` | `CONTINUOUS` |
| `PWR_L2_BK_2.5` | `BK` (IEC) / `YE` (TCVN) | `2.5mm²` *(theo tải)* | Pha L2 động lực | `40` / `30` (Dark Yellow/Orange, tránh `2` vì mờ trên nền trắng) | `0.35 mm` | `CONTINUOUS` |
| `PWR_L3_BK_2.5` | `BK` (IEC) / `BU` (TCVN) | `2.5mm²` *(theo tải)* | Pha L3 động lực | `5` (Blue) hoặc `8` (Grey) | `0.35 mm` | `CONTINUOUS` |
| `PWR_N_BU_2.5` | `BU` (Light Blue) | `2.5mm²` *(theo tải)* | Dây Trung tính (`N`) | `4` (Cyan) | `0.35 mm` | `CONTINUOUS` |
| `PWR_PE_GNYE_2.5` | `GNYE` (Green-Yellow) | `2.5mm²` *(theo tải)* | Dây Tiếp địa (`PE`) | `3` (Green) | `0.35 mm` | **`CONTINUOUS`** *(Không dùng DASHDOT vì PE là dây vật lý)* |
| `CTRL_220AC_RD_1.0` | `RD` (Red) | `1.0mm²` | Điều khiển L (220VAC) | `6` (Magenta) | `0.25 mm` | `CONTINUOUS` |
| `CTRL_220AC_WH_1.0` | `WH` / `BU` | `1.0mm²` | Điều khiển N (220VAC) | `4` (Cyan) | `0.25 mm` | `CONTINUOUS` |
| `CTRL_24VDC_DBU_0.75` | `DBU` (Dark Blue) / `RD` | `0.75mm²` | Nguồn +24VDC & DO | `30` (Orange) | `0.25 mm` | `CONTINUOUS` |
| `CTRL_0VDC_BUWH_0.75` | `BU/WH` (Blue-White) | `0.75mm²` | Nguồn 0VDC Common (PELV) | `5` (Blue) | `0.25 mm` | `CONTINUOUS` |
| `SIG_PLC_BU_0.5` | `BU` (Blue) | `0.5mm²` | Tín hiệu PLC DI / AI | `3` (Green) hoặc `4` (Cyan) | `0.25 mm` | `CONTINUOUS` |
| `SAFE_24VDC_YE_0.75` | `YE` (Yellow) | `0.75mm²` | Mạch Safety 2 kênh (E-Stop / F-DI) | `40` (Dark Yellow) | `0.25 mm` | `CONTINUOUS` |

### B. Layer Ký hiệu, Chữ & Khung bản vẽ (Schematic Elements)
| Tên Layer | Đối tượng | Mã màu CAD (ACI) | Độ dày nét in | Kiểu nét |
| :--- | :--- | :--- | :---: | :--- |
| `SYMS` | Ký hiệu thiết bị Icon Menu | `7` (White/Black) | `0.25 mm` | `CONTINUOUS` |
| `TAGS` / `DESC` | Tên thiết bị (`TAG1`) & Mô tả | `7` hoặc `3` (Green) | `0.18 mm` | `CONTINUOUS` |
| `WIRENO` | Số dây (`Wire Number`) | `40` / `30` (Dark Yellow/Orange) hoặc `7` | `0.18 mm` | `CONTINUOUS` |
| `LOC_BOX` / `MECH_LINK` | Đường bao vùng lắp đặt (`+LOC`) / Liên động cơ khí | `8` (Grey) | `0.15 mm` | `DASHDOT` / `DASHED` |
| `BORDER` | Khung bản vẽ & Khung tên (`Title Block`) | `7` (White/Black) | `0.50 mm` | `CONTINUOUS` |

---

## 2. Bảng Layer & Màu sắc trên Bản vẽ Tủ & Gia công Đồng (Panel Layout 2D)

| Tên Layer | Đối tượng | Mã màu CAD (ACI) | Độ dày nét in | Kiểu nét |
| :--- | :--- | :--- | :---: | :--- |
| `PNL_ENCLOSURE` | Khung vỏ tủ điện (Mặt trước, Cạnh, Hông) | `7` (White/Black) | `0.35 mm` | `CONTINUOUS` |
| `PNL_PLATE` | Tấm lắp thiết bị (Mounting Plate) | `8` (Dark Grey) | `0.25 mm` | `CONTINUOUS` |
| `PNL_FOOTPRINT` | Hình chiếu thiết bị (`AEFOOTPRINT`) | `4` (Cyan) hoặc `7` | `0.25 mm` | `CONTINUOUS` |
| `PNL_DUCT_RAIL` | Thanh DIN Rail & Máng cáp (Wire Duct) | `9` (Light Grey) | `0.18 mm` | `CONTINUOUS` |
| `PNL_BUSBAR_L1` | Thanh cái đồng Pha L1 | `1` (Red) | `0.35 mm` | `CONTINUOUS` |
| `PNL_BUSBAR_L2` | Thanh cái đồng Pha L2 | `40` / `30` (Dark Yellow/Orange) | `0.35 mm` | `CONTINUOUS` |
| `PNL_BUSBAR_L3` | Thanh cái đồng Pha L3 | `5` (Blue) | `0.35 mm` | `CONTINUOUS` |
| `PNL_BUSBAR_N` | Thanh cái Trung tính `N` | `4` (Cyan) | `0.35 mm` | `CONTINUOUS` |
| `PNL_BUSBAR_PE` | Thanh cái Tiếp địa `PE` | `3` (Green) | `0.35 mm` | `CONTINUOUS` |
| `PNL_HOLE_BOLT` | Lỗ đột Busbar & Bu-lông | `6` (Magenta) | `0.20 mm` | `CONTINUOUS` |
| `PNL_CENTER` | Đường tâm lỗ đột & tâm thiết bị | `1` (Red) | `0.13 mm` | `CENTER` |
| `PNL_DIM` | Đường kích thước (Dimensions) | `3` (Green) hoặc `4` (Cyan) | `0.18 mm` | `CONTINUOUS` |
| `PNL_BALLOON` | Số thứ tự Balloon (ISO 6433), Section & Detail Callouts | `7` (White/Black — cấm dùng `2` Yellow vì mờ trên nền trắng) | `0.25 mm` | `CONTINUOUS` |

---

## 3. Quy chuẩn Chữ viết (Text), Kích thước (Dim) & Xuất PDF (Plot Style)

1. **Font chữ, Khắc phục Lỗi `?` Tiếng Việt & Chiều cao chữ (khi in trên giấy A3 tỷ lệ 1:1):**
   - **Cấm để Textstyle mặc định `txt.shx` của AutoCAD:** Font `txt.shx` không có bảng mã Unicode nên mọi chữ Tiếng Việt có dấu (`Ự, Ạ, Đ, Ể, Ẩ, Ố...`) sẽ bị biến thành dấu hỏi chấm (`?`) và chữ bị bè ngang tràn qua khung bảng.
   - **Bắt buộc cấu hình Textstyle dùng Font TrueType Unicode (`arial.ttf`, `isocpeur.ttf` hoặc `tahoma.ttf`)** và lưu file ở chuẩn **`R2018 (AC1032 UTF-8)`** trở lên:
     - Trong AutoCAD / ACADE: Gõ `STYLE` → chọn style `Standard` / `WD_IEC` → đổi `Font Name` thành **`Arial` (`arial.ttf`)**, `Width Factor = 0.80 – 0.85`.
     - Khi sinh bằng `ezdxf`: Bắt buộc gán `doc.styles.get("Standard").dxf.font = "arial.ttf"` và tạo style `"VN_ARIAL"` (`font="arial.ttf"`).
   - **Bắt buộc kẻ lưới ô thực sự cho mọi Bảng biểu & Khung tên (`Real Grid Lines`):**
     - Mọi bảng trên bản vẽ (`Title Block`, `Panel BOM`, `Device Schedule`, `Nameplate Schedule`, `Busbar Cut List`) phải được vẽ bằng đối tượng `TABLE` hoặc **lưới đường kẻ ngang (Rows) và đường kẻ dọc (Columns) khép kín từng ô (Cell)**; tự động co `width_factor` hoặc cắt dòng để chữ nằm gọn 100% trong lòng ô, **tuyệt đối cấm gõ ký tự gạch đứng `|` trong 1 dòng text dài để giả làm bảng**.
   - Chiều cao chữ tiêu chuẩn:
     - `TAG` thiết bị & Số dây (`Wire Number`): `2.5 mm`.
     - Mô tả thiết bị (`DESC`), Nội dung ô bảng: `1.8 – 2.2 mm` (`width_factor = 0.80`).
     - Tiêu đề hình chiếu (`FRONT VIEW`, `MOUNTING PLATE`): `3.5 – 4.5 mm` (trên giấy in).
2. **Quy chuẩn Phân tách Không gian `Model Space` vs `Paper Space` Chuẩn ACADE & Đối tượng `DIMENSION` Gốc AutoCAD:**
   - **Tách biệt rõ Sơ đồ nguyên lý (`1:1`) vs Bản vẽ Bố trí tủ / Gia công cơ khí (`1:S`):**
     - Khai báo đơn vị bản vẽ chuẩn hệ mét: `$INSUNITS = 4` (`Millimeters`), `$MEASUREMENT = 1` (`Metric`).
     - **Trang Sơ đồ nguyên lý, SLD, PLC I/O & Terminal (`01..06`, `09` — Tỷ lệ `1:1`):** Đặt block cấu hình `WD_M`, Khung bản vẽ ISO A3 (`420 × 297 mm`), Lưới chia vùng **`X-Zones (0..9)`** và Khung tên **`TITLE_BLOCK_A3_BILINGUAL` (`WD_TB`)** ngay trong **`Model Space` ở tỷ lệ `1:1 mm`** để khớp cứng gốc tọa độ `XY Grid Origin` của `WD_M` (không đặt `X-Zones` của Schematic ngoài Paper Space tránh sai lệch tham chiếu `/Trang.Cột`).
     - **Trang Bố trí Mặt tủ & Gia công Thanh cái (`07_panel_layout`, `08_busbar_fabrication` — Tỷ lệ thu phóng `1:20`, `1:10`, `1:2.5`):** **100% hình học cơ khí & chi tiết trích phóng đại (`Detail A..D`) nằm trong `Model Space` ở kích thước thật `1:1 mm` (`scale = 1.0`)**; trên **`Paper Space (Layout ISO_A3)`** đặt Khung bản vẽ ISO, Khung tên `WD_TB`, Bảng thống kê và các cửa sổ **`VIEWPORT`** khóa đúng tỷ lệ chuẩn ISO 5455 (`1:1`, `1:2`, `1:2.5`, `1:5`, `1:10`, `1:20`, `1:25`).
   - **100% Dùng Thực thể `DIMENSION` Gốc của AutoCAD (Cấm vẽ tay bằng `LINE` + `TEXT`):**
     - **Tuyệt đối cấm** kẻ đoạn thẳng `LINE` + đặt chữ `TEXT` để giả làm đường kích thước, và **cấm ghi đè chuỗi số giả** lên thuộc tính text của Dim (phải để mặc định tự đo hoặc dùng ký hiệu động `<>`).
     - Sử dụng thực thể `DIMENSION` chuẩn của AutoCAD (`DIMLINEAR`, `DIMALIGNED`, `DIMDIAMETER`, `DIMRADIUS`, `DIMANGULAR`; trong `ezdxf` gọi `msp.add_linear_dim(...).render()`, `msp.add_diameter_dim(...).render()`, `msp.add_aligned_dim(...).render()`) đặt trên Layer `PNL_DIM`.
     - **Thông số chuẩn `DimStyle` (`ISO_MM`):** Font chữ `VN_ARIAL` (`arial.ttf`), mũi tên đặc kín (`Closed filled`), chiều cao chữ trên giấy `dimtxt = 2.5 mm`, cỡ mũi tên `dimasz = 2.5 mm`, khe hở gốc gióng `dimexo = 1.0 mm`, độ nhô đường gióng `dimexe = 1.25 mm`, chữ nằm phía trên và song song đường kích thước (`dimtad = 1`, `dimtih = 0`, `dimtoh = 0`, `dimgap = 0.8 mm`), dấu chấm thập phân (`dimdsep = '.'`), ẩn số `0` vô nghĩa sau dấu chấm (`dimzin = 8`), hệ số đo tuyến tính **`dimlfac = 1.0`**, và `dimscale = S` khớp với mẫu số tỷ lệ `Viewport` `1:S`.
   - **Xuất PDF / Ảnh kiểm tra (`ezdxf.addons.drawing`):**
     - Khi kết xuất DXF sang PDF/PNG bằng Python, bắt buộc dùng `ezdxf.addons.drawing` (`Frontend` + `RenderContext` + `MatplotlibBackend`) để hiển thị đầy đủ 100% cửa sổ `VIEWPORT`, mũi tên, đường gióng và con số của thực thể `DIMENSION` (cấm viết vòng lặp sơ sài chỉ đọc `LINE`/`TEXT` làm mất `DIMENSION`).
   - **Ký hiệu Đánh dấu Chuẩn Quốc tế (ISO 128 / ISO 129-1 / ISO 6433 / ISO 5456-2):**
     - **Balloon (`ISO 6433` & `ISO 128-22`):** Dùng Layer `PNL_BALLOON` (`ACI 7` White/Black, tuyệt đối không dùng màu vàng `ACI 2`). Đường dẫn Leader bắt buộc có **chấm tròn đặc (`•`)** khi chỉ vào bề mặt chi tiết hoặc **mũi tên đặc (`→`)** khi chỉ vào cạnh biên; không đặt đè lên tiêu đề hình chiếu.
     - **Đường cắt Mặt cắt (`ISO 128-30` – Section Cutting Plane):** Mọi hình cắt (`MẶT CẮT A-A`, `B-B`) bắt buộc phải có **Cutting Plane Line** (nét `CENTER` với 2 đầu tô đậm, mũi tên chỉ hướng nhìn và chữ cái `A`, `B`) đặt trên hình chiếu gốc.
     - **Khoanh vùng Chi tiết Phóng đại (`ISO 128-34` – Detail Callout):** Mọi hình trích phóng đại (`DETAIL A..D`) bắt buộc phải có **vòng tròn khoanh vùng** kèm nhãn chữ cái liên kết trên hình chiếu gốc.
     - **Biểu tượng Góc chiếu (`ISO 5456-2` – Projection Symbol):** Khung tên bắt buộc vẽ **biểu tượng hình học chuẩn ISO** (hình nón cụt + 2 vòng tròn đồng tâm) cho `THIRD ANGLE` (hoặc `FIRST ANGLE`).
     - **Tiền tố số lượng trên Dim (`ISO 129-1`):** Dùng tiền tố động kèm `<>` (VD: `6× <>`, `4× <>`) để giữ nguyên khả năng tự đo `1:1` của AutoCAD.
3. **Chế độ xuất PDF (`.ctb` Plot Style):**
   - **Bản vẽ kiểm tra kỹ thuật số (Digital Review PDF):** Xuất **PDF có màu (Color)** theo đúng màu Layer ở trên.
   - **Bản vẽ phát hành in giấy (Hardcopy Official Release):** Sử dụng `monochrome.ctb` (đen trắng) hoặc file `.ctb` riêng có thiết lập **Lineweight rõ ràng** (`0.50 mm` khung $\rightarrow$ `0.35 mm` động lực/vỏ tủ $\rightarrow$ `0.25 mm` điều khiển/thiết bị $\rightarrow$ `0.15–0.18 mm` dim/text/nét đứt).
