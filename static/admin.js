/* D&D 2024 Admin Panel */

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 401) { window.location.href = "/auth/login"; return; }
  if (res.status === 403) { document.body.innerHTML = "<div style='padding:2rem;font-family:serif'>Access denied.</div>"; return; }
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
function err(msg) { toast("⚠ " + msg, 5000); }

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------
function switchTab(tab) {
  document.querySelectorAll(".tab-bar > .tab-btn").forEach(b => b.classList.remove("active"));
  event.target.classList.add("active");
  ["roster", "codex", "grimoire", "lore", "import"].forEach(t =>
    document.getElementById(`tab-${t}`).classList.toggle("hidden", t !== tab));
  if (tab === "roster") loadRoster();
  if (tab === "codex") loadCodex();
  if (tab === "grimoire") loadGrimoireSpells();
  if (tab === "lore") loadLore();
}

function switchCodexTab(sub) {
  document.querySelectorAll("#tab-codex .tab-bar .tab-btn").forEach(b => b.classList.remove("active"));
  event.target.classList.add("active");
  ["species", "backgrounds", "feats"].forEach(t =>
    document.getElementById(`codex-${t}`).classList.toggle("hidden", t !== sub));
  if (sub === "species") loadSpeciesList();
  if (sub === "backgrounds") loadBgList();
  if (sub === "feats") loadFeatList();
}

// ---------------------------------------------------------------------------
// Roster
// ---------------------------------------------------------------------------
let _rosterBios = {};
let _rosterChars = [];

async function loadRoster() {
  const chars = await api("GET", "/api/admin/characters");
  _rosterChars = chars;
  _rosterBios = {};
  chars.forEach(c => { _rosterBios[c.id] = c.bio || ""; });
  const tbody = chars.map(c => {
    const hp = c.hp_max ? `<span class="roster-hp" id="hp-${c.id}">${c.hp_current ?? "?"}/${c.hp_max}</span>` : "—";
    return `
    <tr>
      <td>${c.id}</td>
      <td><span class="roster-name" id="name-${c.id}" onclick="editCharName(${c.id})" title="Click to rename">${c.character_name}</span></td>
      <td>${c.created_by_display_name}</td>
      <td>${c.species_name || "—"}</td>
      <td>${c.class_name || "—"} ${c.level ? "Lv " + c.level : ""}</td>
      <td>${c.background_name || "—"}</td>
      <td>${c.is_complete ? "✅ Done" : `Step ${c.wizard_step}`}</td>
      <td class="roster-hp-cell">
        ${hp}
        ${c.hp_max ? `<div class="hp-adj-row">
          <input type="number" id="hp-adj-${c.id}" class="hp-adj-input" placeholder="±" style="width:50px">
          <button onclick="adminAdjHp(${c.id})">±HP</button>
          <button onclick="adminRest(${c.id})">💤 Long Rest</button>
          <button onclick="adminShortRest(${c.id})">⏱ Short Rest</button>
        </div>` : ""}
      </td>
      <td><div class="actions">
        <button onclick="levelUp(${c.id})" title="Grant level (current: ${c.level}, granted: ${c.level_granted ?? c.level})">+Lv ${c.level_granted != null && c.level_granted > c.level ? `<span style="color:#8fc88f">(${c.level}→${c.level_granted})</span>` : ""}</button>
        <button onclick="unlockStats(${c.id})">🔓 Stats</button>
        ${c.physical_locked ? `<button onclick="unlockPhysical(${c.id})">🔓 Physical</button>` : ""}
        <button onclick="editBio(${c.id})">📜 Bio</button>
        <button onclick="openEditPanel(${c.id})">✏ Edit</button>
        <a href="/characters/${c.id}/sheet" target="_blank"><button>📋 Sheet</button></a>
        <a href="/api/admin/characters/${c.id}/export/json" target="_blank"><button>⬇ JSON</button></a>
        <button class="btn-danger" onclick="deleteChar(${c.id})">✕</button>
      </div></td>
    </tr>`;
  }).join("");
  document.getElementById("roster-table").innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>#</th><th>Character</th><th>Player</th><th>Species</th>
        <th>Class</th><th>Background</th><th>Status</th><th>HP</th><th>Actions</th>
      </tr></thead>
      <tbody>${tbody || '<tr><td colspan="9" class="text-muted">No characters yet.</td></tr>'}</tbody>
    </table>`;
}

async function adminAdjHp(id) {
  const input = document.getElementById(`hp-adj-${id}`);
  const delta = parseInt(input.value, 10);
  if (isNaN(delta)) { toast("Enter a number (e.g. -5 or +3)"); return; }
  try {
    const r = await api("POST", `/api/admin/characters/${id}/hp?delta=${delta}`);
    document.getElementById(`hp-${id}`).textContent = `${r.hp_current}/${r.hp_max}`;
    input.value = "";
    toast(`HP updated: ${r.hp_current}/${r.hp_max}`);
  } catch(e) { err(e.message); }
}

async function adminRest(id) {
  try {
    const r = await api("POST", `/api/admin/characters/${id}/rest`);
    toast(`Long rest — HP and hit dice fully restored (${r.hp_current} HP).`);
    loadRoster();
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Inline character rename
// ---------------------------------------------------------------------------
function editCharName(id) {
  const span = document.getElementById(`name-${id}`);
  if (!span || span.querySelector("input")) return; // already editing
  const current = span.textContent;
  span.innerHTML = `<input type="text" class="roster-name-input" value="${current.replace(/"/g, '&quot;')}"
    onblur="saveCharName(${id}, this)" onkeydown="if(event.key==='Enter')this.blur();if(event.key==='Escape'){this.dataset.cancel='1';this.blur();}">`;
  const input = span.querySelector("input");
  input.focus();
  input.select();
}

async function saveCharName(id, input) {
  if (input.dataset.cancel) {
    loadRoster();
    return;
  }
  const name = input.value.trim();
  if (!name) { loadRoster(); return; }
  const char = _rosterChars.find(x => x.id === id);
  if (char && name === char.character_name) { loadRoster(); return; }
  try {
    const r = await api("PATCH", `/api/admin/characters/${id}/rename`, { character_name: name });
    if (char) char.character_name = r.character_name;
    toast(`Renamed to "${r.character_name}"`);
    loadRoster();
  } catch(e) { err(e.message); loadRoster(); }
}

// ---------------------------------------------------------------------------
// Short rest modal — one hit die at a time, DM enters physical roll result
// ---------------------------------------------------------------------------
let _srState = null;

function adminShortRest(id) {
  const c = _rosterChars.find(x => x.id === id);
  if (!c || !c.hp_max) return;

  if ((c.hp_current || 0) <= 0) {
    toast("Cannot short rest at 0 HP.");
    return;
  }

  _srState = {
    charId: c.id,
    charName: c.character_name,
    hitDie: c.hit_die || 8,
    conMod: c.con_mod || 0,
    hdMax: c.class_level || c.level || 1,
    hdRemain: c.hit_dice_remaining ?? 0,
    hpCurrent: c.hp_current,
    hpMax: c.hp_max,
    rolls: [],
    hpGained: 0,
  };

  _renderSrModal();
}

function _renderSrModal() {
  const existing = document.getElementById("sr-modal-overlay");
  if (existing) existing.remove();

  const s = _srState;
  const dieNum = s.rolls.length + 1;
  const hdLeft = s.hdRemain - s.rolls.length;
  const projectedHp = Math.min(s.hpMax, s.hpCurrent + s.hpGained);
  const noHd = s.hdRemain <= 0;
  const noMoreHd = hdLeft <= 0;
  const atMax = projectedHp >= s.hpMax;
  const canKeepGoing = !noMoreHd && !atMax;

  let bodyHtml = "";
  if (noHd) {
    bodyHtml = `<p class="sr-hint">No hit dice remaining. Take a long rest to recover them.</p>`;
  } else {
    if (canKeepGoing) {
      bodyHtml = `
        <div class="sr-die-row">
          <label class="sr-die-label">Die #${dieNum} — roll your d${s.hitDie}:</label>
          <div class="sr-die-input-row">
            <input type="number" id="sr-roll-input" class="sr-roll-input" min="1" max="${s.hitDie}"
              placeholder="1–${s.hitDie}">
            <span class="sr-con-mod">CON ${s.conMod >= 0 ? "+" : ""}${s.conMod}</span>
          </div>
        </div>`;
    } else if (atMax) {
      bodyHtml = `<p class="sr-hint">Already at full HP — no need to spend more dice.</p>`;
    } else {
      bodyHtml = `<p class="sr-hint">All available hit dice spent.</p>`;
    }
    if (s.rolls.length > 0) {
      bodyHtml += `<div class="sr-total">HP gained: <strong>+${s.hpGained}</strong></div>`;
    }
  }

  const overlay = document.createElement("div");
  overlay.id = "sr-modal-overlay";
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal-box sr-modal">
      <div class="modal-header">
        <h3>Short Rest — ${s.charName}</h3>
        <button class="modal-close-btn" onclick="closeSrModal()">✕</button>
      </div>
      <div class="sr-status-bar">
        HP <strong>${projectedHp}</strong> / <strong>${s.hpMax}</strong>
        &nbsp;·&nbsp;
        Hit Dice <strong>${hdLeft}</strong> / <strong>${s.hdMax}</strong> (d${s.hitDie})
      </div>
      <div class="modal-body">${bodyHtml}</div>
      <div class="modal-footer">
        <button class="sr-btn-cancel" onclick="closeSrModal()">Cancel</button>
        ${canKeepGoing ? `<button class="sr-btn-continue" onclick="srContinue()">Continue</button>` : ""}
        <button class="sr-btn-done" onclick="srDone()">${s.rolls.length === 0 ? "Close" : "Done"}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  const input = document.getElementById("sr-roll-input");
  if (input) {
    input.focus();
    input.addEventListener("keydown", e => { if (e.key === "Enter") srContinue(); });
  }
}

function srContinue() {
  const s = _srState;
  const input = document.getElementById("sr-roll-input");
  if (!input) return;

  const val = parseInt(input.value, 10);
  if (isNaN(val) || val < 1 || val > s.hitDie) {
    toast(`Enter a number between 1 and ${s.hitDie}`);
    input.focus();
    return;
  }

  const gained = Math.max(1, val + s.conMod);
  s.rolls.push(val);
  s.hpGained += gained;
  _renderSrModal();
}

async function srDone() {
  const s = _srState;
  if (s.rolls.length === 0) {
    closeSrModal();
    return;
  }

  try {
    const r = await api("POST", `/api/admin/characters/${s.charId}/short-rest`, { dice_rolls: s.rolls });
    if (!r) return;

    const char = _rosterChars.find(x => x.id === s.charId);
    if (char) {
      char.hp_current = r.hp_current;
      char.hit_dice_remaining = r.hit_dice_remaining;
    }

    closeSrModal();
    toast(`Short rest — +${r.hp_gained} HP. Hit dice: ${r.hit_dice_remaining}/${s.hdMax} remaining.`);
    loadRoster();
  } catch(e) { err(e.message); }
}

function closeSrModal() {
  const overlay = document.getElementById("sr-modal-overlay");
  if (overlay) overlay.remove();
  _srState = null;
}

async function levelUp(id) {
  try {
    const r = await api("POST", `/api/admin/characters/${id}/level-up`);
    toast(`Leveled up to ${r.new_level}!`);
    loadRoster();
  } catch(e) { err(e.message); }
}

async function unlockStats(id) {
  try {
    await api("POST", `/api/admin/characters/${id}/unlock-stats`);
    toast("Stats unlocked for re-rolling.");
    loadRoster();
  } catch(e) { err(e.message); }
}

async function unlockPhysical(id) {
  try {
    await api("POST", `/api/admin/characters/${id}/unlock-physical`);
    toast("Physical details unlocked for editing.");
    loadRoster();
  } catch(e) { err(e.message); }
}

function editBio(id) {
  const modal = document.getElementById("bio-edit-modal");
  const textarea = document.getElementById("bio-edit-text");
  const title = document.getElementById("bio-edit-title");
  title.textContent = `Edit Backstory — Character #${id}`;
  textarea.value = _rosterBios[id] || "";
  modal.dataset.charId = id;
  modal.classList.remove("hidden");
  textarea.focus();
}

function closeBioModal() {
  document.getElementById("bio-edit-modal").classList.add("hidden");
}

async function saveBio() {
  const modal = document.getElementById("bio-edit-modal");
  const id = modal.dataset.charId;
  const bio = document.getElementById("bio-edit-text").value;
  try {
    await api("PATCH", `/api/characters/${id}/bio`, { bio });
    toast("Backstory saved.");
    closeBioModal();
    loadRoster();
  } catch(e) { err(e.message); }
}

async function deleteChar(id) {
  if (!confirm("Delete this character permanently?")) return;
  try {
    await api("DELETE", `/api/admin/characters/${id}`);
    toast("Character deleted.");
    loadRoster();
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Codex — Species
// ---------------------------------------------------------------------------
async function loadCodex() {
  loadSpeciesList();
}

async function loadSpeciesList() {
  const items = await api("GET", "/api/admin/codex/species");
  document.getElementById("species-list").innerHTML = `
    <table class="data-table">
      <thead><tr><th>Name</th><th>Type</th><th>Speed</th><th>Homebrew</th><th>Actions</th></tr></thead>
      <tbody>${items.map(s => `
        <tr>
          <td>${s.name}</td><td>${s.creature_type}</td><td>${s.speed} ft.</td>
          <td>${s.is_homebrew ? "✅" : "—"}</td>
          <td><div class="actions">
            <button class="btn-danger" onclick="deleteSpecies(${s.id})">✕</button>
          </div></td>
        </tr>`).join("") || '<tr><td colspan="5" class="text-muted">No species loaded yet.</td></tr>'}
      </tbody>
    </table>`;
}

function showSpeciesForm() {
  document.getElementById("species-form").classList.remove("hidden");
}

async function saveSpeciesForm() {
  const name = document.getElementById("sp-name").value.trim();
  if (!name) { err("Name is required."); return; }
  let traits = [];
  try { traits = JSON.parse(document.getElementById("sp-traits").value || "[]"); } catch { err("Invalid traits JSON."); return; }
  try {
    await api("POST", "/api/admin/codex/species", {
      name,
      creature_type: document.getElementById("sp-type").value || "Humanoid",
      size_options: document.getElementById("sp-sizes").value.split(",").map(s => s.trim()).filter(Boolean) || ["Medium"],
      speed: parseInt(document.getElementById("sp-speed").value) || 30,
      traits,
    });
    toast("Species saved.");
    document.getElementById("species-form").classList.add("hidden");
    loadSpeciesList();
  } catch(e) { err(e.message); }
}

async function deleteSpecies(id) {
  if (!confirm("Delete this species?")) return;
  try { await api("DELETE", `/api/admin/codex/species/${id}`); loadSpeciesList(); }
  catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Codex — Backgrounds
// ---------------------------------------------------------------------------
async function loadBgList() {
  const items = await api("GET", "/api/admin/codex/backgrounds");
  document.getElementById("bg-list").innerHTML = `
    <table class="data-table">
      <thead><tr><th>Name</th><th>Feat</th><th>Skills</th><th>Homebrew</th><th>Actions</th></tr></thead>
      <tbody>${items.map(b => `
        <tr>
          <td>${b.name}</td><td>${b.origin_feat_name || "—"}</td>
          <td>${(b.skill_proficiencies||[]).join(", ")}</td>
          <td>${b.is_homebrew ? "✅" : "—"}</td>
          <td><div class="actions">
            <button class="btn-danger" onclick="deleteBg(${b.id})">✕</button>
          </div></td>
        </tr>`).join("") || '<tr><td colspan="5" class="text-muted">No backgrounds yet.</td></tr>'}
      </tbody>
    </table>`;
}

function showBgForm() { document.getElementById("bg-form").classList.remove("hidden"); }

async function saveBgForm() {
  const name = document.getElementById("bg-name").value.trim();
  if (!name) { err("Name required."); return; }
  let equipOpts = [];
  try { equipOpts = JSON.parse(document.getElementById("bg-equip").value || "[]"); } catch { err("Invalid equipment JSON."); return; }
  const prereqs = document.getElementById("feat-prereqs")?.value;
  try {
    await api("POST", "/api/admin/codex/backgrounds", {
      name,
      ability_score_options: document.getElementById("bg-abilities").value.split(",").map(s=>s.trim()).filter(Boolean),
      origin_feat_name: document.getElementById("bg-feat").value.trim() || null,
      skill_proficiencies: document.getElementById("bg-skills").value.split(",").map(s=>s.trim()).filter(Boolean),
      tool_proficiency: document.getElementById("bg-tool").value.trim() || null,
      language_count: parseInt(document.getElementById("bg-langs").value) || 0,
      equipment_options: equipOpts,
      description: document.getElementById("bg-desc").value,
    });
    toast("Background saved.");
    document.getElementById("bg-form").classList.add("hidden");
    loadBgList();
  } catch(e) { err(e.message); }
}

async function deleteBg(id) {
  if (!confirm("Delete this background?")) return;
  try { await api("DELETE", `/api/admin/codex/backgrounds/${id}`); loadBgList(); }
  catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Codex — Feats
// ---------------------------------------------------------------------------
async function loadFeatList() {
  const items = await api("GET", "/api/admin/codex/feats");
  const catLabels = { origin: "Origin", general: "General", fighting_style: "Fighting Style", epic_boon: "Epic Boon" };
  const catClass = { origin: "badge-origin", general: "badge-general", fighting_style: "badge-fs", epic_boon: "badge-boon" };
  document.getElementById("feat-list").innerHTML = `
    <table class="data-table">
      <thead><tr><th>Name</th><th>Category</th><th>Homebrew</th><th>Actions</th></tr></thead>
      <tbody>${items.map(f => `
        <tr>
          <td>${f.name}</td>
          <td><span class="badge ${catClass[f.category]||''}">${catLabels[f.category]||f.category}</span></td>
          <td>${f.is_homebrew ? "✅" : "—"}</td>
          <td><div class="actions">
            <button class="btn-danger" onclick="deleteFeat(${f.id})">✕</button>
          </div></td>
        </tr>`).join("") || '<tr><td colspan="4" class="text-muted">No feats yet.</td></tr>'}
      </tbody>
    </table>`;
}

function showFeatForm() { document.getElementById("feat-form").classList.remove("hidden"); }

async function saveFeatForm() {
  const name = document.getElementById("feat-name").value.trim();
  if (!name) { err("Name required."); return; }
  const prereqRaw = document.getElementById("feat-prereqs").value.trim();
  const prerequisites = prereqRaw ? prereqRaw.split(",").map(s=>s.trim()) : null;
  try {
    await api("POST", "/api/admin/codex/feats", {
      name,
      category: document.getElementById("feat-cat").value,
      prerequisites,
      description: document.getElementById("feat-desc").value,
    });
    toast("Feat saved.");
    document.getElementById("feat-form").classList.add("hidden");
    loadFeatList();
  } catch(e) { err(e.message); }
}

async function deleteFeat(id) {
  if (!confirm("Delete this feat?")) return;
  try { await api("DELETE", `/api/admin/codex/feats/${id}`); loadFeatList(); }
  catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Grimoire
// ---------------------------------------------------------------------------
async function loadGrimoireSpells() {
  const level = document.getElementById("spell-filter-level")?.value;
  const items = await api("GET", `/api/content/spells${level ? "?level=" + level : ""}`);
  document.getElementById("grimoire-list").innerHTML = `
    <table class="data-table grimoire-table">
      <thead><tr>
        <th>Name</th><th>Level</th><th>School</th>
        <th>Cast Time</th><th>Range</th><th>Duration</th><th>Components</th>
        <th>Classes</th><th>Actions</th>
      </tr></thead>
      <tbody>${items.map(s => {
        const tags = [s.concentration ? "Concentration" : null, s.ritual ? "Ritual" : null].filter(Boolean).map(t => `<span class="feature-badge">${t}</span>`).join(" ");
        const descRow = s.description ? `<tr class="grimoire-desc-row" id="gdesc-${s.id}" style="display:none"><td colspan="9"><div class="grimoire-desc">${s.description.replace(/\n/g,"<br>")}</div></td></tr>` : "";
        return `<tr class="grimoire-main-row" onclick="toggleGrimoireDesc(${s.id})" style="cursor:pointer">
          <td><strong>${s.name}</strong> ${tags}</td>
          <td>${s.level === 0 ? "Cantrip" : s.level}</td>
          <td>${s.school || "—"}</td>
          <td>${s.casting_time || "—"}</td>
          <td>${s.spell_range || "—"}</td>
          <td>${s.duration || "—"}</td>
          <td style="font-size:0.8rem">${s.components || "—"}</td>
          <td style="font-size:0.8rem">${(s.classes||[]).join(", ") || "—"}</td>
          <td><div class="actions">
            ${s.is_homebrew ? `<button class="btn-danger" onclick="event.stopPropagation();deleteSpell(${s.id})">✕</button>` : "—"}
          </div></td>
        </tr>${descRow}`;
      }).join("") || '<tr><td colspan="9" class="text-muted">No spells loaded yet.</td></tr>'}
      </tbody>
    </table>`;
}

function toggleGrimoireDesc(id) {
  const row = document.getElementById(`gdesc-${id}`);
  if (row) row.style.display = row.style.display === "none" ? "table-row" : "none";
}

function showSpellForm() { document.getElementById("spell-form").classList.remove("hidden"); }

async function saveSpellForm() {
  const name = document.getElementById("spell-name").value.trim();
  if (!name) { err("Name required."); return; }
  try {
    await api("POST", "/api/admin/grimoire/spells", {
      name,
      level: parseInt(document.getElementById("spell-level").value) || 0,
      school: document.getElementById("spell-school").value,
      casting_time: document.getElementById("spell-cast-time").value,
      spell_range: document.getElementById("spell-range").value,
      components: document.getElementById("spell-components").value,
      duration: document.getElementById("spell-duration").value,
      concentration: document.getElementById("spell-conc").checked,
      ritual: document.getElementById("spell-ritual").checked,
      classes: document.getElementById("spell-classes").value.split(",").map(s=>s.trim()).filter(Boolean),
      description: document.getElementById("spell-desc").value,
    });
    toast("Spell saved.");
    document.getElementById("spell-form").classList.add("hidden");
    loadGrimoireSpells();
  } catch(e) { err(e.message); }
}

async function deleteSpell(id) {
  if (!confirm("Delete this spell?")) return;
  try { await api("DELETE", `/api/admin/grimoire/spells/${id}`); loadGrimoireSpells(); }
  catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Import & Seed
// ---------------------------------------------------------------------------
async function runImport() {
  const type = document.getElementById("import-type").value;
  let data;
  try { data = JSON.parse(document.getElementById("import-json").value); }
  catch { err("Invalid JSON."); return; }
  try {
    const r = await api("POST", `/api/admin/import/${type}`, data);
    document.getElementById("import-result").textContent = `✓ Imported: ${r.added} new records.`;
  } catch(e) { err(e.message); }
}

async function triggerSeed() {
  document.getElementById("seed-result").textContent = "Seeding…";
  try {
    const r = await api("POST", "/api/admin/seed");
    const counts = Object.entries(r.seeded).map(([k,v]) => `${k}: ${v}`).join(", ");
    document.getElementById("seed-result").textContent = `✓ Seeded — ${counts}`;
  } catch(e) { err(e.message); document.getElementById("seed-result").textContent = ""; }
}

async function convertGold() {
  const el = document.getElementById("gold-result");
  el.textContent = "Converting…";
  try {
    const r = await api("POST", "/api/admin/convert-gold");
    el.textContent = `✓ Converted ${r.converted} Gold row(s) to currency.gp`;
  } catch(e) { err(e.message); el.textContent = ""; }
}

async function refreshSpells() {
  const el = document.getElementById("spell-refresh-result");
  el.textContent = "Refreshing…";
  try {
    const r = await api("POST", "/api/admin/refresh-spells");
    el.textContent = r.refreshed > 0
      ? `✓ Updated ${r.refreshed} spell(s)`
      : "✓ All spells already have descriptions — nothing to update";
  } catch(e) { err(e.message); el.textContent = ""; }
}

async function repairSchema() {
  const el = document.getElementById("repair-result");
  el.textContent = "Repairing…";
  try {
    const r = await api("POST", "/api/admin/repair-schema");
    el.textContent = `✓ Done — ${r.applied.join("; ")}`;
  } catch(e) { err(e.message); el.textContent = ""; }
}

async function backfillSpeciesSpells() {
  const el = document.getElementById("backfill-result");
  el.textContent = "Running backfill…";
  try {
    const r = await api("POST", "/api/admin/backfill-species-spells");
    const lines = r.characters.filter(c => c.added > 0).map(c => `${c.character}: +${c.added}`).join(", ");
    el.textContent = `✓ Total added: ${r.total_added}${lines ? ` (${lines})` : " — nothing new to add"}`;
  } catch(e) { err(e.message); el.textContent = ""; }
}

// ---------------------------------------------------------------------------
// Lore management
// ---------------------------------------------------------------------------

const LORE_CATEGORY_LABELS = { world: "The World", species: "Species", campaign: "Campaign" };

async function loadLore() {
  const el = document.getElementById("lore-admin-list");
  el.innerHTML = `<p class="hint">Loading…</p>`;
  const pages = await api("GET", "/api/admin/lore");
  if (!pages || !pages.length) {
    el.innerHTML = `<p class="hint">No lore pages found. Run Seed Database from the Import tab.</p>`;
    return;
  }

  const groups = {};
  for (const p of pages) {
    if (!groups[p.category]) groups[p.category] = [];
    groups[p.category].push(p);
  }

  const order = ["world", "species", "campaign"];
  const cats = [...order.filter(c => groups[c]), ...Object.keys(groups).filter(c => !order.includes(c))];

  el.innerHTML = cats.map(cat => `
    <div class="mb-md">
      <h4 style="color:var(--color-gold);margin:12px 0 6px">${LORE_CATEGORY_LABELS[cat] || cat}</h4>
      <table class="admin-table">
        <thead><tr><th>Title</th><th>Slug</th><th style="width:100px;text-align:center">Player View</th><th style="width:80px"></th></tr></thead>
        <tbody>
          ${groups[cat].map(p => `
            <tr id="lore-row-${p.slug}">
              <td><strong>${p.title}</strong></td>
              <td><code style="font-size:0.8em">${p.slug}</code></td>
              <td style="text-align:center">
                <label class="lore-toggle">
                  <input type="checkbox" ${p.player_visible ? "checked" : ""} onchange="setLoreVisibility('${p.slug}', this.checked)">
                  <span>${p.player_visible ? "Visible" : "Hidden"}</span>
                </label>
              </td>
              <td><button onclick="previewLore('${p.slug}')">Preview</button></td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`).join("");
}

async function setLoreVisibility(slug, visible) {
  try {
    await api("PATCH", `/api/admin/lore/${slug}/visibility?visible=${visible}`);
    const row = document.getElementById(`lore-row-${slug}`);
    if (row) {
      const span = row.querySelector("label.lore-toggle span");
      if (span) span.textContent = visible ? "Visible" : "Hidden";
    }
    toast(visible ? `"${slug}" now visible to players` : `"${slug}" hidden from players`);
  } catch(e) { err(e.message); }
}

async function previewLore(slug) {
  const modal = document.getElementById("lore-preview-modal");
  const titleEl = document.getElementById("lore-preview-title");
  const body = document.getElementById("lore-preview-body");
  modal.classList.remove("hidden");
  modal.style.display = "flex";
  body.innerHTML = `<p class="hint">Loading…</p>`;
  try {
    const page = await api("GET", `/api/admin/lore/${slug}`);
    titleEl.textContent = page.title;
    body.innerHTML = `<div class="lore-md">${marked.parse(page.content_md)}</div>`;
  } catch(e) { body.innerHTML = `<p class="hint">Error: ${e.message}</p>`; }
}

function closeLorePreview() {
  const modal = document.getElementById("lore-preview-modal");
  modal.classList.add("hidden");
  modal.style.display = "none";
}

// ---------------------------------------------------------------------------
// Admin Edit Panel — proficiencies, masteries, background
// ---------------------------------------------------------------------------

const ALL_SKILLS_ADMIN = [
  "Acrobatics","Animal Handling","Arcana","Athletics","Deception",
  "History","Insight","Intimidation","Investigation","Medicine",
  "Nature","Perception","Performance","Persuasion","Religion",
  "Sleight of Hand","Stealth","Survival",
];

let _editCharId = null;
let _allBgsAdmin = [];

async function openEditPanel(charId) {
  _editCharId = charId;
  // Fetch char detail + background list in parallel
  const [detail, bgs] = await Promise.all([
    api("GET", `/api/admin/characters/${charId}/detail`),
    _allBgsAdmin.length ? Promise.resolve(_allBgsAdmin) : api("GET", "/api/admin/codex/backgrounds"),
  ]);
  _allBgsAdmin = bgs;

  const skillSet = new Set(detail.skills.map(s => s.name));
  const expertSet = new Set(detail.skills.filter(s => s.expertise).map(s => s.name));

  const skillCheckboxes = ALL_SKILLS_ADMIN.map(s => `
    <label class="ep-skill-row">
      <input type="checkbox" class="ep-skill-cb" value="${s}" ${skillSet.has(s) ? "checked" : ""}>
      ${s}
      <input type="checkbox" class="ep-expert-cb" value="${s}" ${expertSet.has(s) ? "checked" : ""}
        title="Expertise" style="margin-left:8px" ${skillSet.has(s) ? "" : "disabled"}>
      <span style="font-size:0.75rem;opacity:0.6">exp</span>
    </label>`).join("");

  const bgOptions = bgs.map(b =>
    `<option value="${b.id}" ${b.id === detail.background_id ? "selected" : ""}>${b.name}</option>`
  ).join("");

  const overlay = document.createElement("div");
  overlay.id = "ep-overlay";
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal-box ep-modal">
      <div class="modal-header">
        <h3>Edit — ${detail.character_name}</h3>
        <button class="modal-close-btn" onclick="closeEditPanel()">✕</button>
      </div>

      <div class="ep-section">
        <h4>Background</h4>
        <select id="ep-bg-select" class="ep-select">
          <option value="">— no change —</option>
          ${bgOptions}
        </select>
        <p class="hint" style="margin-top:4px">Changing background re-applies its skill profs, tool prof, and origin feat.</p>
      </div>

      <div class="ep-section">
        <h4>Skill Proficiencies <span class="hint">(check = proficient · "exp" = expertise)</span></h4>
        <div class="ep-skill-grid">${skillCheckboxes}</div>
      </div>

      <div class="ep-section">
        <h4>Tool Proficiencies <span class="hint">(one per line)</span></h4>
        <textarea id="ep-tools" class="ep-textarea" rows="4">${detail.tools.join("\n")}</textarea>
      </div>

      <div class="ep-section">
        <h4>Languages <span class="hint">(one per line)</span></h4>
        <textarea id="ep-langs" class="ep-textarea" rows="4">${detail.languages.join("\n")}</textarea>
      </div>

      <div class="ep-section">
        <h4>Weapon Masteries <span class="hint">(one per line)</span></h4>
        <textarea id="ep-masteries" class="ep-textarea" rows="3">${detail.masteries.join("\n")}</textarea>
      </div>

      <div class="ep-footer">
        <button class="btn-primary" onclick="saveEditPanel()">Save Changes</button>
        <button onclick="closeEditPanel()">Cancel</button>
      </div>
    </div>`;

  // Sync expertise checkboxes with skill checkboxes
  overlay.addEventListener("change", e => {
    if (e.target.classList.contains("ep-skill-cb")) {
      const val = e.target.value;
      const expertCb = overlay.querySelector(`.ep-expert-cb[value="${val}"]`);
      if (expertCb) {
        expertCb.disabled = !e.target.checked;
        if (!e.target.checked) expertCb.checked = false;
      }
    }
  });

  document.body.appendChild(overlay);
}

function closeEditPanel() {
  document.getElementById("ep-overlay")?.remove();
}

async function saveEditPanel() {
  const id = _editCharId;
  const errs = [];

  // Background change
  const bgSelect = document.getElementById("ep-bg-select");
  const bgId = bgSelect?.value ? parseInt(bgSelect.value) : null;
  if (bgId) {
    try { await api("PATCH", `/api/admin/characters/${id}/background`, { background_id: bgId }); }
    catch(e) { errs.push("Background: " + e.message); }
  }

  // Proficiencies
  const skillCbs = [...document.querySelectorAll(".ep-skill-cb:checked")];
  const skills = skillCbs.map(cb => cb.value);
  const expertise = [...document.querySelectorAll(".ep-expert-cb:checked")].map(cb => cb.value);
  const tools = document.getElementById("ep-tools").value.split("\n").map(s => s.trim()).filter(Boolean);
  const langs = document.getElementById("ep-langs").value.split("\n").map(s => s.trim()).filter(Boolean);
  try {
    await api("PATCH", `/api/admin/characters/${id}/proficiencies`, { skills, expertise, tools, languages: langs });
  } catch(e) { errs.push("Proficiencies: " + e.message); }

  // Masteries
  const masteries = document.getElementById("ep-masteries").value.split("\n").map(s => s.trim()).filter(Boolean);
  try {
    await api("PATCH", `/api/admin/characters/${id}/masteries`, { weapon_names: masteries });
  } catch(e) { errs.push("Masteries: " + e.message); }

  if (errs.length) { err(errs.join("; ")); return; }
  toast("Changes saved.");
  closeEditPanel();
  loadRoster();
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  const res = await fetch("/auth/me");
  if (res.status === 401) { window.location.href = "/auth/login"; return; }
  if (res.status === 403) { document.body.innerHTML = "<div style='padding:2rem;font-family:serif'>Access denied.</div>"; return; }
  const user = await res.json();

  const badge = document.getElementById("user-badge");
  if (badge) {
    document.getElementById("user-name").textContent = user.name || user.email;
    badge.style.display = "flex";
  }

  loadRoster();
}

boot();
