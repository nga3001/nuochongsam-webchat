"""Web chat test nội bộ — Agent Sâm Thái Minh (giao diện Messenger).
v0.4 (21/08/2026): cập nhật theo Kịch bản bổ sung + 6 quyết định duyệt sau vòng test 1 —
bảng KM 3 combo khách mới, quy tắc kênh nhà thuốc, cấm chia giá, Rule 6-9 chuyển nhân viên
(cờ 📞 trên admin + sheet Excel), bot gửi ảnh sản phẩm/đánh giá ([IMG: id] → /img/{secret}/{id}).

Chạy local:  uvicorn main:app --reload --port 8000
Deploy:      Railway/Render — xem README-huong-dan.md

ENV:
  ANTHROPIC_API_KEY  bắt buộc khi chạy thật (thiếu → DEMO MODE)
  SECRET_PATH        đoạn link ẩn của trang chat  (mặc định: test-samthaiminh-2026)
  ADMIN_KEY          đoạn link ẩn của trang admin (mặc định: admin-thaiminh-2026)
  DEFAULT_MODEL      sonnet | haiku
  WATCH_KEY          (tuỳ chọn) khoá THEO DÕI cho nhân viên: /w/{key} chỉ mở trang báo cáo
                     A/B + nút dừng khẩn + tải Excel. Bỏ trống → tự sinh, lưu trong DB.
"""
import io
import json
import os

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse

import db
import engine
import tools_core

SECRET_PATH = os.environ.get("SECRET_PATH", "test-samthaiminh-2026")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "admin-thaiminh-2026")
APP_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
db.init()


@app.on_event("startup")
def _startup_pancake():
    import pancake_adapter
    pancake_adapter.start_background()   # SLA watcher + polling dự phòng (hướng B)


@app.on_event("shutdown")
def _shutdown_flush():
    """v0.5.29: không bỏ rơi tin khách đang gom khi redeploy (sự cố khe deploy 29/08)."""
    import pancake_adapter
    pancake_adapter.flush_all_batches()


def _page(name: str) -> str:
    with open(os.path.join(APP_DIR, "static", name), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
def root():
    return "<html><body style='font-family:sans-serif;padding:40px'><h3>Không có gì ở đây.</h3></body></html>"


@app.get("/healthz")
def healthz():
    return {"ok": True, "demo_mode": not any(p.ready() for p in engine._REGISTRY.values())}


@app.get("/api/models")
def api_models(secret: str = ""):
    """Danh sách model đã cấu hình đủ key — để UI test nội bộ hiện đúng lựa chọn."""
    if secret not in (SECRET_PATH, ADMIN_KEY):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    import providers
    avail = providers.available(engine._REGISTRY)  # {key: label}
    return {"available": avail,
            "has_external": any(k in avail for k in ("gpt", "deepseek")),
            "pii_mask_external": engine.PII_MASK_EXTERNAL}


# ------------------------------------------------- webhook Pancake (hướng B)
WEBHOOK_PATH = os.environ.get("PANCAKE_WEBHOOK_PATH", "pancake-wh-samthaiminh")


@app.get("/webhook/{wh}")
def webhook_verify(wh: str):
    # Pancake có thể GET để verify endpoint sống
    if wh != WEBHOOK_PATH:
        return JSONResponse({"error": "not found"}, status_code=404)
    return {"ok": True}


@app.post("/webhook/{wh}")
async def webhook_pancake(wh: str, req: Request):
    """Nhận sự kiện Pancake. Trả 200 NGAY (<5s, tránh Pancake treo webhook),
    xử lý ở luồng nền. Nấc B0: PANCAKE_ENABLED=0 → chỉ nghe/log, không gửi gì."""
    if wh != WEBHOOK_PATH:
        return JSONResponse({"error": "not found"}, status_code=404)
    try:
        payload = await req.json()
    except Exception:  # noqa: BLE001
        return {"ok": True}
    import pancake_adapter
    # xử lý bất đồng bộ để trả 200 ngay
    import threading
    threading.Thread(target=_wh_worker, args=(payload,), daemon=True).start()
    return {"ok": True}


def _wh_worker(payload):
    import pancake_adapter
    try:
        # v0.5.6: route_event = hub phân luồng — page mình thì xử lý,
        # page khác trong PANCAKE_FORWARD_MAP thì chuyển tiếp nguyên vẹn (VD: Vương Bảo → n8n)
        res = pancake_adapter.route_event(payload)
        if not (isinstance(res, dict) and res.get("hub")):
            # sự kiện hub (chuyển tiếp / page lạ) đã tự ghi log bên trong route_event
            db.log_webhook(payload.get("event_type", ""), json.dumps(res, ensure_ascii=False))
    except Exception as ex:  # noqa: BLE001
        db.log_webhook("error", str(ex))


# ------------------------------------------------------------------- chat UI
@app.get("/c/{secret}", response_class=HTMLResponse)
def chat_page(secret: str):
    if secret != SECRET_PATH:
        return HTMLResponse("Not found", status_code=404)
    return _page("index.html")


# Ảnh sản phẩm / đánh giá — bot chèn [IMG: id], frontend gọi route này
IMG_DIR = os.path.join(APP_DIR, "static", "img")
IMG_MAP = {
    # Sâm Thái Minh — ảnh nhãn hàng cấp 23/09/2026 (giữ đồng bộ với pancake_adapter.IMG_FILES)
    "hong-sam-lat": "hong-sam-lat.jpg",
    "hong-sam-lat-mieng": "hong-sam-lat-mieng.jpg",
    "hong-sam-lat-ong-ba": "hong-sam-lat-ong-ba.jpg",
    "hong-sam-lat-bieu": "hong-sam-lat-bieu.jpg",
    "hong-sam-chai": "hong-sam-chai.jpg",
    "hong-sam-tui": "hong-sam-tui.jpg",
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
}


@app.get("/img/{secret}/{img_id}")
def img_serve(secret: str, img_id: str):
    if secret not in (SECRET_PATH, ADMIN_KEY) or img_id not in IMG_MAP:
        return HTMLResponse("Not found", status_code=404)
    path = os.path.join(IMG_DIR, IMG_MAP[img_id])
    if not os.path.isfile(path):
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(path, media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.post("/api/chat")
async def api_chat(req: Request):
    body = await req.json()
    if body.get("secret") != SECRET_PATH:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    tester = (body.get("tester") or "khách test").strip()[:60]
    model_key = body.get("model") if body.get("model") in ("sonnet", "haiku", "gpt", "deepseek", "gemini", "gemini_lite", "auto") else None
    text = (body.get("message") or "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)

    conv_id = body.get("conv_id")
    if not conv_id:
        conv_id = db.new_conversation(tester, model_key or engine.DEFAULT_MODEL_KEY)

    db.add_message(conv_id, "user", text)
    history = db.get_history(conv_id)
    result = engine.chat(history, model_key)

    if "error" in result:
        db.add_message(conv_id, "system", f"ERROR: {result['error']}")
        return JSONResponse({"conv_id": conv_id, "error": result["error"]}, status_code=502)

    is_fallback = bool(result.get("is_fallback"))
    mid = db.add_message(conv_id, "assistant", result["reply"],
                         latency_ms=result["latency_ms"], model=result["model"],
                         tool_trace=json.dumps(result["tool_trace"], ensure_ascii=False),
                         is_fallback=is_fallback)
    # Cờ chuyển nhân viên (Rule 7-9 + escalation 4 level): bot chèn [HANDOFF: lý do | SĐT | level]
    for h in result.get("handoffs") or []:
        db.add_handoff(conv_id, tester, h.get("reason", ""), h.get("phone", ""), h.get("level", 2))
    # Chống vòng lặp: 2 tin dự phòng liên tiếp = hội thoại đang hỏng → tự bật cờ để người vào ngay
    if is_fallback and db.recent_fallback_streak(conv_id) >= 2:
        db.add_handoff(conv_id, tester, "HỘI THOẠI LỖI - bot trả rỗng liên tiếp, cần người kiểm tra", "", 4)
    # v0.5.28: trả thêm handoffs + pharmacy để bộ 10 ca guardrail chấm được bằng máy
    return {"conv_id": conv_id, "message_id": mid, "reply": result["reply"],
            "parts": result.get("parts") or [result["reply"]],
            "handoffs": result.get("handoffs") or [], "pharmacy": bool(result.get("pharmacy")),
            "latency_ms": result["latency_ms"], "model": result["model"]}


@app.post("/api/feedback")
async def api_feedback(req: Request):
    body = await req.json()
    if body.get("secret") != SECRET_PATH:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    rating = body.get("rating")
    if rating not in ("up", "down", "clear"):
        return JSONResponse({"error": "bad rating"}, status_code=400)
    db.set_feedback(body.get("message_id"), body.get("conv_id"), rating, (body.get("note") or "")[:1000])
    return {"ok": True}


@app.post("/api/suggest")
async def api_suggest(req: Request):
    """Góp ý huấn luyện chatbot — lưu lại cho admin duyệt, KHÔNG tự động thay đổi bot."""
    body = await req.json()
    if body.get("secret") != SECRET_PATH:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    tester = (body.get("tester") or "").strip()[:60]
    content = (body.get("content") or "").strip()[:1500]
    if not tester:
        return JSONResponse({"error": "Cần nhập tên người test trước khi góp ý"}, status_code=400)
    if len(content) < 5:
        return JSONResponse({"error": "Góp ý quá ngắn"}, status_code=400)
    # Chống spam: tối đa 10 góp ý / người / 10 phút
    if db.recent_suggestion_count(tester, 600) >= 10:
        return JSONResponse({"error": "Bạn gửi góp ý hơi nhanh — chờ vài phút rồi gửi tiếp nhé"}, status_code=429)
    sid = db.add_suggestion(body.get("conv_id"), tester, content)
    return {"ok": True, "id": sid}


# ------------------------------------------------------------------ admin UI
@app.get("/a/{key}", response_class=HTMLResponse)
def admin_page(key: str):
    if key != ADMIN_KEY:
        return HTMLResponse("Not found", status_code=404)
    return _page("admin.html")


def _admin_ok(req_key: str) -> bool:
    return req_key == ADMIN_KEY


# ---------------- v0.5.16: KHOÁ THEO DÕI (watch key) — link gửi nhân viên trực
# Khoá này CHỈ mở: trang báo cáo A/B (/w/{key}), tải Excel A/B, và DUY NHẤT một công tắc
# là kill (dừng khẩn / bật lại bot). KHÔNG vào được trang admin, không sửa van nào khác.
def _watch_key() -> str:
    """ENV WATCH_KEY > setting watch_key > tự sinh một lần rồi lưu DB (khỏi phải đặt ENV)."""
    k = (os.environ.get("WATCH_KEY") or "").strip() or db.get_setting("watch_key")
    if not k:
        import secrets
        k = "watch-tm-" + secrets.token_urlsafe(12)
        db.set_setting("watch_key", k)
    return k


def _watch_ok(req_key: str) -> bool:
    return bool(req_key) and (_admin_ok(req_key) or req_key == _watch_key())


@app.get("/api/admin/stats")
def admin_stats(key: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    s = db.stats()
    s["demo_mode"] = not any(p.ready() for p in engine._REGISTRY.values())
    s["kb_status"] = tools_core.load_kb()["_meta"].get("status", "")
    return s


@app.get("/api/admin/conversations")
def admin_convs(key: str = "", tester: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return db.list_conversations(tester or None)


@app.get("/api/admin/messages")
def admin_msgs(key: str = "", conv_id: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return db.get_messages(conv_id)


@app.get("/api/admin/suggestions")
def admin_suggestions(key: str = "", conv_id: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return db.list_suggestions(conv_id or None)


@app.get("/api/admin/handoffs")
def admin_handoffs(key: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return db.list_handoffs()


@app.post("/api/admin/handoff_done")
async def admin_handoff_done(req: Request):
    body = await req.json()
    if not _admin_ok(body.get("key", "")):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    db.set_handoff_status(body.get("id", ""), "done" if body.get("done", True) else "open")
    return {"ok": True}


@app.get("/api/admin/export.xlsx")
def admin_export(key: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    from openpyxl import Workbook
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=7))
    wb = Workbook()
    ws = wb.active
    ws.title = "Log hội thoại"
    ws.append(["Người test", "Mã hội thoại", "Vai", "Nội dung", "Thời gian",
               "Độ trễ (ms)", "Model", "Chấm", "Ghi chú lỗi"])
    for r in db.export_rows():
        ws.append([r["tester"], r["conv_id"], r["role"], r["content"],
                   datetime.fromtimestamp(r["ts"], tz).strftime("%d/%m/%Y %H:%M:%S"),
                   r["latency_ms"], r["model"],
                   {"up": "tốt", "down": "lỗi"}.get(r["rating"], ""), r["note"] or ""])
    for col, w in zip("ABCDEFGHI", [18, 14, 10, 80, 20, 12, 22, 8, 40]):
        ws.column_dimensions[col].width = w
    ws2 = wb.create_sheet("Góp ý huấn luyện")
    ws2.append(["Người test", "Mã hội thoại", "Nội dung góp ý", "Thời gian"])
    for s in db.list_suggestions():
        ws2.append([s["tester"], s["conv_id"] or "", s["content"],
                    datetime.fromtimestamp(s["ts"], tz).strftime("%d/%m/%Y %H:%M:%S")])
    for col, w in zip("ABCD", [18, 14, 90, 20]):
        ws2.column_dimensions[col].width = w
    ws3 = wb.create_sheet("Chuyển nhân viên")
    ws3.append(["Người test", "Mã hội thoại", "Level", "Lý do", "SĐT khách", "Thời gian", "Trạng thái"])
    _lvl = {1: "1 - Bot chốt đơn", 2: "2 - CSKH (15p)", 3: "3 - Dược sĩ (10p)", 4: "4 - RED FLAG (3p)"}
    for h in db.list_handoffs():
        ws3.append([h["tester"], h["conv_id"] or "", _lvl.get(h.get("level", 2), h.get("level", 2)),
                    h["reason"], h["phone"] or "",
                    datetime.fromtimestamp(h["ts"], tz).strftime("%d/%m/%Y %H:%M:%S"),
                    "đã xử lý" if h["status"] == "done" else "CHỜ XỬ LÝ"])
    for col, w in zip("ABCDEFG", [18, 14, 16, 45, 16, 20, 14]):
        ws3.column_dimensions[col].width = w
    ws4 = wb.create_sheet("Lead SĐT")
    ws4.append(["Mã hội thoại", "Nguồn", "SĐT", "Ngữ cảnh", "Thời gian"])
    for l in db.list_leads():
        ws4.append([l["conv_id"] or "", l["source"], l["phone"], l["context"],
                    datetime.fromtimestamp(l["ts"], tz).strftime("%d/%m/%Y %H:%M:%S")])
    for col, w in zip("ABCDE", [14, 12, 16, 60, 20]):
        ws4.column_dimensions[col].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=log-test-samthaiminh.xlsx"})


# ---------------------------------------------- admin: buồng lái Pancake (hướng B)
@app.get("/api/admin/logs")
def admin_logs(key: str = "", hours: float = 48, event: str = "", q: str = "", limit: int = 2000):
    """v0.5.22b (A4): đọc webhook_log theo khoảng giờ / loại / từ khoá — để rà lỗi 2 ngày và
    phân 3 loại (lỗi thật / no-op / do phía khách) mà không phải mở DB tay. Chỉ admin key."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    import time as _t
    since = _t.time() - max(0.5, min(hours, 24 * 14)) * 3600
    sql = "SELECT ts, event_type, result FROM webhook_log WHERE ts>=?"
    args = [since]
    if event:
        evs = [e.strip() for e in event.split(",") if e.strip()]
        sql += " AND event_type IN (%s)" % ",".join("?" * len(evs))
        args += evs
    if q:
        sql += " AND result LIKE ?"
        args.append("%" + q + "%")
    sql += " ORDER BY ts DESC LIMIT ?"
    args.append(int(max(1, min(limit, 5000))))
    with db._conn() as c:
        rows = [dict(r) for r in c.execute(sql, args).fetchall()]
    counts = {}
    for r in rows:
        counts[r["event_type"]] = counts.get(r["event_type"], 0) + 1
        r["luc"] = _fmt_ts(r["ts"], "%d/%m %H:%M:%S")
    return {"since": _fmt_ts(since), "n": len(rows),
            "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])), "rows": rows}


@app.get("/api/admin/pancake")
def admin_pancake(key: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    import pancake_adapter
    s = pancake_adapter.status()
    s["webhook_url"] = f"/webhook/{WEBHOOK_PATH}"
    s["webhook_log"] = db.webhook_recent(30)
    s["conversations"] = db.pancake_overview(50)
    return s


@app.post("/api/admin/pancake_toggle")
async def admin_pancake_toggle(req: Request):
    """Công tắc lúc chạy — không cần redeploy: kill (tắt khẩn <1 phút), enabled (gửi thật), poll."""
    body = await req.json()
    _key = body.get("key", "")
    field = body.get("field")
    if not _admin_ok(_key):
        # khoá theo dõi: CHỈ được bấm kill switch, không chạm van nào khác
        if not (_watch_ok(_key) and field == "kill"):
            return JSONResponse({"error": "forbidden"}, status_code=403)
    if field not in ("kill", "enabled", "poll", "test_only", "ab_percent", "followup",
                     "comment", "comment_test", "vision"):
        return JSONResponse({"error": "field phải là kill | enabled | poll | test_only | "
                                      "ab_percent | followup | comment | comment_test | vision"},
                            status_code=400)
    if field == "ab_percent":
        try:
            pct = max(0, min(100, int(float(body.get("value")))))
        except Exception:  # noqa: BLE001
            return JSONResponse({"error": "ab_percent phải là số 0-100"}, status_code=400)
        db.set_setting("pancake_ab_percent", str(pct))
        db.log_webhook("toggle", f"ab_percent={pct} (admin)")
    else:
        db.set_setting(f"pancake_{field}", "1" if body.get("value") else "0")
        _who = (str(body.get("by") or "").strip()[:40]
                or ("admin" if _admin_ok(_key) else "khoá theo dõi"))
        db.log_webhook("toggle", f"{field}={'1' if body.get('value') else '0'} (bởi {_who})")
        # v0.5.15: ghi MỐC BẬT nhịp theo đuổi để trang báo cáo A/B đọc số cho đúng — chỉ nhóm
        # BOT có nhịp nhắc, nhóm người trực không có (anh Na chốt 26/08: bật ngay + ghi rõ).
        if field == "followup" and body.get("value") and not db.get_setting("fu_start_ts"):
            db.set_setting("fu_start_ts", str(__import__("time").time()))
    import pancake_adapter
    return {"ok": True, "status": pancake_adapter.status()}


@app.post("/api/admin/pancake_release")
async def admin_pancake_release(req: Request):
    """Thả một hội thoại về tay bot (gỡ human_claimed/returned bị nhận nhầm)."""
    body = await req.json()
    if not _admin_ok(body.get("key", "")):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    cid = (body.get("conv_id") or "").strip()
    if not cid:
        return JSONResponse({"error": "cần conv_id (id hội thoại Pancake)"}, status_code=400)
    db.pancake_release(cid)
    db.log_webhook("release", f"admin thả {cid} về tay bot")
    return {"ok": True, "conv_id": cid}


@app.get("/api/admin/leads")
def admin_leads(key: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return db.list_leads()


@app.get("/api/admin/pancake_report")
def admin_pancake_report(key: str = "", days: int = 7):
    """Báo cáo nhanh cuối ngày nấc B1: hội thoại, tin bot, đầu ra theo level, lead, SLA quá hạn."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return db.pancake_daily_report(days)


@app.get("/api/admin/pancake_probe")
def admin_pancake_probe(key: str = "", cid: str = "", text: str = "probe",
                        variant: str = "2", raw_body: str = "", path: str = "",
                        method: str = "POST", qs: str = "", base: str = ""):
    """Chẩn đoán API Pancake từ server (server có token, container Chi bị chặn pages.fm).
    Trả nguyên văn phản hồi để dò đúng format gửi tin."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if not cid and not path:
        return JSONResponse({"error": "cần cid hoặc path"}, status_code=400)
    import pancake_adapter
    return pancake_adapter.probe(cid, text, variant, raw_body, path, method, qs, base)


# ------- v0.5.16: bảng DỪNG BOT KHẨN CẤP nhúng vào trang báo cáo A/B (2 bước + ghi tên)
KILL_PANEL = """
<h2>🛑 Dừng bot khẩn cấp</h2>
<div class="kbox" id="kbox">
  <div id="kstate" class="kstate">…</div>
  <div class="krow">
    <input id="kby" placeholder="Tên bạn (ghi vào log)" maxlength="40">
    <button id="kbtn" class="kbtn">…</button>
  </div>
  <div id="kmsg" class="kmsg"></div>
  __ENVNOTE__
  <p class="khelp"><b>Dừng bot</b> = bot NGỪNG nhắn tin cho khách ngay (có hiệu lực dưới 1
  phút, không cần deploy lại). Khách nhắn vào sẽ KHÔNG được trả lời tự động nữa — bấm xong
  phải vào Pancake trực tay và báo ngay anh Na + nhóm trực. Nút này không ảnh hưởng luồng
  chuyển tiếp sang page khác (Vương Bảo).</p>
</div>
<script>
var KKEY = "__KEY__", killed = __KILLED__, armed = false, tmr = null;
function el(i){ return document.getElementById(i); }
function draw(){
  var st = el('kstate'), b = el('kbtn');
  if (killed){
    st.className = 'kstate off';
    st.innerHTML = '🛑 <b>BOT ĐANG DỪNG</b> — bot không nhắn tin cho khách.';
    b.className = 'kbtn on';
    b.textContent = armed ? '⚠ Bấm lần nữa để BẬT LẠI bot' : '▶ Bật lại bot';
  } else {
    st.className = 'kstate ok';
    st.innerHTML = '✅ <b>Bot đang chạy</b> bình thường.';
    b.className = 'kbtn off';
    b.textContent = armed ? '⚠ Bấm lần nữa để XÁC NHẬN DỪNG' : '🛑 DỪNG BOT KHẨN CẤP';
  }
  b.disabled = false;
}
function arm(){
  if (!armed){
    armed = true; draw();
    el('kmsg').textContent = 'Chờ xác nhận… (tự huỷ sau 5 giây)';
    tmr = setTimeout(function(){ armed = false; draw();
      el('kmsg').textContent = 'Đã huỷ — chưa thay đổi gì.'; }, 5000);
    return;
  }
  clearTimeout(tmr); armed = false;
  el('kbtn').disabled = true;
  el('kmsg').textContent = 'Đang gửi lệnh…';
  fetch('/api/admin/pancake_toggle', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({key: KKEY, field: 'kill', value: !killed, by: el('kby').value})})
   .then(function(r){ return r.json(); })
   .then(function(j){
      if (j.error){ el('kmsg').textContent = '❌ Lỗi: ' + j.error; draw(); return; }
      killed = !!(j.status && j.status.kill); draw();
      el('kmsg').textContent = (killed ? '🛑 ĐÃ DỪNG BOT lúc ' : '▶ ĐÃ BẬT LẠI BOT lúc ')
        + new Date().toLocaleTimeString('vi-VN') + ' — nhớ báo anh Na + nhóm trực.';
   })
   .catch(function(e){
      el('kmsg').textContent = '❌ Không gửi được lệnh (mất mạng?) — thử lại.'; draw(); });
}
el('kbtn').onclick = arm;
// v0.5.18: bảng tình trạng làm mới mỗi 30s → đồng bộ luôn trạng thái nút (trừ lúc đang chờ
// xác nhận, để không nuốt cú bấm thứ hai của nhân viên).
window.ksync = function(k){ if (!armed && k !== killed){ killed = k; draw(); } };
draw();
</script>
"""


# ------------------------- v0.5.14: A/B theo MỐC ĐO + trang báo cáo đầy đủ + Excel
AB_START_DEFAULT = 1787716403.0   # = 10:53:23 26/08/2026 (+07) — v0.5.13 live: mọi van đo đã vá.
# Số liệu TRƯỚC mốc bị nhiễu (chế độ thử chỉ-nghe + auto-greeting của ad bị tính nhầm là sale)
# nên KHÔNG tính vào báo cáo — dữ liệu vẫn nằm nguyên trong DB để tra cứu. Anh Na chốt 26/08.


def _ab_start() -> float:
    """Mốc bắt đầu đo: setting ab_start_ts (sửa trong DB nếu cần) đè lên mặc định."""
    try:
        return float(db.get_setting("ab_start_ts") or AB_START_DEFAULT)
    except (TypeError, ValueError):
        return AB_START_DEFAULT


def _ab_rows():
    """ab_stats từ mốc đo, kèm is_test/state (đoán lý do ca lai tạp). Dùng db._conn trực tiếp,
    KHÔNG thêm hàm vào db.py (ghi chú v0.5.12: đẩy db.py lên GitHub hay bị chặn)."""
    with db._conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT a.*, m.is_test AS is_test, m.state AS state FROM ab_stats a"
            " LEFT JOIN pancake_map m ON m.pancake_conv_id=a.pancake_conv_id"
            " WHERE a.first_in_ts>=? ORDER BY a.first_in_ts", (_ab_start(),)).fetchall()]


def _ab_phone_map() -> dict:
    """v0.5.21: SĐT THẬT theo hội thoại (bảng ab_phones — ghi cho CẢ HAI nhóm A/B).
    Đọc bằng db._conn, KHÔNG thêm hàm vào db.py."""
    out = {}
    try:
        with db._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS ab_phones("
                      "pancake_conv_id TEXT, phone TEXT, grp TEXT, src TEXT, ts REAL,"
                      " PRIMARY KEY(pancake_conv_id, phone))")
            for r in c.execute("SELECT pancake_conv_id, phone FROM ab_phones ORDER BY ts"):
                out.setdefault(r[0], []).append(r[1])
    except Exception:  # noqa: BLE001
        pass
    return out


def _ab_unreach_set() -> set:
    """v0.5.22 A3: các ca FB #551 (không gửi được cho khách) — đếm thành cột riêng."""
    try:
        with db._conn() as c:
            return {r[0][len("ab_unreach:"):] for r in
                    c.execute("SELECT key FROM settings WHERE key LIKE 'ab_unreach:%'")}
    except Exception:  # noqa: BLE001
        return set()


def _sample_needed(p1, p2, power=0.84, z=1.96) -> int:
    """v0.5.23: cần bao nhiêu hội thoại MỖI NHÓM để kết luận chắc chắn ở mức chênh lệch đang
    thấy (kiểm định 2 tỷ lệ, tin cậy 95%, độ mạnh 80%). Chênh càng nhỏ, mẫu cần càng lớn."""
    import math
    d = abs(p1 - p2)
    if d < 1e-9:
        return -1
    pb = (p1 + p2) / 2.0
    try:
        n = (z * math.sqrt(2 * pb * (1 - pb))
             + power * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (d * d)
    except (ValueError, ZeroDivisionError):
        return -1
    return int(math.ceil(n))


def _ab_order_map() -> dict:
    """v0.5.23 (D2): đơn hàng GẮN TRONG HỘI THOẠI Pancake, theo conv_id. Nối theo hội thoại
    (không ghép qua SĐT) để khách cũ từng mua không bị tính nhầm thành công của bot.
    Bảng ab_orders do pancake_adapter tạo — KHÔNG sửa db.py."""
    out = {}
    try:
        with db._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS ab_orders("
                      "pancake_conv_id TEXT, order_id TEXT, status TEXT, status_name TEXT,"
                      " total REAL, phone TEXT, inserted_at TEXT, ts REAL,"
                      " PRIMARY KEY(pancake_conv_id, order_id))")
            for r in c.execute("SELECT pancake_conv_id, order_id, status, status_name, total,"
                               " inserted_at FROM ab_orders"):
                out.setdefault(r[0], []).append(
                    {"id": r[1], "status": r[2], "status_name": r[3], "total": r[4],
                     "inserted_at": r[5]})
    except Exception:  # noqa: BLE001
        pass
    return out


# v0.5.24 (D2) — TRẠNG THÁI ĐƠN, kiểm chứng bằng 600 đơn thật của shop (16/05→28/08):
# chỉ tồn tại status 0 và 1, và MỌI đơn đều 0đ / 0 sản phẩm ⇒ đội CSKH dùng chức năng "tạo đơn"
# của Pancake như một cái ĐÁNH DẤU, còn đơn + tiền thật nằm ở hệ thống khác của công ty.
# Vì vậy chỉ đo được "ca có đơn" chứ KHÔNG đo được doanh thu — và mốc chốt thật là status 1.
ORDER_CANCELLED = {"-1", "4", "5", "6", "7"}
ORDER_CONFIRMED = {"1", "2", "3", "11", "17", "20"}


def _order_alive(o) -> bool:
    st = str(o.get("status") or "")
    nm = (o.get("status_name") or "").lower()
    return not (st in ORDER_CANCELLED or any(k in nm for k in ("huỷ", "hủy", "cancel", "xoá", "xóa")))


def _order_confirmed(o) -> bool:
    """Đơn đã được nhân viên XÁC NHẬN — mốc 'chốt' theo cách đội đang dùng Pancake."""
    st = str(o.get("status") or "")
    nm = (o.get("status_name") or "").lower()
    if not _order_alive(o):
        return False
    return st in ORDER_CONFIRMED or "xác nhận" in nm or "xac nhan" in nm


def _ab_summary(rows) -> dict:
    out = {}
    unreach = _ab_unreach_set()
    omap = _ab_order_map()
    for grp in ("bot", "human"):
        g = [r for r in rows if r["grp"] == grp]
        clean = [r for r in g if not r["contaminated"]]
        with_order = [r for r in clean
                      if any(_order_alive(o) for o in omap.get(r["pancake_conv_id"], []))]
        with_conf = [r for r in clean
                     if any(_order_confirmed(o) for o in omap.get(r["pancake_conv_id"], []))]
        n_orders = sum(1 for r in clean for o in omap.get(r["pancake_conv_id"], [])
                       if _order_alive(o))
        n_conf = sum(1 for r in clean for o in omap.get(r["pancake_conv_id"], [])
                     if _order_confirmed(o))
        replied = [r for r in clean if r["first_reply_ts"]]
        waits = sorted(r["first_reply_ts"] - r["first_in_ts"] for r in replied)
        med = waits[len(waits) // 2] if waits else None
        out[grp] = {
            "conversations": len(clean), "contaminated_excluded": len(g) - len(clean),
            "replied": len(replied),
            "replied_pct": round(100.0 * len(replied) / len(clean), 1) if clean else None,
            "median_first_reply_sec": round(med, 1) if med is not None else None,
            "phone_pct": round(100.0 * sum(r["phone"] for r in clean) / len(clean), 1) if clean else None,
            "phone_n": sum(r["phone"] for r in clean),
            "unreachable": sum(1 for r in g if r["pancake_conv_id"] in unreach),
            # v0.5.23 (D2): đơn nối theo hội thoại. "conv_with_order" = số ca CÓ đơn còn sống
            # (đơn huỷ không tính); "orders" = tổng số đơn (1 ca có thể 2 đơn).
            "orders": n_orders, "conv_with_order": len(with_order),
            "orders_confirmed": n_conf, "conv_with_confirmed": len(with_conf),
            # "chốt đơn" = ca có đơn ĐÃ XÁC NHẬN (đơn mới/nháp chưa tính là chốt)
            "order_pct": round(100.0 * len(with_conf) / len(clean), 1) if clean else None,
            "orders_synced": bool(omap),
        }
    return out


def _tz7():
    from datetime import timezone, timedelta
    return timezone(timedelta(hours=7))


def _fmt_ts(ts, fmt="%d/%m/%Y %H:%M"):
    from datetime import datetime
    return datetime.fromtimestamp(ts, _tz7()).strftime(fmt)


def _dur(sec) -> str:
    if sec is None:
        return "—"
    if sec < 120:
        return f"{sec:.0f} giây"
    if sec < 7200:
        return f"{sec / 60:.1f} phút"
    return f"{sec / 3600:.1f} giờ"


def _ab_reason(r) -> str:
    who = db.get_setting("ab_flag:" + str(r.get("pancake_conv_id") or ""))
    if who:
        return f"loại tay (bởi {who})"
    if db.get_setting("ab_unreach:" + str(r.get("pancake_conv_id") or "")):
        return "không gửi được cho khách (FB #551 — chặn page / xoá hội thoại / hết cửa sổ)"
    att = db.get_setting("ab_att:" + str(r.get("pancake_conv_id") or ""))
    if att:
        return f"khách gửi {att} — bot chuyển người, không tính vào A/B"
    if r.get("is_test"):
        return "hội thoại thử #tm"
    st = r.get("state") or ""
    if st == "human_claimed":
        return "người tiếp quản (gõ tay hoặc gắn thẻ 'Để NV xử lý')"
    if st == "returned":
        return "bot đã chuyển nhân viên"
    return "khác"


# ---- v0.5.18: BẢNG TÌNH TRẠNG BOT — cho nhân viên trực nhìn là biết bot sống hay lỗi
HEALTH_ERR = ("error", "send_fail", "api_fail", "forward_err", "cmt_fail")
HEALTH_HIDE = ("forward_ok", "forward_none", "poll_baseline", "payload_keys")


def _h_msg(res: str) -> str:
    """Rút câu lỗi dễ đọc từ phản hồi API (bỏ id hội thoại + JSON thô)."""
    import re
    for pat in (r'"message"\s*:\s*"([^"]{3,160})"', r'"error"\s*:\s*"([^"]{3,160})"'):
        m = re.search(pat, res)
        if m:
            t = m.group(1)
            if "outside of allowed window" in t:
                return "quá cửa sổ 24 giờ của Meta — không nhắn ra được nữa (khách phải nhắn lại)"
            if "token" in t.lower():
                return t + " (token page có thể đã hết hạn — báo anh Na)"
            return t
    return res.split(": ", 1)[-1][:110]


def _h_desc(ev: str, res: str):
    """Dịch 1 dòng log máy sang tiếng Việt cho nhân viên đọc. Trả (icon, chữ, loại màu)."""
    j = {}
    if res.startswith("{"):
        try:
            j = json.loads(res)
        except Exception:  # noqa: BLE001
            j = {}
    cid = str(j.get("conv_id") or "")[-10:]
    tail = f" · …{cid}" if cid else ""
    if ev == "reply":
        if j.get("ok"):
            fb = " ⚠ bot trả rỗng" if j.get("is_fallback") else ""
            hd = " · đã giao nhân viên" if j.get("handoffs") else ""
            n = j.get("parts") or 1
            return ("🤖", f"Bot trả lời khách {n} tin{hd}{fb}{tail}", "warn" if fb else "ok")
        sk = j.get("skip")
        if sk == "kill_switch":
            return ("⏸", f"Không trả lời — bot đang bị DỪNG{tail}", "warn")
        if sk == "human_or_returned":
            return ("🧑", f"Không trả lời — hội thoại ở tay nhân viên{tail}", "dim")
        if j.get("error"):
            return ("❌", f"Bot lỗi khi trả lời: {str(j['error'])[:90]}{tail}", "err")
        return ("•", f"reply: {res[:80]}", "dim")
    if ev in ("messaging", "conversation"):
        if j.get("queued"):
            return ("📩", f"Nhận tin khách nhóm BOT — đang gom tin{tail}", "ok")
        if j.get("ab") == "human":
            return ("📩", f"Nhận tin khách nhóm NGƯỜI — nhân viên trả lời{tail}", "dim")
        sk = j.get("skip")
        mp = {"from_page": "tin do page gửi ra", "page_auto": "tin tự động của page",
              "kill_switch": "bot đang bị DỪNG", "human_or_returned": "đang ở tay nhân viên",
              "not_inbox": "không phải inbox", "dup": "tin trùng (đã nhận rồi)",
              "dup_page": "tin trùng (đã nhận rồi)", "empty_text": "tin không có chữ",
              "no_text": "tin không có chữ", "type=COMMENT": "bình luận dưới bài/quảng cáo "
              "— ngoài phạm vi bot", "unknown_page": "page lạ, không thuộc gói"}
        if sk:
            if sk.startswith("type=") and sk not in mp:
                return ("🔇", f"Bỏ qua — không phải inbox ({sk[5:]}){tail}", "dim")
            if sk.startswith("event="):
                return ("", "", "hide")
            return ("🔇", f"Bỏ qua — {mp.get(sk, sk)}{tail}", "dim")
        return ("", "", "hide")   # sự kiện trạng thái thuần — không có gì để nhân viên đọc
    simple = {
        "page_auto": ("🔇", "Lọc tin tự động của page (không tính là sale trả lời)", "dim"),
        "human_tag": ("🧑", "Nhân viên gắn thẻ vào tay — bot rút khỏi hội thoại", "warn"),
        "sale_typed": ("🧑", "Nhân viên nhắn tay — bot rút khỏi hội thoại", "warn"),
        "fu_sent": ("🔔", "Nhịp theo đuổi: nhắc khách đang im lặng", "ok"),
        "fu_handoff": ("📞", "Giao nhân viên gọi ra (khách đã có SĐT)", "ok"),
        "fu_close": ("🔚", "Hết 24h khách không phản hồi → chốt Ko PH", "dim"),
        "attach_handoff": ("🖼", "Khách gửi ảnh/tệp → chuyển nhân viên xem", "ok"),
        "sla_overdue": ("⏰", "QUÁ HẠN: ca chờ nhân viên quá lâu", "warn"),
        "assign_offline": ("👤", "Không ai đang trực tuyến — giao tạm 1 bạn", "warn"),
        "ab_contaminate": ("⚠", "Ca nhóm BOT bị người nhảy vào → loại khỏi số liệu", "warn"),
        "test_conv": ("🧪", "Hội thoại thử #tm", "dim"),
        "empty_msg": ("🔇", "Tin rỗng — bỏ qua", "dim"),
        "no_text_msg": ("🔇", "Tin không có chữ (sticker/ảnh)", "dim"),
        "poll": ("🔄", "Quét dự phòng bắt được tin mới", "ok"),
        "send_fail": ("❌", "GỬI TIN THẤT BẠI — Pancake từ chối", "err"),
        "api_fail": ("❌", "Gọi API Pancake lỗi", "err"),
        "forward_err": ("❌", "Chuyển tiếp sang page khác lỗi", "err"),
        "note_skip": ("📝", "Ghi chú nội bộ (Pancake không hỗ trợ)", "dim"),
        "api_noop": ("✓", "Pancake báo 'không có gì phải đổi' — thẻ/người phụ trách đã đúng sẵn (không phải lỗi)", "dim"),
        "send_unreach": ("🚫", "Không gửi được cho khách (chặn page / xoá hội thoại / hết cửa sổ) — bot ngừng nhắn ca này", "warn"),
        "phone_handoff": ("📞", "Khách gửi SĐT → giao nhân viên gọi ngay", "ok"),
        "src_sync": ("🧭", "Cập nhật nguồn hội thoại (quảng cáo / tự nhiên)", "dim"),
        "pharm_mark": ("🏪", "Khách chọn mua nhà thuốc — hẹn hỏi thăm 1 lần", "dim"),
        "fu_pharm": ("🏪", "Hỏi thăm khách đã mua ở nhà thuốc chưa (đúng 1 lần)", "ok"),
        "pharm_handoff": ("🧑", "Khách phản hồi sau hỏi thăm nhà thuốc → giao nhân viên", "ok"),
        "dedup_part": ("✂", "Chặn một tin lặp nội dung cũ (chống lặp)", "dim"),
        "cmt_priv": ("💬", "Bình luận → đã nhắn riêng tư vấn vào Messenger khách", "ok"),
        "cmt_reply": ("💬", "Đã trả lời công khai dưới bình luận (mời check tin nhắn)", "ok"),
        "cmt_seed": ("💬", "Đã ghi ngữ cảnh bình luận vào hội thoại inbox mới", "dim"),
        "cmt_skip": ("🔇", "Bình luận bỏ qua (giờ im lặng / quá trần mỗi giờ)", "dim"),
        "cmt_human": ("🧑", "Bình luận nhóm ĐỐI CHỨNG (A/B) — nhường nhân viên trả lời", "dim"),
        "cmt_gone": ("🗑", "Bình luận đã bị Facebook gỡ/ẩn — không phải lỗi hệ thống", "dim"),
        "vision_in": ("👁", "Bot xem ảnh/sticker khách gửi kèm tin", "dim"),
        "cmt_fail": ("❌", "Trả lời bình luận LỖI", "err"),
    }
    if ev in simple:
        ic, tx, cl = simple[ev]
        if ev in ("send_fail", "api_fail") and "network:" in (res or ""):
            # v0.5.32: lỗi mạng ≠ Pancake từ chối — ghi cho đúng để khỏi hiểu nhầm (29/08)
            tx = ("GỬI TIN THẤT BẠI — lỗi mạng tới Pancake" if ev == "send_fail"
                  else "Gọi API Pancake lỗi mạng")
        extra = f" — {_h_msg(res)}" if ev in ("send_fail", "api_fail", "forward_err", "cmt_fail") else ""
        return (ic, tx + extra, cl)
    if ev == "error":
        return ("❌", f"Lỗi hệ thống: {res[:110]}", "err")
    if ev == "toggle":
        return ("🎛", f"Đổi công tắc: {res[:80]}", "warn")
    if ev in ("release", "ab_flag"):
        return ("🛠", f"Admin can thiệp: {res[:90]}", "warn")
    return ("•", f"{ev}: {res[:80]}", "dim")


def _health() -> dict:
    """Số liệu sức khoẻ bot: nhịp tim, sự kiện cuối, lỗi, công tắc + nhật ký đã dịch."""
    import time as _t
    import pancake_adapter as _pa
    now = _t.time()
    with db._conn() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT event_type, result, ts FROM webhook_log WHERE ts>=? ORDER BY ts DESC",
            (now - 86400,)).fetchall()]
        try:
            pend = c.execute("SELECT COUNT(*) AS n FROM handoffs WHERE status!='done'"
                             ).fetchone()["n"]
        except Exception:  # noqa: BLE001
            pend = 0

    def sel(pred, within=None):
        return [r for r in rows if pred(r) and (within is None or now - r["ts"] <= within)]

    err15 = sel(lambda r: r["event_type"] in HEALTH_ERR, 900)
    err60 = sel(lambda r: r["event_type"] in HEALTH_ERR, 3600)
    err24 = sel(lambda r: r["event_type"] in HEALTH_ERR)
    rep_ok = sel(lambda r: r["event_type"] == "reply" and '"ok": true' in r["result"])
    rep60 = [r for r in rep_ok if now - r["ts"] <= 3600]
    # mọi lượt flush (kể cả bỏ qua có lý do: người tiếp quản, bot đang dừng) — dùng để biết
    # bot ĐÃ XỬ LÝ xong tin đã gom hay chưa, tránh báo đỏ oan khi nhân viên nhảy vào giữa 45 giây
    rep_any = sel(lambda r: r["event_type"] == "reply")
    fb24 = sel(lambda r: r["event_type"] == "reply" and '"is_fallback": true' in r["result"])
    # v0.5.37: bình luận (event=comment) có pipeline riêng cmt_* (nhắn riêng trong vài giây,
    # lỗi đã có cmt_fail trong HEALTH_ERR) — KHÔNG phải tin inbox chờ bot, kẻo 1 bình luận
    # làm đèn đỏ oan "khách chờ mà bot im" (sự cố 30/08 10:38, ca Lan Nguyen Thi Lan).
    def _q_inbox(r):
        return (r["event_type"] == "messaging" and '"queued"' in r["result"]
                and '"event": "comment"' not in r["result"])
    inb60 = sel(_q_inbox, 3600)
    q_all = sel(_q_inbox)
    fu24 = sel(lambda r: r["event_type"] == "fu_sent")
    last_any = rows[0]["ts"] if rows else 0.0
    last_rep = rep_ok[0]["ts"] if rep_ok else 0.0
    last_flush = rep_any[0]["ts"] if rep_any else 0.0
    last_q = q_all[0]["ts"] if q_all else 0.0
    hb = 0.0
    try:
        hb = float(db.get_setting("hb_ts") or 0)
    except (TypeError, ValueError):
        hb = 0.0

    killed, enabled, testonly = _pa.is_killed(), _pa.is_enabled(), _pa.is_test_only()
    st, reasons = "green", []
    if killed:
        st, reasons = "stopped", ["Có người bấm nút DỪNG BOT KHẨN CẤP (hoặc ENV PANCAKE_KILL=1). "
                                  "Khách nhắn vào sẽ KHÔNG được bot trả lời — phải trực tay."]
    elif hb and now - hb > 180:
        st, reasons = "red", [f"Máy chủ mất nhịp {_dur(now - hb)} — engine có thể đã chết, "
                              f"báo anh Na kiểm tra Railway."]
    elif not hb:
        st, reasons = "yellow", ["Chưa đo được nhịp tim máy chủ — chờ khoảng 1 phút sau khi "
                                 "deploy rồi tải lại trang."]
    elif err15:
        ic, tx, _c = _h_desc(err15[0]["event_type"], err15[0]["result"])
        st, reasons = "red", [f"{len(err15)} lỗi trong 15 phút qua. Gần nhất: {tx}"]
    elif last_q and now - last_q > 300 and last_flush < last_q:
        st, reasons = "red", [f"Đã nhận tin khách nhóm BOT {_dur(now - last_q)} trước mà chưa "
                              f"thấy bot trả lời — vào Pancake trả tay ngay và báo anh Na."]
    elif not enabled:
        st, reasons = "yellow", ["Bot đang ở chế độ CHỈ NGHE — có đọc tin nhưng KHÔNG gửi ra."]
    elif testonly:
        st, reasons = "yellow", ["Bot chỉ trả lời hội thoại có mã thử #tm — khách thường bot "
                                 "không trả lời."]
    elif err60:
        st, reasons = "yellow", [f"{len(err60)} lỗi trong 1 giờ qua (15 phút gần đây đã sạch)."]
    elif last_any and now - last_any > 2700:
        st, reasons = "yellow", [f"{_dur(now - last_any)} không có sự kiện nào — có thể inbox "
                                 f"đang vắng, hoặc webhook Pancake bị ngắt."]
    txt = {"green": "🟢 BOT ĐANG CHẠY BÌNH THƯỜNG", "yellow": "🟡 CẦN CHÚ Ý",
           "red": "🔴 BOT ĐANG CÓ VẤN ĐỀ", "stopped": "⏸ BOT ĐANG DỪNG"}[st]

    def when(ts):
        return f"{_fmt_ts(ts, '%H:%M:%S')} ({_dur(now - ts)} trước)" if ts else "chưa có"

    out_rows = [
        ["Nhịp tim máy chủ", ("🟢 " if hb and now - hb <= 180 else "🔴 ") + (
            f"{_dur(now - hb)} trước" if hb else "chưa có")],
        ["Sự kiện Pancake cuối", when(last_any)],
        ["Bot trả lời gần nhất", when(last_rep) + f" · 1 giờ qua: {len(rep60)} lượt"],
        ["Tin khách nhóm BOT (1 giờ)", f"{len(inb60)} tin vào"],
        ["Lỗi", (f"15 phút: {len(err15)} · 1 giờ: {len(err60)} · 24 giờ: {len(err24)}"
                 + (f" (gần nhất {_fmt_ts(err24[0]['ts'], '%H:%M')})" if err24 else ""))],
        ["Bot trả rỗng (24 giờ)", f"{len(fb24)} lượt"],
        ["Nhịp theo đuổi (24 giờ)", f"{len(fu24)} tin nhắc"],
        ["Ca đang chờ nhân viên", f"{pend} ca"],
        ["Công tắc", ("gửi thật: " + ("BẬT" if enabled else "TẮT")
                      + " · chỉ #tm: " + ("BẬT" if testonly else "TẮT")
                      + " · quét dự phòng: " + ("BẬT" if _pa.is_polling() else "TẮT")
                      + f" · chia A/B: {_pa.status().get('ab_percent')}% cho bot")],
    ]
    log = []
    for r in rows:
        if r["event_type"] in HEALTH_HIDE or len(log) >= 14:
            continue
        ic, tx, cl = _h_desc(r["event_type"], r["result"] or "")
        if cl == "hide":
            continue
        log.append({"icon": ic, "text": tx, "cls": cl, "when": _fmt_ts(r["ts"], "%H:%M:%S")})
    return {"state": st, "state_text": txt, "reasons": reasons, "rows": out_rows,
            "log": log, "kill": killed, "at": _fmt_ts(now, "%H:%M:%S %d/%m/%Y")}


@app.get("/api/admin/bot_health")
def admin_bot_health(key: str = ""):
    """Sức khoẻ bot cho bảng tình trạng (khoá theo dõi xem được)."""
    if not _watch_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return _health()


HEALTH_PANEL = """
<h2 style="margin-top:10px">&#128223; Tình trạng bot</h2>
<div id="hbox" class="hbox"><div class="dim">Đang tải tình trạng…</div></div>
<script>
(function(){
 var K = "__KEY__";
 function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
 function paint(j){
  if (j.error){ document.getElementById('hbox').innerHTML =
     '<div class="hreason">Không đọc được tình trạng: ' + esc(j.error) + '</div>'; return; }
  var h = '<div class="hbanner ' + j.state + '">' + esc(j.state_text) + '</div>';
  (j.reasons || []).forEach(function(r){ h += '<div class="hreason">' + esc(r) + '</div>'; });
  if (j.state === 'red' || j.state === 'stopped')
    h += '<div class="hreason"><a href="#kbox">&#8595; Nút DỪNG / BẬT LẠI BOT ở cuối trang</a></div>';
  h += '<table class="h">';
  (j.rows || []).forEach(function(r){
    h += '<tr><td class="k">' + esc(r[0]) + '</td><td>' + esc(r[1]) + '</td></tr>'; });
  h += '</table><div class="hlog"><b>Bot vừa làm gì</b>';
  (j.log || []).forEach(function(l){
    h += '<div class="' + l.cls + '"><span class="hts">' + esc(l.when) + '</span>'
       + esc(l.icon) + ' ' + esc(l.text) + '</div>'; });
  h += '</div><div class="hts" style="margin-top:8px">Cập nhật ' + esc(j.at)
     + ' — trang tự làm mới mỗi 30 giây</div>';
  var box = document.getElementById('hbox');
  box.className = 'hbox ' + j.state;
  box.innerHTML = h;
  if (window.ksync) window.ksync(!!j.kill);
 }
 function load(){
  fetch('/api/admin/bot_health?key=' + encodeURIComponent(K))
   .then(function(r){ return r.json(); }).then(paint)
   .catch(function(){ document.getElementById('hbox').innerHTML =
     '<div class="hreason">Mất mạng — không đọc được tình trạng bot.</div>'; });
 }
 load(); setInterval(load, 30000);
})();
</script>
"""


# ---- v0.5.17: bảng LOẠI/BỎ LOẠI hội thoại bằng tay (chỉ admin thấy trên trang A/B)
AB_FLAG_PANEL = """
<h2>&#9986; Loại / bỏ loại một hội thoại bằng tay</h2>
<div class="kbox" style="border-color:#2a6b46">
  <div class="krow">
    <input id="fcid" placeholder="ID hội thoại (dán cả id, hoặc 8-10 số cuối)">
    <input id="fby" placeholder="Tên bạn" maxlength="40" style="max-width:150px">
  </div>
  <div class="krow" style="margin-top:8px">
    <button id="fout" class="kbtn off">Loại khỏi số liệu</button>
    <button id="fin" class="kbtn on">Bỏ loại (tính lại)</button>
  </div>
  <div id="fmsg" class="kmsg"></div>
  <p class="khelp">Dùng khi <b>có người nhảy vào ca nhóm BOT</b> mà van tự động chưa bắt được
  (ví dụ ca kẹt vì deploy, phải gắn thẻ chữa cháy). Ca đó phải bị loại để so sánh còn công bằng.
  Bấm xong <b>tải lại trang</b> để thấy số mới.</p>
</div>
<script>
(function(){
 var K="__KEY__";
 function go(v){
  var cid=document.getElementById('fcid').value.trim();
  var by=document.getElementById('fby').value.trim();
  var m=document.getElementById('fmsg');
  if(!cid){m.textContent='Nhập ID hội thoại đã.';return;}
  m.textContent='Đang gửi…';
  fetch('/api/admin/ab_flag',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({key:K,conv_id:cid,value:v,by:by})})
   .then(function(r){return r.json();})
   .then(function(j){ m.textContent = j.ok
     ? ('Xong — '+(v?'đã loại':'đã bỏ loại')+' hội thoại …'+String(j.conv_id).slice(-10)
        +'. Tải lại trang để xem số mới.')
     : ('Lỗi: '+(j.error||'không rõ')); })
   .catch(function(e){ m.textContent='Lỗi mạng: '+e; });
 }
 document.getElementById('fout').onclick=function(){go(1);};
 document.getElementById('fin').onclick=function(){go(0);};
})();
</script>
"""


@app.post("/api/admin/ab_flag")
async def admin_ab_flag(req: Request):
    """v0.5.17: LOẠI (hoặc bỏ loại) một hội thoại khỏi số liệu A/B bằng tay — dành cho ca
    người nhảy vào chữa cháy mà van tự động chưa bắt được. CHỈ admin, khoá theo dõi không được.
    Nhận cả id đầy đủ hoặc vài số cuối (khớp đuôi, chỉ chấp nhận khi ra đúng 1 hội thoại)."""
    body = await req.json()
    if not _admin_ok(body.get("key", "")):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    cid = (body.get("conv_id") or "").strip()
    if len(cid) < 6:
        return JSONResponse({"error": "cần conv_id (ít nhất 6 ký tự cuối)"}, status_code=400)
    val = 1 if body.get("value", 1) else 0
    who = str(body.get("by") or "").strip()[:40] or "admin"
    with db._conn() as c:
        hit = [r["pancake_conv_id"] for r in c.execute(
            "SELECT pancake_conv_id FROM ab_stats WHERE pancake_conv_id=? OR"
            " pancake_conv_id LIKE ?", (cid, "%" + cid)).fetchall()]
        if len(hit) != 1:
            return JSONResponse({"error": ("không thấy hội thoại này trong số liệu A/B (có thể "
                                           "phát sinh trước mốc đo)" if not hit else
                                           f"đuôi id trùng {len(hit)} hội thoại — dán dài hơn")},
                                status_code=404)
        c.execute("UPDATE ab_stats SET contaminated=? WHERE pancake_conv_id=?", (val, hit[0]))
    db.set_setting("ab_flag:" + hit[0], who if val else "")
    db.log_webhook("ab_flag", f"{hit[0]}: contaminated={val} (bởi {who})")
    return {"ok": True, "conv_id": hit[0], "contaminated": val,
            "summary": _ab_summary(_ab_rows())}


@app.get("/api/admin/ab_report")
def admin_ab_report(key: str = ""):
    """A/B bot vs người TÍNH TỪ MỐC ĐO — popup admin đọc key bot/human, key lạ được bỏ qua."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    out = _ab_summary(_ab_rows())
    out["do_tu_moc"] = _fmt_ts(_ab_start(), "%d/%m/%Y %H:%M:%S")
    return out


@app.get("/a/{key}/ab", response_class=HTMLResponse)
@app.get("/w/{key}", response_class=HTMLResponse)
@app.get("/w/{key}/ab", response_class=HTMLResponse)
def admin_ab_page(key: str, req: Request = None):
    """Trang báo cáo A/B đầy đủ: tổng quan, tiến độ mẫu, bảng theo ngày, ca lai tạp,
    kèm bảng DỪNG BOT KHẨN CẤP. Mở được bằng admin key hoặc khoá theo dõi (/w/{key})."""
    if not _watch_ok(key):
        return HTMLResponse("forbidden", status_code=403)
    from datetime import datetime
    tz = _tz7()
    rows = _ab_rows()
    s = _ab_summary(rows)

    def block(grp, icon, label):
        x = s[grp]
        pct = x["replied_pct"] if x["replied_pct"] is not None else "—"
        ph = x["phone_pct"] if x["phone_pct"] is not None else "—"
        # v0.5.25 (anh Na chốt 28/08): BỎ dòng "Số đơn / Tỷ lệ chốt đơn" khỏi báo cáo —
        # đơn trên Pancake không đáng tin (40% là đơn TỰ SINH cùng giây khách nhắn, và mọi đơn
        # đều 0đ/0 sản phẩm). Hướng thay thế: cứ thu SĐT, sau này đối chiếu với hệ thống bán
        # hàng thật để có cả hoàn/huỷ. Số liệu đơn vẫn được lưu (bảng ab_orders) nhưng KHÔNG
        # hiển thị; muốn bật lại thì trả dòng {od} vào đây.
        return (f"<div class='card'><h3>{icon} {label}</h3>"
                f"<p>Hội thoại sạch <b>{x['conversations']}</b> · Trả lời <b>{pct}%</b> ({x['replied']})</p>"
                f"<p>Phản hồi đầu (trung vị): <b>{_dur(x['median_first_reply_sec'])}</b></p>"
                f"<p>Có SĐT: <b>{x['phone_n']}</b> ({ph}%) · Loại <b>{x['contaminated_excluded']}</b> ca lai tạp"
                # v0.5.31 (anh Na 29/08): BỎ dòng "🚫 Không gửi được" khỏi card — số này vẫn có
                # trong Excel (cột "Không gửi được (FB #551)") và ca vẫn được loại đúng khỏi A/B.
                + "</p></div>")

    days = {}
    for r in rows:
        d = datetime.fromtimestamp(r["first_in_ts"], tz).strftime("%d/%m")
        days.setdefault(d, []).append(r)

    def day_cells(g_rows, grp):
        g = [r for r in g_rows if r["grp"] == grp]
        clean = [r for r in g if not r["contaminated"]]
        replied = [r for r in clean if r["first_reply_ts"]]
        waits = sorted(r["first_reply_ts"] - r["first_in_ts"] for r in replied)
        med = _dur(waits[len(waits) // 2]) if waits else "—"
        pct = f"{100 * len(replied) / len(clean):.0f}%" if clean else "—"
        ph = sum(r["phone"] for r in clean)
        return (f"<td>{len(clean)}</td><td>{pct}</td><td>{med}</td>"
                f"<td>{ph}</td><td class='dim'>{len(g) - len(clean)}</td>")

    # v0.5.23 (anh Na 28/08): NGÀY MỚI NHẤT LÊN TRÊN, chỉ hiện 3 ngày — muốn xem thêm thì cuộn
    day_sorted = sorted(days.items(),
                        key=lambda kv: max(r["first_in_ts"] for r in kv[1]), reverse=True)
    day_rows = "".join(f"<tr><td><b>{d}</b></td>{day_cells(g, 'bot')}{day_cells(g, 'human')}</tr>"
                       for d, g in day_sorted)
    day_h = 62 + 30 * min(3, len(day_sorted))     # 2 tầng tiêu đề + tối đa 3 dòng
    day_more = (f'<p class="meta">Đang hiện 3 ngày gần nhất trong tổng số {len(day_sorted)} '
                f'ngày — cuộn trong bảng để xem các ngày trước.</p>'
                if len(day_sorted) > 3 else "")

    # v0.5.23 (anh Na 28/08): CA MỚI NHẤT LÊN TRÊN, khung chỉ cao bằng số ca HÔM NAY —
    # ca của những ngày trước vẫn còn đủ, cuộn trong bảng là thấy.
    bad = sorted((r for r in rows if r["contaminated"]),
                 key=lambda r: r["first_in_ts"], reverse=True)
    _today = datetime.now(tz).strftime("%d/%m")
    n_today = sum(1 for r in bad
                  if datetime.fromtimestamp(r["first_in_ts"], tz).strftime("%d/%m") == _today)
    bad_rows = "".join(
        f"<tr><td>{_fmt_ts(r['first_in_ts'], '%d/%m %H:%M')}</td>"
        f"<td>{'BOT' if r['grp'] == 'bot' else 'NGƯỜI'}</td>"
        f"<td class='mono'>…{str(r['pancake_conv_id'])[-10:]}</td>"
        f"<td>{r['msgs']}</td><td>{_ab_reason(r)}</td></tr>" for r in bad) or         "<tr><td colspan='5'>Chưa có ca nào — tốt!</td></tr>"
    bad_h = 32 + 30 * max(1, min(n_today or 3, len(bad) or 1))
    bad_more = (f'<p class="meta">Đang hiện {n_today} ca của hôm nay ({_today}); '
                f'còn {len(bad) - n_today} ca những ngày trước — cuộn trong bảng để xem.</p>'
                if len(bad) > n_today and n_today else "")

    # v0.5.23 (anh Na 28/08): THAY note "tiến độ mẫu" bằng so sánh tỷ lệ có SĐT + cỡ mẫu cần.
    # (2 note mốc followup / gom tin 12 giây đã bỏ theo yêu cầu — anh Na đã nắm.)
    _b, _h = s["bot"], s["human"]
    if not _b["conversations"] or not _h["conversations"]:
        phone_note = ('<div class="note">📏 Chưa đủ hội thoại ở cả hai nhóm để so tỷ lệ '
                      'để lại số điện thoại.</div>')
    else:
        p1, p2 = _b["phone_n"] / _b["conversations"], _h["phone_n"] / _h["conversations"]
        gap = (p1 - p2) * 100
        need = _sample_needed(p1, p2)
        who = "BOT" if gap > 0 else "NGƯỜI"
        if need < 0:
            tail = ("Hai nhóm đang <b>ngang nhau</b> — chưa có chênh lệch nào để kết luận.")
        elif need > 20000:
            tail = (f"Chênh lệch <b>{abs(gap):.1f} điểm</b> nghiêng về {who} nhưng quá nhỏ: "
                    f"cần trên 20.000 hội thoại mỗi nhóm mới dám khẳng định — thực tế nên coi "
                    f"như <b>chưa khác biệt</b>.")
        else:
            done = min(_b["conversations"], _h["conversations"])
            enough = ("<b>ĐÃ ĐỦ MẪU</b> để kết luận." if done >= need
                      else f"còn thiếu khoảng <b>{need - done}</b> hội thoại mỗi nhóm.")
            tail = (f"Chênh <b>{abs(gap):.1f} điểm</b> nghiêng về <b>{who}</b>. Để khẳng định "
                    f"chắc chắn ở mức chênh này cần khoảng <b>{need}</b> hội thoại mỗi nhóm "
                    f"(tin cậy 95%) — {enough}")
        phone_note = (f'<div class="note">📏 <b>Tỷ lệ khách để lại số điện thoại</b>: '
                      f'BOT <b>{p1 * 100:.1f}%</b> ({_b["phone_n"]}/{_b["conversations"]}) · '
                      f'NGƯỜI <b>{p2 * 100:.1f}%</b> ({_h["phone_n"]}/{_h["conversations"]}). '
                      f'{tail}</div>')

    import pancake_adapter as _pa
    _envnote = ('<div class="note">⚠ Biến môi trường <b>PANCAKE_KILL=1</b> đang ép tắt bot — '
                'nút bật lại ở đây sẽ KHÔNG có tác dụng cho tới khi xoá biến đó trên Railway.'
                '</div>') if os.environ.get("PANCAKE_KILL", "0") == "1" else ""
    kill_panel = (KILL_PANEL.replace("__KEY__", key)
                            .replace("__KILLED__", "true" if _pa.is_killed() else "false")
                            .replace("__ENVNOTE__", _envnote))
    admin_extra = ""
    if _admin_ok(key):
        _base = str(req.base_url).rstrip("/") if req is not None else ""
        if _base.startswith("http://") and not ("localhost" in _base or "127.0.0.1" in _base):
            _base = "https://" + _base[7:]   # Railway proxy trả http — link gửi ra phải https
        _wurl = _base + "/w/" + _watch_key()
        admin_extra = (
            '<a class="btn" style="background:#555" href="/a/' + key + '">← Về admin</a>'
            '<div class="note">🔗 <b>Link gửi nhân viên trực</b> (chỉ xem báo cáo A/B + nút '
            'dừng khẩn, KHÔNG vào được trang admin):<br><a class="mono" href="' + _wurl
            + '">' + _wurl + '</a></div>'
            + AB_FLAG_PANEL.replace("__KEY__", key))

    health_panel = HEALTH_PANEL.replace("__KEY__", key)
    # v0.5.22 A1: Excel chứa SĐT đầy đủ — chỉ admin key thấy nút tải (link /w/ chia cho nhân viên)
    excel_btn = (f'<a class="btn" href="/api/admin/ab_export.xlsx?key={key}">⬇ Tải Excel A/B '
                 f'(có SĐT đầy đủ)</a>') if _admin_ok(key) else ""

    html = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Báo cáo A/B — Sâm Thái Minh</title><style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:16px auto;max-width:860px;padding:0 12px;color:#222;background:#fafaf7}}
h1{{font-size:22px}} h2{{font-size:17px;margin-top:28px}} h3{{margin:0 0 6px}}
.meta{{color:#666;font-size:13px}} .cards{{display:flex;gap:12px;flex-wrap:wrap}}
.card{{flex:1;min-width:260px;border:1px solid #ddd;border-radius:10px;padding:10px 14px;background:#fff}}
.card p{{margin:4px 0;font-size:14px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
th,td{{border:1px solid #ddd;padding:5px 8px;text-align:center}}
th{{background:#f0ede6;position:sticky;top:0;z-index:2}}
.dim{{color:#999}} .mono{{font-family:monospace;font-size:12px}}
.scroll{{overflow-y:auto;border:1px solid #ddd;border-radius:8px;background:#fff}}
.scroll table{{border:0}} h2 .meta{{font-weight:400;font-size:13px}}
.note{{background:#fff8e0;border:1px solid #e8d9a0;border-radius:8px;padding:8px 12px;font-size:13px;margin:14px 0}}
a.btn{{display:inline-block;margin:10px 6px 0 0;padding:7px 14px;border-radius:8px;background:#2a6b46;color:#fff;text-decoration:none;font-size:14px}}
.kbox{{border:2px solid #d33;border-radius:10px;padding:12px 14px;background:#fff}}
.kstate{{font-size:15px;margin-bottom:9px}} .kstate.ok{{color:#1d6b3a}} .kstate.off{{color:#c62828}}
.krow{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.krow input{{flex:1;min-width:150px;padding:9px;border:1px solid #ccc;border-radius:8px;font-size:14px}}
.kbtn{{padding:11px 16px;border:0;border-radius:8px;color:#fff;font-size:15px;font-weight:600;cursor:pointer}}
.kbtn.off{{background:#c62828}} .kbtn.on{{background:#2a6b46}} .kbtn:disabled{{opacity:.6}}
.kmsg{{font-size:13px;color:#444;margin-top:9px;min-height:18px}}
.khelp{{font-size:12.5px;color:#666;margin:10px 0 0;line-height:1.45}}
.hbox{{border:2px solid #ccc;border-radius:10px;padding:12px 14px;background:#fff}}
.hbox.green{{border-color:#2a6b46}} .hbox.yellow{{border-color:#d99500}}
.hbox.red{{border-color:#c62828}} .hbox.stopped{{border-color:#777}}
.hbanner{{font-size:16px;font-weight:700;margin-bottom:4px}}
.hbanner.green{{color:#1d6b3a}} .hbanner.yellow{{color:#8a6100}}
.hbanner.red{{color:#c62828}} .hbanner.stopped{{color:#555}}
.hreason{{font-size:13px;color:#8a3b3b;margin:3px 0;line-height:1.4}}
table.h{{margin-top:8px}} table.h td{{text-align:left;font-size:13px;border-color:#eee}}
table.h td.k{{color:#666;width:42%}}
.hlog{{margin-top:10px;font-size:12.5px}}
.hlog b{{display:block;margin-bottom:3px;color:#444}}
.hlog div{{padding:3px 0;border-top:1px dashed #eee;line-height:1.35}}
.hlog .ok{{color:#1d6b3a}} .hlog .warn{{color:#8a6100}} .hlog .err{{color:#c62828}}
.hlog .dim{{color:#8a8a8a}}
.hts{{color:#999;font-family:monospace;font-size:11.5px;margin-right:6px}}
</style></head><body>
<h1>🧪 Báo cáo A/B — BOT vs NGƯỜI (Sâm Thái Minh)</h1>
<p class="meta">Chỉ tính hội thoại INBOX phát sinh từ <b>mốc đo {_fmt_ts(_ab_start(), "%H:%M %d/%m/%Y")}</b>
(mọi van đo đã vá xong). Comment ngoài phạm vi. Cập nhật lúc {_fmt_ts(__import__("time").time(), "%H:%M %d/%m/%Y")}.</p>
{health_panel}
<h2>Kết quả A/B</h2>
<div class="cards">{block('bot', '🤖', 'Nhóm BOT')}{block('human', '🧑', 'Nhóm NGƯỜI')}</div>
{phone_note}
<h2>Theo ngày <span class="meta">(mới nhất ở trên)</span></h2>
<div class="scroll" style="max-height:{day_h}px">
<table><tr><th rowspan="2">Ngày</th><th colspan="5">🤖 BOT</th><th colspan="5">🧑 NGƯỜI</th></tr>
<tr><th>HT sạch</th><th>Trả lời</th><th>Phản hồi đầu</th><th>SĐT</th><th>Lai tạp</th>
<th>HT sạch</th><th>Trả lời</th><th>Phản hồi đầu</th><th>SĐT</th><th>Lai tạp</th></tr>{day_rows}</table>
</div>{day_more}
<h2>Ca lai tạp (bị loại khỏi số liệu)</h2>
<div class="scroll" style="max-height:{bad_h}px">
<table><tr><th>Lúc</th><th>Nhóm</th><th>Hội thoại</th><th>Tin khách</th><th>Lý do (ước đoán)</th></tr>{bad_rows}</table>
</div>{bad_more}
{kill_panel}
{excel_btn}
{admin_extra}
<p class="meta">🧾 <b>Về tỷ lệ chốt đơn</b>: chưa đưa lên báo cáo. Đơn trên Pancake không dùng
để đo được (không có sản phẩm/số tiền, và một phần đơn tự sinh ngay khi khách nhắn). Cách làm:
bot vẫn <b>thu số điện thoại của cả hai nhóm</b> (xem file Excel), sau này đối chiếu với hệ thống
bán hàng của công ty để ra tỷ lệ chốt thật — có cả đơn hoàn và huỷ.</p>
<p class="meta">Trung vị phản hồi nhóm bot gồm thời gian chờ gom tin theo thiết kế
(45 giây trước mốc hạ, 12 giây sau mốc). Ca lai tạp = có người
nhảy vào ca nhóm BOT (nhắn tay qua Pancake, hoặc gắn thẻ "Để NV xử lý" khi bot đang trực), hội thoại
thử #tm, hoặc ca admin loại tay — bị loại để so sánh công bằng. Ca bot TỰ chuyển nhân viên rồi mới
được gắn thẻ thì vẫn tính, vì đó là đường đi đúng của bot.</p>
</body></html>"""
    return HTMLResponse(html)


@app.get("/api/admin/ab_export.xlsx")
def admin_ab_export(key: str = ""):
    """Excel A/B: Tổng quan + Theo ngày + Chi tiết từng hội thoại (từ mốc đo).
    v0.5.22 A1: file có SĐT đầy đủ → CHỈ admin key tải được (khoá theo dõi /w/ hết quyền)."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    from openpyxl import Workbook
    from datetime import datetime
    tz = _tz7()
    rows = _ab_rows()
    s = _ab_summary(rows)
    wb = Workbook()
    ws = wb.active
    ws.title = "Tổng quan"
    ws.append(["Báo cáo A/B — BOT vs NGƯỜI (Sâm Thái Minh)"])
    ws.append(["Mốc đo từ", _fmt_ts(_ab_start(), "%d/%m/%Y %H:%M:%S")])
    ws.append(["Xuất lúc", _fmt_ts(__import__("time").time(), "%d/%m/%Y %H:%M:%S")])
    ws.append([])
    ws.append(["Nhóm", "Hội thoại sạch", "Đã trả lời", "% trả lời", "Trung vị phản hồi (giây)",
               "Có SĐT", "% SĐT", "Ca lai tạp (loại)", "Không gửi được (FB #551)"])
    for grp, label in (("bot", "BOT"), ("human", "NGƯỜI")):
        x = s[grp]
        ws.append([label, x["conversations"], x["replied"], x["replied_pct"],
                   x["median_first_reply_sec"], x["phone_n"], x["phone_pct"], x["contaminated_excluded"],
                   x.get("unreachable") or 0])
    for col, w in zip("ABCDEFGHI", [10, 14, 12, 10, 22, 9, 9, 16, 20]):
        ws.column_dimensions[col].width = w
    days = {}
    for r in rows:
        d = datetime.fromtimestamp(r["first_in_ts"], tz).strftime("%d/%m/%Y")
        days.setdefault(d, []).append(r)
    ws2 = wb.create_sheet("Theo ngày")
    ws2.append(["Ngày", "Nhóm", "Hội thoại sạch", "Đã trả lời", "% trả lời",
                "Trung vị phản hồi (giây)", "Có SĐT", "Lai tạp"])
    for d, g_rows in days.items():
        for grp, label in (("bot", "BOT"), ("human", "NGƯỜI")):
            g = [r for r in g_rows if r["grp"] == grp]
            clean = [r for r in g if not r["contaminated"]]
            replied = [r for r in clean if r["first_reply_ts"]]
            waits = sorted(r["first_reply_ts"] - r["first_in_ts"] for r in replied)
            med = round(waits[len(waits) // 2], 1) if waits else None
            pct = round(100.0 * len(replied) / len(clean), 1) if clean else None
            ws2.append([d, label, len(clean), len(replied), pct, med,
                        sum(r["phone"] for r in clean), len(g) - len(clean)])
    for col, w in zip("ABCDEFGH", [12, 8, 14, 11, 10, 22, 9, 9]):
        ws2.column_dimensions[col].width = w
    ws3 = wb.create_sheet("Chi tiết")
    pmap = _ab_phone_map()
    ws3.append(["Conv ID", "Nhóm", "Tin đầu của khách", "Trả lời đầu", "Chờ (giây)",
                "Tin khách", "Lượt trả lời", "Có SĐT", "SĐT thật", "Lai tạp", "Lý do (ước đoán)"])
    for r in rows:
        ws3.append([r["pancake_conv_id"], "BOT" if r["grp"] == "bot" else "NGƯỜI",
                    _fmt_ts(r["first_in_ts"], "%d/%m/%Y %H:%M:%S"),
                    _fmt_ts(r["first_reply_ts"], "%d/%m/%Y %H:%M:%S") if r["first_reply_ts"] else "",
                    round(r["first_reply_ts"] - r["first_in_ts"], 1) if r["first_reply_ts"] else "",
                    r["msgs"], r["replies"], "x" if r["phone"] else "",
                    ", ".join(pmap.get(r["pancake_conv_id"]) or []),
                    "LOẠI" if r["contaminated"] else "", _ab_reason(r) if r["contaminated"] else ""])
    for col, w in zip("ABCDEFGHIJK", [38, 8, 20, 20, 11, 9, 11, 8, 26, 8, 34]):
        ws3.column_dimensions[col].width = w
    # v0.5.21: sheet SĐT — mỗi số 1 dòng, dán thẳng vào Pancake POS để tra đơn
    ws4 = wb.create_sheet("SĐT")
    ws4.append(["SĐT", "Nhóm", "Lúc khách nhắn đầu", "Conv ID", "Vào số liệu", "Có đơn?", "Ghi chú"])
    for r in rows:
        for ph in (pmap.get(r["pancake_conv_id"]) or []):
            ws4.append([ph, "BOT" if r["grp"] == "bot" else "NGƯỜI",
                        _fmt_ts(r["first_in_ts"], "%d/%m/%Y %H:%M:%S"), r["pancake_conv_id"],
                        "LOẠI" if r["contaminated"] else "tính", "", ""])
    for col, w in zip("ABCDEFG", [14, 8, 20, 38, 12, 10, 26]):
        ws4.column_dimensions[col].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bao-cao-ab-samthaiminh.xlsx"})


@app.get("/api/admin/ab_phone_backfill")
@app.post("/api/admin/ab_phone_backfill")
def admin_ab_phone_backfill(key: str = "", limit: int = 60, offset: int = 0):
    """v0.5.21: lấp SĐT cho ca CŨ — đi đúng danh sách conv_id đang đo trong ab_stats, gọi
    Pancake đọc tin của KHÁCH rồi moi SĐT về bảng ab_phones (không rà mù cả page).
    Chạy theo lô để khỏi quá hạn HTTP: ?limit=60&offset=0, rồi offset=60, 120..."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    import pancake_adapter as pa
    allr = _ab_rows()
    batch = allr[offset:offset + max(1, limit)]
    done = err = found = 0
    for r in batch:
        cid = r["pancake_conv_id"]
        rm = pa._api("GET", f"/pages/{pa.PAGE_ID}/conversations/{cid}/messages")
        if not isinstance(rm, dict) or rm.get("error"):
            err += 1
            continue
        done += 1
        phones = []
        for m in (rm.get("messages") or rm.get("data") or []):
            f = m.get("from") or {}
            if f.get("id") == pa.PAGE_ID or m.get("is_from_page"):
                continue          # tin của page — chỉ lấy số do KHÁCH nhắn
            for p in pa.find_phones(pa._strip_html(m.get("message") or m.get("text") or "")):
                if p not in phones:
                    phones.append(p)
        if phones:
            pa.ab_save_phones(cid, r["grp"], phones, src="backfill")
            found += len(phones)
    nxt = offset + len(batch)
    return {"ok": True, "tong_ca": len(allr), "da_quet": done, "loi": err,
            "so_dt_ghi_nhan": found, "offset_tiep": nxt if nxt < len(allr) else None,
            "ghi_chu": "Chạy lại nhiều lần vô hại — số trùng không ghi đè."}


@app.post("/api/admin/ab_orders_import")
async def admin_ab_orders_import(req: Request):
    """v0.5.24 (D2): nạp đơn theo hội thoại. Dùng khi CHƯA có khoá API POS — lấy đơn từ giao
    diện Pancake rồi đẩy vào đây. Body: {key, orders:[{conv_id, order_id, status, status_name,
    total, phone, inserted_at}]}. Trạng thái đơn thay đổi được (Mới → Đã xác nhận): gọi lại là
    cập nhật, không tạo trùng."""
    body = await req.json()
    if not _admin_ok(body.get("key", "")):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    orders = body.get("orders") or []
    if not isinstance(orders, list):
        return JSONResponse({"error": "orders phải là danh sách"}, status_code=400)
    import pancake_adapter as pa
    n = pa.ab_save_orders(orders, src=body.get("src") or "import")
    db.log_webhook("orders_import", f"nạp {n}/{len(orders)} đơn (bởi {str(body.get('by') or 'admin')[:40]})")
    return {"ok": True, "nhan": len(orders), "luu": n}


@app.get("/api/admin/ab_orders_sync")
def admin_ab_orders_sync(key: str = "", pages: int = 3):
    """v0.5.24 (D2): quét đơn từ POS ngay (cần ENV PANCAKE_POS_API_KEY)."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    import pancake_adapter as pa
    return pa.pos_orders_sync(max_pages=max(1, min(pages, 20)))


@app.get("/api/admin/ab_orders")
def admin_ab_orders(key: str = ""):
    """v0.5.24 (D2): xem đơn đã nối được, kèm nhóm A/B của từng ca."""
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    omap = _ab_order_map()
    rows = _ab_rows()
    grp = {r["pancake_conv_id"]: (r["grp"], bool(r["contaminated"])) for r in rows}
    out = []
    for cid, orders in omap.items():
        g, bad = grp.get(cid, ("(ngoài mốc đo)", False))
        for o in orders:
            out.append({"conv_id": cid, "nhom": g, "loai_khoi_so_lieu": bad,
                        "don": o["id"], "trang_thai": o["status"],
                        "da_xac_nhan": _order_confirmed(o), "luc": o["inserted_at"]})
    out.sort(key=lambda x: x["luc"] or "", reverse=True)
    return {"n": len(out), "orders": out}


@app.get("/api/admin/kb")
def admin_kb_get(key: str = ""):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return tools_core.load_kb()


@app.post("/api/admin/kb")
async def admin_kb_upload(key: str = "", file: UploadFile = File(...)):
    if not _admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": f"JSON không hợp lệ: {e}"}, status_code=400)
    for k in ("_meta", "products", "need_map", "compliance", "programs", "combo_tiers"):
        if k not in data:
            return JSONResponse({"error": f"KB thiếu khối bắt buộc: {k}"}, status_code=400)
    tools_core.save_kb(data)
    return {"ok": True, "note": "KB đã cập nhật — bot dùng ngay từ tin nhắn tiếp theo."}
