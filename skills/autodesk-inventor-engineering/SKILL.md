---
name: autodesk-inventor-engineering
description: >-
  Industrial-grade Autodesk Inventor Professional engineering workflow via COM API & iLogic:
  portable .ipj project generation, Master Skeleton parametric architecture (Derive), fully constrained
  Planar Sketches (kFullyConstrainedConstraintStatus), DOF=0 & interference-free Assemblies (AnalyzeInterference),
  Sheet Metal DFM (K-Factor, Corner Relief, FlatPattern verification), Weldment Cut Lists (ISO 2553),
  and automated .idw / layered Flat Pattern .dxf (OUTER_PROFILE, INNER_CUTS, BEND_UP, BEND_DOWN) export.
---

# Autodesk Inventor Professional Engineering Skill

Skill chuyên sâu cho **Thiết kế Cơ khí Tham số**, **Kim loại tấm (Sheet Metal)**, **Kết cấu Hàn (Weldments)** và **Tự động hóa Bản vẽ Xưởng (`.idw` / Flat Pattern `.dxf`)** trên **Autodesk Inventor Professional**.

---

## 1. Bốn Trụ Cột Kỹ Thuật Bắt Buộc

### Trụ cột 1: Khởi tạo `.ipj` Chuẩn Độc Lập Máy Trạm
- Mọi dự án Inventor **bắt buộc** khởi tạo file `.ipj` XML chuẩn bằng [scripts/create_inventor_ipj.py](scripts/create_inventor_ipj.py):
  - `Workspace = .\` (tương đối theo thư mục gốc dự án).
  - `Content Center Files = .\03_Purchased_Standard\ContentCenter\` (độc lập máy trạm, `Pack and Go` sang bất kỳ máy kỹ sư nào cũng **`0 Broken Links`**).

### Trụ cột 2: Kiến trúc Tham số `Master Skeleton` & `Derive`
- Bắt buộc tạo file gốc `02_Parts\[Code]-PRT000-MasterSkeleton.ipt` chứa toàn bộ **User Parameters** chuẩn `PascalCase` có gắn đơn vị và mô tả (`CabinetWidth = 800 mm`, `CabinetHeight = 1200 mm`, `CabinetDepth = 300 mm`, `SheetThickness = 2.0 mm`, `DoorGap = 2.0 mm`).
- Mọi chi tiết con (`.ipt` vỏ tủ, cánh tủ, tấm lắp, khung hàn) nhận tham số qua **`Derive`** từ `MasterSkeleton.ipt` — chỉ cần sửa 1 tham số ở Skeleton, toàn bộ cụm lắp (`.iam`) và bản vẽ (`.idw`) tự động cập nhật đồng bộ mà không gãy ràng buộc.

### Trụ cột 3: Kỷ Luật Ràng Buộc Hình Học (`Sketch & Assembly Discipline`)
- **Planar Sketch:** 100% Sketch bắt buộc đạt `ConstraintStatus == kFullyConstrainedConstraintStatus` qua API trước khi `Extrude` / `Flange` / `Cut`.
- **Assembly (`.iam`):**
  - Chi tiết gốc (`PRT000` / `FRM001`) bắt buộc **`Grounded`** tại gốc tọa độ `Origin`.
  - Mọi chi tiết tĩnh phải đạt **`DOF = 0`**; chi tiết chuyển động (cánh cửa, tấm lắp xoay) dùng **`Joint` có `Angular Limits`** (`0°..130°`).
  - Bắt buộc chạy **`AnalyzeInterference()`** đạt **`0 interferences`** (trừ vùng giao ren tiêu chuẩn) trước khi xuất bản vẽ.

### Trụ cột 4: Kim Loại Tấm DFM & Tự Động Xuất Hồ Sơ Xưởng (`.idw` + Flat Pattern `.dxf`)
- Tuân thủ nghiêm ngặt quy chuẩn Kim loại tấm & Kết cấu hàn tại [../autocad-electrical/references/sheet-metal-and-weldment-dfm.md](../autocad-electrical/references/sheet-metal-and-weldment-dfm.md) (`K-Factor`, `R_in`, `Corner Relief`, `Door Gap 2.0–2.5 mm`, `ISO 2553`, `ISO 273`).
- Chạy iLogic Rule [templates/export_sheet_metal_and_idw.iLogicVb](templates/export_sheet_metal_and_idw.iLogicVb) (hoặc MCP `inventor-direct`) để:
  1. Kiểm tra tồn tại `FlatPattern` trên mọi file `SHM` (`HasFlatPattern = True`).
  2. Xuất `.dxf` cắt laser sạch tách rõ Layer **`OUTER_PROFILE`**, **`INNER_CUTS`**, **`BEND_UP`** (nét liền) và **`BEND_DOWN`** (nét đứt, màu khác biệt) để thợ chấn không bao giờ chấn ngược chiều.
  3. Đồng bộ 100% `iProperties` (`Part Number`, `Description`, `Material`, `Revision`, `Mass`) sang khung tên `.idw` và bảng `Parts List / Cut List`.

---

## 2. MCP Server `inventor-direct` (In-Process `.NET 10` Add-in via Named Pipe)
- Server: `C:\Users\Gaadz\.gemini\config\mcp_servers\inventor_mcp_server.py` (`v2.0.0`) → Named Pipe `\\.\pipe\agy-inventor-direct` → `Agy.InventorBridge.dll` (chạy trực tiếp bên trong `Inventor.exe`, không qua PowerShell COM).
- Đủ **6 tools**:
  1. `inventor_status`: Kiểm tra tiến trình Inventor 2027, tài liệu đang mở, `.ipj` hiện hành qua Named Pipe.
  2. `inventor_create_or_open`: Tạo mới `.ipt` (Standard / Sheet Metal), `.iam`, `.idw` từ Template hệ mét `mm` hoặc mở/kích hoạt `.ipj`/file có sẵn.
  3. `inventor_run_script`: Chạy rule **iLogic / VB.NET** trực tiếp in-process (`ThisApplication`, `ThisDoc.Document` gắn sẵn) bọc trong **`Inventor.Transaction` nguyên tử** (tự động `txn.Abort()` rollback toàn bộ nếu có bất kỳ lỗi nào).
  4. `inventor_check_constraints_and_interference`: Kiểm tra 100% Sketch đạt `kFullyConstrainedConstraintStatus`, kiểm tra `Grounded` & bậc tự do `DOF = 0`, và chạy `AnalyzeInterference()`.
  5. `inventor_update_parameters`: Cập nhật `UserParameters`/`ModelParameters` nguyên tử trong `Transaction`, `Update2(True)` và `Save()`.
  6. `inventor_export_flat_pattern_dxf`: Xuất `FlatPattern` `.dxf` tách rõ `OUTER_PROFILE`, `INNER_CUTS`, `BEND_UP` (Continuous `37633`), `BEND_DOWN` (Dashed `37634`).
- Mẫu code iLogic VB.NET chuẩn (`MasterSkeleton`, `SheetMetal`, `Assembly`, `.idw`): xem [references/inventor-com-recipes.md](references/inventor-com-recipes.md).
