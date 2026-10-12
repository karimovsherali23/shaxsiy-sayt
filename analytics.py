"""Saytga tashriflar statistikasi: tashqi xizmatsiz, IP saqlanmaydi.

Tashrifchi = sha256(kunlik tasodifiy tuz + IP + User-Agent) — bir kun ichida bir xil,
ertasi kuni boshqa, IP ni qayta tiklab bo'lmaydi.
"""
import hashlib
import json
import re
import secrets
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse

import uzum

BOT_RE = re.compile(r"bot|crawl|spider|slurp|headless|preview|facebookexternalhit|curl|wget|python|monitor", re.I)
EVENTS = {"view", "project", "lead"}
_salt = {"day": None, "value": ""}


def _db():
    db = uzum.connect()
    db.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            ts     TEXT,
            day    TEXT,
            vid    TEXT,     -- kunlik anonim tashrifchi kodi
            event  TEXT,     -- view | project | lead
            target TEXT,     -- loyiha id si
            ref    TEXT,     -- qaysi saytdan kelgan (faqat domen)
            device TEXT,     -- mobile | desktop
            lang   TEXT
        )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_visits_day ON visits(day)")
    return db


def _visitor(ip: str, ua: str, day: str) -> str:
    if _salt["day"] != day:
        _salt.update(day=day, value=secrets.token_hex(16))
    return hashlib.sha256(f"{_salt['value']}|{ip}|{ua}".encode()).hexdigest()[:16]


def record(data: dict, ip: str, ua: str, own_host: str) -> bool:
    if not ua or BOT_RE.search(ua):
        return False
    event = str(data.get("event") or "view")
    if event not in EVENTS:
        return False
    now = datetime.now(uzum.TZ)
    day = now.strftime("%Y-%m-%d")
    ref = urlparse(str(data.get("ref") or "")).hostname or ""
    if ref == own_host:
        ref = ""
    ref = ref.removeprefix("www.")[:80]
    device = "mobile" if re.search(r"Mobi|Android|iPhone|iPad", ua) else "desktop"
    db = _db()
    db.execute("INSERT INTO visits (ts, day, vid, event, target, ref, device, lang) VALUES (?,?,?,?,?,?,?,?)",
               (now.isoformat(timespec="seconds"), day, _visitor(ip, ua, day), event,
                str(data.get("target") or "")[:40], ref, device, str(data.get("lang") or "")[:5]))
    db.commit()
    return True


def stats(days: int = 30) -> dict:
    db = _db()
    since = (datetime.now(uzum.TZ) - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    today = datetime.now(uzum.TZ).strftime("%Y-%m-%d")
    rows = db.execute("SELECT day, vid, event, target, ref, device, lang FROM visits WHERE day >= ?", (since,)).fetchall()
    daily = {}
    for i in range(days):
        d = (datetime.now(uzum.TZ) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        daily[d] = {"views": 0, "visitors": set()}
    projects, refs, devices, langs = Counter(), Counter(), Counter(), Counter()
    first_by_visitor = {}
    for r in rows:
        if r["event"] == "view":
            daily[r["day"]]["views"] += 1
            daily[r["day"]]["visitors"].add(r["vid"])
            key = (r["day"], r["vid"])
            if key not in first_by_visitor:
                first_by_visitor[key] = r
        elif r["event"] == "project":
            projects[r["target"]] += 1
    for r in first_by_visitor.values():  # har tashrifchini bir marta sanaymiz
        refs[r["ref"] or "To'g'ridan-to'g'ri"] += 1
        devices[r["device"]] += 1
        langs[r["lang"] or "?"] += 1
    t = daily.get(today, {"views": 0, "visitors": set()})
    total_visitors = len(first_by_visitor)
    leads = db.execute("SELECT id, created, name, phone, email, message FROM leads ORDER BY id DESC LIMIT 50").fetchall() \
        if db.execute("SELECT name FROM sqlite_master WHERE name='leads'").fetchone() else []
    return {
        "today": {"views": t["views"], "visitors": len(t["visitors"])},
        "period": {"days": days, "views": sum(d["views"] for d in daily.values()), "visitors": total_visitors},
        "daily": [{"day": d, "views": v["views"], "visitors": len(v["visitors"])} for d, v in daily.items()],
        "projects": projects.most_common(),
        "refs": refs.most_common(10),
        "devices": devices.most_common(),
        "langs": langs.most_common(),
        "leads": [dict(r) for r in leads],
    }


def dumps(o) -> str:
    return json.dumps(o, ensure_ascii=False)
