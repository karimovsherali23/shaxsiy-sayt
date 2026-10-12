"""Uzum mahsulot sharhlari: ochiq api.uzum.uz dan (seller API sharh bermaydi).

Bitta so'rov mahsulotning barcha sharhlarini qaytaradi (page/size e'tiborga olinmaydi).
Har do'konning eng ko'p sotilgan mahsulotlari bo'yicha yig'iladi.
"""
import asyncio
import json
import logging
from collections import Counter
from datetime import datetime

import aiohttp

import uzum

log = logging.getLogger("reviews")

API = "https://api.uzum.uz/api/product/{}/reviews"
TOP_PRODUCTS = 40


def _db():
    db = uzum.connect()
    db.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id         INTEGER PRIMARY KEY,  -- reviewId
            shop_id    TEXT,
            product_id INTEGER,
            product    TEXT,
            date       TEXT,
            customer   TEXT,
            rating     INTEGER,
            content    TEXT,
            pros       TEXT,
            cons       TEXT,
            reply      TEXT,
            photos     TEXT                  -- JSON ro'yxat
        )""")
    return db


ANON = {"безымянный", "anonim", "аноним", "noma'lum"}


def _name(v: dict) -> str:
    n = (v.get("customer") or "").strip()
    return "" if v.get("isAnonymous") or n.lower() in ANON else n.title()


def _photo(p: dict) -> str:
    ph = p.get("photo") or {}
    return (ph.get("540") or ph.get("240") or {}).get("low") or ""


async def refresh() -> str:
    db = _db()
    products = db.execute(f"""
        SELECT shop_id, product_id, MAX(title) title, SUM(qty) q FROM items
        WHERE product_id IS NOT NULL AND status = 'TO_WITHDRAW'
        GROUP BY shop_id, product_id ORDER BY q DESC""").fetchall()
    per_shop = Counter()
    picked = []
    for r in products:
        if per_shop[r["shop_id"]] < TOP_PRODUCTS:
            per_shop[r["shop_id"]] += 1
            picked.append(r)
    if not picked:
        return "mahsulotlar yo'q (product_id hali yuklanmagan)"

    rows = []
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (shaxsiy-sayt)"},
                                     timeout=aiohttp.ClientTimeout(total=60)) as s:
        for r in picked:
            try:
                async with s.get(API.format(r["product_id"]), params={"page": 0, "size": 50}) as resp:
                    if resp.status != 200:
                        continue
                    items = (await resp.json()).get("payload") or []
            except Exception as e:
                log.warning("sharh %s: %r", r["product_id"], e)
                continue
            for v in items:
                if v.get("status") != "PUBLISHED":
                    continue
                reply = (v.get("reply") or {}).get("content") or ""
                rows.append((
                    v["reviewId"], r["shop_id"], r["product_id"], r["title"],
                    datetime.fromtimestamp(v["date"] / 1000).strftime("%Y-%m-%d"),
                    _name(v),
                    v.get("rating") or 0, (v.get("content") or "").strip(), (v.get("pros") or "").strip(),
                    (v.get("cons") or "").strip(), reply.strip(),
                    json.dumps([u for u in map(_photo, v.get("photos") or []) if u]),
                ))
            await asyncio.sleep(0.3)
    db.executemany(f"INSERT OR REPLACE INTO reviews VALUES ({','.join('?' * 12)})", rows)
    db.commit()
    return f"{len(rows)} sharh, {len(picked)} mahsulot"


def _meaningful(text: str) -> bool:
    t = (text or "").lower().strip(" .!")
    return len(t) >= 12 and t not in {"yo'q", "yoq", "нет", "-"}


def stats() -> dict:
    db = _db()
    out = {}
    for shop in [r[0] for r in db.execute("SELECT DISTINCT shop_id FROM reviews")]:
        rows = db.execute("SELECT * FROM reviews WHERE shop_id = ? ORDER BY date DESC", (shop,)).fetchall()
        dist = Counter(r["rating"] for r in rows)
        # ko'rsatish uchun: matnli, 4-5 yulduzli, eng yangilari; rasmlilar oldinda
        good = [r for r in rows if r["rating"] >= 4 and (_meaningful(r["content"]) or _meaningful(r["pros"]))]
        good.sort(key=lambda r: (r["photos"] != "[]", r["date"]), reverse=True)
        out[shop] = {
            "count": len(rows),
            "avg": round(sum(r["rating"] for r in rows) / len(rows), 2) if rows else None,
            "dist": {str(k): dist.get(k, 0) for k in range(5, 0, -1)},
            "items": [{
                "customer": r["customer"] or "Xaridor", "rating": r["rating"], "date": r["date"],
                "product": r["product"], "content": r["content"], "pros": r["pros"],
                "reply": r["reply"], "photos": json.loads(r["photos"])[:3],
            } for r in good[:24]],
        }
    return out
