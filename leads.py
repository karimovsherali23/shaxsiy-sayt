"""Saytdagi "Bog'lanish" formasi: arizani saqlash, Telegramga xabar, email javob."""
import asyncio
import html
import logging
import os
import re
import smtplib
import ssl
import time
from collections import defaultdict, deque
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

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
        "lang": str(data.get("lang") or "uz")[:2],
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


REPLY = {
    "uz": ("Arizangiz qabul qilindi",
           "Assalomu alaykum, {name}!",
           "Saytimdagi arizangiz qabul qilindi. Tez orada siz qoldirgan {phone} raqamiga qo'ng'iroq qilaman.",
           "Savolingiz bo'lsa, shu xatga javob yozishingiz mumkin.",
           "Hurmat bilan,"),
    "ru": ("Ваша заявка принята",
           "Здравствуйте, {name}!",
           "Ваша заявка на моём сайте принята. Скоро перезвоню на номер {phone}.",
           "Если есть вопросы, просто ответьте на это письмо.",
           "С уважением,"),
    "en": ("We've received your request",
           "Hello {name},",
           "Thank you for your request on my website. I'll call you soon at {phone}.",
           "If you have any questions, just reply to this email.",
           "Best regards,"),
}


def _smtp():
    ctx = ssl.create_default_context()  # sertifikat va host nomi tekshiriladi
    s = smtplib.SMTP_SSL(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "465")), timeout=25, context=ctx)
    s.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
    return s


def _html(lines: list[str], button: tuple[str, str] | None = None) -> str:
    e = html.escape
    body = "".join(f'<p style="margin:0 0 14px">{l}</p>' for l in lines)
    btn = (f'<p style="margin:22px 0"><a href="{e(button[1])}" style="background:#2563eb;color:#fff;'
           f'text-decoration:none;padding:12px 22px;border-radius:10px;font-weight:600">{e(button[0])}</a></p>') if button else ""
    return (f'<div style="background:#f6f8fc;padding:32px 12px;font-family:Arial,sans-serif">'
            f'<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;color:#0f1b33;font-size:15px;line-height:1.6">'
            f'<div style="font-weight:800;font-size:20px;margin-bottom:18px">karimovsherali<span style="color:#2563eb">.uz</span></div>'
            f'{body}{btn}</div></div>')


def _send_mail(lead: dict, lead_id: int):
    user = os.getenv("SMTP_USER", "").strip()
    if not os.getenv("SMTP_HOST") or not user:
        return
    site = os.getenv("SITE_URL", "").strip()
    e = html.escape
    msgs = []

    # 1) mijozga avto-javob
    if lead["email"]:
        subj, hello, text, more, bye = REPLY.get(lead.get("lang"), REPLY["uz"])
        m = EmailMessage()
        m["From"] = formataddr(("Sherali Karimov", user))
        m["To"] = lead["email"]
        m["Subject"] = subj
        m["Reply-To"] = user
        plain = [hello.format(name=lead["name"]), text.format(phone=lead["phone"]), more, f"{bye}\nSherali Karimov\n{site}"]
        m.set_content("\n\n".join(plain))
        m.add_alternative(_html([e(hello.format(name=lead["name"])), e(text.format(phone=lead["phone"])), e(more),
                                 f"{e(bye)}<br><b>Sherali Karimov</b>"], (site.replace("https://", ""), site) if site else None),
                          subtype="html")
        msgs.append(m)

    # 2) egasiga bildirishnoma: "Javob berish" to'g'ridan-to'g'ri mijozga ketadi
    notify = os.getenv("LEADS_NOTIFY_EMAIL", "").strip()
    if notify:
        tel = re.sub(r"[^\d+]", "", lead["phone"])
        m = EmailMessage()
        m["From"] = formataddr(("Sayt arizalari", user))
        m["To"] = notify
        m["Subject"] = f"Yangi ariza #{lead_id}: {lead['name']}, {lead['phone']}"
        if lead["email"]:
            m["Reply-To"] = lead["email"]
        rows = [f"Ism: {lead['name']}", f"Telefon: {lead['phone']}", f"Email: {lead['email'] or '—'}",
                f"Til: {lead.get('lang') or 'uz'}", f"Xabar: {lead['message'] or '—'}"]
        m.set_content("\n".join(rows))
        m.add_alternative(_html([f"<b>Saytdan yangi ariza #{lead_id}</b>"] +
                                [f"{e(r.split(': ', 1)[0])}: <b>{e(r.split(': ', 1)[1])}</b>" for r in rows],
                                ("Qo'ng'iroq qilish", f"tel:{tel}")), subtype="html")
        msgs.append(m)

    if msgs:
        with _smtp() as s:
            for m in msgs:
                s.send_message(m)


async def send_reply_email(lead: dict, lead_id: int = 0):
    try:
        await asyncio.to_thread(_send_mail, lead, lead_id)
    except Exception:
        log.exception("Email yuborilmadi")
