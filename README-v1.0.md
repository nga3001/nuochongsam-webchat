# Chatbot Bình Vị Thái Minh — Bản chính thức v1.0 (03/09/2026)

Bot tư vấn – bán hàng TPBVSK Bình Vị Thái Minh trên Facebook Messenger + bình luận (qua Pancake), kèm web chat test nội bộ, trang admin, báo cáo A/B bot-vs-người, nhịp theo đuổi, bảng tình trạng và kill switch.
Công ty Cổ phần Dược phẩm Thái Minh · Người quyết định: anh Na (CEO) · Trợ lý xây dựng: Chi.

## v1.0 là gì
Đóng băng mã nguồn tại commit `3b0613c` (= v0.5.42, tag `v1.0`) đang chạy thật trên page "Thảo Dược Cho Dạ Dày Khỏe". Không đổi hành vi. Từ đây: sửa lỗi = v1.0.x, thêm chức năng = v1.1.

## Nội dung gói bàn giao (`Kết quả\Ban giao v1.0`)
| File | Dành cho |
|---|---|
| `binhvi-chatbot-v1.0-source.zip` | Mã nguồn đầy đủ (không chứa `.git`/token) + `AI-README.md` + thư mục `docs/` (5 tài liệu dạng .md) |
| `01-Danh-sach-chuc-nang-v1.0.docx` | Ban lãnh đạo, PM — bot làm được gì, cố ý không làm gì, việc còn mở |
| `02-Nhat-ky-thay-doi-v0.1-den-v1.0.docx` | Kỹ thuật, PM — 45 bản trong 17 ngày, vì sao và làm gì |
| `03-Huong-dan-su-dung-cho-nguoi-v1.0.docx` | Đội CSKH (Phần A), anh Na/quản trị (Phần B), guardrail 12 ca (Phần C) |
| `04-Huong-dan-cho-AI-v1.0.md` | Bất kỳ AI/agent nào được giao sửa hoặc nhân bản bot — đọc trước khi chạm code |
| `05-Huong-dan-phat-trien-chatbot-san-pham-khac.docx` | Kế hoạch nhân bản sang Vương Bảo, Tràng Phục Linh, KingsUp… |
| `README-v1.0.md` | File này |

## Chạy nhanh
```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   SECRET_PATH=... ADMIN_KEY=... DB_PATH=./data.db
uvicorn main:app --port 8000
# web test: /c/<SECRET_PATH>   admin: /a/<ADMIN_KEY>   báo cáo A/B: /a/<ADMIN_KEY>/ab
```
Không có `ANTHROPIC_API_KEY` → demo mode. Nối Pancake cần thêm bộ ENV `PANCAKE_*` (xem tài liệu 03, mục B6).

## Sản xuất
GitHub `anhhn-ship-it/binhvi-webchat` (nhánh `main`) → Railway tự deploy. Clone làm việc trên máy anh Na: `D:\Claude\Chatbot\repo\binhvi-webchat` (chứa token — không chia sẻ folder này).
