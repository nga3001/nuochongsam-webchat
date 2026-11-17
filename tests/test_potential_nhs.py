"""v0.5.15 (17/11, chị Nga): thẻ "KH tiềm năng" — 5 dấu hiệu, khách chưa để SĐT, chưa chốt đơn; gắn 1 lần, bot vẫn chat.
Chạy: python3 tests/test_potential_nhs.py (không gọi Pancake thật — giả lập db / add_tag)."""
import os, sys, types
os.environ.update(PAGE_FOCUS_PRODUCT="hsmo_tui", PANCAKE_PAGE_ID="1", PANCAKE_TEST_ONLY="0", PANCAKE_ENABLED="1")
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, R); os.chdir(R)
for m in ("pii", "router", "db"):
    sys.modules[m] = types.ModuleType(m)
db = sys.modules["db"]; S = {}
db.get_setting = lambda k, d=None: S.get(k, d); db.set_setting = lambda k, v: S.__setitem__(k, v); db.log_webhook = lambda *a: None
db.pancake_is_test = lambda c: False
import pancake_adapter as pa
calls = []
pa.add_tag = lambda c, t: calls.append((c, t)); pa.is_enabled = lambda: True; pa.is_killed = lambda: False; pa.is_test_only = lambda: False
H = lambda *x: [{"role": r, "content": c} for r, c in x]
Q = "Dạ Nước Hồng sâm Thái Minh mật ong giá 620.000đ/hộp 20 túi ạ."
CASES = [  # (tên, lịch sử, tin khách, có gắn thẻ?)
    ("lưỡng lự", H(("user", "giá sao"), ("assistant", Q), ("user", "để chị hỏi ý kiến chồng đã")), "để chị hỏi ý kiến chồng đã", True),
    ("lương về", H(("user", "giá sao"), ("assistant", Q), ("user", "cuối tháng lương về chị lấy")), "cuối tháng lương về chị lấy", True),
    ("hỏi sâu sau báo giá", H(("user", "giá sao"), ("assistant", Q), ("user", "combo 2 hộp tặng gì em")), "combo 2 hộp tặng gì em", True),
    ("hỏi ship khi chưa báo giá", H(("user", "ship mấy ngày")), "ship mấy ngày", False),
    ("chê đắt vẫn hỏi", H(("user", "giá"), ("assistant", Q), ("user", "đắt quá"), ("assistant", "Dạ em hiểu ạ"), ("user", "có bớt không em")), "có bớt không em", True),
    ("chê đắt rồi từ chối", H(("user", "đắt quá"), ("assistant", "Dạ"), ("user", "thôi không mua đâu")), "thôi không mua đâu", False),
    ("đã có SĐT", H(("user", "giá"), ("assistant", Q), ("user", "0912345678 để sau nhé")), "0912345678 để sau nhé", False),
]
fails = 0
for name, h, t, want in CASES:
    calls.clear(); S.clear()
    pa._potential_check("c1", h, t)
    ok = bool(calls) == want and all(x[1] == "KH tiềm năng" for x in calls)
    fails += not ok; print(("PASS " if ok else "FAIL ") + name)
calls.clear(); S.clear()
for t in ["chào em", "sâm này của ai", "uống có ngọt không"]:
    pa._potential_check("c2", H(("user", t)), t)
ok = calls == [("c2", "KH tiềm năng")]; fails += not ok; print(("PASS " if ok else "FAIL ") + "3 lượt trong ngày")
calls.clear(); S.clear()
db.pancake_local_conv = lambda c, customer=None: c
db.get_history = lambda c: H(("user", "giá"), ("assistant", Q), ("user", "lấy 2 hộp"), ("assistant", "Dạ anh/chị cho em xin số điện thoại và địa chỉ nhận hàng ạ."))
pa._potential_silent_after_ask("c3")
pa._potential_check("c3", H(("user", "để sau")), "để sau")   # đã gắn → không gắn lại
ok = calls == [("c3", "KH tiềm năng")]; fails += not ok; print(("PASS " if ok else "FAIL ") + "muốn mua nhưng im sau lời xin số (1 lần)")
S["order_done:c4"] = "1"; calls.clear()
pa._potential_check("c4", H(("user", "để sau")), "để sau")
ok = calls == []; fails += not ok; print(("PASS " if ok else "FAIL ") + "đơn đã chốt → không gắn")
n = len(CASES) + 3
print(f"\n{n - fails}/{n} ca đạt"); sys.exit(1 if fails else 0)
