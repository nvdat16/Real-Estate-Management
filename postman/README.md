# Postman — kiểm thử API

| File | Vai trò |
| --- | --- |
| `real-estate-api.postman_collection.json` | Collection Phase 2: auth, RBAC, quản lý tài khoản, CRM, audit (Gate 2) |
| `local.postman_environment.json` | Môi trường local qua Nginx (`http://localhost:58080`) và tài khoản demo |
| `run.sh` | Chạy collection (Postman CLI trên cloud hoặc Newman local), lưu báo cáo và ghi lịch sử |
| `history.csv` | Mỗi lần chạy một dòng: thời điểm (UTC), commit, số request/assertion, số lỗi, kết quả |
| `reports/` | Báo cáo HTML/JSON chi tiết từng lần chạy — chỉ giữ ở máy, không commit |

## Chạy

```bash
make up && make migrate && make seed   # lần đầu
make api-test                          # chạy bản trên Postman Cloud, kết quả lên tab Runs
POSTMAN_MODE=local make api-test       # chạy file JSON trong repo bằng Newman, không gửi lên cloud
```

Chế độ mặc định cần Postman CLI (`brew install --cask postman-cli`) và `postman login` bằng API key cá nhân (chạy trong terminal riêng, không dán key vào đâu khác). Collection và environment chạy theo ID trên workspace; đổi bằng `POSTMAN_COLLECTION_ID`/`POSTMAN_ENVIRONMENT_ID`.

**File JSON trong repo là bản gốc.** Chế độ cloud chạy bản đã import lên Postman, nên sau khi sửa file JSON phải import lại (Import → chọn Replace) thì cloud mới có thay đổi.

Collection chạy tuần tự và tự tạo tài khoản mới mỗi lần (email `postman.<timestamp>@example.com`), nên chạy lặp lại được trên cùng database. Rate limit đăng nhập là 10 lần/60 giây mỗi IP; collection dùng 9 lần, nên **chờ 1 phút giữa hai lần chạy**.
