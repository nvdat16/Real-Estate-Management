# Kiến trúc hệ thống quản lý bất động sản

Nguồn: [yeu_cau.pdf](yeu_cau.pdf), trang 1 (yêu cầu chung và bài toán Real Estate), trang 2 (tiêu chí chất lượng).

Đây là kiến trúc **đề xuất**, dựa trên yêu cầu và stack đã khai báo trong repository; không phải xác nhận các chức năng đã được triển khai. Chọn **modular monolith**: một ứng dụng FastAPI chia module nghiệp vụ, dùng chung PostgreSQL; Celery chạy riêng để xử lý tác vụ lâu.

## 1. Architecture diagram

```mermaid
flowchart TB
    subgraph USERS["Người sử dụng"]
        ADMIN["Admin / Quản trị viên"]
        AGENT["Môi giới"]
        CUSTOMER["Khách hàng"]
    end

    subgraph CLIENT["Tầng giao diện"]
        WEB["React Web App<br/>Danh sách và tìm kiếm căn hộ · Đăng tin<br/>Hợp đồng · Hoa hồng · Dashboard"]
    end

    subgraph SERVER["Hạ tầng ứng dụng · Docker Compose"]
        PROXY["Nginx · Reverse proxy<br/>HTTPS · Phục vụ React · Chuyển tiếp /api"]

        subgraph API["FastAPI · Modular monolith"]
            ENTRY["REST API / OpenAPI<br/>Validation · CORS · Rate limit<br/>JWT và phân quyền theo hành động"]
            AUTH["Tài khoản và phân quyền<br/>Đăng ký / đăng nhập · Đặt lại mật khẩu<br/>RBAC · 2FA tùy chọn"]
            PROPERTY["Dự án và căn hộ<br/>CRUD · Tìm kiếm vị trí / giá<br/>Lọc · Sắp xếp · Phân trang"]
            LISTING["Tin bán / cho thuê<br/>Đăng tin · Duyệt tin"]
            CRM["Khách hàng và môi giới<br/>Hồ sơ · Trạng thái KYC"]
            CONTRACT["Hợp đồng và hóa đơn<br/>Ký online · Phiên bản hợp đồng<br/>Lưu tham chiếu PDF và bằng chứng ký"]
            COMMISSION["Hoa hồng môi giới<br/>Tính và theo dõi hoa hồng"]
            REPORT["Báo cáo và thông báo<br/>Số tin · Số hợp đồng<br/>Nhập / xuất Excel, CSV · Xuất PDF"]
            CORE["Hạ tầng dùng chung<br/>Repository / SQLAlchemy · Giao dịch DB<br/>Audit log · Soft-delete · Versioning<br/>Cache · Hàng đợi · Adapter tích hợp"]
            ENTRY --> AUTH & PROPERTY & LISTING & CRM & CONTRACT & COMMISSION & REPORT
            AUTH & PROPERTY & LISTING & CRM & CONTRACT & COMMISSION & REPORT --> CORE
        end

        DB[("PostgreSQL<br/>Tài khoản · Dữ liệu nghiệp vụ<br/>Audit · Phiên bản · Trạng thái job")]
        REDIS[("Redis<br/>Cache danh mục / báo cáo<br/>Rate limit · Celery broker")]
        WORKER["Celery Worker<br/>Gửi email · Tạo hợp đồng PDF<br/>Nhập / xuất dữ liệu và báo cáo lớn"]
        STORE[("Kho tệp riêng tư<br/>Hợp đồng PDF · Báo cáo xuất<br/>Volume hoặc S3-compatible, đề xuất")]
        OBS["Vận hành<br/>Structured logging<br/>Health check /health"]
    end

    subgraph EXT["Dịch vụ tích hợp"]
        KYC["Nhà cung cấp KYC<br/>Chưa chọn nhà cung cấp"]
        MAIL["Email SMTP<br/>MailHog khi phát triển<br/>SMTP thực khi triển khai"]
    end

    ADMIN & AGENT & CUSTOMER --> WEB
    WEB -->|"HTTPS"| PROXY
    PROXY -->|"/api · REST / JSON"| ENTRY
    CORE -->|"Đọc / ghi"| DB
    CORE -->|"Cache / enqueue job"| REDIS
    REDIS -->|"Job"| WORKER
    WORKER -->|"Dữ liệu / kết quả job"| DB
    CORE -->|"Truy cập tệp có phân quyền"| STORE
    WORKER -->|"Lưu PDF / tệp xuất"| STORE
    CRM -->|"Qua adapter · HTTPS"| KYC
    WORKER -->|"Gửi email"| MAIL
    ENTRY -.-> OBS
    WORKER -.-> OBS

    classDef person fill:#e0e7ff,stroke:#4f46e5,color:#1e1b4b
    classDef app fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef external fill:#fff7ed,stroke:#ea580c,color:#7c2d12
    class ADMIN,AGENT,CUSTOMER person
    class WEB,PROXY,ENTRY,AUTH,PROPERTY,LISTING,CRM,CONTRACT,COMMISSION,REPORT,CORE,WORKER,OBS app
    class DB,REDIS,STORE data
    class KYC,MAIL external
```

Các mũi tên có nhãn biểu thị lời gọi hoặc hướng xử lý chính; phản hồi được lược bỏ. Các module bên trong FastAPI là ranh giới mã nguồn, không phải các microservice độc lập. Redis dùng chung hạ tầng nhưng cần tách namespace và chính sách lưu cache với hàng đợi để tránh mất job do eviction.

## 2. Luồng đăng tin → ký hợp đồng

```mermaid
sequenceDiagram
    actor MG as Môi giới
    actor AD as Admin
    actor KH as Khách hàng
    participant UI as React
    participant API as FastAPI
    participant DB as PostgreSQL
    participant KYC as Dịch vụ KYC
    participant Q as Redis / Celery
    participant W as Celery Worker
    participant F as Kho tệp
    participant M as Email SMTP

    MG->>UI: Tạo tin bán / cho thuê
    UI->>API: Gửi tin
    API->>DB: Lưu tin chờ duyệt và audit log
    AD->>UI: Duyệt tin
    UI->>API: Yêu cầu duyệt
    API->>DB: Kiểm tra quyền, cập nhật trạng thái, ghi audit
    KH->>UI: Tìm căn hộ theo vị trí / giá
    UI->>API: Tìm kiếm và phân trang
    API->>DB: Truy vấn tin đã duyệt
    DB-->>API: Danh sách căn hộ
    API-->>UI: Kết quả tìm kiếm
    MG->>UI: Lập hợp đồng cho khách hàng
    UI->>API: Tạo bản nháp hợp đồng
    API->>DB: Lưu nội dung và phiên bản
    KH->>UI: Gửi thông tin xác thực danh tính
    UI->>API: Yêu cầu KYC
    API->>KYC: Xác minh qua adapter
    KYC-->>API: Kết quả xác minh
    API->>DB: Lưu trạng thái KYC
    alt KYC đạt
        KH->>UI: Xác nhận ký phiên bản hợp đồng
        UI->>API: Gửi xác nhận ký
        API->>DB: Kiểm tra quyền, KYC, phiên bản và các bên ký
        Note over API,DB: Chỉ hoàn tất khi đủ bên ký theo quy trình đã chọn
        API->>DB: Giao dịch: lưu bằng chứng ký, trạng thái và audit
        API->>Q: Đưa tác vụ tạo PDF / email vào hàng đợi
        Q->>W: Nhận tác vụ
        W->>DB: Đọc phiên bản hợp đồng đã ký
        W->>F: Lưu hợp đồng PDF
        W->>DB: Lưu tham chiếu PDF và trạng thái xử lý
        W->>M: Gửi thông báo hoàn tất
        KH->>UI: Xem / tải hợp đồng
        UI->>API: Yêu cầu tải PDF
        API->>F: Đọc tệp sau khi kiểm tra quyền
        API-->>UI: Trả hợp đồng PDF
    else KYC không đạt hoặc đang chờ
        API-->>UI: Chưa cho phép ký, hiển thị trạng thái
    end
```

Luồng trên đề xuất KYC trước khi ký. PDF không quy định phương thức ký (xác nhận điện tử, OTP hay nhà cung cấp chữ ký số), các bên bắt buộc ký, hoặc thời điểm ghi nhận hoa hồng; các quy tắc này cần chốt khi đặc tả chi tiết. Tạo PDF là bước xuất tài liệu, không thay thế việc xác nhận ký và lưu bằng chứng ký. Nếu dùng nhà cung cấp chữ ký điện tử, bổ sung adapter vào module hợp đồng.

## 3. Đối chiếu yêu cầu với thành phần

| Yêu cầu trong PDF | Thành phần xử lý |
| --- | --- |
| Đăng ký, đăng nhập, JWT/OAuth2, đặt lại mật khẩu; 2FA tùy chọn | Tài khoản, RBAC, worker gửi email; đề xuất JWT bearer theo luồng OAuth2 phù hợp |
| Ít nhất 3 vai trò; phân quyền màn hình và hành động | React kiểm soát hiển thị; FastAPI bắt buộc kiểm tra quyền và phạm vi dữ liệu |
| CRUD dự án, căn hộ; tìm theo vị trí, giá | Module dự án / căn hộ, PostgreSQL với chỉ mục phù hợp |
| Đăng tin bán / cho thuê, duyệt tin | Module tin đăng; đề xuất Admin duyệt tin |
| Ký hợp đồng online, lưu PDF, KYC | Module hợp đồng, hồ sơ KYC, adapter KYC, worker, kho tệp riêng tư |
| Hoa hồng môi giới | Module hoa hồng, liên kết môi giới và hợp đồng |
| Báo cáo số tin, số hợp đồng; dashboard | Module báo cáo, React, Redis cache |
| Nhập / xuất Excel, CSV; xuất PDF | API nhận yêu cầu, worker xử lý tác vụ lớn, kho tệp lưu kết quả |
| Audit log, soft-delete, versioning cơ bản | Hạ tầng dùng chung và PostgreSQL; audit lưu người thực hiện, thời điểm, hành động |
| Email và/hoặc in-app, hàng đợi tác vụ | Celery + Redis + SMTP; thông báo in-app có thể lưu trong PostgreSQL |
| Dữ liệu chính | `projects`, `properties`, `listings`, `contracts`, `customers`, `agents`, `invoices`; bổ sung bảng tài khoản, quyền, hoa hồng, KYC, audit, phiên bản và job |

PDF nêu vai trò chung Admin/Manager/User nhưng phần Real Estate chỉ định Admin/Môi giới/Khách hàng. Sơ đồ dùng ba vai trò nghiệp vụ này; quyền duyệt tin mặc định đề xuất giao cho Admin. Nếu cần Manager riêng, có thể bổ sung qua RBAC.

## 4. Bảo mật và vận hành

- Chống SQLi bằng truy vấn tham số hóa; kiểm tra và escape nội dung hiển thị để hạn chế XSS; CORS giới hạn origin; rate limit ở API. Nếu dùng cookie xác thực, bổ sung biện pháp CSRF. Phân quyền cả hành động lẫn từng bản ghi, đặc biệt hợp đồng và dữ liệu KYC.
- Kho tệp không công khai; tải qua API đã kiểm tra quyền hoặc URL ký có thời hạn. Chỉ lưu dữ liệu KYC cần thiết, không ghi giấy tờ định danh hoặc token vào log.
- Hợp đồng dùng kiểm tra phiên bản để tránh ghi đè đồng thời. Job cần retry, xử lý idempotent và lưu trạng thái bền vững; trạng thái hợp đồng đã ký phải được đối soát để khôi phục tác vụ nếu enqueue thất bại.
- Docker Compose đề xuất gồm Nginx/React, API, PostgreSQL, Redis, Celery worker, MailHog cho phát triển và volume lưu tệp. Tên dịch vụ trong sơ đồ không khẳng định cấu hình Compose hiện tại đã hoàn chỉnh.
- CI/CD: build → unit test service và integration test API (coverage tối thiểu 30–40% theo tài liệu) → đóng gói image → deploy; migration bằng Alembic và seed ít nhất 2.000 bản ghi mẫu.
- Structured logging, `/health`, OpenAPI/Swagger và Postman collection phục vụ kiểm thử, bàn giao; không ghi bí mật vào log. Chuẩn bị mẫu hợp đồng, dashboard và video demo theo PDF.

## 5. Cơ sở lựa chọn công nghệ

React, FastAPI, PostgreSQL, Redis, Celery và Docker đã xuất hiện trong README, dependency manifest hoặc Docker Compose của repository. Nginx có thư mục cấu hình. Kho tệp riêng tư, adapter KYC, phương thức ký, SMTP khi triển khai và các chính sách bảo mật là phần thiết kế đề xuất để đáp ứng yêu cầu; tài liệu không chỉ định nhà cung cấp.
