const $ = (s) => document.querySelector(s);
const MONTHS = ["yan", "fev", "mar", "apr", "may", "iyun", "iyul", "avg", "sen", "okt", "noy", "dek"];
const POLL_MS = 30000;
const SLIDE_MS = 3500;

const num = (n) => Math.round(n || 0).toLocaleString("ru-RU").replace(/[\s,]/g, " ");
const som = (n) => num(n) + " so'm";
const mln = (n) => ((n || 0) / 1e6).toFixed(n >= 1e8 ? 0 : 1).replace(".", ",") + " mln";
const monthLabel = (m) => MONTHS[+m.slice(5, 7) - 1] + " " + m.slice(2, 4);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const getJSON = async (u) => (await fetch(u, { cache: "no-store" })).json();

let profile = {};
let uzum = null;
let tsueStats = null;
let reviewsData = {};
let quizStats = null;
let shop = "all";
const charts = {};

// ---------------------------------------------------------------- profil

async function loadProfile() {
  profile = await getJSON("/api/profile");
  document.title = profile.name;
  $("#name").textContent = profile.name;
  $("#footName").textContent = profile.name;
  $("#year").textContent = new Date().getFullYear();
  $("#title").textContent = profile.title;
  $("#location").textContent = profile.location || "";
  $("#aboutText").textContent = profile.about;
  $("#avatar").textContent = profile.name.split(" ").map((w) => w[0]).join("").slice(0, 2);
  if (profile.photo) {
    $("#photo").src = profile.photo;
    $("#photo").hidden = false;
    $("#avatar").hidden = true;
  }
  const e = (profile.education || [])[0];
  if (e) {
    $("#education").innerHTML = `<span class="badge">Hozir o'qiyman</span>
      <b>${esc(e.place)}</b><span>${[e.degree, e.field, e.years].filter(Boolean).map(esc).join(" · ")}</span>`;
  }
  $("#skills").innerHTML = (profile.skills || []).map((s) => `<span class="chip">${esc(s)}</span>`).join("");
  const contacts = (profile.contacts || []).filter((c) => c.url);
  const ext = (c) => (c.url.startsWith("http") ? ' target="_blank" rel="noopener"' : "");
  const ico = (c) => `<span class="soc-ico ${esc(c.type)}"><i style="--icon:url(/static/img/icons/${esc(c.type)}.svg)"></i></span>`;
  $("#contacts").innerHTML = contacts.map((c) => `
    <a class="soc-tile" href="${esc(c.url)}"${ext(c)}>${ico(c)}<span><b>${esc(c.label)}</b><small>${esc(c.handle)}</small></span></a>`).join("");
  const row = contacts.map((c) => `<a href="${esc(c.url)}"${ext(c)} title="${esc(c.label)}" aria-label="${esc(c.label)}">${ico(c)}</a>`).join("");
  $("#heroSocial").innerHTML = row;
  $("#footSocial").innerHTML = row;
  renderCarousel();
  renderHeroStats();
}

// ---------------------------------------------------------------- loyihalar karuseli

function liveText(p) {
  if (p.live === "quiz" && quizStats) {
    return `${num(quizStats.total.users)} foydalanuvchi · ${num(quizStats.total.quizzes)} ta test`;
  }
  if (p.live === "tsue" && tsueStats) {
    return `${num(tsueStats.users)} foydalanuvchi · bugun ${num(tsueStats.requests_today)} so'rov`;
  }
  if (p.live?.startsWith("uzum:") && uzum) {
    const v = uzum.views[p.live.slice(5)];
    if (v) return `${num(v.total.sold)} dona sotildi · bugun ${num(v.total.today)} buyurtma`;
  }
  return "";
}

function renderCarousel() {
  $("#carousel").innerHTML = (profile.projects || []).map((p, i) => `
    <button class="pcard" data-i="${i}">
      ${p.cover ? `<div class="cover${p.gallery === "products" ? " products" : ""}">${
        p.gallery === "products"
          ? p.images.slice(0, 3).map((im) => `<img src="${esc(im.src)}" alt="" loading="lazy">`).join("")
          : `<img src="${esc(p.cover)}" alt="${esc(p.name)}" loading="lazy">`}</div>` : ""}
      <div class="body">
        <span class="type">${esc(p.type)}</span>
        <h3>${esc(p.name)}</h3>
        <p>${esc(p.short)}</p>
        <span class="stat" data-live="${i}">${esc(liveText(p))}</span>
        <span class="more">Batafsil →</span>
      </div>
    </button>`).join("");
}

function updateLiveStats() {
  document.querySelectorAll("[data-live]").forEach((el) => {
    el.textContent = liveText(profile.projects[+el.dataset.live]);
  });
}

const carousel = $("#carousel");
let paused = false;
let resumeAt = 0;

function step(dir) {
  const card = carousel.querySelector(".pcard");
  if (!card) return;
  const w = card.offsetWidth + 16;
  const max = carousel.scrollWidth - carousel.clientWidth;
  if (dir > 0 && carousel.scrollLeft >= max - 5) carousel.scrollTo({ left: 0 });
  else if (dir < 0 && carousel.scrollLeft <= 5) carousel.scrollTo({ left: max });
  else carousel.scrollBy({ left: dir * w });
}

function manual(dir) {
  step(dir);
  resumeAt = Date.now() + 8000; // qo'lda surilgandan keyin biroz kutadi
}

$("#next").addEventListener("click", () => manual(1));
$("#prev").addEventListener("click", () => manual(-1));
carousel.addEventListener("mouseenter", () => { paused = true; });
carousel.addEventListener("mouseleave", () => { paused = false; });
carousel.addEventListener("touchstart", () => { resumeAt = Date.now() + 8000; }, { passive: true });
setInterval(() => {
  if (!paused && !document.hidden && !$("#modal").open && Date.now() > resumeAt) step(1);
}, SLIDE_MS);

// ---------------------------------------------------------------- batafsil oyna

let openedProject = null;

function openProject(p) {
  openedProject = p;
  const stats = p.live === "tsue" ? tsueStats : p.live === "quiz" ? quizStats
    : p.live?.startsWith("uzum:") ? uzum?.views[p.live.slice(5)] : null;
  $("#modal").classList.toggle("wide", !!stats);
  const imgs = p.images || [];
  const gallery = !imgs.length ? "" : p.gallery === "products"
    ? `<div class="m-products">${imgs.map((im) => `<img src="${esc(im.src)}" alt="">`).join("")}</div>`
    : `<figure class="m-main"><img id="mMainImg" src="${esc(imgs[0].src)}" alt=""><figcaption id="mMainCap">${esc(imgs[0].caption)}</figcaption></figure>
       ${imgs.length > 1 ? `<div class="m-thumbs">${imgs.map((im, i) => `<button class="${i ? "" : "on"}" data-src="${esc(im.src)}" data-cap="${esc(im.caption)}"><img src="${esc(im.src)}" alt=""></button>`).join("")}</div>` : ""}`;
  $("#modalBody").innerHTML = `
    <span class="m-type">${esc(p.type)}</span>
    <h2>${esc(p.name)}</h2>
    ${p.url ? `<a class="handle" href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.handle || p.url)} ↗</a>` : ""}
    ${gallery}
    ${p.live?.startsWith("uzum:") ? reviewsHtml(p.live.slice(5)) : ""}
    ${p.highlights?.length ? `<div class="m-highlights">${p.highlights.map((h) => `<div><b>${esc(h.value)}</b><span>${esc(h.label)}</span></div>`).join("")}</div>` : ""}
    <p class="m-desc">${esc(p.description)}</p>
    ${p.designs?.length ? `<h3>${p.designs.length} ta tayyor dizayn</h3>
      <div class="m-designs">${p.designs.map((x) => `
        <button data-src="${esc(x.src)}" data-cap="${esc(x.name)}"><img src="${esc(x.src)}" alt="" loading="lazy"><span>${esc(x.name)}</span></button>`).join("")}</div>` : ""}
    ${p.features?.length ? `<h3>Imkoniyatlari</h3><ul class="m-features">${p.features.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}
    <div class="chips">${(p.tags || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("")}</div>
    ${p.url ? `<a class="btn" href="${esc(p.url)}" target="_blank" rel="noopener">Ochish</a>` : ""}
    ${stats ? `<div class="stats" id="mStats"></div>` : ""}`;
  if (p.live === "tsue" && stats) renderTsue();
  if (p.live === "quiz" && stats) renderQuiz();
  if (p.live?.startsWith("uzum:") && stats) { shop = p.live.slice(5); renderUzum(); }
  if (!$("#modal").open) $("#modal").showModal();
}

const stars = (n) => `<span class="stars" style="--r:${n}">★★★★★</span>`;

function reviewsHtml(shopId) {
  const r = reviewsData[shopId];
  if (!r || !r.count) return "";
  const max = Math.max(...Object.values(r.dist));
  return `
    <div class="reviews">
      <div class="rv-summary">
        <div class="rv-avg"><b>${String(r.avg).replace(".", ",")}</b>${stars(r.avg)}<span class="cnt">${num(r.count)} ta sharh</span></div>
        <div class="rv-dist">${Object.entries(r.dist).sort((a, b) => b[0] - a[0]).map(([k, v]) => `
          <div><span>${k} ★</span><i><em style="width:${max ? (100 * v) / max : 0}%"></em></i><small>${num(v)}</small></div>`).join("")}</div>
      </div>
      <h3>Mijozlar fikri</h3>
      <div class="rv-list">${r.items.map((v) => `
        <article class="rv">
          <header><b>${esc(v.customer)}</b>${stars(v.rating)}<time>${esc(v.date.split("-").reverse().join("."))}</time></header>
          ${v.content ? `<p>${esc(v.content)}</p>` : ""}
          ${v.pros ? `<p class="pros"><span>Afzalliklari:</span> ${esc(v.pros)}</p>` : ""}
          ${v.photos.length ? `<div class="rv-photos">${v.photos.map((u) => `<img src="${esc(u)}" alt="" loading="lazy">`).join("")}</div>` : ""}
          <small class="rv-product">${esc(v.product)}</small>
          ${v.reply ? `<div class="rv-reply"><b>Do'kon javobi</b>${esc(v.reply)}</div>` : ""}
        </article>`).join("")}</div>
    </div>`;
}

function closeModal() {
  $("#modal").close();
}

$("#modal").addEventListener("close", () => {
  openedProject = null;
  for (const id of Object.keys(charts)) { charts[id].destroy(); delete charts[id]; }
});

carousel.addEventListener("click", (e) => {
  const c = e.target.closest(".pcard");
  if (c) openProject(profile.projects[+c.dataset.i]);
});
$("#modalClose").addEventListener("click", closeModal);
$("#modalBody").addEventListener("click", (e) => {
  const t = e.target.closest(".m-thumbs button, .m-designs button");
  if (!t) return;
  if (t.closest(".m-designs")) $(".m-main").scrollIntoView({ behavior: "smooth", block: "center" });
  $("#mMainImg").src = t.dataset.src;
  $("#mMainCap").textContent = t.dataset.cap;
  document.querySelectorAll(".m-thumbs button").forEach((b) => b.classList.toggle("on", b === t));
});
$("#modal").addEventListener("click", (e) => { if (e.target === $("#modal")) closeModal(); }); // fon bosilsa

// ---------------------------------------------------------------- umumiy

function renderHeroStats() {
  const all = uzum?.views?.all?.total;
  $("#heroStats").innerHTML = [
    [num((profile.projects || []).filter((p) => p.type !== "Uzum do'kon").length), "loyiha"],
    [tsueStats || quizStats ? num((tsueStats?.users || 0) + (quizStats?.total.users || 0)) : "—", "bot foydalanuvchisi"],
    [all ? num(all.sold) : "—", "Uzumda sotilgan"],
    [all ? mln(all.revenue) : "—", "so'm savdo"],
  ].map(([v, l]) => `<div><b>${v}</b><span>${l}</span></div>`).join("");
}

function renderKpis(box, items) {
  if (box.children.length !== items.length) {
    box.innerHTML = items.map(() => `<div class="kpi"><span></span><b></b><small></small></div>`).join("");
  }
  items.forEach(([label, value, sub], i) => {
    const k = box.children[i];
    const b = k.querySelector("b");
    k.querySelector("span").textContent = label;
    k.querySelector("small").textContent = sub || "";
    if (b.textContent && b.textContent !== value) {
      b.classList.remove("bump");
      void b.offsetWidth;
      b.classList.add("bump");
    }
    b.textContent = value;
  });
}

function chart(id, config) {
  if (charts[id]) {
    charts[id].data = config.data;
    charts[id].update("none");
  } else {
    charts[id] = new Chart($(id), config);
  }
}

function themeColors() {
  const css = getComputedStyle(document.documentElement);
  const c = (v) => css.getPropertyValue(v).trim();
  Chart.defaults.color = c("--muted");
  Chart.defaults.borderColor = c("--border");
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  return { accent: c("--accent"), good: c("--good"), muted: "#c3cad8", danger: c("--danger") };
}

const baseOptions = {
  responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
  plugins: { legend: { display: false } },
  interaction: { mode: "index", intersect: false },
  scales: { x: { grid: { display: false } } },
};

// ---------------------------------------------------------------- Uzum

function renderUzum() {
  const box = $("#mStats");
  const v = uzum?.views[shop];
  if (!box || !v) return;
  if (!$("#kpis")) {
    box.innerHTML = `
      <div class="section-head"><h3>Savdo natijalari</h3><span class="live small"><i></i><span id="uzumLive">jonli</span></span></div>
      <p class="muted small" id="uzumPeriod"></p>
      <div class="kpis" id="kpis"></div>
      <div class="card"><div class="card-head"><h3>Oylik daromad</h3><div class="legend">
        <span><i class="sw sw-rev"></i>Tushum</span><span><i class="sw sw-net"></i>Qo'limga tushgan</span></div></div>
        <div class="chart-box"><canvas id="revChart"></canvas></div></div>
      <div class="card"><h3>Oylik buyurtmalar</h3><div class="chart-box"><canvas id="ordChart"></canvas></div></div>
      <div class="two">
        <div class="card"><h3>Eng ko'p sotilgan mahsulotlar</h3><ol class="top" id="topProducts"></ol></div>
        <div class="card"><h3>Har oy bo'yicha</h3><div class="table-wrap"><table id="monthTable">
          <thead><tr><th>Oy</th><th>Buyurtma</th><th>Sotildi</th><th>Bekor</th><th>Tushum</th><th>Qo'limga</th></tr></thead>
          <tbody></tbody></table></div></div>
      </div>
      <p class="muted small" id="uzumNote"></p>`;
  }
  const t = v.total;
  const months = v.months;
  const col = themeColors();
  const thisMonth = new Date().toISOString().slice(0, 7);
  const done = months.filter((m) => m.month < thisMonth && m.net);
  const best = [...months].sort((a, b) => (b.net || 0) - (a.net || 0))[0] || {};
  const avg = done.length ? done.reduce((a, m) => a + m.net, 0) / done.length : 0;

  $("#uzumPeriod").textContent = v.period.from
    ? `${monthLabel(v.period.from)} — hozirgacha · ${num(t.ordered)} ta buyurtma pozitsiyasi`
    : "";

  renderKpis($("#kpis"), [
    ["Buyurtmalar", num(t.active), `${num(t.sold)} yetkazildi · ${num(t.processing)} yo'lda`],
    ["Bugun", num((t.today || 0) - (t.today_cancelled || 0)), t.today_cancelled ? `${num(t.today_cancelled)} bekor qilindi` : "yangi buyurtma"],
    ["Bekor qilingan", num(t.cancelled), t.ordered ? `${(100 * t.cancelled / t.ordered).toFixed(1).replace(".", ",")}%` : ""],
    ["Jami tushum", mln(t.revenue), som(t.revenue)],
    ["Qo'limga tushgan", mln(t.net), "komissiya va logistikadan keyin"],
    ["Yo'ldagi pul", mln(t.pending_net), "yetkazilishi kutilmoqda"],
    ["O'rtacha oylik", mln(avg), "qo'limga tushgan"],
    ["Eng yaxshi oy", mln(best.net), best.month ? monthLabel(best.month) : ""],
  ]);

  const labels = months.map((m) => monthLabel(m.month));
  chart("#revChart", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Tushum", data: months.map((m) => m.revenue || 0), backgroundColor: col.accent, borderRadius: 4 },
        { label: "Qo'limga tushgan", data: months.map((m) => m.net || 0), backgroundColor: col.good, borderRadius: 4 },
      ],
    },
    options: {
      ...baseOptions,
      plugins: { ...baseOptions.plugins, tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${som(x.raw)}` } } },
      scales: { ...baseOptions.scales, y: { ticks: { callback: (val) => val / 1e6 + " mln" } } },
    },
  });
  chart("#ordChart", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Yetkazildi", data: months.map((m) => m.sold || 0), backgroundColor: col.good, stack: "a" },
        { label: "Yo'lda", data: months.map((m) => m.processing || 0), backgroundColor: col.muted, stack: "a" },
        { label: "Bekor qilindi", data: months.map((m) => m.cancelled || 0), backgroundColor: col.danger, stack: "a" },
      ],
    },
    options: { ...baseOptions, plugins: { legend: { display: true, position: "bottom", labels: { boxWidth: 10 } } } },
  });

  $("#topProducts").innerHTML = v.top_products.map((p) => `
    <li>${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : ""}
      <span class="t">${esc(p.title)}</span><b>${num(p.qty)} dona</b></li>`).join("");

  $("#monthTable tbody").innerHTML = [...months].reverse().map((m) => `
    <tr><td>${monthLabel(m.month)}</td><td>${num(m.ordered)}</td><td>${num(m.sold)}</td>
    <td>${num(m.cancelled)}</td><td>${num(m.revenue)}</td><td>${num(m.net)}</td></tr>`).join("");

  const sync = uzum.last_sync;
  $("#uzumLive").textContent = sync ? `jonli · ${sync.at.slice(11, 16)} da yangilandi` : "jonli";
  $("#uzumNote").textContent = "Ma'lumot Uzum Seller API dan har daqiqada olinadi. " +
    "\"Buyurtmalar\" — bekor qilinmagan buyurtmalar: yangi buyurtma tushsa +1, bekor bo'lsa −1.";
}

async function loadUzum() {
  uzum = await getJSON("/api/uzum");
}

// ---------------------------------------------------------------- TSUE bot

async function loadQuiz() {
  quizStats = await getJSON("/api/quizbot");
}

const dmy = (iso) => iso.split("-").reverse().join(".");

function renderQuiz() {
  const box = $("#mStats");
  const s = quizStats;
  if (!box || !s) return;
  const t = s.total;
  box.innerHTML = `
    <div class="section-head"><h3>Statistika — birinchi versiya</h3>
      <span class="muted small">${dmy(s.period.from)} — ${dmy(s.period.to)}</span></div>
    <div class="kpis" id="quizKpis"></div>
    <div class="card"><div class="card-head"><h3>Oylar bo'yicha</h3><div class="legend">
      <span><i class="sw sw-rev"></i>Daromad</span><span><i class="sw sw-net"></i>Yaratilgan testlar</span></div></div>
      <div class="chart-box"><canvas id="quizChart"></canvas></div></div>`;
  renderKpis($("#quizKpis"), [
    ["Foydalanuvchilar", num(t.users), `${num(t.active_creators)} tasi test yaratgan`],
    ["Yaratilgan testlar", num(t.quizzes), `${num(t.ai_quizzes)} tasi AI bilan`],
    ["Savollar", num(t.questions), "testlarga ajratilgan"],
    ["Daromad", som(t.revenue), `${num(t.payments)} ta to'lov · ${num(t.paying_users)} to'lovchi`],
    ["Referallar", num(t.referrals), "do'stini taklif qilgan"],
    ["Hamkorlar", num(t.partners), "partnyorlik dasturida"],
  ]);
  const col = themeColors();
  const ms = s.months;
  chart("#quizChart", {
    data: {
      labels: ms.map((m) => monthLabel(m.month)),
      datasets: [
        { type: "bar", label: "Daromad", data: ms.map((m) => m.revenue), backgroundColor: col.accent, borderRadius: 6, maxBarThickness: 56, yAxisID: "y" },
        { type: "line", label: "Testlar", data: ms.map((m) => m.quizzes), borderColor: col.good, backgroundColor: col.good, tension: .3, yAxisID: "y1" },
      ],
    },
    options: {
      ...baseOptions,
      plugins: { ...baseOptions.plugins, tooltip: { callbacks: { label: (x) => x.dataset.yAxisID === "y" ? `Daromad: ${som(x.raw)}` : `Testlar: ${num(x.raw)}` } } },
      scales: {
        ...baseOptions.scales,
        y: { position: "left", ticks: { callback: (v) => num(v) } },
        y1: { position: "right", grid: { display: false } },
      },
    },
  });
}

async function loadReviews() {
  reviewsData = await getJSON("/api/reviews");
}

async function loadTsue() {
  tsueStats = await getJSON("/api/tsue");
}

function renderTsue() {
  const box = $("#mStats");
  const s = tsueStats;
  if (!box || !s) return;
  if (!$("#tsueKpis")) {
    box.innerHTML = `
      <div class="section-head"><h3>Bot statistikasi</h3><span class="live small"><i></i>jonli</span></div>
      <div class="kpis" id="tsueKpis"></div>
      <div class="card"><h3>Har oy qo'shilgan foydalanuvchilar</h3><div class="chart-box"><canvas id="tsueChart"></canvas></div></div>`;
  }
  renderKpis($("#tsueKpis"), [
    ["Foydalanuvchilar", num(s.users), `${num(s.active_users)} faol (botni bloklamagan)`],
    ["Oxirgi 24 soat", num(s.active_24h), "foydalangan"],
    ["Oxirgi 7 kun", num(s.active_7d), `30 kun: ${num(s.active_30d)}`],
    ["Bugun yangi", num(s.new_today), "foydalanuvchi"],
    ["So'rovlar", num(s.requests), `bugun ${num(s.requests_today)}`],
    ["Guruhlar", num(s.groups), "jadval obunasi"],
    ...(s.rating ? [["Reyting", String(s.rating).replace(".", ","), `${num(s.ratings)} ta baho`]] : []),
  ]);
  const col = themeColors();
  chart("#tsueChart", {
    type: "bar",
    data: {
      labels: s.growth.map((g) => monthLabel(g.month)),
      datasets: [{ label: "Yangi foydalanuvchi", data: s.growth.map((g) => g.new), backgroundColor: col.accent, borderRadius: 6, maxBarThickness: 64 }],
    },
    options: baseOptions,
  });
}

// ---------------------------------------------------------------- bog'lanish formasi

const form = $("#contactForm");
const formStart = Date.now();
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = $("#formMsg");
  const data = Object.fromEntries(new FormData(form));
  data.consent = form.consent.checked;
  data.t = formStart;
  const btn = form.querySelector("button");
  btn.disabled = true;
  msg.className = "form-msg";
  msg.textContent = "Yuborilmoqda…";
  try {
    const r = await fetch("/api/contact", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    const j = await r.json();
    if (j.ok) {
      form.reset();
      msg.textContent = "";
      form.hidden = true;
      $("#formDone").hidden = false;
    } else {
      msg.className = "form-msg err";
      msg.textContent = j.error || "Xatolik. Qayta urinib ko'ring.";
    }
  } catch {
    msg.className = "form-msg err";
    msg.textContent = "Internet bilan muammo. Qayta urinib ko'ring.";
  }
  btn.disabled = false;
});

$("#formAgain").addEventListener("click", () => {
  $("#formDone").hidden = true;
  form.hidden = false;
});

// ---------------------------------------------------------------- ishga tushirish

const safe = (f) => () => f().catch((e) => console.error(e));
async function refresh() {
  await Promise.all([safe(loadUzum)(), safe(loadTsue)()]);
  updateLiveStats();
  renderHeroStats();
  if (openedProject?.live === "tsue") renderTsue();
  if (openedProject?.live?.startsWith("uzum:")) renderUzum();
}
loadProfile().then(refresh);
safe(loadReviews)();
safe(loadQuiz)().then(() => { updateLiveStats(); renderHeroStats(); });
setInterval(() => { if (!document.hidden) refresh(); }, POLL_MS);
