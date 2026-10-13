# Cognee Remote Memory 0.1.1

**Cài trực tiếp trong Hermes Desktop từ link GitHub:**

https://github.com/lqv221998-design/hermes-plugin-cognee-remote-memory

Capabilities → Plugins → Install plugin → nhập URL → **Review repository** → chọn cả **Agent** và **Desktop**, đúng backend/profile → xác nhận cài. Repo-root có `plugin.yaml`, `__init__.py`, `desktop/plugin.js`, API và bundled skills; không cần fragment, copy file, chạy `install.py` hoặc npm build.

**Hướng dẫn máy nhận:** [START-HERE-HERMES.md](START-HERE-HERMES.md). Trong chat yêu cầu: “Nạp `cognee-remote-memory:setup` và hướng dẫn tôi kết nối bằng form Cognee Memory; không tự bật capture hoặc thay provider.” Skill đi cùng plugin, không cần chép kho skills tác giả.

## Điều kiện và ranh giới

**Cổng chưa đạt trên host Windows đã kiểm:** native Electron review/probe và Desktop installer từ remote PASS (đúng bytes, unified marker, no-overwrite), nhưng native Agent CLI installer bị `WinError 5: Access is denied` khi publish/rename thư mục staged. Vì vậy chưa được tuyên bố cài hoàn chỉnh cả hai half chỉ từ URL trên host này, hoặc mọi máy nhận đều cài một lần thành công. Đây là lỗi tại host publication seam; nguyên nhân chưa xác định, không patch Hermes core/registry hay Force reinstall để vượt. Giữ pre-release; máy gặp lỗi cần giữ log và kiểm host installer, không chỉ bật UI hoặc nhập key để che lỗi Agent.

- Hermes Desktop có native repository installer, Git hoạt động và mạng GitHub. Dependency FastAPI (`>=0.115,<1`) khai báo để PM giải quyết sau consent; client không cần Cognee SDK/server, Docker, MCP, Chrome hay Node/npm riêng cho plugin.
- Bật Agent + Desktop trong inventory **Cognee Memory** sau review. Form mở từ sidebar hoặc command palette. Backend mới cần reload lúc rảnh nếu chưa mount; không kill lượt đang chạy.
- Mỗi người nhập URL HTTPS Cognee API, key ordinary active user của mình, chọn Brain và xác nhận egress/provider. Link GitHub chỉ cài mã, không cấp quyền Brain hay tự kết nối. Không có credential hay config tác giả trong repo.
- `127.0.0.1` chỉ dùng cho server cùng máy. Client máy khác cần HTTPS reachability, TLS trust và ACL do Admin/IT cung cấp. Không tự mở LAN, không tắt TLS/firewall, không dùng key Admin chung.
- Public source không cần đăng nhập GitHub để clone. Native review/pin/profile/consent vẫn giữ nguyên. Không Force reinstall bản đang hoạt động.

## Chức năng

- Remote-only trên nền integration Hermes chính thức của Cognee; wrapper/subclass giữ nguyên upstream 1.3.1 tại commit `5eb4fe9e0054f9934d0a40353129ea07ba70bc93`. Apache 2.0; **bản tùy biến cộng đồng, không Cognee-certified**.
- Explicit recall và auto-prefetch: `HYBRID_COMPLETION`, graph scope, UUID-selected Brains, context-only + references. Không fallback toàn thư viện, không đưa session_id vào query kho chuẩn.
- Automatic remember: snapshots text user/assistant khả dụng, permanent JSON `/remember`, self_improvement=false. Không system/tool/reasoning/file bytes, không backfill lịch sử. Chỉ một writer trong profile; activation chặn khi Cognee Admin/User writer cũ enabled.
- Durable SQLite outbox, dedupe/hash/raw read-back + terminal indexing evidence. `queued/sending/raw_verified/uncertain` không phải indexed; outcome uncertain không resend. Reconcile chỉ đọc, không re-cognify để tạo green.
- Windows payload mã hóa DPAPI current-user; POSIX0600 **plaintext** ngoài Windows. API key theo lifecycle `.env`/quyền OS Hermes, không encrypted vault. Regex redaction không exhaustive; shared Brain chia sẻ conversation theo ACL, không private vì session metadata.
- Tool schemas có trước provider initialization; operations vẫn gated. Prefetch cold/current question có bounded lookup, không dùng cache câu trước. Desktop đăng ký bằng contract host thật, không phụ thuộc registerSettingsPage của phiên bản mới.

## Cài xong không đồng nghĩa nghiệm thu

Kiểm connection/identity/ACL → lưu selection → activation + phiên mới → thử nhớ/truy vấn riêng theo consent. Đã được tác giả xác nhận dùng thành công trên máy hiện tại; test fixtures không thay nghiệm thu trên máy nhận. Thiết bị LAN thứ hai, cross-OS, revoke/concurrency/chi phí/semantic graph-vector coverage chưa được chứng nhận. Snapshot permanent có chi phí/latency và trùng lịch sử giữa các snapshots; không hứa exactly-once toàn server hoặc ngang Hindsight.

Conversation luôn unreviewed, không nâng thành quy định công ty/pháp lý. Không import/runtime-auto-install, không provisioning tài khoản/Brain/key, không sửa Hermes core/server/cấu hình tác giả.

## Kiểm thử

Xem [TESTING.md](TESTING.md). Bộ fork tests gồm fixture HTTP/browser, safety, outbox, lifecycle, native tools và setup registration; upstream snapshot/hash riêng trong UPSTREAM.json. Kết quả phát hành nằm tại release/report, không kèm live receipt/account screenshot/config/outbox trong source. Đây là pre-release cho đến khi máy nhận được nghiệm thu.

Nguồn: [Hermes plugins](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins), [Desktop SDK](https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk), [Cognee integrations](https://github.com/topoteretes/cognee-integrations).
