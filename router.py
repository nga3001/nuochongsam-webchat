"""Định tuyến model theo loại câu hỏi (chế độ 'auto' của bản test nội bộ).

Nguyên tắc (theo kế hoạch v0.5 mục P3 #26): câu đơn giản (giá, liều, điểm bán, chào hỏi,
xác nhận) → model RẺ/NHANH (haiku); câu cần chuyên môn / xử lý phản đối / chốt đơn / an toàn
→ model MẠNH (sonnet). Dùng keyword để định tuyến — rẻ, nhanh, tất định, không tốn thêm 1 lần gọi model.

Trả về model_key. Chỉ chạy khi người dùng chọn 'auto'.
"""
import re

# Câu đơn giản → model rẻ
_SIMPLE = re.compile(
    r"(giá|bao nhiêu|nhiêu|mua ở đâu|cửa hàng|địa chỉ|liều|cách dùng|dùng thế nào|mấy gói|mấy viên|"
    r"freeship|ship|giao hàng|có bán|còn hàng|hotline|"
    r"chào|hello|hi|xin chào|cảm ơn|ok|vâng|dạ|đồng ý|xem giá)", re.IGNORECASE)

# Câu cần model mạnh → luôn ép sonnet dù có match simple
_COMPLEX = re.compile(
    r"(suy thận|ghép|gan|thận|tim mạch|tiểu đường|đường huyết|huyết áp|mỡ máu|đột quỵ|tai biến|ung thư|hoá trị|hóa trị|xạ trị|"
    r"chống đông|kháng sinh|thuốc|stent|phình|thalass|tan máu|sắt|"
    r"có thai|mang thai|bầu|cho con bú|sau sinh|trẻ|bé |con em|con nhà|tuổi|"
    r"dị ứng|mẩn ngứa|tác dụng phụ|phản ứng|khó thở|mất ngủ|nóng người|hồi hộp|nôn|máu|"
    r"bác sĩ|xét nghiệm|kết quả khám|"
    r"đắt|mắc|giảm giá|khuyến mãi|quà|combo|tính ra|tăng giá|"
    r"lừa đảo|hàng giả|chính hãng|uy tín|cam kết|hoàn tiền|khiếu nại|đổi trả|"
    r"khỏi|chữa|hiệu quả không|sinh lý|rượu|sâm tươi|"
    r"hàn quốc|ngọc linh|giấy tờ|nghiên cứu|khách cũ|mua tiếp|đã mua|tích điểm|người hay máy|bot|AI)", re.IGNORECASE)


import os


def route(last_user_text: str, default_strong=None, default_cheap=None) -> str:
    """v0.1.10: model mạnh/rẻ đổi được bằng ENV — ROUTER_STRONG (mặc định sonnet), ROUTER_CHEAP (mặc định haiku).
    Vd chạy toàn Gemini: ROUTER_STRONG=gemini, ROUTER_CHEAP=gemini_lite."""
    default_strong = default_strong or os.environ.get("ROUTER_STRONG", "sonnet")
    default_cheap = default_cheap or os.environ.get("ROUTER_CHEAP", "haiku")
    t = last_user_text or ""
    if _COMPLEX.search(t):
        return default_strong
    if _SIMPLE.search(t):
        return default_cheap
    # mặc định: câu chưa rõ → dùng model mạnh cho chắc (an toàn > tiết kiệm)
    return default_strong
