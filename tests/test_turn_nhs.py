"""v0.5.18 (20/11, ca Nguyễn Xuân Ánh): 1 LƯỢT phản hồi (nhiều tin, nhiều dòng) — không trả lời 1 ý 2 lần.
(1) khách nhắn tin 2 lúc bot đang soạn lượt 1 mà lượt 1 đã đọc cả tin 2 → không chạy lượt 2;
(2) trong cùng lượt: mỗi ý 1 lần, dặn duy trì thuốc 1 lần cả hội thoại, 1 câu hỏi.
Chạy: python3 tests/test_turn_nhs.py (giả lập db / Pancake)."""
import os, sys, types, json, time
os.environ.update(PAGE_FOCUS_PRODUCT="hsmo_tui", PANCAKE_PAGE_ID="1", PANCAKE_TEST_ONLY="0", PANCAKE_ENABLED="1")
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, R); os.chdir(R)
for m in ("pii", "router", "db"):
    sys.modules[m] = types.ModuleType(m)
db = sys.modules["db"]; S = {}
db.get_setting = lambda k, d=None: S.get(k, d); db.set_setting = lambda k, v: S.__setitem__(k, v); db.log_webhook = lambda *a: None
db.pancake_is_test = lambda c: False
import pancake_adapter as pa
import engine
calls = []
A, B = "Thanh toán như thế nào để tôi đưa cho con?", "Tôi bị huyết áp cao có uống thuốc tây hàng ngày"


def fake_respond(conv_id, text, meta, images=None):
    calls.append(text)
    S["answered_ut:" + conv_id] = json.dumps({"t": time.time(), "ut": [pa._norm_ut(A), pa._norm_ut(B)]})
    return {"ok": True}


pa._respond = fake_respond
fails = 0
pa._batches["c1"] = {"texts": [A], "meta": {}, "t0": time.time() - 12}
pa._flush("c1")
pa._batches["c1"] = {"texts": [B], "meta": {}, "t0": time.time() - 1}
pa._flush("c1")
ok = calls == [A]; fails += not ok; print(("PASS " if ok else "FAIL ") + "tin 2 đã được lượt 1 đọc → không trả lời lượt 2")
time.sleep(0.01)
pa._batches["c1"] = {"texts": [A], "meta": {}, "t0": time.time()}
pa._flush("c1")
ok = calls[-1] == A and len(calls) == 2; fails += not ok; print(("PASS " if ok else "FAIL ") + "khách nhắn lại sau đó → vẫn trả lời")
prev = ["Anh vẫn nên duy trì thuốc theo chỉ định của bác sĩ và dùng Nước Hồng sâm cách thuốc khoảng 2 tiếng nhé ạ."]
ai = ("Về thanh toán, anh có 2 cách: nhận hàng kiểm tra rồi mới thanh toán, hoặc chuyển khoản trước qua tài khoản công ty ạ.\n\n"
      "Nước Hồng sâm hỗ trợ ổn định huyết áp ạ. Anh vẫn duy trì uống thuốc theo chỉ định của bác sĩ nhé.\n\n"
      "Anh cho em xin số điện thoại để bên em hỗ trợ giao hàng nhé ạ?\n\n"
      "Dạ người bị huyết áp cao vẫn dùng được Nước Hồng sâm, anh cứ duy trì thuốc tây bác sĩ kê ạ.\n\n"
      "Về phần thanh toán thì anh có thể nhận hàng kiểm tra rồi mới thanh toán, hoặc chuyển khoản trước ạ.\n\n"
      "Anh muốn lấy combo 2 hộp hay mấy hộp ạ?")
out, _n = engine._dedupe_reply(ai, prev)
ok = out.count("chuyển khoản") == 1 and "duy trì" not in out and out.count("?") == 1 and "số điện thoại" in out
fails += not ok; print(("PASS " if ok else "FAIL ") + "cùng lượt: mỗi ý 1 lần, 1 câu hỏi")
# (3) v0.5.18 (20/11, ca Đình Lân): tin SĐT kèm tên / chữ đệm → như tin trần SĐT (ghi nhận + Người xử lý + bot dừng); tin có câu hỏi / địa chỉ / đặt hàng → AI trả lời
ok = (pa._phone_lead_only("đinh lân đt 0798851374", "Đình Lân") == "0798851374" and pa._phone_lead_only("sđt chị 0912 345 678 gọi cho chị nhé") == "0912345678"
      and pa._phone_lead_only("0912345678 người tiểu đường dùng được không") == "" and pa._phone_lead_only("lấy 2 hộp 0912345678") == ""
      and pa.PHONE_STOP and "gọi lại" in pa.PHONE_ACK)
fails += not ok; print(("PASS " if ok else "FAIL ") + "khách thả SĐT kèm tên → ghi nhận, giao người")
out, k = engine._phone_ack_tail("Dạ người tiểu đường vẫn dùng được ạ.\n\nChị mua cho ai dùng ạ?", "0912345678 người tiểu đường dùng được không")
ok = k == 1 and "?" not in out and out.endswith(engine.PHONE_ACK_TAIL)
fails += not ok; print(("PASS " if ok else "FAIL ") + "SĐT kèm câu hỏi → trả lời + hẹn gọi lại, không hỏi thêm")
import tools_core
ok = "gọi điện xác nhận đơn" in tools_core.build_order([{"sku": "hsmo-tui", "qty": 2}], "Lân", "0798851374", "SN 5 ngõ 12 Cầu Giấy, Hà Nội")["confirm_text"]
fails += not ok; print(("PASS " if ok else "FAIL ") + "tổng hợp đơn kết bằng câu gọi xác nhận (không chờ khách xác nhận)")
print(f"\n{6 - fails}/6 ca đạt"); sys.exit(1 if fails else 0)
