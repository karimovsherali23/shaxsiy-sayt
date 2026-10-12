"""TSUE bot statistikasi: bot bazasini faqat o'qish rejimida ochadi, faqat sonlarni qaytaradi."""
import os
import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = os.getenv("TSUE_DB", "/tsue/bot_data.db")


def stats() -> dict | None:
    if not os.path.exists(DB_PATH):
        return None
    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5)
    try:
        q = lambda sql, *a: db.execute(sql, a).fetchone()[0] or 0  # noqa: E731
        # bot vaqtlarni UTC da saqlaydi (datetime.utcnow().isoformat)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        ago = lambda **kw: (now - timedelta(**kw)).isoformat(timespec="seconds")  # noqa: E731
        today_utc = (datetime.now(timezone(timedelta(hours=5))).replace(hour=0, minute=0, second=0, microsecond=0)
                     .astimezone(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds"))
        growth = db.execute(
            "SELECT substr(first_seen, 1, 7) m, COUNT(*) FROM users WHERE first_seen IS NOT NULL GROUP BY m ORDER BY m"
        ).fetchall()
        rating = db.execute("SELECT AVG(rating), COUNT(*) FROM ratings WHERE rating IS NOT NULL").fetchone()
        return {
            "users": q("SELECT COUNT(*) FROM users"),
            "active_users": q("SELECT COUNT(*) FROM users WHERE NOT is_blocked"),
            "active_24h": q("SELECT COUNT(*) FROM users WHERE last_seen >= ?", ago(hours=24)),
            "active_7d": q("SELECT COUNT(*) FROM users WHERE last_seen >= ?", ago(days=7)),
            "active_30d": q("SELECT COUNT(*) FROM users WHERE last_seen >= ?", ago(days=30)),
            "new_today": q("SELECT COUNT(*) FROM users WHERE first_seen >= ?", today_utc),
            "requests": q("SELECT COUNT(*) FROM events"),
            "requests_today": q("SELECT COUNT(*) FROM events WHERE created_at >= ?", today_utc),
            "groups": q("SELECT COUNT(*) FROM group_subscriptions WHERE is_active"),
            "rating": round(rating[0], 2) if rating[0] else None,
            "ratings": rating[1],
            "growth": [{"month": m, "new": n} for m, n in growth],
        }
    finally:
        db.close()
