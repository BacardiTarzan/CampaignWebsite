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
  ["roster", "codex", "grimoire", "lore", "import", "combat"].forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    if (el) el.classList.toggle("hidden", t !== tab);
  });
  if (tab === "roster") loadRoster();
  if (tab === "codex") loadCodex();
  if (tab === "grimoire") loadGrimoireSpells();
  if (tab === "lore") loadLore();
  if (tab === "combat") loadCombat();
}

function switchCodexTab(sub) {
  document.querySelectorAll("#tab-codex .tab-bar .tab-btn").forEach(b => b.classList.remove("active"));
  event.target.classList.add("active");
  ["species", "backgrounds", "feats", "monsters", "items"].forEach(t =>
    document.getElementById(`codex-${t}`).classList.toggle("hidden", t !== sub));
  if (sub === "species") loadSpeciesList();
  if (sub === "backgrounds") loadBgList();
  if (sub === "feats") loadFeatList();
  if (sub === "monsters") loadMonsters();
  if (sub === "items") loadItemList();
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
  const tbody = chars.map((c, i) => {
    const restsGroup = c.hp_max ? `
        <button onclick="event.stopPropagation();adminRest(${c.id})">💤 Long</button>
        <button onclick="event.stopPropagation();adminShortRest(${c.id})">⏱ Short</button>` : "";
    const lockGroup = `
        ${c.physical_locked ? `<button onclick="event.stopPropagation();unlockPhysical(${c.id})">🔓 Physical</button>` : ""}
        <button onclick="event.stopPropagation();editBio(${c.id})">📜 Bio</button>
        <button onclick="event.stopPropagation();openEditPanel(${c.id})">✏ Edit</button>`;
    const statsBtn = !c.is_complete
      ? `<button onclick="event.stopPropagation();unlockStats(${c.id})">🔓 Stats</button>` : "";
    return `
    <tr class="roster-row" onclick="window.open('/characters/${c.id}/sheet','_blank')" title="Open sheet">
      <td>${i + 1}</td>
      <td><span class="roster-name" id="name-${c.id}" onclick="event.stopPropagation();editCharName(${c.id})" title="Click to rename">${c.character_name}</span></td>
      <td>${c.created_by_display_name}</td>
      <td>${c.species_name || "—"}</td>
      <td>${c.class_name || "—"} ${c.level ? "Lv " + c.level : ""}</td>
      <td>${c.background_name || "—"}</td>
      <td>${c.is_complete ? "✅ Done" : `Step ${c.wizard_step}`}</td>
      <td onclick="event.stopPropagation()"><div class="actions">
        <button onclick="levelUp(${c.id})" title="Grant level (current: ${c.level}, granted: ${c.level_granted ?? c.level})">+Lv ${c.level_granted != null && c.level_granted > c.level ? `<span style="color:#8fc88f">(${c.level}→${c.level_granted})</span>` : ""}</button>
        ${restsGroup}
        ${lockGroup}
        ${statsBtn}
        <a href="/api/admin/characters/${c.id}/export/json" target="_blank" onclick="event.stopPropagation()"><button>⬇ JSON</button></a>
        <button class="btn-danger" onclick="event.stopPropagation();deleteChar(${c.id})">✕</button>
      </div></td>
    </tr>`;
  }).join("");
  document.getElementById("roster-table").innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>#</th><th>Character</th><th>Player</th><th>Species</th>
        <th>Class</th><th>Background</th><th>Status</th><th>Actions</th>
      </tr></thead>
      <tbody>${tbody || '<tr><td colspan="8" class="text-muted">No characters yet.</td></tr>'}</tbody>
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
// Codex — Items
// ---------------------------------------------------------------------------

const WEAPON_PROPERTIES = ["Ammunition","Finesse","Heavy","Light","Loading","Range","Reach","Special","Thrown","Two-Handed","Versatile"];
const WEAPON_MASTERIES   = ["Cleave","Graze","Nick","Push","Sap","Slow","Topple","Vex"];
const DAMAGE_TYPES       = ["Slashing","Piercing","Bludgeoning","Acid","Cold","Fire","Force","Lightning","Necrotic","Poison","Psychic","Radiant","Thunder"];
const CATEGORY_HINTS     = {
  weapon: ["Simple Melee","Simple Ranged","Martial Melee","Martial Ranged"],
  armor:  ["Light","Medium","Heavy"],
  shield: ["Shield"],
};

let _editingItemId = null;
let _itemListCache = [];

const _DMG_TYPE_OPTIONS = ["","Slashing","Piercing","Bludgeoning","Acid","Cold","Fire","Force","Lightning","Necrotic","Poison","Psychic","Radiant","Thunder"]
  .map(t => `<option value="${t}">${t || "— none —"}</option>`).join("");

function _renderDmgRolls(rolls) {
  const c = document.getElementById("damage-rolls-container");
  if (!c) return;
  c.innerHTML = "";
  const addedRolls = rolls.length ? rolls : [{ dice: "", type: "" }];
  addedRolls.forEach((r, i) => {
    const row = document.createElement("div");
    row.className = "flex-row";
    row.style.cssText = "gap:0.4rem;align-items:center";
    row.innerHTML = `
      <input type="text" class="dmg-dice" value="${r.dice || ""}" placeholder="e.g. 1d8" style="width:6rem">
      <select class="dmg-type">${_DMG_TYPE_OPTIONS}</select>
      ${i > 0 ? `<button type="button" onclick="this.parentElement.remove()" style="padding:0.1rem 0.4rem;font-size:0.85rem">−</button>` : ""}`;
    row.querySelector(".dmg-type").value = r.type || "";
    c.appendChild(row);
  });
}

function addDmgRoll() {
  const c = document.getElementById("damage-rolls-container");
  if (!c) return;
  const row = document.createElement("div");
  row.className = "flex-row";
  row.style.cssText = "gap:0.4rem;align-items:center";
  row.innerHTML = `
    <input type="text" class="dmg-dice" value="" placeholder="e.g. 1d6" style="width:6rem">
    <select class="dmg-type">${_DMG_TYPE_OPTIONS}</select>
    <button type="button" onclick="this.parentElement.remove()" style="padding:0.1rem 0.4rem;font-size:0.85rem">−</button>`;
  c.appendChild(row);
}

function _collectDmgRolls() {
  const rows = document.querySelectorAll("#damage-rolls-container .flex-row");
  const result = [];
  rows.forEach(row => {
    const dice = row.querySelector(".dmg-dice")?.value.trim();
    const type = row.querySelector(".dmg-type")?.value || "";
    if (dice) result.push({ dice, type });
  });
  return result.length ? result : null;
}

function _buildPropCheckboxes() {
  const container = document.getElementById("item-props-checkboxes");
  if (!container) return;
  container.innerHTML = WEAPON_PROPERTIES.map(p =>
    `<label style="display:flex;align-items:center;gap:0.25rem;font-size:0.85rem">
       <input type="checkbox" class="item-prop-cb" value="${p}"> ${p}
     </label>`
  ).join("");
}

function onItemTypeChange() {
  const t = document.getElementById("item-type").value;
  document.getElementById("item-weapon-fields").classList.toggle("hidden", t !== "weapon");
  document.getElementById("item-armor-fields").classList.toggle("hidden", t !== "armor" && t !== "shield");
  const hints = CATEGORY_HINTS[t] || [];
  const catEl = document.getElementById("item-category");
  catEl.placeholder = hints.length ? hints.join(" / ") : "e.g. Adventuring Gear";
  if (t === "shield") {
    const ac = document.getElementById("item-ac-formula");
    if (!ac.value) ac.value = "+2";
  }
}

async function loadItemList() {
  _itemListCache = await api("GET", "/api/admin/codex/equipment");
  // Populate datalist for base-weapon autocomplete from all weapon-type items
  const dl = document.getElementById("weapon-names-datalist");
  if (dl) {
    const weaponNames = _itemListCache.filter(i => i.item_type === "weapon").map(i => i.name);
    dl.innerHTML = weaponNames.map(n => `<option value="${n}">`).join("");
  }
  const typeLabel = t => t ? t.charAt(0).toUpperCase() + t.slice(1) : "—";
  document.getElementById("item-list").innerHTML = `
    <table class="data-table">
      <thead><tr><th>Name</th><th>Type</th><th>Category</th><th>Damage / AC</th><th>Mastery</th><th>Homebrew</th><th>Actions</th></tr></thead>
      <tbody>${_itemListCache.map(item => `
        <tr>
          <td><strong>${item.name}</strong></td>
          <td>${typeLabel(item.item_type)}</td>
          <td>${item.category || "—"}</td>
          <td>${item.damage ? `${item.damage} ${item.damage_type||""}`.trim() : item.ac_formula || "—"}</td>
          <td>${item.mastery_property || "—"}</td>
          <td>${item.is_homebrew ? "✅" : "—"}</td>
          <td><div class="actions">
            <button onclick="editItem(${item.id})">✎</button>
            <button class="btn-danger" onclick="deleteItem(${item.id})">✕</button>
          </div></td>
        </tr>`).join("") || '<tr><td colspan="7" class="text-muted">No items yet.</td></tr>'}
      </tbody>
    </table>`;
}

function showItemForm(item = null) {
  _editingItemId = item ? item.id : null;
  _buildPropCheckboxes();
  // Reset
  ["item-name","item-category","item-cost","item-weight","item-props-custom",
   "item-ac-formula","item-desc","item-weapon-magic-bonus","item-armor-magic-bonus",
   "item-proficiency-base"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  document.getElementById("item-source").value = "Homebrew";
  document.getElementById("item-homebrew").checked = true;
  document.getElementById("item-stealth-disadv").checked = false;
  document.getElementById("item-str-req").value = "";
  document.getElementById("item-mastery").value = "";
  document.getElementById("item-mastery-custom").value = "";
  document.getElementById("item-mastery-custom").classList.add("hidden");
  _renderDmgRolls([]);

  if (item) {
    document.getElementById("item-name").value = item.name || "";
    document.getElementById("item-type").value = item.item_type || "weapon";
    document.getElementById("item-category").value = item.category || "";
    document.getElementById("item-cost").value = item.cost || "";
    document.getElementById("item-weight").value = item.weight || "";
    document.getElementById("item-source").value = item.source || "Homebrew";
    document.getElementById("item-homebrew").checked = !!item.is_homebrew;
    document.getElementById("item-desc").value = item.description || "";
    // Weapon
    document.getElementById("item-damage").value = item.damage || "";
    document.getElementById("item-damage-type").value = item.damage_type || "";
    const mastery = item.mastery_property || "";
    if (mastery && !WEAPON_MASTERIES.includes(mastery)) {
      document.getElementById("item-mastery").value = "__custom__";
      document.getElementById("item-mastery-custom").value = mastery;
      document.getElementById("item-mastery-custom").classList.remove("hidden");
    } else {
      document.getElementById("item-mastery").value = mastery;
    }
    const props = Array.isArray(item.properties) ? item.properties : [];
    const standardProps = WEAPON_PROPERTIES;
    const customProps = props.filter(p => !standardProps.includes(p));
    document.querySelectorAll(".item-prop-cb").forEach(cb => {
      cb.checked = props.includes(cb.value);
    });
    document.getElementById("item-props-custom").value = customProps.join(", ");
    // Weapon proficiency base
    document.getElementById("item-proficiency-base").value = item.proficiency_base || "";
    // Weapon magic
    document.getElementById("item-weapon-magic-bonus").value = item.magic_bonus ?? "";
    // Damage rolls
    const rolls = item.damage_rolls?.length ? item.damage_rolls
      : (item.damage ? [{ dice: item.damage, type: item.damage_type || "" }] : []);
    _renderDmgRolls(rolls);
    // Armor
    document.getElementById("item-ac-formula").value = item.ac_formula || "";
    document.getElementById("item-str-req").value = item.strength_req || "";
    document.getElementById("item-stealth-disadv").checked = !!item.stealth_disadvantage;
    document.getElementById("item-armor-magic-bonus").value = item.magic_bonus ?? "";
  }

  onItemTypeChange();
  document.getElementById("item-form").classList.remove("hidden");
}

function editItem(id) {
  const item = _itemListCache.find(i => i.id === id);
  if (item) showItemForm(item);
}

function cancelItemForm() {
  document.getElementById("item-form").classList.add("hidden");
  _editingItemId = null;
}

document.addEventListener("change", e => {
  if (e.target.id === "item-mastery") {
    document.getElementById("item-mastery-custom").classList.toggle("hidden", e.target.value !== "__custom__");
  }
});

async function saveItemForm() {
  const name = document.getElementById("item-name").value.trim();
  if (!name) { err("Name required."); return; }
  const itemType = document.getElementById("item-type").value;

  const checkedProps = [...document.querySelectorAll(".item-prop-cb:checked")].map(cb => cb.value);
  const customPropRaw = document.getElementById("item-props-custom").value.trim();
  const customProps = customPropRaw ? customPropRaw.split(",").map(s => s.trim()).filter(Boolean) : [];
  const properties = [...checkedProps, ...customProps];

  const masteryEl = document.getElementById("item-mastery");
  const mastery = masteryEl.value === "__custom__"
    ? document.getElementById("item-mastery-custom").value.trim()
    : masteryEl.value || null;

  const strReq = document.getElementById("item-str-req").value;
  const isWeapon = itemType === "weapon";
  const magicRaw = isWeapon
    ? document.getElementById("item-weapon-magic-bonus").value
    : document.getElementById("item-armor-magic-bonus").value;

  const body = {
    name,
    item_type: itemType,
    category: document.getElementById("item-category").value.trim() || null,
    cost: document.getElementById("item-cost").value.trim() || null,
    weight: document.getElementById("item-weight").value.trim() || null,
    source: document.getElementById("item-source").value.trim() || "Homebrew",
    is_homebrew: document.getElementById("item-homebrew").checked,
    description: document.getElementById("item-desc").value.trim() || null,
    properties: properties.length ? properties : null,
    mastery_property: mastery || null,
    ac_formula: document.getElementById("item-ac-formula").value.trim() || null,
    strength_req: strReq ? parseInt(strReq) : null,
    stealth_disadvantage: document.getElementById("item-stealth-disadv").checked,
    magic_bonus: magicRaw !== "" ? parseInt(magicRaw) : null,
    damage_rolls: isWeapon ? _collectDmgRolls() : null,
    proficiency_base: isWeapon ? (document.getElementById("item-proficiency-base").value.trim() || null) : null,
  };

  try {
    if (_editingItemId) {
      await api("PUT", `/api/admin/codex/equipment/${_editingItemId}`, body);
      toast("Item updated.");
    } else {
      await api("POST", "/api/admin/codex/equipment", body);
      toast("Item created.");
    }
    cancelItemForm();
    loadItemList();
  } catch(e) { err(e.message); }
}

async function deleteItem(id) {
  if (!confirm("Delete this item?")) return;
  try { await api("DELETE", `/api/admin/codex/equipment/${id}`); loadItemList(); }
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

async function backfillClassSpells() {
  const el = document.getElementById("backfill-class-result");
  el.textContent = "Running backfill…";
  try {
    const r = await api("POST", "/api/admin/backfill-class-spells");
    const lines = r.characters.map(c => `${c.character}: +${c.added}`).join(", ");
    el.textContent = `✓ Total added: ${r.total_added}${lines ? ` (${lines})` : " — nothing new to add"}`;
  } catch(e) { err(e.message); el.textContent = ""; }
}

async function backfillPreparedCasterSpells() {
  const el = document.getElementById("backfill-prepared-result");
  el.textContent = "Running backfill…";
  try {
    const r = await api("POST", "/api/admin/backfill-prepared-caster-spells");
    const lines = r.characters.map(c => `${c.character}: +${c.added}`).join(", ");
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
  body.innerHTML = `<p class="hint">Loading…</p>`;
  try {
    const page = await api("GET", `/api/admin/lore/${slug}`);
    titleEl.textContent = page.title;
    body.innerHTML = `<div class="lore-md">${marked.parse(page.content_md)}</div>`;
  } catch(e) { body.innerHTML = `<p class="hint">Error: ${e.message}</p>`; }
}

function closeLorePreview() {
  document.getElementById("lore-preview-modal").classList.add("hidden");
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

const ALL_LANGUAGES_ADMIN = [
  "Common","Common Sign Language","Draconic","Dwarvish","Elvish",
  "Giant","Gnomish","Goblin","Halfling","Orc",
  "Druidic","Thieves' Cant",
  "Abyssal","Celestial","Deep Speech","Infernal","Primordial","Sylvan","Undercommon",
];

let _editCharId = null;
let _allBgsAdmin = [];

// Maps UI category names → DB category strings on weapon rows (data-tip-cat)
const CAT_TO_DB_CATS = {
  "Simple Weapons":               ["Simple Melee", "Simple Ranged"],
  "Simple Melee Weapons":         ["Simple Melee"],
  "Simple Ranged Weapons":        ["Simple Ranged"],
  "Martial Weapons":              ["Martial Melee", "Martial Ranged"],
  "Martial Melee Weapons":        ["Martial Melee"],
  "Martial Ranged Weapons":       ["Martial Ranged"],
  "Simple or Martial Melee Weapons": ["Simple Melee", "Martial Melee"],
  "All Weapons":                  ["Simple Melee", "Simple Ranged", "Martial Melee", "Martial Ranged"],
};

function toggleWeaponCategory(cat) {
  const dbCats = CAT_TO_DB_CATS[cat] || [];
  const overlay = document.getElementById("ep-overlay");
  if (!overlay) return;
  const rows = [...overlay.querySelectorAll(".ep-weapon-row")]
    .filter(r => dbCats.includes(r.dataset.tipCat));
  const anyChecked = rows.some(r => r.querySelector(".ep-wprof-cb")?.checked);
  for (const row of rows) {
    const cb = row.querySelector(".ep-wprof-cb");
    if (cb) cb.checked = !anyChecked;
  }
}

async function openEditPanel(charId) {
  _editCharId = charId;
  const [detail, bgs] = await Promise.all([
    api("GET", `/api/admin/characters/${charId}/detail`),
    _allBgsAdmin.length ? Promise.resolve(_allBgsAdmin) : api("GET", "/api/admin/codex/backgrounds"),
  ]);
  _allBgsAdmin = bgs;

  const skillSet = new Set(detail.skills.map(s => s.name));
  const expertSet = new Set(detail.skills.filter(s => s.expertise).map(s => s.name));
  const toolSet = new Set(detail.tools);
  const langSet = new Set(detail.languages);
  const masterySet = new Set(detail.masteries);
  const wprofSet = new Set(detail.weapon_proficiencies || []);

  // Weapon proficiency categories
  const WP_CATEGORIES = [
    "Simple Weapons",
    "Simple Melee Weapons",
    "Simple Ranged Weapons",
    "Martial Weapons",
    "Martial Melee Weapons",
    "Martial Ranged Weapons",
    "Simple or Martial Melee Weapons",
    "All Weapons",
  ];

  const categoryButtons = WP_CATEGORIES.map(cat =>
    `<button type="button" class="ep-cat-btn" onclick="toggleWeaponCategory('${cat}')">${cat}</button>`
  ).join("");

  // Per-weapon rows: Prof checkbox + Mastery checkbox side by side
  const weaponRows = (detail.all_weapons || []).map(w => {
    const dmgStr = [w.damage, w.damage_type].filter(Boolean).join(" ");
    const propsStr = (w.properties || []).join(", ");
    const masteryTag = w.mastery ? `<span class="ep-mastery-tag">${w.mastery}</span>` : "";
    return `<div class="ep-weapon-row"
        data-tip-name="${w.name}"
        data-tip-cat="${w.category}"
        data-tip-damage="${dmgStr}"
        data-tip-props="${propsStr}"
        data-tip-mastery="${w.mastery || ""}"
        onmouseenter="showWeaponTip(this,event)" onmouseleave="hideWeaponTip()">
      <span class="ep-weapon-name">${w.name}</span>
      <label class="ep-weapon-cb-label" title="Proficient">
        <input type="checkbox" class="ep-wprof-cb" value="${w.name}" ${wprofSet.has(w.name) ? "checked" : ""}> Prof
      </label>
      <label class="ep-weapon-cb-label" title="Mastery${w.mastery ? ': ' + w.mastery : ''}">
        <input type="checkbox" class="ep-mastery-cb" value="${w.name}" ${masterySet.has(w.name) ? "checked" : ""}
          ${!w.mastery ? "disabled" : ""}> Mastery${masteryTag}
      </label>
    </div>`;
  }).join("");

  // Skill checkboxes with expertise toggle
  const skillCheckboxes = ALL_SKILLS_ADMIN.map(s => `
    <label class="ep-skill-row">
      <input type="checkbox" class="ep-skill-cb" value="${s}" ${skillSet.has(s) ? "checked" : ""}>
      ${s}
      <input type="checkbox" class="ep-expert-cb" value="${s}" ${expertSet.has(s) ? "checked" : ""}
        title="Expertise" style="margin-left:8px" ${skillSet.has(s) ? "" : "disabled"}>
      <span style="font-size:0.75rem;opacity:0.6">exp</span>
    </label>`).join("");

  // Tool checkboxes from DB
  const toolCheckboxes = (detail.all_tools || []).map(name => `
    <label class="ep-cb-row">
      <input type="checkbox" class="ep-tool-cb" value="${name}" ${toolSet.has(name) ? "checked" : ""}>
      ${name}
    </label>`).join("");

  // Language checkboxes from fixed list; extras shown in freeform field
  const knownLangs = new Set(ALL_LANGUAGES_ADMIN);
  const extraLangs = detail.languages.filter(l => !knownLangs.has(l));
  const langCheckboxes = ALL_LANGUAGES_ADMIN.map(l => `
    <label class="ep-cb-row">
      <input type="checkbox" class="ep-lang-cb" value="${l}" ${langSet.has(l) ? "checked" : ""}>
      ${l}
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

      <div class="ep-body">
      <div class="ep-section">
        <h4>Background</h4>
        <select id="ep-bg-select" class="ep-select">
          <option value="">— no change —</option>
          ${bgOptions}
        </select>
        <p class="hint" style="margin-top:4px">Re-applies background skill profs, tool prof, and origin feat.</p>
      </div>

      <div class="ep-section">
        <h4>Skill Proficiencies <span class="hint">· "exp" = expertise</span></h4>
        <div class="ep-skill-grid">${skillCheckboxes}</div>
      </div>

      <div class="ep-section">
        <h4>Tool Proficiencies</h4>
        <div class="ep-cb-grid">${toolCheckboxes}</div>
      </div>

      <div class="ep-section">
        <h4>Languages</h4>
        <div class="ep-cb-grid">${langCheckboxes}</div>
        ${extraLangs.length ? `<p class="hint" style="margin-top:6px">Also has: ${extraLangs.join(", ")} (edit via freeform below)</p>` : ""}
        <input type="text" id="ep-extra-langs" class="ep-input" placeholder="Additional languages, comma-separated"
          value="${extraLangs.join(", ")}" style="margin-top:8px">
      </div>

      <div class="ep-section">
        <h4>Weapon Proficiencies &amp; Masteries</h4>
        <p class="hint" style="margin-bottom:8px">Quick-fill by category — fills all if empty, clears all if any are checked:</p>
        <div class="ep-cat-btns" style="margin-bottom:12px">${categoryButtons}</div>
        <p class="hint" style="margin-bottom:6px">Per-weapon overrides — Prof grants individual proficiency, Mastery unlocks mastery property:</p>
        <div class="ep-weapon-table">${weaponRows}</div>
      </div>

      <div class="ep-section">
        <h4>Speed &amp; Currency</h4>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
          <label class="field-label" style="margin:0">Speed (ft)
            <input type="number" id="ep-speed" class="ep-input" value="${detail.speed}" min="0" style="width:72px;margin-left:6px">
          </label>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
          <label class="field-label" style="margin:0">PP <input type="number" id="ep-pp" class="ep-input" value="${detail.currency.pp}" min="0" style="width:72px;margin-left:6px"></label>
          <label class="field-label" style="margin:0">GP <input type="number" id="ep-gp" class="ep-input" value="${detail.currency.gp}" min="0" style="width:72px;margin-left:6px"></label>
          <label class="field-label" style="margin:0">SP <input type="number" id="ep-sp" class="ep-input" value="${detail.currency.sp}" min="0" style="width:72px;margin-left:6px"></label>
          <label class="field-label" style="margin:0">CP <input type="number" id="ep-cp" class="ep-input" value="${detail.currency.cp}" min="0" style="width:72px;margin-left:6px"></label>
        </div>
      </div>

      </div><!-- /ep-body -->

      <div class="ep-footer">
        <button class="btn-primary" onclick="saveEditPanel()">Save Changes</button>
        <button onclick="closeEditPanel()">Cancel</button>
      </div>
    </div>`;

  overlay.addEventListener("change", e => {
    // Skill expertise sync
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
  const skills = [...document.querySelectorAll(".ep-skill-cb:checked")].map(cb => cb.value);
  const expertise = [...document.querySelectorAll(".ep-expert-cb:checked")].map(cb => cb.value);
  const tools = [...document.querySelectorAll(".ep-tool-cb:checked")].map(cb => cb.value);
  const checkedLangs = [...document.querySelectorAll(".ep-lang-cb:checked")].map(cb => cb.value);
  const extraLangs = (document.getElementById("ep-extra-langs")?.value || "")
    .split(",").map(s => s.trim()).filter(Boolean);
  const langs = [...new Set([...checkedLangs, ...extraLangs])];
  try {
    await api("PATCH", `/api/admin/characters/${id}/proficiencies`, { skills, expertise, tools, languages: langs });
  } catch(e) { errs.push("Proficiencies: " + e.message); }

  // Weapon proficiencies — save exactly the individual weapons that are checked
  const wprofIndividual = [...document.querySelectorAll(".ep-wprof-cb:checked")].map(cb => cb.value);
  try {
    await api("PATCH", `/api/admin/characters/${id}/weapon-proficiencies`,
      { proficiency_types: wprofIndividual });
  } catch(e) { errs.push("Weapon proficiencies: " + e.message); }

  // Masteries
  const masteries = [...document.querySelectorAll(".ep-mastery-cb:checked")].map(cb => cb.value);
  try {
    await api("PATCH", `/api/admin/characters/${id}/masteries`, { weapon_names: masteries });
  } catch(e) { errs.push("Masteries: " + e.message); }

  // Speed & currency
  const speed = parseInt(document.getElementById("ep-speed")?.value) || 30;
  const pp = parseInt(document.getElementById("ep-pp")?.value) || 0;
  const gp = parseInt(document.getElementById("ep-gp")?.value) || 0;
  const sp = parseInt(document.getElementById("ep-sp")?.value) || 0;
  const cp = parseInt(document.getElementById("ep-cp")?.value) || 0;
  try {
    await api("PATCH", `/api/admin/characters/${id}/speed-currency`, { speed, pp, gp, sp, cp });
  } catch(e) { errs.push("Speed/Currency: " + e.message); }

  if (errs.length) { err(errs.join("; ")); return; }
  toast("Changes saved.");
  closeEditPanel();
  loadRoster();
}

// ---------------------------------------------------------------------------
// Monster codex
// ---------------------------------------------------------------------------
let _allMonsters = [];

function _crNum(cr) {
  if (!cr) return -1;
  if (cr.includes("/")) { const [n, d] = cr.split("/"); return parseInt(n) / parseInt(d); }
  return parseFloat(cr) || -1;
}

async function loadMonsters() {
  if (_allMonsters.length) { _renderMonsters(); return; }
  _allMonsters = await api("GET", "/api/admin/monsters");
  // Populate CR filter
  const crs = [...new Set(_allMonsters.map(m => m.cr).filter(Boolean))]
    .sort((a, b) => _crNum(a) - _crNum(b));
  const sel = document.getElementById("monster-cr-filter");
  if (sel) sel.innerHTML = '<option value="">All CR</option>' + crs.map(cr => `<option value="${cr}">CR ${cr}</option>`).join("");
  _renderMonsters();
}

function _renderMonsters() {
  const q = (document.getElementById("monster-search")?.value || "").toLowerCase();
  const crFilter = document.getElementById("monster-cr-filter")?.value || "";
  const filtered = _allMonsters.filter(m =>
    (!q || m.name.toLowerCase().includes(q)) &&
    (!crFilter || m.cr === crFilter)
  );
  const el = document.getElementById("monster-list");
  if (!el) return;
  if (!filtered.length) { el.innerHTML = `<p class="hint">No monsters found.</p>`; return; }
  el.innerHTML = `<table class="data-table">
    <thead><tr><th>Name</th><th>Type</th><th>CR</th><th>AC</th><th>HP</th><th>Speed</th><th></th></tr></thead>
    <tbody>${filtered.map(m => `<tr>
      <td><strong>${m.name}</strong></td>
      <td>${[m.size, m.creature_type].filter(Boolean).join(" ") || "—"}</td>
      <td>${m.cr ?? "—"}</td>
      <td>${m.ac ?? "—"}</td>
      <td>${m.hp_max ? `${m.hp_max}${m.hp_formula ? ` (${m.hp_formula})` : ""}` : "—"}</td>
      <td>${m.speed || "—"}</td>
      <td><button onclick="openMonsterModal(${m.id})">View</button></td>
    </tr>`).join("")}
    </tbody>
  </table>`;
}

function filterMonsters() { _renderMonsters(); }

async function openMonsterModal(monsterId) {
  const m = await api("GET", `/api/admin/monsters/${monsterId}`);
  document.getElementById("monster-modal-name").textContent = m.name;
  const mod = n => { const v = Math.floor((n - 10) / 2); return (v >= 0 ? "+" : "") + v; };
  const fmtSection = (items) => (items || []).map(i =>
    `<p class="mb-sm"><strong>${i.name}.</strong> ${i.description}</p>`
  ).join("") || "";

  document.getElementById("monster-modal-body").innerHTML = `
    <div class="monster-stat-block">
      <div class="msb-meta">${[m.size, m.creature_type].filter(Boolean).join(" ")}${m.alignment ? ` · ${m.alignment}` : ""}</div>
      <div class="msb-row"><span>AC</span><span>${m.ac ?? "—"}</span></div>
      <div class="msb-row"><span>HP</span><span>${m.hp_max ?? "—"}${m.hp_formula ? ` (${m.hp_formula})` : ""}</span></div>
      <div class="msb-row"><span>Speed</span><span>${m.speed || "—"}</span></div>
      <div class="msb-row"><span>CR</span><span>${m.cr ?? "—"}${m.xp ? ` (${m.xp.toLocaleString()} XP)` : ""}</span></div>
      ${m.initiative ? `<div class="msb-row"><span>Initiative</span><span>${m.initiative}</span></div>` : ""}

      <div class="msb-abilities">
        ${["str","dex","con","int","wis","cha"].map(ab => `
          <div class="msb-ab"><div class="msb-ab-label">${ab.toUpperCase()}</div>
          <div class="msb-ab-val">${m[ab] ?? "—"}</div>
          <div class="msb-ab-mod">${m[ab] != null ? mod(m[ab]) : ""}</div></div>`).join("")}
      </div>

      ${m.saving_throws ? `<div class="msb-row"><span>Saves</span><span>${m.saving_throws}</span></div>` : ""}
      ${m.skills ? `<div class="msb-row"><span>Skills</span><span>${m.skills}</span></div>` : ""}
      ${m.resistances ? `<div class="msb-row"><span>Resistances</span><span>${m.resistances}</span></div>` : ""}
      ${m.immunities ? `<div class="msb-row"><span>Immunities</span><span>${m.immunities}</span></div>` : ""}
      ${m.vulnerabilities ? `<div class="msb-row"><span>Vulnerabilities</span><span>${m.vulnerabilities}</span></div>` : ""}
      ${m.senses ? `<div class="msb-row"><span>Senses</span><span>${m.senses}</span></div>` : ""}
      ${m.languages ? `<div class="msb-row"><span>Languages</span><span>${m.languages}</span></div>` : ""}
      ${m.gear ? `<div class="msb-row"><span>Gear</span><span>${m.gear}</span></div>` : ""}

      ${m.traits?.length ? `<div class="msb-section-title">Traits</div>${fmtSection(m.traits)}` : ""}
      ${m.actions?.length ? `<div class="msb-section-title">Actions</div>${fmtSection(m.actions)}` : ""}
      ${m.bonus_actions?.length ? `<div class="msb-section-title">Bonus Actions</div>${fmtSection(m.bonus_actions)}` : ""}
      ${m.reactions?.length ? `<div class="msb-section-title">Reactions</div>${fmtSection(m.reactions)}` : ""}
      ${m.legendary_actions?.length ? `<div class="msb-section-title">Legendary Actions</div>${fmtSection(m.legendary_actions)}` : ""}
    </div>`;
  document.getElementById("monster-modal").classList.remove("hidden");
}

function closeMonsterModal(e) {
  if (e && e.target !== document.getElementById("monster-modal")) return;
  document.getElementById("monster-modal").classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Combat tracker
// ---------------------------------------------------------------------------
let _combatants = [];

const ALL_CONDITIONS = [
  "Blinded","Charmed","Deafened","Frightened","Grappled",
  "Incapacitated","Invisible","Paralyzed","Petrified","Poisoned",
  "Prone","Restrained","Stunned","Unconscious","Exhaustion",
];

function renderCondChips(combatantId, conditions) {
  if (!conditions || !conditions.length) return "";
  const chips = conditions.map(c => {
    const label = c.startsWith("Exhaustion:") ? `Exhausted ${c.split(":")[1]}` : c;
    return `<span class="cond-chip">${label}<span class="cond-chip-x" onclick="removeCondition(${combatantId},'${c}',event)">×</span></span>`;
  }).join("");
  return `<div class="cond-chips-row">${chips}</div>`;
}

async function loadCombat() {
  _combatants = await api("GET", "/api/admin/combatants");
  const el = document.getElementById("combat-list");
  if (!_combatants.length) {
    el.innerHTML = `<p class="hint">No combatants. Click "+ Add Combatant" to begin.</p>`;
    return;
  }
  el.innerHTML = `<div class="combat-grid">${_combatants.map((c, i) => {
    const isMonster = c.kind === "monster";
    const hp = c.hp_max ? `${c.hp_current ?? "?"}/${c.hp_max}` : "—";
    const hpId = `chp-${c.combatant_id}`;
    const subtitle = isMonster
      ? [c.creature_type, c.cr ? `CR ${c.cr}` : ""].filter(Boolean).join(" · ")
      : [[c.species_lineage, c.species_name].filter(Boolean).join(" "),
         [c.class_name, c.level ? `Lv ${c.level}` : ""].filter(Boolean).join(" ")].filter(Boolean).join(" · ");
    const clickHandler = isMonster
      ? `openMonsterModal(${c.monster_id})`
      : `combatOpenSheet(${c.character_id}, event)`;
    const speed = isMonster ? (c.speed || "—") : `${c.speed || 30} ft`;
    const acBadge = isMonster && c.ac != null ? `<span class="combat-stat"><span class="combat-stat-label">AC</span> ${c.ac}</span>` : "";
    const tag = isMonster ? `<span class="combat-monster-tag">Monster</span>` : "";
    return `<div class="combat-card" onclick="${clickHandler}">
      <div class="combat-card-header">
        <span class="combat-card-num">${i + 1}</span>
        <span class="combat-card-name">${c.name}</span>
        ${tag}
        <button class="combat-remove-btn" onclick="removeCombatant(${c.combatant_id}, event)" title="Remove">✕</button>
      </div>
      ${subtitle ? `<div class="combat-card-sub">${subtitle}</div>` : ""}
      <div class="combat-card-stats">
        <span class="combat-stat"><span class="combat-stat-label">HP</span> <span id="${hpId}">${hp}</span></span>
        ${acBadge}
        <span class="combat-stat"><span class="combat-stat-label">Speed</span> ${speed}</span>
      </div>
      ${renderCondChips(c.combatant_id, c.conditions)}
      <div class="combat-card-actions" onclick="event.stopPropagation()">
        <button class="combat-hp-btn" onclick="combatAdjHpBtn(${c.combatant_id}, ${isMonster}, ${isMonster ? 0 : c.character_id}, -1)">−1</button>
        <button class="combat-hp-btn" onclick="combatAdjHpBtn(${c.combatant_id}, ${isMonster}, ${isMonster ? 0 : c.character_id}, +1)">+1</button>
        <input type="number" id="combat-adj-${c.combatant_id}" class="combat-hp-input" placeholder="±HP">
        <button class="combat-hp-btn" onclick="combatApplyAdj(${c.combatant_id}, ${isMonster}, ${isMonster ? 0 : c.character_id})">Apply</button>
        <button class="combat-hp-btn" onclick="openConditionPicker(${c.combatant_id},event)" title="Set conditions">＋ Cond</button>
      </div>
    </div>`;
  }).join("")}</div>`;
}

function combatOpenSheet(charId, e) {
  if (e?.target?.closest("button, input")) return;
  window.open(`/characters/${charId}/sheet`, "_blank");
}

async function combatAdjHpBtn(combatantId, isMonster, charId, delta) {
  if (isMonster) {
    const c = _combatants.find(x => x.combatant_id === combatantId);
    if (!c) return;
    const newHp = Math.max(0, (c.hp_current ?? c.hp_max ?? 0) + delta);
    try {
      const r = await api("PATCH", `/api/admin/combatants/${combatantId}/hp`, { hp_current: newHp });
      c.hp_current = r.hp_current;
      const el = document.getElementById(`chp-${combatantId}`);
      if (el) el.textContent = `${r.hp_current}/${r.hp_max}`;
    } catch(e) { err(e.message); }
  } else {
    try {
      const r = await api("POST", `/api/admin/characters/${charId}/hp`, { delta });
      const el = document.getElementById(`chp-${combatantId}`);
      if (el) el.textContent = `${r.hp_current}/${r.hp_max}`;
    } catch(e) { err(e.message); }
  }
}

async function combatApplyAdj(combatantId, isMonster, charId) {
  const input = document.getElementById(`combat-adj-${combatantId}`);
  const delta = parseInt(input?.value);
  if (!delta || isNaN(delta)) { toast("Enter a number first."); return; }
  input.value = "";
  await combatAdjHpBtn(combatantId, isMonster, charId, delta);
}

async function removeCombatant(combatantId, e) {
  e?.stopPropagation();
  try {
    await api("DELETE", `/api/admin/combatants/${combatantId}`);
    loadCombat();
  } catch(e) { err(e.message); }
}

async function clearCombat() {
  if (!_combatants.length) { toast("Combat is already empty."); return; }
  if (!confirm("Remove all combatants?")) return;
  try {
    await api("POST", "/api/admin/combatants/clear");
    loadCombat();
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Condition picker
// ---------------------------------------------------------------------------
let _condPickerCombatantId = null;

function openConditionPicker(combatantId, event) {
  event.stopPropagation();
  closeConditionPicker();
  _condPickerCombatantId = combatantId;

  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  const active = new Set(combatant ? (combatant.conditions || []) : []);
  let exhaustLevel = 0;
  for (const c of active) {
    if (c.startsWith("Exhaustion:")) { exhaustLevel = parseInt(c.split(":")[1], 10); break; }
  }

  const picker = document.createElement("div");
  picker.className = "cond-picker";
  picker.id = "cond-picker";
  picker.onclick = e => e.stopPropagation();

  const items = ALL_CONDITIONS.map(cond => {
    const isExh = cond === "Exhaustion";
    const isActive = isExh ? exhaustLevel > 0 : active.has(cond);
    return `<div class="cond-picker-item${isActive ? " active" : ""}" onclick="toggleCondition(${combatantId},'${cond}',event)">
      <span class="cond-picker-check">${isActive ? "✓" : ""}</span>
      ${cond}${isExh && exhaustLevel > 0 ? ` (${exhaustLevel})` : ""}
    </div>`;
  }).join("");

  const exhaustPicker = `<div class="cond-exhaustion-picker" id="exh-picker">
    ${[1,2,3,4,5,6].map(n => `<button class="cond-exhaustion-btn${n === exhaustLevel ? " active" : ""}"
      onclick="setExhaustionLevel(${combatantId},${n},event)">${n}</button>`).join("")}
    ${exhaustLevel > 0 ? `<button class="cond-exhaustion-btn" onclick="setExhaustionLevel(${combatantId},0,event)" style="color:var(--rubric)">✕</button>` : ""}
  </div>`;

  picker.innerHTML = items + exhaustPicker;

  const btn = event.currentTarget;
  const rect = btn.getBoundingClientRect();
  picker.style.position = "fixed";
  picker.style.top = (rect.bottom + 4) + "px";
  picker.style.left = rect.left + "px";
  document.body.appendChild(picker);
  setTimeout(() => document.addEventListener("click", closeConditionPicker, { once: true }), 0);
}

function closeConditionPicker() {
  const el = document.getElementById("cond-picker");
  if (el) el.remove();
  _condPickerCombatantId = null;
}

async function toggleCondition(combatantId, condName, event) {
  event.stopPropagation();
  if (condName === "Exhaustion") return;
  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  if (!combatant) return;
  const current = [...(combatant.conditions || [])];
  const idx = current.indexOf(condName);
  if (idx >= 0) current.splice(idx, 1);
  else current.push(condName);
  await _applyConditions(combatantId, current);
  closeConditionPicker();
  loadCombat();
}

async function setExhaustionLevel(combatantId, level, event) {
  event.stopPropagation();
  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  if (!combatant) return;
  const current = (combatant.conditions || []).filter(c => !c.startsWith("Exhaustion"));
  if (level > 0) current.push(`Exhaustion:${level}`);
  await _applyConditions(combatantId, current);
  closeConditionPicker();
  loadCombat();
}

async function removeCondition(combatantId, condName, event) {
  event.stopPropagation();
  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  if (!combatant) return;
  const current = (combatant.conditions || []).filter(c => c !== condName);
  await _applyConditions(combatantId, current);
  loadCombat();
}

async function _applyConditions(combatantId, conditions) {
  try {
    const r = await api("PATCH", `/api/admin/combatants/${combatantId}/conditions`, { conditions });
    const combatant = _combatants.find(c => c.combatant_id === combatantId);
    if (combatant) combatant.conditions = r.conditions;
  } catch(e) { err(e.message || "Failed to set conditions"); }
}

function openCombatAddModal() {
  const inCombatCharIds = new Set(_combatants.filter(c => c.kind === "character").map(c => c.character_id));
  const charRows = _rosterChars.filter(c => !inCombatCharIds.has(c.id)).map(c => {
    const cls = c.class_name ? ` · ${c.class_name} Lv ${c.level || "?"}` : "";
    return `<div class="combat-picker-row" data-search="${c.character_name.toLowerCase()}" onclick="addCharacterCombatant(${c.id})">
      <strong>${c.character_name}</strong>
      <span class="hint">${c.created_by_display_name}${cls}</span>
    </div>`;
  }).join("") || `<p class="hint" style="padding:8px 12px">All characters are already in combat.</p>`;

  // Sort monsters by CR for the picker
  const sortedMonsters = [..._allMonsters].sort((a, b) => _crNum(a.cr) - _crNum(b.cr));
  const monsterRows = sortedMonsters.map(m => {
    const sub = [m.creature_type, m.cr ? `CR ${m.cr}` : ""].filter(Boolean).join(" · ");
    return `<div class="combat-picker-row" data-search="${m.name.toLowerCase()}" onclick="addMonsterCombatant(${m.id})">
      <strong>${m.name}</strong>
      <span class="hint">${sub}</span>
    </div>`;
  }).join("");

  document.getElementById("combat-picker-list").innerHTML = `
    <div class="combat-picker-section"><div class="combat-picker-header">Characters</div>${charRows}</div>
    ${monsterRows ? `<div class="combat-picker-section"><div class="combat-picker-header">Monsters</div>${monsterRows}</div>` : ""}`;
  document.getElementById("combat-search").value = "";
  document.getElementById("combat-add-modal").classList.remove("hidden");

  // Ensure monsters are loaded for the picker
  if (!_allMonsters.length) loadMonsters().then(() => openCombatAddModal());
}

function closeCombatAddModal(e) {
  if (e && e.target !== document.getElementById("combat-add-modal")) return;
  document.getElementById("combat-add-modal").classList.add("hidden");
}

function filterCombatPicker() {
  const q = document.getElementById("combat-search").value.toLowerCase();
  document.querySelectorAll(".combat-picker-row").forEach(row => {
    row.style.display = (row.dataset.search || "").includes(q) ? "" : "none";
  });
}

async function addCharacterCombatant(charId) {
  try {
    await api("POST", "/api/admin/combatants/character", { character_id: charId });
    document.getElementById("combat-add-modal").classList.add("hidden");
    loadCombat();
  } catch(e) {
    if (e.message.includes("409") || e.message.toLowerCase().includes("already")) toast("Already in combat.");
    else err(e.message);
  }
}

async function addMonsterCombatant(monsterId) {
  try {
    await api("POST", "/api/admin/combatants/monster", { monster_id: monsterId });
    document.getElementById("combat-add-modal").classList.add("hidden");
    loadCombat();
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Weapon tooltip
// ---------------------------------------------------------------------------
function _initWeaponTip() {
  if (document.getElementById("weapon-tip")) return;
  const tip = document.createElement("div");
  tip.id = "weapon-tip";
  tip.className = "weapon-tip";
  tip.style.display = "none";
  document.body.appendChild(tip);
  document.addEventListener("mousemove", e => {
    if (tip.style.display !== "none") {
      tip.style.left = (e.clientX + 14) + "px";
      tip.style.top  = (e.clientY + 14) + "px";
    }
  });
}

function showWeaponTip(el, e) {
  _initWeaponTip();
  const tip = document.getElementById("weapon-tip");
  const name    = el.dataset.tipName    || "";
  const cat     = el.dataset.tipCat     || "";
  const damage  = el.dataset.tipDamage  || "";
  const props   = el.dataset.tipProps   || "";
  const mastery = el.dataset.tipMastery || "";
  if (!name) return;
  tip.innerHTML =
    `<strong>${name}</strong>` +
    (cat     ? `<div class="wt-cat">${cat}</div>`       : "") +
    (damage  ? `<div class="wt-damage">${damage}</div>` : "") +
    (props   ? `<div class="wt-props">${props}</div>`   : "") +
    (mastery ? `<div class="wt-mastery">Mastery: ${mastery}</div>` : "");
  tip.style.display = "block";
  tip.style.left = (e.clientX + 14) + "px";
  tip.style.top  = (e.clientY + 14) + "px";
}

function hideWeaponTip() {
  const tip = document.getElementById("weapon-tip");
  if (tip) tip.style.display = "none";
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
