# CAD Project Naming Skill (`cad-project-naming`)

Skill quản lý cấu trúc thư mục và quy chuẩn đặt tên file kỹ thuật cho **AutoCAD** và **Autodesk Inventor**.

## Mục đích
- Bắt buộc hỏi thông tin dự án, chuẩn hóa tên sang `PascalCase` / `UPPERCASE` ASCII và xác nhận trước khi khởi tạo thư mục/file.
- Ràng buộc kỹ thuật bắt buộc cho AutoCAD: **Model Space `1:1 mm` tuyệt đối** + **Paper Space `Layout Viewport`** + **100% thực thể `DIMENSION` gốc của AutoCAD** (cấm thu nhỏ hình học trong Model Space, cấm vẽ tay giả đường kích thước bằng `LINE` + `TEXT`).
- Cố định thư mục gốc:
  - AutoCAD: `F:\Projects\CAD\AutoCAD`
  - Autodesk Inventor: `F:\Projects\CAD\Inventor`

## Cấu trúc Skill
- `SKILL.md`: Quy chuẩn và quy trình thực thi chính.
- `docs/work-status.md`: Hồ sơ trạng thái phiên làm việc.
- `CHANGELOG.md`: Lịch sử phiên bản.
