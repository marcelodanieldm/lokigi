// Reviews en localStorage
let reviews = JSON.parse(localStorage.getItem("reviews") || "{}");
// marketplace.js
// Configura aquí la URL base de tu backend FastAPI
const API_BASE_URL = "http://localhost:8000";

// Traducciones
const translations = {
  es: {
    featured: "Apps Destacadas",
    install: "Instalar",
    installing: "Instalando app:",
    noApps: "No hay apps disponibles.",
    mySubs: "Mis Suscripciones",
    noSubs: "No tienes suscripciones.",
    details: "Detalles",
    close: "Cerrar",
    search: "Buscar apps...",
    allCategories: "Todas las categorías",
    allRatings: "Todas las valoraciones",
    fav: "Favorito",
    pay: "Pagar",
    paid: "Pagado",
    addFav: "Agregar a favoritos",
    removeFav: "Quitar de favoritos"
  },
  en: {
    featured: "Featured Apps",
    install: "Install",
    installing: "Installing app:",
    noApps: "No apps available.",
    mySubs: "My Subscriptions",
    noSubs: "No subscriptions.",
    details: "Details",
    close: "Close",
    search: "Search apps...",
    allCategories: "All categories",
    allRatings: "All ratings",
    fav: "Favorite",
    pay: "Pay",
    paid: "Paid",
    addFav: "Add to favorites",
    removeFav: "Remove from favorites"
  }
};

let currentLang = localStorage.getItem("lang") || "es";
let allApps = [];
let favorites = JSON.parse(localStorage.getItem("favorites") || "[]");
let paidApps = JSON.parse(localStorage.getItem("paidApps") || "[]");
let currentPage = 1;
const PAGE_SIZE = 6;

function t(key) {
  return translations[currentLang][key] || key;
}

async function fetchApps() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/apps`);
    if (!res.ok) throw new Error("Error al cargar apps");
    return await res.json();
  } catch (e) {
    console.error(e);
    return [];
  }
}

async function fetchSubs() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/user-subscriptions`);
    if (!res.ok) throw new Error("Error al cargar suscripciones");
    return await res.json();
  } catch (e) {
    console.error(e);
    return [];
  }
}

function renderAppCard(app) {
  const isFav = favorites.includes(app.id);
  const isPaid = paidApps.includes(app.id);
  const rating = app.rating || 0;
  const isFeatured = app.featured;
  return `
    <div class="col-md-4">
      <div class="card h-100 shadow position-relative">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">${app.name}</h5>
            ${isFeatured ? `<span class="badge bg-warning text-dark ms-2">Destacada</span>` : ""}
          </div>
          <p class="card-text">${app.description || ""}</p>
          <div class="mb-2">${renderStars(rating)}</div>
          <div class="d-flex gap-2 mb-2">
            <button class="btn btn-primary flex-fill" onclick="installApp('${app.id}')">
              <i class="bi bi-download"></i> ${t("install")}
            </button>
            <button class="btn btn-outline-light flex-fill" onclick="showAppDetail('${app.id}')">
              <i class="bi bi-info-circle"></i> ${t("details")}
            </button>
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-outline-warning btn-sm flex-fill" onclick="toggleFavorite('${app.id}')">
              <i class="bi ${isFav ? 'bi-star-fill' : 'bi-star'}"></i> ${isFav ? t("removeFav") : t("addFav")}
            </button>
            <button class="btn btn-outline-success btn-sm flex-fill" onclick="payApp('${app.id}')" ${isPaid ? 'disabled' : ''}>
              <i class="bi bi-cash"></i> ${isPaid ? t("paid") : t("pay")}
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderStars(rating) {
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    stars += `<i class="bi ${i <= rating ? 'bi-star-fill text-warning' : 'bi-star text-secondary'}"></i>`;
  }
  return stars;
}

function renderSubCard(sub) {
  return `
    <div class="col-md-4">
      <div class="card h-100 border-success">
        <div class="card-body">
          <h5 class="card-title">${sub.app_name}</h5>
          <p class="card-text">${sub.status || "Activa"}</p>
        </div>
      </div>
    </div>
  `;
}

function filterApps() {
  let filtered = [...allApps];
  const search = document.getElementById("search-input").value.toLowerCase();
  const cat = document.getElementById("category-filter").value;
  const rating = document.getElementById("rating-filter").value;
  const sort = document.getElementById("sort-filter");
  if (search) filtered = filtered.filter(a => a.name.toLowerCase().includes(search) || (a.description || '').toLowerCase().includes(search));
  if (cat) filtered = filtered.filter(a => a.category === cat);
  if (rating) filtered = filtered.filter(a => (a.rating || 0) >= parseInt(rating));
  if (sort && sort.value === "rating") filtered = filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  if (sort && sort.value === "name") filtered = filtered.sort((a, b) => a.name.localeCompare(b.name));
  return filtered;
}

function renderPagination(total) {
  const pages = Math.ceil(total / PAGE_SIZE);
  const pag = document.getElementById("pagination");
  let html = '';
  for (let i = 1; i <= pages; i++) {
    html += `<li class="page-item${i === currentPage ? ' active' : ''}"><a class="page-link" href="#" onclick="gotoPage(${i})">${i}</a></li>`;
  }
  pag.innerHTML = html;
}

function renderApps() {
  const apps = filterApps();
  const list = document.getElementById("apps-list");
  if (!apps.length) {
    list.innerHTML = `<div class=\"col-12 text-center\">${t("noApps")}</div>`;
    renderPagination(0);
    return;
  }
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageApps = apps.slice(start, start + PAGE_SIZE);
  list.innerHTML = pageApps.map(renderAppCard).join("");
  renderPagination(apps.length);
}

async function renderSubs() {
  const subs = await fetchSubs();
  const list = document.getElementById("subs-list");
  if (!subs.length) {
    list.innerHTML = `<div class="col-12 text-center">${t("noSubs")}</div>`;
    return;
  }
  list.innerHTML = subs.map(renderSubCard).join("");
}


window.installApp = async function(appId) {
  alert(`${t("installing")} ${appId}`);
  // Aquí puedes llamar a tu endpoint de instalación si lo tienes
  // await fetch(`${API_BASE_URL}/api/install`, { method: 'POST', body: JSON.stringify({ appId }) });
};

window.toggleFavorite = function(appId) {
  if (favorites.includes(appId)) {
    favorites = favorites.filter(f => f !== appId);
  } else {
    favorites.push(appId);
  }
  localStorage.setItem("favorites", JSON.stringify(favorites));
  renderApps();
};

window.payApp = function(appId) {
  if (!paidApps.includes(appId)) {
    paidApps.push(appId);
    localStorage.setItem("paidApps", JSON.stringify(paidApps));
    alert("Pago simulado exitoso");
    renderApps();
  }
};

window.gotoPage = function(page) {
  currentPage = page;
  renderApps();
};

window.showAppDetail = function(appId) {
  const app = allApps.find(a => a.id === appId);
  if (!app) return;
  document.getElementById("appDetailLabel").textContent = app.name;
  // Mostrar reviews
  const appReviews = (reviews[appId] || []);
  let reviewsHtml = `<h6 class='mt-3 mb-2'><i class=\"bi bi-chat-left-text\"></i> Reseñas de usuarios</h6>`;
  if (appReviews.length) {
    reviewsHtml += appReviews.map(r => `<div class='border rounded p-2 mb-2'><b>${renderStars(r.rating)}</b> <span>${r.text}</span></div>`).join('');
  } else {
    reviewsHtml += `<div class='text-muted'>No hay reseñas aún.</div>`;
  }
  document.getElementById("appDetailBody").innerHTML = `
    <p>${app.description || ""}</p>
    <ul>
      <li><b>ID:</b> ${app.id}</li>
      <li><b>Autor:</b> ${app.author || "-"}</li>
      <li><b>Categoría:</b> ${app.category || "-"}</li>
    </ul>
    ${reviewsHtml}
  `;
  // Setup review form
  const form = document.getElementById("review-form");
  form.onsubmit = function(e) {
    e.preventDefault();
    const text = document.getElementById("review-text").value.trim();
    const rating = parseInt(document.getElementById("review-rating").value);
    if (!text) return;
    if (!reviews[appId]) reviews[appId] = [];
    reviews[appId].push({ text, rating });
    localStorage.setItem("reviews", JSON.stringify(reviews));
    showAppDetail(appId);
    form.reset();
  };
  const modal = new bootstrap.Modal(document.getElementById('appDetailModal'));
  modal.show();
};

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem("lang", lang);
  document.getElementById("main-title").textContent = t("featured");
  document.getElementById("subs-title").textContent = t("mySubs");
  document.getElementById("search-input").placeholder = t("search");
  document.getElementById("category-filter").options[0].text = t("allCategories");
  document.getElementById("rating-filter").options[0].text = t("allRatings");
  renderApps();
  renderSubs();
}

function setupLangSelector() {
  const sel = document.getElementById("lang-select");
  sel.value = currentLang;
  sel.onchange = e => setLang(e.target.value);
}

function setupFilters() {
  document.getElementById("search-input").oninput = () => { currentPage = 1; renderApps(); };
  document.getElementById("category-filter").onchange = () => { currentPage = 1; renderApps(); };
  document.getElementById("rating-filter").onchange = () => { currentPage = 1; renderApps(); };
  const sort = document.getElementById("sort-filter");
  if (sort) sort.onchange = () => { currentPage = 1; renderApps(); };
}

function setupThemeToggle() {
  const btn = document.getElementById("theme-toggle");
  let dark = true;
  btn.onclick = () => {
    dark = !dark;
    document.body.style.background = dark ? "#181a1b" : "#f8f9fa";
    document.body.style.color = dark ? "#f8f9fa" : "#181a1b";
    document.querySelectorAll('.card').forEach(card => {
      card.style.background = dark ? "#23272b" : "#fff";
      card.style.color = dark ? "#f8f9fa" : "#181a1b";
    });
    document.querySelector('.navbar').style.background = dark ? "#23272b" : "#fff";
    btn.innerHTML = dark ? '<i class="bi bi-moon"></i>' : '<i class="bi bi-sun"></i>';
  };
}

window.onload = async () => {
  setupLangSelector();
  setupThemeToggle();
  setupFilters();
  allApps = await fetchApps();
  // Poblar categorías únicas
  const cats = Array.from(new Set(allApps.map(a => a.category).filter(Boolean)));
  const catSel = document.getElementById("category-filter");
  cats.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    catSel.appendChild(opt);
  });
  setLang(currentLang);
  renderSubs();
};
