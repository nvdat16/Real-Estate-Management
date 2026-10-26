# AGENTS.md — Bds.Website

Hệ thống quản lý bất động sản: dự án, căn hộ, tin bán/cho thuê có duyệt, KYC, ký hợp đồng online, hoa hồng môi giới, hóa đơn, báo cáo. Backend ASP.NET Core `net10.0`, Clean Architecture theo module, CQRS với MediatR và FluentValidation, PostgreSQL, Redis, Mailpit. Chưa có frontend.

Đọc thêm trước khi làm việc: [docs/BRD.md](docs/BRD.md), [.planning/PROJECT_BRIEF.md](.planning/PROJECT_BRIEF.md) và [.planning/WORKING_RULES.md](.planning/WORKING_RULES.md).

## Cấu trúc

```
backend/
├── Bds.Website.sln
├── BuildingBlocks/        Bds.BuildingBlocks.{Domain,Application,Infrastructure}
├── Modules/
│   ├── Identity/          Bds.{Domain,Model.Dto,Infrastructure,Service,Presentation}.Identity     schema identity
│   ├── RealEstate/        Bds.{Domain,Model.Dto,Infrastructure,Service,Presentation}.RealEstate   schema realestate
│   └── Storage/           Bds.{Model.Dto,Service,Presentation}.Storage                            không có DB
├── Host/Bds.Host.Api/     chỉ phục vụ API
├── Migrations/Bds.Migration/   nơi duy nhất apply migration và seed
└── Tests/                 Bds.Tests.{Architecture,Unit,Integration}
```

Khung một module (RealEstate làm mẫu):

```
Bds.Domain.RealEstate/            Entities/, Enums/
Bds.Model.Dto.RealEstate/         Requests/, Responses/, Constants/
Bds.Infrastructure.RealEstate/    Contexts/{RealEstateContext.cs, RealEstateConnectionFactory.cs, Configurations/},
                                  Interfaces/, Repositories/, ReadModels/, Results/, Seed/, Migrations/
                                  (Identity dùng EF nên có thêm UnitOfWorks/)
Bds.Service.RealEstate/           Extensions/, Helpers/, Interfaces/, Services/,
                                  UseCases/{Feature}/{Commands/Handlers, Queries/Handlers, Validators}
Bds.Presentation.RealEstate/      Controllers/v1/, Extensions/
```

Feature hiện có:

- Identity: `Auth`, `User`, `Role`.
- RealEstate: `Location`, `Project`, `Property`, `Listing`, `Customer`, `Agent`, `Kyc`, `Contract`, `Commission`, `Invoice`, `Report`.

## Quy tắc bắt buộc

- Tiền tố mọi project và namespace là `Bds.`.
- `BuildingBlocks` không tham chiếu `Modules`. Các module không tham chiếu trực tiếp lẫn nhau. Host chỉ tham chiếu `Bds.Presentation.*` và `BuildingBlocks`.
- Tham chiếu giữa các tầng trong module: Domain → BuildingBlocks.Domain; Dto → không có; Infrastructure → Domain; Service → Infrastructure, Dto; Presentation → Service, Dto. `Tests/Bds.Tests.Architecture` kiểm tra các quy tắc này.
- `IdentityContext` và `RealEstateContext` dùng schema `identity` và `realestate` trong database `bds_website`. Bảng lịch sử migration nằm trong schema của từng module.
- Customer và Agent (RealEstate) chỉ lưu `UserId` của Identity dạng giá trị, không tạo khóa ngoại sang schema `identity`.
- Chỉ `Bds.Migration` được gọi `Database.Migrate*`, chạy seed và tạo schema cho thư viện ngoài (ví dụ Hangfire).
- Migration phải sinh bằng `dotnet ef`, không viết tay. Dùng bản ghim trong `backend/.config/dotnet-tools.json`:
  ```bash
  cd backend
  dotnet tool restore
  dotnet ef migrations add <Name> \
    --project Modules/RealEstate/Bds.Infrastructure.RealEstate \
    --startup-project Migrations/Bds.Migration \
    --context RealEstateContext --output-dir Migrations
  ```
- RealEstate truy cập dữ liệu bằng Dapper, không dùng EF lúc chạy và không có UnitOfWork:
  - đọc qua function `realestate.fn_*` (`SELECT * FROM realestate.fn_...(...)`);
  - ghi qua procedure `realestate.sp_*` (`CommandType.StoredProcedure`), trả mã kết quả qua `INOUT p_result`, repository đổi sang enum trong `Results/`;
  - kiểm tra cần chạy cùng transaction với thao tác ghi (trùng mã, tồn tại, quan hệ dữ liệu) đặt trong procedure;
  - `RealEstateContext` và Configurations chỉ dùng để sinh migration tạo bảng và chạy seed;
  - function/procedure tạo bằng `migrationBuilder.Sql(...)` trong migration rỗng sinh bằng `dotnet ef migrations add`. Muốn sửa thì thêm migration mới với `CREATE OR REPLACE`, không sửa migration đã apply.
- Không dùng FileHeader. Không thêm comment mô tả trên declaration. Comment giải thích chỉ viết bằng tiếng Anh.
- Thông báo hiển thị cho người dùng viết bằng tiếng Việt.
- Không đưa `bin/`, `obj/`, `node_modules/`, `dist/` vào source.
- Không chạy `git add`, `git commit`, `git push` hoặc lệnh hoàn tác working tree khi chưa được yêu cầu.

## Quy ước đặt tên

- Command: `CreateListingCommand.cs`, `UpdateListingCommand.cs`, `DeleteListingCommand.cs`. Query: `GetListingByIdQuery.cs`, `SearchListingsQuery.cs`.
- Handler trong `Commands/Handlers` hoặc `Queries/Handlers`; Validator trong `Validators`.
- Service nghiệp vụ: `I{Feature}Service.cs` trong `Bds.Service.{Module}/Interfaces/`, `{Feature}Service.cs` trong `Bds.Service.{Module}/Services/`, một service cho mỗi feature (`IListingService`, `ListingService`). Handler gọi service, service gọi repository và UnitOfWork (RealEstate không có UnitOfWork; xem luồng trong `.planning/WORKING_RULES.md`).
- Mapping và business rule dùng chung đặt ở gốc `UseCases/{Feature}`, ví dụ `ListingMapping.cs`, `ListingRules.cs`.
- DTO: `{Entity}Request.cs`, `{Entity}Response.cs`.
- Repository: `I{Entity}Repository.cs` trong `Interfaces/`, `{Entity}Repository.cs` trong `Repositories/`.
- Giữ tên feature hiện có; không tự đổi tên để đồng nhất.

## Kiểm tra bắt buộc trước khi báo hoàn thành

```bash
cd backend
dotnet build -warnaserror
dotnet test
cd .. && docker compose --env-file .env.example config --quiet
```

Báo rõ từng lệnh, kết quả và phần chưa kiểm chứng.
