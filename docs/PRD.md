# PRD — Hệ thống quản lý bất động sản

| Thuộc tính | Nội dung |
| --- | --- |
| Phiên bản | 1.0 — đề xuất cho MVP bài tập lớn |
| Ngày cập nhật | 06/09/2026 |
| Nguồn yêu cầu | [yeu_cau.pdf](yeu_cau.pdf), trang 1–2 |
| Tài liệu liên quan | [Kiến trúc](ARCHITECTURE.md), [ERD](ERD.md) |
| Trạng thái | Cơ sở đặc tả và triển khai; chưa xác nhận chức năng đã hoàn thành |

## 1. Vấn đề và mục tiêu sản phẩm

Đơn vị kinh doanh bất động sản cần quản lý tập trung dự án, căn hộ, tin bán/cho thuê và hợp đồng. Môi giới cần theo dõi tin, giao dịch và hoa hồng; khách hàng cần tìm căn phù hợp, xác thực danh tính, xem và ký hợp đồng trực tuyến. Quản trị viên cần kiểm soát chất lượng tin và theo dõi hoạt động qua dashboard.

Mục tiêu MVP:

1. Hoàn thành luồng dự án/căn hộ → đăng tin → duyệt tin → tìm kiếm → KYC → ký hợp đồng → tải PDF.
2. Quản lý hoa hồng gắn với hợp đồng và môi giới, có lịch sử thay đổi.
3. Cung cấp dashboard về số tin và số hợp đồng với số liệu kiểm chứng được.
4. Đáp ứng yêu cầu nền tảng, kiểm thử, triển khai và bàn giao trong PDF.

## 2. Phạm vi và giả định

**Bắt buộc từ PDF:** CRUD dự án/căn hộ; tin bán/cho thuê và duyệt tin; tìm theo vị trí, giá; ký online; báo cáo số tin, số hợp đồng; hoa hồng; lưu hợp đồng PDF; KYC. Yêu cầu chung gồm tài khoản, RBAC, nhập/xuất, audit, soft-delete, versioning, thông báo, job, bảo mật và vận hành.

**Quyết định đề xuất cho MVP:** các quy tắc dưới đây làm rõ phần PDF chưa quy định và có thể điều chỉnh trước khi triển khai.

| Mã | Quyết định đề xuất |
| --- | --- |
| A-01 | Dùng ba vai trò Admin, Môi giới, Khách hàng theo phần Real Estate; Admin duyệt tin và quản lý danh mục. Vai trò Manager riêng chưa thuộc MVP. |
| A-02 | Nền tảng đại diện đơn vị bán/cho thuê; Admin được phân quyền ký đại diện đơn vị, khách hàng ký với vai trò bên mua/thuê. Môi giới lập hợp đồng nhưng không mặc nhiên có quyền ký đại diện. |
| A-03 | Một hợp đồng gắn một căn hộ, một tin đăng, một khách hàng và một môi giới chính. Đồng sở hữu, nhiều khách hàng hoặc chia hoa hồng nhiều môi giới chưa thuộc MVP. |
| A-04 | KYC khách hàng phải đạt trước khi gửi hợp đồng chờ ký và khi khách thực hiện ký. Bản demo có thể dùng adapter KYC giả lập, phải hiển thị rõ chế độ demo. |
| A-05 | Ký demo bằng tài khoản đã đăng nhập và OTP email, ràng buộc với đúng phiên bản hợp đồng. Chưa chọn nhà cung cấp KYC/chữ ký số; không tự coi cơ chế demo là tích hợp chữ ký số được chứng thực. |
| A-06 | Tiền tệ MVP là VND. Giá bán tính cho toàn căn, giá thuê theo tháng. Hoa hồng tính theo tỷ lệ phần trăm trên cơ sở tính được lưu tại hợp đồng; mặc định cơ sở là giá trị giao dịch ghi trong hợp đồng. |
| A-07 | Mỗi căn chỉ có một tin đang chờ duyệt/đã duyệt và một hợp đồng đang chờ ký/đã ký. Thuê nhiều kỳ, gia hạn, chấm dứt hợp đồng đã ký và bán lại sẽ cần luồng bổ sung. |
| A-08 | Hóa đơn là chứng từ theo dõi nội bộ gắn hợp đồng; ghi nhận thanh toán thủ công có audit. Tích hợp hóa đơn điện tử, kế toán và cổng thanh toán chưa thuộc MVP. |

**Ngoài phạm vi:** ứng dụng di động riêng, bản đồ/GIS và định giá AI, chat realtime, thanh toán online, quy trình thế chấp, phân phối nhiều môi giới, marketplace chủ nhà tự đăng, xử lý pháp lý hoặc thuế tự động. 2FA là tính năng tùy chọn theo PDF, không chặn nghiệm thu MVP.

## 3. Người dùng và quyền truy cập

| Khả năng | Admin | Môi giới | Khách hàng |
| --- | --- | --- | --- |
| Tài khoản, vai trò, khóa tài khoản | Quản lý toàn hệ thống | Sửa hồ sơ cá nhân | Sửa hồ sơ cá nhân |
| CRUD dự án/căn hộ | Có | Xem danh mục hoạt động | Xem thông tin qua tin đã duyệt |
| Tạo/sửa/gửi duyệt tin | Quản lý toàn bộ | Tin do mình phụ trách | Không |
| Duyệt/từ chối tin | Có, ghi người duyệt và lý do | Không | Không |
| Tìm kiếm tin công khai | Có | Có | Có; khách chưa đăng nhập cũng xem được |
| Hồ sơ khách hàng/KYC | Quản lý theo quyền | Xem thông tin cần thiết của khách trong hợp đồng phụ trách; chỉ xem trạng thái KYC | Xem/gửi hồ sơ của mình |
| Lập hợp đồng | Có | Hợp đồng mình phụ trách | Xem hợp đồng mình tham gia |
| Ký hợp đồng | Với tư cách đại diện được chỉ định | Không mặc định | Ký với tư cách khách được chỉ định |
| Hóa đơn/hoa hồng | Quản lý và xác nhận | Xem hoa hồng của mình, chứng từ giao dịch phụ trách | Xem hóa đơn hợp đồng của mình; không xem hoa hồng |
| Dashboard, xuất dữ liệu | Toàn hệ thống | Trong phạm vi phụ trách | Chỉ dữ liệu/tài liệu của mình |
| Audit log | Theo quyền quản trị | Không | Không |

Mỗi quyền phải kiểm tra ở API theo hành động và bản ghi. Ẩn nút trên giao diện không đủ để cấp quyền. Người dùng tự đăng ký chỉ nhận vai trò Khách hàng; không được tự cấp vai trò Admin/Môi giới. Email mời hoặc cách tạo tài khoản môi giới do Admin quản lý.

## 4. Yêu cầu chức năng và tiêu chí nghiệm thu

Tất cả mục P0 là bắt buộc cho MVP. Phần chi tiết đánh dấu A-xx tuân theo giả định ở mục 2.

| ID | Ưu tiên | Chức năng / nhu cầu | Tiêu chí nghiệm thu |
| --- | --- | --- | --- |
| FR-01 | P0 | Đăng ký, đăng nhập, JWT/OAuth2, đặt lại mật khẩu | Email không trùng sau chuẩn hóa; mật khẩu được băm; token hết hạn bị từ chối; token reset chỉ dùng một lần và có hạn; không tiết lộ email có tồn tại qua thông báo reset. |
| FR-02 | P0 | RBAC | Có tối thiểu ba vai trò; API từ chối hành động trái quyền và truy cập bản ghi người khác; tự đăng ký không nhận quyền quản trị. |
| FR-03 | P0 | Quản lý dự án | Admin tạo/xem/sửa/xóa mềm; có mã, tên, địa chỉ, trạng thái; hỗ trợ tìm kiếm, lọc, sắp xếp, phân trang; không xóa dự án khi còn căn chưa xóa. |
| FR-04 | P0 | Quản lý căn hộ | Căn thuộc dự án, có mã, diện tích, vị trí, số phòng, trạng thái; mã căn duy nhất trong dự án; diện tích > 0; không xóa căn có tin hoặc hợp đồng đang hoạt động. |
| FR-05 | P0 | Đăng và duyệt tin | Môi giới tạo bản nháp, gửi duyệt; Admin duyệt/từ chối kèm lý do; chỉ tin đã duyệt và căn khả dụng được công khai; sửa nội dung tin đã duyệt phải đưa về nháp và duyệt lại. |
| FR-06 | P0 | Tìm căn theo vị trí, giá | Lọc theo địa bàn/dự án, loại bán/thuê, khoảng giá; phân trang có thứ tự ổn định; không so sánh chung giá bán toàn căn với giá thuê theo tháng; dữ liệu nháp/từ chối/xóa không xuất hiện. |
| FR-07 | P0 | Hồ sơ khách và môi giới | Hồ sơ gắn tài khoản; hợp đồng trỏ đúng khách và môi giới; môi giới không thể xem giấy tờ KYC thô hoặc hồ sơ khách ngoài phạm vi. |
| FR-08 | P0 | KYC | Gửi yêu cầu, xem trạng thái chờ/đạt/không đạt; kết quả gắn đúng khách và mã yêu cầu; callback được xác thực, xử lý lặp an toàn; lỗi nhà cung cấp không được chuyển thành đạt. |
| FR-09 | P0 | Lập và ký hợp đồng | Tạo từ tin đã duyệt; lưu loại bán/thuê, số tiền, điều khoản và các bên; khách KYC đạt; gửi OTP và ký đúng phiên bản; chỉ chuyển đã ký khi đủ hai bên theo A-02. |
| FR-10 | P0 | Lưu và tải hợp đồng PDF | PDF tạo từ nội dung phiên bản đã ký, lưu riêng tư, có hash và tham chiếu; bên có quyền tải được; bên khác bị từ chối; lỗi tạo PDF hiện trạng thái và có thể thử lại, không mất chữ ký đã ghi nhận. |
| FR-11 | P0 | Quản lý hoa hồng | Sau khi đủ chữ ký, sinh một khoản hoa hồng cho môi giới chính; lưu cơ sở tính, tỷ lệ, số tiền; Admin duyệt/ghi nhận chi; gửi lại job không tạo khoản trùng. |
| FR-12 | P0 | Báo cáo và dashboard | Hiển thị số tin theo trạng thái, số hợp đồng theo trạng thái; lọc thời gian và phạm vi quyền; kết quả khớp dữ liệu gốc, không đếm trùng do join; định nghĩa chỉ số ở mục 7. |
| FR-13 | P0 | Nhập/xuất Excel và CSV | Hỗ trợ mẫu nhập dự án/căn hộ; xuất danh sách tin, hợp đồng, hoa hồng theo quyền; kiểm tra từng dòng và báo lỗi rõ; đề xuất nhập toàn bộ hoặc không nhập nếu có lỗi; ngăn nội dung ô bị diễn giải thành công thức nguy hiểm. |
| FR-14 | P0 | Xuất báo cáo/chứng từ PDF | Có mẫu hợp đồng, hóa đơn nội bộ và báo cáo; dữ liệu đúng bộ lọc và quyền người yêu cầu; tác vụ lớn chạy nền và trả trạng thái/tệp kết quả. |
| FR-15 | P0 | Thông báo | Gửi email khi reset mật khẩu, có yêu cầu ký và hoàn tất hợp đồng; tác vụ gửi mail chạy nền, có retry giới hạn; thất bại không làm lặp giao dịch nghiệp vụ. In-app là phần mở rộng tùy chọn. |
| FR-16 | P0 | Audit, soft-delete, versioning | Audit ghi ai/làm gì/lúc nào/đối tượng; bản ghi đã xóa không vào danh sách mặc định; sửa bản ghi nhạy cảm yêu cầu phiên bản hiện tại, xung đột bị từ chối; hợp đồng đã ký không được sửa/xóa. |
| FR-17 | P0 | Hóa đơn nội bộ theo A-08 | Tạo hóa đơn từ hợp đồng đã ký, mã duy nhất, số tiền dương; Admin ghi nhận đã thanh toán kèm thời điểm/tham chiếu; có bản PDF; không mặc nhiên tạo hoa hồng từ trạng thái hóa đơn. |
| FR-18 | P1 | 2FA đăng nhập | Nếu thực hiện, có luồng bật/tắt và khôi phục được xác thực; OTP ký hợp đồng không đồng nghĩa đã triển khai 2FA cho đăng nhập. |

## 5. Luồng nghiệp vụ và trạng thái

### 5.1. Đăng tin và tìm kiếm

1. Admin tạo dự án và căn hộ ở trạng thái `available`.
2. Môi giới lập tin `draft`, chọn `sale` hoặc `rent`, nhập giá và nội dung.
3. Gửi duyệt chuyển `pending`; Admin chuyển `approved` hoặc `rejected` với lý do.
4. Khách tìm kiếm chỉ thấy tin `approved` của căn `available`.
5. Sửa tin đã duyệt chuyển lại `draft`. Khi có hợp đồng `pending_signatures`, khóa sửa/đóng tin thủ công cho đến khi hợp đồng được hủy hoặc hoàn tất.

| Đối tượng | Chuyển trạng thái hợp lệ |
| --- | --- |
| Tin đăng | `draft → pending → approved/rejected`; `rejected → draft`; `approved → draft/closed`; `pending → draft` khi rút duyệt |
| KYC | `pending → verified/rejected/failed`; `verified → rejected` khi bị thu hồi có audit; lần gửi lại tạo hồ sơ mới, không ghi đè lịch sử; yêu cầu mới nhất quyết định trạng thái hiện tại |
| Hợp đồng | `draft → pending_signatures → signed`; `draft/pending_signatures → cancelled` |
| Căn hộ | `available → reserved` khi gửi hợp đồng chờ ký; `reserved → sold/rented` khi ký đủ; `reserved → available` khi hủy hợp đồng |
| Hoa hồng | `pending → approved → paid`; `pending/approved → cancelled` kèm lý do |
| Hóa đơn | `draft → issued → paid`; `draft/issued → void` kèm lý do |

### 5.2. KYC và ký hợp đồng

1. Môi giới/Admin lập hợp đồng nháp từ tin đã duyệt, chỉ định khách và Admin đại diện đơn vị. Giá và điều khoản được chụp lại trong phiên bản hợp đồng.
2. Khách gửi KYC. Khi KYC đạt, người lập gửi hợp đồng chờ ký; hệ thống giữ căn bằng giao dịch nguyên tử. Nếu căn đã được giữ bởi hợp đồng khác, yêu cầu bị từ chối.
3. Hệ thống đóng băng phiên bản và các bên ký. Mỗi bên xem nội dung, yêu cầu OTP email, rồi xác nhận ký trên phiên bản đó. Đề xuất OTP hết hạn sau 5 phút, tối đa 5 lần thử và có rate limit gửi lại.
4. Mỗi xác nhận lưu thời điểm, phương thức, người ký và hash nội dung. OTP thô không được lưu lâu dài hoặc ghi log. Chỉ khách có KYC đạt được ký; tài khoản bị khóa không được ký.
5. Khi đủ hai bên ký, trong cùng giao dịch cập nhật hợp đồng `signed`, căn `sold/rented`, tin `closed`, tạo hoa hồng và sự kiện tạo PDF/email. Worker xử lý sự kiện sau commit.
6. Các bên xem trạng thái tạo PDF và tải tài liệu khi hoàn tất. Gửi yêu cầu ký lặp không tạo thêm chữ ký, hoa hồng hoặc chuyển trạng thái lần hai.

Nếu cần sửa nội dung sau khi gửi ký, hủy hợp đồng hiện tại và lập hợp đồng mới; không tái sử dụng xác nhận ký cũ. MVP không xử lý sửa/hủy hợp đồng đã ký. OTP/email lỗi cho phép thử lại trong giới hạn; KYC lỗi giữ trạng thái chưa đạt; PDF/email lỗi được xử lý lại độc lập.

### 5.3. Hoa hồng và hóa đơn

- Hoa hồng = `round(cơ_sở_tính × tỷ_lệ_phần_trăm / 100, 0)` VND; cơ sở không âm và tỷ lệ nằm trong [0, 100]. Giá trị này được chốt khi gửi hợp đồng chờ ký.
- Với hợp đồng thuê, phải thể hiện rõ tổng giá trị/cơ sở tính trong hợp đồng; không tự suy ra hoa hồng từ giá thuê tháng của tin đăng.
- Admin kiểm tra và duyệt khoản hoa hồng, sau đó ghi nhận đã chi với thời điểm/tham chiếu. MVP không chuyển tiền tự động.
- Một hợp đồng có thể có nhiều hóa đơn theo đợt; mỗi hóa đơn chỉ ghi nhận thanh toán toàn bộ trong MVP. Hóa đơn đã phát hành giữ nguyên nội dung; sai sót được đánh dấu `void` có lý do rồi lập chứng từ mới.

## 6. Màn hình chính

| Nhóm | Màn hình |
| --- | --- |
| Chung | Đăng nhập, đăng ký, quên/đặt lại mật khẩu, hồ sơ cá nhân |
| Khách hàng | Danh sách/tìm kiếm và chi tiết tin, KYC của tôi, hợp đồng của tôi, xem nội dung và ký OTP, tải PDF, hóa đơn của tôi |
| Môi giới | Tin của tôi, tạo/sửa tin, khách thuộc giao dịch phụ trách, lập/theo dõi hợp đồng, hoa hồng của tôi, báo cáo trong phạm vi |
| Admin | Dashboard, tài khoản và quyền, dự án, căn hộ, hàng chờ duyệt tin, hồ sơ/KYC, hợp đồng, hóa đơn, duyệt hoa hồng, nhập/xuất, audit |

Danh sách có loading, trạng thái rỗng, lỗi và phân trang. Các thao tác xóa mềm, duyệt, ký, ghi nhận tiền cần hiển thị rõ đối tượng và kết quả; lỗi không làm mất nội dung biểu mẫu đã nhập. Giao diện dùng tiếng Việt, hiển thị giờ Việt Nam và tiền VND nhất quán.

## 7. Chỉ số và tiêu chí thành công

| Chỉ số | Định nghĩa / tiêu chí |
| --- | --- |
| Số tin | Đếm `listings.id` chưa xóa mềm, theo `created_at` trong khoảng lọc; chia theo trạng thái hiện tại. Không phải số sự kiện duyệt tin. |
| Số hợp đồng | Đếm `contracts.id` chưa xóa mềm theo `created_at`; chia theo trạng thái hiện tại. |
| Hợp đồng đã ký trong kỳ | Đếm hợp đồng `signed` theo `signed_at`, tách riêng chỉ số số hợp đồng được tạo. |
| Hoa hồng | Tổng số tiền theo trạng thái và môi giới được phép xem; lọc theo `created_at`. Không gọi đây là doanh thu bất động sản. |
| Thời gian và độ mới | Bộ lọc ngày theo Asia/Ho_Chi_Minh chuyển sang UTC, khoảng `[bắt đầu, kết thúc)`; cache báo cáo đề xuất tối đa 60 giây và hiển thị thời điểm cập nhật. |
| Hoàn thành nghiệp vụ | Cả kịch bản bán và thuê chạy xuyên suốt; có kịch bản từ chối tin, KYC lỗi, ký lặp, truy cập trái quyền và xung đột giữ căn. |
| Chất lượng | Toàn bộ tiêu chí P0 được kiểm chứng; không còn lỗi chặn luồng chính hoặc lộ dữ liệu ngoài quyền; coverage đạt ngưỡng mục 8. |

## 8. Yêu cầu phi chức năng

| ID | Yêu cầu và cách kiểm chứng |
| --- | --- |
| NFR-01 | Chống SQLi/XSS/CSRF theo cơ chế xác thực; truy vấn tham số hóa, validation, CORS allowlist, rate limit; kiểm thử truy cập sai vai trò và sai chủ sở hữu. |
| NFR-02 | Băm mật khẩu, HTTPS khi triển khai, bí mật qua cấu hình môi trường; không log mật khẩu/token/OTP/giấy tờ KYC; tải tệp riêng tư cần kiểm tra quyền. |
| NFR-03 | Redis cache danh mục và báo cáo; invalidate khi cập nhật danh mục; tác vụ lâu đưa vào Celery, có trạng thái, retry giới hạn và idempotency. |
| NFR-04 | Mục tiêu hiệu năng đề xuất: API danh sách/tìm kiếm p95 ≤ 2 giây với ≥ 2.000 bản ghi mẫu và 20 người dùng đồng thời, không tính thời gian nhà cung cấp bên ngoài. Ghi cấu hình máy, thời lượng và kết quả đo khi nghiệm thu. |
| NFR-05 | Unit test service và integration test API; yêu cầu PDF tối thiểu 30–40% coverage, đề xuất đặt CI gate ≥ 40% line coverage cho mã ứng dụng backend. Có test ranh giới quyền, giữ căn đồng thời, ký và job lặp. |
| NFR-06 | Docker Compose chạy các thành phần theo kiến trúc, có hướng dẫn cấu hình, migration, seed ≥ 2.000 bản ghi dữ liệu mẫu và tài khoản demo ba vai trò. |
| NFR-07 | CI/CD đơn giản: build, test, đóng gói, deploy; thất bại kiểm thử chặn bước deploy. |
| NFR-08 | Logging có cấu trúc, request/job ID, health endpoint; phân biệt tiến trình hoạt động với khả năng kết nối DB/Redis; lưu trạng thái job bền vững để đối soát sau lỗi. |
| NFR-09 | OpenAPI/Swagger và Postman collection đủ cho luồng chính; tài liệu hướng dẫn cài đặt/sử dụng, mẫu hợp đồng, dashboard và video demo 5–10 phút. |

## 9. Kế hoạch triển khai và bàn giao

| Mốc | Kết quả | Điều kiện hoàn thành |
| --- | --- | --- |
| M1 — Nền tảng | Schema/migration, tài khoản/RBAC, Docker, CI | Ba vai trò truy cập đúng; migration và test nền tảng chạy được |
| M2 — Danh mục/tin | Dự án, căn hộ, duyệt tin, tìm kiếm | Tin chưa duyệt không công khai; CRUD và bộ lọc chạy với dữ liệu seed |
| M3 — Giao dịch | KYC, hợp đồng/OTP, PDF, hóa đơn, hoa hồng | Bán và thuê chạy xuyên suốt; kiểm chứng quyền, phiên bản, giữ căn và idempotency |
| M4 — Hoàn thiện | Báo cáo, nhập/xuất, audit, tối ưu, tài liệu | Đạt tiêu chí P0/NFR, có bằng chứng test, mẫu hợp đồng và video |

Bộ bàn giao gồm SRS, ERD, use case/flow, sơ đồ kiến trúc, hướng dẫn triển khai/sử dụng, OpenAPI/Postman, mã nguồn và migration, seed, test/coverage, mẫu hợp đồng, dashboard và video. Thời lượng từng mốc phụ thuộc nhân lực; tài liệu này không tự đặt ngày cam kết.

## 10. Điểm cần chốt và rủi ro triển khai

| Vấn đề | Mặc định để tiếp tục thiết kế | Ảnh hưởng khi thay đổi |
| --- | --- | --- |
| Vai trò Manager trong yêu cầu chung | A-01: ba vai trò nghiệp vụ | Bổ sung role/permission, ma trận quyền và test |
| Nhà cung cấp KYC và chữ ký | A-04/A-05: adapter, demo có nhãn | Thay adapter, cơ chế callback/bằng chứng và cấu hình triển khai |
| Chủ thể và người đại diện ký | A-02: khách và Admin được chỉ định | Cập nhật các bên ký, biểu mẫu và quy trình ủy quyền |
| Công thức hoa hồng | A-06: một tỷ lệ và cơ sở chốt trong hợp đồng | Đổi quy tắc cho hợp đồng mới; không tính lại khoản lịch sử |
| Hợp đồng thuê nhiều kỳ/kết thúc | A-07: chưa tự giải phóng căn đã thuê | Cần trạng thái, lịch kỳ hạn và quy tắc chống trùng khoảng thuê |
| Phạm vi hóa đơn | A-08: chứng từ nội bộ | Tích hợp hóa đơn/thuế/thanh toán cần đặc tả riêng |
| Dữ liệu KYC và tệp lưu lâu dài | Kho riêng tư, dữ liệu demo giả lập | Cần chốt chính sách lưu/xóa và sao lưu trước khi dùng dữ liệu thực |

Các giả định này đã được phản ánh trong [ERD](ERD.md); nếu đổi phạm vi cần cập nhật đồng thời hai tài liệu.
