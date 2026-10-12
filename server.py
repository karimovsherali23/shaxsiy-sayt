"""Shaxsiy sayt: portfolio + jonli Uzum savdo va TSUE bot statistikasi."""
import asyncio
import base64
import hmac
import json
import logging
import os
import sys
import time
from pathlib import Path

from aiohttp import web

ROOT = Path(__file__).parent


def load_env(path=ROOT / ".env"):
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()
import analytics  # noqa: E402  (.env o'qilgandan keyin)
import leads  # noqa: E402
import reviews  # noqa: E402
import tsue  # noqa: E402
import uzum  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
log = logging.getLogger("site")

# statistika har sinxrondan keyin qayta hisoblanadi, so'rovlar keshdan oladi
_cache = {"uzum": None, "tsue": None, "tsue_at": 0.0, "reviews": None}


async def refresh_uzum():
    _cache["uzum"] = await asyncio.to_thread(uzum.stats)


async def get_tsue():
    if time.time() - _cache["tsue_at"] > 30:
        try:
            _cache["tsue"] = await asyncio.to_thread(tsue.stats)
        except Exception:
            log.exception("TSUE statistikasi o'qilmadi")
        _cache["tsue_at"] = time.time()
    return _cache["tsue"]


NO_CACHE = {"Cache-Control": "no-store"}


async def api_profile(request):
    lang = request.query.get("lang", "uz")
    f = ROOT / "content" / (f"profile.{lang}.json" if lang in ("ru", "en") else "profile.json")
    if not f.exists():
        f = ROOT / "content" / "profile.json"
    return web.json_response(json.loads(f.read_text(encoding="utf-8")))


async def api_uzum(_):
    if _cache["uzum"] is None:
        await refresh_uzum()
    return web.json_response(_cache["uzum"], headers=NO_CACHE)


async def api_contact(request):
    ip = _client_ip(request)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri so'rov"}, status=400)
    lead, err = leads.validate(data)
    if err == "spam":
        return web.json_response({"ok": True})  # botga xato aytmaymiz
    lang = str(data.get("lang") or "uz")
    if err:
        return web.json_response({"ok": False, "error": leads.msg(err, lang)}, status=400)
    if leads.rate_limited(ip):
        return web.json_response({"ok": False, "error": leads.msg("rate", lang)}, status=429)
    lead_id = await asyncio.to_thread(leads.save, lead, ip)
    asyncio.create_task(leads.notify_telegram(lead, lead_id))
    asyncio.create_task(leads.send_reply_email(lead, lead_id))
    return web.json_response({"ok": True})


def _client_ip(request) -> str:
    return request.headers.get("X-Forwarded-For", request.remote or "").split(",")[0].strip()


async def api_hit(request):
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=204)
    await asyncio.to_thread(analytics.record, data, _client_ip(request),
                            request.headers.get("User-Agent", ""), request.host.split(":")[0])
    return web.Response(status=204)


def _admin_ok(request) -> bool:
    password = os.getenv("ADMIN_PASSWORD", "")
    if not password:
        return False
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        user, _, pwd = base64.b64decode(auth[6:]).decode().partition(":")
    except Exception:
        return False
    return hmac.compare_digest(user, os.getenv("ADMIN_USER", "admin")) and hmac.compare_digest(pwd, password)


def _need_auth():
    return web.Response(status=401, text="Login kerak", headers={"WWW-Authenticate": 'Basic realm="admin", charset="UTF-8"'})


async def admin_page(request):
    if not _admin_ok(request):
        return _need_auth()
    return web.FileResponse(ROOT / "static" / "admin.html", headers=NO_CACHE)


async def admin_stats(request):
    if not _admin_ok(request):
        return _need_auth()
    days = max(1, min(int(request.query.get("days", "30") or 30), 365))
    data = await asyncio.to_thread(analytics.stats, days)
    return web.json_response(data, headers=NO_CACHE)


async def api_quizbot(_):
    return web.FileResponse(ROOT / "content" / "quizbot_v1.json", headers={"Cache-Control": "public, max-age=3600"})


async def api_tsue(_):
    return web.json_response(await get_tsue(), headers=NO_CACHE)


async def api_reviews(_):
    if _cache["reviews"] is None:
        _cache["reviews"] = await asyncio.to_thread(reviews.stats)
    return web.json_response(_cache["reviews"], headers={"Cache-Control": "public, max-age=600"})


async def reviews_loop(app):
    hours = float(os.getenv("REVIEWS_HOURS", "6"))
    while True:
        try:
            log.info("Sharhlar: %s", await reviews.refresh())
            _cache["reviews"] = await asyncio.to_thread(reviews.stats)
        except Exception:
            log.exception("Sharhlarni yangilashda xato")
        await asyncio.sleep(hours * 3600)


def _asset_version() -> str:
    # CSS/JS o'zgarsa versiya o'zgaradi: brauzer eski keshni ishlatmaydi
    st = ROOT / "static"
    return str(int(max((st / f).stat().st_mtime for f in ("style.css", "app.js", "i18n.js"))))


async def index(_):
    v = _asset_version()
    page = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    page = page.replace("/static/style.css", f"/static/style.css?v={v}").replace("/static/app.js", f"/static/app.js?v={v}").replace("/static/i18n.js", f"/static/i18n.js?v={v}")
    return web.Response(text=page, content_type="text/html", headers=NO_CACHE)


async def sync_loop(app):
    fast = int(os.getenv("UZUM_FAST_SECONDS", "60"))
    full_every = int(os.getenv("UZUM_FULL_MINUTES", "30")) * 60
    last_full = 0.0
    while True:
        full = time.time() - last_full >= full_every
        try:
            log.info("Uzum sync %s", await uzum.sync(full=full))
            if full:
                last_full = time.time()
            await refresh_uzum()
        except Exception:
            log.exception("Uzum sync xatosi")
        await asyncio.sleep(fast)


async def on_startup(app):
    app["sync"] = asyncio.create_task(sync_loop(app))
    app["reviews"] = asyncio.create_task(reviews_loop(app))


async def on_cleanup(app):
    app["sync"].cancel()
    app["reviews"].cancel()


def make_app():
    app = web.Application(client_max_size=64 * 1024)
    app.router.add_get("/", index)
    app.router.add_get("/api/profile", api_profile)
    app.router.add_get("/api/uzum", api_uzum)
    app.router.add_get("/api/tsue", api_tsue)
    app.router.add_get("/api/reviews", api_reviews)
    app.router.add_get("/api/quizbot", api_quizbot)
    app.router.add_post("/api/contact", api_contact)
    app.router.add_post("/api/hit", api_hit)
    app.router.add_get("/admin", admin_page)
    app.router.add_get("/admin/api/stats", admin_stats)
    app.router.add_static("/static", ROOT / "static")
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    if sys.argv[1:] == ["sync"]:
        print(asyncio.run(uzum.sync(full=True)))
    elif sys.argv[1:] == ["reviews"]:
        print(asyncio.run(reviews.refresh()))
    else:
        web.run_app(make_app(), host=os.getenv("WEB_HOST", "127.0.0.1"),
                    port=int(os.getenv("WEB_PORT", "8080")), access_log=None)
