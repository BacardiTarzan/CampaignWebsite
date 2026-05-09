/* Campaign Lore Library */

async function api(method, path) {
  const res = await fetch(path, { method, headers: { "Content-Type": "application/json" } });
  if (res.status === 401) { window.location.href = "/auth/login"; return null; }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json().catch(() => null);
}

const CATEGORY_LABELS = {
  world:    "The World",
  species:  "Species",
  campaign: "Campaign",
};

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  try {
    const me = await api("GET", "/auth/me");
    if (!me) return;
    document.getElementById("lore-user-name").textContent = me.name || me.email;
  } catch {
    window.location.href = "/auth/login";
    return;
  }

  let pages;
  try {
    pages = await api("GET", "/api/content/lore");
  } catch {
    document.getElementById("lore-nav").innerHTML = `<p class="hint" style="padding:12px">Could not load lore.</p>`;
    return;
  }

  renderNav(pages || []);

  // Open page from URL hash if present
  const slug = window.location.hash.slice(1);
  if (slug) openPage(slug);
}

// ---------------------------------------------------------------------------
// Sidebar nav
// ---------------------------------------------------------------------------
function renderNav(pages) {
  const nav = document.getElementById("lore-nav");
  if (!pages.length) {
    nav.innerHTML = `<p class="hint" style="padding:12px">No lore pages available yet.</p>`;
    return;
  }

  const groups = {};
  for (const p of pages) {
    const cat = p.category || "world";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(p);
  }

  const order = ["world", "species", "campaign"];
  const sorted = [...order.filter(c => groups[c]), ...Object.keys(groups).filter(c => !order.includes(c))];

  nav.innerHTML = sorted.map(cat => `
    <div class="lore-nav-group">
      <div class="lore-nav-category">${CATEGORY_LABELS[cat] || cat}</div>
      ${groups[cat].map(p => `
        <button class="lore-nav-item" id="nav-${p.slug}" onclick="openPage('${p.slug}')">${p.title}</button>
      `).join("")}
    </div>
  `).join("");
}

// ---------------------------------------------------------------------------
// Page viewer
// ---------------------------------------------------------------------------
async function openPage(slug) {
  // Highlight active nav item
  document.querySelectorAll(".lore-nav-item").forEach(b => b.classList.remove("active"));
  const btn = document.getElementById(`nav-${slug}`);
  if (btn) btn.classList.add("active");

  window.location.hash = slug;

  const content = document.getElementById("lore-content");
  content.innerHTML = `<p class="hint" style="padding:24px">Loading…</p>`;

  try {
    const page = await api("GET", `/api/content/lore/${slug}`);
    if (!page) return;
    document.title = page.title + " — Lore Library";
    content.innerHTML = `
      <article class="lore-article">
        <div class="lore-md">${marked.parse(page.content_md)}</div>
      </article>`;
    content.scrollTop = 0;
  } catch {
    content.innerHTML = `<p class="hint" style="padding:24px">Page not found.</p>`;
  }
}

boot();
