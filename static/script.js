/* ============================================================
   D&D 2024 Character Wizard — state machine
   ============================================================ */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const state = {
  charId: null,
  step: 1,
  displayName: "",
  charName: "",
  speciesId: null,
  backgroundId: null,
  classId: null,
  selectedRollSet: null,
  assignedStats: { str: null, dex: null, con: null, int: null, wis: null, cha: null },
  backgroundASI: {},
  featuresChoices: [],
  selectedSkills: [],
  selectedLanguages: [],
  classEquipOption: null,
  bgEquipOption: null,
  resolvedItems: [],
  cantripIds: [],
  spellIds: [],
  // content cache
  allSpecies: [],
  allBackgrounds: [],
  allClasses: [],
  allSpells: [],
  currentClass: null,
  currentBackground: null,
  currentSpecies: null,
  toolChoiceRequired: false,
  toolChoiceOptions: [],
};

const STEPS = [
  { label: "Identity" }, { label: "Species" }, { label: "Background" },
  { label: "Class" }, { label: "Stats" }, { label: "Features" },
  { label: "Skills" }, { label: "Equipment" }, { label: "Spells" },
  { label: "Bio" },
];

const ALL_LANGUAGES = [
  "Common", "Common Sign Language", "Draconic", "Dwarvish", "Elvish",
  "Giant", "Gnomish", "Goblin", "Halfling", "Orc", "Celestial",
  "Deep Speech", "Infernal", "Primordial", "Sylvan", "Thieves' Cant",
  "Undercommon",
];

const TOOL_OPTIONS = {
  "Choose one kind of Artisan's Tools": [
    "Alchemist's Supplies","Brewer's Supplies","Calligrapher's Supplies",
    "Carpenter's Tools","Cobbler's Tools","Cook's Utensils","Glassblower's Tools",
    "Jeweler's Tools","Leatherworker's Tools","Mason's Tools","Painter's Supplies",
    "Potter's Tools","Smith's Tools","Tinker's Tools","Weaver's Tools","Woodcarver's Tools",
  ],
  "Choose one kind of Musical Instrument": [
    "Bagpipes","Drum","Dulcimer","Flute","Lute","Lyre",
    "Horn","Pan Flute","Shawm","Viol",
  ],
  "Choose one kind of Gaming Set": [
    "Dice Set","Dragonchess Set","Playing Card Set","Three-Dragon Ante Set",
  ],
};

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json().catch(() => null);
}

function toast(msg, ms = 2800) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), ms);
}

function err(msg) { toast("⚠ " + msg, 4000); console.error(msg); }

// ---------------------------------------------------------------------------
// Wizard progress bar
// ---------------------------------------------------------------------------
function renderProgress() {
  const bar = document.getElementById("wizard-progress");
  bar.innerHTML = STEPS.map((s, i) => {
    const num = i + 1;
    const cls = num < state.step ? "done" : num === state.step ? "active" : "";
    return `<div class="wizard-step-pip ${cls}">
      <div class="pip-circle">${num < state.step ? "✓" : num}</div>
      <div class="pip-label">${s.label}</div>
    </div>`;
  }).join("");
}

function showStep(n) {
  document.querySelectorAll(".wizard-panel").forEach(p => p.classList.add("hidden"));
  const panel = document.getElementById(n <= 10 ? `step-${n}` : "step-done");
  if (panel) panel.classList.remove("hidden");
  state.step = n;
  renderProgress();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function goToStep(n) { showStep(n); }

// ---------------------------------------------------------------------------
// Step 1 — Identity
// ---------------------------------------------------------------------------
function saveIdentity() {
  const dn = document.getElementById("display-name").value.trim();
  const cn = document.getElementById("char-name").value.trim();
  if (!dn || !cn) { toast("Please fill in both names."); return; }
  state.displayName = dn;
  state.charName = cn;
  api("POST", "/api/characters", { created_by_display_name: dn, character_name: cn })
    .then(r => {
      state.charId = r.id;
      loadSpecies();
      showStep(2);
    }).catch(e => err(e.message));
}

// ---------------------------------------------------------------------------
// Step 2 — Species
// ---------------------------------------------------------------------------
async function loadSpecies() {
  if (state.allSpecies.length) return;
  state.allSpecies = await api("GET", "/api/content/species");
  renderSpeciesGrid();
}

function renderSpeciesGrid() {
  const grid = document.getElementById("species-grid");
  grid.innerHTML = state.allSpecies.map(s =>
    `<div class="select-card" data-id="${s.id}" onclick="selectSpecies(${s.id})">
      <span class="select-card-name">${s.name}</span>
      <span class="select-card-sub">${(s.size_options||[]).join("/")} · ${s.speed} ft.</span>
    </div>`
  ).join("");
}

function selectSpecies(id) {
  state.speciesId = id;
  document.querySelectorAll("#species-grid .select-card").forEach(c =>
    c.classList.toggle("selected", +c.dataset.id === id));
  const sp = state.allSpecies.find(s => s.id === id);
  if (!sp) return;
  state.currentSpecies = sp;
  const detail = document.getElementById("species-detail");
  document.getElementById("species-detail-name").textContent = sp.name;
  document.getElementById("species-detail-body").innerHTML =
    `<p class="hint mb-sm">${sp.creature_type} · ${(sp.size_options||[]).join(" or ")} · Speed ${sp.speed} ft.</p>` +
    (sp.traits||[]).map(t =>
      `<p class="mb-sm"><strong class="trait-name">${t.name}.</strong> ${t.description}</p>`
    ).join("");
  detail.classList.add("visible");
  document.getElementById("btn-species-next").disabled = false;
}

function saveSpecies() {
  if (!state.speciesId) { toast("Pick a species first."); return; }
  api("POST", `/api/characters/${state.charId}/step/species`, { species_id: state.speciesId })
    .then(() => { loadBackgrounds(); showStep(3); })
    .catch(e => err(e.message));
}

// ---------------------------------------------------------------------------
// Step 3 — Background
// ---------------------------------------------------------------------------
async function loadBackgrounds() {
  if (state.allBackgrounds.length) return;
  state.allBackgrounds = await api("GET", "/api/content/backgrounds");
  renderBackgroundGrid();
}

function renderBackgroundGrid() {
  const grid = document.getElementById("background-grid");
  grid.innerHTML = state.allBackgrounds.map(b =>
    `<div class="select-card" data-id="${b.id}" onclick="selectBackground(${b.id})">
      <span class="select-card-name">${b.name}</span>
      <span class="select-card-sub">${(b.skill_proficiencies||[]).join(", ")}</span>
    </div>`
  ).join("");
}

function selectBackground(id) {
  state.backgroundId = id;
  document.querySelectorAll("#background-grid .select-card").forEach(c =>
    c.classList.toggle("selected", +c.dataset.id === id));
  const bg = state.allBackgrounds.find(b => b.id === id);
  if (!bg) return;
  state.currentBackground = bg;

  const detail = document.getElementById("background-detail");
  document.getElementById("background-detail-name").textContent = bg.name;

  const abilityStr = (bg.ability_score_options||[]).join(", ");
  document.getElementById("background-detail-body").innerHTML =
    `<p class="mb-sm"><strong>Ability Scores:</strong> ${abilityStr}</p>` +
    `<p class="mb-sm"><strong>Origin Feat:</strong> ${bg.origin_feat_name || "—"}</p>` +
    `<p class="mb-sm"><strong>Skills:</strong> ${(bg.skill_proficiencies||[]).join(", ")}</p>` +
    `<p class="mb-sm"><strong>Tool:</strong> ${bg.tool_proficiency || "—"}</p>`;

  // Tool choice
  const toolRow = document.getElementById("tool-choice-row");
  const toolSelect = document.getElementById("tool-choice-select");
  const isChoice = bg.tool_proficiency && bg.tool_proficiency.toLowerCase().startsWith("choose");
  state.toolChoiceRequired = isChoice;
  if (isChoice) {
    const opts = Object.entries(TOOL_OPTIONS).find(([k]) => bg.tool_proficiency.toLowerCase().includes(k.split(" ")[3]?.toLowerCase() || ""));
    const choices = opts ? opts[1] : [];
    state.toolChoiceOptions = choices;
    document.getElementById("tool-choice-label").textContent = bg.tool_proficiency + ":";
    toolSelect.innerHTML = choices.map(c => `<option>${c}</option>`).join("");
    toolRow.classList.remove("hidden");
  } else {
    toolRow.classList.add("hidden");
    state.toolChoiceOptions = [];
  }

  detail.classList.add("visible");
  document.getElementById("btn-background-next").disabled = false;
}

function saveBackground() {
  if (!state.backgroundId) { toast("Pick a background first."); return; }
  const toolChoice = state.toolChoiceRequired
    ? document.getElementById("tool-choice-select").value
    : null;
  api("POST", `/api/characters/${state.charId}/step/background`, {
    background_id: state.backgroundId,
    tool_proficiency_choice: toolChoice,
  }).then(() => { loadClasses(); showStep(4); })
    .catch(e => err(e.message));
}

// ---------------------------------------------------------------------------
// Step 4 — Class
// ---------------------------------------------------------------------------
async function loadClasses() {
  if (state.allClasses.length) return;
  state.allClasses = await api("GET", "/api/content/classes");
  renderClassGrid();
}

function renderClassGrid() {
  const grid = document.getElementById("class-grid");
  grid.innerHTML = state.allClasses.map(c => {
    const casting = c.spellcasting_type ? ` · ${c.spellcasting_type} caster` : "";
    return `<div class="select-card" data-id="${c.id}" onclick="selectClass(${c.id})">
      <span class="select-card-name">${c.name}</span>
      <span class="select-card-sub">d${c.hit_die} · ${(c.primary_abilities||[]).join("/")}${casting}</span>
    </div>`;
  }).join("");
}

async function selectClass(id) {
  state.classId = id;
  document.querySelectorAll("#class-grid .select-card").forEach(c =>
    c.classList.toggle("selected", +c.dataset.id === id));
  state.currentClass = await api("GET", `/api/content/classes/${id}`);

  const cls = state.currentClass;
  const detail = document.getElementById("class-detail");
  document.getElementById("class-detail-name").textContent = cls.name;

  const featureNames = (cls.features||[]).filter(f => f.level === 1).map(f => f.name).join(", ");
  document.getElementById("class-detail-body").innerHTML =
    `<p class="mb-sm"><strong>Hit Die:</strong> d${cls.hit_die} · <strong>Save Proficiencies:</strong> ${(cls.saving_throws||[]).join(", ")}</p>` +
    `<p class="mb-sm"><strong>Armor:</strong> ${(cls.armor_proficiencies||[]).join(", ") || "None"}</p>` +
    `<p class="mb-sm"><strong>Weapons:</strong> ${(cls.weapon_proficiencies||[]).join(", ")}</p>` +
    `<p class="mb-sm"><strong>Skills (choose ${cls.skill_choices}):</strong> ${(cls.skill_options||[]).join(", ")}</p>` +
    (featureNames ? `<p class="mb-sm"><strong>Level 1 Features:</strong> ${featureNames}</p>` : "");

  detail.classList.add("visible");
  document.getElementById("btn-class-next").disabled = false;
}

function saveClass() {
  if (!state.classId) { toast("Pick a class first."); return; }
  api("POST", `/api/characters/${state.charId}/step/class`, { class_id: state.classId })
    .then(() => { showStep(5); renderStatsStep(); })
    .catch(e => err(e.message));
}

// ---------------------------------------------------------------------------
// Step 5 — Stats
// ---------------------------------------------------------------------------
let dragToken = null;

function renderStatsStep() {
  // Reset stat assignment state
  state.selectedRollSet = null;
  state.assignedStats = { str: null, dex: null, con: null, int: null, wis: null, cha: null };
  document.getElementById("roll-set-picker").classList.add("hidden");
  document.getElementById("stat-assignment").classList.add("hidden");
  document.getElementById("asi-section").classList.add("hidden");
  document.getElementById("btn-stats-next").disabled = true;
  document.getElementById("manual-entry").classList.add("hidden");
  renderManualSets();
}

function renderManualSets() {
  const container = document.getElementById("manual-sets");
  container.innerHTML = [1, 2, 3].map(i =>
    `<div class="mb-sm">
      <label>Set ${i} — enter six values (comma-separated, e.g. 15,14,13,12,10,8):</label>
      <input type="text" id="manual-set-${i}" placeholder="15, 14, 13, 12, 10, 8">
    </div>`
  ).join("");
}

function showManualEntry() {
  document.getElementById("manual-entry").classList.remove("hidden");
  document.getElementById("roll-set-picker").classList.add("hidden");
  document.getElementById("stat-assignment").classList.add("hidden");
}

async function autoRoll() {
  try {
    const r = await api("POST", `/api/characters/${state.charId}/roll-stats`);
    renderRollSets(r.sets, false);
  } catch(e) { err(e.message); }
}

function submitManualRolls() {
  const sets = [];
  for (let i = 1; i <= 3; i++) {
    const val = document.getElementById(`manual-set-${i}`).value;
    const nums = val.split(/[\s,]+/).map(Number).filter(n => n >= 1 && n <= 20);
    if (nums.length !== 6) { toast(`Set ${i} must have exactly 6 values between 1 and 20.`); return; }
    sets.push(nums);
  }
  renderRollSets(sets, true);
}

function renderRollSets(sets, isManual) {
  document.getElementById("roll-set-picker").classList.remove("hidden");
  document.getElementById("stat-assignment").classList.add("hidden");
  const cards = document.getElementById("roll-set-cards");
  cards.innerHTML = sets.map((set, i) => {
    const total = set.reduce((a, b) => a + b, 0);
    return `<div class="roll-set-card" data-idx="${i}" onclick="pickRollSet(${i}, this)">
      <div class="roll-set-values">${set.join(" · ")}</div>
      <div class="roll-set-total">Sum: ${total}</div>
    </div>`;
  }).join("");
  window._rollSets = sets;
  window._rollIsManual = isManual;
}

function pickRollSet(idx, el) {
  document.querySelectorAll(".roll-set-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
  state.selectedRollSet = window._rollSets[idx];
  renderStatAssignment(state.selectedRollSet);
}

const STAT_LABELS = {
  str: "Strength", dex: "Dexterity", con: "Constitution",
  int: "Intelligence", wis: "Wisdom", cha: "Charisma",
};

function renderStatAssignment(values) {
  document.getElementById("stat-assignment").classList.remove("hidden");
  // Token pool
  const pool = document.getElementById("token-pool");
  pool.innerHTML = values.map(v =>
    `<div class="stat-token" draggable="true" data-value="${v}"
      ondragstart="onTokenDragStart(event)"
      ondragend="onTokenDragEnd(event)">${v}</div>`
  ).join("");
  // Ability slots
  const slots = document.getElementById("ability-slots");
  slots.innerHTML = Object.keys(STAT_LABELS).map(key =>
    `<div class="ability-cell drop-target" data-stat="${key}"
      ondragover="onSlotDragOver(event)"
      ondragleave="onSlotDragLeave(event)"
      ondrop="onSlotDrop(event, '${key}')">
      <span class="ability-name">${STAT_LABELS[key].slice(0, 3).toUpperCase()}</span>
      <span class="ability-score" id="slot-val-${key}">—</span>
      <span class="ability-mod" id="slot-mod-${key}"></span>
    </div>`
  ).join("");
}

function onTokenDragStart(e) {
  dragToken = e.target;
  e.target.classList.add("dragging");
  e.dataTransfer.setData("text/plain", e.target.dataset.value);
}
function onTokenDragEnd(e) {
  e.target.classList.remove("dragging");
  dragToken = null;
}
function onSlotDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add("drop-hover");
}
function onSlotDragLeave(e) { e.currentTarget.classList.remove("drop-hover"); }
function onSlotDrop(e, stat) {
  e.preventDefault();
  e.currentTarget.classList.remove("drop-hover");
  const val = parseInt(e.dataTransfer.getData("text/plain"));

  // Swap: if stat already has a value, put the old value back in the pool
  const oldVal = state.assignedStats[stat];
  if (oldVal !== null) {
    const pool = document.getElementById("token-pool");
    const returnToken = document.createElement("div");
    returnToken.className = "stat-token";
    returnToken.draggable = true;
    returnToken.dataset.value = oldVal;
    returnToken.textContent = oldVal;
    returnToken.addEventListener("dragstart", onTokenDragStart);
    returnToken.addEventListener("dragend", onTokenDragEnd);
    pool.appendChild(returnToken);
  }

  // Remove token from pool
  if (dragToken && dragToken.parentElement) {
    dragToken.parentElement.removeChild(dragToken);
  }

  state.assignedStats[stat] = val;
  document.getElementById(`slot-val-${stat}`).textContent = val;
  const mod = Math.floor((val - 10) / 2);
  document.getElementById(`slot-mod-${stat}`).textContent = (mod >= 0 ? "+" : "") + mod;

  checkAllStatsAssigned();
}

function checkAllStatsAssigned() {
  const allFilled = Object.values(state.assignedStats).every(v => v !== null);
  if (allFilled) {
    renderASISection();
  }
}

function renderASISection() {
  const bg = state.currentBackground;
  if (!bg) return;
  document.getElementById("asi-section").classList.remove("hidden");
  document.getElementById("asi-hint").textContent =
    `Your background (${bg.name}) allows you to improve: ${(bg.ability_score_options||[]).join(", ")}.`;
  renderASIOptions();
}

function computeASI() {
  const plus2el = document.querySelector('input[name="asi-plus2"]:checked');
  const plus1el = document.querySelector('input[name="asi-plus1"]:checked');
  if (!plus2el || !plus1el) return;
  if (plus2el.value === plus1el.value) { toast("Choose two different abilities."); return; }
  state.backgroundASI = {
    [abilityKey(plus2el.value)]: 2,
    [abilityKey(plus1el.value)]: 1,
  };
  renderFinalAbilityGrid();
  document.getElementById("btn-stats-next").disabled = false;
}

function renderASIOptions() {
  const bg = state.currentBackground;
  if (!bg) return;
  const mode = document.querySelector('input[name="asi-mode"]:checked').value;
  const abilities = bg.ability_score_options || [];
  const container = document.getElementById("asi-options");

  if (mode === "one_one_one") {
    state.backgroundASI = {};
    abilities.forEach(a => { state.backgroundASI[abilityKey(a)] = 1; });
    container.innerHTML = abilities.map(a =>
      `<span style="margin-right:16px;font-family:var(--font-hand)">+1 ${a}</span>`
    ).join("");
    document.getElementById("btn-stats-next").disabled = false;
  } else {
    container.innerHTML = `
      <div class="grid-2">
        <div>
          <p class="hint mb-sm">Which ability gets <strong>+2</strong>?</p>
          ${abilities.map(a => `<label class="flex-row mb-sm"><input type="radio" name="asi-plus2" value="${a}" onchange="computeASI()"> +2 ${a}</label>`).join("")}
        </div>
        <div>
          <p class="hint mb-sm">Which ability gets <strong>+1</strong>?</p>
          ${abilities.map(a => `<label class="flex-row mb-sm"><input type="radio" name="asi-plus1" value="${a}" onchange="computeASI()"> +1 ${a}</label>`).join("")}
        </div>
      </div>`;
    state.backgroundASI = {};
    document.getElementById("btn-stats-next").disabled = true;
  }
  renderFinalAbilityGrid();
}

function renderFinalAbilityGrid() {
  const grid = document.getElementById("final-ability-grid");
  grid.innerHTML = Object.entries(STAT_LABELS).map(([key, label]) => {
    const base = state.assignedStats[key] || 0;
    const bonus = state.backgroundASI[key] || 0;
    const total = base + bonus;
    const mod = Math.floor((total - 10) / 2);
    return `<div class="ability-cell">
      <span class="ability-name">${label.slice(0, 3).toUpperCase()}</span>
      <span class="ability-score">${total || "—"}</span>
      <span class="ability-mod">${total ? ((mod >= 0 ? "+" : "") + mod) : ""}</span>
      ${bonus ? `<span class="ability-total">+${bonus} ASI</span>` : ""}
    </div>`;
  }).join("");
}

function abilityKey(name) {
  return { Strength: "str", Dexterity: "dex", Constitution: "con",
           Intelligence: "int", Wisdom: "wis", Charisma: "cha" }[name] || name.slice(0,3).toLowerCase();
}

async function saveStats() {
  const allFilled = Object.values(state.assignedStats).every(v => v !== null);
  if (!allFilled) { toast("Assign all 6 ability scores first."); return; }
  if (!Object.keys(state.backgroundASI).length) { toast("Choose your Background ASI distribution."); return; }
  try {
    const r = await api("POST", `/api/characters/${state.charId}/step/stats`, {
      base_attributes: state.assignedStats,
      background_asi: state.backgroundASI,
    });
    toast(`HP set to ${r.hp_max}`);
    renderFeaturesStep();
    showStep(6);
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Step 6 — Class Features
// ---------------------------------------------------------------------------
const WEAPON_LIST = [
  "Club","Dagger","Greatclub","Handaxe","Javelin","Light Hammer","Mace",
  "Quarterstaff","Sickle","Spear","Dart","Light Crossbow","Shortbow","Sling",
  "Battleaxe","Flail","Glaive","Greataxe","Greatsword","Halberd","Lance",
  "Longsword","Maul","Morningstar","Pike","Rapier","Scimitar","Shortsword",
  "Trident","Warhammer","War Pick","Whip",
];

function renderFeaturesStep() {
  const cls = state.currentClass;
  if (!cls) return;
  state.featuresChoices = [];
  const container = document.getElementById("features-choices");
  const level1Features = (cls.features || []).filter(f => f.level === 1 && f.choice_required);

  if (!level1Features.length) {
    container.innerHTML = `<p class="hint">No choices required at level 1 for ${cls.name}.</p>`;
    return;
  }

  container.innerHTML = level1Features.map(feat => {
    if (feat.choice_key === "weapon_mastery") {
      // Weapon mastery — pick N weapons from the full list
      const slots = cls.features.find(f => f.name === "Weapon Mastery")?.description.match(/(\d+) weapons/) ?
        parseInt(cls.features.find(f => f.name === "Weapon Mastery").description.match(/(\d+) weapons/)[1]) : 3;
      return `<div class="mb-md">
        <h3>${feat.name}</h3>
        <p class="hint mb-sm">Choose ${slots} weapons to apply mastery properties to. (Select exactly ${slots}.)</p>
        <div class="checklist" id="mastery-checklist">
          ${WEAPON_LIST.map(w =>
            `<label class="check-item"><input type="checkbox" class="mastery-cb" value="${w}" onchange="checkMasteryLimit(${slots})"> ${w}</label>`
          ).join("")}
        </div>
      </div>`;
    }
    if (feat.choice_key === "fighting_style") {
      return `<div class="mb-md">
        <h3>${feat.name}</h3>
        <p class="hint mb-sm">Choose a Fighting Style feat:</p>
        ${(feat.options||[]).map(opt =>
          `<label class="flex-row mb-sm"><input type="radio" name="fighting_style" value="${opt}"> <strong>${opt}</strong></label>`
        ).join("")}
      </div>`;
    }
    if (feat.choice_key === "divine_order") {
      return `<div class="mb-md">
        <h3>${feat.name}</h3>
        <p class="hint mb-sm">Choose your Divine Order:</p>
        ${(feat.options||[]).map(opt =>
          `<label class="flex-row mb-sm"><input type="radio" name="divine_order" value="${opt}"> <strong>${opt}</strong>
           ${opt === "Protector" ? "— Martial weapons + Heavy armor" : "— Extra cantrip + Arcana/Religion bonus"}
           </label>`
        ).join("")}
      </div>`;
    }
    // Generic single-choice
    return `<div class="mb-md">
      <h3>${feat.name}</h3>
      <p class="hint mb-sm">${feat.description}</p>
      ${(feat.options||[]).map(opt =>
        `<label class="flex-row mb-sm"><input type="radio" name="${feat.choice_key}" value="${opt}"> ${opt}</label>`
      ).join("")}
    </div>`;
  }).join("");
}

function checkMasteryLimit(max) {
  const checked = document.querySelectorAll(".mastery-cb:checked");
  if (checked.length > max) {
    document.querySelectorAll(".mastery-cb:not(:checked)").forEach(cb => cb.disabled = true);
  } else {
    document.querySelectorAll(".mastery-cb").forEach(cb => cb.disabled = false);
  }
}

async function saveFeatures() {
  const cls = state.currentClass;
  const choices = [];
  const level1Features = (cls.features || []).filter(f => f.level === 1 && f.choice_required);

  for (const feat of level1Features) {
    if (feat.choice_key === "weapon_mastery") {
      const checked = [...document.querySelectorAll(".mastery-cb:checked")].map(cb => cb.value);
      if (!checked.length) { toast("Choose at least one weapon for Weapon Mastery."); return; }
      choices.push({ feature_key: "weapon_mastery", choice_value: checked });
    } else {
      const selected = document.querySelector(`input[name="${feat.choice_key}"]:checked`);
      if (!selected && feat.options?.length) { toast(`Choose an option for ${feat.name}.`); return; }
      if (selected) choices.push({ feature_key: feat.choice_key, choice_value: selected.value });
    }
  }

  // Spellcasting cantrip count for Cleric Divine Order (Thaumaturge gets extra cantrip)
  const divineOrderChoice = choices.find(c => c.feature_key === "divine_order");
  if (divineOrderChoice?.choice_value === "Thaumaturge") {
    state._clericExtraCantrip = true;
  }

  state.featuresChoices = choices;
  try {
    await api("POST", `/api/characters/${state.charId}/step/features`, { choices });
    renderSkillsStep();
    showStep(7);
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Step 7 — Skills & Languages
// ---------------------------------------------------------------------------
const ALL_SKILLS = [
  "Acrobatics","Animal Handling","Arcana","Athletics","Deception",
  "History","Insight","Intimidation","Investigation","Medicine",
  "Nature","Perception","Performance","Persuasion","Religion",
  "Sleight of Hand","Stealth","Survival",
];

function renderSkillsStep() {
  const cls = state.currentClass;
  const bg = state.currentBackground;
  if (!cls || !bg) return;

  const bgSkills = bg.skill_proficiencies || [];
  const classOptions = cls.skill_options || [];
  const needed = cls.skill_choices || 2;

  document.getElementById("skills-section").innerHTML =
    `<h3>Class Skills (choose ${needed})</h3>
     <p class="hint mb-sm">Your background already grants: ${bgSkills.join(", ")}.</p>
     <div class="checklist" id="class-skill-list">
       ${classOptions.map(skill => {
         const fromBg = bgSkills.includes(skill);
         return `<label class="check-item ${fromBg ? "already-proficient" : ""}">
           <input type="checkbox" class="class-skill-cb" value="${skill}"
             ${fromBg ? "checked disabled" : ""}
             onchange="checkSkillLimit(${needed})">
           ${skill}${fromBg ? " <em>(background)</em>" : ""}
         </label>`;
       }).join("")}
     </div>`;

  // Language pickers
  document.getElementById("languages-section").innerHTML =
    `<div class="grid-2">
       <div>
         <label>Language 1</label>
         <select id="lang-1">
           ${ALL_LANGUAGES.filter(l => l !== "Common").map(l => `<option>${l}</option>`).join("")}
         </select>
       </div>
       <div>
         <label>Language 2</label>
         <select id="lang-2">
           ${ALL_LANGUAGES.filter(l => l !== "Common").map(l => `<option>${l}</option>`).join("")}
         </select>
       </div>
     </div>`;
}

function checkSkillLimit(max) {
  const freeChecks = [...document.querySelectorAll(".class-skill-cb:checked:not(:disabled)")];
  if (freeChecks.length >= max) {
    document.querySelectorAll(".class-skill-cb:not(:checked):not(:disabled)").forEach(cb => cb.disabled = true);
  } else {
    const bgSkills = state.currentBackground?.skill_proficiencies || [];
    document.querySelectorAll(".class-skill-cb").forEach(cb => {
      if (!bgSkills.includes(cb.value)) cb.disabled = false;
    });
  }
}

async function saveSkills() {
  const cls = state.currentClass;
  const bg = state.currentBackground;
  const bgSkills = bg?.skill_proficiencies || [];
  const needed = cls?.skill_choices || 2;
  const chosen = [...document.querySelectorAll(".class-skill-cb:checked:not(:disabled)")].map(cb => cb.value);

  if (chosen.length !== needed) { toast(`Choose exactly ${needed} class skills.`); return; }

  const lang1 = document.getElementById("lang-1")?.value;
  const lang2 = document.getElementById("lang-2")?.value;
  const langs = ["Common"];
  if (lang1) langs.push(lang1);
  if (lang2 && lang2 !== lang1) langs.push(lang2);

  state.selectedSkills = chosen;
  state.selectedLanguages = langs;

  try {
    await api("POST", `/api/characters/${state.charId}/step/skills`, {
      skills: chosen,
      languages: langs,
    });
    renderEquipmentStep();
    showStep(8);
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Step 8 — Equipment
// ---------------------------------------------------------------------------
function renderEquipmentStep() {
  const cls = state.currentClass;
  const bg = state.currentBackground;
  document.getElementById("equip-class-header").textContent = `${cls?.name || "Class"} Equipment`;
  document.getElementById("equip-bg-header").textContent = `${bg?.name || "Background"} Equipment`;
  renderEquipOptions("class-equipment-options", cls?.equipment_options || [], "class");
  renderEquipOptions("background-equipment-options", bg?.equipment_options || [], "bg");
}

function renderEquipOptions(containerId, options, prefix) {
  const container = document.getElementById(containerId);
  if (!options.length) { container.innerHTML = `<p class="hint">No equipment options found.</p>`; return; }

  container.innerHTML = options.map((opt, idx) => {
    const isGold = opt.gold && !opt.items?.length;
    const label = isGold
      ? `<strong>Option ${opt.label}:</strong> ${opt.gold} GP`
      : `<strong>Option ${opt.label}:</strong> ` + renderItemList(opt.items || []);
    const choiceHtml = buildChoiceSelects(opt.items || [], opt.label, prefix);
    return `<div class="mb-sm">
      <label class="flex-row">
        <input type="radio" name="${prefix}-equip-opt" value="${opt.label}"
          ${idx === 0 ? "checked" : ""} onchange="selectEquipOption('${prefix}', '${opt.label}', ${JSON.stringify(opt).replace(/"/g,'&quot;')})">
        ${label}
      </label>
      ${choiceHtml ? `<div id="${prefix}-choices-${opt.label}" class="mt-sm" style="padding-left:24px;">${choiceHtml}</div>` : ""}
    </div>`;
  }).join("");

  // Initialize first option
  if (options[0]) {
    state[prefix === "class" ? "classEquipOption" : "bgEquipOption"] = options[0].label;
  }
}

function renderItemList(items) {
  return items.map(i => {
    if (i.type === "gold") return `${i.qty} GP`;
    if (i.type === "choice") return `<em>${i.name}</em>`;
    return `${i.qty > 1 ? i.qty + "× " : ""}${i.name}`;
  }).join(", ");
}

function buildChoiceSelects(items, optLabel, prefix) {
  return items.filter(i => i.type === "choice" || i.type === "ref").map((item, idx) => {
    if (item.type === "ref") {
      // Resolved by tool_proficiency_choice — show as info
      return `<p class="hint">${item.qty > 1 ? item.qty + "× " : ""}Your chosen tool proficiency will be added to your inventory.</p>`;
    }
    const cat = item.category || "";
    const choices = TOOL_OPTIONS[Object.keys(TOOL_OPTIONS).find(k => k.toLowerCase().includes(cat.toLowerCase().split(" ").pop())) || ""] || [];
    if (!choices.length) return `<p class="hint">Choose: ${item.name}</p>`;
    return `<label>${item.name}:
      <select id="${prefix}-choice-${optLabel}-${idx}">
        ${choices.map(c => `<option>${c}</option>`).join("")}
      </select>
    </label>`;
  }).join("");
}

function selectEquipOption(prefix, label, optData) {
  if (prefix === "class") state.classEquipOption = label;
  else state.bgEquipOption = label;
}

async function saveEquipment() {
  const cls = state.currentClass;
  const bg = state.currentBackground;
  const classOptLabel = state.classEquipOption || (cls?.equipment_options?.[0]?.label ?? "A");
  const bgOptLabel = state.bgEquipOption || (bg?.equipment_options?.[0]?.label ?? "A");

  const allOpts = [
    ...(cls?.equipment_options || []).filter(o => o.label === classOptLabel),
    ...(bg?.equipment_options || []).filter(o => o.label === bgOptLabel),
  ];

  const resolvedItems = [];
  for (const opt of allOpts) {
    if (opt.gold && !opt.items?.length) {
      resolvedItems.push({ name: "Gold", qty: opt.gold, equipped: false });
    } else {
      for (const item of opt.items || []) {
        if (item.type === "gold") {
          resolvedItems.push({ name: "Gold", qty: item.qty, equipped: false });
        } else if (item.type === "ref") {
          const toolName = state.currentBackground?.tool_proficiency;
          if (toolName && !toolName.toLowerCase().startsWith("choose")) {
            resolvedItems.push({ name: toolName, qty: item.qty, equipped: false });
          }
        } else if (item.type === "choice") {
          // Try to find a select for this choice
          const selects = document.querySelectorAll(`[id*="-choice-"]`);
          const sel = [...selects].find(s => s.id.includes(item.name.slice(0,6).replace(/\s/g,"")));
          resolvedItems.push({ name: sel ? sel.value : item.name, qty: item.qty, equipped: false });
        } else {
          resolvedItems.push({ name: item.name, qty: item.qty, equipped: false });
        }
      }
    }
  }

  state.resolvedItems = resolvedItems;

  try {
    await api("POST", `/api/characters/${state.charId}/step/equipment`, {
      class_option: classOptLabel,
      background_option: bgOptLabel,
      resolved_items: resolvedItems,
    });

    // Check if spells needed
    if (cls?.spellcasting_type) {
      await loadSpellsStep();
      showStep(9);
    } else {
      showStep(10);
    }
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Step 9 — Spells
// ---------------------------------------------------------------------------
async function loadSpellsStep() {
  const cls = state.currentClass;
  if (!cls) return;
  state.allSpells = await api("GET", `/api/content/spells?class_name=${encodeURIComponent(cls.name)}`);
  renderSpellsStep();
}

function renderSpellsStep() {
  const cls = state.currentClass;
  if (!cls) return;

  // Cantrip counts by class at level 1
  const cantripCounts = {
    Bard: 2, Cleric: 3, Druid: 2, Sorcerer: 4, Wizard: 3, Warlock: 2,
  };
  // Spell counts at level 1
  const spellCounts = {
    Bard: 4, Cleric: 4, Druid: 4, Sorcerer: 2, Wizard: 6, Warlock: 2, Paladin: 2, Ranger: 2,
  };
  const cantripCount = cantripCounts[cls.name] || 2;
  const spellCount = spellCounts[cls.name] || 2;

  const cantrips = state.allSpells.filter(s => s.level === 0);
  const spells1 = state.allSpells.filter(s => s.level === 1);

  document.getElementById("spells-hint").textContent =
    `Choose ${cantripCount} cantrip${cantripCount > 1 ? "s" : ""} and ${spellCount} level 1 spell${spellCount > 1 ? "s" : ""}.`;

  const cantripSec = document.getElementById("cantrips-section");
  cantripSec.innerHTML = cantrips.length
    ? `<h3>Cantrips (choose ${cantripCount})</h3>
       <div class="spell-grid" id="cantrip-cards">
         ${cantrips.map(s => spellCard(s, "cantrip", cantripCount)).join("")}
       </div>`
    : "";

  const spell1Sec = document.getElementById("level1-spells-section");
  spell1Sec.innerHTML = spells1.length
    ? `<h3>Level 1 Spells (choose ${spellCount})</h3>
       <div class="spell-grid" id="spell1-cards">
         ${spells1.map(s => spellCard(s, "spell1", spellCount)).join("")}
       </div>`
    : "";

  window._cantripCount = cantripCount;
  window._spellCount = spellCount;
}

function spellCard(spell, group, max) {
  const conc = spell.concentration ? " · Conc." : "";
  const ritual = spell.ritual ? " · Ritual" : "";
  return `<div class="spell-card" id="sc-${spell.id}" data-id="${spell.id}" data-group="${group}"
    onclick="toggleSpell(${spell.id},'${group}',${max})">
    <span class="spell-name">${spell.name}</span>
    <span class="spell-meta">${spell.school}${conc}${ritual} · ${spell.casting_time}</span>
    <span class="spell-desc">${(spell.description||"").slice(0,120)}…</span>
  </div>`;
}

function toggleSpell(id, group, max) {
  const el = document.getElementById(`sc-${id}`);
  const isChosen = el.classList.contains("chosen");
  if (isChosen) {
    el.classList.remove("chosen");
  } else {
    const chosen = document.querySelectorAll(`.spell-card.chosen[data-group="${group}"]`);
    if (chosen.length >= max) { toast(`You can only choose ${max} from this group.`); return; }
    el.classList.add("chosen");
  }
}

async function saveSpells() {
  const cantripIds = [...document.querySelectorAll('.spell-card.chosen[data-group="cantrip"]')].map(el => +el.dataset.id);
  const spellIds = [...document.querySelectorAll('.spell-card.chosen[data-group="spell1"]')].map(el => +el.dataset.id);

  const needed = window._cantripCount || 0;
  const neededSpells = window._spellCount || 0;
  if (cantripIds.length < needed) { toast(`Choose ${needed} cantrips.`); return; }
  if (spellIds.length < neededSpells) { toast(`Choose ${neededSpells} level 1 spells.`); return; }

  state.cantripIds = cantripIds;
  state.spellIds = spellIds;

  try {
    await api("POST", `/api/characters/${state.charId}/step/spells`, {
      cantrip_ids: cantripIds,
      spell_ids: spellIds,
    });
    showStep(10);
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Step 10 — Bio
// ---------------------------------------------------------------------------
async function saveBio() {
  const alignment = document.getElementById("alignment-select").value;
  const bio = document.getElementById("bio-text").value.trim();
  try {
    await api("POST", `/api/characters/${state.charId}/step/bio`, { alignment, bio });
    renderDoneStep();
    showStep(11);
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Done
// ---------------------------------------------------------------------------
function renderDoneStep() {
  const cls = state.currentClass?.name || "—";
  const sp = state.currentSpecies?.name || "—";
  const bg = state.currentBackground?.name || "—";
  document.getElementById("done-summary").textContent =
    `${state.charName} · ${sp} ${cls} · ${bg} · Created by ${state.displayName}`;
}

async function exportJSON(e) {
  e.preventDefault();
  const data = await api("GET", `/api/characters/${state.charId}/export/json`);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${state.charName || "character"}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

async function exportPDF(e) {
  e.preventDefault();
  const res = await fetch(`/api/characters/${state.charId}/export/pdf`);
  if (!res.ok) { err("PDF generation failed."); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${state.charName || "character"}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

function startNewCharacter() {
  Object.assign(state, {
    charId: null, step: 1, displayName: "", charName: "",
    speciesId: null, backgroundId: null, classId: null,
    selectedRollSet: null,
    assignedStats: { str: null, dex: null, con: null, int: null, wis: null, cha: null },
    backgroundASI: {}, featuresChoices: [], selectedSkills: [], selectedLanguages: [],
    classEquipOption: null, bgEquipOption: null, resolvedItems: [],
    cantripIds: [], spellIds: [], currentClass: null, currentBackground: null, currentSpecies: null,
  });
  document.getElementById("display-name").value = "";
  document.getElementById("char-name").value = "";
  showStep(1);
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
showStep(1);
