"""SQLite storage: hội thoại, tin nhắn, feedback. Stdlib only."""
import os
import sqlite3
import time
import uuid

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db"))


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS conversations(
            id TEXT PRIMARY KEY, tester TEXT, started_at REAL, model TEXT);
        CREATE TABLE IF NOT EXISTS messages(
            id TEXT PRIMARY KEY, conv_id TEXT, role TEXT, content TEXT,
            ts REAL, latency_ms INTEGER, model TEXT, tool_trace TEXT,
            is_fallback INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS feedback(
            message_id TEXT PRIMARY KEY, conv_id TEXT, rating TEXT, note TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS suggestions(
            id TEXT PRIMARY KEY, conv_id TEXT, tester TEXT, content TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS handoffs(
            id TEXT PRIMARY KEY, conv_id TEXT, tester TEXT, reason TEXT, phone TEXT,
            ts REAL, status TEXT DEFAULT 'open', level INTEGER DEFAULT 2);
        CREATE TABLE IF NOT EXISTS pancake_map(
            pancake_conv_id TEXT PRIMARY KEY, local_conv_id TEXT, customer TEXT,
            state TEXT DEFAULT 'bot_active', returned_level INTEGER DEFAULT 0, ts REAL);
        CREATE TABLE IF NOT EXISTS webhook_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, result TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY, value TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS leads(
            id TEXT PRIMARY KEY, conv_id TEXT, source TEXT, phone TEXT,
            context TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS ab_stats(
            pancake_conv_id TEXT PRIMARY KEY, grp TEXT, first_in_ts REAL,
            first_reply_ts REAL, msgs INTEGER DEFAULT 0, replies INTEGER DEFAULT 0,
            phone INTEGER DEFAULT 0, contaminated INTEGER DEFAULT 0, ts REAL);
        """)
        # migration cho DB cũ (data.db vòng trước) — thêm cột nếu thiếu
        for tbl, col, ddl in [("messages", "is_fallback", "ALTER TABLE messages ADD COLUMN is_fallback INTEGER DEFAULT 0"),
                              ("handoffs", "level", "ALTER TABLE handoffs ADD COLUMN level INTEGER DEFAULT 2"),
                              ("handoffs", "source", "ALTER TABLE handoffs ADD COLUMN source TEXT DEFAULT ''"),
                              ("handoffs", "sla_pinged", "ALTER TABLE handoffs ADD COLUMN sla_pinged INTEGER DEFAULT 0"),
                              ("pancake_map", "ab_group", "ALTER TABLE pancake_map ADD COLUMN ab_group TEXT DEFAULT ''"),
                              ("pancake_map", "is_test", "ALTER TABLE pancake_map ADD COLUMN is_test INTEGER DEFAULT 0")]:
            cols = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()]
            if col not in cols:
                c.execute(ddl)


def new_conversation(tester: str, model: str) -> str:
    cid = uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute("INSERT INTO conversations VALUES(?,?,?,?)", (cid, tester, time.time(), model))
    return cid


def add_message(conv_id, role, content, latency_ms=None, model=None, tool_trace=None,
                is_fallback=False) -> str:
    mid = uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute("INSERT INTO messages(id,conv_id,role,content,ts,latency_ms,model,tool_trace,is_fallback)"
                  " VALUES(?,?,?,?,?,?,?,?,?)",
                  (mid, conv_id, role, content, time.time(), latency_ms, model, tool_trace,
                   1 if is_fallback else 0))
    return mid


def get_history(conv_id, limit=40):
    """Lịch sử gửi lại model — LỌC BỎ tin dự phòng (is_fallback) và tin rỗng.
    Đây là mấu chốt chống vòng lặp câu chờ v0.4: câu 'chờ em kiểm tra' không bao giờ
    quay lại prompt để model tưởng mình 'đang đi kiểm tra' rồi im lặng tiếp."""
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE conv_id=? AND role IN ('user','assistant') "
            "AND COALESCE(is_fallback,0)=0 AND TRIM(COALESCE(content,''))<>'' ORDER BY ts LIMIT ?",
            (conv_id, limit)).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def recent_fallback_streak(conv_id) -> int:
    """Đếm số tin assistant dự phòng LIÊN TIẾP ở cuối hội thoại (để bật cờ khi >=2)."""
    with _conn() as c:
        rows = c.execute(
            "SELECT is_fallback FROM messages WHERE conv_id=? AND role='assistant' ORDER BY ts DESC LIMIT 5",
            (conv_id,)).fetchall()
    n = 0
    for r in rows:
        if r["is_fallback"]:
            n += 1
        else:
            break
    return n


def set_feedback(message_id, conv_id, rating, note):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO feedback VALUES(?,?,?,?,?)",
                  (message_id, conv_id, rating, note, time.time()))


def add_suggestion(conv_id, tester, content) -> str:
    sid = uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute("INSERT INTO suggestions VALUES(?,?,?,?,?)",
                  (sid, conv_id, tester, content, time.time()))
    return sid


def add_handoff(conv_id, tester, reason, phone="", level=2) -> str:
    """Cờ chuyển nhân viên (Rule 6-9 + escalation 4 level): lưu ca cần người thật kiểm tra & gọi lại."""
    hid = uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute("INSERT INTO handoffs(id,conv_id,tester,reason,phone,ts,status,level)"
                  " VALUES(?,?,?,?,?,?,?,?)",
                  (hid, conv_id, tester, (reason or "")[:200], (phone or "")[:20], time.time(), "open",
                   int(level) if level else 2))
    return hid


def list_handoffs(limit=500):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM handoffs ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()]


def set_handoff_status(hid, status):
    with _conn() as c:
        c.execute("UPDATE handoffs SET status=? WHERE id=?", (status, hid))


# ---- Pancake conversation mapping (hướng B) ----
def pancake_local_conv(pancake_conv_id, customer=None) -> str:
    """Ánh xạ hội thoại Pancake -> conv_id nội bộ (giữ trí nhớ giữa các tin của cùng khách)."""
    with _conn() as c:
        r = c.execute("SELECT local_conv_id FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
        if r and r["local_conv_id"]:
            return r["local_conv_id"]
        local = uuid.uuid4().hex[:12]
        c.execute("INSERT INTO conversations VALUES(?,?,?,?)",
                  (local, f"pancake:{customer or pancake_conv_id}", time.time(), "sonnet"))
        if r:
            # row đã được tạo trước bởi pancake_ab_group / claim — chỉ điền local_conv_id
            c.execute("UPDATE pancake_map SET local_conv_id=?, customer=COALESCE(NULLIF(customer,''),?)"
                      " WHERE pancake_conv_id=?",
                      (local, str(customer or ""), pancake_conv_id))
        else:
            c.execute("INSERT INTO pancake_map(pancake_conv_id,local_conv_id,customer,state,returned_level,ts)"
                      " VALUES(?,?,?,?,?,?)",
                      (pancake_conv_id, local, str(customer or ""), "bot_active", 0, time.time()))
        return local


def pancake_is_human(pancake_conv_id) -> bool:
    with _conn() as c:
        r = c.execute("SELECT state FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
    return bool(r and r["state"] == "human_claimed")


def pancake_claim_human(pancake_conv_id):
    """Sale gắn thẻ 'Người xử lý' → bot rút vĩnh viễn khỏi hội thoại này.
    Hội thoại chưa từng qua bot (chưa có row) vẫn phải nhớ được → upsert."""
    with _conn() as c:
        r = c.execute("SELECT 1 FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
        if r:
            c.execute("UPDATE pancake_map SET state='human_claimed' WHERE pancake_conv_id=?",
                      (pancake_conv_id,))
        else:
            c.execute("INSERT INTO pancake_map(pancake_conv_id,local_conv_id,customer,state,returned_level,ts)"
                      " VALUES(?,?,?,?,?,?)",
                      (pancake_conv_id, "", "", "human_claimed", 0, time.time()))


def pancake_mark_returned(pancake_conv_id, level):
    with _conn() as c:
        c.execute("UPDATE pancake_map SET state='returned', returned_level=? WHERE pancake_conv_id=?",
                  (level, pancake_conv_id))


def pancake_is_blocked(pancake_conv_id) -> bool:
    """Quy tắc 7.3: bot KHÔNG trả lời khi hội thoại đã trả về người (returned)
    hoặc sale đã tiếp quản (human_claimed)."""
    with _conn() as c:
        r = c.execute("SELECT state FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
    return bool(r and r["state"] in ("returned", "human_claimed"))


def pancake_mark_test(pancake_conv_id):
    """Hội thoại THỬ NỘI BỘ (khách nhắn kèm mã test): bot được gửi thật kể cả ở chế độ test-only.
    MIỄN TRỪ A/B: luôn ép về nhóm bot + loại khỏi số liệu (contaminated). Đồng thời MỞ KHOÁ:
    nhắn lại mã test là hội thoại quay về tay bot kể cả đang human_claimed/returned
    (lỗi 25/08: redeploy làm bot nhận nhầm echo của mình là sale → tự rút, kẹt vĩnh viễn)."""
    with _conn() as c:
        r = c.execute("SELECT 1 FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
        if r:
            c.execute("UPDATE pancake_map SET is_test=1, ab_group='bot', state='bot_active',"
                      " returned_level=0 WHERE pancake_conv_id=?", (pancake_conv_id,))
        else:
            c.execute("INSERT INTO pancake_map(pancake_conv_id,local_conv_id,customer,state,"
                      "returned_level,ts,ab_group,is_test) VALUES(?,?,?,?,?,?,'bot',1)",
                      (pancake_conv_id, "", "", "bot_active", 0, time.time()))
        c.execute("UPDATE ab_stats SET contaminated=1, grp='bot' WHERE pancake_conv_id=?",
                  (pancake_conv_id,))


def pancake_release(pancake_conv_id):
    """Admin thả hội thoại về tay bot (gỡ human_claimed/returned nhầm)."""
    with _conn() as c:
        c.execute("UPDATE pancake_map SET state='bot_active', returned_level=0"
                  " WHERE pancake_conv_id=?", (pancake_conv_id,))


def pancake_bot_sent_recent(pancake_conv_id, hours=24):
    """Nội dung các tin assistant gần đây của hội thoại pancake này — đối chiếu để nhận diện
    echo tin bot sau khi redeploy (bộ nhớ RAM _sent bị xoá, không được nhận nhầm là sale gõ tay)."""
    with _conn() as c:
        r = c.execute("SELECT local_conv_id FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
        if not r or not r["local_conv_id"]:
            return []
        rows = c.execute(
            "SELECT content FROM messages WHERE conv_id=? AND role='assistant' AND ts>?"
            " ORDER BY ts DESC LIMIT 10",
            (r["local_conv_id"], time.time() - hours * 3600)).fetchall()
    return [x["content"] or "" for x in rows]


def pancake_is_test(pancake_conv_id) -> bool:
    with _conn() as c:
        r = c.execute("SELECT is_test FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
    return bool(r and r["is_test"])


def pancake_conv_of_local(local_conv_id):
    with _conn() as c:
        r = c.execute("SELECT pancake_conv_id FROM pancake_map WHERE local_conv_id=?",
                      (local_conv_id,)).fetchone()
    return r["pancake_conv_id"] if r else None


def pancake_overview(limit=200):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM pancake_map ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()]


# ---- Settings (kill switch / bật gửi thật — đổi được từ admin, không cần redeploy) ----
def get_setting(key, default=None):
    with _conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def set_setting(key, value):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO settings VALUES(?,?,?)", (key, str(value), time.time()))


# ---- Bảng lead SĐT (rule S2/S3: SĐT là lưới đỡ ở mọi cửa thoát) ----
def add_lead(conv_id, source, phone, context="") -> str:
    """Ghi SĐT khách để sale gọi lại — kèm ngữ cảnh (lý do rời / sản phẩm quan tâm).
    Chống trùng: cùng conv_id + phone chỉ ghi 1 lần."""
    with _conn() as c:
        r = c.execute("SELECT id FROM leads WHERE conv_id=? AND phone=?",
                      (conv_id, phone)).fetchone()
        if r:
            return r["id"]
        lid = uuid.uuid4().hex[:12]
        c.execute("INSERT INTO leads VALUES(?,?,?,?,?,?)",
                  (lid, conv_id, source, (phone or "")[:20], (context or "")[:300], time.time()))
    return lid


def list_leads(limit=1000):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM leads ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()]


# ---- A/B test: chia nhóm bot/người theo hash customer_id (bền vững, khách quay lại giữ nhóm) ----
def pancake_ab_group(pancake_conv_id, customer=None, percent=100) -> str:
    """Trả 'bot' hoặc 'human'. Nhóm gán 1 lần rồi giữ nguyên (kể cả đổi percent giữa chừng)."""
    import zlib
    with _conn() as c:
        r = c.execute("SELECT ab_group FROM pancake_map WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
        if r and r["ab_group"]:
            return r["ab_group"]
        key = str(customer or pancake_conv_id)
        grp = "bot" if (zlib.crc32(key.encode("utf-8")) % 100) < int(percent) else "human"
        if r:
            c.execute("UPDATE pancake_map SET ab_group=? WHERE pancake_conv_id=?",
                      (grp, pancake_conv_id))
        else:
            c.execute("INSERT INTO pancake_map(pancake_conv_id,local_conv_id,customer,state,"
                      "returned_level,ts,ab_group) VALUES(?,?,?,?,?,?,?)",
                      (pancake_conv_id, "", str(customer or ""), "bot_active", 0, time.time(), grp))
        return grp


def ab_in(pancake_conv_id, grp, has_phone=False) -> bool:
    """Ghi 1 tin KHÁCH gửi vào. Trả True nếu đây là tin đầu tiên (hội thoại mới với A/B)."""
    now = time.time()
    with _conn() as c:
        r = c.execute("SELECT msgs, phone FROM ab_stats WHERE pancake_conv_id=?",
                      (pancake_conv_id,)).fetchone()
        if r:
            c.execute("UPDATE ab_stats SET msgs=msgs+1, phone=MAX(phone,?) WHERE pancake_conv_id=?",
                      (1 if has_phone else 0, pancake_conv_id))
            return False
        c.execute("INSERT INTO ab_stats(pancake_conv_id,grp,first_in_ts,first_reply_ts,msgs,"
                  "replies,phone,contaminated,ts) VALUES(?,?,?,NULL,1,0,?,0,?)",
                  (pancake_conv_id, grp, now, 1 if has_phone else 0, now))
        return True


def ab_reply(pancake_conv_id, n=1):
    """Ghi lượt trả lời đầu ra (bot gửi thật, hoặc sale nhắn ở nhóm người).
    Chỉ đo hội thoại đã bắt đầu sau khi A/B bật (không có row thì bỏ qua)."""
    now = time.time()
    with _conn() as c:
        c.execute("UPDATE ab_stats SET replies=replies+?, "
                  "first_reply_ts=COALESCE(first_reply_ts,?) WHERE pancake_conv_id=?",
                  (n, now, pancake_conv_id))


def ab_contaminate(pancake_conv_id):
    """Sale nhắn tay vào ca nhóm bot → ca lai tạp, loại khỏi số liệu so sánh."""
    with _conn() as c:
        c.execute("UPDATE ab_stats SET contaminated=1 WHERE pancake_conv_id=?", (pancake_conv_id,))


def ab_report() -> dict:
    """So sánh 2 nhóm: số hội thoại, % được trả lời, trung vị thời gian phản hồi đầu,
    % có SĐT, số ca lai tạp (bị loại). Tính trên ca sạch (contaminated=0)."""
    with _conn() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM ab_stats").fetchall()]
    out = {}
    for grp in ("bot", "human"):
        g = [r for r in rows if r["grp"] == grp]
        clean = [r for r in g if not r["contaminated"]]
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
        }
    return out


# ---- SLA (mục 7.4): ca pancake mở + quá hạn theo level ----
SLA_MINUTES = {1: 30, 2: 15, 3: 10, 4: 3}


def pancake_open_handoffs():
    """Ca chuyển người nguồn pancake còn mở — cho SLA watcher."""
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM handoffs WHERE status='open' AND tester='pancake' ORDER BY ts",
        ).fetchall()]


def mark_sla_pinged(hid):
    with _conn() as c:
        c.execute("UPDATE handoffs SET sla_pinged=1 WHERE id=?", (hid,))


def pancake_daily_report(days=7):
    """Báo cáo nhanh cuối ngày (nấc B1): hội thoại, tin bot, đầu ra theo level, lead, fallback."""
    import datetime
    out = []
    with _conn() as c:
        rows = c.execute("""
            SELECT date(m.ts, 'unixepoch', '+7 hours') d,
                   COUNT(DISTINCT m.conv_id) convs,
                   SUM(CASE WHEN m.role='assistant' THEN 1 ELSE 0 END) bot_msgs,
                   SUM(CASE WHEN m.role='assistant' AND m.is_fallback=1 THEN 1 ELSE 0 END) fallbacks
            FROM messages m JOIN conversations v ON v.id=m.conv_id
            WHERE v.tester LIKE 'pancake:%'
            GROUP BY d ORDER BY d DESC LIMIT ?""", (days,)).fetchall()
        ho = c.execute("""
            SELECT date(ts, 'unixepoch', '+7 hours') d, level, COUNT(*) n,
                   SUM(sla_pinged) overdue
            FROM handoffs WHERE tester='pancake'
            GROUP BY d, level""").fetchall()
        ld = c.execute("""
            SELECT date(ts, 'unixepoch', '+7 hours') d, COUNT(*) n FROM leads
            GROUP BY d""").fetchall()
    ho_map, ld_map = {}, {r["d"]: r["n"] for r in ld}
    for r in ho:
        ho_map.setdefault(r["d"], {})[r["level"]] = {"n": r["n"], "overdue": r["overdue"] or 0}
    for r in rows:
        out.append({"date": r["d"], "conversations": r["convs"], "bot_messages": r["bot_msgs"],
                    "fallbacks": r["fallbacks"], "handoffs": ho_map.get(r["d"], {}),
                    "leads": ld_map.get(r["d"], 0)})
    return out


def log_webhook(event_type, result):
    with _conn() as c:
        c.execute("INSERT INTO webhook_log(event_type,result,ts) VALUES(?,?,?)",
                  (event_type, str(result)[:1000], time.time()))


def webhook_recent(limit=50):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM webhook_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]


def recent_suggestion_count(tester, seconds=600) -> int:
    """Chống spam: đếm số góp ý của một người test trong N giây gần nhất."""
    with _conn() as c:
        r = c.execute("SELECT COUNT(*) n FROM suggestions WHERE tester=? AND ts>?",
                      (tester, time.time() - seconds)).fetchone()
    return r["n"]


def list_suggestions(conv_id=None, limit=1000):
    q = "SELECT * FROM suggestions"
    args = ()
    if conv_id:
        q += " WHERE conv_id=?"
        args = (conv_id,)
    q += " ORDER BY ts DESC LIMIT ?"
    with _conn() as c:
        return [dict(r) for r in c.execute(q, args + (limit,)).fetchall()]


def list_conversations(tester=None):
    q = """SELECT v.id, v.tester, v.started_at, v.model,
             (SELECT COUNT(*) FROM messages m WHERE m.conv_id=v.id) AS n_messages,
             (SELECT COUNT(*) FROM feedback f WHERE f.conv_id=v.id AND f.rating='down') AS n_down,
             (SELECT COUNT(*) FROM feedback f WHERE f.conv_id=v.id AND f.rating='up') AS n_up,
             (SELECT COUNT(*) FROM suggestions s WHERE s.conv_id=v.id) AS n_suggest,
             (SELECT COUNT(*) FROM handoffs h WHERE h.conv_id=v.id AND h.status='open') AS n_handoff
           FROM conversations v"""
    args = ()
    if tester:
        q += " WHERE v.tester LIKE ?"
        args = (f"%{tester}%",)
    q += " ORDER BY v.started_at DESC LIMIT 500"
    with _conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def get_messages(conv_id):
    with _conn() as c:
        rows = c.execute("""
            SELECT m.*, f.rating, f.note FROM messages m
            LEFT JOIN feedback f ON f.message_id = m.id
            WHERE m.conv_id=? ORDER BY m.ts""", (conv_id,)).fetchall()
    return [dict(r) for r in rows]


def export_rows():
    with _conn() as c:
        rows = c.execute("""
            SELECT v.tester, m.conv_id, m.role, m.content, m.ts, m.latency_ms, m.model,
                   f.rating, f.note
            FROM messages m
            JOIN conversations v ON v.id = m.conv_id
            LEFT JOIN feedback f ON f.message_id = m.id
            ORDER BY v.started_at DESC, m.ts""").fetchall()
    return [dict(r) for r in rows]


def stats():
    with _conn() as c:
        n_conv = c.execute("SELECT COUNT(*) n FROM conversations").fetchone()["n"]
        n_msg = c.execute("SELECT COUNT(*) n FROM messages WHERE role='assistant'").fetchone()["n"]
        fb = c.execute("SELECT rating, COUNT(*) n FROM feedback GROUP BY rating").fetchall()
        lat = c.execute("SELECT AVG(latency_ms) a FROM messages WHERE latency_ms IS NOT NULL").fetchone()["a"]
        n_sug = c.execute("SELECT COUNT(*) n FROM suggestions").fetchone()["n"]
        n_ho = c.execute("SELECT COUNT(*) n FROM handoffs WHERE status='open'").fetchone()["n"]
    fbm = {r["rating"]: r["n"] for r in fb}
    return {"conversations": n_conv, "bot_messages": n_msg,
            "up": fbm.get("up", 0), "down": fbm.get("down", 0),
            "suggestions": n_sug, "handoffs_open": n_ho,
            "avg_latency_ms": int(lat) if lat is not None else None}
