# Working Rules

## Quy trình

1. Đọc `AGENTS.md`, file này và `PROJECT_BRIEF.md`; kiểm tra code thực tế. Nếu tài liệu khác với code thì ưu tiên code và báo lại.
2. Với thay đổi cấu trúc hoặc nhiều file: trình bày cây thư mục và danh sách file, chờ duyệt rồi mới ghi.
3. Không ghi đè, di chuyển hoặc xóa code hiện có khi chưa được yêu cầu.
4. Sau khi sửa: chạy các kiểm tra trong `AGENTS.md`, báo kết quả từng lệnh và phần chưa kiểm chứng.

## Luồng xử lý một request

```
Controller → IMediator.Send(Command/Query)
           → ValidationBehavior → Validator
           → Handler → I{Feature}Service → {Feature}Service
           → Repository / UnitOfWork → Database
```

| Vị trí | Trách nhiệm |
| --- | --- |
| `Controllers/v1` | Nhận HTTP request, tạo Command/Query, gửi qua `IMediator`, trả HTTP response |
| `Validators` | Kiểm tra dữ liệu đầu vào (bắt buộc, định dạng, độ dài, khoảng giá trị); tự chạy qua `ValidationBehavior` trước handler. Không truy vấn database |
| `Commands/Handlers`, `Queries/Handlers` | Nhận Command/Query, gọi một phương thức của `I{Feature}Service`, trả response. Không chứa nghiệp vụ, không gọi repository hay UnitOfWork trực tiếp |
| `Interfaces/I{Feature}Service.cs` | Hợp đồng nghiệp vụ của một feature; handler chỉ phụ thuộc vào interface này |
| `Services/{Feature}Service.cs` | Nghiệp vụ: lấy dữ liệu qua repository, kiểm tra quy tắc phụ thuộc dữ liệu và trạng thái, gọi phương thức của entity, lưu qua UnitOfWork, mapping sang response |
| Gốc `UseCases/{Feature}` | Mapping và business rule dùng chung (`ListingMapping.cs`, `ListingRules.cs`), được service gọi |
| Entity trong Domain | Quy tắc gắn với dữ liệu của chính entity (`listing.Approve(...)`, `property.Reserve()`) |
| Repository trong Infrastructure | Truy cập dữ liệu: Identity thêm, sửa, xóa đối tượng trong DbContext; RealEstate gọi function `fn_*`/procedure `sp_*` bằng Dapper |
| Interface + implementation kỹ thuật | Phần kỹ thuật hoặc tích hợp ngoài (`IJwtTokenGenerator`, `IPasswordHasher`, lưu file) |

Mỗi feature có một service (`IListingService`/`ListingService`) với nhiều phương thức, mỗi phương thức ứng với một use case. Service có thể gọi service khác trong cùng module, không gọi sang module khác.

Ví dụ cập nhật tin đăng:

```
UpdateListingCommandValidator kiểm tra input
→ UpdateListingCommandHandler → listingService.UpdateAsync(command, ct)
→ ListingService: repo.GetByIdAsync → ListingRules.EnsureCanEdit(listing, currentUser)
  → listing.Update(...) → unitOfWork.SaveChangesAsync → ListingMapping.ToResponse(listing)
```

## UnitOfWork

- Identity có UoW `IIdentityUnitOfWork` (trong `Interfaces/` của Infrastructure), kế thừa `IUnitOfWork` và `UnitOfWork<TContext>` từ BuildingBlocks. Các quy tắc UoW bên dưới áp dụng cho Identity.
- RealEstate không dùng UoW: mỗi lần gọi procedure `sp_*` là một transaction. Nghiệp vụ cần nhiều thao tác ghi cùng lúc phải viết trong một procedure, dùng `SELECT ... FOR UPDATE` khi cần khóa dòng.
- Repository chỉ thêm, sửa, xóa đối tượng trong DbContext, không gọi `SaveChanges`.
- Mỗi phương thức ghi dữ liệu của service gọi `SaveChangesAsync` đúng một lần ở cuối để mọi thay đổi nằm trong một transaction. Khi service gọi service khác, chỉ phương thức ngoài cùng gọi `SaveChangesAsync`.
- Phương thức đọc của service không dùng UoW; repository nên đọc với `AsNoTracking`.
- Một UoW không bao giờ trải qua nhiều module.

## Đăng ký DI

- `Bds.Service.{Module}/Extensions`: đăng ký DbContext và UoW (RealEstate: `IRealEstateConnectionFactory`), repository, service (`services.AddScoped<IListingService, ListingService>()`), MediatR handler và validator của module.
- `Bds.Presentation.{Module}/Extensions`: `Add{Module}Module` thêm controller của module và gọi đăng ký của Service.
- `ValidationBehavior` chỉ đăng ký một lần ở Host qua `AddBuildingBlocksApplication()`.

## Thư viện

- MediatR ghim 12.5.0 vì bản 13+ yêu cầu license key thương mại. Không nâng version khi chưa thống nhất.
- Version package quản lý tập trung trong `backend/Directory.Packages.props`.

## Tác vụ nền

- Gửi email, sinh PDF, xuất báo cáo chạy nền qua Hangfire (BRD BR-32). Service chỉ enqueue job **sau** khi `SaveChangesAsync` thành công.
- Job phải chạy lại được an toàn: ví dụ job sinh PDF bỏ qua nếu hợp đồng đã có file.
- Không đưa nghiệp vụ cần tính nguyên tử (đổi trạng thái hợp đồng, căn, tin, sinh hoa hồng) vào job; các thay đổi này nằm trong phương thức của service.
