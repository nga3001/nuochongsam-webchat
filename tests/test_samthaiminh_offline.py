"""Test offline bot Sâm Thái Minh — không cần FastAPI/Pancake/API key (mẫu stub docs/04 mục 5).
Chạy: python3 tests/test_samthaiminh_offline.py"""
import os, sys, types, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")
os.environ["PANCAKE_PAGE_ID"] = "999"
import db, engine, tools_core as t, pancake_adapter as pa

ok = 0
def check(cond, msg):
    global ok
    assert cond, msg
    ok += 1

# 1. system prompt build + không còn dấu vết Bình Vị/dạ dày trong phần não
sp = engine.build_system_prompt()
for bad in ["Bình Vị Thái Minh là", "trào ngược", "[IMG: san-pham]", "1800 6397", "niêm mạc", "HP"]:
    check(bad not in sp, f"system prompt còn '{bad}'")
check("92 Trung Kính" in sp and "xưng \"cháu\"" in sp, "prompt thiếu cửa hàng / xưng hô cháu")
check('LUÔN DÙNG CHỮ "HỖ TRỢ"' in sp and "không thay thế thuốc điều trị" in sp, "prompt thiếu rule 'hỗ trợ' cho tác dụng bệnh lý")
_kb = t.load_kb()
check(all(b.lower().startswith("hỗ trợ") or b.lower().startswith("mẹ sau sinh") for b in _kb["products"]["hsvn_lat"]["benefits"]), "benefits HS lát phải bắt đầu bằng 'hỗ trợ'")
check("Thủ tướng" not in _kb["compliance"]["words_banned"] and "pm_visit" in _kb["scripts_approved"], "Thủ tướng: chỉ trả lời khi khách hỏi")
check("chống ung thư" not in _kb["compliance"]["words_banned"] and "chữa ung thư" in _kb["compliance"]["words_banned"], "words_banned chưa cập nhật")
print("system prompt chars:", len(sp))

# 2. tool schema khớp KB
kb = t.load_kb()
check(set(engine.PRODUCT_IDS) == set(kb["products"]), "PRODUCT_IDS lệch KB")
all_skus = {k["sku"] for p in kb["products"].values() for k in p["packages"]}
check(all_skus == {x.strip() for x in engine.SKUS.split(",")}, "SKUS lệch KB")
check(set(kb["compliance"]["all_flags"]) == {x.strip() for x in engine.FLAGS.split(",")}, "FLAGS lệch KB")
for r in kb["programs"]["new_customer"]["rules"]:
    check(r["if_sku"] in all_skus, f"rule sku lạ {r['if_sku']}")

# 3. an toàn — các ca đã chốt với chị Nga
cc = lambda pid, fl: t.compliance_check(fl, pid)["verdict"]
check(cc("hsvn_lat", ["breastfeeding"]) == "BLOCK", "HS lát + cho con bú phải BLOCK")
check(cc("hsmo_tui", ["breastfeeding"]) == "CAUTION", "HS túi + cho con bú dùng được")
check(cc("hsmo_chai", ["breastfeeding"]) == "CAUTION", "HS chai + cho con bú dùng được")
check(cc("hsvn_lat", ["child_under6"]) == "BLOCK", "HS lát trẻ <6")
check(cc("tam_sam_dan", ["child_under12"]) == "BLOCK", "Tam Sâm Đan trẻ <12")
check(cc("tam_sam_dan", ["pregnant"]) == "BLOCK", "Tam Sâm Đan có thai")
check(cc("dong_trung", ["child_under6"]) == "BLOCK", "Đông trùng trẻ <6 (chốt 23/09)")
check(cc("dong_trung", ["child_6_11"]) == "CAUTION", "Đông trùng trẻ 6–11 dùng được, liều do dược sĩ")
check(cc("ruou_sam", ["pregnant"]) == "BLOCK" and cc("ruou_sam", ["breastfeeding"]) == "BLOCK", "Rượu: có thai/cho con bú BLOCK")
check(cc("dong_trung", ["breastfeeding"]) == "BLOCK", "Đông trùng cho con bú")
check(cc("duong_sam", ["under18"]) == "BLOCK", "Dương Sâm <18")
check(cc("ruou_sam", ["under18"]) == "BLOCK", "Rượu <18")
check(cc("long_sam", ["pregnant"]) == "NO_GUIDANCE", "Long Sâm + có thai: chưa có hướng dẫn → không khẳng định")
check(cc("hsvn_lat", []) == "OK", "HS lát không flag")
check(t.compliance_check([], "xyz").get("error"), "product lạ phải lỗi")

# 4. đơn hàng
o = t.build_order([{"sku": "hsvn-lat-14", "qty": 3}], "Lan", "0912345678", "12 Trần Duy Hưng, Trung Hòa, Cầu Giấy, Hà Nội", "new")
check(o["ready_to_confirm"] and o["ship_fee"] == 0 and "dầu nóng" in o["confirm_text"], "combo 3 hộp lát")
o = t.build_order([{"sku": "hsvn-lat-14", "qty": 4}], "Lan", "0912345678", "a, b, Nghệ An", "new")
check(o["promo_applied"][0]["tier_qty"] == 3, "4 hộp → quà bậc 3")
o = t.build_order([{"sku": "hsvn-lat-14", "qty": 2}], "Lan", "0912345678", "a, b, Nghệ An", "unknown")
check(not o["promo_applied"] and not o["ready_to_confirm"], "chưa biết khách mới → không quà, không xác nhận")
o = t.build_order([{"sku": "tra1700-10", "qty": 1}], "Lan", "0912345678", "5 Láng Hạ, Thành Công, Ba Đình, Hà Nội", "new")
check(o["ship_fee"] == 15000, "ship nội thành HN 15k")
o = t.build_order([{"sku": "tra1700-10", "qty": 1}], "Lan", "0912345678", "Thôn 2, xã A, Thanh Hóa", "new")
check(o["ship_fee"] == 20000, "ship tỉnh 20k")
check(t.build_order([{"sku": "tra-nguyenla-40", "qty": 1}], customer_type="new").get("error"), "hàng hết phải chặn")
check(t.build_order([{"sku": "hsvn-lat-14", "qty": 1}], customer_type="returning")["handoff_required"], "khách cũ → handoff")
o = t.build_order([{"sku": "samtuoi-kg", "qty": 1}], "Lan", "0912345678", "a, b, Hà Giang", "new")
check(o["handoff_note"] and o["ship_fee"] == 0, "sâm tươi → handoff, miễn ship (chốt 23/09)")
o = t.build_order([{"sku": "ruou-650", "qty": 1}], "Lan", "0912345678", "a, b, Nghệ An", "new")
check(o["ship_fee"] == 0, "rượu sâm miễn ship (chốt 23/09)")
# CTKM 23/09/2026 – 31/12/2026
_kb2 = t.load_kb()
check(t._promo_active(_kb2, "2026-09-23") and t._promo_active(_kb2, "2026-12-31"), "CTKM phải active trong khung")
check(not t._promo_active(_kb2, "2027-01-01") and not t._promo_active(_kb2, "2026-09-22"), "CTKM ngoài khung phải tắt")
check(t._gift_for(_kb2, "hsvn-lat-14", 2, "2027-01-01") is None, "hết hạn không có quà")
# giấy tờ đã nhận
check("11/CNCTHAIMINH" not in _kb2["products"]["hsmo_chai"]["registration"] and "32 độ" in _kb2["products"]["ruou_sam"]["packages"][1]["label"], "chai HSMO không dùng số túi; hũ 3,5L 32 độ")
check("3496/2024" in _kb2["products"]["duong_sam"]["registration"] and "6193/2024" in _kb2["products"]["long_sam"]["registration"], "số ĐKSP Dương Sâm/Long Sâm")
o = t.build_order([{"sku": "longsam-6", "qty": 1}], "Lan", "0912345678", "a, b, Hà Giang", "new")
check(o["disclaimer_to_mention"], "TPBVSK phải nhắc câu không phải thuốc")
o = t.build_order([{"sku": "hsmo-chai", "qty": 2}], "Lan", "0912345678", "a, b, Nghệ An", "new")
check(o["ship_fee"] == 0, "2 chai Hồng sâm: miễn phí ship (chốt 23/09)")
check("[HANDOFF: đổi trả" in sp and "KHÔNG trả lời" in sp, "prompt: đổi trả → chuyển chuyên viên")

# 5. kênh Pancake chạy trọn 1 lượt với engine giả
db.init(); db.set_setting("pancake_test_only", "0"); db.set_setting("pancake_enabled", "1")
sent = []
pa._api = lambda method, path, params=None, body=None, base=None, **k: (sent.append((method, path, body)) or {"success": True, "id": "m_1"})
_real_engine = pa.engine
def _fake_chat(h, model_key=None, profile=None):
    reply = "Dạ cháu chào bác ạ.\n\nHồng sâm lát giá 1.420.000đ/hộp 14 gói ạ."
    return {"reply": reply, "parts": _real_engine.split_messages(reply), "tool_trace": [], "model": "stub",
            "is_fallback": False, "latency_ms": 1, "usage": {}}
pa.engine = types.SimpleNamespace(chat=_fake_chat, extract_handoffs=_real_engine.extract_handoffs,
                                  split_messages=_real_engine.split_messages, strip_markdown=_real_engine.strip_markdown,
                                  sanitize_out=_real_engine.sanitize_out, FALLBACK_TEXT=_real_engine.FALLBACK_TEXT)
payload = {"event_type": "messaging", "page_id": "999", "data": {  # payload thật bọc trong "data" (stub docs/04 đã cũ)
           "conversation": {"id": "999_C1", "type": "INBOX", "customer_id": "u1"},
           "message": {"id": "m1", "message": "bác muốn hỏi giá hồng sâm", "from": {"uid": None}}}}
pa.handle_event(payload); pa._flush("999_C1")
msgs = [b.get("message") for _, _, b in sent if b and b.get("action") == "reply_inbox"]
check(msgs, "adapter không gửi tin")
print("tin gửi khách:", msgs)

# 5b. bóc thẻ ẩn của engine thật
clean, hs = engine.extract_handoffs("Dạ em chuyển nhân viên ạ.\n[HANDOFF: khách cũ mua tiếp | 0912345678 | 2]")
check("[HANDOFF" not in clean and hs[0]["level"] == 2 and hs[0]["phone"] == "0912345678", "extract_handoffs")
check(engine.sanitize_out("HSMO+ rất tốt, HSD 24 tháng") == "Hồng sâm mật ong dạng túi rất tốt, hạn sử dụng 24 tháng", "sanitize viết tắt")

# 5c. ảnh: map main/adapter khớp nhau, file tồn tại < 1MB, prompt chỉ nhắc mã có thật
import re as _re
_main_src = open(os.path.join(os.path.dirname(pa.__file__), "main.py"), encoding="utf-8").read()
_main_map = _main_src[_main_src.index("IMG_MAP = {"):_main_src.index("}", _main_src.index("IMG_MAP = {"))]
check(pa.IMG_FILES and set(pa.IMG_FILES) == set(_re.findall(r'"([a-z0-9-]+)":', _main_map)), "IMG_FILES (adapter) lệch IMG_MAP (main)")
for _id, _f in pa.IMG_FILES.items():
    _p = os.path.join(pa.IMG_DIR, _f)
    check(os.path.exists(_p) and os.path.getsize(_p) < 1_000_000, f"ảnh {_id} thiếu hoặc > 1MB")
check(set(_re.findall(r"\[IMG: ([a-z0-9-]+)\]", sp)) == set(pa.IMG_FILES), "mã ảnh trong prompt lệch IMG_FILES")
check("KHÔNG giới thiệu là khách hàng thật" in sp, "prompt thiếu cảnh báo ảnh quảng cáo ≠ review")

# 5d. không gọi khách là "mình" (chốt 23/09)
import re as _re2
_kbtxt = json.dumps(t.load_kb()["scripts_approved"], ensure_ascii=False) + json.dumps(t.load_kb()["pharmacy_policy"], ensure_ascii=False) + json.dumps(t.load_kb()["programs"], ensure_ascii=False)
check(not _re2.search(r"\b[Mm]ình\b", _kbtxt), "KB còn câu gọi khách là 'mình'")
_sp_clean = sp.replace('KHÔNG gọi khách là "mình"', "").replace('sai: "Mình cho em xin số điện thoại"', "")
check(not _re2.search(r"\b[Mm]ình\b", _sp_clean), "prompt/persona còn câu gọi khách là 'mình'")
_msgs = " ".join([pa.ATT_ACK, pa.PHONE_ACK, pa.PH_MSG] + list(pa.FU_MSG.values()) + list(pa.CMT_PUBLIC))
check("mình" not in _msgs.lower(), "tin nhắn Pancake còn 'mình'")
check("mình" not in engine.FALLBACK_TEXT.lower(), "FALLBACK_TEXT còn 'mình'")

# 6. engine demo mode trả lời Sâm
if not engine.API_KEY:
    r = engine.chat([{"role": "user", "content": "chào em"}])
    check("Sâm Thái Minh" in r["reply"], "demo reply")
print(f"PASS {ok} checks")
