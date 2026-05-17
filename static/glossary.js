/* Rules Glossary */

async function api(method, path) {
  const res = await fetch(path, { method, headers: { "Content-Type": "application/json" } });
  if (res.status === 401) { window.location.href = "/auth/login"; return null; }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json().catch(() => null);
}

const CATEGORY_LABELS = {
  combat:          "Combat",
  condition:       "Conditions",
  action:          "Actions",
  weapon_property: "Weapon Properties",
  mastery:         "Masteries",
  skill:           "Skills",
};

const CATEGORY_ORDER = ["combat", "condition", "action", "weapon_property", "mastery", "skill"];

let _allTerms = [];
let _activeCategory = "all";

function toggleSidebar() {
  const sidebar = document.getElementById("gloss-sidebar");
  const btn = document.querySelector(".lore-nav-toggle");
  const open = sidebar.classList.toggle("is-open");
  if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  try {
    const me = await api("GET", "/auth/me");
    if (!me) return;
    document.getElementById("gloss-user-name").textContent = me.name || me.email;
  } catch {
    window.location.href = "/auth/login";
    return;
  }

  let terms;
  try {
    terms = await api("GET", "/api/content/glossary");
  } catch {
    document.getElementById("gloss-content").innerHTML =
      `<p class="hint" style="padding:24px">Could not load glossary.</p>`;
    return;
  }

  _allTerms = (terms || []).sort((a, b) => a.term.localeCompare(b.term));
  renderNav();
  renderTerms(_allTerms);

  const hash = window.location.hash.slice(1);
  if (hash) setTimeout(() => openTerm(hash), 80);
}

// ---------------------------------------------------------------------------
// Sidebar nav
// ---------------------------------------------------------------------------
function renderNav() {
  const nav = document.getElementById("gloss-nav");
  const present = new Set(_allTerms.map(t => t.category));
  const ordered = [...CATEGORY_ORDER.filter(c => present.has(c)),
                   ...[...present].filter(c => !CATEGORY_ORDER.includes(c))];

  const allCount = _allTerms.length;
  nav.innerHTML = `
    <button class="lore-nav-item${_activeCategory === "all" ? " active" : ""}"
            onclick="setCategory('all')">
      All <span class="gloss-cat-count">${allCount}</span>
    </button>
    ${ordered.map(cat => {
      const count = _allTerms.filter(t => t.category === cat).length;
      return `<button class="lore-nav-item${_activeCategory === cat ? " active" : ""}"
                      onclick="setCategory('${cat}')">
        ${CATEGORY_LABELS[cat] || cat} <span class="gloss-cat-count">${count}</span>
      </button>`;
    }).join("")}
  `;
}

function setCategory(cat) {
  _activeCategory = cat;
  renderNav();
  filterTerms();
  const sidebar = document.getElementById("gloss-sidebar");
  if (sidebar.classList.contains("is-open")) {
    sidebar.classList.remove("is-open");
    const btn = document.querySelector(".lore-nav-toggle");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }
}

// ---------------------------------------------------------------------------
// Search + filter
// ---------------------------------------------------------------------------
function filterTerms() {
  const query = (document.getElementById("gloss-search").value || "").toLowerCase().trim();
  const filtered = _allTerms.filter(t => {
    if (_activeCategory !== "all" && t.category !== _activeCategory) return false;
    if (!query) return true;
    return t.term.toLowerCase().includes(query) ||
           t.short_description.toLowerCase().includes(query) ||
           (t.full_description || "").toLowerCase().includes(query);
  });
  renderTerms(filtered);
}

// ---------------------------------------------------------------------------
// Render term cards
// ---------------------------------------------------------------------------
function renderTerms(terms) {
  const content = document.getElementById("gloss-content");
  if (!terms.length) {
    content.innerHTML = `<p class="hint" style="padding:24px">No matching rules.</p>`;
    return;
  }
  content.innerHTML = terms.map(t => {
    const catLabel = CATEGORY_LABELS[t.category] || t.category.replace(/_/g, " ");
    const hasMore = t.full_description && t.full_description !== t.short_description;
    return `<div class="gloss-card" id="gloss-${t.slug}" data-slug="${t.slug}" data-cat="${t.category}">
      <div class="gloss-card-header" onclick="toggleCard('${t.slug}')">
        <div class="gloss-card-title-row">
          <h3 class="gloss-card-term">${_esc(t.term)}</h3>
          <span class="gloss-cat-badge gloss-cat-${t.category}">${_esc(catLabel)}</span>
        </div>
        <p class="gloss-card-short">${_esc(t.short_description)}</p>
        ${hasMore ? `<span class="gloss-card-chevron" id="chev-${t.slug}">▼</span>` : ""}
      </div>
      ${hasMore ? `<div class="gloss-card-full" id="full-${t.slug}" hidden>
        <div class="gloss-full-body">${_simpleMarkdown(t.full_description)}</div>
      </div>` : ""}
    </div>`;
  }).join("");
}

// ---------------------------------------------------------------------------
// Accordion
// ---------------------------------------------------------------------------
function toggleCard(slug) {
  const full = document.getElementById(`full-${slug}`);
  const chev = document.getElementById(`chev-${slug}`);
  if (!full) return;
  const isOpen = !full.hidden;
  full.hidden = isOpen;
  if (chev) chev.textContent = isOpen ? "▼" : "▲";
  if (!isOpen) window.location.hash = slug;
}

function openTerm(slug) {
  const card = document.getElementById(`gloss-${slug}`);
  if (!card) return;
  const full = document.getElementById(`full-${slug}`);
  const chev = document.getElementById(`chev-${slug}`);
  if (full && full.hidden) {
    full.hidden = false;
    if (chev) chev.textContent = "▲";
  }
  card.scrollIntoView({ behavior: "smooth", block: "start" });
  card.classList.add("gloss-card--highlight");
  setTimeout(() => card.classList.remove("gloss-card--highlight"), 1500);
}

// ---------------------------------------------------------------------------
// HTML escape (for term/short_description)
// ---------------------------------------------------------------------------
function _esc(s) {
  return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ---------------------------------------------------------------------------
// Simple markdown → HTML (same as sheet.js)
// ---------------------------------------------------------------------------
function _simpleMarkdown(text) {
  if (!text) return "";
  return `<p>${text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")}</p>`;
}

boot();
