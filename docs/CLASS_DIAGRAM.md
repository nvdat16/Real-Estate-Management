# Class Diagram — Bds.Website

Bản thiết kế dựa trên [BRD.md](BRD.md) v0.3. Code hiện chưa có entity nào; các diagram dưới đây là đề xuất để thống nhất trước khi viết Domain, Infrastructure và Service.

Quy ước chung:

- Mọi entity kế thừa `BaseEntity` (`Id` kiểu `Guid` v7, `CreatedAt`, `UpdatedAt`).
- Tiền tính bằng VND, kiểu `long`. Tỷ lệ % kiểu `decimal` (0–100).
- Các `*FileKey` là khóa tệp trong module Storage, không phải khóa ngoại.
- Phương thức trên entity là quy tắc gắn với dữ liệu của chính entity; quy tắc cần dữ liệu khác nằm trong `{Feature}Rules` hoặc service.

## 1. BuildingBlocks

```mermaid
classDiagram
    class BaseEntity {
        <<abstract>>
        +Guid Id
        +DateTime CreatedAt
        +DateTime? UpdatedAt
    }
    class ISoftDelete {
        <<interface>>
        +bool IsDeleted
        +DateTime? DeletedAt
        +Guid? DeletedBy
    }
    class IVersioned {
        <<interface>>
        +int Version
    }
    class AuditLog {
        +Guid? UserId
        +string Action
        +string EntityName
        +Guid EntityId
        +string? Changes
        +DateTime OccurredAt
    }
    BaseEntity <|-- AuditLog
```

| Thành phần | Mục đích | Áp dụng cho |
| --- | --- | --- |
| `ISoftDelete` | BR-28 soft-delete, lọc mặc định bằng global query filter | Project, Property, Listing, Customer, Agent |
| `IVersioned` | BR-29 versioning, cấu hình làm concurrency token | Contract, Commission, Invoice |
| `AuditLog` | BR-27, ghi tự động bằng SaveChanges interceptor | Mỗi DbContext có bảng `audit_logs` trong schema của mình, vì module không tham chiếu lẫn nhau |

`ISoftDelete`, `IVersioned`, `AuditLog` hiện **chưa có** trong BuildingBlocks.

## 2. Module Identity (schema `identity`)

```mermaid
classDiagram
    direction LR
    class User {
        +string Email
        +string PasswordHash
        +string FullName
        +string? PhoneNumber
        +Guid RoleId
        +bool IsLocked
        +DateTime? LastLoginAt
        +ChangeRole(Role role) void
        +Lock() void
        +Unlock() void
        +ChangePassword(string passwordHash) void
    }
    class Role {
        +string Name
        +string? Description
    }
    class Permission {
        +string Code
        +string Name
        +string Group
    }
    class RolePermission {
        +Guid RoleId
        +Guid PermissionId
    }
    class PasswordResetToken {
        +Guid UserId
        +string TokenHash
        +DateTime ExpiresAt
        +DateTime? UsedAt
        +IsValid(DateTime now) bool
        +MarkUsed(DateTime now) void
    }

    Role "1" --> "0..*" User
    Role "1" --> "0..*" RolePermission
    Permission "1" --> "0..*" RolePermission
    User "1" --> "0..*" PasswordResetToken
```

- Ba vai trò seed sẵn: `Admin`, `Agent`, `Customer` (Q-01). Mỗi tài khoản có đúng một vai trò (`User.RoleId`). Người tự đăng ký chỉ nhận `Customer` (BR-20).
- `Permission.Code` dạng `listing.approve`, `contract.sign`… dùng cho RBAC theo hành động (BR-23).
- `PasswordResetToken` chỉ lưu hash, dùng một lần (BR-21).

## 3. Module RealEstate (schema `realestate`)

### 3.1. Danh mục, tin đăng, khách hàng, môi giới

```mermaid
classDiagram
    direction LR
    class Province {
        +string Code
        +string Name
    }
    class District {
        +Guid ProvinceId
        +string Code
        +string Name
    }
    class Project {
        +string Code
        +string Name
        +Guid ProvinceId
        +Guid DistrictId
        +string AddressLine
        +string Developer
        +ProjectStatus Status
    }
    class Property {
        +Guid ProjectId
        +string Code
        +decimal Area
        +int Floor
        +string? Position
        +int Bedrooms
        +Direction Direction
        +PropertyStatus Status
        +Reserve() void
        +Release() void
        +MarkSold() void
        +MarkRented() void
        +MarkAvailableAfterLease() void
    }
    class Listing {
        +Guid PropertyId
        +Guid AgentId
        +ListingType Type
        +string Title
        +string Description
        +long Price
        +ListingStatus Status
        +DateTime? SubmittedAt
        +Guid? ReviewedBy
        +DateTime? ReviewedAt
        +string? RejectionReason
        +Update(title, description, price) void
        +Submit(DateTime now) void
        +Approve(Guid reviewerId, DateTime now) void
        +Reject(Guid reviewerId, string reason, DateTime now) void
        +Close() void
    }
    class ListingImage {
        +Guid ListingId
        +string FileKey
        +int SortOrder
    }
    class Customer {
        +Guid UserId
        +string FullName
        +string Email
        +string? PhoneNumber
    }
    class Agent {
        +Guid UserId
        +string FullName
        +string Email
        +string? PhoneNumber
        +bool IsActive
    }
    class KycVerification {
        +Guid CustomerId
        +string FullName
        +string IdNumber
        +DateOnly DateOfBirth
        +string IdFrontFileKey
        +string IdBackFileKey
        +string Provider
        +string? ProviderReference
        +KycStatus Status
        +string? FailureReason
        +DateTime SubmittedAt
        +DateTime? CompletedAt
        +MarkPassed(DateTime now) void
        +MarkFailed(string reason, DateTime now) void
        +MarkError(string reason, DateTime now) void
    }

    Province "1" --> "0..*" District
    Province "1" --> "0..*" Project
    District "1" --> "0..*" Project
    Project "1" --> "0..*" Property
    Property "1" --> "0..*" Listing
    Agent "1" --> "0..*" Listing
    Listing "1" *-- "0..*" ListingImage
    Customer "1" --> "0..*" KycVerification
```

### 3.2. Hợp đồng, hoa hồng, hóa đơn

```mermaid
classDiagram
    direction LR
    class Contract {
        +string Code
        +ContractType Type
        +Guid PropertyId
        +Guid ListingId
        +Guid CustomerId
        +Guid AgentId
        +Guid CreatedByUserId
        +long Value
        +string Terms
        +decimal CommissionRate
        +long? CommissionAmount
        +DateOnly? LeaseStartDate
        +int? LeaseMonths
        +long? MonthlyRent
        +ContractStatus Status
        +string? ContentHash
        +DateTime? SentForSigningAt
        +DateTime? SignedAt
        +string? CancelReason
        +string? PdfFileKey
        +string? PdfHash
        +int Version
        +SendForSigning(string contentHash, DateTime now) void
        +AddSignature(ContractSignature signature) void
        +IsFullySigned() bool
        +Cancel(string reason, DateTime now) void
        +AttachPdf(string fileKey, string hash) void
    }
    class ContractSignature {
        +Guid ContractId
        +Guid SignerUserId
        +SignerParty Party
        +string ContentHash
        +DateTime SignedAt
        +string? IpAddress
    }
    class SigningOtp {
        +Guid ContractId
        +Guid UserId
        +string CodeHash
        +DateTime SentAt
        +DateTime ExpiresAt
        +int FailedAttempts
        +DateTime? UsedAt
        +Verify(string codeHash, DateTime now) bool
    }
    class Commission {
        +Guid ContractId
        +Guid AgentId
        +long BaseAmount
        +decimal Rate
        +long Amount
        +CommissionStatus Status
        +Guid? ApprovedBy
        +DateTime? ApprovedAt
        +DateTime? PaidAt
        +string? PaymentReference
        +string? CancelReason
        +int Version
        +Approve(Guid adminId, DateTime now) void
        +MarkPaid(string reference, DateTime paidAt) void
        +Cancel(string reason) void
    }
    class Invoice {
        +string Code
        +Guid ContractId
        +int InstallmentNo
        +long Amount
        +DateOnly DueDate
        +InvoiceStatus Status
        +DateTime? IssuedAt
        +DateTime? PaidAt
        +string? PaymentNote
        +string? CancelReason
        +string? PdfFileKey
        +int Version
        +Issue(DateTime now) void
        +MarkPaid(string note, DateTime paidAt) void
        +Cancel(string reason) void
    }
    class Property
    class Listing
    class Customer
    class Agent

    Property "1" --> "0..*" Contract
    Listing "1" --> "0..*" Contract
    Customer "1" --> "0..*" Contract
    Agent "1" --> "0..*" Contract
    Contract "1" *-- "0..2" ContractSignature
    Contract "1" *-- "0..*" SigningOtp
    Contract "1" --> "0..1" Commission
    Agent "1" --> "0..*" Commission
    Contract "1" --> "0..*" Invoice
```

### 3.3. Enum

```mermaid
classDiagram
    direction LR
    class ProjectStatus {
        <<enumeration>>
        Active
        Inactive
    }
    class PropertyStatus {
        <<enumeration>>
        Available
        Reserved
        Sold
        Rented
    }
    class Direction {
        <<enumeration>>
        North
        South
        East
        West
        NorthEast
        NorthWest
        SouthEast
        SouthWest
    }
    class ListingType {
        <<enumeration>>
        Sale
        Rent
    }
    class ListingStatus {
        <<enumeration>>
        Draft
        PendingApproval
        Approved
        Rejected
        Closed
    }
    class KycStatus {
        <<enumeration>>
        Pending
        Passed
        Failed
        Error
    }
    class ContractType {
        <<enumeration>>
        Sale
        Lease
    }
    class ContractStatus {
        <<enumeration>>
        Draft
        PendingSignature
        Signed
        Cancelled
    }
    class SignerParty {
        <<enumeration>>
        Customer
        Company
    }
    class CommissionStatus {
        <<enumeration>>
        Pending
        Approved
        Paid
        Cancelled
    }
    class InvoiceStatus {
        <<enumeration>>
        Draft
        Issued
        Paid
        Cancelled
    }
```

### 3.4. Ràng buộc chính

| Ràng buộc | Nguồn | Thực hiện |
| --- | --- | --- |
| `Property.Code` duy nhất trong một `Project` | BR-02 | Unique index (`ProjectId`, `Code`) |
| `Project.Code`, `Contract.Code`, `Invoice.Code` duy nhất | BR-01, BR-12 | Unique index |
| Mỗi căn tối đa một tin `PendingApproval`/`Approved` | RULE-02 | Partial unique index trên `PropertyId` + `ListingRules` |
| Mỗi căn tối đa một hợp đồng `PendingSignature`/`Signed` | RULE-02, BR-08 | Partial unique index trên `PropertyId` + `ContractRules` |
| Mỗi hợp đồng đúng một hoa hồng | BR-11 | Unique index trên `Commission.ContractId` |
| Khách phải có KYC `Passed` khi gửi ký và khi ký | RULE-05 | `ContractRules` kiểm tra `KycVerification` mới nhất |
| Hoa hồng = round(`Value` × `CommissionRate` / 100), chốt khi gửi ký | RULE-08 | `Contract.SendForSigning` |
| Hợp đồng thuê: `Value` = `MonthlyRent` × `LeaseMonths` | Q-04 | Validator + `Contract` |
| Ký đủ: hợp đồng `Signed`, căn `Sold`/`Rented`, tin `Closed`, sinh `Commission` | RULE-09 | Một phương thức của `ContractService`, một lần `SaveChangesAsync` |
| Chữ ký gắn đúng phiên bản nội dung | BR-09, RULE-06 | `ContractSignature.ContentHash` phải bằng `Contract.ContentHash` |
| OTP hết hạn 5 phút, tối đa 5 lần sai | RULE-07 | `SigningOtp.Verify` |
| `Customer.UserId`, `Agent.UserId` không có khóa ngoại sang `identity` | AGENTS.md | Chỉ lưu giá trị, unique index |

## 4. Luồng xử lý một use case (ví dụ cập nhật tin đăng)

```mermaid
classDiagram
    direction TB
    class ListingsController {
        -IMediator mediator
        +Update(Guid id, UpdateListingRequest request) Task~IActionResult~
    }
    class UpdateListingCommand {
        <<record>>
        +Guid Id
        +string Title
        +string Description
        +long Price
    }
    class UpdateListingCommandValidator {
        +UpdateListingCommandValidator()
    }
    class UpdateListingCommandHandler {
        -IListingService listingService
        +Handle(UpdateListingCommand command, CancellationToken ct) Task~ListingResponse~
    }
    class IListingService {
        <<interface>>
        +CreateAsync(CreateListingCommand command, CancellationToken ct) Task~ListingResponse~
        +UpdateAsync(UpdateListingCommand command, CancellationToken ct) Task~ListingResponse~
        +SubmitAsync(Guid id, CancellationToken ct) Task
        +ApproveAsync(Guid id, CancellationToken ct) Task
        +RejectAsync(Guid id, string reason, CancellationToken ct) Task
        +GetByIdAsync(Guid id, CancellationToken ct) Task~ListingResponse~
    }
    class ListingService {
        -IListingRepository listingRepository
        -IRealEstateUnitOfWork unitOfWork
        -ICurrentUser currentUser
    }
    class ListingRules {
        <<static>>
        +EnsureCanEdit(Listing listing, ICurrentUser user) void
    }
    class ListingMapping {
        <<static>>
        +ToResponse(Listing listing) ListingResponse
    }
    class IListingRepository {
        <<interface>>
        +GetByIdAsync(Guid id, CancellationToken ct) Task~Listing~
        +Add(Listing listing) void
    }
    class ListingRepository {
        -RealEstateContext context
    }
    class IRealEstateUnitOfWork {
        <<interface>>
        +SaveChangesAsync(CancellationToken ct) Task~int~
    }
    class RealEstateUnitOfWork
    class RealEstateContext

    ListingsController ..> UpdateListingCommand : Send qua IMediator
    UpdateListingCommandValidator ..> UpdateListingCommand : ValidationBehavior
    UpdateListingCommandHandler ..> UpdateListingCommand : xử lý
    UpdateListingCommandHandler --> IListingService
    IListingService <|.. ListingService
    ListingService ..> ListingRules
    ListingService ..> ListingMapping
    ListingService --> IListingRepository
    ListingService --> IRealEstateUnitOfWork
    IListingRepository <|.. ListingRepository
    IRealEstateUnitOfWork <|.. RealEstateUnitOfWork
    ListingRepository --> RealEstateContext
    RealEstateUnitOfWork --> RealEstateContext
```

| Thành phần | Project | Thư mục |
| --- | --- | --- |
| `ListingsController` | `Bds.Presentation.RealEstate` | `Controllers/v1` |
| `UpdateListingCommand`, handler, validator | `Bds.Service.RealEstate` | `UseCases/Listings/...` |
| `IListingService` / `ListingService` | `Bds.Service.RealEstate` | `Interfaces/` / `Services/` |
| `ListingRules`, `ListingMapping` | `Bds.Service.RealEstate` | `UseCases/Listings` |
| `IListingRepository` / `ListingRepository` | `Bds.Infrastructure.RealEstate` | `Interfaces/` / `Repositories/` |
| `UpdateListingRequest`, `ListingResponse` | `Bds.Model.Dto.RealEstate` | `Requests/`, `Responses/` |

`ICurrentUser` chưa có trong BuildingBlocks.

## 5. Điểm cần chốt

1. `ProjectStatus` chỉ gồm `Active`/`Inactive`, hay cần thêm giai đoạn (sắp mở bán, đang bán, đã bàn giao)?
2. `AuditLog` đặt riêng trong mỗi schema như mục 1, hay gom về một chỗ?
3. Mẫu hợp đồng (BR-15) lưu dạng tệp template trong code, không phải entity. Cần quản trị mẫu trên giao diện thì thêm entity `ContractTemplate`.
