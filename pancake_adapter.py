"""Pancake adapter (v0.1.59 — 23/10: chưa đọc cả ca gửi ảnh/tệp; v0.1.57 — 23/10: nhắc nhớ chỉ ca dở dang, B4 bước cuối, chưa đọc khi khách nhắn; v0.1.55 — 23/10: không nhắc nhớ khi khách \"Cam on\" không dấu / bot đã chúc kết thúc) — cửa ra HƯỚNG B: bot TIẾP QUẢN TOÀN PHẦN page Facebook qua Pancake.
v0.5.2 (25/08/2026) — bản kết nối đầy đủ theo Kế hoạch hoàn chỉnh v0.5 mục 7 + Thiết kế Pancake v1.0.
Sâm v0.1.13 (13/10/2026, chị Nga): SẢN PHẨM TRỌNG TÂM theo bài viết/quảng cáo khách bấm vào (POST_PRODUCT_MAP)
và mặc định theo page (PAGE_FOCUS_PRODUCT, đọc ở engine.py).

Cùng một engine (engine.chat) phục vụ cả web test (main.py) lẫn Pancake.
File này lo:
  - nhận webhook → lọc INBOX / dedupe / GOM TIN 60s → gọi engine → gửi trả lời
  - trả hội thoại về người: 5 thẻ + assign + đánh dấu chưa đọc + note gói bàn giao (mục 7.2)
  - ranh giới bot-người (mục 7.3): returned/human_claimed thì bot im; thẻ "Người xử lý" = van ngược
  - kill switch + bật/tắt gửi thật từ TRANG ADMIN (DB setting, không cần redeploy — tắt <1 phút)
  - bảng lead SĐT (rule S2/S3), SLA watcher (mục 7.4), polling dự phòng khi chưa bật được webhook

API Pancake (đã kiểm chứng 22/08): base pages.fm/api/public_api/v1 ; token QUERY PARAM page_access_token ;
rate limit 5 req/giây/page. Container cloud bị chặn gọi pages.fm — module này chạy khi deploy trên Railway.

ENV:
  PANCAKE_PAGE_ID          (bắt buộc — page_id của page Sâm Thái Minh)
  PANCAKE_PAGE_TOKEN       page_access_token có sẵn (KHÔNG bấm "Tạo Token")
  PANCAKE_ENABLED          "1" để bật gửi thật lúc khởi động; admin đổi được lúc chạy (DB setting đè ENV)
  PANCAKE_KILL             "1" = tắt khẩn từ ENV; admin cũng có nút kill riêng (DB setting)
  PANCAKE_BATCH_SECONDS    gom tin: chờ N giây sau tin CUỐI của khách rồi trả lời 1 lần
                           (Sâm: mặc định 60 — chị Nga chốt 25/09 và 13/10: khách nhắn → 1 phút sau bot mới trả lời)
  PANCAKE_PART_GAP         v0.5.22: nghỉ tối thiểu giữa các tin khi bot trả lời nhiều đoạn (mặc định 1.5,
                           cộng ngẫu nhiên tới +0.5 giây cho giống người gõ)
  PANCAKE_POLL             "1" = bật chế độ hỏi định kỳ (dự phòng khi webhook chưa bật được vì slot)
  PANCAKE_AB_PERCENT       A/B test: % hội thoại MỚI vào nhóm bot (mặc định 100 = tiếp quản toàn phần;
                           50 = chia đôi bot/người). Đổi lúc chạy từ admin, hash theo customer_id.
  PANCAKE_POLL_SECONDS     chu kỳ polling (mặc định 25 giây)
  PANCAKE_FORWARD_MAP      HUB PHÂN LUỒNG: Pancake chỉ có MỘT URL webhook chung cho cả gói cước —
                           bot này làm trạm trung tâm, sự kiện page khác được chuyển tiếp NGUYÊN VẸN.
                           Định dạng "page_id=https://url-dich", nhiều tuyến cách nhau phẩy/chấm phẩy.
  PANCAKE_FORWARD_TIMEOUT  giây chờ mỗi lần chuyển tiếp (mặc định 8; thử lại 1 lần nếu lỗi)
  PANCAKE_PHARMACIST_IDS   danh sách user_id dược sĩ trực (phẩy) — Level 3-4 gán thẳng; trống = round robin
  POST_PRODUCT_MAP         v0.1.13: bài viết / quảng cáo → sản phẩm trọng tâm. Định dạng
                           "id_bài_hoặc_quảng_cáo=product_id", nhiều cặp cách nhau phẩy/chấm phẩy/xuống dòng.
                           id bài: số cuối link bài viết (hoặc dạng PAGEID_POSTID); id quảng cáo: Ad ID trong Ads Manager.
                           product_id: hsvn_lat, hsmo_chai, hsmo_tui, duong_sam, long_sam, tam_sam_dan, dong_trung,
                           tra_1700, tra_nguyen_la, ruou_sam, sam_tuoi.  Trang admin đè được bằng setting "post_product_map".
"""
import difflib
import json
import os
import random
import re
import unicodedata
import threading
import time
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request

import db

# ---- v0.1.25 (16/10, chị Nga): MỞ LẠI CA ĐÃ CHUYỂN NGƯỜI cho khách cũ quay lại ----
# Trước đây (thiết kế Bình Vị) ca đã "trả về người" (bot tự chuyển / sale gõ tay / thẻ "Người xử lý")
# thì bot rút VĨNH VIỄN — khách cũ hôm sau nhắn lại bot im. Nay: nếu nhân viên KHÔNG nhắn gì trong
# ca quá PANCAKE_REOPEN_HOURS giờ (mặc định 24) thì lần tới khách nhắn, bot tiếp nhận lại (khách cũ).
# Nhân viên gõ tay lại vào ca → bot rút như cũ. Mốc giờ lưu ở settings: human_at:<conv>, reopen_at:<conv>.
REOPEN_HOURS = float(os.environ.get("PANCAKE_REOPEN_HOURS", "1"))   # v0.1.47: chị Nga chốt 1 giờ (ca không thẻ)
_db_is_blocked_orig = getattr(db, "pancake_is_blocked", lambda *a, **k: False)
_db_is_human_orig = getattr(db, "pancake_is_human", lambda *a, **k: False)
_db_claim_orig = getattr(db, "pancake_claim_human", lambda *a, **k: None)
_db_returned_orig = getattr(db, "pancake_mark_returned", lambda *a, **k: None)


def _ts_setting(key):
    try:
        return float(db.get_setting(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def _touch_human(conv_id):
    db.set_setting("human_at:" + str(conv_id), f"{time.time():.0f}")


def _is_reopened(conv_id) -> bool:
    r = _ts_setting("reopen_at:" + str(conv_id))
    return bool(r) and r > _ts_setting("human_at:" + str(conv_id))


# v0.1.47 (chị Nga 22/10): ca nhân viên chỉ nhắn tay (không gắn thẻ) → mở lại sau REOPEN_HOURS (chị đặt 1–2 giờ);
# ca đang mang thẻ GIỮ NGƯỜI ("Người xử lý" / "Để NV xử lý" / "ADR/Khiếu nại"; "Bot chốt đơn" KHÔNG giữ — chị Nga 22/10) → chờ ít nhất
# REOPEN_HOURS_TAGGED (mặc định 24 giờ) — đơn đang lên, khiếu nại, nhân viên muốn tự giữ khách thì bot không chen vào.
REOPEN_HOURS_TAGGED = float(os.environ.get("PANCAKE_REOPEN_HOURS_TAGGED", "24"))
_HOLD_TAGS = {"người xử lý", "để nv xử lý", "adr/khiếu nại"}


def _reopen_hours_for(conv_obj, conv_id=None) -> float:
    # v0.1.47 (chị Nga 22/10, ca Van Quyet Le): khách ĐÃ ĐỂ SĐT mà nhân viên nhắn tay vào → nhân viên đang gọi / lên đơn
    # → giữ như ca có thẻ (24 giờ), bot không chen vào lên đơn trùng.
    if conv_id and _ts_setting("human_at:" + str(conv_id)) and _fu_has_phone(conv_id, {}):
        return max(REOPEN_HOURS, REOPEN_HOURS_TAGGED)
    try:
        names = {(n or "").strip().lower() for n in _tag_names((conv_obj or {}).get("tags") or (conv_obj or {}).get("tag_ids") or [])}
    except Exception:  # noqa: BLE001
        names = set()
    if names & (_HOLD_TAGS | TAG_HUMAN_NAMES):
        return max(REOPEN_HOURS, REOPEN_HOURS_TAGGED)
    return REOPEN_HOURS


def _maybe_reopen(conv_id, conv_obj=None) -> bool:
    """Gọi khi KHÁCH nhắn tin mới: ca đang bị chặn mà người im quá REOPEN_HOURS → mở lại cho bot."""
    hours = _reopen_hours_for(conv_obj, conv_id)
    if hours <= 0 or _is_reopened(conv_id) or db.get_setting("no_reopen:" + str(conv_id)) == "1":
        return False
    if not (_db_is_blocked_orig(conv_id) or _db_is_human_orig(conv_id)):
        return False
    last = _ts_setting("human_at:" + str(conv_id))
    if last and time.time() - last < hours * 3600:
        return False
    db.set_setting("reopen_at:" + str(conv_id), f"{time.time():.0f}")
    db.log_webhook("reopen", f"{conv_id}: nhân viên im quá {hours:g} giờ → bot tiếp nhận lại (khách cũ quay lại)")
    return True


def _blocked_wrap(conv_id):
    return False if _is_reopened(conv_id) else _db_is_blocked_orig(conv_id)


def _human_wrap(conv_id):
    return False if _is_reopened(conv_id) else _db_is_human_orig(conv_id)


def _claim_wrap(conv_id, *a, **k):
    _touch_human(conv_id)
    return _db_claim_orig(conv_id, *a, **k)


def _returned_wrap(conv_id, *a, **k):
    _touch_human(conv_id)
    return _db_returned_orig(conv_id, *a, **k)


db.pancake_is_blocked = _blocked_wrap
db.pancake_is_human = _human_wrap
db.pancake_claim_human = _claim_wrap
db.pancake_mark_returned = _returned_wrap
import engine
import nhanh          # v0.1.15: đẩy đơn chốt trong chat lên phần mềm Nhanh
import tools_core     # v0.1.15: đọc giá/quà từ kb.json cho tin bám khách (không ghi cứng giá)

PAGE_ID = os.environ.get("PANCAKE_PAGE_ID", "")   # BẮT BUỘC đặt ENV cho page Sâm Thái Minh (docs/05 mục 3)
PAGE_TOKEN = os.environ.get("PANCAKE_PAGE_TOKEN", "")
BASE = "https://pages.fm/api/public_api/v1"
BASE_V2 = "https://pages.fm/api/public_api/v2"
BASE_POS = "https://pos.pages.fm/api/v1"      # v0.5.23 (D2): cổng POS — nơi Pancake giữ đơn hàng

# v0.5.42: ảnh sản phẩm/đánh giá cố định — gửi THẬT qua Messenger (trước đây chỉ bỏ thẻ [IMG]).
# Giữ bản sao map ở đây để KHÔNG import ngược main.py (main import file này → sẽ vòng lặp).
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")
IMG_FILES = {
    # Sâm Thái Minh — ảnh nhãn hàng cấp 23/09/2026 (giữ đồng bộ với main.IMG_MAP)
    "hong-sam-lat": "hong-sam-lat.jpg",
    "hong-sam-lat-mieng": "hong-sam-lat-mieng.jpg",
    "hong-sam-lat-ong-ba": "hong-sam-lat-ong-ba.jpg",
    "hong-sam-lat-bieu": "hong-sam-lat-bieu.jpg",
    "hong-sam-chai": "hong-sam-chai.jpg",
    "hong-sam-tui": "hong-sam-tui.jpg",
    "nuoc-hong-sam-10tui": "nuoc-hong-sam-10tui.jpg",  # v0.1.46: hộp nhỏ 10 túi — CHỈ khi khách hỏi loại 10 túi
    "nuoc-hong-sam": "nuoc-hong-sam.jpg",    # v0.1.46: ảnh chính Nước Hồng sâm hộp 20 túi (chị Nga gửi 21/10) — ƯU TIÊN khi giới thiệu NHS
    "hong-sam-tui-pha": "hong-sam-tui-pha.jpg",
    "duong-sam": "duong-sam.jpg",
    "long-sam": "long-sam.jpg",
    "long-sam-qua-bieu": "long-sam-qua-bieu.jpg",
    "tam-sam-dan": "tam-sam-dan.jpg",
    "ruou-sam": "ruou-sam.jpg",
    "tra-1700": "tra-1700.jpg",
    "tra-nguyen-la": "tra-nguyen-la.jpg",
    "sam-tuoi-vuon": "sam-tuoi-vuon.jpg",
    "sam-tuoi-can": "sam-tuoi-can.jpg",
    "dong-trung": "dong-trung.jpg",
    "nha-may": "nha-may.jpg",            # v0.1.16: ảnh nhà máy Thái Minh Hi-tech (chị Nga gửi 14/10) — công nhân sấy sâm lát
    "nha-may-2": "nha-may-2.jpg",        # v0.1.16: ảnh nhà máy — công nhân vận hành nồi hấp tiệt trùng
    "duong-sam-vien": "duong-sam-vien.jpg",          # v0.1.16: viên hoàn Dương Sâm Linh Đan trong giấy gói (chị Nga gửi 14/10)
    "duong-sam-dong-goi": "duong-sam-dong-goi.jpg",  # v0.1.16: công nhân đóng gói Dương Sâm Linh Đan
    "vuon-sam-lai-chau": "vuon-sam-lai-chau.jpg",  # v0.1.16: vườn sâm Lai Châu có Thủ tướng ghé thăm — CHỈ gửi khi khách TỰ hỏi chuyến thăm
}
_content_cache = {}   # img_id -> content_id (ảnh cố định nên tái dùng được cả phiên)
# ---- v0.5.24 (D2): ĐO CHỐT ĐƠN ----
# Đơn hàng KHÔNG nằm ở public API của page mà ở POS (kiểm chứng 28/08 bằng network request của
# giao diện Pancake). Mỗi đơn POS có sẵn `conversation_id` ⇒ nối ca ↔ đơn THEO HỘI THOẠI, không
# phải ghép qua SĐT (khách cũ từng mua sẽ không bị tính nhầm thành công của bot).
# PAGE_TOKEN KHÔNG dùng được cho POS (error_code 102) — POS nhận `api_key` riêng của shop.
SHOP_ID = os.environ.get("PANCAKE_SHOP_ID", "")  # v0.1.15: bỏ mã shop Bình Vị — phải đặt ENV cho shop Sâm
POS_API_KEY = os.environ.get("PANCAKE_POS_API_KEY", "")
# (Kế thừa Bình Vị) Trạng thái đơn thật trên shop Bình Vị (quét 600 đơn 16/05→28/08): chỉ có 0 và 1, mọi đơn đều
# 0đ/0 sản phẩm ⇒ đội đang dùng "tạo đơn" như một cái ĐÁNH DẤU, tiền nằm ở hệ thống khác.
# 0 = Mới (nháp) · 1 = Đã xác nhận (mốc CHỐT thật) · 2,3 = đã gửi/đã nhận · 6,7 và số âm = huỷ/xoá.
ORDER_CANCELLED = {"-1", "6", "7", "5", "4"}
ORDER_CONFIRMED = {"1", "2", "3", "11", "17", "20"}
BATCH_SECONDS = float(os.environ.get("PANCAKE_BATCH_SECONDS", "30"))   # v0.1.22 (chị Nga 16/10): các câu SAU chờ 30 giây
BATCH_FIRST_SECONDS = float(os.environ.get("PANCAKE_BATCH_FIRST_SECONDS", "50"))   # v0.1.22: câu ĐẦU TIÊN của khách chờ 50 giây
PHONE_STOP = os.environ.get("PANCAKE_PHONE_STOP", "0") == "1"   # v0.1.22: mặc định khách gửi SĐT bot VẪN chat tiếp (1 = kiểu cũ: dừng, giao người)
# (trước v0.1.22: 60 giây) Sâm v0.1.12 (chị Nga 25/09, nhắc lại 13/10): phản hồi sau 1 phút
# v0.5.22 A6: nghỉ 1,5–2 giây giữa các tin nhiều đoạn — bắn liền 2-4 tin nhìn rõ là máy
PART_GAP = max(0.0, float(os.environ.get("PANCAKE_PART_GAP", "1.5")))
POLL_SECONDS = max(15.0, float(os.environ.get("PANCAKE_POLL_SECONDS", "25")))
PHARMACIST_IDS = [x.strip() for x in os.environ.get("PANCAKE_PHARMACIST_IDS", "").split(",") if x.strip()]


# ================= v0.1.13 (13/10): SẢN PHẨM TRỌNG TÂM THEO BÀI VIẾT / QUẢNG CÁO =================
# Khách bấm "Gửi tin nhắn" từ bài viết hoặc quảng cáo → conversation của Pancake mang post_id / ad_ids.
# Bot lưu nguồn đó (setting origin:<conv>) rồi tra POST_PRODUCT_MAP để biết khách đang quan tâm sản phẩm nào.
# Không khớp → engine dùng mặc định của page (PAGE_FOCUS_PRODUCT: Sâm Thái Minh = hsvn_lat; Dương Sâm Linh Đan = duong_sam).
def _parse_post_map(raw: str) -> dict:
    out = {}
    for part in re.split(r"[,;\n]", raw or ""):
        part = part.strip()
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip().strip("<>\"' ")
        v = v.strip().strip("<>\"' ").lower()
        if k and v in engine.PRODUCT_IDS:
            out[k] = v
    return out


def _post_map() -> dict:
    """DB setting (admin sửa lúc chạy) đè ENV. Đọc mỗi lần — map nhỏ, setting có cache của sqlite."""
    raw = db.get_setting("post_product_map")
    if raw is None:
        raw = os.environ.get("POST_PRODUCT_MAP", "")
    return _parse_post_map(raw)


def _map_lookup(m: dict, any_id) -> str:
    """Khớp id đầy đủ hoặc phần sau dấu '_' (post_id Pancake có dạng PAGEID_POSTID)."""
    s = str(any_id or "").strip()
    if not s:
        return ""
    if s in m:
        return m[s]
    tail = s.split("_")[-1]
    if tail in m:
        return m[tail]
    for k, v in m.items():
        if k.split("_")[-1] == tail:
            return v
    return ""


def _save_origin(conv_id: str, conv: dict):
    """Lưu post_id / ad_ids của hội thoại (1 lần, bổ sung nếu lần sau có thêm)."""
    if not conv_id or not isinstance(conv, dict):
        return
    post = conv.get("post_id") or ""
    ads = conv.get("ad_ids") or conv.get("ads") or []
    if isinstance(ads, (str, int)):
        ads = [ads]
    ad_list = []
    for a in ads:
        if isinstance(a, dict):
            a = a.get("ad_id") or a.get("id") or ""
        if a:
            ad_list.append(str(a))
    if not post and not ad_list:
        return
    try:
        cur = json.loads(db.get_setting("origin:" + conv_id) or "{}")
    except Exception:  # noqa: BLE001
        cur = {}
    new = {"post_id": cur.get("post_id") or str(post or ""),
           "ad_ids": sorted(set((cur.get("ad_ids") or []) + ad_list))}
    if new != cur:
        db.set_setting("origin:" + conv_id, json.dumps(new))


# v0.1.42 (21/10, chị Nga): quảng cáo "CTKM - Biếu quà" ghi "TẶNG MIỄN PHÍ 1 HỘP TRÀ SÂM 1700 KHI MUA HỒNG SÂM VIỆT NAM THÁI MINH"
# → khách đến từ các quảng cáo này mua 1 hộp Hồng sâm lát được tặng 1 hộp Trà sâm 1700 (10 gói) như quảng cáo hứa.
# Thêm/bớt quảng cáo: biến Railway AD_GIFT_1BOX_IDS (Ad ID cách nhau dấu phẩy).
AD_GIFT_1BOX_IDS = {x.strip() for x in os.environ.get("AD_GIFT_1BOX_IDS", "" if (engine.IS_DS or engine.IS_NHS) else "120252524881450596").replace(";", ",").split(",") if x.strip()}


def _ad_gift_line(conv_id: str) -> str:
    try:
        o = json.loads(db.get_setting("origin:" + conv_id) or "{}")
    except Exception:  # noqa: BLE001
        o = {}
    if AD_GIFT_1BOX_IDS & set(str(a) for a in (o.get("ad_ids") or [])):
        # v0.1.56 (chị Nga 23/10): KHÔNG tự báo quà này — chỉ áp khi khách chủ động hỏi (rule 5o-g)
        return ("QUẢNG CÁO HỨA QUÀ: khách đến từ quảng cáo 'Tặng miễn phí 1 hộp Trà sâm 1700 khi mua Hồng sâm Việt Nam Thái Minh' "
                "— KHÔNG tự báo quà mua 1 hộp; CHỈ khi khách chủ động hỏi CT tặng trà (hoặc chê đắt) mới áp: 1 hộp Hồng sâm lát tặng "
                "1 hộp Trà sâm 1700 (10 gói), build_order price_objection=true. Khách không hỏi → báo giá combo như thường")
    return ""


def _focus_of(conv_id: str):
    """(product_id, nguồn) của hội thoại. ('', '') = không khớp → engine dùng mặc định của page."""
    try:
        o = json.loads(db.get_setting("origin:" + conv_id) or "{}")
    except Exception:  # noqa: BLE001
        o = {}
    m = _post_map()
    if not m or not o:
        return "", ""
    for ad in o.get("ad_ids") or []:
        pid = _map_lookup(m, ad)
        if pid:
            return pid, "ads"
    pid = _map_lookup(m, o.get("post_id"))
    if pid:
        return pid, ("comment" if db.get_setting("cmt:" + conv_id) else "post")
    return "", ""


# 5 thẻ mới (bên cạnh 12 thẻ sale đang dùng) — kế hoạch v0.5 mục 7.2
# Chốt 14/10 (chị Nga): gộp "Chuyển TV" + "TV chuyên môn" thành "Người xử lý" (bot đã trả ca về người
# nên thẻ van ngược này chỉ xác nhận, bot không nói tiếp); "RED FLAG" đổi tên "ADR/Khiếu nại".
TAG_BY_LEVEL = {1: "Bot chốt đơn", 2: "Người xử lý", 3: "Người xử lý", 4: "ADR/Khiếu nại"}
TAG_BOT = "Bot"
# Van ngược: sale gắn thẻ này → bot rút vĩnh viễn. Trên page anh Na tạo tên "Để NV xử lý" (25/08);
# nhận cả tên cũ trong kế hoạch lẫn tên thực tế + tên tuỳ chỉnh qua ENV.
TAG_HUMAN_NAMES = {"người xử lý", "để nv xử lý"}
if os.environ.get("PANCAKE_TAG_HUMAN", "").strip():
    TAG_HUMAN_NAMES.add(os.environ["PANCAKE_TAG_HUMAN"].strip().lower())
TAG_AB_HUMAN = "Nhóm người"        # A/B test: đánh dấu hội thoại nhóm đối chứng (người trực như cũ)

# ---- v0.5.15: TIN KHÔNG CÓ CHỮ (sticker / ảnh) ----
# Câu đưa vào não bot khi khách gửi sticker: giữ nguyên ngữ cảnh để bot tự hiểu là đồng ý.
STICKER_TEXT = os.environ.get("PANCAKE_STICKER_TEXT") or (
    "[Khách gửi biểu tượng cảm xúc / sticker, không kèm chữ. Nếu ngay trước đó em vừa hỏi "
    "xác nhận thì hiểu là khách ĐỒNG Ý và làm tiếp bước sau; nếu không thì hỏi lại thật ngắn.]")
ATT_MARK = "[Khách gửi ảnh/tệp, không kèm chữ]"
# v0.5.37 (anh Na duyệt 01/09): bot NHÌN ảnh/sticker thật — 2 marker dưới đưa vào não kèm ảnh
IMG_SEE = "[Khách gửi ảnh — hãy XEM ảnh đính kèm và xử lý theo rule 5q]"
STICKER_SEE = "[Khách gửi sticker — hãy NHÌN hình sticker đính kèm, phản hồi đúng cảm xúc của nó theo rule 5q]"
ATT_ACK = os.environ.get("PANCAKE_ATT_ACK") or (
    "Dạ em nhận được ảnh của anh/chị rồi ạ, em nhờ chuyên viên xem giúp rồi phản hồi anh/chị ngay nhé ạ.")
TAG_NO_REPLY = "Ko PH"
# v0.5.22 A3: FB #551 — khách chặn page / xoá hội thoại / hết cửa sổ: không gửi được nữa
TAG_UNREACH = os.environ.get("PANCAKE_TAG_UNREACH", "Ko gửi được")
# v0.5.22 A7: khách gửi TRẦN SĐT → 1 câu ghi nhận rồi giao người NGAY (không chờ nhịp 30 phút)
PHONE_ACK = os.environ.get("PANCAKE_PHONE_ACK") or (
    "Dạ em nhận được số điện thoại của anh/chị rồi ạ. Chuyên viên tư vấn bên em sẽ gọi lại cho anh/chị "
    "sớm nhất có thể, anh/chị để ý điện thoại giúp em nhé ạ!")   # v0.1.21: bỏ "Dược sĩ" (anh Huy chốt 14/10)

# ---- v0.5.27 (phần B, anh Na chốt 28/08): NHỊP THEO NGUỒN + CỬA SỔ THEO CA ----
# Nguồn ca lấy từ API conversations (field ad_ids / post_id — dò 29/08, xem _src_loop).
# Cửa sổ: ca từ QUẢNG CÁO được Meta cho 7 ngày; ca tự nhắn 24 giờ. Kiểm chứng B6 (29/08):
# gửi thử vào ca đã im 3,7 ngày qua Pancake → THÀNH CÔNG, có message id thật — Pancake không
# chặn sau 24h (họ tự lo message tag phía dưới). Dù vậy nhịp vẫn đặt trong cửa sổ chính sách.
FU_WINDOW = float(os.environ.get("PANCAKE_FU_WINDOW", "86400"))            # organic: 24 giờ
FU_WINDOW_ADS = float(os.environ.get("PANCAKE_FU_WINDOW_ADS", "604800"))   # ads: 7 ngày
# Nhịp ads (phương án a): 30 phút → 1 ngày → 3 ngày. Organic: 1 giờ → 8 giờ (không có nhịp 3).
# Sâm v0.1.12 (brief 25/09 — quy trình 4 bước bám khách không phản hồi): nhắc nhớ sau 30 phút → xây niềm tin sau thêm
# ~4 giờ → nhắc ưu đãi & kết thúc sau thêm ~12 giờ (mốc tính từ tin cuối của khách: 0,5h / 4,5h / 16,5h — nằm trong 24h).
# Sau nhịp 3 KHÔNG chủ động nhắn nữa.
FU_ADS = [float(x) for x in (os.environ.get("PANCAKE_FU_ADS") or "1800,16200,59400").split(",")]
FU_ORG = [float(x) for x in (os.environ.get("PANCAKE_FU_ORG") or "1800,16200,59400").split(",")]
# Có SĐT: im thêm FU_GRACE sau nhịp 1 là GIAO NGƯỜI GỌI luôn, không chờ nhịp sau.
FU_GRACE = float(os.environ.get("PANCAKE_FU_GRACE", "1800"))
# B4: giờ im lặng — không bắn tin đuổi 0h00–7h30 giờ VN (kế hoạch ghi 0h–5h dồn về 7h30;
# em chặn luôn tới 7h30 vì 5–7h sáng nhắn cũng phản cảm — tin dồn bung đúng 7h30).
QUIET_UNTIL_MIN = int(os.environ.get("PANCAKE_QUIET_UNTIL", "450"))   # phút kể từ 0h VN
# B9: ca khách chọn mua NHÀ THUỐC — hỏi thăm ĐÚNG 1 LẦN sau ~21 giờ (trong cửa sổ 24h).
PH_T = float(os.environ.get("PANCAKE_PH_T", "75600"))
PH_MSG = os.environ.get("PANCAKE_PH_MSG") or (
    "Dạ anh/chị ơi, hôm trước anh/chị có hỏi điểm bán Sâm Thái Minh — anh/chị đã mua được "
    "hàng chưa ạ? Nếu cần em hỗ trợ thêm về cách dùng thì anh/chị cứ nhắn em nhé ạ.")
# B8 (số thật 96h, 29/08): nhịp 1 kéo lại 11% khách; câu nhịp 2 cũ 4,8%; câu nhịp 3 cũ (21h)
# chỉ 1/46 ≈ 2,2% → BỎ. Nhịp ads mới cách 1–3 ngày nên câu phải đổi góc, không lặp xin SĐT.
# v0.1.14 (chị Nga chốt 13/10): 3 tin bám khách theo mẫu của chị Nga — {who} = cách gọi có tên ("Chị Trịnh Thị Chanh"),
# {p} = đại từ ("chị" / "anh" / "anh/chị"), {P} = viết hoa đầu. Nhịp 2 gửi kèm ảnh nhà máy + vườn sâm (FU_IMG2).
_FU1 = ("{who} ơi, không biết {p} đã nhận được tin nhắn của em chưa ạ.\n\n"
        "{P} còn băn khoăn gì về sản phẩm thì {p} chia sẻ thêm thông tin để em hỗ trợ thêm cho {p} nhé! 😊")
# v0.1.102 (28/10, chị Nga duyệt; tin nhắc nhớ không gắn tên khách): NHỊP 1 nhiều cách viết, chọn theo tin cuối của bot, xoay vòng trong nhóm, cùng khách không lặp.
#  A = chưa báo giá · B = bot vừa hỏi, khách chưa trả lời · C = đã báo giá / combo. (N5 bỏ theo chị Nga.)
_FU1_VARIANTS = {
    "A": [_FU1,
          "{who} ơi, em gửi thông tin rồi mà chưa thấy {p} phản hồi, không biết {p} đã xem được chưa ạ? {P} có câu hỏi nào em giải đáp ngay cho {p} ạ 😊",
          "{who} ơi, chắc {p} đang bận ạ. Khi nào tiện {p} cứ nhắn em, em tư vấn kỹ hơn cho {p} nhé ạ.",
          "{who} ơi, nếu {p} còn phân vân, {p} chỉ cần cho em biết sâm dùng cho ai và tình trạng sức khỏe hiện tại, em sẽ gợi ý liệu trình phù hợp nhất cho {p} ạ."],
    "B": ["{who} ơi, em vẫn đang chờ {p} ạ. {P} chia sẻ thêm một chút để em gợi ý cách dùng phù hợp nhất cho {p} nhé ạ 😊"],
    "C": ["{who} ơi, bên em giao hàng tận nhà toàn quốc, {p} nhận hàng kiểm tra rồi mới thanh toán nên {p} hoàn toàn yên tâm ạ. "
          "{P} muốn chọn combo nào thì nhắn em, em lên đơn ngay cho {p} nhé.",
          "{who} ơi, chương trình quà tặng kèm combo đang áp dụng đến hết 31/12/2026 ạ. {P} cần em tư vấn thêm gói nào phù hợp thì cứ nhắn em nhé ạ."],
}


def _fu1_pick(conv_id: str) -> str:
    try:
        hist = db.get_history(db.pancake_local_conv(conv_id))
    except Exception:  # noqa: BLE001
        hist = []
    bots = [str(m.get("content") or "") for m in hist if m.get("role") == "assistant" and str(m.get("content") or "").strip()]
    last = bots[-1] if bots else ""
    if re.search(r"\d{1,3}(?:[.,]\d{3}){1,2}\s*đ|combo", " ".join(bots), re.I):
        grp = "C"
    elif last.rstrip().endswith("?"):
        grp = "B"
    else:
        grp = "A"
    used = (db.get_setting("fu1used:" + conv_id) or "").split("|")
    if all(f"{grp}{i}" in used for i in range(len(_FU1_VARIANTS[grp]))) and grp != "A":
        grp = "A"                       # nhóm đã dùng hết với khách này → lấy câu hỏi thăm chung chưa dùng
    opts = _FU1_VARIANTS[grp]
    k = int(db.get_setting("fu1rr:" + grp) or 0)
    for i in range(len(opts)):
        cand = (k + i) % len(opts)
        if f"{grp}{cand}" not in used or i == len(opts) - 1:
            break
    db.set_setting("fu1rr:" + grp, str(cand + 1))
    db.set_setting("fu1used:" + conv_id, "|".join([u for u in used if u] + [f"{grp}{cand}"])[-200:])
    return opts[cand]


_FU2 = ("Về chất lượng và uy tín sản phẩm thì {p} hoàn toàn yên tâm ạ. Hồng sâm Thái Minh được sản xuất tại nhà máy "
        "Thái Minh Hi-tech đạt tiêu chuẩn GMP và ISO/IEC 17025. Toàn bộ hệ thống sản xuất đều tuân thủ tiêu chuẩn, đảm bảo chất lượng "
        "sản phẩm đầu ra an toàn, ổn định đến tay khách hàng ạ.\n\n"
        "Thái Minh là công ty dược lớn gần 15 năm trên thị trường, có rất nhiều sản phẩm nổi tiếng xuất hiện trên truyền hình VTV1, VTV3... "
        "như Khương Thảo Đan, Bình Vị Thái Minh, Vương Bảo.\n\n"
        "{P} mua dùng thử một hộp trải nghiệm nhé, dùng tốt {p} có thể yên tâm mua thêm ạ 🌿")
# Nhịp 2 khi sản phẩm trọng tâm là Dương Sâm / Long Sâm (chị Nga 14/10 — không nói "nhà máy Thái Minh Hi-tech")
_FU2_DL = ("Về chất lượng và uy tín sản phẩm {sp} thì {p} hoàn toàn yên tâm ạ. Toàn bộ hệ thống sản xuất đều tuân thủ tiêu chuẩn, "
           "đảm bảo chất lượng sản phẩm đầu ra an toàn, ổn định đến tay khách hàng ạ.\n\n"
           "Sản phẩm được phân phối bởi Thái Minh là công ty dược lớn gần 15 năm trên thị trường, có rất nhiều sản phẩm nổi tiếng khác "
           "xuất hiện trên truyền hình VTV1, VTV3... như Khương Thảo Đan, Bình Vị Thái Minh, Vương Bảo đó ạ.\n\n"
           "{P} mua dùng thử một hộp trải nghiệm nhé, dùng tốt {p} có thể yên tâm mua thêm ạ 🌿")
_DL_NAMES = {"duong_sam": "Dương Sâm Linh Đan", "long_sam": "Long Sâm Linh Đan"}
# {combos} = các dòng combo Hồng sâm lát sinh từ kb.json lúc gửi (đổi giá/quà chỉ cần sửa build_kb.py)
_FU3 = ("Dạ em xin gửi lại chương trình ưu đãi tốt nhất hiện tại ạ:\n"
        "{combos}\n\n"
        "{who} muốn mua ưu đãi nào thì {p} cứ để lại tin nhắn, hoặc có thể liên hệ qua Tổng đài 1800 1120 của bên em nha.\n"
        "Chúc {p} nhiều sức khỏe ạ! 🌿")
# Nhịp 3 khi sản phẩm trọng tâm KHÔNG phải Hồng sâm lát (combo ở trên là của Hồng sâm lát)
_FU3_OTHER = ("{who} ơi, chương trình ưu đãi dành cho khách mới đang áp dụng đến hết 31/12/2026 ạ.\n\n"
              "{P} muốn đặt hàng thì cứ để lại tin nhắn cho em, hoặc liên hệ Tổng đài 1800 1120 của bên em nha.\n"
              "Chúc {p} nhiều sức khỏe ạ! 🌿")
# v0.3.0: page Dương Sâm — nhịp 3 gửi lại 3 gói liệu trình + hotline 1800 8308
_FU3_DS = ("Dạ em xin gửi lại chương trình tri ân khách hàng mới của Dương Sâm Linh Đan ạ:\n"
           "{combos}\n"
           "✅ Miễn phí vận chuyển toàn quốc, nhận hàng kiểm tra rồi mới thanh toán.\n\n"
           "{who} muốn bắt đầu liệu trình nào thì {p} cứ để lại tin nhắn, hoặc liên hệ Tổng đài 1800 8308 của bên em nha.\n"
           "Chúc {p} nhiều sức khỏe ạ! 🌿")

# v0.4.0: bot Nước Hồng sâm — nhịp 3 gửi lại 3 combo 2/4/6 hộp + tổng đài 1800 1120
_FU3_NHS = ("Dạ em xin gửi lại chương trình tri ân khách hàng mới của Nước Hồng sâm Thái Minh mật ong ạ:\n"
            "{combos}\n"
            "✅ Từ 2 hộp miễn phí vận chuyển, nhận hàng kiểm tra rồi mới thanh toán.\n\n"
            "{who} muốn lấy combo nào thì {p} cứ để lại tin nhắn, hoặc liên hệ Tổng đài 1800 1120 của bên em nha.\n"
            "Chúc {p} nhiều sức khỏe ạ! 🌿")


def _nhs_combo_lines() -> str:
    try:
        kb = tools_core.load_kb()
        sku = "hsmo-chai" if engine.PAGE_FOCUS_PRODUCT == "hsmo_chai" else "hsmo-tui"
        unit = "chai" if sku == "hsmo-chai" else "hộp"
        _, pkg = tools_core.find_package(kb, sku)
        rules = {r["min_qty"]: r.get("gift") or "" for r in kb["programs"]["new_customer"]["rules"]
                 if r["if_sku"] == sku and not r.get("condition")}
        return "\n".join(f"🎁 Combo {q} {unit}: {tools_core.fmt_vnd(pkg['price_retail'] * q)} – tặng {rules[q]}"
                         for q in (2, 4, 6) if rules.get(q))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"fu nhs combo: {ex}")
        return "🎁 Combo 2 – 4 – 6 hộp đang có quà Trà sâm tặng kèm"


def _ds_combo_lines() -> str:
    try:
        kb = tools_core.load_kb()
        _, pkg = tools_core.find_package(kb, "duongsam-10")
        rules = sorted((r for r in kb["programs"]["new_customer"]["rules"]
                        if r["if_sku"] == "duongsam-10" and r.get("label") and not r.get("condition")), key=lambda r: r["min_qty"])
        return "\n".join(f"🎁 {r['label']} ({r['min_qty']} hộp): {tools_core.fmt_vnd(pkg['price_retail'] * r['min_qty'])} – "
                         f"Tặng {r['gift']}" for r in rules)
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"fu ds combo: {ex}")
        return "🎁 Các liệu trình 1 – 2 – 3 tháng đang có quà tặng kèm"


FU_LAST_TAG = os.environ.get("PANCAKE_FU_LAST_TAG", "B4").strip()   # v0.1.56: thẻ gắn khi gửi nhịp cuối (CTKM + chào kết)
FU_IMG2 = [x.strip() for x in (os.environ.get("PANCAKE_FU_IMG2") or "nha-may,nha-may-2,sam-tuoi-vuon").split(",") if x.strip()]
FU_MSG = {
    # Nhịp 1 (30 phút sau tin cuối của khách) — hỏi khách đã nhận tin chưa, còn băn khoăn gì
    "1_phone": os.environ.get("PANCAKE_FU_MSG1_PHONE") or _FU1,
    "1_nophone": os.environ.get("PANCAKE_FU_MSG1_NOPHONE") or _FU1,
    # Nhịp 2 (thêm 4 giờ) — nhà máy, uy tín Thái Minh + ảnh nhà máy, vườn sâm
    "org2": os.environ.get("PANCAKE_FU_MSG2_NOPHONE") or _FU2,
    "ads2": os.environ.get("PANCAKE_FU_MSG_ADS2") or _FU2,
    # Nhịp 3 (thêm 12 giờ) — gửi lại ưu đãi + tổng đài, chào kết; sau đó không nhắn nữa
    "org3": os.environ.get("PANCAKE_FU_MSG_ORG3") or _FU3,
    "ads3": os.environ.get("PANCAKE_FU_MSG_ADS3") or _FU3,
}


def _lat_combo_lines(p: str) -> str:
    """Dòng combo Hồng sâm lát lấy từ bảng khuyến mại trong kb.json (nguồn giá duy nhất)."""
    try:
        kb = tools_core.load_kb()
        lat = kb["products"]["hsvn_lat"]
        price = next(k["price_retail"] for k in lat["packages"] if k["sku"] == "hsvn-lat-14")
        rules = sorted((r for r in kb["programs"]["new_customer"]["rules"]
                        if r["if_sku"] == "hsvn-lat-14" and r.get("label")), key=lambda r: r["min_qty"])
        out = []
        for i, r in enumerate(rules):
            line = (f"🎁 {r['label']} ({r['min_qty']} hộp): Giá {tools_core.fmt_vnd(price * r['min_qty'])} – "
                    f"Tặng ngay {r['gift']}")
            out.append(line + (f" để {p} dùng kết hợp ạ" if i else ""))
        return "\n".join(out)
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"fu combo lines: {ex}")
        return "🎁 Các combo 1 – 2 – 3 tháng đang có quà tặng kèm"


class _SafeFmt(dict):
    def __missing__(self, k):
        return "{" + k + "}"


# v0.1.65 (24/10, ca Ngô Xuân Hiền): tên Facebook không đoán được giới tính, Pancake chưa có giới tính
# → tin nhắc nhớ gọi "anh/chị" dù cả hội thoại đã rõ là anh. Đoán giới tính từ chính hội thoại.
_RE_SELF_MALE = re.compile(r"(?:^|[\s,.!?])(?:cho|để|giúp|với)\s+anh\s+(?:hỏi|mua|đặt|xem|lấy|xin|biết)|^\s*anh\s+(?:muốn|hỏi|cần|lấy|mua|dùng|uống|định|đặt|tên là)\b"
                           r"|\b(?:vợ|bà xã) (?:tôi|anh|mình|em)\b|\btôi là (?:nam|đàn ông)\b", re.I | re.M)
_RE_SELF_FEMALE = re.compile(r"(?:^|[\s,.!?])(?:cho|để|giúp|với)\s+chị\s+(?:hỏi|mua|đặt|xem|lấy|xin|biết)|^\s*chị\s+(?:muốn|hỏi|cần|lấy|mua|dùng|uống|định|đặt|tên là)\b"
                             r"|\b(?:chồng|ông xã) (?:tôi|chị|mình|em)\b|\btôi là (?:nữ|phụ nữ)\b|\bđang (?:cho con bú|mang thai|bầu)\b", re.I | re.M)


def _infer_gender(conv_id: str) -> str:
    """'male' / 'female' / '' — (1) giới tính Pancake đã lưu; (2) khách tự xưng anh/chị, nói 'vợ tôi'/'chồng tôi' (lưu lại);
    (3) các tin bot đã gửi khách trong hội thoại chỉ gọi 'anh' (hoặc chỉ 'chị')."""
    g = db.get_setting("gender:" + conv_id) or ""
    try:
        hist = db.get_history(db.pancake_local_conv(conv_id))
    except Exception:  # noqa: BLE001
        return g if g in ("male", "female") else ""
    # v0.1.66 (ca Đông Đao): khách TỰ XƯNG "chị" ("chị uống 6 năm rồi", "gửi cho chị xem") → ĐÈ giới tính Pancake/tên
    sg = engine.customer_self_gender([str(m.get("content") or "") for m in hist if m.get("role") == "user"])
    if sg:
        if sg != g:
            db.set_setting("gender:" + conv_id, sg)
        return sg
    if g in ("male", "female"):
        return g
    users = " \n".join(str(m.get("content") or "") for m in hist if m.get("role") == "user")
    m, f = bool(_RE_SELF_MALE.search(users)), bool(_RE_SELF_FEMALE.search(users))
    if m != f:
        g = "male" if m else "female"
        db.set_setting("gender:" + conv_id, g)
        return g
    bots = " ".join(re.sub(r"anh/chị|Anh/chị|anh chị", " ", str(x.get("content") or "")) for x in hist if x.get("role") == "assistant")
    na = len(re.findall(r"(?<![A-Za-zÀ-ỹĐđ])[Aa]nh(?![A-Za-zÀ-ỹĐđ])", bots))
    nc = len(re.findall(r"(?<![A-Za-zÀ-ỹĐđ])[Cc]hị(?![A-Za-zÀ-ỹĐđ])", bots))
    if na >= 2 and nc == 0:
        return "male"
    if nc >= 2 and na == 0:
        return "female"
    return ""


def _fu_text(key: str, conv_id: str) -> str:
    """Điền tên/xưng hô của khách vào câu bám khách. Có tên + giới tính → "Chị Trịnh Thị Chanh";
    có tên chưa rõ giới tính → "Anh/chị Trịnh Thị Chanh"; không có tên đạt chuẩn → "Anh/chị"."""
    txt = FU_MSG.get(key) or FU_MSG["1_nophone"]
    if key.startswith("1_") and txt == _FU1:
        try:
            txt = _fu1_pick(conv_id)        # v0.1.102: nhịp 1 nhiều cách viết
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"fu1 pick {conv_id}: {ex}")
    if key.endswith("3") and txt == _FU3 and (_focus_of(conv_id)[0] or engine.PAGE_FOCUS_PRODUCT) == "duong_sam":
        txt = _FU3_DS.replace("{combos}", _ds_combo_lines())
    elif key.endswith("3") and txt == _FU3 and engine.IS_NHS \
            and (_focus_of(conv_id)[0] or engine.PAGE_FOCUS_PRODUCT) in ("hsmo_tui", "hsmo_chai"):
        txt = _FU3_NHS.replace("{combos}", _nhs_combo_lines())   # v0.4.0
    elif key.endswith("3") and (_focus_of(conv_id)[0] or engine.PAGE_FOCUS_PRODUCT) != "hsvn_lat" \
            and txt == _FU3:
        txt = _FU3_OTHER
    focus_now = _focus_of(conv_id)[0] or engine.PAGE_FOCUS_PRODUCT
    if key.endswith("2") and txt == _FU2 and focus_now in _DL_NAMES:
        txt = _FU2_DL
    nm = db.get_setting("name:" + conv_id) or ""
    g = _infer_gender(conv_id)   # v0.1.65
    p = "anh" if g == "male" else ("chị" if g == "female" else ("anh" if engine.IS_DS else "anh/chị"))
    # v0.1.44: gọi đúng TÊN GỌI ("Chị Hoa") thay vì cả tên Facebook ("Chị Hoa Nguyễn"); không tách được tên → "Anh/chị"
    # v0.1.102 (28/10, chị Nga): tin nhắc nhớ KHÔNG gắn tên khách ("Anh Sùng ơi" → "Anh ơi") — tên Facebook dễ tách nhầm
    who = p[:1].upper() + p[1:]
    try:   # v0.1.63 (ca Phay Hoang): khách tự xưng cô/bác/chú… → tin nhắc nhớ gọi đúng danh xưng
        _t = engine._customer_title([str(m.get("content") or "") for m in db.get_history(db.pancake_local_conv(conv_id))
                                     if m.get("role") == "user"])
    except Exception:  # noqa: BLE001
        _t = ""
    if _t:
        p, who = _t, _t[:1].upper() + _t[1:]
    try:
        out = txt.format_map(_SafeFmt(who=who, p=p, P=p[:1].upper() + p[1:], sp=_DL_NAMES.get(focus_now, ""),
                                      combos=_lat_combo_lines(p) if "{combos}" in txt else ""))
        return engine._fix_title(out, _t) if _t else out
    except Exception:  # noqa: BLE001
        return txt


def _ab_percent() -> int:
    """% hội thoại MỚI rơi vào nhóm bot. 100 = bot tiếp quản toàn phần (mặc định);
    50 = A/B một nửa. Đổi lúc chạy từ admin (DB setting đè ENV PANCAKE_AB_PERCENT)."""
    v = db.get_setting("pancake_ab_percent")
    if v is None:
        v = os.environ.get("PANCAKE_AB_PERCENT", "100")
    try:
        return max(0, min(100, int(float(v))))
    except Exception:  # noqa: BLE001
        return 100


# ---- Công tắc lúc chạy: DB setting (admin đổi được ngay) đè ENV ----
def _flag(setting_key: str, env_key: str) -> bool:
    v = db.get_setting(setting_key)
    if v is not None:
        return v == "1"
    return os.environ.get(env_key, "0") == "1"


def is_enabled() -> bool:
    return _flag("pancake_enabled", "PANCAKE_ENABLED")


def is_killed() -> bool:
    # kill switch: ENV "1" ép tắt bất kể admin; còn lại theo DB setting
    if os.environ.get("PANCAKE_KILL", "0") == "1":
        return True
    return db.get_setting("pancake_kill", "0") == "1"


def is_polling() -> bool:
    return _flag("pancake_poll", "PANCAKE_POLL")


def _ab_tagged(conv_id) -> bool:
    """v0.5.12: hội thoại đã được gắn thẻ nhóm A/B (Bot / Nhóm người) chưa.
    Cờ lưu ở bảng settings (key ab_tagged:<conv_id>) — không phải sửa schema db.py."""
    return db.get_setting(f"ab_tagged:{conv_id}") == "1"


def _mark_ab_tagged(conv_id):
    db.set_setting(f"ab_tagged:{conv_id}", "1")


TEST_KEYWORD = os.environ.get("PANCAKE_TEST_KEYWORD", "#tm").lower()


def is_test_only() -> bool:
    """Chế độ THỬ NỘI BỘ (mặc định BẬT cho an toàn): dù 'gửi thật' đã bật, bot chỉ thực sự
    nhắn ra ở hội thoại có mã test (khách nhắn kèm '#tm'); hội thoại thường vẫn chỉ nghe/log.
    Tắt nấc này = bot gửi thật cho TOÀN BỘ hội thoại nhóm bot."""
    v = db.get_setting("pancake_test_only")
    if v is not None:
        return v == "1"
    return os.environ.get("PANCAKE_TEST_ONLY", "1") == "1"


def _may_send(conv_id: str) -> bool:
    if not is_enabled():
        return False
    if is_test_only():
        return db.pancake_is_test(conv_id)
    return True


def status() -> dict:
    return {"page_id": PAGE_ID, "token_set": bool(PAGE_TOKEN),
            "enabled": is_enabled(), "kill": is_killed(), "polling": is_polling(),
            "batch_seconds": BATCH_SECONDS, "poll_seconds": POLL_SECONDS,
            "pending_batches": len(_batches), "pharmacist_ids": PHARMACIST_IDS,
            "ab_percent": _ab_percent(), "test_only": is_test_only(),
            "followup": is_fu_enabled(), "fu_pending": _fu_pending(), "keep_unread": is_keep_unread(),
            "test_keyword": TEST_KEYWORD,
            "page_focus_product": engine.PAGE_FOCUS_PRODUCT, "post_product_map": _post_map(),
            "nhanh_enabled": nhanh.enabled(), "nhanh_mapped_skus": sorted(nhanh.product_map()),
            "forward_map": {pid: _host(url) for pid, url in FORWARD_MAP.items()},
            "forward_stats": dict(_fw_stats)}


# ---- Rate limit đơn giản: tôn trọng 5 req/giây/page ----
_rl_lock = threading.Lock()
_rl_times = []


def _throttle():
    with _rl_lock:
        now = time.time()
        while _rl_times and now - _rl_times[0] > 1.0:
            _rl_times.pop(0)
        if len(_rl_times) >= 5:
            time.sleep(1.0 - (now - _rl_times[0]) + 0.02)
        _rl_times.append(time.time())


def _api(method: str, path: str, params: dict = None, body: dict = None, base: str = None,
         _retry=True) -> dict:
    """Gọi Pancake API, token qua query param. Retry 1 lần khi 429."""
    if not PAGE_TOKEN:
        return {"error": "no page token"}
    params = dict(params or {})
    params["page_access_token"] = PAGE_TOKEN
    url = f"{base or BASE}{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"content-type": "application/json"})
    _throttle()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as ex:
        if ex.code == 429 and _retry:
            time.sleep(1.0)
            return _api(method, path, params, body, base, _retry=False)
        return {"error": f"HTTP {ex.code}", "detail": _safe_read(ex)}
    except Exception as ex:  # noqa: BLE001
        if _retry and _is_neterr(ex):
            # v0.5.32: TLS handshake timeout hàng loạt 29/08 11:31–11:42 (Railway → pages.fm)
            # — lỗi thoáng qua, thử lại 1 lần sau 2s là đi được (fu nhịp 1 tự hồi sau 4 phút,
            # nhưng tin _respond và gắn thẻ thì mất luôn nếu không retry).
            time.sleep(2.0)
            return _api(method, path, params, body, base, _retry=False)
        return {"error": f"network: {ex}"}


def _is_neterr(ex) -> bool:
    """Lỗi tầng mạng/TLS (chưa chắc request đã tới nơi) — an toàn để thử lại 1 lần."""
    return isinstance(ex, (urllib.error.URLError, ssl.SSLError, socket.timeout,
                           ConnectionError, TimeoutError))


def _safe_read(ex) -> str:
    try:
        return ex.read().decode("utf-8")[:300]
    except Exception:  # noqa: BLE001
        return ""


# ---- Gửi trả lời / gắn thẻ / assign / đánh dấu chưa đọc / note ----
def _body_ok(r: dict) -> bool:
    """Pancake có thể trả HTTP 200 nhưng ruột {'success': false} — phải soi ruột (lỗi 25/08:
    log 'ĐÃ GỬI' mà Messenger không nhận)."""
    if not isinstance(r, dict) or r.get("error"):
        return False
    if r.get("success") is False:
        return False
    return True


def _is_noop(r) -> bool:
    """v0.5.22 A2: Pancake trả 'Nothing to update!' khi assign/thẻ ĐÃ ĐÚNG SẴN — không phải lỗi
    (anh Na thấy log ❌ 11:13:38). Hạ xuống info, không đếm vào bộ đếm lỗi của đèn trạng thái."""
    try:
        return "nothing to update" in json.dumps(r, ensure_ascii=False).lower()
    except Exception:  # noqa: BLE001
        return False


def _is_unreach(r) -> bool:
    """v0.5.22 A3: FB #551 'This person isn\'t available right now' — khách chặn page, xoá hội
    thoại, hoặc ngoài cửa sổ. Gửi tiếp chỉ tốn API và làm xấu oan số A/B (anh Na thấy 13:44:11)."""
    try:
        s = json.dumps(r, ensure_ascii=False).lower()
    except Exception:  # noqa: BLE001
        return False
    return ("#551" in s or '"code": 551' in s or '"code":551' in s
            or "isn't available" in s or "not available right now" in s
            or "hiện không có mặt" in s)


def _mark_unreach(conv_id: str):
    """Ca không gửi được (FB #551): ghi cờ 1 lần + dừng nhịp theo đuổi + gắn thẻ riêng.
    Ca nhóm bot CHƯA TỪNG trả lời được → loại khỏi A/B (không phải lỗi bot, đừng đếm
    'bot không trả lời'); đã từng trả lời rồi thì giữ số liệu, chỉ dừng nhắn."""
    if db.get_setting("ab_unreach:" + conv_id):
        return
    db.set_setting("ab_unreach:" + conv_id, str(time.time()))
    _fu_clear(conv_id)
    try:
        with db._conn() as c:
            row = c.execute("SELECT replies FROM ab_stats WHERE pancake_conv_id=?",
                            (conv_id,)).fetchone()
        if row is not None and not row["replies"]:
            db.ab_contaminate(conv_id)
            db.log_webhook("ab_contaminate", f"{conv_id}: không gửi được (FB #551) — loại khỏi A/B")
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"unreach {conv_id}: {ex}")
    if _tag_id(TAG_UNREACH) is not None:
        add_tag(conv_id, TAG_UNREACH)
    else:
        db.log_webhook("api_noop", f"thẻ '{TAG_UNREACH}' chưa có trên page — tạo thẻ này trong "
                                   f"Pancake để nhân viên nhìn thấy ca không gửi được")


def normalize_pronoun(conv_id: str, text: str) -> str:
    """v0.1.72 (ca Nguyễn Tường): MỌI tin gửi khách (cả câu cố định: nhận ảnh, nhận SĐT, nhắc nhớ, hỏi thăm nhà thuốc…)
    đổi "anh/chị" theo đúng người: khách tự xưng cô/bác… → danh xưng đó + 'cháu'; biết giới tính → anh/chị + tên gọi."""
    if not text or not conv_id:
        return text
    try:
        users = [str(m.get("content") or "") for m in db.get_history(db.pancake_local_conv(conv_id)) if m.get("role") == "user"]
        t = engine._customer_title(users)
        if t:
            return engine._fix_title(text, t, users)
        g = _infer_gender(conv_id)
        if g not in ("male", "female"):
            return text
        nm = db.get_setting("name:" + conv_id) or ""
        call = call_name(nm, g) if nm else ""
        prof = f'GỌI KHÁCH: "{call}"' if call else ("xưng hô với khách: " + ("anh" if g == "male" else "chị"))
        return engine._fix_bare_name(engine._fix_pronoun(text, prof, users), prof)
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"normalize_pronoun {conv_id}: {ex}")
        return text


def send_message(conv_id: str, text: str) -> dict:
    """Gửi tin trả lời inbox. Public API Pancake yêu cầu action=reply_inbox."""
    text = normalize_pronoun(conv_id, text)
    _remember_sent(conv_id, text)
    r = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages",
             body={"action": "reply_inbox", "message": text})
    if not _body_ok(r):
        if _is_unreach(r):
            # v0.5.22 A3: khách không nhận được tin nữa — đánh dấu + dừng nhịp, KHÔNG log ❌
            db.log_webhook("send_unreach", f"{conv_id}: FB #551 — khách chặn page/xoá hội thoại/"
                                           f"hết cửa sổ, bot ngừng nhắn ca này")
            _mark_unreach(conv_id)
            r["unreachable"] = True
        else:
            db.log_webhook("send_fail", f"{conv_id}: {json.dumps(r, ensure_ascii=False)[:400]}")
        r["error"] = r.get("error") or f"send rejected: {json.dumps(r, ensure_ascii=False)[:200]}"
    return r


def probe(conv_id: str, text: str = "probe", variant: str = "2", raw_body: str = "",
          path: str = "", method: str = "POST", qs: str = "", base: str = "") -> dict:
    """Chẩn đoán API Pancake: gọi thật 1 request và trả NGUYÊN VĂN phản hồi (admin dùng).
    variant 1 = {"message"} · 2 = {"action":"reply_inbox","message"} · raw_body = JSON tuỳ ý.
    v0.5.23 (D2): thêm `qs` (query string, VD "since=2026-08-26&page_number=1") vì path chứa "?"
    bị vỡ ở _api; và `base` để thử API v2 / POS mà không phải sửa code."""
    body = None
    if raw_body:
        try:
            body = json.loads(raw_body)
        except Exception as ex:  # noqa: BLE001
            return {"error": f"raw_body không phải JSON: {ex}"}
    elif method.upper() != "GET":
        body = {"message": text} if str(variant) == "1" else {"action": "reply_inbox", "message": text}
    p = path or f"/pages/{PAGE_ID}/conversations/{conv_id}/messages"
    if "?" in p and not qs:          # gọi nhầm kiểu cũ: tự bóc phần sau dấu ? ra params
        p, _, qs = p.partition("?")
    params = dict(urllib.parse.parse_qsl(qs)) if qs else None
    _base = {"v1": BASE, "v2": BASE_V2, "pos": BASE_POS}.get(base, base or None)
    r = _api(method.upper(), p, params=params, body=body, base=_base)
    return {"method": method.upper(), "path": p, "params": params, "base": _base or BASE,
            "sent_body": body, "response": r, "body_ok": _body_ok(r)}


def add_tag(conv_id: str, tag_name: str) -> dict:
    """Gắn thẻ theo TÊN — tự tra tag_id qua GET tags (probe 25/08: API đòi action=add + tag_id;
    gửi tag_name bị từ chối 'Missing required field: action')."""
    tid = _tag_id(tag_name)
    if tid is None:
        db.log_webhook("api_fail", f"tag '{tag_name}' không tồn tại trên page — tạo thẻ này trong Pancake")
        return {"error": f"tag '{tag_name}' not found"}
    r = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/tags",
             body={"action": "add", "tag_id": tid})
    if not _body_ok(r):
        if _is_noop(r):   # v0.5.22 A2: thẻ đã gắn sẵn — không phải lỗi
            db.log_webhook("api_noop", f"tag {tag_name}: đã đúng sẵn — không có gì phải đổi")
        else:
            db.log_webhook("api_fail", f"tag {tag_name}: {json.dumps(r, ensure_ascii=False)[:300]}")
    return r


# ---- Assign: API đòi assignee_ids (mảng id nhân viên) — bot tự xoay vòng,
# ƯU TIÊN NGƯỜI ĐANG TRỰC TUYẾN (đúng logic "Ưu tiên trực tuyến" của Pancake, góp ý anh Na 25/08:
# chia mù cho bạn đang off thì ca kẹt). GET users trả is_online từng người — cache 60 giây.
# Danh sách trực: setting/ENV PANCAKE_ASSIGN_IDS; trống thì lấy round_robin_users.inbox của Pancake.
_assign_state = {"i": 0}
_users_cache = {"ts": 0.0, "online": set(), "rr_inbox": []}


def _refresh_users(force=False, ttl=60):
    if not force and time.time() - _users_cache["ts"] < ttl:
        return
    r = _api("GET", f"/pages/{PAGE_ID}/users")
    users = r.get("users") or []
    rr = (r.get("round_robin_users") or {}).get("inbox") or []
    if users or rr:
        _users_cache.update(
            ts=time.time(),
            online={str(u.get("id")) for u in users if u.get("is_online")},
            rr_inbox=[str(x) for x in rr])


def _assign_pool() -> list:
    v = db.get_setting("pancake_assign_ids") or os.environ.get("PANCAKE_ASSIGN_IDS", "")
    ids = [x.strip() for x in v.split(",") if x.strip()]
    if ids:
        return ids
    _refresh_users()
    return _users_cache["rr_inbox"]


def assign(conv_id: str, user_id: str = None) -> dict:
    if user_id:
        ids = [user_id]
    else:
        pool = _assign_pool()
        if not pool:
            db.log_webhook("api_fail", "assign: không có nhân viên trực (đặt PANCAKE_ASSIGN_IDS hoặc bật xoay vòng)")
            return {"error": "no assignees"}
        _refresh_users()
        online = [x for x in pool if x in _users_cache["online"]]
        cand = online or pool   # có người online → chỉ chia trong nhóm online; không ai → chia đều cả danh sách
        _assign_state["i"] += 1
        ids = [cand[_assign_state["i"] % len(cand)]]
        if not online:
            db.log_webhook("assign_offline", f"{conv_id}: không ai trực tuyến — giao {ids[0]}, SLA watcher sẽ nhắc")
    r = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/assign",
             body={"assignee_ids": ids})
    if not _body_ok(r):
        if _is_noop(r):   # v0.5.22 A2: đã giao đúng người sẵn — không phải lỗi
            db.log_webhook("api_noop", f"assign {conv_id}: đã giao đúng người sẵn — không có gì phải đổi")
        else:
            db.log_webhook("api_fail", f"assign: {json.dumps(r, ensure_ascii=False)[:300]}")
    return r


def mark_unread(conv_id: str) -> dict:
    return _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/unread", body={})


# v0.1.47 (chị Nga 22/10): bot mới chạy — muốn đọc lại MỌI ca bot chat. Pancake tự chuyển ca sang "đã đọc"
# khi page trả lời → bot trả lời xong (và gửi nhịp theo đuổi xong) thì đánh dấu lại CHƯA ĐỌC.
# Tắt: biến Railway PANCAKE_KEEP_UNREAD=0 (hoặc setting pancake_keep_unread=0).
def is_keep_unread() -> bool:
    v = db.get_setting("pancake_keep_unread")
    if v is None:
        v = os.environ.get("PANCAKE_KEEP_UNREAD", "1")
    return v == "1"


def _keep_unread(conv_id: str):
    if not is_keep_unread() or is_test_only():
        return
    def _later():
        # v0.1.57 (chị Nga 23/10: nhiều ca bot trả lời xong vẫn bị "đã đọc"): Pancake đánh dấu đã đọc khi nhận echo tin page
        # — echo có lúc về chậm hơn 3 giây → đánh dấu chưa đọc 3 lần (4s, 15s, 45s) và GHI LOG kết quả để kiểm tra.
        last = None
        for wait in (4, 11, 30):
            try:
                time.sleep(wait)
                last = mark_unread(conv_id)
            except Exception as ex:  # noqa: BLE001
                last = {"error": str(ex)}
        if not _body_ok(last or {}) and not _is_noop(last or {}):
            db.log_webhook("api_fail", f"keep_unread {conv_id}: {json.dumps(last, ensure_ascii=False)[:300]}")
        else:
            db.log_webhook("keep_unread", f"{conv_id}: đã đánh dấu chưa đọc")
    threading.Thread(target=_later, daemon=True).start()


def note(conv_id: str, text: str) -> dict:
    """Public API Pancake KHÔNG hỗ trợ note nội bộ (probe 25/08: /notes 404, messages chỉ cho
    reply_comment/reply_inbox/private_replies). Gói bàn giao nằm ở admin (bảng handoffs) + thẻ level."""
    db.log_webhook("note_skip", f"{conv_id}: {text[:200]}")
    return {"skip": "notes API không hỗ trợ"}


# ---- Lọc HTML: Pancake trả nội dung tin có thể bọc thẻ (<div>chào em</div>) ----
_RE_TAG = re.compile(r"<[^>]{1,200}>")


def _strip_html(t: str) -> str:
    import html as _html
    t = _RE_TAG.sub(" ", t or "")
    t = _html.unescape(t)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


# ---- Nhớ tin bot vừa gửi: phân biệt echo của chính bot với tin SALE gõ tay ----
_sent_lock = threading.Lock()
_sent = {}            # conv_id -> [(norm_text, ts), ...] giữ 10 phút


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip().lower())[:400]


def _remember_sent(conv_id, text):
    with _sent_lock:
        lst = _sent.setdefault(conv_id, [])
        lst.append((_norm(text), time.time()))
        _sent[conv_id] = [(t, ts) for t, ts in lst if time.time() - ts < 600][-20:]


def _was_sent_by_bot(conv_id, text) -> bool:
    """Tin from_page có phải do bot gửi không. 2 lớp: (1) bộ nhớ RAM phiên này;
    (2) DB — SỐNG SÓT QUA REDEPLOY (lỗi 25/08: push code xong RAM trắng, bot đọc lại
    echo của chính mình tưởng sale gõ tay → tự rút khỏi hội thoại đang chat dở).
    So substring vì reply lưu nguyên khối còn gửi đi theo từng phần."""
    n = _norm(text)
    if not n:
        return False
    with _sent_lock:
        if any(t == n for t, _ in _sent.get(conv_id, [])):
            return True
    for full in db.pancake_bot_sent_recent(conv_id):
        if n in _norm(_render_img_for_messenger(full)):
            return True
    return False


# ---- Dedupe: webhook có thể bắn trùng message; polling cũng đi qua đây ----
_seen_lock = threading.Lock()
_seen = {}          # key -> ts, tự dọn sau 1 giờ
_SEEN_TTL = 3600


def _already_seen(key: str) -> bool:
    with _seen_lock:
        now = time.time()
        for k in [k for k, t in _seen.items() if now - t > _SEEN_TTL]:
            _seen.pop(k, None)
        if key in _seen:
            return True
        _seen[key] = now
        return False


# ---- Cache thẻ: map tag_id <-> tên (10 phút) ----
_tags_cache = {"ts": 0.0, "map": {}}


def _refresh_tags(force=False):
    if not force and _tags_cache["map"] and time.time() - _tags_cache["ts"] < 600:
        return
    r = _api("GET", f"/pages/{PAGE_ID}/tags")
    m = {}
    for t in (r.get("tags") or r.get("data") or []):
        m[str(t.get("id"))] = t.get("text") or t.get("name") or ""
    if m:
        _tags_cache.update(ts=time.time(), map=m)


def _tag_id(name: str):
    """Tra tag_id theo tên (không phân biệt hoa thường). Không thấy → refresh 1 lần rồi chịu."""
    for attempt in (False, True):
        _refresh_tags(force=attempt)
        for i, n in _tags_cache["map"].items():
            if n.strip().lower() == (name or "").strip().lower():
                return int(i)
    return None


def _tag_names(ids_or_names) -> list:
    """Nhận list tag id hoặc tên (payload Pancake có thể trả cả hai dạng) → list tên."""
    names = []
    need_map = False
    for t in ids_or_names or []:
        if isinstance(t, dict):
            names.append(t.get("text") or t.get("name") or "")
        elif isinstance(t, str) and not t.isdigit():
            names.append(t)
        else:
            need_map = True
    if need_map:
        _refresh_tags()
        for t in ids_or_names or []:
            if isinstance(t, (int, str)) and str(t).isdigit():
                names.append(_tags_cache["map"].get(str(t), ""))
    return [n for n in names if n]


def _ab_state(conv_id: str) -> str:
    """Trạng thái ranh giới bot-người của hội thoại (pancake_map.state) — đọc bằng db._conn,
    KHÔNG sửa db.py. 'human_claimed' = người nhảy vào; 'returned' = bot tự chuyển."""
    try:
        with db._conn() as c:
            r = c.execute("SELECT state FROM pancake_map WHERE pancake_conv_id=?",
                          (conv_id,)).fetchone()
        return (r["state"] or "") if r else ""
    except Exception:  # noqa: BLE001
        return ""


def _ab_grp(conv_id):
    """Nhóm A/B đã ghi trong ab_stats (None = chưa có row → hội thoại ngoài phạm vi đo).
    Đọc db._conn trực tiếp để KHÔNG phải thêm hàm vào db.py (ghi chú v0.5.12)."""
    try:
        with db._conn() as c:
            r = c.execute("SELECT grp FROM ab_stats WHERE pancake_conv_id=?",
                          (conv_id,)).fetchone()
        return r["grp"] if r else None
    except Exception:  # noqa: BLE001
        return None


# ---- v0.1.85 (26/10, chị Nga — CÁCH A): KIỂM TRA TRƯỚC KHI NHẮC NHỚ ----
# Ngay trước mỗi lần gửi tin nhắc, bot hỏi lại Pancake: có thẻ Mua hàng / Người xử lý / Bot chốt đơn / ADR / Ko PH,
# hoặc nhân viên đã nhắn tay sau tin cuối của bot → huỷ nhắc. (Nhân viên gọi điện xong nên gắn thẻ "Mua hàng".)
FU_STOP_TAGS = {x.strip().lower() for x in (os.environ.get("PANCAKE_FU_STOP_TAGS") or
                "Mua hàng,Người xử lý,Để NV xử lý,Bot chốt đơn,ADR/Khiếu nại,Ko PH").split(",") if x.strip()}


def _store_tags(conv_id: str, conv_obj: dict):
    if not isinstance(conv_obj, dict) or not ("tags" in conv_obj or "tag_ids" in conv_obj):
        return
    names = [n for n in _tag_names(conv_obj.get("tags") or conv_obj.get("tag_ids") or []) if n]
    db.set_setting("tags:" + str(conv_id), json.dumps(names, ensure_ascii=False))


def _fu_stop_check(conv_id: str) -> str:
    """Trả lý do huỷ nhắc ('' nếu được nhắc)."""
    names = []
    try:
        names = json.loads(db.get_setting("tags:" + str(conv_id)) or "[]")
    except Exception:  # noqa: BLE001
        names = []
    try:
        r = _api("GET", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages")
    except Exception:  # noqa: BLE001
        r = {}
    if isinstance(r, dict) and "error" not in r:
        for holder in (r, r.get("conversation") or {}, r.get("conv") or {}):
            if isinstance(holder, dict) and ("tags" in holder or "tag_ids" in holder):
                names = [n for n in _tag_names(holder.get("tags") or holder.get("tag_ids") or []) if n] or names
        hit = [n for n in names if n.strip().lower() in FU_STOP_TAGS]
        if hit:
            return "có thẻ " + ", ".join(hit)
        # nhân viên nhắn tay SAU tin cuối của bot (tin page không khớp tin nào bot đã gửi)
        msgs = sorted(r.get("messages") or r.get("data") or [], key=lambda m: str(m.get("inserted_at") or ""))
        bot_said = {_norm(_strip_html(str(m.get("content") or ""))) for m in db.get_history(db.pancake_local_conv(conv_id))
                    if m.get("role") == "assistant"}
        for m in reversed(msgs):
            frm = str((m.get("from") or {}).get("id") or "")
            t = _strip_html(m.get("original_message") or m.get("message") or "")
            if frm != str(PAGE_ID):
                break                     # gặp tin khách trước → không có tin nhân viên sau đó
            if not t or _RE_SYS_NOTICE.search(t):
                continue
            nt = _norm(t)
            if any(nt[:120] in b or b[:120] in nt for b in bot_said if b):
                break                     # tới tin cuối của bot → các tin page trước đó (vd tin tự động quảng cáo) không tính
            if nt:
                return "nhân viên đã nhắn tay sau tin cuối của bot"
        return ""
    hit = [n for n in names if n.strip().lower() in FU_STOP_TAGS]
    return ("có thẻ " + ", ".join(hit)) if hit else ""


def _sync_human_tag(conv_id, conv_obj) -> bool:
    """Nếu hội thoại có thẻ van ngược ('Để NV xử lý' / 'Người xử lý') → bot rút vĩnh viễn.
    v0.5.17: thẻ này rơi vào ca NHÓM BOT mà bot vẫn đang trực (state bot_active) = CÓ NGƯỜI
    NHẢY VÀO → phải đánh dấu ca lai tạp, loại khỏi số liệu A/B. Trước đây chỉ nhánh 'sale gõ
    tay qua Pancake' mới loại, nên ca anh Na tự gắn thẻ chữa cháy 26/08 vẫn nằm trong số sạch.
    Ngoại lệ: ca BOT ĐÃ TỰ CHUYỂN NGƯỜI trước đó (state 'returned') thì thẻ này chỉ là xác
    nhận của nhân viên — đó là đường đi đúng của bot, KHÔNG loại."""
    if _is_reopened(conv_id):
        return False   # v0.1.25: ca đã mở lại cho bot — thẻ "Người xử lý" cũ còn trên ca không chặn nữa
    tags = conv_obj.get("tags") or conv_obj.get("tag_ids") or []
    if any((n or "").strip().lower() in TAG_HUMAN_NAMES for n in _tag_names(tags)):
        if not db.pancake_is_human(conv_id):
            bot_da_chuyen = db.pancake_is_blocked(conv_id)   # state == 'returned'
            db.pancake_claim_human(conv_id)
            _fu_clear(conv_id)          # v0.5.15: người tiếp quản → dừng nhịp theo đuổi
            db.log_webhook("human_tag", f"claim {conv_id}")
            if not bot_da_chuyen and _ab_grp(conv_id) == "bot":
                db.ab_contaminate(conv_id)
                db.log_webhook("ab_contaminate",
                               f"{conv_id}: thẻ chuyển người trên ca nhóm BOT đang trực "
                               f"→ loại khỏi số liệu A/B")
        return True
    return db.pancake_is_human(conv_id)


# ---- Lead SĐT: bắt SĐT khách nhắn + SĐT trong handoff (rule S2/S3) ----
# v0.5.21 (anh Na 28/08): regex cũ chỉ bắt 10 số LIỀN NHAU nên bỏ sót "0865 866 180",
# "0865.866.180", "+84865866180" — làm mẫu SĐT của A/B nhỏ đi oan. Nay cho phép dấu
# cách/chấm/gạch xen giữa các chữ số và tiền tố +84/84, rồi chuẩn hoá về dạng 0xxxxxxxxx.
_PSEP = r"[\s.\-–—]{0,2}"
_RE_PHONE = re.compile(r"(?<!\d)(?:\+?84" + _PSEP + r"|0)(?:\d" + _PSEP + r"){8}\d(?!\d)")


_RE_ORDER_QUERY = re.compile(r"\b(ship|shipper|giao hang|van don|ma don|don hang|xem lai don|kiem tra don|chua (thay|nhan)|bao gio (giao|nhan|toi|den)|"
                             r"huy don|doi dia chi|sua don|them don|doi don)\b")


def _phones_in_obj(obj, depth: int = 0) -> list:
    """v0.1.60: quét object Pancake (hội thoại / khách / danh sách tin) lấy SĐT ở các trường có chữ 'phone'
    (recent_phone_numbers, phone_numbers, conv_phone_numbers, phone_number...)."""
    out = []
    if depth > 4:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "phone" in str(k).lower():
                if isinstance(v, (str, int)):
                    out += find_phones(str(v))
                elif isinstance(v, list):
                    for x in v:
                        if isinstance(x, (str, int)):
                            out += find_phones(str(x))
                        elif isinstance(x, dict):
                            out += find_phones(str(x.get("phone_number") or x.get("phone") or x.get("captured") or ""))
            elif isinstance(v, (dict, list)) and k in ("page_customer", "customer", "customers", "conversation", "from"):
                out += _phones_in_obj(v, depth + 1)
    elif isinstance(obj, list):
        for x in obj[:20]:
            out += _phones_in_obj(x, depth + 1)
    return out


def _gender_in_obj(obj, depth: int = 0) -> str:
    """v0.1.73 (ca Ngô Hồng Thanh: Pancake hiện biểu tượng NAM mà bot không biết): tìm trường 'gender' trong object Pancake."""
    if depth > 4:
        return ""
    if isinstance(obj, dict):
        g = str(obj.get("gender") or "").lower()
        if g in ("male", "female"):
            return g
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and k in ("page_customer", "customer", "customers", "conversation", "from", "data"):
                g = _gender_in_obj(v, depth + 1)
                if g:
                    return g
    elif isinstance(obj, list):
        for x in obj[:10]:
            g = _gender_in_obj(x, depth + 1)
            if g:
                return g
    return ""


def _save_conv_gender(conv_id: str, conv: dict):
    g = _gender_in_obj(conv)
    if g and db.get_setting("gender:" + conv_id) != g and not db.get_setting("gender_self:" + conv_id):
        db.set_setting("gender:" + conv_id, g)


def _save_conv_phones(conv_id: str, conv: dict):
    ph = _phones_in_obj(conv)
    if ph and db.get_setting("phone:" + str(conv_id)) != ph[-1]:
        db.set_setting("phone:" + str(conv_id), ph[-1])


def _fetch_old_phone(conv_id: str) -> str:
    """v0.1.60 (chị Nga: ca chốt cách đây cả năm cũng không xin lại số): chưa biết SĐT → hỏi Pancake 1 lần/ngày:
    (1) SĐT Pancake lưu ở hội thoại/khách; (2) quét chữ các tin cũ khách gửi; (3) SĐT trên đơn POS đã đồng bộ."""
    key = "phonefetch:" + str(conv_id)
    last = _ts_setting(key)
    if last and time.time() - last < 86400:
        return ""
    db.set_setting(key, f"{time.time():.0f}")
    found = []
    try:
        r = _api("GET", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages")
        if isinstance(r, dict) and "error" not in r:
            found += _phones_in_obj({k: v for k, v in r.items() if k != "messages"}, 0)
            for m in r.get("messages") or r.get("data") or []:
                frm = (m.get("from") or {}).get("id")
                if frm and str(frm) == str(PAGE_ID):
                    continue          # tin page gửi (vd hotline) — bỏ
                found += find_phones(str(m.get("message") or m.get("original_message") or ""))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"phone fetch {conv_id}: {ex}")
    if not found:
        try:
            with db._conn() as c:
                _orders_table(c)
                row = c.execute("SELECT phone FROM ab_orders WHERE pancake_conv_id=? AND phone<>'' ORDER BY ts DESC LIMIT 1",
                                (str(conv_id),)).fetchone()
                if row:
                    found += find_phones(str(row[0]))
        except Exception:  # noqa: BLE001
            pass
    found = [p for p in found if p not in _PAGE_PHONES]
    if found:
        db.log_webhook("phone_known", f"{conv_id}: lấy được SĐT cũ của khách từ Pancake — bot không xin lại")
        return found[-1]
    return ""


_PAGE_PHONES = {"18001120", "18008308", "18008396"}


def _known_phone(conv_id: str, history: list = None) -> str:
    """v0.1.60: SĐT khách đã gửi trong hội thoại — số mới nhất trong lịch sử, hoặc số đã lưu (phone:<conv>) từ lần trước,
    hoặc SĐT của đơn đã nhớ để đẩy Nhanh. Lưu lại để lần sau (tin cũ trôi khỏi lịch sử) vẫn nhớ."""
    ph = ""
    for m in history or []:
        if m.get("role") == "user":
            f = find_phones(str(m.get("content") or ""))
            if f:
                ph = f[-1]
    if not ph:
        ph = db.get_setting("phone:" + str(conv_id)) or ""
    if not ph:
        try:
            ph = ((json.loads(db.get_setting("nhanh_last_order:" + str(conv_id)) or "{}").get("customer") or {}).get("phone") or "")
        except Exception:  # noqa: BLE001
            ph = ""
    if not ph:
        ph = _fetch_old_phone(conv_id)
    ph = re.sub(r"\D", "", ph or "")
    if len(ph) == 10 and ph.startswith("0"):
        if db.get_setting("phone:" + str(conv_id)) != ph:
            db.set_setting("phone:" + str(conv_id), ph)
        return ph
    return ""


def find_phones(text: str) -> list:
    """SĐT trong câu → chuẩn hoá 0xxxxxxxxx, bỏ trùng, giữ thứ tự xuất hiện."""
    out = []
    for m in _RE_PHONE.finditer(text or ""):
        d = re.sub(r"\D", "", m.group(0))
        if d.startswith("84"):
            d = "0" + d[2:]
        if len(d) == 10 and d[0] == "0" and d[1] not in "01" and d not in out:
            out.append(d)
    return out


def ab_save_phones(conv_id, grp, phones, src="webhook") -> list:
    """v0.5.21: lưu SĐT THẬT cho CẢ HAI nhóm A/B. Trước đây chỉ nhóm bot ghi số (qua
    _respond → bảng leads), nhóm người chỉ có cờ 0/1 nên không tra được đơn — anh Na hỏi
    28/08. Ghi thẳng qua db._conn để KHỎI sửa db.py (v0.5.12: db.py đẩy GitHub hay bị chặn)."""
    if not phones:
        return []
    now = time.time()
    try:
        with db._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS ab_phones("
                      "pancake_conv_id TEXT, phone TEXT, grp TEXT, src TEXT, ts REAL,"
                      " PRIMARY KEY(pancake_conv_id, phone))")
            for ph in phones:
                c.execute("INSERT OR IGNORE INTO ab_phones(pancake_conv_id,phone,grp,src,ts)"
                          " VALUES(?,?,?,?,?)", (conv_id, ph, grp, src, now))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"ab_save_phones {conv_id}: {ex}")
    return phones


def _capture_leads(local_id, text, handoffs):
    for ph in find_phones(text):
        db.add_lead(local_id, "pancake", ph, "khách để lại SĐT trong hội thoại")
    for h in handoffs or []:
        if h.get("phone"):
            db.add_lead(local_id, "pancake", h["phone"], h.get("reason", "")[:200])


def _handoff_note(handoffs, order_note=""):
    lines = []
    for h in handoffs:
        lvl = h.get("level", 2)
        lines.append(f"[Level {lvl}] {h.get('reason','')}" +
                     (f" — SĐT: {h.get('phone')}" if h.get("phone") else " — chưa có SĐT"))
    if order_note:
        lines.append(order_note)
    return "GÓI BÀN GIAO (bot tự động):\n" + "\n".join(lines) if lines else ""


# ================================ GOM TIN 60 GIÂY (kế hoạch #17) ================================
# Tin khách đến không xử lý ngay: chờ BATCH_SECONDS, khách nhắn thêm thì gộp, trả lời 1 lần.
_batch_lock = threading.Lock()
_batches = {}       # conv_id -> {"texts": [...], "timer": Timer, "meta": {...}}
_payload_samples = 0   # v0.5.27 B1: số payload đã ghi mẫu trong tiến trình này


def _enqueue(conv_id, text, meta, imgs=None):
    with _batch_lock:
        b = _batches.get(conv_id)
        if b:
            b["texts"].append(text)
            b["timer"].cancel()
        else:
            b = _batches[conv_id] = {"texts": [text], "meta": meta}
        if imgs:
            b.setdefault("imgs", []).extend(imgs)
            b["imgs"] = b["imgs"][:3]
        wait = BATCH_SECONDS if db.get_setting("bot_replied:" + str(conv_id)) else BATCH_FIRST_SECONDS
        t = threading.Timer(wait, _flush, args=(conv_id,))
        t.daemon = True
        b["timer"] = t
        t.start()
    return len(b["texts"])


def _flush(conv_id):
    try:
        db.set_setting("bot_replied:" + str(conv_id), "1")   # v0.1.22: từ lượt sau chờ BATCH_SECONDS (30s)
    except Exception:  # noqa: BLE001
        pass
    with _batch_lock:
        b = _batches.pop(conv_id, None)
    if not b:
        return
    try:
        res = _respond(conv_id, "\n".join(b["texts"]), b["meta"], images=b.get("imgs"))
        db.log_webhook("reply", json.dumps(res, ensure_ascii=False))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"flush {conv_id}: {ex}")


# ================================ XỬ LÝ LÕI ================================
def handle_event(payload: dict) -> dict:
    """Xử lý 1 sự kiện webhook Pancake: lọc → gom tin (trả lời chạy ở timer).
    Idempotent + chỉ INBOX + tôn trọng kill switch."""
    if is_killed():
        return {"skip": "kill_switch"}

    etype = payload.get("event_type")
    data = payload.get("data", {}) or {}
    conv = data.get("conversation", {}) or {}
    msg = data.get("message", {}) or {}
    conv_id = conv.get("id") or msg.get("conversation_id")

    # sự kiện conversation (đổi thẻ, assign...) — chỉ dùng để bắt thẻ "Người xử lý"
    if etype == "conversation" and conv_id:
        _store_tags(conv_id, conv)   # v0.1.85: nhớ thẻ hiện tại của hội thoại (kiểm tra trước khi nhắc nhớ)
        claimed = _sync_human_tag(conv_id, conv)
        return {"ok": True, "event": "conversation", "conv_id": conv_id, "human": claimed}

    if etype != "messaging":
        return {"skip": f"event={etype}"}

    # v0.5.27 B1: payload có thể mang sẵn ad_ids/ads — tận dụng, không thì _src_loop lo.
    if conv_id:
        try:
            _src_from_conv_obj(conv_id, conv)
        except Exception:  # noqa: BLE001
            pass
        try:
            _store_tags(conv_id, conv)         # v0.1.85
            _save_conv_phones(conv_id, conv)   # v0.1.60: SĐT Pancake đã nhận diện trong hội thoại (kể cả tin cũ)
            _save_conv_gender(conv_id, conv)   # v0.1.73: giới tính Pancake có sẵn trong payload thì lấy luôn
        except Exception:  # noqa: BLE001
            pass
    # sampler: ghi lại bộ khoá payload vài lần đầu mỗi tiến trình để đối chiếu tài liệu
    global _payload_samples
    if _payload_samples < 3 and etype == "messaging":
        _payload_samples += 1
        db.log_webhook("payload_keys", json.dumps(
            {"conv": sorted(conv.keys())[:25], "msg": sorted(msg.keys())[:25]},
            ensure_ascii=False)[:500])

    conv_type = (conv.get("type") or data.get("type") or "").upper()
    # 7.6: chỉ auto-reply INBOX; COMMENT đi nhánh D1 (v0.5.34), loại khác bỏ qua
    if conv_type and conv_type != "INBOX":
        if conv_type == "COMMENT":
            return handle_comment(conv, msg, conv_id)
        return {"skip": f"type={conv_type}", "conv_id": conv_id}

    text = _strip_html((msg.get("message") or msg.get("text") or ""))
    msg_id = msg.get("id") or msg.get("message_id") or ""

    # A/B test: chia nhóm theo hash customer_id, gán 1 lần rồi giữ nguyên.
    # Hội thoại THỬ NỘI BỘ (#tm) được MIỄN TRỪ A/B — luôn thuộc bot, kể cả đã lỡ rơi nhóm người.
    customer = conv.get("customer_id")
    grp = db.pancake_ab_group(conv_id, customer, _ab_percent()) if conv_id else "bot"
    if conv_id and TEST_KEYWORD in text.lower():
        db.pancake_mark_test(conv_id)
        db.log_webhook("test_conv", f"hội thoại thử {conv_id}")
    if conv_id and db.pancake_is_test(conv_id):
        grp = "bot"

    # tin do page gửi: echo tin bot → bỏ qua; nhóm NGƯỜI → đó là sale trả lời, ghi metric;
    # nhóm BOT mà sale gõ tay → van an toàn phụ: bot rút + đánh dấu ca lai tạp
    if msg.get("from", {}).get("id") == PAGE_ID or msg.get("is_from_page"):
        if text and conv_id and not _was_sent_by_bot(conv_id, text):
            if _already_seen(f"page:{conv_id}:{msg_id or _norm(text)}"):
                return {"skip": "dup_page", "conv_id": conv_id}
            # v0.5.13: tin từ page KHÔNG có định danh người thật = tin TỰ ĐỘNG (câu chào của
            # quảng cáo, auto-reply...) — không phải sale gõ tay. Sự cố Anh Thi 26/08: welcome
            # message của ad bắn sau 3 giây làm van ngược claim nhầm → bot im + ca bị loại khỏi
            # A/B với MỌI khách vào từ ad. Tin người thật gõ qua Pancake luôn kèm uid/admin_name
            # (đã kiểm chứng bằng GET messages ca thật). Tin auto: chỉ ghi log, đi tiếp như cũ.
            _f = msg.get("from") or {}
            _page_said_add(conv_id, text)   # v0.1.41: nhớ tin page (nhân viên/tự động) để bot không chào lại
            if not (_f.get("uid") or _f.get("admin_name") or msg.get("admin_id")):
                db.log_webhook("page_auto", f"{conv_id}: tin tự động của page — không coi là sale: {text[:120]}")
                return {"skip": "page_auto", "conv_id": conv_id}
            _touch_human(conv_id)   # v0.1.25: nhân viên vừa gõ tay → tính lại mốc mở lại; ca đang mở thì đóng lại
            if grp == "human":
                db.ab_reply(conv_id)          # sale trả lời nhóm đối chứng — đo response time
                return {"ok": True, "ab": "human_reply", "conv_id": conv_id}
            if not db.pancake_is_blocked(conv_id):
                db.pancake_claim_human(conv_id)
                db.ab_contaminate(conv_id)    # ca nhóm bot bị sale nhảy vào → loại khỏi số liệu
                db.log_webhook("sale_typed", f"claim {conv_id}")
                return {"ok": True, "claimed_by_sale_message": True, "conv_id": conv_id}
        return {"skip": "from_page", "conv_id": conv_id}

    # v0.5.15: TIN KHÔNG CÓ CHỮ — trước đây chặn thẳng ở đây nên mất cả đơn đã chốt: ca chị
    # Vì Trúc 26/08, bot đọc lại đơn 15:21:44, khách trả 👍 lúc 15:21:54, bot im, mà A/B cũng
    # không đếm là khách đã phản hồi (chặn trước cả ab_in). Shape thật: message rỗng +
    # attachments=[{"type":"sticker"}]. Sticker → vào não bot; ảnh/tệp → chuyển người.
    att = ""
    _card = ""
    try:
        _card = _card_text(msg)
    except Exception:  # noqa: BLE001
        _card = ""
    if _card:
        db.log_webhook("card_in", f"{conv_id}: {_card[:200]}")
        text = (_card + ("\n" + text if text else "")).strip()
    if not text:
        att = _attach_kind(msg)
        if not att:
            db.log_webhook("empty_msg", json.dumps(
                {"conv_id": conv_id, "keys": sorted(msg.keys())[:20],
                 "att": str(msg.get("attachments") or "")[:300]}, ensure_ascii=False)[:900])
            if conv_id and is_enabled() and not is_test_only():
                mark_unread(conv_id)    # v0.1.91: tin bot không đọc được → để chưa đọc cho nhân viên thấy
            return {"skip": "empty_text", "conv_id": conv_id}
        dk = msg_id or f"{att}:{msg.get('inserted_at') or msg.get('created_time') or ''}"
        if _already_seen(f"{conv_id}:att:{dk}"):
            return {"skip": "dup", "conv_id": conv_id}
        db.log_webhook("no_text_msg", f"{conv_id}: tin không có chữ, loại '{att}'")
        imgs = _attach_urls(msg) if _vision_on() else []
        if att == "sticker":
            text = STICKER_SEE if imgs else STICKER_TEXT
        else:
            text = IMG_SEE if imgs else ATT_MARK
    elif _already_seen(f"{conv_id}:{msg_id or _norm(text)}"):
        return {"skip": "dup", "conv_id": conv_id}
    else:
        # v0.5.37: tin CÓ chữ kèm ảnh (trước đây ảnh bị bỏ rơi hoàn toàn) — nhặt link cho não nhìn
        imgs = _attach_urls(msg) if _vision_on() else []

    # xoá mã thử khỏi nội dung trước khi đưa vào não bot (đánh dấu test đã làm ở trên)
    if TEST_KEYWORD in text.lower():
        text = re.sub(re.escape(TEST_KEYWORD), "", text, flags=re.I).strip() or "chào shop"

    # v0.5.30 C4: tin của khách thường mang from.name — xét và lưu tên chào 1 lần
    if conv_id:
        _maybe_save_name(conv_id, (msg.get("from") or {}).get("name") or "")

    # ghi metric tin khách vào (cả 2 nhóm) + bắt cờ SĐT
    # v0.5.21: đồng thời LƯU SỐ THẬT cho cả 2 nhóm (bảng ab_phones) để tra đơn về sau.
    _phones = find_phones(text)
    is_new = db.ab_in(conv_id, grp, bool(_phones))
    if _phones:
        ab_save_phones(conv_id, grp, _phones)
    if db.pancake_is_test(conv_id):
        db.ab_contaminate(conv_id)   # hội thoại thử không được tính vào số liệu A/B
    # v0.5.19 (anh Na chốt 27/08): khách gửi ẢNH/TỆP thì bot CỐ Ý không đoán nội dung mà
    # chuyển người — ca đó bot không có cơ hội bán, để trong số liệu là oan cho bot (trước
    # đây bị đếm "bot không trả lời"). Loại khỏi A/B ở CẢ HAI NHÓM để hai tập cùng tiêu chí.
    if att and att != "sticker":
        db.ab_contaminate(conv_id)
        db.set_setting("ab_att:" + conv_id, "ảnh" if att == "image" else "tệp")
        db.log_webhook("ab_contaminate", f"{conv_id}: khách gửi {att} — loại khỏi A/B (cả 2 nhóm)")

    # NHÓM NGƯỜI: bot tuyệt đối không nhắn — chỉ định tuyến ca mới về sale như cũ
    # (chế độ test-only thì cũng không đụng vào hội thoại thật: không tag/assign gì)
    if grp == "human":
        # v0.5.12: gắn thẻ theo CỜ DB (không theo is_new) — gắn bù được cho hội thoại cũ
        # sinh ra trong chế độ thử / trước go-live nên chưa từng có thẻ (anh Na phát hiện
        # 26/08). Assign + đánh chưa đọc vẫn CHỈ làm với ca mới — ca cũ sale đang chăm.
        if is_enabled() and not is_test_only() and not _ab_tagged(conv_id):
            add_tag(conv_id, TAG_AB_HUMAN)
            _mark_ab_tagged(conv_id)
            if is_new:
                assign(conv_id)          # round robin về sale trực
                mark_unread(conv_id)
        return {"ok": True, "ab": "human", "conv_id": conv_id, "first": is_new}

    # v0.1.25: khách cũ quay lại sau khi nhân viên im quá REOPEN_HOURS → mở lại cho bot
    _maybe_reopen(conv_id, conv)
    # NHÓM BOT — thẻ "Người xử lý" trên payload / hội thoại đã trả về → bot im (mục 7.3)
    if _sync_human_tag(conv_id, conv) or db.pancake_is_blocked(conv_id):
        # v0.5.26 — LỖ HỔNG 3 (anh Na phát hiện gián tiếp 28/08: bot tụt 100%→98,6%):
        # nếu NGƯỜI tiếp quản TRƯỚC khi ca có dòng trong ab_stats (sale gõ tay lúc 19:13,
        # khách nhắn tiếp lúc 19:17) thì db.ab_contaminate lúc claim chạy vào KHÔNG có dòng
        # nào ⇒ cờ loại rơi mất, rồi ab_in tạo dòng mới sạch ⇒ ca quay lại nhóm BOT với 0
        # lượt trả lời và bị đếm oan là "bot không trả lời". Dòng ab_stats giờ đã tồn tại
        # (ab_in ở trên vừa chạy) nên đánh dấu lại ở đây là chắc chắn.
        # CHỈ loại ca NGƯỜI TIẾP QUẢN (human_claimed); ca 'returned' là bot TỰ chuyển nhân
        # viên — đường đi đúng của bot, vẫn tính vào số liệu (quy tắc v0.5.17).
        if _ab_state(conv_id) == "human_claimed":
            db.ab_contaminate(conv_id)
        return {"skip": "human_or_returned", "conv_id": conv_id}

    # v0.5.11: gắn thẻ "Bot" NGAY TIN ĐẦU TIÊN — không đợi hết cửa gom tin 45s mới tag.
    # Sale nhìn thẻ là biết ca của bot để không gõ tay vào (mỗi ca sale nhảy vào là 1 ca
    # lai tạp bị loại khỏi số liệu A/B — góp ý anh Na 26/08). Chế độ test-only thì không
    # đụng hội thoại thật, giống nhánh nhóm người ở trên.
    # v0.5.12: theo cờ DB thay vì is_new — hội thoại cũ chưa có thẻ cũng được gắn bù.
    if is_enabled() and not is_test_only() and not _ab_tagged(conv_id):
        add_tag(conv_id, TAG_BOT)
        _mark_ab_tagged(conv_id)

    # Chế độ thử: hội thoại KHÔNG phải test thì chỉ ghi nhận, KHÔNG soạn nháp
    # (đỡ tốn API + đỡ gây hiểu lầm "bot trả lời hội thoại lạ" — góp ý anh Na 25/08)
    if is_test_only() and not db.pancake_is_test(conv_id):
        return {"ok": True, "listen_only": True, "conv_id": conv_id}

    meta = {"customer": customer or msg.get("from", {}).get("id")}
    # v0.5.27 B9: ca nhà thuốc — khách nhắn lại SAU câu hỏi thăm → giao người ngay (không để
    # bot mời lại online); khách tự quay lại TRƯỚC giờ hỏi thăm → huỷ hẹn, bot chat tiếp thường.
    _ph = _pharm_get(conv_id)
    if _ph:
        if _ph.get("sent"):
            return _pharm_handoff(conv_id, meta, text)
        _pharm_clear(conv_id)
    # v0.5.15: ảnh/tệp → bot KHÔNG đoán nội dung (có thể là đơn thuốc, kết quả nội soi) mà
    # ghi nhận 1 câu rồi chuyển người thật (anh Na chốt 26/08).
    if att and att != "sticker" and not imgs:
        return _attach_handoff(conv_id, att, meta)   # tệp/video hoặc ảnh không lấy được link
    # v0.5.22 A7: khách gửi TRẦN SĐT — chuyển người NGAY, không chờ nhịp 1 (30 phút)
    if not att:
        bp = _bare_phone(text)
        if bp and PHONE_STOP:
            return _phone_handoff(conv_id, bp, meta, text)
        # v0.1.22 (chị Nga 16/10): khách gửi SĐT mà còn thiếu thông tin → bot VẪN chat tiếp
        # (hỏi nốt tên/địa chỉ/sản phẩm, trả lời câu hỏi kèm theo); đơn đủ thì build_order + HANDOFF như thường.
    _fu_touch(conv_id, has_phone=bool(_RE_PHONE.search(text)))
    if db.get_setting("cfw:" + str(conv_id)):
        db.set_setting("cfw:" + str(conv_id), "")   # v0.1.81: khách đã trả lời sau tổng hợp đơn → không cần đợi 10 phút
    n = _enqueue(conv_id, text, meta, imgs)
    return {"ok": True, "queued": n, "conv_id": conv_id, "batch_seconds": BATCH_SECONDS,
            "attachment": att or None}


def _page_said_add(conv_id: str, text: str):
    """v0.1.41 (21/10, chị Nga): tin page gửi khách mà KHÔNG phải bot (nhân viên nhắc khách, tin tự động,
    AI agent của Pancake...) → nhớ lại để lần tới bot trả lời: đưa vào lịch sử như tin của page,
    bot KHÔNG chào lại và tiếp nối đúng mạch."""
    try:
        cur = json.loads(db.get_setting("page_said:" + str(conv_id)) or "[]")
    except Exception:  # noqa: BLE001
        cur = []
    cur = (cur + [str(text)[:600]])[-5:]
    db.set_setting("page_said:" + str(conv_id), json.dumps(cur, ensure_ascii=False))


def _page_said_flush(conv_id: str, local_id) -> int:
    try:
        cur = json.loads(db.get_setting("page_said:" + str(conv_id)) or "[]")
    except Exception:  # noqa: BLE001
        cur = []
    for t in cur:
        db.add_message(local_id, "assistant", t)
    if cur:
        db.set_setting("page_said:" + str(conv_id), "[]")
    return len(cur)


_RE_NO_FU_TEXT = re.compile(r"hỏi ý kiến bác sĩ|tham khảo ý kiến bác sĩ|ý kiến của bác sĩ|bác sĩ (điều trị )?(đồng ý|cho phép)|"
                            r"khi bé cai sữa|chưa nên dùng (các |sản phẩm|sâm|hồng sâm|loại)|(chưa|không) dùng được (sản phẩm|loại|hồng sâm|sâm|ạ)|"
                            r"(chưa|không) nên dùng (sản phẩm|hồng sâm|lúc này)", re.I)


def _no_followup_reason(result: dict) -> str:
    """v0.1.56: lý do KHÔNG nhắc nhớ — tool an toàn trả BLOCK/NO_GUIDANCE/khuyên hỏi bác sĩ, hoặc câu trả lời nói khách chưa dùng được.
    Ngoại lệ: cùng lượt đó bot đang mời sản phẩm KHÁC dùng được (vd mẹ sau sinh → Nước Hồng sâm, có báo giá) → vẫn nhắc nhớ bình thường."""
    reply = result.get("reply") or ""
    traces = [tr for tr in (result.get("tool_trace") or []) if tr.get("tool") == "compliance_check" and isinstance(tr.get("output"), dict)]
    if any(tr["output"].get("verdict") in ("OK", "CAUTION") and not any(re.search(r"bác sĩ", h.get("action") or "")
           for h in tr["output"].get("caution_hits") or []) for tr in traces) and re.search(r"\d{2,3}\.000đ", reply):
        return ""
    for tr in result.get("tool_trace") or []:
        if tr.get("tool") != "compliance_check" or not isinstance(tr.get("output"), dict):
            continue
        out = tr["output"]
        if out.get("verdict") in ("BLOCK", "NO_GUIDANCE"):
            return f"an toàn: {out.get('verdict')} ({out.get('product', '')})"
        for h in out.get("caution_hits") or []:
            if re.search(r"bác sĩ", h.get("action") or "", re.I) and re.search(r"trước|tham khảo|hỏi ý kiến", h.get("action") or "", re.I) \
                    and not re.search(r"dùng được\b", (h.get("action") or "")[:40], re.I):
                return f"khuyên hỏi bác sĩ ({h.get('key')})"
    if _RE_NO_FU_TEXT.search(reply) and not re.search(r"\d{2,3}\.000đ", reply):
        return "bot đã nói khách chưa dùng được / cần hỏi bác sĩ"
    return ""


_RE_PLEASANT_ASCII = re.compile(
    r"^(?:(?:da|vang|uh|u|um|ok|oke|okie|okay|o ke|ok em|oki|ừ|duoc|dc|roi|nhe|nha|a|em|chi|anh|co|bac|chau|ban|shop|nhieu|lam|"
    r"cam on|cam o|camon|thanks|thank you|thank|tks|thanks em|"
    r"chuc[a-z ]{0,80}|chao em|chao|bye|tam biet|good night|ngu ngon|"
    r"hi|hihi|haha|hehe|tuyet|hay qua|dep qua|de thuong|qua|ve|thuong)[\s,.!~:)(]*)+$")


def _is_pleasantry(text: str) -> bool:
    """Sticker / like / ảnh không chữ / lời chào, cảm ơn, chúc ngắn — không có câu hỏi hay nội dung mua hàng."""
    t = (text or "").strip()
    if t in (STICKER_TEXT, STICKER_SEE):
        return True
    if t in (IMG_SEE, ATT_MARK):
        return False        # v0.1.77: ảnh không chữ có thể là ảnh hộp sản phẩm / biên lai → luôn để bot/nhân viên xử lý
    if "?" in t or len(t) > 90:
        return False
    f = re.sub(r"[^\w\s,.!~:)(]", " ", _fold_name(t)).strip()
    f = re.sub(r"\s+", " ", f)
    return bool(f) and bool(_RE_PLEASANT_ASCII.match(f))


def _closing_state(prior: list) -> bool:
    """Tin bot gần nhất KHÔNG phải câu hỏi chờ khách trả lời (đã cảm ơn / chào / chúc) → khách gửi xã giao thì không cần đáp."""
    bots = [str(m.get("content") or "") for m in prior or [] if m.get("role") == "assistant" and (m.get("content") or "").strip()]
    users = [str(m.get("content") or "") for m in prior or [] if m.get("role") == "user"]
    if not bots or not users:
        return False
    last_b = re.sub(r"\[[A-Z]+:[^\]]*\]", "", bots[-1]).strip()
    if last_b.endswith("?") or re.search(r"\?\s*(🌿|😊|🙏)?\s*$", last_b) or "?" in last_b[-200:]:
        return False
    if re.search(r"xác nhận|kiểm tra giúp|kiểm tra lại|chuyển khoản|chụp|địa chỉ|số điện thoại|tổng tiền|lên đơn", last_b, re.I):
        return False        # v0.1.77: đang chốt đơn / chờ khách xác nhận → "ok" là ĐỒNG Ý, phải xử lý tiếp
    return bool(re.search(r"cảm ơn|cám ơn|chúc|tạm biệt|hẹn gặp|nhắn (lại )?cho em|cứ nhắn|ý nghĩa|ấm áp", last_b, re.I)) \
        or _is_pleasantry(users[-1])


# ---- v0.1.74 (25/10, chị Nga): MỖI LƯỢT BOT ĐỌC TOÀN BỘ HỘI THOẠI TRÊN PANCAKE ----
# Trước đây bot chỉ thấy tin lưu trong DB của bot (tin trước khi có bot, tin nhân viên nhắn từ lâu, tin của ca cũ không có)
# → hỏi lại thông tin khách đã cấp. Nay mỗi lượt lấy lịch sử thật từ Pancake: tin khách + tin page (bot VÀ nhân viên).
FULL_HISTORY = os.environ.get("PANCAKE_FULL_HISTORY", "1") == "1"
FULL_HISTORY_MAX = int(os.environ.get("PANCAKE_FULL_HISTORY_MAX", "60"))   # tối đa số tin gần nhất đưa cho AI
_RE_SYS_NOTICE = re.compile(r"đã trả lời một quảng cáo|replied to an ad|đã đặt giai đoạn|đã gắn thẻ|đã chuyển|đã giao|"
                            r"đã bắt đầu cuộc trò chuyện|started a conversation", re.I)


def _pancake_history(conv_id: str) -> list:
    """Lịch sử thật trên Pancake → [{role, content}] theo thứ tự thời gian. Lỗi → []."""
    if not FULL_HISTORY or not PAGE_ID:
        return []
    msgs, cur = [], 0
    for _ in range(3):                         # tối đa 3 trang (Pancake trả ~25–30 tin/trang)
        params = {"current_count": cur} if cur else None
        r = _api("GET", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages", params=params)
        page = (r.get("messages") or r.get("data") or []) if isinstance(r, dict) and "error" not in r else []
        if not page:
            break
        new = [m for m in page if m.get("id") not in {x.get("id") for x in msgs}]
        if not new:
            break
        msgs = new + msgs
        cur = len(msgs)
        if len(msgs) >= FULL_HISTORY_MAX or len(page) < 20:
            break
    msgs.sort(key=lambda m: str(m.get("inserted_at") or m.get("created_time") or ""))
    out = []
    for m in msgs[-FULL_HISTORY_MAX:]:
        frm = str((m.get("from") or {}).get("id") or "")
        t = _strip_html(m.get("original_message") or m.get("message") or "")
        if not t:
            atts = m.get("attachments") or []
            if not atts:
                continue
            kind = str((atts[0] or {}).get("type") or "")
            try:
                _ct = _card_text(m)
            except Exception:  # noqa: BLE001
                _ct = ""
            if _ct and not (frm and frm == str(PAGE_ID)):
                out.append({"role": "user", "content": _ct.replace("[", "(").replace("]", ")")[:400]})
                continue
            # v0.1.86: KHÔNG dùng dạng ngoặc vuông (AI bắt chước thành "[ảnh: …]" gửi cho khách)
            if frm and frm == str(PAGE_ID):
                t = "(page đã gửi ảnh)"
            else:
                t = "(khách gửi sticker)" if "sticker" in kind else "(khách gửi ảnh/tệp)"
        if _RE_SYS_NOTICE.search(t) and len(t) < 120:
            continue
        role = "assistant" if frm and frm == str(PAGE_ID) else "user"
        out.append({"role": role, "content": t[:800]})
    return out


def _merge_history(api_hist: list, db_hist: list, current: str) -> list:
    """Lấy lịch sử Pancake (đầy đủ, có cả tin nhân viên) làm nền; bỏ các tin khách CUỐI (chính là lượt đang trả lời)
    rồi gắn tin hiện tại (đã gộp) vào cuối. Pancake lỗi / ngắn hơn DB → dùng DB như cũ."""
    if not api_hist:
        return db_hist
    h = list(api_hist)
    cur_n = _norm(re.sub(r"\[[^\]]*\]", " ", current or ""))
    # chỉ bỏ các tin khách CUỐI thuộc lượt hiện tại (chữ nằm trong tin đã gộp, hoặc sticker/ảnh) — tin cũ hơn giữ lại
    while h and h[-1]["role"] == "user":
        last = _norm(re.sub(r"\[[^\]]*\]", " ", h[-1]["content"]))
        if not last or (last and last in cur_n):
            h.pop()
        else:
            break
    if sum(1 for m in h if m["role"] == "user") < sum(1 for m in db_hist[:-1] if m.get("role") == "user"):
        return db_hist                          # Pancake trả thiếu → giữ DB
    out = []
    for m in h:
        if out and out[-1]["role"] == "user" and m["role"] == "user":
            out[-1] = {"role": "user", "content": out[-1]["content"] + "\n" + m["content"]}   # tin khách cũ liền nhau → gộp
        else:
            out.append(dict(m))
    if out and out[-1]["role"] == "user":       # tin cũ của khách chưa ai trả lời → gộp vào lượt này, ghi rõ để AI phân biệt
        old = out.pop()["content"]
        return out + [{"role": "user", "content": f"(Tin khách gửi trước đó, chưa được trả lời: {old})\n{current}"}]
    return out + [{"role": "user", "content": current}]


_RE_ACCUSE_HARD = re.compile(r"(?<![A-Za-zÀ-ỹĐđ])(lừa đảo|lừa gạt|lừa đảo|bịp|bóc phốt|phốt|công an|tố cáo|đi kiện|sẽ kiện|khởi kiện|kiện (bên em|công ty|shop|cửa hàng|các người|chúng mày|ra tòa)|bán hàng giả|hàng giả hết|"
                             r"đồ chó|loại chó|thằng chó|mất dạy|vô học|đm|đmm|dm|đéo|cút|láo toét|khốn nạn)(?![A-Za-zÀ-ỹĐđ])", re.I)


def _respond(conv_id: str, text: str, meta: dict, images: list = None) -> dict:
    """Hết cửa gom tin: gọi engine và gửi trả lời + xử lý trả về người."""
    if is_killed():
        return {"skip": "kill_switch", "conv_id": conv_id}
    if db.pancake_is_blocked(conv_id):
        return {"skip": "human_or_returned", "conv_id": conv_id}

    local_id = db.pancake_local_conv(conv_id, customer=meta.get("customer"))
    if _page_said_flush(conv_id, local_id):   # v0.1.41: tin nhân viên/page gửi trước đó → vào lịch sử, bot không chào lại
        db.log_webhook("page_ctx", f"{conv_id}: đưa tin page/nhân viên gửi trước vào ngữ cảnh — bot tiếp nối, không chào lại")
    _prior = db.get_history(local_id)
    db.add_message(local_id, "user", text)
    # v0.1.67 (24/10, ca Nguyễn Khuê): hội thoại đã cảm ơn/chào xong, khách gửi tiếp ảnh chúc, like, "ô kê", "chúc em buổi tối…"
    # → bot KHÔNG trả lời từng tin (chào nhiều quá). Tin khách vẫn để chưa đọc cho nhân viên xem; không nhắc nhớ.
    if _is_pleasantry(text) and _closing_state(_prior):
        _fu_clear(conv_id)
        try:
            mark_unread(conv_id)   # v0.1.77: tin khách vẫn nổi để nhân viên xem
        except Exception:  # noqa: BLE001
            pass
        db.log_webhook("pleasantry_skip", f"{conv_id}: khách gửi lời chào/sticker sau khi đã kết thúc — bot không trả lời")
        return {"ok": True, "skip": "pleasantry", "conv_id": conv_id}
    history = db.get_history(local_id)
    try:   # v0.1.74: đọc toàn bộ hội thoại thật trên Pancake (cả tin nhân viên, tin cũ trước khi có bot)
        _ph = _pancake_history(conv_id)
        if _ph:
            _merged = _merge_history(_ph, [dict(m) for m in history], text)
            if _merged is not history:
                db.log_webhook("full_history", f"{conv_id}: bot đọc {len(_merged)} tin từ Pancake (DB có {len(history)})")
            history = _merged
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"full_history {conv_id}: {ex}")
    # v0.5.37: có ảnh/sticker đính kèm → gắn vào tin user CUỐI (tin vừa thêm) cho não nhìn
    if images:
        history = [dict(m) for m in history]
        history[-1]["images"] = images[:3]
        db.log_webhook("vision_in", f"{conv_id}: bot nhìn {len(images[:3])} ảnh/sticker đính kèm")
    # v0.5.30 C2 (lưới code): 2 tin gần nhất của bot — để chặn gửi lại nội dung gần y hệt
    _prev_bot = [m["content"] for m in history if m["role"] == "assistant"][-2:]
    # v0.5.30 C4+C5: hồ sơ khách (tên chào hợp lệ + xưng hô theo gender thật) vào system prompt
    profile = _profile_of(conv_id) or None     # gọi trước: có thể nạp post_id/ad_ids từ API
    _adg = _ad_gift_line(conv_id)   # v0.1.42: quảng cáo hứa tặng quà khi mua 1 hộp
    if _adg:
        profile = (profile + " · " if profile else "") + _adg
    # v0.1.13: sản phẩm trọng tâm theo bài viết/quảng cáo khách bấm vào (không khớp → mặc định của page)
    focus, focus_src = _focus_of(conv_id)
    # v0.1.60 (23/10, ca Hải Bùi): khách đã cho SĐT / đã chốt đơn từ hôm trước (tin cũ có thể nằm ngoài lịch sử gửi AI)
    # → nhớ SĐT theo hội thoại, đưa vào hồ sơ để bot KHÔNG xin lại; đơn đã chốt → luật 5o-k (chuyển bạn phụ trách đơn)
    _kp = _known_phone(conv_id, history)
    _extra = []
    if _kp:
        _extra.append(f'SĐT KHÁCH ĐÃ GỬI: "{_kp}" (đã có — TUYỆT ĐỐI KHÔNG xin lại / hỏi lại SĐT; dùng đúng số này cho build_order và [HANDOFF])')
    if db.get_setting("order_done:" + str(conv_id)):
        _extra.append("ĐƠN ĐÃ CHỐT TRƯỚC ĐÓ: khách hỏi giao hàng / chưa thấy ship / đổi, huỷ đơn → làm đúng luật 5o-k: "
                      "'Dạ em đã báo bạn phụ trách đơn kiểm tra và liên hệ lại anh/chị ngay ạ' + [HANDOFF: khách hỏi đơn đã chốt | SĐT | 2]; "
                      "KHÔNG xin lại SĐT/địa chỉ, KHÔNG báo giá lại")
    if _extra:
        profile = "; ".join(([profile] if profile else []) + _extra)
    result = engine.chat(history, profile=profile, channel="messenger",
                         focus=focus or None, focus_source=focus_src)

    if "error" in result:
        db.add_message(local_id, "system", f"ERROR: {result['error']}")
        # v0.1.33 (17/10): AI lỗi/quá tải (gói miễn phí hết lượt) → KHÔNG để khách bị bỏ lơ:
        # gắn thẻ người xử lý + giao ca + chưa đọc + ghi chú để nhân viên vào trả lời ngay.
        try:
            if _may_send(conv_id):
                reason = "Bot lỗi AI (có thể hết lượt Gemini miễn phí) — nhân viên trả lời khách ngay"
                db.add_handoff(local_id, "pancake", reason, "", 2)
                add_tag(conv_id, TAG_BOT)
                add_tag(conv_id, TAG_BY_LEVEL[2])
                assign(conv_id)
                mark_unread(conv_id)
                note(conv_id, _handoff_note([{"level": 2, "reason": reason}]))
                db.pancake_mark_returned(conv_id, 2)
                db.log_webhook("error", f"ai_error_handoff {conv_id}: {str(result['error'])[:200]}")
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"ai_error_handoff fail {conv_id}: {ex}")
        return {"error": result["error"], "conv_id": conv_id}
    if result.get("filter_log"):     # v0.1.100: lưới nào đã sửa / bỏ gì trong tin này (để tra khi tin bị cụt, lửng lơ)
        try:
            db.log_webhook("filter_log", f"{conv_id}: " + json.dumps(result["filter_log"], ensure_ascii=False)[:700])
        except Exception:  # noqa: BLE001
            pass
    if result.get("leak_samples"):   # v0.1.96: ghi lại đoạn ghi chú AI đã bị chặn (để theo dõi kiểu lộ mới)
        try:
            db.log_webhook("leak_blocked", f"{conv_id}: " + " || ".join(result["leak_samples"])[:700])
        except Exception:  # noqa: BLE001
            pass

    is_fb = bool(result.get("is_fallback"))
    db.add_message(local_id, "assistant", result["reply"],
                   latency_ms=result["latency_ms"], model=result["model"],
                   tool_trace=json.dumps(result["tool_trace"], ensure_ascii=False), is_fallback=is_fb)

    handoffs = result.get("handoffs") or []
    _kp2 = db.get_setting("phone:" + str(conv_id)) or ""
    # v0.1.60 (ca Hải Bùi): đơn đã chốt, khách hỏi giao hàng / chưa thấy ship / đổi-huỷ đơn mà bot quên chuyển → tự chuyển nhân viên
    if db.get_setting("order_done:" + str(conv_id)) and not handoffs and _RE_ORDER_QUERY.search(_fold_name(text or "")):
        handoffs.append({"reason": "khách hỏi đơn đã chốt (giao hàng / sửa đơn)", "phone": _kp2, "level": 2})
        db.log_webhook("order_query", f"{conv_id}: đơn đã chốt, khách hỏi giao hàng/đơn → chuyển nhân viên")
    # v0.1.90 (ca Hồ Minh): khách cáo buộc / xúc phạm ("lừa đảo", "hàng giả", "công an"…) mà AI quên chuyển → tự chuyển mức 4
    if not handoffs and _RE_ACCUSE_HARD.search(text or "") and not re.search(r"\bsợ\b|lo là|có phải|có .{0,20}không|\?|(?<![A-Za-zÀ-ỹĐđ])(à|hả|hở|không|ko|k|chứ)\s*[.!…]*\s*$", text or "", re.I):
        handoffs.append({"reason": "khách cáo buộc / phàn nàn gay gắt", "phone": _kp2, "level": 4})
        db.log_webhook("accuse_handoff", f"{conv_id}: khách cáo buộc/xúc phạm → chuyển nhân viên (ADR/Khiếu nại)")
    for h in handoffs:   # v0.1.60: HANDOFF thiếu SĐT mà hội thoại đã có số → điền vào
        if not h.get("phone") and _kp2:
            h["phone"] = _kp2
    # v0.1.15: nhớ đơn đủ thông tin mới nhất (build_order ready_to_confirm) để đẩy lên Nhanh khi khách xác nhận
    for tr in result.get("tool_trace") or []:
        if tr.get("tool") == "build_order" and isinstance(tr.get("output"), dict):
            try:
                nhanh.remember_order(conv_id, tr["output"])
            except Exception as ex:  # noqa: BLE001
                db.log_webhook("error", f"nhanh remember {conv_id}: {ex}")
    # v0.5.27 B9: bot vừa chốt hướng mua NHÀ THUỐC (thẻ [PHARMACY]) → hẹn hỏi thăm 1 lần ~21h
    if result.get("pharmacy"):
        _pharm_mark(conv_id)
    for h in handoffs:
        db.add_handoff(local_id, "pancake", h.get("reason", ""), h.get("phone", ""), h.get("level", 2))
    if is_fb and db.recent_fallback_streak(local_id) >= 2:
        handoffs.append({"reason": "HỘI THOẠI LỖI - bot trả rỗng liên tiếp", "phone": "", "level": 4})
        db.add_handoff(local_id, "pancake", "HỘI THOẠI LỖI - bot trả rỗng liên tiếp", "", 4)
    _capture_leads(local_id, text, handoffs)
    # v0.1.56 (chị Nga 23/10): ca bot đã kết luận khách KHÔNG dùng được / cần HỎI Ý KIẾN BÁC SĨ → không nhắc nhớ nữa
    try:
        why = "bot đánh dấu hội thoại đã kết thúc [END]" if result.get("ended") else _no_followup_reason(result)
        if why:
            db.set_setting("fu_stop:" + str(conv_id), f"{time.time():.0f}")
            _fu_clear(conv_id)
            db.log_webhook("fu_stop", f"{conv_id}: {why} — không gửi nhắc nhớ")
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"fu_stop {conv_id}: {ex}")

    try:
        _auto_first_images(conv_id, result, focus or engine.PAGE_FOCUS_PRODUCT, text, _prev_bot)
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"auto_img {conv_id}: {ex}")
    sent = []
    if _may_send(conv_id):
        # gửi từng phần như người thật gõ
        for part in (result.get("parts") or [result["reply"]]):
            # v0.5.42: tách thẻ ẢNH ra khỏi phần chữ — gửi chữ trước, rồi gửi ẢNH THẬT sau
            img_ids = _extract_img_ids(part)
            # v0.1.24 (16/10, chị Nga test): ảnh đã gửi trong hội thoại thì KHÔNG gửi lại,
            # trừ khi khách báo không xem được / xin gửi lại ảnh.
            if img_ids:
                try:
                    _sent_before = set(json.loads(db.get_setting("imgs_sent:" + str(conv_id)) or "[]"))
                except Exception:  # noqa: BLE001
                    _sent_before = set()
                if not re.search(r"(không|ko|k|chưa)\s*(xem|thấy|mở|load|tải)\s*(được|đc)?\s*(ảnh|hình)?|gửi lại|lỗi ảnh|ảnh lỗi", text or "", re.I):
                    img_ids = [i for i in img_ids if i not in _sent_before]
            clean = _render_img_for_messenger(part)
            # 1) PHẦN CHỮ (nếu có, và không lặp lại 2 tin bot gần nhất — C2)
            if clean:
                if any(_too_similar(clean, p) for p in _prev_bot):
                    db.log_webhook("dedup_part", f"{conv_id}: chặn 1 tin lặp lại nội dung cũ: {clean[:80]}")
                else:
                    if sent:
                        # v0.5.22 A6: nghỉ 1,5–2 giây giữa các tin — như người thật gõ
                        time.sleep(PART_GAP + random.random() * 0.5)
                    r = send_message(conv_id, clean)
                    sent.append(r.get("error") or "ok")
                    if r.get("unreachable"):
                        break   # v0.5.22 A3: khách không nhận được nữa — gửi các phần sau vô ích
            # 2) ẢNH THẬT (nếu part có thẻ [IMG]) — gửi RỜI bằng content_ids
            if img_ids:
                if sent:
                    time.sleep(PART_GAP + random.random() * 0.5)
                ri = send_images(conv_id, img_ids)
                if ri.get("sent"):
                    try:
                        _sb = set(json.loads(db.get_setting("imgs_sent:" + str(conv_id)) or "[]"))
                        db.set_setting("imgs_sent:" + str(conv_id), json.dumps(sorted(_sb | set(img_ids))))
                    except Exception:  # noqa: BLE001
                        pass
                # ảnh gửi RỜI: đánh dấu "img" (KHÔNG tính vào bộ đếm reply A/B — giữ nguyên
                # tiêu chí so sánh của vòng đang chạy; phần chữ mới là tin đo tốc độ trả lời)
                sent.append("img" if ri.get("sent") else (ri.get("error") or "img_fail"))
                if ri.get("unreachable"):
                    break
        if not any(x in ("ok", "img") for x in sent) and not handoffs and not sent:
            # v0.1.66 (ca Đông Đao): mọi phần trả lời bị chặn (trùng nội dung cũ / rỗng) → khách KHÔNG nhận được gì.
            # Báo nhân viên ngay: giao ca + chưa đọc + ghi chú (bot vẫn trực, không rút).
            db.log_webhook("bot_silent", f"{conv_id}: bot không gửi được tin nào cho khách (bị chặn lặp/rỗng) — báo nhân viên")
            try:
                add_tag(conv_id, "Người xử lý")
                assign(conv_id)
                mark_unread(conv_id)
                note(conv_id, "🔴 Bot chưa trả lời được tin mới nhất của khách (nội dung trùng/lỗi) — nhân viên nhắn giúp.")
                db.add_handoff(local_id, "pancake", "Bot chưa trả lời được — nhân viên nhắn giúp", "", 2)
            except Exception as ex:  # noqa: BLE001
                db.log_webhook("error", f"bot_silent {conv_id}: {ex}")
        if any(s == "ok" for s in sent):
            db.ab_reply(conv_id, n=sum(1 for s in sent if s == "ok"))  # metric A/B nhóm bot
        add_tag(conv_id, TAG_BOT)
        if any(x in ("ok", "img") for x in sent):
            _keep_unread(conv_id)   # v0.1.47: khách vừa nhắn → giữ "chưa đọc" để nhân viên đọc lại (v0.1.57: cả ca chuyển nhân viên)
        # có handoff → trả về người: thẻ level cao nhất + assign + chưa đọc + note (mục 7.2)
        if handoffs:
            top = max(h.get("level", 2) for h in handoffs)
            add_tag(conv_id, TAG_BY_LEVEL.get(top, "Người xử lý"))
            # Level 3-4 gán thẳng dược sĩ trực nếu có cấu hình; còn lại round robin
            if top >= 3 and PHARMACIST_IDS:
                assign(conv_id, PHARMACIST_IDS[int(time.time()) % len(PHARMACIST_IDS)])
            else:
                assign(conv_id)
            mark_unread(conv_id)
            if top == 1:
                # v0.1.47 (chị Nga 22/10): bot CHỐT ĐƠN xong vẫn TRỰC TIẾP — khách hỏi thêm câu đơn giản
                # ("bố tôi huyết áp dùng được không") bot trả lời luôn, nhân viên chỉ lo gọi xác nhận / lên đơn.
                # Đổi đơn, huỷ đơn, hỏi giao hàng → engine tự HANDOFF mức 2 (rule 5o-k) → lúc đó mới về người.
                db.set_setting("order_done:" + str(conv_id), f"{time.time():.0f}")   # nhịp theo đuổi bỏ qua ca đã chốt
                db.log_webhook("order_keep_bot", f"{conv_id}: đã chốt đơn — gắn thẻ + báo nhân viên, bot vẫn trực câu hỏi thêm")
            else:
                db.pancake_mark_returned(conv_id, top)
            # v0.1.26 (chị Nga 16/10): khách TỰ yêu cầu chat với người → KHÔNG tự mở lại cho bot sau 24h
            if any("muốn chat với người" in (h.get("reason") or "").lower() for h in handoffs):
                db.set_setting("no_reopen:" + str(conv_id), "1")
                db.log_webhook("no_reopen", f"{conv_id}: khách muốn chat với người — không tự mở lại cho bot")
            _fu_clear(conv_id)          # v0.5.15: đã về người → dừng nhịp theo đuổi
            nt = _handoff_note(handoffs)
            if nt:
                note(conv_id, nt)
    # v0.1.81 (25/10, chị Nga): bot vừa gửi TỔNG HỢP ĐƠN (chưa chốt) → hẹn 10 phút; khách im → bot tự ghi nhận đơn + mời lên gói
    try:
        _rep = result.get("reply") or ""
        if any(h.get("level") == 1 for h in handoffs) or text == CONFIRM_SILENT:
            db.set_setting("cfw:" + str(conv_id), "")
        elif len(engine._RE_CONFIRM_BLOCK.findall(_rep)) >= 2 and any(x in ("ok", "img") for x in sent):
            db.set_setting("cfw:" + str(conv_id), f"{time.time():.0f}")
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"cfw set {conv_id}: {ex}")
    # v0.1.15: khách đã xác nhận đơn (HANDOFF level 1) → tạo đơn trên Nhanh (lỗi thì chỉ ghi log, nhân viên lên đơn tay)
    nh = None
    lvl1 = [h for h in handoffs if h.get("level") == 1]
    if lvl1 and _may_send(conv_id):
        try:
            nh = nhanh.push_order(conv_id, note=lvl1[0].get("reason", ""), test=db.pancake_is_test(conv_id))
            if not nh.get("ok") and nhanh.enabled():
                db.add_handoff(local_id, "pancake", "Đẩy đơn Nhanh lỗi — lên đơn tay: " + str(nh.get("reason"))[:150],
                               lvl1[0].get("phone", ""), 1)
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"nhanh push {conv_id}: {ex}")
    return {"ok": True, "conv_id": conv_id, "local_id": local_id, "nhanh": nh,
            "parts": len(result.get("parts") or []), "handoffs": len(handoffs),
            "is_fallback": is_fb, "enabled": is_enabled(), "sent": sent,
            "focus": focus or engine.PAGE_FOCUS_PRODUCT}


_RE_IMG = re.compile(r"\[IMG:\s*([a-z0-9-]+)\s*\]", re.I)
_RE_QR = re.compile(r"\[QR:[^\]]*\]", re.I)


def _upload_multipart(path: str, filename: str, data: bytes, ctype: str) -> dict:
    """POST multipart/form-data (dùng cho upload_contents). token qua query param như _api."""
    if not PAGE_TOKEN:
        return {"error": "no page token"}
    boundary = "----samtm" + os.urandom(8).hex()
    body = b"".join([
        ("--" + boundary + "\r\n").encode(),
        ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode(),
        ("Content-Type: %s\r\n\r\n" % ctype).encode(),
        data, b"\r\n",
        ("--" + boundary + "--\r\n").encode(),
    ])
    url = f"{BASE}{path}?{urllib.parse.urlencode({'page_access_token': PAGE_TOKEN})}"
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"content-type": "multipart/form-data; boundary=" + boundary})
    _throttle()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as ex:
        return {"error": f"HTTP {ex.code}", "detail": _safe_read(ex)}
    except Exception as ex:  # noqa: BLE001
        return {"error": f"network: {ex}"}


IMG_CID_TTL = float(os.environ.get("PANCAKE_IMG_CID_TTL", "1800"))   # v0.1.24: 30 phút upload lại ảnh 1 lần


def _upload_local_img(img_id: str) -> str:
    """Upload 1 ảnh cố định lên Pancake, trả content_id (cache tiến trình + DB — ảnh không đổi)."""
    img_id = (img_id or "").lower()
    # v0.1.24 (16/10, chị Nga test): content_id Pancake HẾT HẠN sau vài giờ → gửi lại id cũ thì khách
    # chỉ thấy ô xám "meta_… Xem", không có ảnh. Cache kèm mốc giờ, quá IMG_CID_TTL giây thì upload lại.
    raw = _content_cache.get(img_id) or db.get_setting("pk_content:" + img_id) or ""
    cid, _, ts = str(raw).partition("|")
    try:
        fresh = bool(cid) and bool(ts) and (time.time() - float(ts) < IMG_CID_TTL)
    except ValueError:
        fresh = False
    if fresh:
        _content_cache[img_id] = raw
        return cid
    fname = IMG_FILES.get(img_id)
    if not fname:
        return ""
    try:
        with open(os.path.join(IMG_DIR, fname), "rb") as f:
            data = f.read()
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("img_upload_fail", f"{img_id}: đọc file lỗi {ex}")
        return ""
    r = _upload_multipart(f"/pages/{PAGE_ID}/upload_contents", fname, data, "image/jpeg")
    cid = (r.get("id") or "") if isinstance(r, dict) else ""
    if cid and r.get("success") is not False:
        val = f"{cid}|{time.time():.0f}"
        _content_cache[img_id] = val
        db.set_setting("pk_content:" + img_id, val)
        return cid
    db.log_webhook("img_upload_fail", f"{img_id}: {json.dumps(r, ensure_ascii=False)[:300]}")
    return ""


def send_images(conv_id: str, img_ids: list) -> dict:
    """Gửi ẢNH THẬT qua Messenger: upload lấy content_id → reply_inbox với content_ids.
    (Facebook tối đa 30 content_ids/lần; message và content_ids LOẠI TRỪ nhau — phải gửi rời.)"""
    cids, ok_ids = [], []
    for iid in img_ids:
        cid = _upload_local_img(iid)
        if cid:
            cids.append(cid)
            ok_ids.append(iid)
    if not cids:
        db.log_webhook("img_send_fail", f"{conv_id}: không upload được ảnh nào ({','.join(img_ids)})")
        return {"error": "no content", "sent": False}
    r = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages",
             body={"action": "reply_inbox", "content_ids": cids[:30]})
    if not _body_ok(r):
        if _is_unreach(r):
            _mark_unreach(conv_id)
            r["unreachable"] = True
        else:
            db.log_webhook("img_send_fail", f"{conv_id}: {json.dumps(r, ensure_ascii=False)[:300]}")
        r["error"] = r.get("error") or "img send rejected"
        return r
    db.log_webhook("img_sent", f"{conv_id}: gửi {len(cids)} ảnh ({','.join(ok_ids)})")
    return {"ok": True, "sent": True, "n": len(cids)}


# v0.1.62 (23/10, ca Thi Yen Lương): khách đến từ quảng cáo, page đã tự gửi tin chào → bot báo giá mà KHÔNG kèm ảnh.
# Lưới code: hội thoại CHƯA từng nhận ảnh nào từ bot, câu trả lời nói về 1 sản phẩm chính mà AI quên thẻ [IMG] → tự gắn ảnh.
_AUTO_IMG = [  # (mẫu nhận diện trong câu trả lời, product_id, ảnh)
    (r"hồng sâm[^.\n]{0,40}(dạng )?lát|sâm lát", "hsvn_lat", ["hong-sam-lat", "hong-sam-lat-mieng"]),
    (r"dương sâm", "duong_sam", ["duong-sam"]),
    (r"long sâm", "long_sam", ["long-sam", "long-sam-qua-bieu"]),
    (r"nước hồng sâm|hồng sâm[^.\n]{0,30}mật ong[^.\n]{0,20}(túi|dạng túi)", "hsmo_tui", ["nuoc-hong-sam"]),
    (r"hồng sâm[^.\n]{0,30}(chai 175|dạng chai)", "hsmo_chai", ["hong-sam-chai"]),
]
_AUTO_IMG_FOCUS = {pid: imgs for _, pid, imgs in _AUTO_IMG}


_RE_ASK_SEE = re.compile(r"(?:gửi|gui|cho)\s+(?:cho\s+)?(?:chị|chi|anh|em|cô|co|bác|bac|chú|chu|tôi|toi|mình|minh)?\s*(?:xem|sem|coi)(?![A-Za-zÀ-ỹĐđ])"
                         r"|(?:gửi|xin|cho xem|cho coi)\s+(?:cái\s+)?(?:ảnh|hình|hinh anh|hình ảnh)(?![A-Za-zÀ-ỹĐđ])|(?:ảnh|hình)\s+(?:sản phẩm|sp)", re.I)


def _auto_first_images(conv_id: str, result: dict, focus: str = "", user_text: str = "", prev_bot: list = None):
    parts = result.get("parts") or ([result["reply"]] if result.get("reply") else [])
    if not parts or any(_RE_IMG.search(p or "") for p in parts):
        return
    try:
        _sent_imgs = set(json.loads(db.get_setting("imgs_sent:" + str(conv_id)) or "[]"))
    except Exception:  # noqa: BLE001
        _sent_imgs = set()
    asked = bool(_RE_ASK_SEE.search(user_text or ""))   # v0.1.66 (v0.1.77: "Cho anh hỏi giá" KHÔNG phải xin ảnh)
    # v0.1.76/77: khách từ bình luận → inbox chưa có ảnh nào → logic "lượt đầu chưa nhận ảnh" bên dưới tự gửi khi câu trả lời nói về sản phẩm
    if _sent_imgs and not asked:
        return
    reply = "\n".join(parts)
    if not asked and (db.get_setting("order_done:" + str(conv_id)) or
                      re.search(r"giao hàng|đơn hàng|vận chuyển|shipper|bạn phụ trách|nhân viên|chuyên viên|bác sĩ|không dùng được|chưa nên dùng", reply, re.I)):
        return   # v0.1.77: tin về đơn/giao hàng, chuyển người, an toàn → không chèn ảnh sản phẩm
    if not asked and not re.search(r"\d{2,3}\.000đ|sản phẩm|hỗ trợ|dùng|hộp", reply, re.I):
        return   # câu xã giao / hỏi lại → chưa gửi ảnh
    if asked and not any(re.search(pat, reply, re.I) for pat, _, _ in _AUTO_IMG):
        reply = reply + "\n" + "\n".join(prev_bot or [])   # sản phẩm vừa nhắc ở tin bot trước
    imgs = None
    pos = None
    for pat, pid, im in _AUTO_IMG:
        m = re.search(pat, reply, re.I)
        if m and (pos is None or m.start() < pos):
            pos, imgs = m.start(), im
    if imgs is None:
        imgs = _AUTO_IMG_FOCUS.get(focus or "")
    if not imgs:
        return
    tag = "\n".join(f"[IMG: {i}]" for i in imgs[:2] if i in IMG_FILES and i not in _sent_imgs)
    if not tag:
        return
    parts[0] = (parts[0] or "").rstrip() + "\n" + tag
    result["parts"] = parts
    db.log_webhook("auto_img", f"{conv_id}: AI quên gửi ảnh lượt đầu → tự gắn {imgs[:2]}")


def _extract_img_ids(text: str) -> list:
    """Danh sách id ảnh trong thẻ [IMG: ...] — chỉ giữ id ĐÃ CÓ file (bỏ id lạ do model bịa)."""
    return [m.lower() for m in _RE_IMG.findall(text or "") if m.lower() in IMG_FILES]


def _render_img_for_messenger(text: str) -> str:
    """Bỏ thẻ [IMG]/[QR] khỏi PHẦN CHỮ (ảnh được gửi RỜI qua send_images bằng content_ids —
    message và content_ids loại trừ nhau). [QR: ...] là nút gợi ý của web test, cũng bỏ."""
    return _RE_QR.sub("", _RE_IMG.sub("", text or "")).strip()


# ================= HUB PHÂN LUỒNG WEBHOOK (v0.5.6) =================
# Pancake dùng MỘT URL webhook chung cho cả gói cước (payload nào cũng kèm page_id).
# Bot này là trạm trung tâm: page mình → xử lý; page trong FORWARD_MAP → chuyển tiếp
# NGUYÊN VẸN payload (giữ đúng body JSON, hệ thống nhận không phải sửa gì);
# page lạ → chỉ ghi log để người vận hành biết, không gửi dữ liệu đi đâu.
# LƯU Ý: kill switch chỉ tắt BOT MÌNH — chuyển tiếp cho luồng khác (VD: Vương Bảo/n8n)
# vẫn chạy kể cả khi kill, vì đó là hạ tầng của đội khác, không phải của bot.
FORWARD_TIMEOUT = max(2.0, float(os.environ.get("PANCAKE_FORWARD_TIMEOUT", "8")))


def _parse_forward_map(raw: str) -> dict:
    """Chịu lỗi nhập liệu (sự cố 25/08: dán '<page_id>=url' nguyên cả dấu <> từ hướng dẫn
    → không khớp page_id thật → n8n Vương Bảo đói tin): bóc <>, nháy, khoảng trắng."""
    out = {}
    for part in re.split(r"[,;]", raw or ""):
        part = part.strip()
        if not part or "=" not in part:
            continue
        pid, url = part.split("=", 1)
        pid = pid.strip().strip("<>\"' ").strip()
        url = url.strip().strip("<>\"' ").strip()
        if pid and url.startswith("http"):
            out[pid] = url
    return out


FORWARD_MAP = _parse_forward_map(os.environ.get("PANCAKE_FORWARD_MAP", ""))
_fw_stats = {}      # page_id -> {"ok": n, "err": n, "last_ts": epoch}
_fw_lock = threading.Lock()


def _host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:  # noqa: BLE001
        return url[:40]


def _fw_count(pid: str, ok: bool):
    with _fw_lock:
        s = _fw_stats.setdefault(pid, {"ok": 0, "err": 0, "last_ts": 0})
        s["ok" if ok else "err"] += 1
        s["last_ts"] = int(time.time())


def _forward(pid: str, url: str, payload: dict) -> dict:
    """Chuyển tiếp nguyên vẹn payload sang hệ thống của page khác. Thử lại 1 lần nếu lỗi."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_err = None
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                url, data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "X-Forwarded-By": "thaiminh-webhook-hub",
                         # v0.5.20: n8n mới của Huyền Anh (n8n.tieukhonghet.com) đứng sau WAF —
                         # UA mặc định "Python-urllib/3.x" bị chặn 403 (POST y hệt từ trình duyệt
                         # trả 200). Gắn UA trình duyệt + Accept để qua cửa.
                         "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/126.0.0.0 Safari/537.36"),
                         "Accept": "application/json, */*"})
            with urllib.request.urlopen(req, timeout=FORWARD_TIMEOUT) as r:
                code = r.getcode()
            _fw_count(pid, True)
            db.log_webhook("forward_ok", json.dumps(
                {"page_id": pid, "to": _host(url), "http": code,
                 "event": payload.get("event_type", "")}, ensure_ascii=False))
            return {"hub": True, "forwarded": True, "page_id": pid, "http": code}
        except Exception as ex:  # noqa: BLE001
            last_err = ex
            if attempt == 1:
                time.sleep(2)
    _fw_count(pid, False)
    db.log_webhook("forward_err", json.dumps(
        {"page_id": pid, "to": _host(url), "error": str(last_err)[:200]}, ensure_ascii=False))
    return {"hub": True, "forwarded": False, "page_id": pid, "error": str(last_err)}


def route_event(payload: dict) -> dict:
    """Cửa vào duy nhất của webhook: chia sự kiện theo page_id.
    - page mình  → handle_event (toàn bộ luật bot: kill/test/A-B/dedupe... như cũ)
    - page trong FORWARD_MAP → _forward (KHÔNG dính kill switch của bot mình)
    - page lạ    → log forward_none, không gửi đi đâu (tránh lộ dữ liệu nhầm chỗ)"""
    pid = str(payload.get("page_id") or "")
    if not pid or pid == PAGE_ID:
        return handle_event(payload)
    url = FORWARD_MAP.get(pid)
    if not url:
        db.log_webhook("forward_none", json.dumps(
            {"page_id": pid, "event": payload.get("event_type", "")}, ensure_ascii=False))
        return {"hub": True, "skip": "unknown_page", "page_id": pid}
    return _forward(pid, url, payload)


# ============ v0.5.15: TIN KHÔNG CÓ CHỮ + ENGINE NHỊP THEO ĐUỔI ============
_STICKER_HINT = ("sticker", "like", "thumb")


# v0.1.91 (26/10, ca Phạm Ngọc An / Huỳnh Cương — page Dương Sâm): khách gửi THẺ ĐƠN HÀNG ("Đơn hàng DSLĐ1-1 Dương Sâm Linh Đan
# 990.000đ x1") hoặc THẺ SẢN PHẨM kèm "Tư vấn thêm" → trước đây bot coi là tin rỗng/tệp nên im hoặc không biết khách hỏi gì.
# Nay đọc chữ trong thẻ (tên, mã, giá, số lượng) đưa vào não bot. Shape Pancake chưa kiểm chứng → quét mọi khóa, ghi log 'card_in'.
_CARD_NAME_KEYS = ("title", "name", "product_name", "item_name", "display_id", "sku", "code")
_CARD_NUM_KEYS = ("price", "retail_price", "total", "total_price", "amount", "quantity", "qty")
_CARD_ORDER_HINT = ("order", "đơn hàng", "don_hang", "receipt", "bill")


def _card_text(msg: dict) -> str:
    names, nums, is_order = [], [], False
    srcs = []
    try:
        if _attach_kind(msg) in ("sticker", "image", "audio", "video", "pdf"):
            return ""             # ảnh/sticker/tệp thật → để nhánh cũ xử lý
    except Exception:  # noqa: BLE001
        pass
    for k in ("attachments", "attachment", "order", "orders", "product", "products", "template", "payload"):
        v = msg.get(k)
        if v:
            srcs.append((k, v))
            if any(h in k for h in ("order",)):
                is_order = True

    def walk(o, depth=0, key=""):
        nonlocal is_order
        if depth > 5:
            return
        if isinstance(o, dict):
            t = str(o.get("type") or o.get("template_type") or "").lower()
            if any(h in t for h in _CARD_ORDER_HINT):
                is_order = True
            if "sticker" in t or t.startswith(("image", "audio", "video")) or t in ("photo", "gif", "file"):
                return
            for kk, vv in o.items():
                kl = str(kk).lower()
                if any(h in kl for h in _CARD_ORDER_HINT):
                    is_order = True
                if isinstance(vv, (dict, list)):
                    walk(vv, depth + 1, kl)
                elif isinstance(vv, (str, int, float)) and str(vv).strip():
                    sv = str(vv).strip()
                    if sv.lower().startswith("http") or len(sv) > 120:
                        continue
                    if kl in _CARD_NAME_KEYS and not sv.isdigit() and not re.search(r"\.(jpe?g|png|gif|webp|mp4|pdf|m4a)$", sv, re.I):
                        names.append(sv)
                    elif kl in _CARD_NUM_KEYS:
                        nums.append(f"{kl}={sv}")
                    if any(h in sv.lower() for h in ("đơn hàng",)):
                        is_order = True
        elif isinstance(o, list):
            for x in o[:10]:
                walk(x, depth + 1, key)
    for _k, v in srcs:
        walk(v)
    names = list(dict.fromkeys(n for n in names if n))[:4]
    if not names:
        return ""
    body = ", ".join(names + list(dict.fromkeys(nums))[:4])
    if is_order:
        return ("[Khách gửi ĐƠN HÀNG đặt trên Facebook: " + body + ". Khách muốn mua sản phẩm này — xác nhận sản phẩm, số lượng, "
                "giá theo tài liệu rồi xin họ tên, SĐT, địa chỉ nhận hàng (phần nào khách đã gửi thì không xin lại)]")
    return "[Khách gửi thẻ sản phẩm: " + body + " — khách đang quan tâm sản phẩm này]"


def _attach_kind(msg: dict) -> str:
    """Tin không có chữ là loại gì: 'sticker' | 'image' | 'other' | '' (không nhận ra).
    Kiểm chứng thật 26/08 (ca chị Vì Trúc): attachments = [{"type": "sticker"}]."""
    if msg.get("sticker") or msg.get("sticker_id") or msg.get("sticker_url"):
        return "sticker"
    atts = msg.get("attachments") or msg.get("attachment") or []
    if isinstance(atts, dict):
        atts = [atts]
    kinds = []
    for a in atts:
        if not isinstance(a, dict):
            continue
        t = str(a.get("type") or a.get("mime_type") or "").lower()
        pay = a.get("payload") if isinstance(a.get("payload"), dict) else {}
        url = str(a.get("url") or pay.get("url") or "").lower()
        if a.get("sticker_id") or pay.get("sticker_id") or \
                any(h in t for h in _STICKER_HINT) or any(h in url for h in _STICKER_HINT):
            kinds.append("sticker")
        elif t.startswith("image") or t in ("photo", "gif", "image"):
            kinds.append("image")
        # v0.5.39: gọi đúng loại tệp — khách VN hay gửi TIN NHẮN THOẠI, và PDF thường là
        # đơn thuốc/kết quả khám scan (vẫn chuyển người, nhưng ghi nhận + note đúng loại)
        elif t.startswith("audio") or "voice" in t or url.split("?")[0].endswith(
                (".mp3", ".m4a", ".ogg", ".wav", ".aac")):
            kinds.append("audio")
        elif t.startswith("video") or url.split("?")[0].endswith((".mp4", ".mov", ".avi")):
            kinds.append("video")
        elif "pdf" in t or url.split("?")[0].endswith(".pdf"):
            kinds.append("pdf")
        elif t or url:
            kinds.append("other")
    if not kinds:
        return ""
    if all(k == "sticker" for k in kinds):
        return "sticker"
    for k in ("image", "audio", "video", "pdf"):
        if k in kinds:
            return k
    return "other"


def _vision_on() -> bool:
    """v0.5.37: van cho bot nhìn ảnh/sticker (toggle field 'vision'; mặc định BẬT)."""
    return db.get_setting("pancake_vision", "1") == "1"


def _attach_urls(msg: dict, max_n: int = 3) -> list:
    """Link ảnh/sticker trong tin (chỉ lấy http(s) công khai — kiểm chứng 01/09:
    ảnh khách nằm ở content.pancake.vn, tải công khai được)."""
    urls = []
    atts = msg.get("attachments") or msg.get("attachment") or []
    if isinstance(atts, dict):
        atts = [atts]
    for a in atts:
        if not isinstance(a, dict):
            continue
        pay = a.get("payload") if isinstance(a.get("payload"), dict) else {}
        u = str(a.get("url") or pay.get("url") or a.get("image_url") or pay.get("image_url") or "")
        t = str(a.get("type") or a.get("mime_type") or "").lower()
        looks_img = (t.startswith("image") or t in ("photo", "gif", "image", "sticker")
                     or "sticker" in t
                     or any(u.lower().split("?")[0].endswith(e) for e in (".jpg", ".jpeg", ".png", ".gif", ".webp")))
        if u.startswith("http") and looks_img:
            urls.append(u)
    su = str(msg.get("sticker_url") or "")
    if su.startswith("http"):
        urls.append(su)
    return urls[:max_n]


def _attach_handoff(conv_id: str, kind: str, meta: dict) -> dict:
    """Khách gửi ảnh/tệp không kèm chữ: bot ghi nhận 1 câu rồi chuyển người thật — không đoán
    nội dung ảnh (đơn thuốc, kết quả nội soi, ảnh vỏ hộp là rủi ro chuyên môn)."""
    local_id = db.pancake_local_conv(conv_id, customer=meta.get("customer"))
    kind_vn = {"image": "ảnh", "audio": "tin nhắn thoại", "video": "video",
               "pdf": "file PDF (thường là đơn thuốc/kết quả khám scan)"}.get(kind, "tệp")
    db.add_message(local_id, "user", f"[Khách gửi {kind_vn}, không kèm chữ]")
    reason = ("Khách gửi %s không kèm chữ — cần người %s nội dung"
              % (kind_vn, "nghe" if kind == "audio" else "xem"))
    db.add_handoff(local_id, "pancake", reason, "", 2)
    _fu_clear(conv_id)
    if not _may_send(conv_id):
        return {"ok": True, "attachment": kind, "conv_id": conv_id, "sent": False}
    ack = {
        "audio": "Dạ em nhận được tin nhắn thoại của anh/chị rồi ạ, em chuyển bạn phụ trách nghe "
                 "và phản hồi anh/chị sớm nhất nhé ạ.",
        "video": "Dạ em nhận được video của anh/chị rồi ạ, em chuyển bạn phụ trách xem "
                 "và phản hồi anh/chị sớm nhất nhé ạ.",
        "pdf": "Dạ em nhận được tài liệu của anh/chị rồi ạ, em nhờ chuyên viên xem giúp "
               "rồi phản hồi anh/chị ngay nhé ạ.",
    }.get(kind, ATT_ACK)
    db.add_message(local_id, "assistant", ack)
    r = send_message(conv_id, ack)
    add_tag(conv_id, TAG_BOT)
    add_tag(conv_id, TAG_BY_LEVEL[2])
    assign(conv_id)
    mark_unread(conv_id)
    _keep_unread(conv_id)   # v0.1.59: khách vừa nhắn + bot đã gửi câu ghi nhận → đánh lại chưa đọc sau 4s/15s/45s (không bị Pancake đè)
    note(conv_id, _handoff_note([{"level": 2, "reason": reason}]))
    db.pancake_mark_returned(conv_id, 2)
    db.log_webhook("attach_handoff", f"{conv_id}: {reason}")
    return {"ok": True, "attachment": kind, "handoffs": 1, "conv_id": conv_id,
            "sent": not r.get("error")}


def _bare_phone(text: str) -> str:
    """v0.5.22 A7: tin CHỈ chứa SĐT (không kèm chữ) — tín hiệu mua rõ nhất (Vương Bảo + team).
    Trả về số đã chuẩn hoá, hoặc '' nếu tin còn nội dung khác."""
    ph = find_phones(text)
    if len(ph) != 1:
        return ""
    left = _RE_PHONE.sub("", text or "")
    if re.sub(r"[\W_\d]+", "", left, flags=re.UNICODE):
        return ""
    return ph[0]


def _phone_handoff(conv_id: str, phone: str, meta: dict, text: str) -> dict:
    """v0.5.22 A7: khách gửi trần SĐT → 1 câu ghi nhận + thẻ + assign + giao người NGAY,
    không chờ hết nhịp 1 (30 phút) — mất nhiệt. Dừng bot + dừng nhịp theo đuổi ca này."""
    local_id = db.pancake_local_conv(conv_id, customer=meta.get("customer"))
    db.add_message(local_id, "user", text)
    reason = "Khách chủ động gửi SĐT — tín hiệu mua, gọi lại ngay"
    db.add_handoff(local_id, "pancake", reason, phone, 2)
    db.add_lead(local_id, "pancake", phone, "khách gửi trần SĐT")
    _fu_clear(conv_id)
    with _batch_lock:      # huỷ tin đang gom dở — từ giờ người thật trả lời ca này
        b = _batches.pop(conv_id, None)
        if b:
            b["timer"].cancel()
    if not _may_send(conv_id):
        return {"ok": True, "phone_handoff": phone, "conv_id": conv_id, "sent": False}
    db.add_message(local_id, "assistant", PHONE_ACK)
    r = send_message(conv_id, PHONE_ACK)
    if not r.get("error"):
        db.ab_reply(conv_id)
    add_tag(conv_id, TAG_BOT)
    add_tag(conv_id, TAG_BY_LEVEL[2])
    assign(conv_id)
    mark_unread(conv_id)
    _keep_unread(conv_id)   # v0.1.59: khách vừa nhắn + bot đã gửi câu ghi nhận → đánh lại chưa đọc sau 4s/15s/45s (không bị Pancake đè)
    note(conv_id, _handoff_note([{"level": 2, "reason": reason, "phone": phone}]))
    db.pancake_mark_returned(conv_id, 2)
    db.log_webhook("phone_handoff", f"{conv_id}: khách gửi trần SĐT {phone} → giao người gọi ngay")
    return {"ok": True, "phone_handoff": phone, "handoffs": 1, "conv_id": conv_id,
            "sent": not r.get("error")}


# ================= v0.5.24 (D2): ĐƠN HÀNG THEO HỘI THOẠI =================
def _orders_table(c):
    c.execute("CREATE TABLE IF NOT EXISTS ab_orders("
              "pancake_conv_id TEXT, order_id TEXT, status TEXT, status_name TEXT,"
              " total REAL, phone TEXT, inserted_at TEXT, ts REAL,"
              " PRIMARY KEY(pancake_conv_id, order_id))")


def ab_save_orders(rows, src="pos") -> int:
    """Ghi/cập nhật đơn vào bảng ab_orders (tạo bảng bằng db._conn — KHÔNG sửa db.py).
    rows: list dict {conv_id, order_id, status, status_name, total, phone, inserted_at}.
    Trạng thái đơn ĐỔI theo thời gian (Mới → Đã xác nhận) nên ghi đè bản ghi cũ."""
    n = 0
    try:
        with db._conn() as c:
            _orders_table(c)
            for r in rows or []:
                cid = str(r.get("conv_id") or "").strip()
                oid = str(r.get("order_id") or "").strip()
                if not cid or not oid:
                    continue
                c.execute("INSERT INTO ab_orders(pancake_conv_id, order_id, status, status_name,"
                          " total, phone, inserted_at, ts) VALUES(?,?,?,?,?,?,?,?)"
                          " ON CONFLICT(pancake_conv_id, order_id) DO UPDATE SET"
                          " status=excluded.status, status_name=excluded.status_name,"
                          " total=excluded.total, ts=excluded.ts",
                          (cid, oid, str(r.get("status") if r.get("status") is not None else ""),
                           r.get("status_name") or "", float(r.get("total") or 0),
                           str(r.get("phone") or ""), str(r.get("inserted_at") or ""), time.time()))
                n += 1
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"ab_save_orders: {ex}")
    return n


def pos_orders_sync(since_iso: str = "", max_pages: int = 5, page_size: int = 100) -> dict:
    """Quét đơn từ POS và lưu theo hội thoại. Cần ENV PANCAKE_POS_API_KEY (khoá API của shop,
    anh Na tạo trong Pancake POS) — KHÔNG dùng được token page. Không có khoá thì trả rõ lý do
    để trang báo cáo hiển thị 'chưa nối được đơn' thay vì im lặng."""
    if not POS_API_KEY:
        return {"ok": False, "reason": "chưa có PANCAKE_POS_API_KEY (khoá API của shop POS)"}
    if not SHOP_ID:
        return {"ok": False, "reason": "chưa có PANCAKE_SHOP_ID (mã shop POS của Sâm Thái Minh)"}
    seen, saved, page = 0, 0, 1
    while page <= max(1, max_pages):
        r = _api("GET", f"/shops/{SHOP_ID}/orders",
                 params={"api_key": POS_API_KEY, "page_number": page, "page_size": page_size},
                 base=BASE_POS)
        if r.get("error") or r.get("success") is False:
            db.log_webhook("api_fail", f"pos_orders: {json.dumps(r, ensure_ascii=False)[:200]}")
            return {"ok": False, "reason": r.get("message") or r.get("error"), "saved": saved}
        data = r.get("data") or []
        if not data:
            break
        seen += len(data)
        rows, oldest = [], ""
        for o in data:
            cid = o.get("conversation_id")
            oldest = o.get("inserted_at") or oldest
            if not cid or (o.get("page_id") and str(o["page_id"]) != str(PAGE_ID)):
                continue
            rows.append({"conv_id": cid, "order_id": o.get("id") or o.get("display_id"),
                         "status": o.get("status"), "status_name": o.get("status_name") or "",
                         "total": o.get("total_price_after_sub_discount") or o.get("cod") or 0,
                         "phone": o.get("phone_number") or "", "inserted_at": o.get("inserted_at")})
        saved += ab_save_orders(rows)
        if since_iso and oldest and oldest < since_iso:
            break            # đã quét lùi qua mốc đo — dừng, khỏi kéo cả lịch sử shop
        page += 1
    db.log_webhook("pos_sync", f"quét {seen} đơn POS, lưu {saved} đơn có hội thoại")
    return {"ok": True, "seen": seen, "saved": saved}


def _orders_loop():
    """Đơn đổi trạng thái sau khi tạo (Mới → Đã xác nhận) nên quét lại định kỳ."""
    while True:
        time.sleep(1800)
        try:
            if POS_API_KEY and not is_killed():
                pos_orders_sync(max_pages=3)
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"orders_loop: {ex}")


# ================= v0.5.27 B1: NGUỒN HỘI THOẠI (ads / post / organic) =================
# Webhook Pancake KHÔNG bắn field nguồn ổn định, nhưng public API conversations có ad_ids +
# post_id + page_customer.gender (dò 29/08: 14/60 ca có ad_ids). Bot tự quét định kỳ và lưu
# setting src:<conv> — nhịp đuổi đọc nguồn từ đây. Gender lưu sẵn cho C5 (chưa dùng).
# ---- v0.5.30 C4 (anh Na chốt 28/08 phương án b): chào tên CHỈ khi tên FB đạt chuẩn ----
# Tên FB rất hay là nickname ("Mèo Con", "Bà Trùm Hoa") — chào bằng tên rác tệ hơn không chào.
# Chuẩn: 2-4 từ, toàn chữ cái, không từ nào quá 8 ký tự, và TỪ ĐẦU phải là HỌ người Việt thật.
_VN_SURNAMES = {
    "nguyen", "tran", "le", "pham", "hoang", "huynh", "phan", "vu", "vo", "dang", "bui",
    "do", "ho", "ngo", "duong", "ly", "dao", "dinh", "truong", "lam", "mai", "trinh",
    "doan", "cao", "vuong", "ta", "luu", "to", "ha", "quach", "chu", "chau", "la", "kieu",
    "thai", "tang", "trieu", "tu", "luong", "van", "dam", "han", "mac", "thach", "diep",
    "tong", "nghiem", "ninh", "giang", "nong", "hua", "khong", "long", "quan", "son", "au"}


def _strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.replace("đ", "d").replace("Đ", "D")


def valid_fb_name(name: str) -> str:
    """v0.5.41 (anh Na chốt 03/09): trả NGUYÊN TÊN FB nếu "có vẻ giống tên Việt", '' nếu không.
    KHÔNG tách họ/tên nữa (đoán sai "Huệ Lê"→"Lê" còn tệ hơn) — bot gọi "chị Huệ Lê".
    Giống tên Việt = 2-4 từ, toàn chữ cái, không từ nào >8 ký tự, không viết tắt in hoa,
    và có HỌ Việt thật ở đầu HOẶC cuối (FB hay đảo Tên-Họ)."""
    name = " ".join((name or "").split())
    words = name.split()
    if not 2 <= len(words) <= 4:
        return ""
    if not all(all(ch.isalpha() for ch in w) for w in words):
        return ""              # emoji / số / ký tự lạ → loại
    if any(len(w) > 8 or (len(w) > 1 and w.isupper()) for w in words):
        return ""              # từ quá dài hoặc viết tắt in hoa ("LP Luong") → loại
    first, last = _strip_accents(words[0]).lower(), _strip_accents(words[-1]).lower()
    if first not in _VN_SURNAMES and last not in _VN_SURNAMES:
        return ""              # không có họ Việt thật ở đầu/cuối → coi là nickname
    return " ".join(w[:1].upper() + w[1:] for w in words)


def _maybe_save_name(conv_id: str, raw_name: str):
    if not raw_name:
        return
    cur = db.get_setting("name:" + conv_id)
    nm = valid_fb_name(raw_name)
    if nm and nm != cur:
        db.set_setting("name:" + conv_id, nm)  # v0.5.41: ca cũ lưu tên rút gọn ("Huệ") → nâng lên tên đầy đủ
    elif cur is None:
        db.set_setting("name:" + conv_id, nm)  # rỗng = "đã xét, không đạt" (xét lại khi có tên mới)


def _profile_fetch_once(conv_id: str, lookback: float = 7200) -> bool:
    """v0.5.40: webhook Pancake thường chỉ mang conv tối giản (KHÔNG có page_customer.gender, ad_ids)
    → lúc trả lời TIN ĐẦU bot mù giới tính (ca Huệ Lê 03/09: Pancake biết nữ, bot vẫn anh/chị).
    Nếu hồ sơ còn thiếu gender: gọi API conversations 1 LẦN cho conv này (đánh dấu prof:<conv>),
    tìm đúng id rồi nạp ad_ids/gender/tên qua _src_from_conv_obj. Lỗi mạng → bỏ qua, lần sau thử lại.
    v0.1.13: cũng gọi khi CHƯA biết nguồn bài viết/quảng cáo (origin:<conv>) — cần cho sản phẩm trọng tâm."""
    if db.get_setting("prof:" + conv_id):
        return False
    if db.get_setting("gender:" + conv_id) and db.get_setting("origin:" + conv_id):
        return False
    try:
        now = time.time()
        r = _api("GET", f"/pages/{PAGE_ID}/conversations",
                 params={"since": int(now - lookback), "until": int(now) + 60,
                         "page_number": 1, "page_size": 50})
        convs = r.get("conversations") or []
        if "error" in r:
            return False                       # lỗi mạng: chưa đánh dấu, tin sau thử lại
        _found = False
        for c in convs:
            if c.get("id") == conv_id:
                _src_from_conv_obj(conv_id, c)
                pc = c.get("page_customer") or {}
                if pc.get("gender") in ("male", "female") and not db.get_setting("gender:" + conv_id):
                    db.set_setting("gender:" + conv_id, pc["gender"])
                db.log_webhook("profile", f"{conv_id}: hồ sơ từ API — gender={pc.get('gender')} "
                               f"tên={db.get_setting('name:' + conv_id) or '(không đạt)'} "
                               f"nguồn={db.get_setting('origin:' + conv_id) or '(không có)'}")
                _found = True
                break
        if not db.get_setting("gender:" + conv_id):
            # v0.1.73: không thấy trong danh sách 2 giờ gần nhất (page đông) → hỏi thẳng hội thoại này
            rm = _api("GET", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages")
            if isinstance(rm, dict) and "error" not in rm:
                g = _gender_in_obj({k: v for k, v in rm.items() if k != "messages"}) or \
                    _gender_in_obj([m.get("from") for m in (rm.get("messages") or [])[:10] if isinstance(m, dict)])
                if g:
                    db.set_setting("gender:" + conv_id, g)
                    db.log_webhook("profile", f"{conv_id}: giới tính từ hội thoại Pancake — {g}")
        db.set_setting("prof:" + conv_id, "1")
        return _found
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"profile_fetch {conv_id}: {ex}")
        return False


# ---- v0.1.31 (17/10, chị Nga): tách TÊN GỌI + giới tính từ tên Facebook ----
# "Ngoan Do Thi" (không dấu, đảo thứ tự) = Đỗ Thị Ngoan → "chị Ngoan"; "Đoàn Phương Mai" → "chị Mai".
_SURNAMES = {"nguyen", "tran", "le", "pham", "hoang", "huynh", "phan", "vu", "vo", "dang", "bui", "do", "ho",
             "ngo", "duong", "ly", "dinh", "trinh", "truong", "lam", "luong", "ha", "cao", "doan", "ta", "tong",
             "chu", "kieu", "lai", "luu", "mac", "nghiem", "quach", "thai", "tieu", "trieu", "van", "vuong", "la",
             "mai", "khuc", "kim", "lu", "giap", "an", "ung", "au", "bach", "dao", "diep", "dong", "han", "hua", "tang"}


def _fold_name(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def call_name(full: str, gender: str = "") -> str:
    """Trả 'chị Ngoan' / 'anh Hùng' hoặc '' (không chắc → để bot gọi anh/chị)."""
    toks = [t for t in re.split(r"[\s._\-]+", (full or "").strip()) if t]
    if not toks or len(toks) > 5 or any(ch.isdigit() for ch in full):
        return ""
    folded = [_fold_name(t) for t in toks]
    has_marks = _fold_name(full) != (full or "").lower()
    # v0.1.98: tên trang / cửa hàng / có danh xưng ("Shop Sâm Hà Nội", "Cô Ba Sài Gòn") → không gọi tên
    if any(f in ("shop", "store", "official", "sam", "nha", "thuoc", "cty", "company", "gon", "hanoi", "saigon") for f in folded) \
            or folded[0] in ("co", "chu", "bac", "di", "ong", "ba", "anh", "chi", "em", "mr", "mrs", "ms"):
        return ""
    # v0.1.98: tên có "Thị" mà giới tính là nam (hoặc "Văn" mà là nữ) → tài khoản người nhà → không gọi tên
    if (gender == "male" and "thi" in folded[1:]) or (gender == "female" and "van" in folded[1:-1]):
        return ""
    # giới tính: hồ sơ Pancake > tên đệm Thị / Văn
    sex = gender if gender in ("male", "female") else ""
    if not sex:
        if "thi" in folded[1:] or (len(folded) >= 2 and folded[-1] == "thi"):
            sex = "female"
        elif "van" in folded[1:-1] or (len(folded) >= 3 and folded[-1] == "van"):
            sex = "male"
    if not sex:
        return ""
    _TOP = {"nguyen", "tran", "le", "pham", "hoang", "huynh", "phan", "vu", "vo", "dang", "bui", "do", "ho", "ngo", "duong", "ly", "dinh",
            "trinh", "truong", "doan"}
    if len(toks) == 1:
        given = toks[0]
    elif len(toks) == 2 and folded[0] in _SURNAMES and folded[-1] in _SURNAMES:
        # v0.1.98: "An Nguyen", "Hà Trần", "Mai Ha" — cả 2 chữ đều có thể là họ → chữ cuối là họ phổ biến thì tên là chữ đầu; không chắc → không gọi tên
        if folded[-1] in _TOP and folded[0] not in _TOP:
            given = toks[0]
        elif folded[0] in _TOP and folded[-1] not in _TOP:
            given = toks[-1]
        else:
            return ""
    elif folded[0] in _SURNAMES:
        given = toks[-1]                       # thứ tự Việt: Họ … Tên
    elif folded[-1] in _SURNAMES:
        # v0.1.44 (21/10, ca "Hoa Nguyễn" bị gọi "chị Nguyễn"): Tên Họ kiểu Facebook — 2 chữ thì tên là chữ đầu;
        # từ 3 chữ ("Phương Anh Nguyễn") tên ghép không chắc → không gọi tên
        if len(toks) == 2:
            given = toks[0]
        else:
            return ""
    elif any(f in _SURNAMES for f in folded[1:]):
        given = toks[0]                        # đảo kiểu Facebook: Tên Họ (Đệm)
    elif has_marks:
        given = toks[-1]
    else:
        return ""
    if _fold_name(given) in ("thi", "van", "anh", "chi", "em") or len(given) < 2:
        return ""                              # v0.1.98: "Hoang Anh" → không gọi "anh Anh"
    given = given[:1].upper() + given[1:]
    return ("chị " if sex == "female" else "anh ") + given


def _profile_of(conv_id: str) -> str:
    """v0.5.30 C4+C5: hồ sơ khách đưa vào system prompt — nguồn DUY NHẤT cho tên chào/xưng hô."""
    _profile_fetch_once(conv_id)
    parts = []
    nm = db.get_setting("name:" + conv_id) or ""
    g = _infer_gender(conv_id)   # v0.1.65: đoán thêm từ hội thoại khi Pancake chưa có giới tính
    if nm:
        parts.append('tên Facebook của khách: "' + nm + '"')
        call = call_name(nm, g)
        if call:
            parts.append('GỌI KHÁCH: "' + call + '" (hệ thống đã tách tên — dùng đúng cách gọi này, kể cả câu chào)')
    if g in ("male", "female"):
        parts.append("xưng hô với khách: " + ("anh" if g == "male" else "chị"))
    if _off_hours():
        parts.append("THỜI ĐIỂM: NGOÀI GIỜ LÀM VIỆC (nhân viên làm từ " + WORK_START_TXT + ") — khi chuyển nhân viên / chốt đơn / khách để SĐT "
                     "dùng câu chuẩn scripts_approved.off_hours (chốt đơn xong: off_hours_order), KHÔNG hứa 'trong ít phút' / 'gọi ngay'")
    return "; ".join(parts)


# ---- v0.1.27 (chị Nga 16/10): GIỜ LÀM VIỆC — ngoài giờ bot báo "nhân viên nhắn lại từ 08h00 sáng mai" ----
WORK_HOURS = os.environ.get("PANCAKE_WORK_HOURS", "08:00-21:00")   # giờ VN; chị Nga chốt 16/10: 8h–21h mọi ngày, kể cả thứ 7, Chủ nhật


def _hm(x: str) -> int:
    h, _, m = x.strip().partition(":")
    return int(h) * 60 + int(m or 0)


try:
    _WS, _WE = (_hm(p) for p in WORK_HOURS.split("-", 1))
except Exception:  # noqa: BLE001
    _WS, _WE = 480, 1260
WORK_START_TXT = f"{_WS // 60:02d}h{_WS % 60:02d}"


def _off_hours() -> bool:
    t = time.gmtime(time.time() + 7 * 3600)          # giờ VN
    m = t.tm_hour * 60 + t.tm_min
    return not (_WS <= m < _WE)


# ---- v0.5.30 C2: KHỬ TRÙNG LẶP lớp code — lưới cuối sau rule prompt ----
def _norm_dup(s: str) -> str:
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def _too_similar(a: str, b: str, thr: float = 0.9) -> bool:
    a, b = _norm_dup(a), _norm_dup(b)
    if not a or not b:
        return False
    if a == b:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= thr


def _src_of(conv_id: str) -> str:
    return db.get_setting("src:" + conv_id) or "organic"


def _set_src(conv_id: str, src: str, gender: str = ""):
    cur = db.get_setting("src:" + conv_id)
    if cur != src and (cur is None or src == "ads"):    # chỉ ghi mới / nâng cấp lên ads
        db.set_setting("src:" + conv_id, src)
    if gender in ("male", "female") and not db.get_setting("gender:" + conv_id):
        db.set_setting("gender:" + conv_id, gender)


def _src_from_conv_obj(conv_id: str, conv: dict) -> bool:
    """Đọc nguồn từ MỘT object conversation (payload webhook hoặc API). True nếu xác định được."""
    if not isinstance(conv, dict):
        return False
    _save_origin(conv_id, conv)            # v0.1.13: giữ post_id/ad_ids cho sản phẩm trọng tâm
    ads = conv.get("ad_ids") or conv.get("ads")
    pc = conv.get("page_customer") or {}
    g = pc.get("gender") or ""
    _maybe_save_name(conv_id, (conv.get("from") or {}).get("name") or pc.get("name") or "")
    if ads:
        _set_src(conv_id, "ads", g)
        return True
    if "ad_ids" in conv or "ads" in conv:   # field CÓ MẶT nhưng rỗng → biết chắc không phải ads
        _set_src(conv_id, "post" if conv.get("post_id") else "organic", g)
        return True
    return False


def _src_sync_once(lookback: float = 21600, pages: int = 2) -> int:
    """Quét conversations gần đây, cập nhật nguồn cho ca chưa có. since/until là UNIX ts."""
    now, updated = time.time(), 0
    for p in range(1, pages + 1):
        r = _api("GET", f"/pages/{PAGE_ID}/conversations",
                 params={"since": int(now - lookback), "until": int(now),
                         "page_number": p, "page_size": 100})
        convs = r.get("conversations") or []
        if not convs:
            break
        for c in convs:
            cid = c.get("id")
            if not cid or (c.get("type") or "").upper() != "INBOX":
                continue
            if db.get_setting("src:" + cid) == "ads" and db.get_setting("gender:" + cid):
                continue                      # đã chốt ads + có gender thì thôi (v0.5.40: ads thiếu gender vẫn quét)
            before = db.get_setting("src:" + cid)
            _src_from_conv_obj(cid, c)
            if db.get_setting("src:" + cid) != before:
                updated += 1
        if len(convs) < 100:
            break
    if updated:
        db.log_webhook("src_sync", f"cập nhật nguồn cho {updated} hội thoại")
    return updated


def _src_loop():
    while True:
        time.sleep(600)
        try:
            if not is_killed():
                _src_sync_once()
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"src_loop: {ex}")


# ---- B4: giờ im lặng — 0h00–7h30 giờ VN không bắn tin đuổi (tin dồn bung lúc 7h30) ----
def _quiet_now() -> bool:
    t = time.gmtime(time.time() + 7 * 3600)          # giờ VN
    return (t.tm_hour * 60 + t.tm_min) < QUIET_UNTIL_MIN


# ================= v0.5.27 B9: CA NHÀ THUỐC — hỏi thăm ĐÚNG 1 LẦN =================
# Bot chèn thẻ [PHARMACY] khi khách chọn mua nhà thuốc (engine bóc thẻ, trả cờ pharmacy).
# Trạng thái: setting fu_ph:<conv> = {"t": lúc chốt, "sent": 0/1}. Nhịp đuổi thường TẮT.
def _pharm_get(conv_id) -> dict:
    try:
        return json.loads(db.get_setting(f"fu_ph:{conv_id}") or "{}")
    except Exception:  # noqa: BLE001
        return {}


def _pharm_mark(conv_id):
    db.set_setting(f"fu_ph:{conv_id}", json.dumps({"t": time.time(), "sent": 0}))
    _fu_clear(conv_id)      # ca nhà thuốc chỉ hỏi thăm 1 lần — không chạy nhịp đuổi thường
    db.log_webhook("pharm_mark", f"{conv_id}: khách chọn mua nhà thuốc — hẹn hỏi thăm sau ~21h")


def _pharm_clear(conv_id):
    try:
        with db._conn() as c:
            c.execute("DELETE FROM settings WHERE key=?", (f"fu_ph:{conv_id}",))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"pharm_clear {conv_id}: {ex}")


def _pharm_check_once() -> int:
    """Gửi câu hỏi thăm cho ca nhà thuốc đến hạn (~21h, trong cửa sổ 24h; quá 2 ngày thì bỏ)."""
    if is_killed() or not is_enabled() or _quiet_now():
        return 0
    now, acted = time.time(), 0
    try:
        with db._conn() as c:
            rows = c.execute("SELECT key, value FROM settings WHERE key LIKE 'fu_ph:%'").fetchall()
    except Exception:  # noqa: BLE001
        return 0
    for r in rows:
        conv_id = r["key"][6:]
        try:
            st = json.loads(r["value"] or "{}")
            t = float(st.get("t") or 0)
            if st.get("sent") or not t:
                continue
            if db.pancake_is_blocked(conv_id) or (is_test_only() and not db.pancake_is_test(conv_id)):
                _pharm_clear(conv_id)
                continue
            age = now - t
            if age > 2 * 86400:              # trễ quá (kill dài / nghỉ lễ) — thôi, đừng nhắn
                _pharm_clear(conv_id)
                continue
            if age >= PH_T and _may_send(conv_id):
                resp = send_message(conv_id, PH_MSG)
                if not resp.get("error"):
                    db.add_message(db.pancake_local_conv(conv_id), "assistant", PH_MSG)
                    st.update(sent=1, ls=now)
                    db.set_setting(f"fu_ph:{conv_id}", json.dumps(st))
                    add_tag(conv_id, TAG_BOT)
                    db.log_webhook("fu_pharm", f"{conv_id}: hỏi thăm đã mua ở nhà thuốc chưa (1 lần duy nhất)")
                    acted += 1
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"pharm {conv_id}: {ex}")
    return acted


def _pharm_handoff(conv_id: str, meta: dict, text: str) -> dict:
    """Khách phản hồi SAU câu hỏi thăm nhà thuốc → giao người ngay (anh Na chốt: chưa mua hay
    đồng ý đều chuyển Nhóm người), bot không tự xử lý tiếp để khỏi phạm rule 5b."""
    local_id = db.pancake_local_conv(conv_id, customer=meta.get("customer"))
    db.add_message(local_id, "user", text)
    reason = "Khách phản hồi sau hỏi thăm mua nhà thuốc — nhân viên chăm tiếp (không mời lại online)"
    phones = find_phones(text)
    db.add_handoff(local_id, "pancake", reason, phones[0] if phones else "", 2)
    _pharm_clear(conv_id)
    if not _may_send(conv_id):
        return {"ok": True, "pharm_handoff": True, "conv_id": conv_id, "sent": False}
    ack = ("Dạ em cảm ơn anh/chị đã phản hồi ạ. Em chuyển thông tin để bạn phụ trách "
           "hỗ trợ anh/chị ngay nhé ạ.")
    db.add_message(local_id, "assistant", ack)
    rr = send_message(conv_id, ack)
    if not rr.get("error"):
        db.ab_reply(conv_id)
    add_tag(conv_id, TAG_BOT)
    add_tag(conv_id, TAG_BY_LEVEL[2])
    assign(conv_id)
    mark_unread(conv_id)
    _keep_unread(conv_id)   # v0.1.59: khách vừa nhắn + bot đã gửi câu ghi nhận → đánh lại chưa đọc sau 4s/15s/45s (không bị Pancake đè)
    note(conv_id, _handoff_note([{"level": 2, "reason": reason,
                                  "phone": phones[0] if phones else ""}]))
    db.pancake_mark_returned(conv_id, 2)
    db.log_webhook("pharm_handoff", f"{conv_id}: khách phản hồi sau hỏi thăm nhà thuốc → giao người")
    return {"ok": True, "pharm_handoff": True, "handoffs": 1, "conv_id": conv_id,
            "sent": not rr.get("error")}


# ---- Trạng thái nhịp: bảng settings, key fu:<conv_id> — KHÔNG sửa schema db.py ----
def is_fu_enabled() -> bool:
    return _flag("pancake_followup", "PANCAKE_FOLLOWUP")


def _fu_get(conv_id) -> dict:
    try:
        return json.loads(db.get_setting(f"fu:{conv_id}") or "{}")
    except Exception:  # noqa: BLE001
        return {}


def _fu_touch(conv_id, has_phone=False):
    """Khách vừa nhắn → đặt lại đồng hồ và xoá số nhịp đã gửi (khách phản hồi là hết đuổi).
    Cờ 'ph' chỉ tăng, không mất: đã cho SĐT một lần là coi như có."""
    st = _fu_get(conv_id)
    db.set_setting(f"fu:{conv_id}", json.dumps(
        {"t": time.time(), "n": 0, "ls": 0, "ph": 1 if (has_phone or st.get("ph")) else 0}))


def _fu_clear(conv_id):
    try:
        with db._conn() as c:
            c.execute("DELETE FROM settings WHERE key=?", (f"fu:{conv_id}",))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"fu_clear {conv_id}: {ex}")


def _fu_rows() -> list:
    with db._conn() as c:
        rows = c.execute("SELECT key, value FROM settings WHERE key LIKE 'fu:%'").fetchall()
    out = []
    for r in rows:
        try:
            out.append((r["key"][3:], json.loads(r["value"] or "{}")))
        except Exception:  # noqa: BLE001
            continue
    return out


def _fu_pending() -> int:
    try:
        return len(_fu_rows())
    except Exception:  # noqa: BLE001
        return -1


def _fu_has_phone(conv_id, st) -> bool:
    if st.get("ph"):
        return True
    try:
        with db._conn() as c:
            r = c.execute("SELECT phone FROM ab_stats WHERE pancake_conv_id=?",
                          (conv_id,)).fetchone()
        return bool(r and r["phone"])
    except Exception:  # noqa: BLE001
        return False


def _fu_phone_of(conv_id) -> str:
    """SĐT khách đã để lại (bảng leads theo hội thoại nội bộ) — ghi vào gói bàn giao cho TV."""
    try:
        with db._conn() as c:
            r = c.execute("SELECT local_conv_id FROM pancake_map WHERE pancake_conv_id=?",
                          (conv_id,)).fetchone()
            if not r or not r["local_conv_id"]:
                return ""
            p = c.execute("SELECT phone FROM leads WHERE conv_id=? ORDER BY ts DESC LIMIT 1",
                          (r["local_conv_id"],)).fetchone()
        return (p["phone"] if p else "") or ""
    except Exception:  # noqa: BLE001
        return ""


def _fu_send(conv_id, step: int, has_phone: bool, st: dict, src: str = "organic") -> bool:
    """Gửi ĐÚNG 1 CÂU cho một nhịp (anh Na chốt: không nhắn nhiều). Câu chọn theo nguồn ca."""
    if not _may_send(conv_id):
        return False
    if step == 1:
        key = "1_phone" if has_phone else "1_nophone"
    else:
        key = f"{'ads' if src == 'ads' else 'org'}{step}"
    txt = _fu_text(key, conv_id)
    r = send_message(conv_id, txt)
    if r.get("error"):
        return False
    if step == 2 and FU_IMG2:
        # v0.1.14: nhịp 2 gửi kèm ảnh nhà máy + vườn sâm (ảnh thiếu file thì bỏ qua, chỉ ghi log)
        time.sleep(PART_GAP)
        imgs = FU_IMG2
        fp = _focus_of(conv_id)[0] or engine.PAGE_FOCUS_PRODUCT
        if fp == "duong_sam":
            imgs = ["duong-sam-vien", "duong-sam-dong-goi"]   # ảnh sản xuất Dương Sâm (chị Nga gửi 14/10)
        elif fp in _DL_NAMES:
            imgs = [x for x in FU_IMG2 if not x.startswith("nha-may")]   # Long Sâm không sản xuất tại nhà máy Thái Minh Hi-tech
        if imgs:
            send_images(conv_id, imgs)
    db.add_message(db.pancake_local_conv(conv_id), "assistant", txt)
    st.update(n=step, ls=time.time())
    db.set_setting(f"fu:{conv_id}", json.dumps(st))
    add_tag(conv_id, TAG_BOT)
    st["sent"] = sorted(set((st.get("sent") or []) + [step]))
    db.set_setting(f"fu:{conv_id}", json.dumps(st))
    if step >= 3 and FU_LAST_TAG and {1, 2} <= set(st["sent"]):   # chị Nga 23/10: B4 CHỈ gắn khi đã gửi đủ bước 2, 3 trước đó
        # v0.1.56 (chị Nga 23/10): bước cuối (gửi lại CTKM + chào kết) → gắn thẻ B4 để chị kiểm soát
        add_tag(conv_id, FU_LAST_TAG)
    # v0.1.57 (chị Nga 23/10): CHỈ nổi (chưa đọc) khi KHÁCH nhắn — tin nhắc nhớ bot tự gửi thì KHÔNG đánh dấu chưa đọc
    db.log_webhook("fu_sent", f"{conv_id}: nhịp {step} ({src}, {'có SĐT' if has_phone else 'chưa SĐT'})")
    return True


def _fu_handoff(conv_id):
    """Có SĐT mà nhịp 1 vẫn im → giao người gọi ra NGAY, không chờ nhịp 2-3 (anh Na chốt 26/08)."""
    phone = _fu_phone_of(conv_id)
    reason = "Khách im sau nhịp nhắc — đã có SĐT, gọi ra tư vấn trực tiếp"
    db.add_handoff(db.pancake_local_conv(conv_id), "pancake", reason, phone, 2)
    add_tag(conv_id, TAG_BY_LEVEL[2])
    assign(conv_id)
    mark_unread(conv_id)
    note(conv_id, _handoff_note([{"level": 2, "reason": reason, "phone": phone}]))
    db.pancake_mark_returned(conv_id, 2)
    _fu_clear(conv_id)
    db.log_webhook("fu_handoff", f"{conv_id}: giao người gọi ra (SĐT {phone or 'xem trong hội thoại'})")


def _fu_close(conv_id, src: str = "organic", window: float = 86400.0):
    """B5: chỉ đóng Ko PH khi hết CỬA SỔ THẬT của ca (ads 7 ngày, organic 24h) — trước đây
    đóng cứng ở 24h là tự bỏ lead ads khi mới dùng ~14% thời gian cho phép."""
    add_tag(conv_id, TAG_NO_REPLY)
    _fu_clear(conv_id)
    db.log_webhook("fu_close", f"{conv_id}: hết cửa sổ {src} ({window / 3600:.0f}h) không phản hồi, "
                               f"chưa có SĐT → Ko PH")


# v0.1.44 (21/10, chị Nga, ca chị Hoa Nguyễn): hội thoại ĐÃ KẾT THÚC thì KHÔNG nhắc nhớ —
# khách chào/cảm ơn/hẹn "khi nào… sẽ nhắn lại", chưa mua vì lý do sức khỏe, hoặc bot vừa chào tạm biệt/chúc sức khỏe.
_RE_FU_USER_END = re.compile(r"(cảm ơn|cám ơn|camon|thanks|thank|tks|"   # "để suy nghĩ / để sau" KHÔNG tính — vẫn nhắc để chốt
                             r"sẽ nhắn lại|nhắn lại sau|khi nào .{0,40}(nhắn|liên hệ|mua)|chưa (cần|mua|dùng)|không (mua|cần|lấy)|"
                             r"ko (mua|cần|lấy)|thôi nhé|thôi ạ|tạm biệt|bye|hẹn (dịp|lần) khác)", re.I)
_RE_FU_BOT_END = re.compile(r"(chúc .{0,40}(sức khỏe|mạnh khỏe|an lành|ổn định)|cảm ơn .{0,40}(tin tưởng|chia sẻ|quan tâm)|"
                            r"khi nào .{0,60}(nhắn lại|liên hệ)|nhắn lại cho em|cứ nhắn lại|trò chuyện tiếp|hẹn gặp|"
                            r"bên em sẽ (gọi|liên hệ) (lại|xác nhận))", re.I)


def _last_user_thinking(conv_id) -> bool:
    try:
        hist = db.get_history(db.pancake_local_conv(conv_id))
        users = [str(m.get("content") or "") for m in hist if m.get("role") == "user"][-2:]
        return any(_RE_THINKING_ASCII.search(_fold_name(u)) for u in users)
    except Exception:  # noqa: BLE001
        return False


def _fu_conversation_ended(conv_id) -> bool:
    try:
        hist = db.get_history(db.pancake_local_conv(conv_id))
    except Exception:  # noqa: BLE001
        return False
    users = [str(m.get("content") or "") for m in hist if m.get("role") == "user"]
    bots = [str(m.get("content") or "") for m in hist if m.get("role") == "assistant"]
    if not users or not bots:
        return False
    last_u, last_b = users[-1].strip(), bots[-1].strip()
    if "?" in last_u:
        return False                       # khách còn hỏi → vẫn theo
    if any(_RE_THINKING_ASCII.search(_fold_name(u)) for u in users[-2:]):
        return False                       # v0.1.56 (chị Nga chọn cách A): "để suy nghĩ / hỏi người nhà" → VẪN nhắc nhớ để chốt
    if _refused_after_quote(hist):
        return True                        # v0.1.56: đã tư vấn đủ (giá/CTKM) mà khách vẫn dứt khoát không mua
    if _RE_FU_USER_END.search(last_u) or _RE_FU_USER_END_ASCII.search(_fold_name(last_u)):
        return True                        # v0.1.55: bắt cả kiểu gõ không dấu ("Cam on", "tks", "ko mua")
    tail = last_b[-300:]
    if tail.rstrip().endswith("?"):
        return False
    return bool(_RE_FU_BOT_END.search(tail) or _RE_FU_BOT_END_ASCII.search(_fold_name(tail)))


_RE_THINKING_ASCII = re.compile(r"(?<![a-z])(suy nghi|nghi them|nghi da|hoi (y )?(nguoi nha|vo|chong|con|bo|me|chau|gia dinh)|"
                                r"ban (voi|lai voi) (vo|chong|con|nha|gia dinh)|de sau|tinh sau|xem them|can nhac)(?![a-z])")


# v0.1.56 (chị Nga 23/10): ca đã tư vấn ĐẦY ĐỦ (bot đã báo giá / CTKM) mà khách vẫn DỨT KHOÁT không mua → không nhắc nhớ.
# "Để suy nghĩ / để sau / hỏi người nhà" KHÔNG tính là từ chối (vẫn nhắc để chốt); "đắt quá" là chê giá (bot mời Nước Hồng sâm), không tính.
_RE_REFUSE_ASCII = re.compile(r"(?<![a-z])(thoi (khong|ko|k|chua) (mua|lay|can|dung)|(khong|ko|k) (mua|lay|can|dung) (dau|nua|nhe|a|em|chi|anh|roi)|"
                              r"(khong|ko|k|chua) co nhu cau|(khong|ko|k) quan tam|(khong|ko|k) mua (duoc|dau)|thoi khong|thoi ko|"
                              r"(khong|ko|k) can (dau|nua)|de dip khac|hen dip khac|(minh|em|chi|anh|toi|tao) (khong|ko|k) mua)(?![a-z])")


def _refused_after_quote(hist) -> bool:
    quoted = False
    refused = False
    for m in hist:
        c = str(m.get("content") or "")
        if m.get("role") == "assistant" and re.search(r"\d{2,3}\.000đ", c):
            quoted = True
        elif m.get("role") == "user" and quoted:
            if _RE_REFUSE_ASCII.search(_fold_name(c)):
                refused = True
            elif refused and "?" in c:
                refused = False          # từ chối xong lại hỏi tiếp → vẫn đang quan tâm
    return refused


# v0.1.55 (23/10, ca Luong Nguyen Van): khách gõ "Cam on" không dấu, bot đã chúc "một ngày tốt lành và nhiều sức khỏe"
# → vẫn bị nhắc nhớ. So khớp thêm trên chữ đã bỏ dấu.
_RE_FU_USER_END_ASCII = re.compile(r"(?<![a-z])(cam on|camon|cam onn|c on|thank|thanks|tks|thx|tam biet|bye|"
                                   r"hen (dip|lan) khac|khong (mua|can|lay)|ko (mua|can|lay)|k (mua|can|lay)|"
                                   r"chua (can|mua|dung)|se nhan lai|nhan lai sau|thoi nhe|thoi a)(?![a-z])")
_RE_FU_BOT_END_ASCII = re.compile(r"chuc .{0,60}(suc khoe|manh khoe|an lanh|on dinh|tot lanh|vui ve)|"
                                  r"cam on .{0,40}(tin tuong|chia se|quan tam)|nhan (lai )?(cho )?em (nhe|bat cu)")


def _fu_check_once() -> int:
    """Một lượt quét nhịp — v0.5.27 theo NGUỒN ca: ads 30ph/1 ngày/3 ngày trong cửa sổ 7 ngày;
    organic 1h/8h trong 24h. Nhịp 1 cho mọi ca; sau đó CÓ SĐT thì giao người gọi (grace 30'),
    CHƯA CÓ SĐT thì đi tiếp các nhịp của nguồn đó. B4: 0h–7h30 giờ VN không bắn gì."""
    if is_killed() or not is_enabled() or not is_fu_enabled():
        return 0
    if _quiet_now():
        return 0                # B4: tin dồn sẽ bung sau 7h30 (loop chạy mỗi 60 giây)
    now, acted = time.time(), 0
    for conv_id, st in _fu_rows():
        try:
            t = float(st.get("t") or 0)
            n = int(st.get("n") or 0)
            if not t:
                _fu_clear(conv_id)
                continue
            # ca đã về người / sale tiếp quản / ngoài phạm vi chế độ thử → không đuổi
            if db.pancake_is_blocked(conv_id) or (is_test_only() and not db.pancake_is_test(conv_id)):
                _fu_clear(conv_id)
                continue
            if not db.pancake_bot_sent_recent(conv_id):
                continue        # bot chưa từng nhắn trong ca này → chưa có gì để theo đuổi
            if _ts_setting("fu_stop:" + str(conv_id)) >= t and not _last_user_thinking(conv_id):
                # v0.1.56: lượt trả lời cuối đã kết luận không dùng được / hỏi bác sĩ (khách nhắn lại sau đó thì tính lại từ đầu)
                _fu_clear(conv_id)
                continue
            if db.get_setting("order_done:" + str(conv_id)):
                # v0.1.47 (chị Nga 22/10): khách ĐÃ CHỐT ĐƠN → không nhắc nhớ nữa (kể cả khi khách hỏi thêm rồi im)
                db.log_webhook("fu_skip", f"{conv_id}: khách đã chốt đơn — không nhắc nhớ")
                _fu_clear(conv_id)
                continue
            if _ts_setting("human_at:" + str(conv_id)) and _fu_has_phone(conv_id, st):
                # v0.1.47: khách có SĐT + nhân viên đã nhắn tay vào ca → nhân viên đang lo (gọi/lên đơn) → không nhắc nhớ
                db.log_webhook("fu_skip", f"{conv_id}: có SĐT + nhân viên đã vào ca — không nhắc nhớ")
                _fu_clear(conv_id)
                continue
            if _fu_conversation_ended(conv_id):   # v0.1.45: áp cho MỌI nhịp
                db.log_webhook("fu_skip", f"{conv_id}: hội thoại đã kết thúc (khách cảm ơn/hẹn lại hoặc bot đã chào) — không nhắc nhớ")
                _fu_clear(conv_id)
                continue
            src = _src_of(conv_id)
            steps = FU_ADS if src == "ads" else FU_ORG
            window = FU_WINDOW_ADS if src == "ads" else FU_WINDOW
            age = now - t
            has_phone = _fu_has_phone(conv_id, st)
            if age >= window:               # B5: hết cửa sổ THẬT của ca mới đóng
                if n >= 1 and has_phone:
                    _fu_handoff(conv_id)
                elif n >= 1:
                    _fu_close(conv_id, src, window)
                else:
                    _fu_clear(conv_id)
                acted += 1
            elif n >= 1 and has_phone:
                if now - float(st.get("ls") or t) >= FU_GRACE:
                    _fu_handoff(conv_id)
                    acted += 1
            elif n < len(steps) and age >= steps[n]:
                _why = _fu_stop_check(conv_id)   # v0.1.85: kiểm tra lại Pancake NGAY TRƯỚC khi nhắc
                if _why:
                    db.log_webhook("fu_skip", f"{conv_id}: {_why} — huỷ nhắc nhớ")
                    _fu_clear(conv_id)
                    continue
                acted += 1 if _fu_send(conv_id, n + 1, has_phone, st, src) else 0
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"fu {conv_id}: {ex}")
    return acted


CONFIRM_WAIT = float(os.environ.get("PANCAKE_CONFIRM_WAIT", "300"))   # v0.1.81: 5 phút (chị Nga 25/10)
CONFIRM_SILENT = "[Khách chưa trả lời sau 5 phút kể từ khi em gửi tổng hợp đơn — coi như khách ĐỒNG Ý đơn]"


def _confirm_wait_check() -> int:
    """v0.1.81 (chị Nga 25/10): khách nhắn 'lấy 1 hộp' → bot gửi tổng hợp đơn → 10 phút khách im (hoặc khách ok/like)
    → bot ghi nhận đơn + gắn thẻ 'Bot chốt đơn' (HANDOFF mức 1, đẩy Nhanh) + mời lên gói ĐÚNG 1 LẦN."""
    if is_killed() or not is_enabled():
        return 0
    with db._conn() as c:
        rows = c.execute("SELECT key, value FROM settings WHERE key LIKE 'cfw:%'").fetchall()
    now, n = time.time(), 0
    for r in rows:
        conv_id, v = r["key"][4:], (r["value"] or "").strip()
        if not v:
            continue
        try:
            ts = float(v)
        except ValueError:
            db.set_setting("cfw:" + conv_id, "")
            continue
        if now - ts < CONFIRM_WAIT:
            continue
        db.set_setting("cfw:" + conv_id, "")
        if now - ts > 6 * 3600 or db.pancake_is_blocked(conv_id) or db.get_setting("order_done:" + conv_id):
            continue
        if is_test_only() and not db.pancake_is_test(conv_id):
            continue
        db.log_webhook("cfw_due", f"{conv_id}: 5 phút sau tổng hợp đơn khách chưa trả lời → ghi nhận đơn + mời lên gói")
        try:
            _respond(conv_id, CONFIRM_SILENT, {"customer": None})
            n += 1
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"cfw respond {conv_id}: {ex}")
    return n


def _fu_loop():
    while True:
        time.sleep(60)
        try:
            _fu_check_once()
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"fu_loop: {ex}")
        try:
            _confirm_wait_check()   # v0.1.81: tổng hợp đơn quá 10 phút khách chưa trả lời → ghi nhận + mời lên gói
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"cfw_loop: {ex}")
        try:
            _pharm_check_once()   # v0.5.27 B9: hỏi thăm ca nhà thuốc đến hạn
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"pharm_loop: {ex}")


# ================= v0.5.34 D1: TRẢ LỜI BÌNH LUẬN (cơ chế test thật OK 29/08) =================
# Van: pancake_comment (mặc định 0 — TẮT), pancake_comment_test (mặc định 1 — chỉ trả lời
# bình luận chứa #tm). Luồng: khách comment → (1) nhắn riêng inbox 1 tin tư vấn do engine soạn
# (FB CHỈ CHO ĐÚNG 1 TIN private reply mỗi comment; khách nhắn lại thì luồng INBOX thường
# tiếp quản) → (2) trả lời công khai 1 câu ngắn mời check Messenger (không nêu giá) →
# (3) ghi sẵn lịch sử vào hội thoại inbox vừa sinh để bot có ngữ cảnh + đánh dấu cmt:<conv>.
CMT_RATE_MAX = int(os.environ.get("CMT_RATE_MAX", "30"))     # trần trả lời bình luận mỗi giờ
# v0.1.15 (chị Nga chốt 13/10): trả lời CÔNG KHAI dưới bình luận — 2 kiểu, luân phiên ngẫu nhiên.
# {sp} = tên sản phẩm của bài viết (POST_PRODUCT_MAP) hoặc mặc định của page.
CMT_PUBLIC_CHECK = [   # v0.1.40 (chị Nga 21/10): cảm ơn quan tâm sản phẩm + nhờ khách kiểm tra tin nhắn để nhận thông tin chi tiết
    "Dạ em cảm ơn anh/chị đã quan tâm đến sản phẩm {sp} ạ. Em đã gửi thông tin chi tiết qua tin nhắn, anh/chị kiểm tra Messenger giúp em nhé ạ 🌿",
    "Em cảm ơn anh/chị đã quan tâm sản phẩm {sp} ạ. Anh/chị vui lòng kiểm tra tin nhắn để nhận thông tin chi tiết từ em nhé ạ 😊",
    "Dạ cảm ơn anh/chị đã quan tâm đến {sp} ạ. Thông tin chi tiết và ưu đãi em đã nhắn riêng cho anh/chị, anh/chị xem tin nhắn giúp em nhé ạ.",
]
CMT_PUBLIC_HOTLINE = [  # mẫu chị Nga — dùng khi KHÔNG nhắn riêng được (hoặc xen kẽ khi đã nhắn riêng)
    "Em cảm ơn anh/chị đã tin tưởng lựa chọn sản phẩm {sp} để hỗ trợ bồi bổ, nâng cao sức khỏe ạ. Cần đặt mua hàng hoặc tư vấn thêm về sản phẩm, anh/chị có thể liên hệ đến hotline 1800 1120 hoặc ghé cửa hàng địa chỉ số 92 Trung Kính - Cầu Giấy - Hà Nội ạ.",
]
# v0.1.40 (chị Nga 21/10): PHÂN LOẠI BÌNH LUẬN trước khi trả lời
#  1 hỏi giá/thông tin → nhắn riêng tư vấn + CMT_PUBLIC_CHECK
#  2 khen/chia sẻ dùng tốt → công khai CMT_PUBLIC_THANKS + nhắn riêng hỏi thăm, báo ưu đãi khách quen
#  3 chê/phàn nàn/tiêu cực → KHÔNG trả lời; gắn thẻ Người xử lý + giao ca + chưa đọc + ghi chú
#  4 tag bạn bè / chỉ icon / link lạ / không liên quan → bỏ qua
CMT_PUBLIC_THANKS = [
    "Dạ em cảm ơn anh/chị đã tin dùng và chia sẻ cảm nhận ạ. Chúc anh/chị và gia đình luôn mạnh khỏe ạ 🌿",
]
_CMT_NEG_HARD = re.compile(r"(hàng giả|\bgiả\b|lừa|đảo|fake|phốt|công an|tố cáo|khiếu nại|hoàn tiền|trả hàng|đổi trả|"
                           r"vô dụng|\btệ\b|\bdở\b|kém chất lượng|thất vọng|đừng mua|không nên mua|ko nên mua|ngộ độc|"
                           r"mất tiền|chặt chém|giá cắt cổ|\bbịp\b)", re.I)
_CMT_NEG_SOFT = re.compile(r"(không (thấy|có) (tác dụng|hiệu quả|gì)|ko (thấy|có) (tác dụng|hiệu quả|gì)|chẳng (thấy|có) (gì|tác dụng)|"
                           r"tác dụng phụ|dị ứng|mẩn ngứa|nổi mẩn|đau bụng|tiêu chảy|buồn nôn|\bnôn\b)", re.I)
_CMT_QUESTION = re.compile(r"(\?|\b(không|ko|k|hông|chưa|nhỉ|ạ)\s*$|có .{0,30}(không|ko)\b)", re.I)
_CMT_POS = re.compile(r"(tốt lắm|rất tốt|tốt quá|dùng tốt|uống tốt|hiệu quả lắm|thấy khỏe|khỏe hơn|ngủ ngon|ngon lắm|tuyệt vời|"
                      r"hài lòng|ưng lắm|ok lắm|oke lắm|đã dùng|dùng rồi|mua rồi|uống rồi|đang dùng|tin dùng|cảm ơn shop|"
                      r"cảm ơn page|cám ơn shop|xịn|đẹp quá|đẹp lắm)", re.I)
_CMT_ASK = re.compile(r"(giá|bao nhiêu|\bbn\b|\bib\b|\binb\b|inbox|tư vấn|\btv\b|ship|đặt hàng|cách dùng|dùng (thế|như) nào|"
                      r"có tốt không|dùng được|uống được|\bxin\b|thông tin|\?)", re.I)


def classify_comment(text: str) -> int:
    """Trả 1 (hỏi), 2 (khen), 3 (tiêu cực), 4 (bỏ qua)."""
    t = (text or "").strip()
    if re.fullmatch(r"\s*\.+\s*", t):
        return 1                                   # khách chấm '.' = xin inbox
    if _CMT_NEG_HARD.search(t):
        return 3                                   # cáo buộc / chê nặng
    if _CMT_NEG_SOFT.search(t) and not _CMT_QUESTION.search(t):
        return 3                                   # kể bị phản ứng / không hiệu quả (câu hỏi "có tác dụng phụ không?" → loại 1)
    if re.search(r"https?://|www\.", t, re.I):
        return 4                                   # link lạ / quảng cáo của người khác
    core = re.sub(r"@\S+", " ", t)                 # bỏ tag bạn bè
    words = re.findall(r"[0-9A-Za-zÀ-ỹĐđ]+", core)
    if not words:
        return 4                                   # chỉ icon / sticker / tag
    if _CMT_ASK.search(t):
        return 1
    if _CMT_POS.search(t):
        return 2                                   # khen (không kèm câu hỏi giá/thông tin)
    if "@" in t and len(words) <= 3:
        return 4                                   # tag bạn bè kèm vài chữ ("@Lan xem này")
    return 1                                       # còn lại: coi như quan tâm sản phẩm → tư vấn


if engine.IS_DS:   # v0.3.0: page Dương Sâm — trả lời công khai tế nhị (không nhắc chuyện sinh lý), hotline 1800 8308
    CMT_PUBLIC_CHECK = [
        "Dạ em cảm ơn anh đã quan tâm đến sản phẩm {sp} ạ. Em đã gửi thông tin chi tiết qua tin nhắn, anh kiểm tra Messenger giúp em nhé ạ 🌿",
        "Dạ em cảm ơn anh đã quan tâm ạ. Thông tin chi tiết và ưu đãi em đã nhắn riêng cho anh, anh xem tin nhắn giúp em nhé ạ.",
    ]
    CMT_PUBLIC_HOTLINE = [
        "Dạ em cảm ơn anh đã quan tâm sản phẩm {sp} ạ. Cần tư vấn hoặc đặt hàng, anh liên hệ hotline 1800 8308 (miễn phí) hoặc nhắn tin cho page giúp em nhé ạ.",
    ]
    CMT_PUBLIC_THANKS = ["Dạ em cảm ơn anh đã tin dùng và chia sẻ cảm nhận ạ. Chúc anh luôn mạnh khỏe ạ 🌿"]
CMT_PUBLIC = CMT_PUBLIC_CHECK   # giữ tên cũ cho chỗ khác có thể đang dùng
CMT_PROFILE = ("KHÁCH ĐẾN TỪ BÌNH LUẬN dưới bài đăng/quảng cáo của page — nội dung bình luận nằm "
               "ở tin nhắn của khách. Đây là TIN NHẮN RIÊNG ĐẦU TIÊN VÀ DUY NHẤT em được gửi "
               "trước khi khách trả lời (Facebook chỉ cho đúng 1 tin), nên trong MỘT tin liền mạch: "
               "(1) chào khách 'Dạ Sâm Thái Minh chào anh/chị ạ' (KHÔNG xưng dược sĩ); "
               "(2) trả lời đúng ý bình luận (hỏi giá → báo giá + các combo theo tháng; hỏi công dụng/đối tượng → trả lời đúng trọng tâm, có chữ 'hỗ trợ'); "
               "(3) nếu phù hợp thì mời khách mua bằng ĐÚNG 1 câu hỏi chọn gói/liệu trình, không ép; bình luận chỉ khen/cảm ơn → "
               "cảm ơn và hỏi khách có cần em tư vấn thêm không. Kết bằng đúng 1 câu hỏi để khách nhắn lại. "
               "TUYỆT ĐỐI không chèn thẻ [HANDOFF]/[IMG]/[PHARMACY], không hứa gọi điện.")


CMT_PROFILE_POS = ("KHÁCH ĐẾN TỪ BÌNH LUẬN KHEN / CHIA SẺ DÙNG TỐT sản phẩm dưới bài đăng của page (khách đã dùng). "
                   "Đây là TIN NHẮN RIÊNG ĐẦU TIÊN VÀ DUY NHẤT em được gửi trước khi khách trả lời. Trong MỘT tin: "
                   "chào 'Dạ Sâm Thái Minh chào anh/chị ạ', cảm ơn khách đã tin dùng và chia sẻ, chúc sức khỏe, rồi theo câu chuẩn "
                   "scripts_approved.positive_feedback: báo bên em có ưu đãi tri ân dành riêng cho khách hàng quen và hỏi khách có muốn "
                   "tham khảo cho đợt dùng tiếp theo không. KHÔNG báo giá, KHÔNG nêu combo khách mới, KHÔNG chèn thẻ [HANDOFF]/[IMG].")
if engine.IS_DS:
    CMT_PROFILE = CMT_PROFILE.replace("Dạ Sâm Thái Minh chào anh/chị ạ", "Dạ Dương Sâm Linh Đan chào anh ạ").replace(
        "combo theo tháng", "3 gói Liệu trình 1/2/3 tháng theo scripts_approved.price_quote_duongsam")
    CMT_PROFILE_POS = CMT_PROFILE_POS.replace("Dạ Sâm Thái Minh chào anh/chị ạ", "Dạ Dương Sâm Linh Đan chào anh ạ")
if engine.IS_NHS:   # v0.4.0: bot Nước Hồng sâm — báo giá dưới bình luận theo 3 combo 2/4/6 hộp
    CMT_PROFILE = CMT_PROFILE.replace("các combo theo tháng", "3 combo 2/4/6 hộp theo scripts_approved.price_quote_nhs").replace(
        "chọn gói/liệu trình", "chọn gói (KHÔNG nói 'liệu trình', KHÔNG gọi combo theo tháng)")


def _cmt_post_id(conv: dict, conv_id: str) -> str:
    """post_id = {PAGE_ID}_{POST_ID}; conv_id của comment = {POST_ID}_{COMMENT_ID}."""
    pid = conv.get("post_id") or ""
    if pid:
        return pid
    return f"{PAGE_ID}_{(conv_id or '').split('_')[0]}"


def _cmt_rate_ok() -> bool:
    """Đếm trả lời bình luận theo giờ VN — quá trần thì thôi (chống loạt comment ảo/spam)."""
    hour = time.strftime("%Y%m%d%H", time.gmtime(time.time() + 7 * 3600))
    raw = db.get_setting("cmt_rate", "") or ""
    h, _, n = raw.partition(":")
    cnt = int(n or 0) if h == hour else 0
    if cnt >= CMT_RATE_MAX:
        return False
    db.set_setting("cmt_rate", f"{hour}:{cnt + 1}")
    return True


def handle_comment(conv: dict, msg: dict, conv_id: str) -> dict:
    """Guard rẻ chạy ngay trong webhook; việc nặng (engine + 2 lần gửi) đẩy sang thread."""
    # v0.1.38 (21/10, chị Nga): bật/tắt bằng biến Railway PANCAKE_COMMENT=1 (setting admin, nếu có, vẫn ưu tiên)
    if db.get_setting("pancake_comment", os.environ.get("PANCAKE_COMMENT", "0")) != "1":
        return {"skip": f"type=COMMENT", "conv_id": conv_id}
    if msg.get("from", {}).get("id") == PAGE_ID or msg.get("is_from_page"):
        return {"skip": "cmt_from_page", "conv_id": conv_id}
    text = _strip_html(msg.get("message") or msg.get("text") or "")
    if not text:
        return {"skip": "cmt_no_text", "conv_id": conv_id}
    kind = classify_comment(text)
    if kind == 4:
        if not _already_seen(f"cmt4:{msg.get('id') or conv_id}"):
            db.log_webhook("cmt_skip", f"{conv_id}: bình luận tag bạn/icon/không liên quan — bot bỏ qua: {text[:80]}")
        return {"skip": "cmt_irrelevant", "conv_id": conv_id}
    if kind == 3:
        if not _already_seen(f"cmt3:{msg.get('id') or conv_id}"):
            try:
                reason = "Bình luận CHÊ/PHÀN NÀN công khai — bot KHÔNG trả lời, nhân viên xử lý tay ngay"
                add_tag(conv_id, TAG_BY_LEVEL[2])
                assign(conv_id)
                mark_unread(conv_id)
                note(conv_id, f"🔴 {reason}: \"{text[:200]}\"")
                db.log_webhook("cmt_negative", f"{conv_id}: {reason}: {text[:120]}")
            except Exception as ex:  # noqa: BLE001
                db.log_webhook("error", f"cmt_negative {conv_id}: {ex}")
        return {"skip": "cmt_negative", "conv_id": conv_id}
    if (db.get_setting("pancake_comment_test", os.environ.get("PANCAKE_COMMENT_TEST", "1")) != "0"
            or db.get_setting("pancake_test_only", "0") == "1"):
        if TEST_KEYWORD not in text.lower():
            return {"skip": "cmt_not_test", "conv_id": conv_id}
    if is_killed() or not is_enabled():
        return {"skip": "cmt_van_off", "conv_id": conv_id}
    # v0.5.35: A/B 50/50 Ở TẦNG BÌNH LUẬN (anh Na chốt 29/08) — chia theo hash KHÁCH y như
    # inbox, nên hội thoại inbox sinh từ private reply rơi ĐÚNG NHÓM đó luôn (cùng customer).
    # Nhóm ĐỐI CHỨNG (human): bot không đụng — nhân viên trả lời comment như quy trình cũ.
    # Comment #tm luôn thuộc bot (miễn trừ A/B như inbox).
    if TEST_KEYWORD not in text.lower():
        grp = db.pancake_ab_group(conv_id, conv.get("customer_id"), _ab_percent())
        if grp == "human":
            if not _already_seen(f"cmtab:{conv_id}"):
                db.log_webhook("cmt_human",
                               f"{conv_id}: bình luận nhóm ĐỐI CHỨNG — nhường nhân viên: {text[:80]}")
            return {"skip": "cmt_ab_human", "conv_id": conv_id}
    if _quiet_now():
        db.log_webhook("cmt_skip", f"{conv_id}: bình luận trong giờ im lặng — không auto trả lời: {text[:80]}")
        return {"skip": "cmt_quiet", "conv_id": conv_id}
    msg_id = msg.get("id") or msg.get("message_id") or conv_id
    if _already_seen(f"cmt:{msg_id}"):
        return {"skip": "dup", "conv_id": conv_id}
    if not _cmt_rate_ok():
        db.log_webhook("cmt_skip", f"{conv_id}: quá trần {CMT_RATE_MAX} trả lời bình luận/giờ — bỏ qua")
        return {"skip": "cmt_rate", "conv_id": conv_id}
    threading.Thread(target=_cmt_worker, daemon=True,
                     args=(conv_id, msg_id, text, conv.get("customer_id") or "",
                           _cmt_post_id(conv, conv_id), kind)).start()
    return {"ok": True, "event": "comment", "conv_id": conv_id, "queued": True}


def _cmt_gone(r) -> bool:
    """v0.5.36: bình luận đã bị Facebook gỡ/ẩn (bộ lọc spam, người viết xoá) — KHÔNG phải lỗi
    hệ thống. FB trả '(#100, 33) Unsupported post request' khi object không còn (ca anh Na
    29/08: comment test bị FB gắn spam và gỡ → reply_comment fail, tin nhắn riêng vẫn đến)."""
    try:
        t = json.dumps(r, ensure_ascii=False)
    except Exception:  # noqa: BLE001
        return False
    return ("Unsupported post request" in t or "does not exist" in t
            or "cannot be loaded" in t)


def _cmt_worker(conv_id: str, msg_id: str, text: str, customer: str, post_id: str, kind: int = 1):
    """Soạn + gửi: nhắn riêng TRƯỚC (quan trọng hơn), thành công mới trả lời công khai
    (câu công khai nói "đã nhắn riêng" — nhắn riêng fail mà vẫn đăng là nói dối khách)."""
    try:
        # v0.1.13: bình luận dưới bài/quảng cáo của sản phẩm nào → tư vấn đúng sản phẩm đó
        focus = _map_lookup(_post_map(), post_id)
        sp = engine.FOCUS_NAMES.get(focus or engine.PAGE_FOCUS_PRODUCT, "Sâm Thái Minh")
        # v0.1.56 (23/10, ca Phạm Thiêu): channel="messenger" để lưới chào bắt buộc chạy — tin nhắn riêng đầu tiên LUÔN có lời chào
        result = engine.chat([{"role": "user", "content": text}], profile=(CMT_PROFILE_POS if kind == 2 else CMT_PROFILE),
                             channel="messenger", focus=focus or None, focus_source="comment" if focus else "")
        if "error" in result:
            db.log_webhook("cmt_fail", f"{conv_id}: engine: {result['error']}")
            return
        priv = _RE_QR.sub("", _RE_IMG.sub("", result.get("reply") or "")).strip()
        # v0.1.76 (25/10, ca Dương Hạnh): bỏ thẻ ảnh để lại dòng trống lớn → gom lại, mỗi đoạn cách 1 dòng trống
        priv = re.sub(r"[ \t]+\n", "\n", priv)
        priv = re.sub(r"\n{3,}", "\n\n", priv).strip()
        if not priv:
            db.log_webhook("cmt_fail", f"{conv_id}: engine trả rỗng")
            return
        params = {"customer_id": customer} if customer else None
        r1 = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages", params=params,
                  body={"action": "private_replies", "message": priv,
                        "message_id": msg_id, "post_id": post_id})
        if not _body_ok(r1):
            if _cmt_gone(r1):
                db.log_webhook("cmt_gone", f"{conv_id}: bình luận đã bị Facebook gỡ/ẩn trước khi "
                                           f"kịp nhắn riêng — bỏ qua: {text[:80]}")
                return
            db.log_webhook("cmt_fail",
                           f"{conv_id}: private_replies: {json.dumps(r1, ensure_ascii=False)[:250]}")
            # v0.1.15: không nhắn riêng được → vẫn trả lời công khai bằng mẫu hotline + cửa hàng (không nói "đã nhắn tin")
            r3 = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages", params=params,
                      body={"action": "reply_comment", "message": random.choice(CMT_PUBLIC_HOTLINE).format(sp=sp),
                            "message_id": msg_id})
            db.log_webhook("cmt_reply" if _body_ok(r3) else "cmt_fail",
                           f"{conv_id}: trả lời công khai mẫu hotline (nhắn riêng lỗi)")
            return
        db.log_webhook("cmt_priv", f"{conv_id}: '{text[:60]}' → đã nhắn riêng ({len(priv)} ký tự)")
        r2 = _api("POST", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages", params=params,
                  body={"action": "reply_comment",
                        "message": random.choice(CMT_PUBLIC_THANKS if kind == 2 else CMT_PUBLIC_CHECK).format(sp=sp),   # v0.1.39/40: đã nhắn riêng → mời xem tin nhắn (khen → cảm ơn); hotline chỉ khi nhắn riêng lỗi
                        "message_id": msg_id})
        if _body_ok(r2):
            db.log_webhook("cmt_reply", f"{conv_id}: đã trả lời công khai dưới bình luận")
        elif _cmt_gone(r2):
            db.log_webhook("cmt_gone", f"{conv_id}: bình luận đã bị Facebook gỡ/ẩn — không trả lời "
                                       f"công khai được, tin nhắn riêng ĐÃ gửi thành công")
        else:
            db.log_webhook("cmt_fail",
                           f"{conv_id}: reply_comment: {json.dumps(r2, ensure_ascii=False)[:250]}")
        _cmt_seed_inbox(conv_id, msg_id, text, customer, priv, post_id)
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("cmt_fail", f"{conv_id}: {ex}")


def _cmt_seed_inbox(conv_id: str, msg_id: str, text: str, customer: str, priv: str, post_id: str = ""):
    """Nhắn riêng mở 1 hội thoại INBOX mới — ghi sẵn lịch sử để khi khách trả lời, bot có
    ngữ cảnh (không tư vấn lại từ đầu, rule 5k/5m dùng được) + đánh dấu nguồn cmt:<inbox>.
    v0.1.13: ghi luôn post_id của bài để inbox đó giữ đúng sản phẩm trọng tâm."""
    try:
        params = {"customer_id": customer} if customer else None
        r = _api("GET", f"/pages/{PAGE_ID}/conversations/{conv_id}/messages", params=params)
        inbox = ""
        for m in (r.get("messages") or []):
            if m.get("id") == msg_id and m.get("private_reply_conversation"):
                prc = m["private_reply_conversation"]
                inbox = (prc.get("id") or "") if isinstance(prc, dict) else str(prc)
                break
        if not inbox:
            return
        local = db.pancake_local_conv(inbox, customer=customer)
        db.add_message(local, "user", f"[Bình luận của khách dưới bài đăng] {text}")
        db.add_message(local, "assistant", priv)
        db.set_setting(f"cmt:{inbox}", "1")
        if post_id:
            _save_origin(inbox, {"post_id": post_id})
        # v0.1.76: tin nhắn riêng từ bình luận chỉ được 1 tin chữ (Facebook) → chưa gửi được ảnh;
        # khách nhắn lại là lượt đầu trong inbox sẽ gửi kèm ảnh sản phẩm
        db.set_setting("img_pending:" + str(inbox), "1")
        db.log_webhook("cmt_seed", f"bình luận {conv_id} → inbox {inbox}: đã ghi ngữ cảnh cho bot")
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("cmt_fail", f"seed {conv_id}: {ex}")


# ================================ SLA WATCHER (mục 7.4) ================================
# Quét mỗi 60 giây các ca pancake còn mở; quá hạn theo level → đánh dấu chưa đọc lần nữa
# (+ assign lại với Level 2) — đúng phương án tạm của kế hoạch cho tới khi có cảnh báo Zalo/Telegram.
def _sla_check_once() -> int:
    """Một lượt quét SLA. Trả về số ca quá hạn vừa nhắc."""
    if is_killed() or not is_enabled():
        return 0
    now = time.time()
    pinged = 0
    for h in db.pancake_open_handoffs():
        if h.get("sla_pinged"):
            continue
        mins = db.SLA_MINUTES.get(h.get("level", 2), 15)
        if now - h["ts"] < mins * 60:
            continue
        pconv = db.pancake_conv_of_local(h["conv_id"])
        if pconv:
            mark_unread(pconv)
            if h.get("level", 2) == 2:
                assign(pconv)   # quá hạn → chuyển người kế tiếp
            note(pconv, f"⚠️ QUÁ SLA {mins} phút — ca Level {h.get('level',2)}: {h.get('reason','')}")
        db.mark_sla_pinged(h["id"])
        db.log_webhook("sla_overdue", f"{h['id']} level={h.get('level')} conv={h['conv_id']}")
        pinged += 1
    return pinged


def _sla_loop():
    while True:
        time.sleep(60)
        try:
            # v0.5.18: NHỊP TIM — bảng "Tình trạng bot" đọc mốc này để biết engine còn sống.
            # Đặt trước mọi việc khác để nhịp vẫn đập kể cả khi bot đang bị kill/tắt gửi.
            db.set_setting("hb_ts", str(time.time()))
            _sla_check_once()
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"sla_loop: {ex}")


# ================================ POLLING DỰ PHÒNG ================================
# Khi webhook chưa bật được (thiếu slot gói cước): hỏi GET /v2 conversations mỗi 25 giây,
# phát hiện tin khách mới và đưa qua đúng luồng handle_event. Chạy được NGAY với token sẵn có.
# CHỐNG NUỐT BACKLOG (phát hiện 25/08 khi bật thử): (1) lượt quét ĐẦU TIÊN chỉ ghi mốc,
# không xử lý gì; (2) mọi lượt sau chỉ nhận tin có timestamp còn TƯƠI (mặc định 15 phút).
_poll_state = {"baseline_done": False}
POLL_MAX_AGE = float(os.environ.get("PANCAKE_POLL_MAX_AGE", "900"))   # giây


def _msg_is_fresh(m: dict) -> bool:
    """Tin phải có timestamp và không cũ quá POLL_MAX_AGE. Không đọc được timestamp = coi là CŨ
    (an toàn: thà bỏ sót một tin — khách nhắn tiếp sẽ có tin mới — còn hơn trả lời tin hôm qua).
    Pancake có thể trả giờ UTC hoặc giờ VN không kèm múi — chấp nhận tin khớp một trong hai cách hiểu."""
    raw = m.get("inserted_at") or m.get("created_at") or m.get("updated_at") or ""
    if not raw:
        return False
    try:
        from datetime import datetime
        t = datetime.fromisoformat(str(raw).replace("Z", "").split("+")[0].strip())
        epoch = t.timestamp()                      # hiểu như giờ máy chủ (UTC trên Railway)
        now = time.time()
        for shift in (0, -7 * 3600):               # thử cả trường hợp chuỗi là giờ VN (UTC+7)
            age = now - (epoch + shift)
            if -120 <= age <= POLL_MAX_AGE:
                return True
        return False
    except Exception:  # noqa: BLE001
        return False


def _poll_once():
    r = _api("GET", f"/pages/{PAGE_ID}/conversations",
             params={"unread_first": "true", "mode": "NONE", "order_by": "updated_at"},
             base=BASE_V2)
    convs = r.get("conversations") or r.get("data") or []
    if not isinstance(convs, list):
        return {"error": r.get("error") or "bad response"}
    first = not _poll_state["baseline_done"]
    picked = 0
    for cv in convs[:30]:
        cid = cv.get("id")
        ctype = (cv.get("type") or "").upper()
        # v0.5.8 (30/10, chị Nga: bình luận "Ib" không được trả lời): chế độ POLL trước đây CHỈ xét hội thoại INBOX nên bình luận
        # không bao giờ tới bot (bình luận chỉ đi qua webhook). Nay xét cả COMMENT khi đã bật trả lời bình luận.
        _cmt_on = db.get_setting("pancake_comment", os.environ.get("PANCAKE_COMMENT", "0")) == "1"
        if not cid or (ctype and ctype != "INBOX" and not (ctype == "COMMENT" and _cmt_on)):
            continue
        upd = cv.get("updated_at") or ""
        if _already_seen(f"poll:{cid}:{upd}"):
            continue
        if first:
            continue          # lượt đầu: chỉ ghi mốc các hội thoại hiện có, không xử lý
        # lấy tin mới nhất của hội thoại — chỉ nhận tin còn tươi
        rm = _api("GET", f"/pages/{PAGE_ID}/conversations/{cid}/messages")
        msgs = rm.get("messages") or rm.get("data") or []
        for m in msgs[-5:]:
            if not _msg_is_fresh(m):
                continue
            payload = {"event_type": "messaging",
                       "data": {"conversation": cv, "message": m}}
            res = handle_event(payload)
            if res.get("ok"):
                picked += 1
    if first:
        _poll_state["baseline_done"] = True
        return {"polled": len(convs), "baseline": True, "queued": 0}
    return {"polled": len(convs), "queued": picked}


def _poll_loop():
    while True:
        time.sleep(POLL_SECONDS)
        try:
            if not is_polling() or is_killed():
                continue
            res = _poll_once()
            if res.get("baseline"):
                db.log_webhook("poll_baseline", json.dumps(res))
            elif res.get("queued"):
                db.log_webhook("poll", json.dumps(res))
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"poll_loop: {ex}")


def flush_all_batches() -> int:
    """v0.5.29: server sắp tắt (redeploy/restart) — TRẢ LỜI VÉT ngay mọi tin đang nằm trong
    bộ gom, không đợi timer. Sự cố 29/08: khách đang CHỐT ĐƠN nhắn lúc 09:40:56, tin nằm trong
    RAM đúng khe deploy v0.5.28 → mất, khách chờ 1 giờ (đèn đỏ bắt được, phải cứu tay bằng
    replay webhook). Bộ gom là RAM thuần nên tắt là mất — phải vét trước khi chết."""
    with _batch_lock:
        convs = list(_batches.keys())
        for cid in convs:
            b = _batches.get(cid)
            if b and b.get("timer"):
                b["timer"].cancel()
    for cid in convs:
        try:
            _flush(cid)
        except Exception as ex:  # noqa: BLE001
            db.log_webhook("error", f"flush_shutdown {cid}: {ex}")
    if convs:
        db.log_webhook("toggle", f"shutdown: trả lời vét {len(convs)} ca đang gom tin trước khi tắt")
    return len(convs)


_started = False


def start_background():
    """Gọi 1 lần lúc app khởi động: SLA watcher + polling (nếu bật)."""
    global _started
    if _started:
        return
    _started = True
    # v0.5.22 A5: ghi mốc hạ gom tin 45→12 giây lên trang A/B (như mốc bật followup 26/08)
    try:
        if BATCH_SECONDS <= 12 and not db.get_setting("batch12_ts"):
            db.set_setting("batch12_ts", str(time.time()))
            db.log_webhook("toggle", f"gom tin hạ 45→{BATCH_SECONDS:g} giây (v0.5.22) — mốc hiện trên trang A/B")
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"batch12_ts: {ex}")
    try:
        db.log_webhook("nhanh_init", json.dumps(nhanh.init_token(), ensure_ascii=False))   # v0.1.15
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", f"nhanh init: {ex}")
    threading.Thread(target=_sla_loop, daemon=True).start()
    threading.Thread(target=_fu_loop, daemon=True).start()
    threading.Thread(target=_poll_loop, daemon=True).start()
    threading.Thread(target=_orders_loop, daemon=True).start()   # v0.5.24 (D2)
    threading.Thread(target=_src_loop, daemon=True).start()      # v0.5.27 (B1)
