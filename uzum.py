"""Uzum Market savdo ma'lumotlari: Seller API dan sinxronlash, SQLite saqlash, statistika.

Har bir qator = buyurtma pozitsiyasi (orderItems[].id). Uzum maydonlari:
  amount         — sotilgan / kutilayotgan dona (bekor bo'lsa 0)
  amountReturns  — bekor qilingan yoki qaytarilgan dona
  sellerProfit   — sellPrice*amount - commission - logisticDeliveryFee
  status         — PROCESSING | TO_WITHDRAW | CANCELED
"""
import asyncio
import json
import logging
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import aiohttp

log = logging.getLogger("uzum")

TZ = timezone(timedelta(hours=5))  # Toshkent
DATA_DIR = os.getenv("DATA_DIR", "data")
DB_PATH = os.path.join(DATA_DIR, "uzum.db")
BASE_URL = os.getenv("UZUM_BASE_URL", "https://api-seller.uzum.uz/api/seller-openapi").rstrip("/")
PAGE_SIZE = 1000
# Uzum AWS IP larini bloklaydi: bo'lsa, so'rovlar O'zbekistondagi proxy/uzum-proxy.php orqali
PROXY_URL = os.getenv("UZUM_PROXY_URL", "").strip()
PROXY_KEY = os.getenv("UZUM_PROXY_KEY", "").strip()


def _request(session, path: str, token: str, params: dict | None = None):
    if PROXY_URL:
        return session.get(PROXY_URL, params={"path": path, **(params or {})},
                           headers={"X-Proxy-Key": PROXY_KEY, "X-Uzum-Token": token})
    return session.get(f"{BASE_URL}{path}", params=params, headers={"Authorization": token})

COLS = ("id", "shop_id", "order_id", "created", "status", "sku", "title", "image", "qty",
        "returns", "price", "commission", "logistics", "net", "cost", "product_id")


def shops_config() -> dict[str, str]:
    """UZUM_SHOPS=58457,95546 va UZUM_TOKEN_<id>=... dan {shop_id: token}."""
    ids = [s.strip() for s in os.getenv("UZUM_SHOPS", "").split(",") if s.strip()]
    return {i: os.getenv(f"UZUM_TOKEN_{i}", "").strip() for i in ids if os.getenv(f"UZUM_TOKEN_{i}")}


# ---------------------------------------------------------------- DB

def connect() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("DROP TABLE IF EXISTS orders")  # eski Excel importi
    db.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id         INTEGER PRIMARY KEY,  -- Uzum orderItems[].id
            shop_id    TEXT,
            order_id   INTEGER,
            created    TEXT,                 -- ISO, Toshkent vaqti
            status     TEXT,
            sku        TEXT,
            title      TEXT,
            image      TEXT,
            qty        INTEGER,
            returns    INTEGER,
            price      INTEGER,
            commission INTEGER,
            logistics  INTEGER,
            net        INTEGER,
            cost       INTEGER
        )""")
    if "product_id" not in {r["name"] for r in db.execute("PRAGMA table_info(items)")}:
        db.execute("ALTER TABLE items ADD COLUMN product_id INTEGER")
    db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id       INTEGER PRIMARY KEY,  -- Uzum payments[].id
            shop_id  TEXT,
            date     TEXT,                 -- xizmat sanasi, Toshkent vaqti
            source   TEXT,                 -- Ombor | Marketing | Logistika | ...
            code     TEXT,
            name     TEXT,
            amount   INTEGER,              -- so'm; daromad (INCOME) manfiy
            status   TEXT
        )""")
    db.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    return db


def set_meta(db, k, v):
    db.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (k, json.dumps(v, ensure_ascii=False)))
    db.commit()


def get_meta(db, k, default=None):
    row = db.execute("SELECT v FROM meta WHERE k = ?", (k,)).fetchone()
    return json.loads(row["v"]) if row else default


# ---------------------------------------------------------------- API

def _row(o: dict) -> tuple:
    photo = ((o.get("productImage") or {}).get("photo") or {}).get("240") or {}
    return (
        o["id"], str(o.get("shopId")), o.get("orderId"),
        datetime.fromtimestamp(o["date"] / 1000, TZ).replace(tzinfo=None).isoformat(timespec="seconds"),
        o.get("status") or "", o.get("skuTitle") or "", o.get("productTitle") or "",
        photo.get("low") or "", o.get("amount") or 0, o.get("amountReturns") or 0,
        o.get("sellPrice") or 0, o.get("commission") or 0, o.get("logisticDeliveryFee") or 0,
        o.get("sellerProfit") or 0, (o.get("purchasePrice") or 0) * (o.get("amount") or 0),
        o.get("productId"),
    )


async def _fetch_shop(session, shop_id: str, token: str, days: int | None) -> list[tuple]:
    params = {"group": "false", "size": PAGE_SIZE, "shopIds": shop_id}
    if days:
        now = int(time.time() * 1000)
        params.update(dateFrom=now - days * 86_400_000, dateTo=now + 3_600_000)
    rows, page = [], 0
    while page < 500:
        for attempt in range(6):
            async with _request(session, "/v1/finance/orders", token, {**params, "page": page}) as r:
                if r.status == 429:  # Uzum so'rov limiti
                    await asyncio.sleep(float(r.headers.get("Retry-After") or 0) or 2 * (attempt + 1))
                    continue
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status} {(await r.text())[:150]}")
                items = (await r.json()).get("orderItems") or []
                break
        else:
            raise RuntimeError("HTTP 429: limit, keyinroq")
        await asyncio.sleep(0.5)
        # token boshqa do'konlarga ham kirsa ham, faqat shu do'kon
        rows += [_row(o) for o in items if str(o.get("shopId")) == shop_id]
        if len(items) < PAGE_SIZE:
            break
        page += 1
    return rows


async def _fetch_shop_names(session, shops: dict[str, str]) -> dict[str, str]:
    names = {}
    for token in set(shops.values()):
        async with _request(session, "/v1/shops", token) as r:
            if r.status == 200:
                names.update({str(s["id"]): s["name"] for s in await r.json()})
    return {i: names[i] for i in shops if i in names}


TAX_RATE = float(os.getenv("UZUM_TAX_RATE", "0.01"))  # aylanmadan soliq


def expense_row(e: dict) -> tuple:
    sign = -1 if e.get("type") == "INCOME" else 1
    ts = e.get("dateService") or e.get("dateCreated") or 0
    return (e["id"], str(e.get("shopId")),
            datetime.fromtimestamp(ts / 1000, TZ).replace(tzinfo=None).isoformat(timespec="seconds"),
            e.get("source") or "", e.get("code") or "", (e.get("name") or "")[:200],
            sign * (e.get("paymentPrice") or 0) * (e.get("amount") or 1), e.get("status") or "")


async def _fetch_expenses(session, db, shop_id: str, token: str) -> int:
    """Eng yangisidan boshlab o'qiydi; butun sahifa bazada bo'lsa to'xtaydi."""
    known = {r[0] for r in db.execute("SELECT id FROM expenses WHERE shop_id = ?", (shop_id,))}
    added, page = 0, 0
    while page < 500:
        for attempt in range(6):
            async with _request(session, "/v1/finance/expenses", token,
                                {"page": page, "size": 100, "shopIds": shop_id}) as r:
                if r.status == 429:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                if r.status != 200:
                    raise RuntimeError(f"expenses HTTP {r.status}")
                items = ((await r.json()).get("payload") or {}).get("payments") or []
                break
        else:
            raise RuntimeError("expenses HTTP 429")
        rows = [expense_row(e) for e in items if str(e.get("shopId")) == shop_id]
        new = [x for x in rows if x[0] not in known]
        db.executemany("INSERT OR REPLACE INTO expenses VALUES (?,?,?,?,?,?,?,?)", rows)
        db.commit()
        added += len(new)
        if len(items) < 100 or (known and not new):
            break
        page += 1
        await asyncio.sleep(0.4)
    return added


async def sync(full: bool) -> str:
    """full=True — butun tarix; aks holda oxirgi UZUM_FAST_DAYS kun (yangi va bekor bo'lganlar)."""
    shops = shops_config()
    if not shops:
        return "UZUM_SHOPS / UZUM_TOKEN_<id> berilmagan"
    days = None if full else int(os.getenv("UZUM_FAST_DAYS", "10"))
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (shaxsiy-sayt)"}  # UA siz Cloudflare 403
    db = connect()
    msgs, ok = [], True
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as s:
        if full or not get_meta(db, "shops"):
            names = await _fetch_shop_names(s, shops)
            if names:
                set_meta(db, "shops", {**get_meta(db, "shops", {}), **names})
        for shop_id, token in shops.items():
            try:
                rows = await _fetch_shop(s, shop_id, token, days)
            except Exception as e:
                msgs.append(f"{shop_id}: XATO {e!r}"[:200])
                ok = False
                continue
            db.executemany(f"INSERT OR REPLACE INTO items ({','.join(COLS)}) VALUES ({','.join('?' * len(COLS))})", rows)
            db.commit()
            msgs.append(f"{shop_id}: {len(rows)}")
            if full:
                try:
                    msgs.append(f"xarajat +{await _fetch_expenses(s, db, shop_id, token)}")
                except Exception as e:
                    msgs.append(f"xarajat XATO {e!r}"[:120])
    set_meta(db, "last_sync", {"at": datetime.now(TZ).isoformat(timespec="seconds"), "ok": ok,
                               "full": full, "result": "; ".join(msgs)})
    return ("full " if full else "fast ") + "; ".join(msgs)


# ---------------------------------------------------------------- statistika (ommaviy)

def _empty_view():
    return {"total": defaultdict(int), "months": defaultdict(lambda: defaultdict(int)),
            "products": {}, "first": None, "last": None}


def stats() -> dict:
    db = connect()
    shops = get_meta(db, "shops", {})
    views = defaultdict(_empty_view)
    today = datetime.now(TZ).strftime("%Y-%m-%d")

    for r in db.execute("SELECT * FROM items ORDER BY created"):
        for v in (views["all"], views[r["shop_id"]]):
            t, m = v["total"], v["months"][r["created"][:7]]
            v["first"] = v["first"] or r["created"]
            v["last"] = r["created"]
            ordered = r["qty"] + r["returns"]
            add = {"ordered": ordered}
            if r["status"] == "CANCELED":
                add["cancelled"] = r["returns"]
            else:
                add["returns"] = r["returns"]
                if r["status"] == "TO_WITHDRAW":
                    add.update(sold=r["qty"], revenue=r["price"] * r["qty"], net=r["net"],
                               commission=r["commission"], logistics=r["logistics"],
                               profit=r["net"] - r["cost"])
                else:
                    add.update(processing=r["qty"], pending_net=r["net"])
            if r["created"][:10] == today:
                add["today"] = ordered
                if r["status"] == "CANCELED":
                    add["today_cancelled"] = r["returns"]
            for k, val in add.items():
                t[k] += val
                m[k] += val
            if r["status"] == "TO_WITHDRAW" and r["qty"]:
                p = v["products"].setdefault(r["title"] or r["sku"],
                                             {"title": r["title"] or r["sku"], "image": r["image"], "qty": 0, "revenue": 0})
                p["qty"] += r["qty"]
                p["revenue"] += r["price"] * r["qty"]

    # Uzum xarajatlari: logistika sellerProfit ichida allaqachon ayirilgan, qolganlari bu yerda
    cat = {"Ombor": "storage", "Marketing": "marketing", "Logistika": None}
    for r in db.execute("SELECT shop_id, date, source, amount FROM expenses WHERE status = 'CONFIRMED'"):
        key = cat.get(r["source"], "other")
        if key is None:
            continue
        for v in (views["all"], views[r["shop_id"]]):
            v["total"][key] += r["amount"]
            v["months"][r["date"][:7]][key] += r["amount"]

    out = {}
    for key, v in views.items():
        for t in [v["total"], *v["months"].values()]:
            t["tax"] = round(t["revenue"] * TAX_RATE)
            t["payout"] = t["net"] - t["storage"] - t["marketing"] - t["other"] - t["tax"]
        t = v["total"]
        # faol buyurtmalar: yangi buyurtma +1, bekor bo'lsa -1
        t["active"] = t["ordered"] - t["cancelled"] - t["returns"]
        out[key] = {
            "total": dict(t),
            "months": [{"month": k, **m} for k, m in sorted(v["months"].items())],
            "top_products": sorted(v["products"].values(), key=lambda p: p["qty"], reverse=True)[:10],
            "period": {"from": v["first"], "to": v["last"]},
        }
    return {
        "shops": [{"id": i, "name": n} for i, n in shops.items() if i in out],
        "views": out,
        "last_sync": get_meta(db, "last_sync"),
    }
