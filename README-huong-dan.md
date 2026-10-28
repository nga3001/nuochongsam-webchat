# Web chat test nội bộ — Agent Bình Vị Thái Minh

## MỚI trong v0.3 (20/08/2026)
- Trang chat tách 2 cửa sổ: khung chat Messenger + "Trung tâm huấn luyện chatbot AI Thái Minh" (ghi chú test, chọn model, tên người test, form GÓP Ý chỉnh sửa chatbot).
- Góp ý lưu vào bảng suggestions (SQLite), gắn tên người test + mã hội thoại + thời gian; chống spam: tối đa 10 góp ý/người/10 phút, tối thiểu 5 ký tự, bắt buộc có tên. Bot KHÔNG tự thay đổi theo góp ý — admin duyệt rồi mới cập nhật KB (human-in-the-loop).
- TRẢ LỜI NHƯ NGƯỜI THẬT: bot viết từng ý ngắn cách nhau dòng trống → hệ thống tách thành nhiều tin nhắn gửi lần lượt kèm hiệu ứng "đang gõ..." (tối đa 4 tin/lượt, khối [QR] luôn dính tin cuối); 👍👎 gắn ở tin cuối mỗi lượt; admin cũng hiển thị tách bong bóng.
- Trang admin đổi tiêu đề "Admin - Trung tâm huấn luyện Chatbot AI Thái Minh"; xem hội thoại có 2 tab: Chat và Góp ý; thêm ô thống kê góp ý; Excel xuất thêm sheet "Góp ý huấn luyện".

## MỚI trong v0.2 (20/08/2026)
Não bot được dựng lại từ 3 nguồn: (1) TÀI LIỆU CHUẨN nhãn hàng "Tài liệu Bình Vị.docx", (2) 51 hội thoại thật của nhân viên page Thảo Dược Cho Dạ Dày Khỏe, (3) cơ chế vận hành bot Meta Sahemul.
- KB chính thức: liều 2 lần x 2-3 viên trước ăn 30p, cách thuốc khác 1 GIỜ - sắt 2 GIỜ, phân liều trẻ em từ 2 tuổi, ngừng 2-4 tuần trước test HP hơi thở, tá dược (Talc/Lactose/Canxi), nghiên cứu ĐH Y HN - Quân Y 103 - 98% Tin Dùng VN.
- Chương trình chính thức: KHÁCH MỚI (1 lọ tặng hộp 20 + freeship; 2 lọ tặng trà ĐTHT...) vs ĐƠN TÁI (nước súc miệng / Bổ gan / Tinh bột nghệ); ship đơn lẻ 15.000đ. Tool build_order TỰ áp quà + phí ship theo customer_type.
- Safety mở rộng: BLOCK thêm lactose_intolerance, child_under2, adr_severe; CAUTION thêm hp_positive, serious_condition, adr_mild, child_2_11; PNCCB đổi thành "dùng được"; PNCT "khuyên không nên dùng".
- Slot-filling: build_order validate SĐT (10 số đầu 0) + địa chỉ đủ 3 phần, chỉ hỏi phần thiếu, ready_to_confirm gate.
- Post-processor strip markdown (** # • `) ở tầng code — hết lỗi ký tự thô kiểu bot Sahemul.
- Giọng điệu theo nhân viên thật: hỏi giá là báo giá ngay + 1 câu khai thác; xưng "con" với khách lớn tuổi; hiểu tiếng Việt không dấu; câu bản lề "từng dùng Bình Vị chưa?"; kịch bản xử lý chê đắt/nhà thuốc/cuộc gọi/khiếu nại theo tài liệu chuẩn.


Bản test cho team nội bộ Thái Minh: khung chat mô phỏng Facebook Messenger + chấm 👍👎 + trang admin + sửa KB không cần code. Kiến trúc kế thừa não KingsUp: LLM lo hội thoại, tool lo fact/giá/safety gate, toàn bộ tri thức nằm trong `brain/kb.json`.

## Cấu trúc

```
binhvi-app/
├── main.py               # FastAPI: route chat, feedback, admin, KB
├── engine.py             # Claude API tool-use + system prompt
├── tools_core.py         # 4 tool: kb_lookup, compliance_check, recommend, build_order
├── db.py                 # SQLite: hội thoại, tin nhắn, feedback
├── brain/
│   ├── kb.json           # NGUỒN CHÂN LÝ DUY NHẤT (giá, liều, an toàn, chương trình)
│   ├── persona.md        # Giọng điệu, format Messenger
│   ├── playbook.md       # Quy trình 7 bước, xử lý phản đối
│   └── faq.md            # FAQ theo tài liệu CSKH chính thức của nhãn hàng
├── static/index.html     # UI chat kiểu Messenger
├── static/admin.html     # UI admin
├── requirements.txt
└── Procfile              # cho Railway/Render
```

## Chạy thử trên máy (tùy chọn)

```
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...    (Windows; Linux/Mac: export ...)
uvicorn main:app --port 8000
```

Mở: `http://localhost:8000/c/test-binhvi-2026` (chat) và `http://localhost:8000/a/admin-thaiminh-2026` (admin).
Không đặt ANTHROPIC_API_KEY → chạy DEMO MODE (bot trả lời mẫu, đủ để xem giao diện).

## Deploy lên Railway (khuyến nghị — việc C4)

1. Đăng nhập railway.app (việc A2) → New Project → **Deploy from GitHub repo** (đẩy folder này lên 1 repo private) *hoặc* dùng Railway CLI: `railway init` → `railway up` ngay trong folder.
2. Vào tab **Variables**, đặt:
   - `ANTHROPIC_API_KEY` = key từ console.anthropic.com (việc A1)
   - `SECRET_PATH` = một chuỗi ngẫu nhiên dài, VD `bv-7k2m9x4qtr81`
   - `ADMIN_KEY` = chuỗi ngẫu nhiên khác, VD `qt-5rp8w3n6zk42`
   - (tùy chọn) `DEFAULT_MODEL` = `sonnet` hoặc `haiku`
3. Tab **Settings → Networking → Generate Domain** → được link dạng `https://xxx.up.railway.app`.
4. Link gửi team test: `https://xxx.up.railway.app/c/<SECRET_PATH>`
   Link admin (chỉ anh Na + đầu mối giữ): `https://xxx.up.railway.app/a/<ADMIN_KEY>`
5. Nghi lộ link → đổi giá trị `SECRET_PATH` trong Variables, service tự restart, link cũ chết ngay.

Lưu ý Railway: SQLite ghi trên filesystem của service — gắn thêm **Volume** (Settings → Volumes, mount `/app`) để log không mất khi redeploy. Nếu chưa gắn volume thì trước mỗi lần redeploy vào admin bấm Xuất Excel để giữ log.

## Cập nhật tri thức (không cần code)

- Vào trang admin → **Tải KB hiện tại** → sửa file JSON (giá, chương trình, chống chỉ định) → **Cập nhật KB** → bot dùng ngay từ tin nhắn kế tiếp.
- `programs.money_back.active` đang để `false` — bot sẽ KHÔNG hứa hoàn tiền cho tới khi anh Na xác nhận và đổi thành `true`.
- KB hiện tại là BẢN TẠM dựng từ thông tin công khai — cần anh Na duyệt giá/chương trình (việc A0).

## Đặt hard limit chi phí

console.anthropic.com → Settings → Limits → đặt monthly spend limit (VD 30 USD) + email cảnh báo.
