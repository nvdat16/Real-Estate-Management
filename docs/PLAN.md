# PLAN — Kế hoạch hoàn thiện dự án

| Thuộc tính | Nội dung |
| --- | --- |
| Phiên bản | 1.0 — bản đề xuất để review, 17/09/2026 |
| Căn cứ | [PRD](PRD.md), [SPEC](SPEC.md), [ERD](ERD.md), [USE_CASES](USE_CASES.md), [ARCHITECTURE](ARCHITECTURE.md), khảo sát repository |
| Trạng thái | Phase 0–3 đã hoàn thành và kiểm chứng; xem Nhật ký thực hiện ở mục 9 |
| Giả định nhân lực | 1 người làm chính; ước lượng theo **ngày công**, không phải ngày lịch |
| Tổng ước lượng | 62–83 ngày công (chi tiết ở mục 6) |

## 1. Cách dùng tài liệu này

- `- [ ]` là việc chưa làm, `- [x]` là đã xong và **đã có bằng chứng** (test pass, lệnh chạy được, ảnh chụp).
- Mỗi phase có **Gate**: không mở phase sau khi gate của phase trước chưa đạt, trừ Phase 9 được phép chạy song song.
- Mã `T-01…T-13` là bộ kiểm chứng ở [SPEC §12](SPEC.md); mã `E2E-01…E2E-09` là kịch bản demo ở [USE_CASES §6](USE_CASES.md). Gate tham chiếu trực tiếp các mã này để không tự đặt tiêu chí mới.
- Định nghĩa "xong" cho một module nghiệp vụ nằm ở mục 7.

## 2. Hiện trạng khởi điểm

Phần đã có mã nguồn chạy được và có test: `app/main.py` với `/health`, `app/core/config.py`, `app/core/database.py`, 4 middleware (`request_id`, `rate_limit`, `audit`, `error_handler`) và `tests/unit/test_middleware.py`.

Phần còn rỗng: 14 module nghiệp vụ dưới `src/backend/app/modules/` (98 file 0 byte), `app/workers/*`, `app/integrations/*`, `app/common/*`, `app/core/{security,permissions,exceptions,logging,constants}.py`, `scripts/{seed,create_admin}.py`, `alembic.ini`, `infrastructure/nginx/nginx.conf`. Hai tài liệu bàn giao `docs/API.md` và `docs/DEPLOYMENT.md` chưa tồn tại trong repo. Frontend còn template Vite mặc định. CI chỉ `echo`.

Bốn blocker phải xử lý trước mọi việc khác:

| # | Blocker | Hệ quả nếu không sửa |
| --- | --- | --- |
| B1 | [`src/backend/Dockerfile`](../src/backend/Dockerfile) viết `CMD` dạng JSON array nhiều dòng mà không có `\` | `docker build` lỗi parse `unknown instruction`, không dựng được image |
| B2 | [`docker-compose.yml`](../docker-compose.yml) mount `./backend:/app` (đúng phải là `./src/backend`) — `build.context` đã được sửa | volume che mã nguồn trong image, container chạy thư mục rỗng |
| B3 | Không có `pyproject.toml`/`pytest.ini`, `tests/conftest.py` rỗng | `pytest-asyncio` thiếu `asyncio_mode`, không có DB test, không đo được coverage |
| B4 | `requirements.txt` thiếu `email-validator`, `openpyxl`, thư viện PDF, `celery[redis]`; chưa pin phiên bản | FR-10/FR-13/FR-14 không code được; build hai thời điểm khác kết quả |

---

## 3. Các phase

### Phase 0 — Mở đường (3–4 ngày công)

Điều kiện tiên quyết: không có. **Mục tiêu:** mọi việc sau đó đều kiểm chứng được bằng lệnh.

- [x] **0.1** Sửa B1: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` trên một dòng; bỏ `--reload` khỏi image, để `--reload` ở compose dev.
- [x] **0.2** Sửa B2: `volumes: - ./src/backend:/app` cho cả `api` và `worker`; thêm `healthcheck` cho `postgres`/`redis` và `depends_on: condition: service_healthy`.
- [x] **0.3** Thêm service `frontend` (Vite dev server) và `nginx` vào compose; viết [`infrastructure/nginx/nginx.conf`](../infrastructure/nginx/nginx.conf): serve build React, proxy `/api` sang `api:8000`, giữ header `X-Request-ID`.
- [x] **0.4** Sửa B4: pin toàn bộ `requirements.txt`, tách `requirements-dev.txt` (ruff, mypy, pytest*), bổ sung `email-validator`, `openpyxl`, thư viện PDF đã chốt, `celery[redis]`.
- [x] **0.5** Sửa B3: `pyproject.toml` cấu hình ruff + mypy + pytest (`asyncio_mode = "auto"`) + coverage; viết `tests/conftest.py` với app fixture, async client, database test riêng và dọn dữ liệu giữa các test.
- [x] **0.6** Viết lại [`.github/workflows/ci.yaml`](../.github/workflows/ci.yaml): job `lint` (ruff + mypy) → `test` (pytest + `--cov=app --cov-fail-under=40`) → `build` (docker build) → `smoke` (`docker compose up -d` rồi gọi `/health`).
- [x] **0.7** Sinh `JWT_SECRET_KEY` thật cho môi trường dev, viết `.env.example` ở gốc repo (hiện rỗng), dọn entry cũ `backend/.env`, `frontend/.env` trong `.gitignore`.

**Gate 0:** `docker compose up -d` dựng được postgres + redis + api + worker + mailhog + nginx; `curl /api/v1/health` trả 200 qua Nginx; CI đỏ khi cố tình làm một test fail.

### Phase 1 — Nền dữ liệu (5–7 ngày công)

Điều kiện tiên quyết: Gate 0. **Mục tiêu:** schema thật khớp [ERD](ERD.md), có dữ liệu để đo hiệu năng.

- [x] **1.1** `alembic init`, viết `env.py` async đọc `settings.DATABASE_URL`, điền `alembic.ini` (đang rỗng).
- [x] **1.2** Models SQLAlchemy cho 24 bảng theo ERD; mixin chung `created_at/updated_at`, `deleted_at/deleted_by`, `row_version`; enum trạng thái đúng danh sách ở [ERD §4](ERD.md).
- [x] **1.3** Migration #1 với toàn bộ ràng buộc: FK `ON DELETE RESTRICT`; CHECK giá/diện tích/tỷ lệ/số tiền; 4 partial unique index (`listings.property_id`, `contracts.property_id`, `kyc_verifications.customer_id`, `signing_challenges.party_id`) và UNIQUE toàn cục cho `users.email`; 4 UNIQUE phụ trợ cho FK ghép theo [ERD §5.1](ERD.md); FK ghép cho `contract_signatures`, `commissions`, `contract_versions`.
- [x] **1.4** Chỉ mục truy vấn theo [ERD §7](ERD.md).
- [x] **1.5** `scripts/seed.py`: seed 3 role + permission, 3 tài khoản demo, và ≥ 2.000 bản ghi dự án/căn hộ/tin/khách hàng phục vụ NFR-04/NFR-06.
- [x] **1.6** `tests/integration/test_schema_invariants.py`: trùng email, trùng `(project_id, unit_code)`, cặp `sale/month`, hai tin `pending` cùng căn, hai hợp đồng giữ cùng căn, challenge của party khác.

**Gate 1:** `alembic upgrade head` trên database sạch; `make seed` xong và `COUNT(*) ≥ 2000`; test invariant đỏ nếu xóa một index bất kỳ (kịch bản 2–5 của [ERD §9](ERD.md)).

### Phase 2 — Tài khoản, RBAC, audit (6–8 ngày công)

Điều kiện tiên quyết: Gate 1. Bao phủ FR-01, FR-02, FR-07 (một phần), FR-16.

- [x] **2.1** `core/security.py`: băm mật khẩu, tạo/giải mã JWT với `sub/exp/iat/auth_version`.
- [x] **2.2** `core/permissions.py` + `dependencies.py`: registry permission, `get_current_user` (kiểm `status`, `deleted_at`, `auth_version`), `require_permission`, helper scope bản ghi.
- [x] **2.3** `core/exceptions.py` map lỗi nghiệp vụ sang `AppError` sẵn có; `core/logging.py` structured log + redaction mật khẩu/token/OTP.
- [x] **2.4** Module `auth`: `register`, `token`, `logout` (tăng `auth_version`), `password-reset/request`, `password-reset/confirm`, `GET/PATCH /me`.
- [x] **2.5** Module `users` + `roles`: Admin tạo tài khoản môi giới kèm hồ sơ, gán role, `lock`/`unlock`, cập nhật có `row_version`.
- [x] **2.6** Module `customers` + `agents`: hồ sơ, scope "khách trong giao dịch phụ trách" theo [SP-01](SPEC.md).
- [x] **2.7** Module `audit_logs`: service ghi audit **trong cùng transaction** nghiệp vụ + API tra cứu có phân trang.
- [x] **2.8** Cấu hình rate limit cho `login`/`reset` vào middleware đã có; xác nhận route nhạy cảm fail closed.

**Gate 2:** T-01, T-02 (phần hồ sơ), T-13 pass; 3 tài khoản demo đăng nhập đúng quyền; token cũ bị từ chối sau logout/khóa/đổi role; payload `role` do client gửi bị bỏ qua.

### Phase 3 — Danh mục, tin đăng, tìm kiếm (6–8 ngày công)

Điều kiện tiên quyết: Gate 2. Bao phủ FR-03, FR-04, FR-05, FR-06 và một phần NFR-03.

- [x] **3.1** Module `projects`: CRUD, soft-delete, chặn xóa khi còn căn chưa xóa, chặn `inactive` khi có căn `reserved`.
- [x] **3.2** Module `properties`: CRUD trong dự án, chặn sửa trạng thái `reserved/sold/rented` bằng tay, chặn xóa khi có tin/hợp đồng hoạt động.
- [x] **3.3** Module `listings`: 6 lệnh `submit/withdraw/approve/reject/edit/close` theo bảng chuyển trạng thái [SP-02](SPEC.md), lưu `reviewed_by/reviewed_at/rejection_reason`.
- [x] **3.4** Endpoint public `GET /public/listings`, `/public/listings/{id}` với projection công khai; validate bộ lọc giá theo `sale/rent`.
- [x] **3.5** Cache Redis cho danh mục dự án/địa bàn + invalidate sau commit; tách namespace khỏi broker.
- [x] **3.6** Test T-03 và ranh giới quyền: môi giới không duyệt được tin, không sửa tin người khác.

**Gate 3:** T-03 pass; biết UUID tin `draft` vẫn không đọc được qua API public; đo p95 sơ bộ của `/public/listings` trên seed 2.000 bản ghi.

### Phase 4 — Job, outbox, worker, tệp (5–6 ngày công)

Điều kiện tiên quyết: Gate 2 (không cần Gate 3). Phải xong **trước** Phase 6. Bao phủ FR-15, NFR-08.

- [ ] **4.1** Module `notifications`: bảng `jobs`, `outbox_events`, `email_deliveries`; API `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry` với scope chủ job.
- [ ] **4.2** `app/workers/celery.py`: Celery app đọc `settings.REDIS_URL`; dispatcher lấy outbox theo lease và chỉ đánh dấu `published` sau khi broker nhận.
- [ ] **4.3** Retry có `max_attempts`/backoff, `error_code` đã làm sạch, task đối soát job `pending/running` quá hạn.
- [ ] **4.4** `integrations/email/service.py` gửi qua MailHog; `email_tasks` cho reset mật khẩu (nối vào 2.4) với một job một recipient.
- [ ] **4.5** `integrations/file_storage/service.py` kho private; API `POST /files`, `GET /files/{id}/download` kiểm `purpose` và quan hệ chủ sở hữu, trả `Content-Disposition: attachment` và `nosniff`.
- [ ] **4.6** Test T-12: giả lập Redis/SMTP lỗi sau commit, kill worker giữa job, gửi lại job đã succeeded.

**Gate 4:** email reset chạy end-to-end và thấy trong MailHog; dừng worker giữa job rồi khởi động lại không tạo side effect lần hai; job lặp không nhân đôi bản ghi.

### Phase 5 — KYC (3–4 ngày công)

Điều kiện tiên quyết: Gate 4. Bao phủ FR-08.

- [ ] **5.1** `integrations/kyc/service.py`: adapter demo có nhãn, gọi ngoài transaction đang giữ khóa, lưu `provider_request_id`.
- [ ] **5.2** Module `kyc`: `POST /me/kyc`, `GET /me/kyc`, `GET /kyc` (hàng chờ Admin), `GET /kyc/{id}`, `POST /kyc/{id}/revoke`.
- [ ] **5.3** `POST /integrations/kyc/callback`: xác thực chữ ký/secret, chống replay, chỉ chuyển `pending → verified/rejected/failed`, callback trùng là no-op.
- [ ] **5.4** Logic "yêu cầu mới nhất quyết định trạng thái" + xử lý `expires_at` + timeout 15 phút thành `failed`.
- [ ] **5.5** Test T-04: callback giả, lặp, cũ, mâu thuẫn, timeout; khách không tự set `verified`.

**Gate 5:** T-04 pass; lỗi nhà cung cấp không bao giờ thành `verified`; môi giới chỉ thấy trạng thái, không tải được giấy tờ thô.

### Phase 6 — Hợp đồng và ký online (10–14 ngày công) — đường tới hạn

Điều kiện tiên quyết: Gate 3, Gate 4, Gate 5. Bao phủ FR-09, FR-10, FR-14 (phần hợp đồng), FR-16.

- [ ] **6.1** Draft và versioning: `POST /contracts`, `PATCH /contracts/{id}` tạo version mới, hai `contract_parties`, snapshot JSON chuẩn hóa, `content_hash`, tách `internal_terms` khỏi phần khách ký.
- [ ] **6.2** `POST /contracts/{id}/send-for-signing`: một transaction khóa theo thứ tự căn → tin → hợp đồng → khách; kiểm KYC, `row_version`, version mới nhất; đặt `frozen_at`, `pending_signatures`, căn `reserved`; tạo audit + job mời ký + outbox.
- [ ] **6.3** OTP: `POST /contract-parties/{id}/otp` tạo job, worker sinh mã và lưu hash HMAC, revoke mã cũ; `GET /contract-parties/{id}/challenge` chỉ chủ party đọc được.
- [ ] **6.4** `POST /contract-parties/{id}/sign`: kiểm actor/KYC/hash/TTL/lần thử; `attempt_count` tăng và commit riêng khi OTP sai; request lặp cùng party/version/hash/challenge trả kết quả đã lưu.
- [ ] **6.5** Chữ ký thứ hai hoàn tất trong một transaction: `signed`, căn `sold/rented`, tin `closed`, tạo 1 `commissions` `pending`, tạo job PDF + email.
- [ ] **6.6** `POST /contracts/{id}/cancel`: lý do, revoke challenge mở, giải phóng căn, giữ chữ ký đã có; `signed` không hủy được.
- [ ] **6.7** PDF hợp đồng: `integrations/pdf` + `contract_tasks` render từ bản frozen, lưu file private, `sha256` byte, chỉ gắn `pdf_file_id` khi file `ready`; tải có kiểm quyền.
- [ ] **6.8** Test T-05, T-06, T-07, T-08 và kịch bản E2E-01, E2E-02, E2E-05.

**Gate 6:** hai hợp đồng gửi ký đồng thời chỉ một thành công; hai bên ký đồng thời tạo đúng 2 chữ ký, 1 hoa hồng, 1 job PDF; không tồn tại căn `reserved` khi hợp đồng còn `draft`; PDF không chứa `internal_terms`.

### Phase 7 — Hoa hồng và hóa đơn (4–5 ngày công)

Điều kiện tiên quyết: Gate 6. Bao phủ FR-11, FR-17, FR-14 (phần chứng từ).

- [ ] **7.1** Module `commissions`: đọc theo scope (môi giới chỉ khoản của mình), `approve`, `pay` (cần `commission.pay` + `payment_reference`), `cancel` kèm lý do.
- [ ] **7.2** Bất biến hoa hồng: không sửa `base/rate/amount` sau khi tạo; khách không nhận trường hoa hồng ở bất kỳ response/export/PDF nào.
- [ ] **7.3** Module `invoices`: tạo draft từ hợp đồng `signed`, `issue` (đóng băng snapshot + job PDF), `pay` toàn bộ, `void` kèm lý do.
- [ ] **7.4** Test T-09: gửi lại `approve`/`pay` không ghi nhận hai lần; tham chiếu khác gây 409; làm tròn khớp ví dụ `2.000.000.000 × 1,5% = 30.000.000`.

**Gate 7:** T-09 pass; một hợp đồng không bao giờ có hai khoản hoa hồng; hóa đơn `issued` không sửa được nội dung.

### Phase 8 — Báo cáo, nhập/xuất (5–7 ngày công)

Điều kiện tiên quyết: Gate 7. Bao phủ FR-12, FR-13, FR-14 (phần báo cáo).

- [ ] **8.1** `GET /reports/dashboard` theo định nghĩa chỉ số [PRD §7](PRD.md): số tin, số hợp đồng, hợp đồng ký trong kỳ, hoa hồng; loại `deleted_at`; không đếm trùng do join.
- [ ] **8.2** Quy đổi `from_date/to_date` giờ Việt Nam sang UTC `[đầu from_date, đầu ngày sau to_date)`; trả `generated_at` và bộ lọc đã áp dụng.
- [ ] **8.3** Cache báo cáo TTL ≤ 60 giây, khóa chứa user/scope/quyền/bộ lọc; không dùng chung cache Admin và môi giới.
- [ ] **8.4** Import `projects`/`properties`: `.xlsx`/`.csv`, giới hạn 10 MB/5.000 dòng, chặn macro/công thức/external link, validate toàn bộ rồi ghi all-or-nothing, retry không nhập lần hai.
- [ ] **8.5** Export Excel/CSV/PDF theo scope qua job: allowlist cột, ô bắt đầu `=`, `+`, `-`, `@` xuất dạng text, worker kiểm tra lại quyền lúc xử lý và lúc tải.
- [ ] **8.6** Test T-10, T-11 và kịch bản E2E-08.

**Gate 8:** import một dòng sai thì không có bản ghi nghiệp vụ nào được thêm; dashboard khớp dữ liệu seed ở ranh giới ngày Việt Nam; export không lộ hoa hồng cho khách.

### Phase 9 — Frontend (12–16 ngày công, song song từ sau Gate 2)

Điều kiện tiên quyết: Gate 2 cho slice đầu; mỗi slice sau bám gate backend tương ứng.

- [ ] **9.1** Nền: router, layout theo vai trò, session store giữ token trong bộ nhớ, API client (envelope lỗi, `row_version`, `X-Request-ID`, 401 → đăng nhập lại).
- [ ] **9.2** Bộ trạng thái dùng chung: Loading, Empty, Forbidden, Validation, Conflict, Unavailable, Success; bảng có phân trang/sắp xếp phía server.
- [ ] **9.3** Slice tìm tin công khai + chi tiết tin (sau Gate 3).
- [ ] **9.4** Slice đăng nhập/đăng ký/quên mật khẩu/hồ sơ (sau Gate 2).
- [ ] **9.5** Slice môi giới: tin của tôi, tạo/sửa/gửi duyệt, hợp đồng phụ trách, hoa hồng của tôi (sau Gate 3, Gate 7).
- [ ] **9.6** Slice khách hàng: KYC của tôi, hợp đồng của tôi, xem nội dung và ký OTP, tải PDF, hóa đơn của tôi (sau Gate 6).
- [ ] **9.7** Slice Admin: hàng chờ duyệt tin, danh mục, hồ sơ/KYC, hợp đồng, hóa đơn, duyệt hoa hồng, audit, nhập/xuất (sau Gate 8).
- [ ] **9.8** Slice dashboard theo phạm vi quyền (sau Gate 8).

**Gate 9:** mỗi màn hình hiển thị đúng 7 trạng thái; không có màn hình nào fallback sang dữ liệu giả khi API lỗi; giao diện tiếng Việt, giờ Việt Nam, tiền VND nhất quán.

### Phase 10 — Siết chặt và bàn giao (5–7 ngày công)

Điều kiện tiên quyết: Gate 8, Gate 9. Bao phủ NFR-01, NFR-02, NFR-04, NFR-05, NFR-09.

- [ ] **10.1** Security pass: chạy T-02 toàn diện trên mọi module; CORS allowlist; escape nội dung tin đăng; kiểm log không chứa mật khẩu/token/OTP/KYC.
- [ ] **10.2** Đo hiệu năng NFR-04: p95 của list/search với ≥ 2.000 bản ghi và 20 user đồng thời; ghi cấu hình máy, thời lượng, kết quả.
- [ ] **10.3** Nâng coverage đạt ngưỡng CI ≥ 40% và xuất báo cáo coverage làm bằng chứng.
- [ ] **10.4** Xuất OpenAPI từ implementation + Postman collection; tạo `docs/API.md` và đối chiếu với [SPEC §11](SPEC.md).
- [ ] **10.5** Tạo `docs/DEPLOYMENT.md`: yêu cầu môi trường, biến cấu hình, chạy migration, seed, tài khoản demo, troubleshooting.
- [ ] **10.6** Mẫu hợp đồng, ảnh dashboard, video demo 5–10 phút theo bộ bàn giao [PRD §9](PRD.md).
- [ ] **10.7** Cập nhật `README.md` (hiện bị cắt giữa code block) và rà lại nhãn trạng thái trong [ARCHITECTURE](ARCHITECTURE.md) cho khớp mã nguồn cuối cùng.

**Gate 10:** bộ bàn giao PRD §9 đủ món; mọi tiêu chí P0 có bằng chứng kiểm chứng; không còn lỗi chặn luồng chính hoặc lộ dữ liệu ngoài quyền.

---

## 4. Truy vết yêu cầu sang phase

| Yêu cầu | Phase | Ghi chú |
| --- | --- | --- |
| FR-01, FR-02 | 2 | Gate 2 dùng T-01 |
| FR-03, FR-04 | 3 | |
| FR-05, FR-06 | 3 | |
| FR-07 | 2 (hồ sơ), 5 (trạng thái KYC cho môi giới) | |
| FR-08 | 5 | |
| FR-09 | 6 | slice 6.1–6.6 |
| FR-10 | 6 | slice 6.7 |
| FR-11 | 7 | sinh khoản ở 6.5, vòng đời ở 7.1 |
| FR-12 | 8 | |
| FR-13 | 8 | import 8.4, export 8.5 |
| FR-14 | 6, 7, 8 | PDF hợp đồng, hóa đơn, báo cáo |
| FR-15 | 4 | email OTP nối ở 6.3 |
| FR-16 | 1, 2 | audit 2.7, soft-delete/`row_version` 1.2–1.3 |
| FR-17 | 7 | |
| FR-18 (P1) | — | cắt khỏi MVP, xem mục 5 |
| NFR-01 | 2, 3, 10 | |
| NFR-02 | 2, 4, 10 | |
| NFR-03 | 3, 4 | |
| NFR-04 | 10 | dữ liệu đo có từ 1.5 |
| NFR-05 | 0 (gate), mọi phase | |
| NFR-06 | 0, 1 | |
| NFR-07 | 0 | |
| NFR-08 | 0, 4 | |
| NFR-09 | 10 | |

| Bộ kiểm chứng | Phase đạt |
| --- | --- |
| T-01, T-02 (hồ sơ), T-13 | 2 |
| T-03 | 3 |
| T-12 | 4 |
| T-04 | 5 |
| T-05, T-06, T-07, T-08 | 6 |
| T-09 | 7 |
| T-10, T-11 | 8 |
| T-02 (toàn diện) | 10 |

## 5. Thứ tự cắt giảm nếu thiếu thời gian

Cắt theo thứ tự này và **phải ghi rõ trong báo cáo**, không để tài liệu ghi P0 mà sản phẩm không có:

1. FR-18 2FA đăng nhập — đã là P1 trong PRD, cắt không ảnh hưởng nghiệm thu.
2. Export PDF báo cáo (giữ PDF hợp đồng và hóa đơn vì FR-10/FR-17 là P0).
3. Import Excel (task 8.4) — giữ export; import là phần nặng nhất của FR-13.
4. Thông báo in-app — yêu cầu gốc cho phép chọn email.

Không được cắt: ký hợp đồng online có bằng chứng và phiên bản (FR-09/FR-10), giữ căn không trùng (A-07), phân quyền theo hành động và bản ghi (FR-02). Đây là ba thứ đề bài dùng để phân biệt bài làm.

## 6. Ánh xạ mốc PRD và tổng ước lượng

| Mốc [PRD §9](PRD.md) | Phase | Ngày công |
| --- | --- | --- |
| M1 — Nền tảng | 0, 1, 2 | 14–19 |
| M2 — Danh mục/tin | 3 | 6–8 |
| M3 — Giao dịch | 4, 5, 6, 7 | 22–29 |
| M4 — Hoàn thiện | 8, 10 | 10–14 |
| Song song | 9 — frontend | 12–16 |
| **Tổng** | | **62–83** |

Đường tới hạn là Phase 0 → 1 → 2 → 4 → 5 → 6 → 7 → 8 → 10. Phase 3 có thể chen vào sau Gate 2 mà không chặn Phase 4. Phase 9 bám sau từng gate backend.

## 7. Định nghĩa "xong" cho một module nghiệp vụ

Một module chỉ được tick khi có đủ:

1. `router.py` chỉ map HTTP, không chứa business rule.
2. `service.py` sở hữu transaction, kiểm permission theo hành động **và** scope bản ghi.
3. `repository.py` truy vấn tham số hóa, khóa bản ghi đúng thứ tự, update có điều kiện `row_version`.
4. `schemas.py` không nhận `status`, `signed_at`, `paid_at`, `role` từ client.
5. Audit ghi trong cùng transaction cho mọi lệnh nhạy cảm.
6. Unit test cho service và integration test cho ràng buộc/quyền.
7. OpenAPI hiển thị đúng request/response, mã lỗi theo [SPEC §3.2](SPEC.md).

Thiếu mục 6 thì coi như chưa xong: [PRD §3](PRD.md) ghi rõ ẩn nút trên giao diện không phải phân quyền.

## 8. Điểm cần chốt khi review

| # | Vấn đề | Mặc định tôi dùng trong plan |
| --- | --- | --- |
| Q1 | Thư viện tạo PDF | **đã chốt**: WeasyPrint 70.0 + Jinja2 (HTML → PDF, giữ được layout hợp đồng và dấu tiếng Việt); Dockerfile đã cài pango/cairo/fonts-dejavu |
| Q2 | Kho tệp riêng tư | volume Docker cho MVP, giao diện adapter giữ nguyên để đổi sang S3-compatible sau |
| Q3 | Nginx trong compose ngay Phase 0 hay để Phase 10 | làm ở 0.3 để luồng tải tệp và CORS được kiểm chứng sớm |
| Q4 | Frontend router/state | chưa chốt thư viện; task 9.1 cần quyết định trước khi bắt đầu |
| Q5 | Năng lực thực tế mỗi tuần | plan chỉ cho ngày công; cần bạn cho số giờ/tuần để quy ra ngày lịch và mốc bảo vệ |
| Q6 | Có làm `/ready` ngoài `/health` | đề xuất có, nằm trong 0.6/4.3 |

---

## 9. Nhật ký thực hiện

### Phase 0 + Phase 1 — hoàn thành 17/09/2026

Đã kiểm chứng bằng lệnh, không phải chỉ viết file:

| Việc | Bằng chứng |
| --- | --- |
| Build image backend | `docker compose build api` thành công sau khi sửa `CMD` của Dockerfile |
| Dựng stack | `docker compose up -d --wait postgres redis api` khỏe; `frontend` và `nginx` chạy |
| Reverse proxy | Qua Nginx: `/health` trả 200 và giữ nguyên `X-Request-ID` client gửi, `/docs` 200, `/` trả React 200 |
| Migration | `alembic upgrade head` trên database sạch tạo **24 bảng** nghiệp vụ + `alembic_version` |
| Kiểu thời gian | 72 cột `timestamptz`, 0 cột `timestamp without time zone` |
| Ràng buộc | 4 partial unique index và 4 FK ghép có mặt trong `pg_constraint`/`pg_indexes` |
| Seed | `make seed` tạo **2.798 bản ghi** (211 tài khoản, 10 môi giới, 200 khách, 20 dự án, 1.200 căn, 900 tin) và 3 tài khoản demo |
| Test | 18 test pass (5 middleware + 13 invariant database) |
| Coverage | 92,93% line, vượt gate 40% |
| Lint và type | `ruff check`, `ruff format --check`, `mypy app` đều sạch |

### Quyết định và sai lệch so với bản plan

1. **WeasyPrint được chọn cho PDF** (Q1). Dockerfile cài thêm `libpango`, `libcairo`, `fonts-dejavu-core`; CI cài cùng bộ này trước khi chạy test.
2. **Service `worker` đặt sau compose profile `worker`.** `app/workers/celery.py` còn rỗng nên nếu để mặc định thì `docker compose up` sẽ đỏ. Bỏ `profiles` ở Phase 4 khi có mã worker.
3. **Thêm module `app/modules/files/`** làm chủ sở hữu bảng `files`. Skeleton ban đầu không có module này nhưng mỗi bảng cần đúng một module ghi; SPEC mục 11 đã có nhóm endpoint tệp.
4. **Kéo sớm phần băm mật khẩu của task 2.1** vào `app/core/security.py` vì seed cần tạo tài khoản demo. Phần JWT vẫn thuộc Phase 2.
5. **`JWT_SECRET_KEY` không còn giá trị mặc định.** `Settings` bắt buộc biến môi trường này, nên ứng dụng dừng ngay khi thiếu thay vì chạy với `change-me` (đóng rủi ro R13 của ARCHITECTURE).
6. **Cổng publish ở máy phát triển được đổi** trong `.env` cục bộ (`55432`, `56379`, `58000`, `55173`, `58080`) vì 5432/6379/8000 đang bị một project khác chiếm. Cổng trong mạng nội bộ compose không đổi.
7. **`users.locked_at` là cột mới** so với bản ERD trước; đã bổ sung vào từ điển dữ liệu ERD mục 4.

### Việc còn treo sau Phase 1 — trạng thái

- Rate limit `/auth/token` và `/auth/password-reset/request` đã dùng tiền tố `/api/v1` (đóng ở Phase 2).
- CI thật trên GitHub Actions vẫn chưa chạy.
- `docs/API.md` và `docs/DEPLOYMENT.md` vẫn thuộc task 10.4, 10.5.

### Phase 2 — hoàn thành 25/09/2026

| Việc | Bằng chứng |
| --- | --- |
| T-01 | `test_auth_flow.py`: đăng ký bỏ qua role client gửi, reset dùng một lần, JWT cũ bị thu hồi sau logout/reset |
| T-02 (hồ sơ) | `test_rbac_scope.py`: môi giới chỉ thấy khách trong scope, ngoài scope trả 404 |
| T-13 | `test_audit_logs.py`: audit đúng actor, không chứa secret, router chỉ đọc |
| Token bị thu hồi | Sau logout/khóa/đổi role token cũ trả 401 (pytest và Postman) |
| Kiểm thử API | Postman collection `postman/` chạy bằng Postman CLI, lịch sử ở tab Runs và `postman/history.csv` |

Sửa trong lúc kiểm thử:

1. Tài khoản demo đổi từ `@demo.local` sang `@demo.com`: `email-validator` từ chối tên miền dành riêng nên tài khoản demo không gọi được quên mật khẩu.
2. `GET /me` trả thêm `row_version`, trước đó client không có giá trị để gửi `PATCH /me`.
3. Rate limit sau Nginx: uvicorn không tin `X-Forwarded-For` nên mọi request qua Nginx chung một bucket IP. Compose cố định IP Nginx (`NGINX_IP`), api chỉ tin header từ IP đó (`FORWARDED_ALLOW_IPS`), Nginx ghi đè `X-Forwarded-For $remote_addr`.

### Phase 3 — hoàn thành 25/09/2026

| Việc | Bằng chứng |
| --- | --- |
| API | `projects`, `properties`, `listings` (6 lệnh trạng thái), `GET /public/listings`, `/public/listings/{id}`, `/public/catalog` |
| T-03 | `test_public_listings.py`: tin draft/pending/rejected/closed trả 404 dù biết UUID; căn reserved hoặc dự án inactive bị ẩn; lọc giá/sắp xếp giá bắt buộc chọn bán hoặc thuê |
| Quyền (3.6) | `test_listings.py`: môi giới không duyệt/từ chối được tin (403), không đọc/sửa tin của môi giới khác (404), không lập tin dưới tên người khác |
| Xóa có phụ thuộc | `test_catalog.py`, `test_listings.py`: dự án còn căn, căn còn tin chưa đóng hoặc hợp đồng đã ký, tin gắn hợp đồng đều trả 409 `DEPENDENCY_EXISTS` |
| Cache (3.5) | Danh mục công khai cache Redis `real_estate:cache:catalog:v1`, TTL 60 giây, xóa sau commit khi dự án đổi; Redis lỗi thì đọc thẳng DB |
| Test | 99 test pass; coverage 93% line |
| Postman | Thêm thư mục "05 Danh mục và tin đăng": 71 request, 324 assertion pass (chế độ local) |
| p95 sơ bộ (Gate 3) | `GET /public/listings` trên 640 tin công khai của seed, 20 client đồng thời, 800 request trộn bộ lọc: danh sách p95 123 ms, chi tiết p95 69 ms, chung p95 120 ms. Máy Apple M1 Pro, Docker 4 CPU/4 GB; đo không qua rate limiter (giới hạn mặc định 100 request/phút/IP sẽ chặn tải từ một máy) |

Quyết định và sai lệch:

1. **Danh mục địa bàn cấu hình trong mã** (`app/modules/projects/locations.py`), dùng chung cho validate, bộ lọc công khai và seed. ERD không có bảng địa bàn.
2. **Đọc danh mục nội bộ** cho người có `project.manage`, `property.manage` hoặc `listing.manage`; khách hàng dùng API công khai.
3. **`listing.approve` là mốc "thấy mọi tin"**: người có quyền duyệt quản lý mọi tin, người chỉ có `listing.manage` bị giới hạn về tin của hồ sơ môi giới của mình.
4. **PATCH từng phần** cho dự án, căn, tin; `code` dự án, `project_id`/`unit_code` căn và `property_id`/`agent_id` tin không sửa được sau khi tạo. Sửa tin approved/rejected tự đưa về draft và bỏ thông tin duyệt.
5. **DELETE nhận `row_version` qua query string** vì DELETE không có body.
6. **Tạo tin nháp cũng kiểm tra căn available và dự án active** theo tiền điều kiện UC-07; submit và approve kiểm tra lại, khóa dòng căn trước khi đổi trạng thái tin (thứ tự căn → tin như task 6.2).
7. **Projection công khai không có thông tin môi giới.** PRD không yêu cầu hiển thị liên hệ; thêm sau nếu cần.
8. **Coverage bật `concurrency = ["greenlet", "thread"]`**: SQLAlchemy async chạy qua greenlet, thiếu cấu hình này coverage bỏ sót dòng sau `await` và báo thấp hơn thực tế.
9. **Sửa test flaky có từ trước** `test_token_sai_secret_bi_tu_choi`: test đổi ký tự base64url cuối của chữ ký, ký tự này chỉ mang 4 bit nên đôi khi chữ ký không đổi.
10. **Micro ORM cho toàn bộ backend (ADR-011).** Repository của mọi module (Phase 2 và 3) viết SQL tay qua `text()` và trả dataclass; code trong `app/` không còn import model ORM, model chỉ dùng cho Alembic, test factory và seed; `conditional_update` được thay bằng `app/common/db.py::update_versioned`. Phase 4 trở đi viết theo cách này. Đo lại `/public/listings` sau khi chuyển Phase 3: p95 116 ms, p50 40 ms (trước 56 ms), throughput 392 request/giây (trước 299). Thêm test cho các đường SQL mới viết: `updated_at` sau khi sửa, đổi role thu hồi token cũ (trước đó chỉ có ở Postman), danh sách tài khoản, hồ sơ môi giới, bộ lọc audit.

### Chưa đạt theo định nghĩa "xong" ở mục 7

- Mục 6 yêu cầu unit test cho service; Phase 2 và Phase 3 mới có integration test qua HTTP và DB thật.
- Mục 7 yêu cầu OpenAPI hiển thị mã lỗi theo SPEC §3.2; router chưa khai báo `responses` cho 401/403/404/409/422.

---

**Tài liệu liên quan:** [PRD](PRD.md) · [SPEC](SPEC.md) · [ERD](ERD.md) · [USE_CASES](USE_CASES.md) · [ARCHITECTURE](ARCHITECTURE.md) · [Yêu cầu gốc](yeu_cau.pdf)
