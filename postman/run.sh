#!/usr/bin/env bash
# Chạy Postman collection và lưu lịch sử.
#
# - Mặc định (POSTMAN_MODE=cloud): Postman CLI chạy bản collection/environment trên
#   workspace Postman, kết quả hiện ở tab Runs của collection. Cần `postman login`.
# - POSTMAN_MODE=local: Newman chạy file JSON trong repo, không gửi gì lên Postman.
#
# Cả hai chế độ đều lưu báo cáo HTML + JSON ở postman/reports/<timestamp>.* (chỉ giữ
# ở máy) và thêm một dòng tóm tắt vào postman/history.csv (được commit).
set -uo pipefail

cd "$(dirname "$0")"
mode="${POSTMAN_MODE:-cloud}"
workspace_id="${POSTMAN_WORKSPACE_ID:-10ce84cc-f869-4a27-8952-92f522ed55ee}"
collection_name="${POSTMAN_COLLECTION_NAME:-Real Estate Management}"
environment_name="${POSTMAN_ENVIRONMENT_NAME:-Real Estate — local (Nginx)}"
stamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p reports

# Tìm ID trên workspace theo tên: import lại collection (Replace hoặc bản mới)
# không làm lệnh chạy nhầm bản cũ. Đặt POSTMAN_*_ID để bỏ qua bước tra cứu.
cloud_id() {
  local kind="$1" name="$2"
  postman "$kind" list --workspace "$workspace_id" --json |
    node -e '
      let raw = ""; process.stdin.on("data", c => raw += c).on("end", () => {
        const hits = JSON.parse(raw).filter(item => item.name === process.argv[1]);
        if (hits.length !== 1) {
          console.error(`Cần đúng 1 ${process.argv[2]} tên "${process.argv[1]}" trên workspace, thấy ${hits.length}`);
          process.exit(1);
        }
        console.log(hits[0].id);
      });
    ' "$name" "$kind"
}

case "$mode" in
  cloud)
    collection_id="${POSTMAN_COLLECTION_ID:-$(cloud_id collection "$collection_name")}" || exit 1
    environment_id="${POSTMAN_ENVIRONMENT_ID:-$(cloud_id environment "$environment_name")}" || exit 1
    postman collection run "$collection_id" \
      -e "$environment_id" \
      --reporters cli,json,html \
      --reporter-json-structure newman \
      --reporter-json-export "reports/${stamp}.json" \
      --reporter-html-export "reports/${stamp}.html" \
      "$@"
    ;;
  local)
    npx --yes -p newman@6 -p newman-reporter-htmlextra@1 newman run real-estate-api.postman_collection.json \
      -e local.postman_environment.json \
      --reporters cli,htmlextra,json \
      --reporter-htmlextra-export "reports/${stamp}.html" \
      --reporter-htmlextra-title "Real Estate API — ${stamp}" \
      --reporter-json-export "reports/${stamp}.json" \
      "$@"
    ;;
  *)
    echo "POSTMAN_MODE phải là cloud hoặc local" >&2
    exit 2
    ;;
esac
status=$?

if [[ -f "reports/${stamp}.json" ]]; then
  [[ -f history.csv ]] || echo "run_at,git_commit,requests,requests_failed,assertions,assertions_failed,avg_response_ms,result" > history.csv
  commit="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
  [[ -n "$(git status --porcelain -- .. 2>/dev/null)" ]] && commit="${commit}-dirty"
  node -e '
    const run = require(process.argv[1]).run;
    const s = run.stats;
    const result = s.requests.failed + s.assertions.failed === 0 ? "PASS" : "FAIL";
    console.log([process.argv[2], process.argv[3], s.requests.total, s.requests.failed,
      s.assertions.total, s.assertions.failed, Math.round(run.timings.responseAverage), result].join(","));
  ' "./reports/${stamp}.json" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$commit" >> history.csv
  echo "Báo cáo: postman/reports/${stamp}.html — lịch sử: postman/history.csv (chế độ ${mode})"
fi

exit $status
