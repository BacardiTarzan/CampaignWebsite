# Rules Glossary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone `/glossary` page where players can browse and search all rules, fix the sheet tooltip to hide "Read full rule ›" when there's nothing extra to show, and add a "View in Glossary ↗" link inside the sheet modal.

**Architecture:** Glossary data is already seeded from `reference_claude/rules/` into the `glossary_terms` table and exposed via `GET /api/content/glossary`. The glossary page reuses `lore.css` layout (sidebar + parchment main), adds its own `glossary.css` for term cards, and a standalone `glossary.js` that fetches all terms, renders category filters, and handles accordion expand / hash-anchor deep-linking. Sheet fixes are two small edits to `_showGlossPopover` and `openGlossaryModal` in `sheet.js`.

**Tech Stack:** FastAPI (FileResponse route), vanilla JS, CSS variables from `style.css`

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `app/main.py` | Modify | Add `GET /glossary` route |
| `static/portal.html` | Modify | Add "📜 Rules Glossary" nav button |
| `static/glossary.html` | Create | Page shell — reuses lore layout |
| `static/glossary.css` | Create | Term card styles, search bar, badges |
| `static/glossary.js` | Create | Fetch, filter, render, hash anchor, accordion |
| `static/sheet.js` | Modify | Conditional "Read full rule ›"; add "View in Glossary ↗" |

---

## Task 1: Route + portal button

**Files:**
- Modify: `app/main.py:107-109`
- Modify: `static/portal.html:26`

- [ ] **Step 1: Add `/glossary` route to `app/main.py`**

After the `/lore` route (line 109), add:

```python
@app.get("/glossary")
def serve_glossary():
    return FileResponse(str(static_path / "glossary.html"))
```

- [ ] **Step 2: Add "Rules Glossary" button to `static/portal.html`**

Find line 26:
```html
      <a href="/lore"><button class="btn-secondary">📖 Lore Library</button></a>
```
Replace with:
```html
      <a href="/lore"><button class="btn-secondary">📖 Lore Library</button></a>
      <a href="/glossary"><button class="btn-secondary">📜 Rules Glossary</button></a>
```

- [ ] **Step 3: Verify**

Run `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`, navigate to `/portal`. Confirm the "📜 Rules Glossary" button appears next to Lore Library. Clicking it should 404 (the HTML file doesn't exist yet — that's expected).

- [ ] **Step 4: Commit**

```bash
git add app/main.py static/portal.html
git commit -m "feat: add /glossary route and portal nav button"
```

---

## Task 2: `glossary.html` — page shell

**Files:**
- Create: `static/glossary.html`

- [ ] **Step 1: Create `static/glossary.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rules Glossary</title>
  <link rel="icon" type="image/png" href="/static/d20.png">
  <link rel="stylesheet" href="/static/style.css">
  <link rel="stylesheet" href="/static/lore.css">
  <link rel="stylesheet" href="/static/glossary.css">
</head>
<body>
<div class="lore-layout">

  <div class="lore-sidebar" id="gloss-sidebar">
    <div class="lore-sidebar-header">
      <a href="/portal" class="lore-back">← My Characters</a>
      <h2 class="lore-sidebar-title">Rules Glossary</h2>
    </div>
    <div id="gloss-nav"></div>
  </div>

  <div class="lore-main">
    <div class="lore-topbar">
      <button class="lore-nav-toggle" onclick="toggleSidebar()" aria-expanded="false" aria-controls="gloss-sidebar">
        ☰ Categories
      </button>
      <span id="gloss-user-name" class="lore-user"></span>
    </div>
    <div class="gloss-search-bar">
      <input type="search" id="gloss-search" placeholder="Search rules…" oninput="filterTerms()">
    </div>
    <div id="gloss-content" class="gloss-content">
      <p class="hint" style="padding:24px">Loading…</p>
    </div>
  </div>

</div>
<script src="/static/glossary.js"></script>
</body>
</html>
```

- [ ] **Step 2: Verify**

Navigate to `/glossary`. The page should load with the leather sidebar and parchment content area (same visual as Lore Library). Console will show JS errors because `glossary.js` doesn't exist yet — that's expected.

- [ ] **Step 3: Commit**

```bash
git add static/glossary.html
git commit -m "feat: add glossary.html page shell"
```

---

## Task 3: `glossary.css` — term card styles

**Files:**
- Create: `static/glossary.css`

- [ ] **Step 1: Create `static/glossary.css`**

```css
/* ─────────────────────────────────────────────────────────────────
   RULES GLOSSARY — term cards and search
   ───────────────────────────────────────────────────────────────── */

/* ─── Search bar ─── */
.gloss-search-bar {
  flex-shrink: 0;
  padding: var(--sp-3) clamp(20px, 4vw, 52px) 0;
  background: linear-gradient(175deg, var(--parchment-bright) 0%, var(--parchment) 100%);
}

#gloss-search {
  width: 100%;
  max-width: 480px;
  padding: 8px 14px;
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--ink);
  background: rgba(255,255,255,0.5);
  border: 1px solid rgba(168,120,43,0.35);
  border-radius: var(--radius-sm);
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
}
#gloss-search::placeholder { color: var(--ink-faded); }
#gloss-search:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 2px rgba(168,120,43,0.18);
}

/* ─── Content scroll area ─── */
.gloss-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4) clamp(20px, 4vw, 52px) clamp(28px, 5vw, 52px);
  scrollbar-width: thin;
  scrollbar-color: rgba(168,120,43,0.35) transparent;
}
.gloss-content::-webkit-scrollbar { width: 5px; }
.gloss-content::-webkit-scrollbar-track { background: transparent; }
.gloss-content::-webkit-scrollbar-thumb { background: rgba(168,120,43,0.35); border-radius: 3px; }

/* ─── Sidebar category count badges ─── */
.gloss-cat-count {
  display: inline-block;
  margin-left: auto;
  font-size: 0.72rem;
  font-family: var(--font-body);
  color: var(--ink-faded);
  background: rgba(168,120,43,0.12);
  border-radius: 10px;
  padding: 1px 7px;
  min-width: 20px;
  text-align: center;
}

/* ─── Term card ─── */
.gloss-card {
  border: 1px solid rgba(168,120,43,0.22);
  border-left: 3px solid rgba(168,120,43,0.4);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
  background: rgba(255,255,255,0.28);
  transition: border-left-color 0.15s, box-shadow 0.15s;
  scroll-margin-top: 12px;
}
.gloss-card:hover {
  border-left-color: var(--gold);
  box-shadow: 0 2px 12px rgba(60,30,10,0.1);
}

/* Category accent colors on left border */
.gloss-card[data-slug] { /* default — gold */ }
/* Applied via JS: data-category attribute for specificity */
.gloss-card[data-cat="combat"]          { border-left-color: var(--rubric); }
.gloss-card[data-cat="condition"]       { border-left-color: #7a4a00; }
.gloss-card[data-cat="action"]          { border-left-color: var(--green); }
.gloss-card[data-cat="weapon_property"] { border-left-color: var(--gold-deep); }
.gloss-card[data-cat="mastery"]         { border-left-color: var(--gold-bright); }
.gloss-card[data-cat="skill"]           { border-left-color: #4a7070; }

.gloss-card-header {
  padding: var(--sp-3) var(--sp-4);
  cursor: pointer;
  user-select: none;
  position: relative;
}

.gloss-card-title-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  margin-bottom: var(--sp-1);
}

.gloss-card-term {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--rubric);
  margin: 0;
  flex-shrink: 0;
}

/* ─── Category badge pill ─── */
.gloss-cat-badge {
  font-family: var(--font-display);
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid rgba(168,120,43,0.3);
  color: var(--gold-deep);
  background: rgba(168,120,43,0.1);
  white-space: nowrap;
}
.gloss-cat-badge.gloss-cat-combat          { color: var(--rubric); border-color: rgba(139,26,26,0.3); background: rgba(139,26,26,0.08); }
.gloss-cat-badge.gloss-cat-condition       { color: #7a4a00; border-color: rgba(122,74,0,0.3); background: rgba(122,74,0,0.08); }
.gloss-cat-badge.gloss-cat-action          { color: var(--green); border-color: rgba(46,122,66,0.3); background: rgba(46,122,66,0.08); }
.gloss-cat-badge.gloss-cat-weapon_property { color: var(--gold-deep); border-color: rgba(107,74,24,0.35); background: rgba(107,74,24,0.08); }
.gloss-cat-badge.gloss-cat-mastery         { color: var(--gold); border-color: rgba(168,120,43,0.35); background: rgba(168,120,43,0.1); }
.gloss-cat-badge.gloss-cat-skill           { color: #4a7070; border-color: rgba(74,112,112,0.3); background: rgba(74,112,112,0.08); }

.gloss-card-short {
  font-family: var(--font-body);
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--ink-soft);
  margin: 0;
  padding-right: var(--sp-5);
}

.gloss-card-chevron {
  position: absolute;
  right: var(--sp-4);
  top: var(--sp-3);
  font-size: 0.7rem;
  color: var(--ink-faded);
  pointer-events: none;
}

/* ─── Expanded full description ─── */
.gloss-card-full {
  padding: 0 var(--sp-4) var(--sp-3);
  border-top: 1px solid rgba(168,120,43,0.15);
}
.gloss-card-full[hidden] { display: none; }

.gloss-full-body {
  font-family: var(--font-body);
  font-size: 0.92rem;
  line-height: 1.65;
  color: var(--ink);
  padding-top: var(--sp-3);
}
.gloss-full-body p { margin: 0 0 var(--sp-2); }
.gloss-full-body p:last-child { margin-bottom: 0; }
.gloss-full-body strong { color: var(--ink); font-weight: 700; }
.gloss-full-body em { color: var(--ink-soft); }

/* ─── Hash anchor highlight flash ─── */
@keyframes gloss-highlight {
  0%   { box-shadow: 0 0 0 3px rgba(168,120,43,0.6); }
  100% { box-shadow: none; }
}
.gloss-card--highlight {
  animation: gloss-highlight 1.5s ease-out forwards;
}

/* ─────────────────────────────────────────────────────────────────
   RESPONSIVE — mobile sidebar
   ───────────────────────────────────────────────────────────────── */
@media (max-width: 680px) {
  .lore-nav-toggle { display: inline-flex; }

  #gloss-sidebar {
    position: fixed;
    left: -270px;
    top: 0;
    bottom: 0;
    z-index: 300;
    transition: left 0.25s ease;
  }
  #gloss-sidebar.is-open { left: 0; }
}
```

- [ ] **Step 2: Verify**

Reload `/glossary`. The parchment content area should now have a search bar below the topbar. No JS yet — "Loading…" text visible.

- [ ] **Step 3: Commit**

```bash
git add static/glossary.css
git commit -m "feat: add glossary.css term card and layout styles"
```

---

## Task 4: `glossary.js` — fetch, filter, render, hash anchor

**Files:**
- Create: `static/glossary.js`

- [ ] **Step 1: Create `static/glossary.js`**

```javascript
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
           t.full_description.toLowerCase().includes(query);
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
          <h3 class="gloss-card-term">${t.term}</h3>
          <span class="gloss-cat-badge gloss-cat-${t.category}">${catLabel}</span>
        </div>
        <p class="gloss-card-short">${t.short_description}</p>
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
```

- [ ] **Step 2: Verify full page**

Navigate to `/glossary`. The page should:
- Show category buttons in sidebar (All, Combat, Conditions, etc.) with counts
- Show all terms as cards with term name, category badge, and short description
- Search bar filters as you type
- Clicking a category filters the list; active category is highlighted in sidebar
- Clicking a card with more content expands it to show the full rule; chevron flips ▼ → ▲
- Mobile (resize to < 680px): sidebar hides behind "☰ Categories" toggle
- Test hash link: navigate to `/glossary#advantage` — the Advantage card should scroll into view, expand, and flash a gold outline

- [ ] **Step 3: Commit**

```bash
git add static/glossary.js
git commit -m "feat: add glossary.js fetch, filter, accordion, hash anchor"
```

---

## Task 5: Fix sheet.js tooltip — conditional "Read full rule ›" + modal "View in Glossary ↗"

**Files:**
- Modify: `static/sheet.js:167-192` (popover), `static/sheet.js:136-155` (modal)

- [ ] **Step 1: Fix `_showGlossPopover` to hide "Read full rule ›" when no extra content**

Find this block in `_showGlossPopover` (around line 175-177):
```javascript
  pop.innerHTML = `<div class="gloss-popover-term">${term.term}</div>
    <div class="gloss-popover-body">${term.short_description}</div>
    <span class="gloss-popover-more" onclick="openGlossaryModal('${slug}')">Read full rule ›</span>`;
```
Replace with:
```javascript
  const hasMore = term.full_description && term.full_description !== term.short_description;
  pop.innerHTML = `<div class="gloss-popover-term">${term.term}</div>
    <div class="gloss-popover-body">${term.short_description}</div>
    ${hasMore ? `<span class="gloss-popover-more" onclick="openGlossaryModal('${slug}')">Read full rule ›</span>` : ""}`;
```

- [ ] **Step 2: Add "View in Glossary ↗" to `openGlossaryModal`**

Find this block in `openGlossaryModal` (around line 143-153):
```javascript
  overlay.innerHTML = `<div class="modal-box" style="max-width:480px">
    <div class="modal-header">
      <h3>${term.term}</h3>
      <button class="modal-close-btn" onclick="closeGlossaryModal()">✕</button>
    </div>
    <div class="modal-body">
      <p class="gloss-modal-category">${term.category.replace(/_/g, ' ')}</p>
      <div class="gloss-modal-body"><p>${_simpleMarkdown(term.full_description)}</p></div>
    </div>
  </div>`;
```
Replace with:
```javascript
  overlay.innerHTML = `<div class="modal-box" style="max-width:480px">
    <div class="modal-header">
      <h3>${term.term}</h3>
      <button class="modal-close-btn" onclick="closeGlossaryModal()">✕</button>
    </div>
    <div class="modal-body">
      <p class="gloss-modal-category">${term.category.replace(/_/g, ' ')}</p>
      <div class="gloss-modal-body"><p>${_simpleMarkdown(term.full_description)}</p></div>
    </div>
    <div style="text-align:right;padding:8px 20px 16px">
      <a href="/glossary#${slug}" target="_blank" class="gloss-glossary-link">View in Glossary ↗</a>
    </div>
  </div>`;
```

- [ ] **Step 3: Fix `pointer-events` on `.gloss-popover-more` in `sheet.css`**

The popover container has `pointer-events: none` (so it doesn't block underlying clicks), but this also blocks clicks on "Read full rule ›" inside it — the actual root cause of it "rarely doing anything." Fix by enabling pointer events on the interactive element only.

Find in `sheet.css` (around line 1031):
```css
.gloss-popover-more { font-family: var(--font-body); font-size: 0.78rem; color: var(--gold-deep); margin-top: 5px; font-style: italic; }
```
Replace with:
```css
.gloss-popover-more { font-family: var(--font-body); font-size: 0.78rem; color: var(--gold-deep); margin-top: 5px; font-style: italic; pointer-events: auto; cursor: pointer; display: block; }
```

- [ ] **Step 4: Add `.gloss-glossary-link` style to `sheet.css`**

Find the `.gloss-modal-body` block in `sheet.css` (around line 1043) and add after it:
```css
.gloss-glossary-link {
  font-family: var(--font-body);
  font-size: 0.82rem;
  color: var(--gold-deep);
  text-decoration: none;
  font-style: italic;
  transition: color 0.15s;
}
.gloss-glossary-link:hover { color: var(--gold); text-decoration: underline; }
```

- [ ] **Step 5: Verify**

Open a character sheet. Click a gloss-term tooltip (e.g. a weapon mastery or skill name).
- If the term's `full_description` equals `short_description`: "Read full rule ›" should NOT appear.
- If the term has extra content: "Read full rule ›" should appear, clicking it opens the modal; the modal should show a "View in Glossary ↗" link at the bottom that opens `/glossary#slug` in a new tab.

- [ ] **Step 6: Commit**

```bash
git add static/sheet.js static/sheet.css
git commit -m "fix: hide 'Read full rule' when no extra content; add 'View in Glossary' link in modal"
```
