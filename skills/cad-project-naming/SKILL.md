---
name: cad-project-naming
description: Enforce strict folder structure and technical file naming standards for AutoCAD and Autodesk Inventor. Mandatory trigger before creating, saving, organizing, or exporting any CAD project, drawing, part, or assembly. (Quản lý cấu trúc thư mục và quy chuẩn đặt tên file kỹ thuật cho AutoCAD & Autodesk Inventor. Bắt buộc kích hoạt trước khi tạo mới, lưu trữ hoặc tổ chức bất kỳ bản vẽ/mô hình CAD nào.)
---

# CAD Project & File Naming Standard (Quy Chuẩn Thư Mục & Đặt Tên File CAD)

## 1. Fixed Root Directories (Thư Mục Gốc Cố Định)
All CAD projects MUST be stored under the exact root directory matching the software:
- **AutoCAD:** `F:\Projects\CAD\AutoCAD`
- **Autodesk Inventor:** `F:\Projects\CAD\Inventor`

## 2. Mandatory Execution Gate (Cổng Kiểm Soát Kép: Hành Chính + Kỹ Thuật)
**CRITICAL:** NEVER create folders or files before completing all 3 steps below:
1. **Ask (Hỏi thông tin Hành chính & Kỹ thuật tối thiểu trong 1 lượt — cấm tự đoán):**
   > *"Bạn đang thiết kế trên phần mềm nào (AutoCAD hay Inventor), cho dự án/khách hàng nào, hạng mục gì và có mã dự án riêng không? Đồng thời cho tôi các thông số kỹ thuật đầu vào:"*
   - **Nếu là Tủ điện:** Điện áp & Sơ đồ nối đất (`3P+N+PE 380/400V TN-S`?), Dòng cắt $I_{cu}$ (`kA`), Vị trí lắp & Cấp `IP`/Vật liệu (`Trong nhà RAL7035 IP54` hay `Ngoài trời SUS304 IP65`), Hướng cáp vào/ra (`Đáy` hay `Nóc`), Hãng thiết bị ưu tiên.
   - **Nếu là Cơ khí / Kim loại tấm:** Tải trọng làm việc (`kg`), Vật liệu & Độ dày tôn/thép hộp (`mm`), Bán kính dao chấn xưởng (`R_in`), Kích thước tâm lỗ thiết bị đặt lên khung.
2. **Infer & Normalize (Suy luận & Chuẩn hóa):**
   - Translate Vietnamese technical terms into standard English `PascalCase` (e.g., *"tủ điện điều khiển chính"* → `MainControlPanel`, *"xe đẩy quả cân chuẩn"* → `CalibrationCart`).
   - Strip all Vietnamese diacritics for proper nouns/client names (e.g., *"Hòa Phát"* → `HP` or `HoaPhat`).
   - Default `ClientCode` to `INT` (Internal) if no external client is mentioned.
   - Default `YYYY` to the current year if not specified.
3. **Confirm (Xác nhận):** Display the proposed folder tree and file path using Section 7's template and wait for explicit user approval (`Y`) before executing any file system operation.

## 3. Global Naming Rules (Quy Tắc Đặt Tên Chung)
- **Allowed characters (Ký tự hợp lệ):** `A-Z`, `a-z`, `0-9`, `_`, `-` ONLY.
- **Forbidden (Tuyệt đối cấm):** Spaces (khoảng trắng), Vietnamese accents (dấu tiếng Việt), and special characters (`\ / : * ? " < > | & % #`).
- **Casing (Quy tắc viết hoa):**
  - `UPPERCASE`: Codes (`ClientCode`, `ProjectCode`, `Discipline`, `DocType`, `Type`).
  - `PascalCase`: Descriptive names (`ProjectName`, `Description`).
- **Project Folder Format (Tên thư mục dự án):**
  `[YYYY]_[ClientCode]_[ProjectName]`
  - `YYYY`: 4-digit year / Năm thực hiện (e.g., `2026`).
  - `ClientCode`: 2–5 uppercase letters / Mã khách hàng (e.g., `HP`, `NHC`, `INT`).
  - `ProjectName`: Concise `PascalCase` name / Tên dự án ngắn gọn (e.g., `BeltWeigherRetrofit`, `FEMS_Panel`).

## 4. AutoCAD Standard (`F:\Projects\CAD\AutoCAD\[ProjectFolder]`)

### Standard Subfolders (Cấu trúc thư mục con)
- `01_Drawings/` — Active working `.dwg` files (File `.dwg` đang làm việc).
- `02_Xrefs_Blocks/` — External references and project-specific blocks (File Xref, block riêng của dự án).
- `03_Issued_PDF/` — Released `.pdf` / `.plt` prints (Bản vẽ PDF/PLT đã phát hành).
- `04_BOM_Docs/` — Excel BOMs, specs, and datasheets (File bóc tách vật tư, tài liệu kỹ thuật).
- `99_Archive/` — Superseded/old drawing versions (Phiên bản cũ).

### File Naming Format (Quy chuẩn tên file)
- **File `.dwg`/`.dxf` đang làm việc (trong `01_Drawings/`):** `[ProjectCode]-[Discipline]-[DocType]-[Description].[ext]` *(KHÔNG gắn hậu tố `_R00` lên file đang làm việc — phiên bản được quản lý bằng Git và thuộc tính `REV` trong Khung tên; chỉ gắn `_R[XX]` lên bản xuất tĩnh trong `03_Issued_PDF/` hoặc `05_Exports/`)*.
- **Dự án AutoCAD Electrical (`.wdp`):** Cho phép tiền tố số tờ `[SheetNo]` ở đầu để tương thích `Project Manager`: `[SheetNo]_[ProjectCode]-[Discipline]-[DocType]-[Description].dwg` (VD: `07_BW500-EL-LAY-MainControlPanel.dwg`).
- **Discipline (Bộ môn):**
  - `EL`: Electrical / Industrial Panels (Điện công nghiệp / Tủ điện)
  - `ME`: Mechanical / Structure (Cơ khí / Kết cấu)
  - `GA`: General Arrangement (Bố trí tổng thể)
  - `PID`: Piping & Instrumentation Diagram (Sơ đồ công nghệ P&ID)
- **DocType (Loại bản vẽ):**
  - `SCH`: Schematic (Sơ đồ nguyên lý)
  - `LAY`: Layout / Panel Front View (Bố trí thiết bị / Mặt tủ)
  - `WIR`: Wiring Diagram (Sơ đồ đấu dây)
  - `DET`: Detail Drawing (Bản vẽ chi tiết gia công)
  - `ASM`: Assembly Drawing (Bản vẽ lắp)
- **Revision (`R[XX]`):** `R00`, `R01`, `R02`... — **CHỈ gắn lên bản phát hành tĩnh** trong `03_Issued_PDF/` hoặc `05_Exports/` (VD: `03_Issued_PDF\BW500-EL-SCH-MainControlPanel_R00.pdf`).
- **Example:** `01_Drawings\04_BW500-EL-SCH-MainControlPanel.dwg` (active) → `03_Issued_PDF\BW500-EL-SCH-MainControlPanel_R00.pdf` (issued).

## 5. Autodesk Inventor Standard (`F:\Projects\CAD\Inventor\[ProjectFolder]`)

### Standard Subfolders (Cấu trúc thư mục con)
- `[ProjectCode]_[ProjectName].ipj` — Inventor Project file MUST reside at the project root (File `.ipj` bắt buộc nằm ở thư mục gốc dự án).
- `01_Assemblies/` — Main assembly and sub-assemblies `.iam` (Cụm lắp tổng & cụm con).
- `02_Parts/` — Custom-designed parts, sheet metal, frame components `.ipt` (Chi tiết tự thiết kế, kim loại tấm, khung thép).
- `03_Purchased_Standard/` — Vendor 3D models `.step` / `.ipt` (Linh kiện mua ngoài tải từ hãng: động cơ, cảm biến, thiết bị tủ điện).
- `04_Drawings/` — Inventor 2D drawings `.idw` / `.dwg` (Bản vẽ 2D xuất từ mô hình 3D).
- `05_Exports/` — Manufacturing / 3D printing / release exports `.step`, `.stl`, `.dxf`, `.pdf` (File xuất gia công, cắt laser, in 3D, PDF phát hành).
- `06_BOM_Docs/` — Exported BOM spreadsheets and calculations (File BOM và tài liệu tính toán).

### File Naming Format (Quy chuẩn tên file)
`[ProjectCode]-[Type][Seq]-[Description].[ext]`
- **Type (Loại đối tượng):**
  - `ASM`: Assembly / Sub-assembly (`.iam`)
  - `PRT`: Standard custom machined/printed part (`.ipt`)
  - `SHM`: Sheet Metal part / enclosure (`.ipt`)
  - `FRM`: Frame Generator / Weldment structure (`.iam` / `.ipt`)
  - `STD`: Purchased / Standard component (`.ipt` / `.step`)
- **Seq (Số thứ tự 3 chữ số):**
  - `000`: Top-level Main Assembly (Cụm lắp tổng).
  - `010`, `020`, `030`...: Sub-assemblies (Cụm lắp con).
  - `001`, `002`, `003`...: Individual parts (Chi tiết đơn).
- **Example Flow:**
  - Project file: `F:\Projects\CAD\Inventor\2026_INT_CalibrationCart\CART_CalibrationCart.ipj`
  - Top Assembly: `01_Assemblies\CART-ASM000-MainAssembly.iam`
  - Sheet Metal Part: `02_Parts\CART-SHM001-SidePanel.ipt`
  - 2D Drawing: `04_Drawings\CART-SHM001-SidePanel.idw`
  - Exported Laser Cut: `05_Exports\CART-SHM001-SidePanel_R00.dxf`

## 6. Strict Constraints (Ràng Buộc Kỹ Thuật Bắt Buộc)
- **World-Class Model vs. Paper Space Separation (ISO 128 / ASME Y14.100):** 100% of ALL design geometry — including main views, sections, 3D views, **and enlarged detail views (`Detail A, B, C, D`)** — MUST be drawn at exact **`1:1 mm`** in **Model Space** (`$INSUNITS = 4`). NEVER draw sheet borders (`BORDER`), Title Blocks, or schedules in Model Space, and NEVER draw part geometry, 3D views, or enlarged detail geometry directly in Paper Space. **Paper Space (`Layout`)** holds ONLY ISO sheet frames (`A4..A0`), Title Blocks, schedules, and calibrated **`VIEWPORT`**s (`1:1`, `1:2`, `1:2.5`, `1:5`, `1:10`, `1:20`, `1:25`) zooming onto Model Space geometry.
- **100% Native AutoCAD `DIMENSION` Entities (No Hand-Drawn Fake Dims):** Every dimension on AutoCAD `.dwg`/`.dxf` drawings MUST use native AutoCAD `DIMENSION` entities (`DIMLINEAR`, `DIMALIGNED`, `DIMDIAMETER`, `DIMRADIUS`, `DIMANGULAR` / `ezdxf` `.add_*_dim(...).render()`) measuring true geometry (`dimlfac = 1.0`). Strictly prohibit faking dimensions with manual `LINE` + `TEXT` or overriding dimension text with hardcoded numbers.
- **No Revision Suffix on Active Inventor 3D Files:** NEVER append `_R00`, `_R01` to active `.ipt` or `.iam` filenames (renaming breaks Inventor assembly/drawing references). Track revisions inside Inventor **iProperties**; only append `_R[XX]` to exported deliverables in `05_Exports/`.
- **Exact 2D-to-3D Name Match (Inventor):** `.idw` / `.dwg` drawing filenames MUST match their parent `.ipt` or `.iam` filename 100%.
- **No Manual `OldVersions`:** NEVER manually create an `OldVersions` folder inside Inventor projects; let Inventor manage it automatically.

## 7. Confirmation Output Template (Mẫu Phản Hồi Xác Nhận)
Always present the proposal to the user in this exact concise format before creating any files:
```text
- Software / Phần mềm: [AutoCAD / Autodesk Inventor]
- Project Folder / Thư mục dự án: [Full Path]
- Project File (.ipj): [Full Path — omit if AutoCAD]
- Target File / File làm việc: [Full Path]
-> Xác nhận tạo cấu trúc này? (Y/N)
```
