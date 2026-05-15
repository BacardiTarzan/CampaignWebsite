/* D&D 2024 — Player Portal */

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 401) { window.location.href = "/auth/login"; return; }
  if (!res.ok) {
    const e = await res.json().catch(() => ({}));
    throw new Error(e.detail || `HTTP ${res.status}`);
  }
  return res.json().catch(() => null);
}

function toast(msg, ms = 3000) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), ms);
}

// ---------------------------------------------------------------------------
// Boot — check auth, load roster
// ---------------------------------------------------------------------------

async function boot() {
  try {
    const me = await api("GET", "/auth/me");
    if (!me) return;
    const badge = document.getElementById("user-badge");
    document.getElementById("user-name").textContent = me.name || me.email;
    badge.style.display = "flex";
    if (me.is_admin) {
      document.getElementById("admin-link").style.display = "inline";
    }
  } catch {
    window.location.href = "/auth/login";
    return;
  }
  loadRoster();
}

// ---------------------------------------------------------------------------
// Roster
// ---------------------------------------------------------------------------

async function loadRoster() {
  const roster = document.getElementById("char-roster");
  roster.innerHTML = `<p class="hint">Loading…</p>`;
  try {
    const chars = await api("GET", "/api/characters");
    if (!chars || chars.length === 0) {
      roster.innerHTML = `
        <div style="text-align:center;padding:48px 0">
          <p class="hint mb-md">No characters yet.</p>
          <a href="/charactercreator"><button class="btn-primary">Create Your First Character</button></a>
        </div>`;
      return;
    }
    roster.innerHTML = `<div class="char-cards">${chars.map(renderCard).join("")}</div>`;
  } catch (e) {
    roster.innerHTML = `<p class="hint">Failed to load characters: ${e.message}</p>`;
  }
}

function renderCard(c) {
  const speciesDisplay = (c.species_name === "Dragonborn" && c.species_lineage)
    ? `${c.species_lineage} Dragonborn`
    : (c.species_lineage || c.species_name || "");
  const classDisplay = c.class_name ? `${c.class_name}${c.level ? ` Lv ${c.level}` : ""}` : null;
  const subtitle = [speciesDisplay, classDisplay, c.background_name].filter(Boolean).join(" &nbsp;·&nbsp; ");

  const statusBadge = c.is_complete
    ? `<span class="char-status char-status--done">Complete</span>`
    : `<span class="char-status char-status--wip">Step ${c.wizard_step} of 10</span>`;

  const stats = c.is_complete && c.hp_max ? `
    <div class="char-stats">
      <span class="char-stat"><span class="char-stat-label">HP</span>${c.hp_max}</span>
      <span class="char-stat"><span class="char-stat-label">Speed</span>${c.speed} ft.</span>
      ${c.alignment ? `<span class="char-stat"><span class="char-stat-label">Alignment</span>${c.alignment}</span>` : ""}
    </div>` : "";

  if (c.is_complete) {
    const canLevelUp = c.level_granted != null && c.level < c.level_granted;
    const levelUpBtn = canLevelUp
      ? `<div class="char-card-actions"><a href="/characters/${c.id}/levelup"><button class="btn-levelup">⬆ Level Up to ${c.level_granted}</button></a></div>`
      : "";
    return `
      <div class="char-card ${canLevelUp ? "" : "char-card--clickable"}" ${canLevelUp ? "" : `onclick="window.location.href='/characters/${c.id}/sheet'"`}>
        <div class="char-card-header">
          <div>
            <div class="char-card-name">${c.character_name}</div>
            <div class="char-card-sub">${subtitle || "&nbsp;"}</div>
          </div>
          ${statusBadge}
        </div>
        ${stats}
        ${levelUpBtn}
      </div>`;
  }

  return `
    <div class="char-card">
      <div class="char-card-header">
        <div>
          <div class="char-card-name">${c.character_name}</div>
          <div class="char-card-sub">${subtitle || "&nbsp;"}</div>
        </div>
        ${statusBadge}
      </div>
      ${stats}
      <div class="char-card-actions">
        <a href="/charactercreator?char=${c.id}"><button class="btn-primary">Continue →</button></a>
      </div>
    </div>`;
}

boot();
