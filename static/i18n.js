// Interfeys tarjimalari: uz (asosiy), ru, en
const I18N = {
  uz: {
    "nav.about": "Men haqimda", "nav.edu": "Ta'lim", "nav.projects": "Loyihalar", "nav.contact": "Bog'lanish",
    "hero.hello": "Salom, men", "hero.projects": "Loyihalarim", "hero.contact": "Bog'lanish",
    "about.title": "Men haqimda", "edu.title": "Ta'lim", "edu.badge": "Hozir o'qiyman",
    "edu.c1": "Iqtisodiyot fakulteti", "edu.c2": "Ochiq osmon ostidagi muzey", "edu.c3": "Universitet binosi",
    "edu.credit": "Rasmlar: TSUE WikiClub (CC BY-SA 4.0), Bestalex (CC0) — Wikimedia Commons",
    "projects.title": "Loyihalarim", "projects.hint": "Batafsil ma'lumot va jonli statistika uchun kartani bosing",
    "projects.prev": "Oldingi", "projects.next": "Keyingi", "card.more": "Batafsil →",
    "hs.projects": "loyiha", "hs.botUsers": "bot foydalanuvchisi", "hs.sold": "Uzumda sotilgan", "hs.sales": "so'm savdo",
    "live.quiz": "{u} foydalanuvchi · {q} ta test", "live.tsue": "{u} foydalanuvchi · bugun {r} so'rov",
    "live.uzum": "{s} dona sotildi · bugun {t} buyurtma", "live": "jonli", "live.updated": "jonli · {t} da yangilandi",
    "m.open": "Ochish", "m.features": "Imkoniyatlari", "m.designs": "{n} ta tayyor dizayn", "m.close": "Yopish",
    "rv.count": "{n} ta sharh", "rv.title": "Mijozlar fikri", "rv.pros": "Afzalliklari:", "rv.reply": "Do'kon javobi", "rv.buyer": "Xaridor",
    "u.title": "Savdo natijalari", "u.period": "{from} — hozirgacha · {n} ta buyurtma pozitsiyasi",
    "u.orders": "Buyurtmalar", "u.ordersSub": "{s} yetkazildi · {p} yo'lda", "u.today": "Bugun",
    "u.todayCancel": "{n} bekor qilindi", "u.todayNew": "yangi buyurtma", "u.cancelled": "Bekor qilingan",
    "u.revenue": "Jami tushum", "u.net": "Qo'limga tushgan", "u.netSub": "komissiya va logistikadan keyin",
    "u.pending": "Yo'ldagi pul", "u.pendingSub": "yetkazilishi kutilmoqda", "u.avg": "O'rtacha oylik", "u.best": "Eng yaxshi oy",
    "u.monthRev": "Oylik daromad", "u.monthOrd": "Oylik buyurtmalar", "u.top": "Eng ko'p sotilgan mahsulotlar", "u.byMonth": "Har oy bo'yicha",
    "u.delivered": "Yetkazildi", "u.inTransit": "Yo'lda", "u.cancelledL": "Bekor qilindi",
    "u.th": ["Oy", "Buyurtma", "Sotildi", "Bekor", "Tushum", "Qo'limga"], "u.pcs": "dona",
    "u.note": "Ma'lumot Uzum Seller API dan har daqiqada olinadi. \"Buyurtmalar\" — bekor qilinmagan buyurtmalar: yangi buyurtma tushsa +1, bekor bo'lsa −1.",
    "q.title": "Statistika — birinchi versiya", "q.users": "Foydalanuvchilar", "q.usersSub": "{n} tasi test yaratgan",
    "q.tests": "Yaratilgan testlar", "q.testsSub": "{n} tasi AI bilan", "q.questions": "Savollar", "q.questionsSub": "testlarga ajratilgan",
    "q.revenue": "Daromad", "q.revenueSub": "{p} ta to'lov · {u} to'lovchi", "q.refs": "Referallar", "q.refsSub": "do'stini taklif qilgan",
    "q.partners": "Hamkorlar", "q.partnersSub": "partnyorlik dasturida", "q.byMonth": "Oylar bo'yicha", "q.testsL": "Yaratilgan testlar", "q.testsShort": "Testlar",
    "t.title": "Bot statistikasi", "t.users": "Foydalanuvchilar", "t.usersSub": "{n} faol (botni bloklamagan)",
    "t.d1": "Oxirgi 24 soat", "t.d1Sub": "foydalangan", "t.d7": "Oxirgi 7 kun", "t.d7Sub": "30 kun: {n}", "t.newToday": "Bugun yangi",
    "t.newTodaySub": "foydalanuvchi", "t.req": "So'rovlar", "t.reqSub": "bugun {n}", "t.groups": "Guruhlar", "t.groupsSub": "jadval obunasi",
    "t.rating": "Reyting", "t.ratingSub": "{n} ta baho", "t.growth": "Har oy qo'shilgan foydalanuvchilar", "t.newUser": "Yangi foydalanuvchi",
    "c.badge": "Bog'lanish", "c.title": "Keling, birga ishlaymiz",
    "c.text": "Telegram bot, sayt, Uzum do'koni yoki hamkorlik bo'yicha savolingiz bormi? Raqamingizni qoldiring — o'zim qo'ng'iroq qilaman.",
    "c.form": "Ariza qoldiring", "c.name": "Ismingiz", "c.phone": "Telefon raqam", "c.email": "Email (ixtiyoriy)",
    "c.msg": "Qisqacha nima haqida? (ixtiyoriy)", "c.consent": "Men bilan telefon yoki email orqali bog'lanishga roziman",
    "c.send": "Yuborish", "c.sending": "Yuborilmoqda…", "c.doneTitle": "Arizangiz qabul qilindi!",
    "c.doneText": "Rahmat. Tez orada siz qoldirgan raqamga qo'ng'iroq qilaman.", "c.again": "Yana yozish",
    "c.err": "Xatolik. Qayta urinib ko'ring.", "c.errNet": "Internet bilan muammo. Qayta urinib ko'ring.",
    "unit.som": "so'm", "unit.mln": "mln",
    "months": ["yan", "fev", "mar", "apr", "may", "iyun", "iyul", "avg", "sen", "okt", "noy", "dek"],
  },
  ru: {
    "nav.about": "Обо мне", "nav.edu": "Образование", "nav.projects": "Проекты", "nav.contact": "Связаться",
    "hero.hello": "Привет, я", "hero.projects": "Мои проекты", "hero.contact": "Связаться",
    "about.title": "Обо мне", "edu.title": "Образование", "edu.badge": "Сейчас учусь",
    "edu.c1": "Экономический факультет", "edu.c2": "Музей под открытым небом", "edu.c3": "Здание университета",
    "edu.credit": "Фото: TSUE WikiClub (CC BY-SA 4.0), Bestalex (CC0) — Wikimedia Commons",
    "projects.title": "Мои проекты", "projects.hint": "Нажмите на карточку, чтобы увидеть подробности и живую статистику",
    "projects.prev": "Назад", "projects.next": "Вперёд", "card.more": "Подробнее →",
    "hs.projects": "проекта", "hs.botUsers": "пользователей ботов", "hs.sold": "продано на Uzum", "hs.sales": "сум продаж",
    "live.quiz": "{u} пользователей · {q} тестов", "live.tsue": "{u} пользователей · сегодня {r} запросов",
    "live.uzum": "продано {s} шт · сегодня {t} заказов", "live": "онлайн", "live.updated": "онлайн · обновлено в {t}",
    "m.open": "Открыть", "m.features": "Возможности", "m.designs": "{n} готовых дизайнов", "m.close": "Закрыть",
    "rv.count": "{n} отзывов", "rv.title": "Отзывы покупателей", "rv.pros": "Достоинства:", "rv.reply": "Ответ магазина", "rv.buyer": "Покупатель",
    "u.title": "Результаты продаж", "u.period": "{from} — по сей день · {n} позиций заказов",
    "u.orders": "Заказы", "u.ordersSub": "{s} доставлено · {p} в пути", "u.today": "Сегодня",
    "u.todayCancel": "{n} отменено", "u.todayNew": "новых заказов", "u.cancelled": "Отменено",
    "u.revenue": "Выручка", "u.net": "Чистыми на руки", "u.netSub": "после комиссии и логистики",
    "u.pending": "Деньги в пути", "u.pendingSub": "ожидают доставки", "u.avg": "В среднем в месяц", "u.best": "Лучший месяц",
    "u.monthRev": "Доход по месяцам", "u.monthOrd": "Заказы по месяцам", "u.top": "Самые продаваемые товары", "u.byMonth": "По месяцам",
    "u.delivered": "Доставлено", "u.inTransit": "В пути", "u.cancelledL": "Отменено",
    "u.th": ["Месяц", "Заказы", "Продано", "Отмена", "Выручка", "На руки"], "u.pcs": "шт",
    "u.note": "Данные берутся из Uzum Seller API каждую минуту. «Заказы» — неотменённые заказы: новый заказ +1, отмена −1.",
    "q.title": "Статистика — первая версия", "q.users": "Пользователи", "q.usersSub": "{n} создали тесты",
    "q.tests": "Создано тестов", "q.testsSub": "{n} с помощью ИИ", "q.questions": "Вопросы", "q.questionsSub": "извлечено в тесты",
    "q.revenue": "Доход", "q.revenueSub": "{p} платежей · {u} плательщиков", "q.refs": "Рефералы", "q.refsSub": "пригласили друзей",
    "q.partners": "Партнёры", "q.partnersSub": "в партнёрской программе", "q.byMonth": "По месяцам", "q.testsL": "Создано тестов", "q.testsShort": "Тесты",
    "t.title": "Статистика бота", "t.users": "Пользователи", "t.usersSub": "{n} активных (не заблокировали бота)",
    "t.d1": "За 24 часа", "t.d1Sub": "пользовались", "t.d7": "За 7 дней", "t.d7Sub": "за 30 дней: {n}", "t.newToday": "Новых сегодня",
    "t.newTodaySub": "пользователей", "t.req": "Запросы", "t.reqSub": "сегодня {n}", "t.groups": "Группы", "t.groupsSub": "подписка на расписание",
    "t.rating": "Рейтинг", "t.ratingSub": "{n} оценок", "t.growth": "Новые пользователи по месяцам", "t.newUser": "Новые пользователи",
    "c.badge": "Связаться", "c.title": "Давайте работать вместе",
    "c.text": "Есть вопрос по Telegram-боту, сайту, магазину на Uzum или сотрудничеству? Оставьте номер — я сам перезвоню.",
    "c.form": "Оставить заявку", "c.name": "Ваше имя", "c.phone": "Номер телефона", "c.email": "Email (необязательно)",
    "c.msg": "Кратко о чём? (необязательно)", "c.consent": "Согласен(на), чтобы со мной связались по телефону или email",
    "c.send": "Отправить", "c.sending": "Отправка…", "c.doneTitle": "Заявка принята!",
    "c.doneText": "Спасибо. Скоро перезвоню на оставленный номер.", "c.again": "Написать ещё",
    "c.err": "Ошибка. Попробуйте ещё раз.", "c.errNet": "Проблема с интернетом. Попробуйте ещё раз.",
    "unit.som": "сум", "unit.mln": "млн",
    "months": ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
  },
  en: {
    "nav.about": "About", "nav.edu": "Education", "nav.projects": "Projects", "nav.contact": "Contact",
    "hero.hello": "Hi, I'm", "hero.projects": "My projects", "hero.contact": "Contact me",
    "about.title": "About me", "edu.title": "Education", "edu.badge": "Currently studying",
    "edu.c1": "Faculty of Economics", "edu.c2": "Open-air museum", "edu.c3": "University building",
    "edu.credit": "Photos: TSUE WikiClub (CC BY-SA 4.0), Bestalex (CC0) — Wikimedia Commons",
    "projects.title": "My projects", "projects.hint": "Tap a card for details and live statistics",
    "projects.prev": "Previous", "projects.next": "Next", "card.more": "Details →",
    "hs.projects": "projects", "hs.botUsers": "bot users", "hs.sold": "sold on Uzum", "hs.sales": "UZS in sales",
    "live.quiz": "{u} users · {q} tests", "live.tsue": "{u} users · {r} requests today",
    "live.uzum": "{s} items sold · {t} orders today", "live": "live", "live.updated": "live · updated at {t}",
    "m.open": "Open", "m.features": "Features", "m.designs": "{n} ready-made designs", "m.close": "Close",
    "rv.count": "{n} reviews", "rv.title": "Customer reviews", "rv.pros": "Pros:", "rv.reply": "Shop reply", "rv.buyer": "Customer",
    "u.title": "Sales results", "u.period": "{from} — today · {n} order items",
    "u.orders": "Orders", "u.ordersSub": "{s} delivered · {p} in transit", "u.today": "Today",
    "u.todayCancel": "{n} cancelled", "u.todayNew": "new orders", "u.cancelled": "Cancelled",
    "u.revenue": "Total revenue", "u.net": "Net payout", "u.netSub": "after commission and logistics",
    "u.pending": "Money in transit", "u.pendingSub": "awaiting delivery", "u.avg": "Monthly average", "u.best": "Best month",
    "u.monthRev": "Monthly income", "u.monthOrd": "Monthly orders", "u.top": "Best-selling products", "u.byMonth": "By month",
    "u.delivered": "Delivered", "u.inTransit": "In transit", "u.cancelledL": "Cancelled",
    "u.th": ["Month", "Orders", "Sold", "Cancelled", "Revenue", "Net"], "u.pcs": "pcs",
    "u.note": "Data comes from the Uzum Seller API every minute. \"Orders\" = non-cancelled orders: a new order adds 1, a cancellation subtracts 1.",
    "q.title": "Statistics — first version", "q.users": "Users", "q.usersSub": "{n} created tests",
    "q.tests": "Tests created", "q.testsSub": "{n} with AI", "q.questions": "Questions", "q.questionsSub": "extracted into tests",
    "q.revenue": "Revenue", "q.revenueSub": "{p} payments · {u} payers", "q.refs": "Referrals", "q.refsSub": "invited a friend",
    "q.partners": "Partners", "q.partnersSub": "in the partner program", "q.byMonth": "By month", "q.testsL": "Tests created", "q.testsShort": "Tests",
    "t.title": "Bot statistics", "t.users": "Users", "t.usersSub": "{n} active (haven't blocked the bot)",
    "t.d1": "Last 24 hours", "t.d1Sub": "active users", "t.d7": "Last 7 days", "t.d7Sub": "30 days: {n}", "t.newToday": "New today",
    "t.newTodaySub": "users", "t.req": "Requests", "t.reqSub": "today {n}", "t.groups": "Groups", "t.groupsSub": "timetable subscriptions",
    "t.rating": "Rating", "t.ratingSub": "{n} ratings", "t.growth": "New users per month", "t.newUser": "New users",
    "c.badge": "Contact", "c.title": "Let's work together",
    "c.text": "Have a question about a Telegram bot, a website, an Uzum store or a partnership? Leave your number and I'll call you back.",
    "c.form": "Send a request", "c.name": "Your name", "c.phone": "Phone number", "c.email": "Email (optional)",
    "c.msg": "What is it about? (optional)", "c.consent": "I agree to be contacted by phone or email",
    "c.send": "Send", "c.sending": "Sending…", "c.doneTitle": "Request received!",
    "c.doneText": "Thank you. I'll call the number you left soon.", "c.again": "Write again",
    "c.err": "Something went wrong. Please try again.", "c.errNet": "Connection problem. Please try again.",
    "unit.som": "UZS", "unit.mln": "M",
    "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  },
};

const LANGS = ["uz", "ru", "en"];

function detectLang() {
  try {
    const saved = localStorage.getItem("lang");
    if (LANGS.includes(saved)) return saved;
  } catch { /* xotira yopiq bo'lishi mumkin */ }
  const nav = (navigator.language || "").slice(0, 2);
  return nav === "ru" ? "ru" : nav === "en" ? "en" : "uz";
}

const LANG = detectLang();

function t(key, vars) {
  let s = (I18N[LANG] && I18N[LANG][key]) ?? I18N.uz[key] ?? key;
  if (vars && typeof s === "string") s = s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
  return s;
}

function setLang(l) {
  try { localStorage.setItem("lang", l); } catch { /* e'tiborsiz */ }
  location.reload();
}

// HTML dagi data-i18n (matn), data-i18n-ph (placeholder/label), data-i18n-aria
function applyStatic() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
  document.querySelectorAll(".lang-switch button").forEach((b) => b.classList.toggle("on", b.dataset.lang === LANG));
}
