# Hệ thống quản lý bất động sản

Nền tảng quản lý dự án, căn hộ, tin bán/cho thuê, KYC, hợp đồng ký online, hoa hồng và hóa đơn cho một đơn vị kinh doanh bất động sản.

## Chạy nhanh

Yêu cầu: Docker Desktop (Compose v2), `make`, `python3` (chỉ để sinh secret).

```bash
# 1. Tạo file cấu hình rồi đặt JWT_SECRET_KEY
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # dán vào JWT_SECRET_KEY trong .env

# 2. Dựng stack, tạo schema, nạp dữ liệu mẫu
make build
make up
make migrate
make seed
```


### Tài khoản demo

Mật khẩu chung: **`Demo@12345678`**

| Email | Vai trò |
| --- | --- |
| `admin@demo.com` | Admin — toàn quyền, kể cả `job.manage`, `kyc.read_sensitive` |
| `agent@demo.com` | Môi giới — quản lý tin của mình, xem khách trong giao dịch phụ trách |
| `customer@demo.com` | Khách hàng |



## Kiến trúc

### C4 Level 1 — System Context

```mermaid
flowchart LR
    guest(["👤 Khách truy cập"])
    customer(["👤 Khách hàng"])
    agent(["👤 Môi giới"])
    admin(["👤 Admin"])

    subgraph boundary["REM System Boundary"]
        rem["Quản lý bất động sản (REM)<br/><i>[Software System]</i><br/>Dự án, căn hộ, tin đăng, KYC, hợp đồng, chứng từ, báo cáo"]
    end

    kyc["Nhà cung cấp KYC<br/><i>[External System — chưa chọn]</i>"]
    mail["Email SMTP<br/><i>[External System — MailHog khi dev]</i>"]
    store[("Kho tệp riêng tư<br/><i>[External System — volume hoặc S3-compatible]</i>")]

    guest -- "tìm và xem tin công khai; đăng ký" --> rem
    customer -- "KYC, ký hợp đồng, tải PDF, xem hóa đơn" --> rem
    agent -- "tin phụ trách, lập hợp đồng, hoa hồng của mình" --> rem
    admin -- "danh mục, duyệt tin, chứng từ, hoa hồng, audit" --> rem
    rem -- "gửi yêu cầu xác thực danh tính qua adapter" --> kyc
    kyc -- "callback kết quả đã xác thực chữ ký" --> rem
    rem -- "email reset, OTP ký, mời ký, hoàn tất" --> mail
    rem -- "ghi/đọc hợp đồng PDF và tệp xuất" --> store

    style rem fill:#1168bd,color:#fff
    style kyc fill:#999,color:#fff
    style mail fill:#999,color:#fff
    style store fill:#999,color:#fff
```

### Sequence diagram — tìm kiếm tin công khai

```mermaid
sequenceDiagram
    autonumber
    actor G as Khách truy cập
    participant W as React
    participant A as FastAPI
    participant R as Redis
    participant D as PostgreSQL

    G->>W: Chọn địa bàn, loại giao dịch, khoảng giá
    W->>A: GET /api/v1/public/listings?filter&page&sort
    A->>A: Validate bộ lọc, chặn trộn giá bán và giá thuê
    A->>R: Đọc cache danh mục địa bàn/dự án
    R-->>A: Danh mục (TTL ≤ 60 giây)
    A->>D: SELECT tin approved · căn available · dự án active + phân trang
    D-->>A: items + total
    A-->>W: 200 {items, page, page_size, total}
    W-->>G: Danh sách hoặc trạng thái rỗng
```

### Class diagrams

Các sơ đồ dưới đây rút gọn các lớp miền và quan hệ canonical được mô tả trong
[ARCHITECTURE](docs/ARCHITECTURE.md) và [ERD](docs/ERD.md); chúng không thay thế
ERD đầy đủ cùng các ràng buộc cơ sở dữ liệu.

#### Tài khoản, dự án và tin đăng

```mermaid
classDiagram
    class User {
        +UUID id
        +string email
        +string full_name
        +string status
        +int auth_version
    }
    class Customer {
        +UUID id
        +string customer_code
        +string address
    }
    class Agent {
        +UUID id
        +string agent_code
        +string status
    }
    class Project {
        +UUID id
        +string code
        +string name
        +string province_code
        +string ward_code
        +string status
    }
    class Property {
        +UUID id
        +string unit_code
        +decimal area_m2
        +int bedrooms
        +string status
        +int row_version
    }
    class Listing {
        +UUID id
        +string listing_type
        +decimal asking_price
        +string price_unit
        +string title
        +string status
        +int row_version
    }

    User "1" --> "0..1" Customer : has profile
    User "1" --> "0..1" Agent : has profile
    User "0..1" --> "0..*" Listing : reviews
    Project "1" *-- "0..*" Property : contains
    Property "1" --> "0..*" Listing : advertised in
    Agent "1" --> "0..*" Listing : manages
```

Chi tiết C4 Level 2/3, các runtime scenario khác và quyết định kiến trúc nằm tại
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Luồng End-to-End (Đăng tin -> Ký hợp đồng)
```mermaid
flowchart TD
    A["Admin tạo dự án và căn available"] --> B["Môi giới tạo draft và gửi pending"]
    B --> C{"Admin duyệt?"}
    C -->|"Không"| D["Rejected kèm lý do"]
    D --> B
    C -->|"Có"| E["Approved · Khách tìm và xem tin"]
    E --> F["Admin/môi giới lập hợp đồng draft"]
    F --> G{"KYC mới nhất đạt?"}
    G -->|"Không"| H["Khách thực hiện KYC · UC-10"]
    H --> G
    G -->|"Có"| I{"Gửi ký và giữ căn thành công?"}
    I -->|"Xung đột"| J["Giữ nguyên draft · Chọn giao dịch phù hợp khác"]
    I -->|"Có"| K["Pending signatures · Căn reserved"]
    K --> L["Hai bên xem nội dung và ký OTP"]
    L --> M{"Đủ chữ ký?"}
    M -->|"Chưa đủ"| L
    M -->|"Đủ"| N["Signed · Căn sold/rented · Tin closed"]
    K -->|"Hủy trước hoàn tất"| X["Cancelled · Revoke OTP · Căn available"]
    N --> O["Một khoản hoa hồng pending"]
    N --> P["Worker tạo PDF riêng tư"]
    P --> Q{"Tạo PDF thành công?"}
    Q -->|"Không"| R["Job failed · Cho thử lại theo quyền"]
    R --> P
    Q -->|"Có"| S["Gửi email hoàn tất · Các bên tải PDF"]
```



## Cấu trúc thư mục

```text
.
├── docker-compose.yml          # postgres, redis, api, worker, frontend, nginx, mailhog
├── Makefile
├── .env.example                # cấu hình compose (cổng, JWT_SECRET_KEY)
├── infrastructure/nginx/       # reverse proxy
├── docs/                       # PRD, SPEC, ERD, USE_CASES, ARCHITECTURE, PLAN
└── src/
    ├── frontend/               # React 19 + Vite (chưa triển khai)
    └── backend/
        ├── app/
        │   ├── main.py         # app FastAPI, router, /health, /ready
        │   ├── core/           # config, bảo mật JWT, quyền, lỗi, cache, logging
        │   ├── common/         # micro ORM (db.py), enum, phân trang, helper tệp
        │   ├── middleware/     # request id, rate limit, audit, error handler
        │   ├── modules/        # mỗi domain: router, service, repository, schemas, permissions
        │   ├── integrations/   # adapter SMTP, kho tệp (KYC, PDF: chưa làm)
        │   └── workers/        # Celery app, dispatcher outbox, runner, email task
        ├── migrations/         # Alembic
        ├── scripts/seed.py
        └── tests/{unit,integration}/
```


## Tài liệu

| Tài liệu | Nội dung |
| --- | --- |
| [PRD](docs/PRD.md) | Phạm vi sản phẩm, vai trò, yêu cầu chức năng và phi chức năng |
| [SPEC](docs/SPEC.md) | Hành vi API, validation, transaction, mã lỗi, bộ test nghiệm thu T-01…T-13 |
| [ERD](docs/ERD.md) | 24 bảng, ràng buộc, chỉ mục |
| [USE_CASES](docs/USE_CASES.md) | Luồng sử dụng UC-01…UC-22 |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Kiến trúc C4, ADR, rủi ro |
| [PLAN](docs/PLAN.md) | Kế hoạch theo phase, gate và nhật ký thực hiện |
