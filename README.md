# Bds.Website

Hệ thống quản lý bất động sản: ASP.NET Core (`net10.0`), PostgreSQL, Redis, Clean Architecture theo module, CQRS với MediatR..

## Yêu cầu

- .NET SDK 10.0
- Docker Desktop (Compose v2)

## Chạy bằng Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Thứ tự khởi động: `postgres` → `migration` (apply migration rồi thoát) → `api`; `api` chờ thêm `redis` và `mailpit`.

| Dịch vụ | Địa chỉ |
| --- | --- |
| API | http://localhost:8080, kiểm tra sức khỏe `GET /health` |
| PostgreSQL | `localhost:5432`, database `bds_website`, user `bds`, mật khẩu `bds_dev_password` |
| Redis | `localhost:6379` |
| Mailpit (xem email đã gửi) | http://localhost:8025, SMTP `localhost:1025` |

## Chạy backend trên máy

```bash
docker compose up -d postgres redis mailpit
cd backend
dotnet tool restore
dotnet run --project Migrations/Bds.Migration
dotnet run --project Host/Bds.Host.Api      # http://localhost:5080, OpenAPI tại /openapi/v1.json
```

Chuỗi kết nối mặc định khi chạy local nằm trong `appsettings.Development.json` của Host và `appsettings.json` của Migration; giá trị này chỉ dùng cho môi trường dev.

## Kiểm tra

```bash
cd backend
dotnet build -warnaserror
dotnet test
```

Quy tắc kiến trúc và quy ước code: xem [AGENTS.md](AGENTS.md).
