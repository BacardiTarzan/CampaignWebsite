/* D&D 2024 Level-Up Wizard */

const charId = parseInt(location.pathname.split("/")[2]);

let opts = null;        // levelup-options response
let allSpells = [];     // class spell list

// Choices accumulated across steps
const choices = {
  subclass_id: null,
  cantrip_ids: [],
  spell_ids: [],
};

// Step order built dynamically after options load
let steps = [];
let stepIdx = 0;

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

function toast(msg, ms = 3500) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), ms);
}

function show(id)  { document.getElementById(id)?.classList.remove("hidden"); }
function hide(id)  { document.getElementById(id)?.classList.add("hidden"); }

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  try {
    const me = await api("GET", "/auth/me");
    if (me?.display_name) document.getElementById("lu-user-name").textContent = me.display_name;
  } catch(_) {}

  try {
    opts = await api("GET", `/api/characters/${charId}/levelup-options`);
  } catch(e) {
    // No level-up available — send back to portal
    window.location.href = "/portal";
    return;
  }

  document.title = `Level Up — ${opts.character_name}`;
  document.getElementById("lu-title").textContent = `${opts.character_name}`;
  document.getElementById("lu-subtitle").textContent =
    `${opts.class_name} · Level ${opts.current_level} → ${opts.next_level}`;

  // Load class spells if needed
  if (opts.cantrip_gains > 0 || opts.spell_gains > 0) {
    try {
      allSpells = await api("GET", `/api/content/spells?class_name=${encodeURIComponent(opts.class_name)}`);
    } catch(_) { allSpells = []; }
  }

  buildSteps();
  hide("lu-loading");
  show("lu-root");
  renderCurrentStep();
}

// ---------------------------------------------------------------------------
// Step management
// ---------------------------------------------------------------------------
function buildSteps() {
  steps = ["features"];
  if (opts.subclass_needed) steps.push("subclass");
  if (opts.cantrip_gains > 0) steps.push("cantrips");
  if (opts.spell_gains > 0) steps.push("spells");
  steps.push("confirm");
  renderStepPips();
}

function renderStepPips() {
  const labels = { features: "Features", subclass: "Subclass", cantrips: "Cantrips", spells: "Spells", confirm: "Confirm" };
  document.getElementById("lu-steps").innerHTML = steps.map((s, i) =>
    `<span class="lu-pip ${i === stepIdx ? "lu-pip--active" : i < stepIdx ? "lu-pip--done" : ""}">${labels[s]}</span>`
  ).join('<span class="lu-pip-sep">›</span>');
}

function showPanel(name) {
  ["features","subclass","cantrips","spells","confirm","done"].forEach(s =>
    document.getElementById(`lu-step-${s}`)?.classList.add("hidden"));
  show(`lu-step-${name}`);
}

function renderCurrentStep() {
  const step = steps[stepIdx];
  renderStepPips();
  if (step === "features")  renderFeatures();
  if (step === "subclass")  renderSubclass();
  if (step === "cantrips")  renderCantrips();
  if (step === "spells")    renderSpells();
  if (step === "confirm")   renderConfirm();
  showPanel(step);
}

function luNext() {
  if (stepIdx < steps.length - 1) {
    stepIdx++;
    renderCurrentStep();
  }
}

function luBack() {
  if (stepIdx > 0) {
    stepIdx--;
    renderCurrentStep();
  }
}

// ---------------------------------------------------------------------------
// Features step
// ---------------------------------------------------------------------------
function renderFeatures() {
  const all = [...opts.new_features, ...opts.subclass_features];
  const el = document.getElementById("lu-features-list");
  if (!all.length) {
    el.innerHTML = `<p class="lu-no-features">No new class features at this level — but your power grows.</p>`;
    return;
  }
  el.innerHTML = all.map(f => `
    <div class="lu-feature-card">
      <div class="lu-feature-name">${f.name}</div>
      <div class="lu-feature-desc">${f.description || ""}</div>
      ${f.choice_required && f.options?.length ? `
        <div class="lu-feature-choice">
          <strong>Choose one:</strong>
          ${f.options.map(o => `<span class="lu-choice-tag">${o}</span>`).join("")}
        </div>` : ""}
    </div>`).join("");
}

// ---------------------------------------------------------------------------
// Subclass step
// ---------------------------------------------------------------------------
let selectedSubclass = null;

function renderSubclass() {
  const grid = document.getElementById("lu-subclass-grid");
  grid.innerHTML = opts.subclass_options.map(s => `
    <div class="lu-subclass-card ${choices.subclass_id === s.id ? "chosen" : ""}"
         onclick="selectSubclass(${s.id}, this)">
      <div class="lu-subclass-name">${s.name}</div>
      <div class="lu-subclass-desc">${s.description || ""}</div>
      ${s.features?.length ? `
        <div class="lu-subclass-features">
          ${s.features.map(f => `<div class="lu-sub-feat"><strong>${f.name}:</strong> ${f.description || ""}</div>`).join("")}
        </div>` : ""}
    </div>`).join("");
  document.getElementById("lu-subclass-next").disabled = !choices.subclass_id;
}

function selectSubclass(id, el) {
  choices.subclass_id = id;
  document.querySelectorAll(".lu-subclass-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
  document.getElementById("lu-subclass-next").disabled = false;
}

// ---------------------------------------------------------------------------
// Cantrips step
// ---------------------------------------------------------------------------
function renderCantrips() {
  const needed = opts.cantrip_gains;
  document.getElementById("lu-cantrip-hint").textContent =
    `Choose ${needed} new cantrip${needed > 1 ? "s" : ""}.`;
  const owned = new Set(opts.owned_spell_ids);
  const cantrips = allSpells.filter(s => s.level === 0 && !owned.has(s.id));
  document.getElementById("lu-cantrip-grid").innerHTML = cantrips.map(s => spellCard(s, "cantrip")).join("");
  updateCantripNext();
}

function updateCantripNext() {
  const chosen = document.querySelectorAll('.lu-spell-card.chosen[data-group="cantrip"]').length;
  document.getElementById("lu-cantrip-next").disabled = chosen < opts.cantrip_gains;
}

// ---------------------------------------------------------------------------
// Spells step
// ---------------------------------------------------------------------------
let spellFilterLevel = null;

function renderSpells() {
  const needed = opts.spell_gains;
  const maxSl = opts.max_spell_level;
  const owned = new Set(opts.owned_spell_ids);
  document.getElementById("lu-spell-hint").textContent =
    `Choose ${needed} new spell${needed > 1 ? "s" : ""} (up to level ${maxSl}).`;

  // Level filter buttons
  const levels = [...new Set(
    allSpells.filter(s => s.level >= 1 && s.level <= maxSl && !owned.has(s.id)).map(s => s.level)
  )].sort((a, b) => a - b);

  const filterEl = document.getElementById("lu-spell-filter");
  filterEl.innerHTML = [
    `<button class="lu-filter-btn ${spellFilterLevel === null ? "active" : ""}" onclick="setSpellFilter(null, this)">All</button>`,
    ...levels.map(l => `<button class="lu-filter-btn ${spellFilterLevel === l ? "active" : ""}" onclick="setSpellFilter(${l}, this)">Level ${l}</button>`)
  ].join("");

  renderSpellCards();
  updateSpellNext();
}

function setSpellFilter(level, btn) {
  spellFilterLevel = level;
  document.querySelectorAll(".lu-filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderSpellCards();
}

function renderSpellCards() {
  const owned = new Set(opts.owned_spell_ids);
  const chosenIds = new Set(choices.spell_ids);
  const maxSl = opts.max_spell_level;
  const filtered = allSpells.filter(s =>
    s.level >= 1 && s.level <= maxSl && !owned.has(s.id) &&
    (spellFilterLevel === null || s.level === spellFilterLevel)
  );
  document.getElementById("lu-spell-grid").innerHTML = filtered.map(s =>
    spellCard(s, "spell", chosenIds.has(s.id))
  ).join("");
}

function updateSpellNext() {
  const chosen = document.querySelectorAll('.lu-spell-card.chosen[data-group="spell"]').length;
  document.getElementById("lu-spell-next").disabled = chosen < opts.spell_gains;
}

// ---------------------------------------------------------------------------
// Shared spell card
// ---------------------------------------------------------------------------
function spellCard(s, group, preChosen = false) {
  const lvlLabel = s.level === 0 ? "Cantrip" : `Level ${s.level}`;
  return `<div class="lu-spell-card ${preChosen ? "chosen" : ""}" data-id="${s.id}" data-group="${group}"
    onclick="toggleSpell(this, '${group}')">
    <div class="lu-spell-name">${s.name}</div>
    <div class="lu-spell-meta">${lvlLabel}${s.school ? " · " + s.school : ""}</div>
    ${s.description ? `<div class="lu-spell-desc hidden">${s.description}</div>` : ""}
  </div>`;
}

function toggleSpell(el, group) {
  const id = parseInt(el.dataset.id);
  const needed = group === "cantrip" ? opts.cantrip_gains : opts.spell_gains;
  const chosen = document.querySelectorAll(`.lu-spell-card.chosen[data-group="${group}"]`);

  if (el.classList.contains("chosen")) {
    el.classList.remove("chosen");
    if (group === "cantrip") choices.cantrip_ids = choices.cantrip_ids.filter(x => x !== id);
    else choices.spell_ids = choices.spell_ids.filter(x => x !== id);
  } else {
    if (chosen.length >= needed) {
      toast(`You can only choose ${needed} ${group === "cantrip" ? "cantrip" : "spell"}${needed > 1 ? "s" : ""}.`);
      return;
    }
    el.classList.add("chosen");
    if (group === "cantrip") choices.cantrip_ids.push(id);
    else choices.spell_ids.push(id);
  }

  if (group === "cantrip") updateCantripNext();
  else updateSpellNext();
}

// ---------------------------------------------------------------------------
// Confirm step
// ---------------------------------------------------------------------------
function renderConfirm() {
  const lines = [];

  if (choices.subclass_id) {
    const sub = opts.subclass_options.find(s => s.id === choices.subclass_id);
    lines.push(`<div class="lu-confirm-row"><span class="lu-confirm-label">Subclass</span><span>${sub?.name || "—"}</span></div>`);
  }

  if (choices.cantrip_ids.length) {
    const names = choices.cantrip_ids.map(id => allSpells.find(s => s.id === id)?.name || id).join(", ");
    lines.push(`<div class="lu-confirm-row"><span class="lu-confirm-label">New Cantrips</span><span>${names}</span></div>`);
  }

  if (choices.spell_ids.length) {
    const names = choices.spell_ids.map(id => allSpells.find(s => s.id === id)?.name || id).join(", ");
    const label = opts.class_name === "Wizard" ? "Added to Spellbook" : "New Spells";
    lines.push(`<div class="lu-confirm-row"><span class="lu-confirm-label">${label}</span><span>${names}</span></div>`);
  }

  lines.push(`<div class="lu-confirm-row"><span class="lu-confirm-label">Hit Points</span><span>+${opts.hp_increase} (${opts.hp_increase_detail})</span></div>`);
  lines.push(`<div class="lu-confirm-row lu-confirm-level"><span class="lu-confirm-label">New Level</span><span>${opts.next_level}</span></div>`);

  document.getElementById("lu-confirm-summary").innerHTML = lines.join("");
}

// ---------------------------------------------------------------------------
// Apply level-up
// ---------------------------------------------------------------------------
async function luApply() {
  const btn = document.getElementById("lu-apply-btn");
  btn.disabled = true;
  btn.textContent = "Applying…";
  try {
    const result = await api("POST", `/api/characters/${charId}/levelup`, {
      subclass_id: choices.subclass_id,
      cantrip_ids: choices.cantrip_ids,
      spell_ids: choices.spell_ids,
    });

    // Show done step
    showPanel("done");
    document.getElementById("lu-done-title").textContent =
      `${opts.character_name} is now Level ${result.new_level}!`;
    document.getElementById("lu-done-sub").textContent =
      `HP maximum is now ${result.hp_max}.`;
    document.getElementById("lu-sheet-link").href = `/characters/${charId}/sheet`;
    document.getElementById("lu-steps").innerHTML = "";
    document.getElementById("lu-subtitle").textContent = `${opts.class_name} · Level ${result.new_level}`;

  } catch(e) {
    toast("⚠ " + e.message, 5000);
    btn.disabled = false;
    btn.textContent = "⬆ Level Up";
  }
}

boot();
