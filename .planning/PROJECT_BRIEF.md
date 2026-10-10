# Project Brief — Bds.Website

Nguồn yêu cầu đầy đủ: [docs/BRD.md](../docs/BRD.md) (dựa trên [docs/yeu_cau.pdf](../docs/yeu_cau.pdf)). File này chỉ tóm tắt các quyết định ảnh hưởng tới thiết kế.

## Mục tiêu

Quản lý dự án, căn hộ, tin bán/cho thuê có duyệt; khách tìm căn theo vị trí, giá; KYC và ký hợp đồng online; lưu hợp đồng PDF; hoa hồng môi giới; hóa đơn nội bộ; báo cáo số tin, số hợp đồng và dashboard.

## Vai trò

Admin, Môi giới, Khách hàng (cùng khách vãng lai không đăng nhập). Không có vai trò Manager.

## Module

| Module | Schema | Feature | Dữ liệu dự kiến |
| --- | --- | --- | --- |
| Identity | `identity` | `Auth`, `User`, `Role` | User, Role, Permission, PasswordResetToken |
| RealEstate | `realestate` | `Location`, `Project`, `Property`, `Listing`, `Customer`, `Agent`, `Kyc`, `Contract`, `Commission`, `Invoice`, `Report` | Province, District, Project, Property, Listing, Customer, Agent, KycVerification, Contract, ContractSignature, Commission, Invoice |
| Storage | không có | ảnh tin, PDF hợp đồng/hóa đơn, tệp xuất | không có |

- Mọi nghiệp vụ bất động sản nằm chung module RealEstate vì khi ký đủ, hợp đồng, căn, tin và hoa hồng phải đổi trong cùng một transaction (BRD RULE-09), và khi gửi ký phải kiểm tra KYC (RULE-05).
- Identity chỉ giữ tài khoản, vai trò, quyền. Customer và Agent lưu `UserId` dạng giá trị.
- Admin ký đại diện đơn vị (RULE-04). Ký online bằng tài khoản kèm OTP email, không phải chữ ký số chứng thực.

## Quyết định đã chốt (BRD mục 12)

| # | Quyết định |
| --- | --- |
| Q-01 | Không có vai trò Manager |
| Q-02 | Admin ký đại diện bên bán/cho thuê |
| Q-03 | Hoa hồng = round(giá trị hợp đồng × tỷ lệ % / 100) |
| Q-04 | Hợp đồng thuê làm đơn giản: ngày bắt đầu, số tháng, giá thuê tháng; giá trị = giá thuê tháng × số tháng; Admin chuyển căn về Còn trống thủ công khi hết hạn |
| Q-05 | Hóa đơn là chứng từ nội bộ, không phải hóa đơn điện tử |
| Q-06 | Chỉ thông báo qua email, không làm in-app |
| Q-07 | Hàng đợi tác vụ dùng Hangfire trên PostgreSQL, retry tối đa 3 lần, dashboard chỉ Admin xem. Chưa thêm vào code; thêm khi làm phần email và PDF |

## Ngoài phạm vi

Thanh toán online, hóa đơn điện tử, chữ ký số chứng thực, thông báo in-app, gia hạn/chấm dứt sớm hợp đồng thuê, ứng dụng di động, bản đồ/GIS, chat.

## Hạ tầng

- Docker Compose: `postgres` (17), `redis` (7), `mailpit` (bắt email khi dev, thay MailHog vì có image arm64), `migration` (chạy một lần), `api`.
- Thứ tự khởi động: postgres → migration → api; api chờ thêm redis và mailpit.
- Database `bds_website`, schema `identity` và `realestate`.
