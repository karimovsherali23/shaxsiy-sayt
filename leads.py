"""Saytdagi "Bog'lanish" formasi: arizani saqlash, Telegramga xabar, email javob."""
import asyncio
import html
import logging
import os
import re
import smtplib
import time
from collections import defaultdict, deque
from datetime import datetime
from email.message import EmailMessage

import aiohttp

import uzum

log = logging.getLogger("leads")

PHONE_RE = re.compile(r"^\+?[\d\s\-()]{9,20}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[a-z]{2,}$", re.I)
_hits: dict[str, deque] = defaultdict(deque)
RATE = 3            # bir IP dan
RATE_WINDOW = 3600  # soatiga


def _db():
    db = uzum.connect()
    db.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT,
            name    TEXT,
            phone   TEXT,
            email   TEXT,
            message TEXT,
            ip      TEXT
        )""")
    return db


MSG = {
    "name": {"uz": "Ismingizni yozing", "ru": "Укажите имя", "en": "Please enter your name"},
    "phone": {"uz": "Telefon raqamini to'g'ri yozing", "ru": "Укажите корректный номер телефона", "en": "Please enter a valid phone number"},
    "email": {"uz": "Email noto'g'ri", "ru": "Некорректный email", "en": "Invalid email"},
    "consent": {"uz": "Bog'lanishga rozilik belgisini qo'ying", "ru": "Отметьте согласие на связь", "en": "Please tick the consent box"},
    "rate": {"uz": "Juda ko'p urinish. Keyinroq qayta yozing.", "ru": "Слишком много попыток. Попробуйте позже.", "en": "Too many attempts. Please try later."},
}


def msg(key: str, lang: str) -> str:
    return MSG[key].get(lang, MSG[key]["uz"])


def validate(data: dict) -> tuple[dict | None, str]:
    if data.get("website"):  # yashirin maydon: odam to'ldirmaydi, bot to'ldiradi
        return None, "spam"
    try:
        if time.time() * 1000 - float(data.get("t") or 0) < 3000:  # 3 soniyadan tez = bot
            return None, "spam"
    except ValueError:
        return None, "spam"
    lead = {
        "name": str(data.get("name") or "").strip()[:80],
        "phone": str(data.get("phone") or "").strip()[:20],
        "email": str(data.get("email") or "").strip()[:254],
        "message": str(data.get("message") or "").strip()[:2000],
    }
    if len(lead["name"]) < 2:
        return None, "name"
    if not PHONE_RE.match(lead["phone"]) or len(re.sub(r"\D", "", lead["phone"])) < 9:
        return None, "phone"
    if lead["email"] and not EMAIL_RE.match(lead["email"]):
        return None, "email"
    if not data.get("consent"):
        return None, "consent"
    return lead, ""


def rate_limited(ip: str) -> bool:
    q = _hits[ip]
    now = time.time()
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE:
        return True
    q.append(now)
    return False


def save(lead: dict, ip: str) -> int:
    db = _db()
    cur = db.execute(
        "INSERT INTO leads (created, name, phone, email, message, ip) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now(uzum.TZ).isoformat(timespec="seconds"), lead["name"], lead["phone"],
         lead["email"], lead["message"], ip))
    db.commit()
    return cur.lastrowid


async def notify_telegram(lead: dict, lead_id: int):
    token = os.getenv("LEADS_BOT_TOKEN", "").strip()
    chat = os.getenv("LEADS_CHAT_ID", "").strip()
    if not token or not chat:
        log.info("Telegram sozlanmagan, ariza #%s faqat bazada", lead_id)
        return
    e = html.escape
    tel = re.sub(r"[^\d+]", "", lead["phone"])
    text = (f"<b>Saytdan yangi ariza #{lead_id}</b>\n\n"
            f"Ism: {e(lead['name'])}\nTelefon: <a href=\"tel:{e(tel)}\">{e(lead['phone'])}</a>\n"
            + (f"Email: {e(lead['email'])}\n" if lead["email"] else "")
            + (f"\n{e(lead['message'])}" if lead["message"] else ""))
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
        async with s.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": text, "parse_mode": "HTML"}) as r:
            if r.status != 200:
                log.warning("Telegramga yuborilmadi: %s %s", r.status, (await r.text())[:200])


def _send_mail(lead: dict):
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    if not host or not user or not lead["email"]:
        return
    msg = EmailMessage()
    msg["From"] = f"Sherali Karimov <{user}>"
    msg["To"] = lead["email"]
    msg["Subject"] = "Arizangiz qabul qilindi"
    msg.set_content(
        f"Assalomu alaykum, {lead['name']}!\n\n"
        "Saytimdagi arizangiz qabul qilindi. Tez orada siz bilan bog'lanaman.\n\n"
        "Hurmat bilan,\nSherali Karimov\n" + os.getenv("SITE_URL", ""))
    with smtplib.SMTP_SSL(host, int(os.getenv("SMTP_PORT", "465")), timeout=20) as s:
        s.login(user, os.getenv("SMTP_PASSWORD", ""))
        s.send_message(msg)


async def send_reply_email(lead: dict):
    try:
        await asyncio.to_thread(_send_mail, lead)
    except Exception:
        log.exception("Email javob yuborilmadi")
