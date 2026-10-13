---
name: setup
description: Use when installing or connecting Cognee Memory remotely.
version: 0.1.1
---
# Thiết lập Cognee Memory trên máy nhận

Chỉ xử lý profile/backend người dùng chọn. Không dùng key, đường dẫn, localhost hay Brain của máy tác giả. Không tự thay provider, tắt plugin Admin hoặc bật capture.

## Cài từ link repo — không copy file/chạy installer thủ công
1. Hermes Desktop → Capabilities → Plugins → Install plugin. Dán https://github.com/lqv221998-design/hermes-plugin-cognee-remote-memory rồi Review repository.
2. Kiểm Agent cognee-remote-memory và Desktop half, đúng backend/profile, commit đã duyệt. Cài cả hai half qua UI native; không Force reinstall bản đang hoạt động.
3. Hermes/PM quản lý dependency FastAPI khai báo trong plugin.yaml sau consent. Không cài Cognee, Docker, Node package hoặc MCP trên client. Desktop cần Git hoạt động và mạng GitHub; chưa có Git là prerequisite của host, không lỗi cần custom installer.
4. Trong inventory, bật Agent và Desktop của Cognee Memory sau review. Nếu backend API mới chưa mount, restart backend/app lúc rảnh; không kill turn hiện tại. Sidebar hoặc command palette Cognee Memory mở form. Cài plugin không đồng nghĩa đã kết nối/activate.

## Kết nối riêng
- Nhập origin HTTPS của Cognee API do Admin/IT cung cấp, không có path/query/userinfo. 127.0.0.1 chỉ dùng nếu Cognee cùng máy; máy khác không kết nối Cognee máy tác giả bằng localhost. Không bỏ TLS verification; trusted CA/network/ACL là cổng riêng.
- Nhập issued API key ordinary active user qua ô secret của form, không qua chat; không key Admin. Kiểm tra và lưu kết nối chỉ đọc identity/schema/Brain ACL, không tự tạo Brain/key.
- Chọn Brain lưu có read+write nếu muốn remember; các Brain tra cứu phải có read. Chọn read Brain không thay cho dropdown write Brain. Không ghi conversation vào kho chuẩn/pháp lý. Brain chung chia sẻ hội thoại với mọi người được cấp read.
- Tra cứu trước: tắt capture, chọn read Brains/auto recall, xác nhận egress rồi Lưu lựa chọn Brain. Muốn capture phải chọn write Brain trước. Dấu tích trên form chưa chứng minh đã lưu; đọc state sau thành công.
- Xác nhận thay external provider rồi Bật Cognee Memory, mở session mới. Nếu writer cũ enabled: dừng và hỏi lựa chọn migration; không tự tắt Admin hoặc chạy hai writer. Local Hermes history vẫn tồn tại.

## Chẩn đoán / nghiệm thu
Known Windows host gate: actual Electron remote Desktop install passed; native Agent CLI publish/rename failed WinError 5 trong isolated target. Root layout/Doctor pass chưa chứng minh cả hai half install. Nếu gặp gate này, giữ source/installed state/log, báo pending host installer; không force/core-patch/registry-edit hoặc manual-copy rồi gọi native PASS. Nguyên nhân chưa xác định; physical recipient acceptance vẫn riêng.
Load cognee-remote-memory:using. Dùng host Doctor/validator nếu cần, kiểm profile/config/connection/selected Brains/new-session provider riêng. HTTP400 generic không chứng minh key sai: kiểm destination, consent, ACL, writer conflict. 404 router cần đúng enable/runtime, không nhập key lặp lại.

Chỉ nhớ/truy vấn thử khi người dùng cho phép đúng Brain; kiểm raw hash và terminal indexing, sau đó recall mới. Fixture/Doctor/connection200 không chứng minh semantic retrieval hoặc thiết bị thứ hai. Sending/uncertain/raw_verified: đối chiếu chỉ đọc, không resend/re-cognify hoặc xoá receipt.

Windows outbox dùng DPAPI current-user; ngoài Windows file0600 plaintext. API key lưu bằng lifecycle .env/quyền OS của profile, không encrypted vault. Conversation text user/assistant có thể tới LLM/embedding server; loại system/tool/file bytes, redaction theo mẫu không exhaustive. Không backfill lịch sử. Không nạp dữ liệu người dùng trong quá trình install/import.
