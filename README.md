# Shaxsiy sayt

Portfolio + Uzum Market savdo statistikasi. Python aiohttp, SQLite, Chart.js.

## Tuzilma

- `content/profile.json` — ism, matn, botlar, saytlar, aloqa. Kontentni shu yerda o'zgartiring.
- `uzum.py` — Uzum ma'lumotlari: Excel import, API sinxronlash, statistika.
- `server.py` — web server (`/`, `/api/profile`, `/api/uzum`).
- `static/` — sahifa (HTML/CSS/JS).
- `data/uzum.db` — buyurtmalar bazasi (gitga kirmaydi).

Saytga faqat umumlashtirilgan raqamlar chiqadi (oylik summa, soni, top mahsulotlar). Buyurtma raqamlari chiqmaydi.

## Ishga tushirish

```bash
pip install -r requirements.txt
copy .env.example .env
python server.py
```

## Uzum ma'lumotlari

Faqat Seller API dan: `.env` da `UZUM_SHOPS=58457,95546` va har do'kon uchun `UZUM_TOKEN_<id>=...`.
Server har `UZUM_FAST_SECONDS` (60) sekundda oxirgi `UZUM_FAST_DAYS` (10) kunni, har `UZUM_FULL_MINUTES` (30) daqiqada butun tarixni yangilaydi. Qo'lda: `python server.py sync`.

Uzum Cloudflare'i AWS IP larini bloklaydi (HTTP 400). Shuning uchun serverda so'rovlar O'zbekistondagi hostingga qo'yilgan `proxy/uzum-proxy.php` orqali o'tadi: `UZUM_PROXY_URL=https://.../uzum-proxy.php`, `UZUM_PROXY_KEY` = PHP fayldagi `PROXY_KEY`.

## TSUE bot statistikasi

`tsue.py` bot bazasini (`TSUE_DB`, konteynerda `/tsue/bot_data.db`, read-only) o'qiydi, faqat sonlarni chiqaradi.

## Server (AWS EC2)

Docker konteyner `sayt`, port `127.0.0.1:8300`, Caddy: `https://karimovsherali.uz`.

Redeploy:

```bash
tar czf sayt.tgz Dockerfile .dockerignore requirements.txt server.py uzum.py tsue.py content static
scp -i ~/.ssh/darsreja-key.pem sayt.tgz ubuntu@52.58.206.125:/tmp/
ssh -i ~/.ssh/darsreja-key.pem ubuntu@52.58.206.125
sudo tar xzf /tmp/sayt.tgz -C /opt/sayt/src
cd /opt/sayt/src && sudo docker build -t sayt:latest .
sudo docker rm -f sayt
sudo docker run -d --name sayt --restart unless-stopped --memory 300m \
  --env-file /opt/sayt/.env -v /opt/sayt/data:/app/data -v /opt/tsuebot/data:/tsue:ro \
  -p 127.0.0.1:8300:8080 sayt:latest
```
