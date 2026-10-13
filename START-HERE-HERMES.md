# Hướng dẫn Hermes máy nhận

## 1. Cài từ một link

https://github.com/lqv221998-design/hermes-plugin-cognee-remote-memory

Hermes Desktop → Capabilities → Plugins → Install plugin → Repository → dán URL → Review repository.

Chọn cả Agent `cognee-remote-memory` và Desktop, đúng profile/backend; kiểm commit và warnings; xác nhận cài. Không Force reinstall/ghi đè plugin đang dùng. Public clone không cần tài khoản GitHub. Git và mạng GitHub là prerequisite của installer host. PM giải quyết FastAPI khai báo sau consent, không cần pip/npm/copy thủ công.

## 2. Mở form

Trong inventory **Cognee Memory**, bật Agent và Desktop sau review. Nếu router mới chưa mount, reload backend/app lúc rảnh. Sidebar hoặc command palette mở **Cognee Memory**. Không tìm display name bằng technical ID nếu bộ lọc không hỗ trợ.

Trong chat có thể dùng: **“Nạp cognee-remote-memory:setup và hướng dẫn tôi điền form; không tự thay provider hoặc bật capture.”**

## 3. Tự kết nối

1. Admin/IT cung cấp origin HTTPS API truy cập được từ client, ordinary-user API key và ACL Brain. Không key Admin, không copy key tác giả. Không nhập key vào chat. `127.0.0.1` của máy nhận không phải máy server khác; không có default LAN endpoint trong gói.
2. Điền URL/key trong form, **Kiểm tra và lưu kết nối**; kiểm identity/tenant và Brain directory. Kết nối không ghi corpus.
3. Chọn Brain lưu có read+write nếu muốn remember. Chọn Brain tra cứu có read. Bật options theo nhu cầu, xác nhận phạm vi chia sẻ và LLM/embedding egress, **Lưu lựa chọn Brain**. Dấu tích chưa phải saved state. Thử recall-only: tắt Tự lưu hội thoại, chọn read Brains + auto recall.
4. Xác nhận thay external memory provider của đúng profile, **Bật Cognee Memory**, mở session mới. Khi writer cũ enabled, dừng để quyết định migration; không tự tắt Admin hay lưu trùng.
5. Thử nhớ/truy vấn chỉ trong Brain được người dùng cho phép; kiểm raw hash, terminal indexing và new-session recall. Sending/uncertain/raw_verified cần read-only reconcile, không resend hay xóa receipt.

## Troubleshooting

Known host gate: actual native Desktop remote probe/install PASS; native Agent CLI install trên host Windows thử riêng bị WinError 5 khi rename/publish staged tree. Chưa nghiệm thu full native install hai half trên host đó. Nếu máy nhận gặp lỗi này: giữ nguyên bản đang chạy, giữ log/exact build/profile; không Force reinstall, core/registry patch, tự copy file vào installed để gọi native PASS. Repo/Doctor/fixture green không giải quyết lỗi host. Phát hành pre-release, không hứa mọi máy chỉ một link là cài thành công.

HTTP400 generic: kiểm write Brain khi capture=true, selection đã lưu, consent, ACL và writer conflict; không mặc định key sai. HTTP404: kiểm Agent enabled/router/runtime/profile, không nhập key lặp lại. TLS/network refusal: nhờ Admin/IT sửa đúng truy cập/certificate, không insecure fallback. Không reinstall để sửa ACL/config.

Cài/enable, UI loaded, auth connection, Brain selection, provider activation và real memory acceptance là các bước riêng. Plugin không tự cấp quyền, tạo Brain hoặc provision server. Hướng dẫn không cam kết mọi máy/OS đã được kiểm.
