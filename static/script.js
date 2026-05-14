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
  speciesLineage: null,
  speciesSizeChoice: null,
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
  shopCart: [],
  shopTab: "weapon",
  equipCatalog: [],
  cantripIds: [],
  spellIds: [],
  // content cache
  allSpecies: [],
  allBackgrounds: [],
  allClasses: [],
  allSpells: [],
  ownedSpells: [],
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

const STANDARD_LANGUAGES = [
  "Common Sign Language", "Draconic", "Dwarvish", "Elvish",
  "Giant", "Gnomish", "Goblin", "Halfling", "Orc",
];

const SPECIES_LANGUAGE = {
  "Dragonborn": "Draconic",
  "Dwarf": "Dwarvish",
  "Elf": "Elvish",
  "Gnome": "Gnomish",
  "Goliath": "Giant",
  "Halfling": "Halfling",
  "Orc": "Orc",
};

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
  if (res.status === 401) { window.location.href = "/auth/login"; return; }
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP ${res.status}`);
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
  state.speciesLineage = null;
  state.speciesSizeChoice = null;
  document.querySelectorAll("#species-grid .select-card").forEach(c =>
    c.classList.toggle("selected", +c.dataset.id === id));
  const sp = state.allSpecies.find(s => s.id === id);
  if (!sp) return;
  state.currentSpecies = sp;

  document.getElementById("species-detail-name").textContent = sp.name;
  document.getElementById("species-detail-body").innerHTML =
    `<p class="hint mb-sm">${sp.creature_type} · ${(sp.size_options||[]).join(" or ")} · Speed ${sp.speed} ft.</p>` +
    (sp.traits||[]).map(t =>
      `<p class="mb-sm"><strong class="trait-name">${t.name}.</strong> ${t.description}</p>`
    ).join("");

  // Lineage selector
  const lineageSec = document.getElementById("species-lineage-section");
  const lineageSel = document.getElementById("species-lineage-select");
  const lineageDesc = document.getElementById("species-lineage-desc");
  if (sp.lineages && sp.lineages.length) {
    // Determine label from first trait whose name contains a choice keyword
    const lineageTrait = (sp.traits||[]).find(t =>
      /lineage|legacy|ancestry/i.test(t.name));
    document.getElementById("species-lineage-label").textContent =
      lineageTrait ? `Choose a ${lineageTrait.name}` : "Choose a Lineage";
    lineageSel.innerHTML = '<option value="">— Select —</option>' +
      sp.lineages.map(l => `<option value="${l.name}">${l.name}</option>`).join("");
    lineageDesc.textContent = "";
    lineageSec.classList.remove("hidden");
  } else {
    lineageSec.classList.add("hidden");
  }

  // Size selector
  const sizeSec = document.getElementById("species-size-section");
  if ((sp.size_options||[]).length > 1) {
    const pills = document.getElementById("species-size-options");
    pills.innerHTML = sp.size_options.map(sz =>
      `<button class="pill" onclick="selectSize('${sz}')">${sz}</button>`
    ).join("");
    sizeSec.classList.remove("hidden");
  } else {
    sizeSec.classList.add("hidden");
    state.speciesSizeChoice = (sp.size_options||[])[0] || null;
  }

  document.getElementById("species-detail").classList.add("visible");
  _updateSpeciesNextBtn();
}

function onLineageChange() {
  const sel = document.getElementById("species-lineage-select");
  state.speciesLineage = sel.value || null;
  const sp = state.currentSpecies;
  if (sp && sp.lineages) {
    const entry = sp.lineages.find(l => l.name === sel.value);
    const desc = document.getElementById("species-lineage-desc");
    if (entry) {
      let text = entry.description || "";
      if (entry.level3_spell) text += ` · Level 3: ${entry.level3_spell}`;
      if (entry.level5_spell) text += ` · Level 5: ${entry.level5_spell}`;
      desc.textContent = text;
    } else {
      desc.textContent = "";
    }
  }
  _updateSpeciesNextBtn();
}

function selectSize(sz) {
  state.speciesSizeChoice = sz;
  document.querySelectorAll("#species-size-options .pill").forEach(p =>
    p.classList.toggle("selected", p.textContent === sz));
  _updateSpeciesNextBtn();
}

function _updateSpeciesNextBtn() {
  const sp = state.currentSpecies;
  if (!sp) { document.getElementById("btn-species-next").disabled = true; return; }
  const needsLineage = sp.lineages && sp.lineages.length && !state.speciesLineage;
  const needsSize = (sp.size_options||[]).length > 1 && !state.speciesSizeChoice;
  document.getElementById("btn-species-next").disabled = !!(needsLineage || needsSize);
}

function saveSpecies() {
  if (!state.speciesId) { toast("Pick a species first."); return; }
  const sp = state.currentSpecies;
  if (sp && sp.lineages && sp.lineages.length && !state.speciesLineage) {
    toast("Choose a lineage before continuing."); return;
  }
  if (sp && (sp.size_options||[]).length > 1 && !state.speciesSizeChoice) {
    toast("Choose a size before continuing."); return;
  }
  api("POST", `/api/characters/${state.charId}/step/species`, {
    species_id: state.speciesId,
    species_lineage: state.speciesLineage,
    species_size_choice: state.speciesSizeChoice,
  })
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
    const choices = TOOL_OPTIONS[bg.tool_proficiency] || [];
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
    const casting = "";
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
  const container = document.getElementById("manual-fields");
  container.innerHTML = [1,2,3,4,5,6].map(i =>
    `<input type="number" id="manual-val-${i}" min="1" max="20" placeholder="${i}">`
  ).join("");
}

function showManualEntry() {
  document.getElementById("manual-entry").classList.remove("hidden");
  document.getElementById("roll-set-picker").classList.add("hidden");
  document.getElementById("stat-assignment").classList.add("hidden");
  document.getElementById("manual-fields").querySelector("input")?.focus();
}

async function autoRoll() {
  try {
    const r = await api("POST", `/api/characters/${state.charId}/roll-stats`);
    renderRollSets(r.sets, false);
  } catch(e) { err(e.message); }
}

function submitManualRolls() {
  const nums = [];
  for (let i = 1; i <= 6; i++) {
    const n = parseInt(document.getElementById(`manual-val-${i}`).value, 10);
    if (!n || n < 1 || n > 20) { toast(`Value ${i} must be a number between 1 and 20.`); return; }
    nums.push(n);
  }
  document.getElementById("manual-entry").classList.add("hidden");
  renderStatAssignment(nums);
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
  const fromStat = e.dataTransfer.getData("from-stat");

  // If dragging from another slot, swap values
  if (fromStat && fromStat !== stat) {
    const oldVal = state.assignedStats[stat];
    // Update the source slot
    state.assignedStats[fromStat] = oldVal;
    const srcCell = document.getElementById(`slot-val-${fromStat}`);
    if (oldVal !== null) {
      srcCell.textContent = oldVal;
      srcCell.dataset.value = oldVal;
      srcCell.dataset.stat = fromStat;
      const srcMod = Math.floor((oldVal - 10) / 2);
      document.getElementById(`slot-mod-${fromStat}`).textContent = (srcMod >= 0 ? "+" : "") + srcMod;
    } else {
      srcCell.textContent = "—";
      srcCell.draggable = false;
      srcCell.classList.remove("assigned-token");
      srcCell.ondragstart = null;
      document.getElementById(`slot-mod-${fromStat}`).textContent = "";
    }
    state.assignedStats[stat] = val;
  } else {
    // Dragging from pool — if slot occupied, return old value to pool
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
  }
  const cell = document.getElementById(`slot-val-${stat}`);
  cell.textContent = val;
  cell.draggable = true;
  cell.dataset.value = val;
  cell.dataset.stat = stat;
  cell.classList.add("assigned-token");
  cell.ondragstart = (ev) => {
    dragToken = ev.currentTarget;
    ev.currentTarget.classList.add("dragging");
    ev.dataTransfer.setData("text/plain", ev.currentTarget.dataset.value);
    ev.dataTransfer.setData("from-stat", stat);
  };
  cell.ondragend = (ev) => {
    ev.currentTarget.classList.remove("dragging");
    dragToken = null;
  };
  const mod = Math.floor((val - 10) / 2);
  document.getElementById(`slot-mod-${stat}`).textContent = (mod >= 0 ? "+" : "") + mod;

  checkAllStatsAssigned();
}

function onPoolDrop(e) {
  e.preventDefault();
  const fromStat = e.dataTransfer.getData("from-stat");
  if (!fromStat) return;
  const val = parseInt(e.dataTransfer.getData("text/plain"));
  // Return to pool
  const pool = document.getElementById("token-pool");
  const token = document.createElement("div");
  token.className = "stat-token";
  token.draggable = true;
  token.dataset.value = val;
  token.textContent = val;
  token.addEventListener("dragstart", onTokenDragStart);
  token.addEventListener("dragend", onTokenDragEnd);
  pool.appendChild(token);
  // Clear the slot
  state.assignedStats[fromStat] = null;
  const cell = document.getElementById(`slot-val-${fromStat}`);
  cell.textContent = "—";
  cell.draggable = false;
  cell.classList.remove("assigned-token");
  cell.ondragstart = null;
  document.getElementById(`slot-mod-${fromStat}`).textContent = "";
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
const FIGHTING_STYLE_DESCRIPTIONS = {
  "Archery":               "+2 bonus to attack rolls with Ranged weapons.",
  "Blind Fighting":        "Blindsight with a range of 10 feet.",
  "Defense":               "+1 AC while wearing Light, Medium, or Heavy armor.",
  "Dueling":               "+2 damage rolls with a Melee weapon held in one hand while wielding no other weapons.",
  "Great Weapon Fighting": "When rolling damage with a Melee weapon held in two hands (Two-Handed or Versatile), treat any 1 or 2 on a damage die as a 3.",
  "Interception":          "Reaction — when a creature within 5 ft is hit by an attack, reduce damage by 1d10 + Proficiency Bonus. Must hold a Shield or Simple/Martial weapon.",
  "Protection":            "Reaction — impose Disadvantage on an attack against an ally within 5 ft. Requires a Shield.",
  "Thrown Weapon Fighting":"+ 2 damage on hits with a weapon that has the Thrown property.",
  "Two-Weapon Fighting":   "Add your ability modifier to the damage of the extra attack granted by the Light property.",
  "Unarmed Fighting":      "Unarmed Strikes deal 1d6 + Strength Bludgeoning damage (1d8 if not holding a weapon or Shield). At turn start, deal 1d4 Bludgeoning to one creature you've Grappled.",
};

const MASTERY_PROPERTIES = {
  Club:          { name: "Slow",   desc: "On hit, reduce target's Speed by 10 ft until the start of your next turn." },
  Dagger:        { name: "Nick",   desc: "Make the Light extra attack as part of the Attack action, not a Bonus Action." },
  Greatclub:     { name: "Push",   desc: "On hit, push target up to 10 ft away (Large or smaller)." },
  Handaxe:       { name: "Vex",    desc: "On hit, gain Advantage on your next attack roll against that target." },
  Javelin:       { name: "Slow",   desc: "On hit, reduce target's Speed by 10 ft until the start of your next turn." },
  "Light Hammer":{ name: "Nick",   desc: "Make the Light extra attack as part of the Attack action, not a Bonus Action." },
  Mace:          { name: "Sap",    desc: "On hit, target has Disadvantage on its next attack roll before your next turn." },
  Quarterstaff:  { name: "Topple", desc: "On hit, target makes a Constitution save or gains the Prone condition." },
  Sickle:        { name: "Nick",   desc: "Make the Light extra attack as part of the Attack action, not a Bonus Action." },
  Spear:         { name: "Sap",    desc: "On hit, target has Disadvantage on its next attack roll before your next turn." },
  Dart:          { name: "Vex",    desc: "On hit, gain Advantage on your next attack roll against that target." },
  "Light Crossbow":{ name: "Slow", desc: "On hit, reduce target's Speed by 10 ft until the start of your next turn." },
  Shortbow:      { name: "Vex",    desc: "On hit, gain Advantage on your next attack roll against that target." },
  Sling:         { name: "Slow",   desc: "On hit, reduce target's Speed by 10 ft until the start of your next turn." },
  Battleaxe:     { name: "Topple", desc: "On hit, target makes a Constitution save or gains the Prone condition." },
  Flail:         { name: "Sap",    desc: "On hit, target has Disadvantage on its next attack roll before your next turn." },
  Glaive:        { name: "Graze",  desc: "On a miss, deal damage equal to your ability modifier (min 0)." },
  Greataxe:      { name: "Cleave", desc: "On hit, make one free melee attack against a second creature within 5 ft (once per turn, no ability mod to damage)." },
  Greatsword:    { name: "Graze",  desc: "On a miss, deal damage equal to your ability modifier (min 0)." },
  Halberd:       { name: "Cleave", desc: "On hit, make one free melee attack against a second creature within 5 ft (once per turn, no ability mod to damage)." },
  Lance:         { name: "Topple", desc: "On hit, target makes a Constitution save or gains the Prone condition." },
  Longsword:     { name: "Sap",    desc: "On hit, target has Disadvantage on its next attack roll before your next turn." },
  Maul:          { name: "Topple", desc: "On hit, target makes a Constitution save or gains the Prone condition." },
  Morningstar:   { name: "Sap",    desc: "On hit, target has Disadvantage on its next attack roll before your next turn." },
  Pike:          { name: "Push",   desc: "On hit, push target up to 10 ft away (Large or smaller)." },
  Rapier:        { name: "Vex",    desc: "On hit, gain Advantage on your next attack roll against that target." },
  Scimitar:      { name: "Nick",   desc: "Make the Light extra attack as part of the Attack action, not a Bonus Action." },
  Shortsword:    { name: "Vex",    desc: "On hit, gain Advantage on your next attack roll against that target." },
  Trident:       { name: "Topple", desc: "On hit, target makes a Constitution save or gains the Prone condition." },
  Warhammer:     { name: "Push",   desc: "On hit, push target up to 10 ft away (Large or smaller)." },
  "War Pick":    { name: "Slow",   desc: "On hit, reduce target's Speed by 10 ft until the start of your next turn." },
  Whip:          { name: "Slow",   desc: "On hit, reduce target's Speed by 10 ft until the start of your next turn." },
};

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
          ${WEAPON_LIST.map(w => {
            const mp = MASTERY_PROPERTIES[w];
            const titleAttr = mp ? ` title="${mp.name}: ${mp.desc}"` : "";
            const tag = mp ? `<span class="mastery-tag" title="${mp.desc}">${mp.name}</span>` : "";
            return `<label class="check-item"${titleAttr}><input type="checkbox" class="mastery-cb" value="${w}" onchange="checkMasteryLimit(${slots})"> ${w}${tag}</label>`;
          }).join("")}
        </div>
      </div>`;
    }
    if (feat.choice_key === "fighting_style") {
      return `<div class="mb-md">
        <h3>${feat.name}</h3>
        <p class="hint mb-sm">Choose a Fighting Style feat:</p>
        ${(feat.options||[]).map(opt => {
          const desc = FIGHTING_STYLE_DESCRIPTIONS[opt] || "";
          return `<label class="feat-option">
            <span class="feat-option-header"><input type="radio" name="fighting_style" value="${opt}"> ${opt}</span>
            ${desc ? `<span class="feat-option-desc">${desc}</span>` : ""}
          </label>`;
        }).join("")}
      </div>`;
    }
    if (feat.choice_key === "divine_order") {
      const divineDescs = {
        "Protector":    "Gain proficiency with Martial weapons and Heavy armor.",
        "Thaumaturge":  "Learn one extra Cleric cantrip and gain Expertise in Arcana or Religion.",
      };
      return `<div class="mb-md">
        <h3>${feat.name}</h3>
        <p class="hint mb-sm">Choose your Divine Order:</p>
        ${(feat.options||[]).map(opt => {
          const desc = divineDescs[opt] || "";
          return `<label class="feat-option">
            <span class="feat-option-header"><input type="radio" name="divine_order" value="${opt}"> ${opt}</span>
            ${desc ? `<span class="feat-option-desc">${desc}</span>` : ""}
          </label>`;
        }).join("")}
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
  const ALL_SKILLS = ["Acrobatics","Animal Handling","Arcana","Athletics","Deception","History","Insight","Intimidation","Investigation","Medicine","Nature","Perception","Performance","Persuasion","Religion","Sleight of Hand","Stealth","Survival"];
  const classOptions = (cls.skill_options && cls.skill_options.length > 0) ? cls.skill_options : ALL_SKILLS;
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
  const className = state.currentClass?.name || "";
  const speciesName = state.currentSpecies?.name || "";
  const speciesLang = SPECIES_LANGUAGE[speciesName] || null;
  const isRogue = className === "Rogue";
  const isDruid = className === "Druid";

  const grantedLanguages = [];
  if (isRogue) grantedLanguages.push("Thieves' Cant");
  if (isDruid) grantedLanguages.push("Druidic");

  const classNote = grantedLanguages.length
    ? `<p class="hint mb-sm">Your class grants you <strong>${grantedLanguages.join(" and ")}</strong> — no choice needed.</p>`
    : "";

  const pickerCount = isRogue ? 3 : 2;
  const defaults = [speciesLang, STANDARD_LANGUAGES.find(l => l !== speciesLang), null];

  const pickerHtml = Array.from({ length: pickerCount }, (_, i) =>
    `<div><label>Language ${i + 1}</label>
      <select id="lang-${i + 1}" onchange="syncLangPickers()">
        <option value="">— choose —</option>
        ${STANDARD_LANGUAGES.map(l => `<option${l === defaults[i] ? " selected" : ""}>${l}</option>`).join("")}
      </select></div>`
  ).join("");

  document.getElementById("languages-section").innerHTML = `
    ${classNote}
    <div class="grid-2">${pickerHtml}</div>`;

  syncLangPickers();
}

function syncLangPickers() {
  const selects = [1, 2, 3].map(i => document.getElementById(`lang-${i}`)).filter(Boolean);
  const selected = selects.map(s => s.value);
  selects.forEach((sel, i) => {
    const others = selected.filter((_, j) => j !== i);
    const current = sel.value;
    sel.innerHTML = `<option value="">— choose —</option>` + STANDARD_LANGUAGES
      .filter(l => l === current || !others.includes(l))
      .map(l => `<option${l === current ? " selected" : ""}>${l}</option>`)
      .join("");
  });
  const allChosen = selects.every(s => s.value !== "");
  document.getElementById("btn-skills-next").disabled = !allChosen;
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
  if (state.currentClass?.name === "Rogue") langs.push("Thieves' Cant");
  if (state.currentClass?.name === "Druid") langs.push("Druidic");
  const lang3 = document.getElementById("lang-3")?.value;
  if (lang1) langs.push(lang1);
  if (lang2 && lang2 !== lang1) langs.push(lang2);
  if (lang3 && lang3 !== lang1 && lang3 !== lang2) langs.push(lang3);

  state.selectedSkills = chosen;
  state.selectedLanguages = langs;

  try {
    await api("POST", `/api/characters/${state.charId}/step/skills`, {
      skills: chosen,
      languages: langs,
    });
    await renderEquipmentStep();
    showStep(8);
  } catch(e) { err(e.message); }
}

// ---------------------------------------------------------------------------
// Step 8 — Equipment
// ---------------------------------------------------------------------------
async function renderEquipmentStep() {
  const cls = state.currentClass;
  const bg = state.currentBackground;
  document.getElementById("equip-class-header").textContent = `${cls?.name || "Class"} Equipment`;
  document.getElementById("equip-bg-header").textContent = `${bg?.name || "Background"} Equipment`;
  state.shopCart = [];
  state.shopTab = "weapon";
  if (!state.equipCatalog.length) {
    try { state.equipCatalog = await api("GET", "/api/content/equipment"); } catch(e) { state.equipCatalog = []; }
  }
  renderEquipOptions("class-equipment-options", cls?.equipment_options || [], "class");
  renderEquipOptions("background-equipment-options", bg?.equipment_options || [], "bg");
  updateShopVisibility();
}

function parseCostGP(costStr) {
  if (!costStr) return 0;
  const m = costStr.match(/([\d.]+)\s*(GP|SP|CP)/i);
  if (!m) return 0;
  const n = parseFloat(m[1]);
  const unit = m[2].toUpperCase();
  if (unit === "GP") return n;
  if (unit === "SP") return n / 10;
  return n / 100;
}

function shopGetBudget() {
  const classOpts = state.currentClass?.equipment_options || [];
  const bgOpts = state.currentBackground?.equipment_options || [];
  const classOpt = classOpts.find(o => o.label === state.classEquipOption);
  const bgOpt = bgOpts.find(o => o.label === state.bgEquipOption);
  return ((classOpt?.gold && !classOpt?.items?.length) ? classOpt.gold : 0)
       + ((bgOpt?.gold && !bgOpt?.items?.length) ? bgOpt.gold : 0);
}

function shopSpent() {
  return state.shopCart.reduce((sum, i) => sum + i.qty * parseCostGP(i.cost), 0);
}

function shopAddItem(name) {
  const item = state.equipCatalog.find(i => i.name === name);
  if (!item) return;
  const existing = state.shopCart.find(c => c.name === name);
  if (existing) existing.qty++;
  else state.shopCart.push({ name: item.name, qty: 1, cost: item.cost, item_type: item.item_type });
  renderShop();
}

function shopRemoveItem(name) {
  const idx = state.shopCart.findIndex(c => c.name === name);
  if (idx === -1) return;
  if (state.shopCart[idx].qty > 1) state.shopCart[idx].qty--;
  else state.shopCart.splice(idx, 1);
  renderShop();
}

function setShopTab(tab) {
  state.shopTab = tab;
  renderShop();
}

function updateShopVisibility() {
  const budget = shopGetBudget();
  const shopDiv = document.getElementById("unified-shop");
  if (!shopDiv) return;
  if (budget > 0) {
    shopDiv.classList.remove("hidden");
    renderShop();
  } else {
    shopDiv.classList.add("hidden");
  }
}

function renderShop() {
  const container = document.getElementById("unified-shop");
  if (!container) return;
  const budget = shopGetBudget();
  const spent = Math.round(shopSpent() * 100) / 100;
  const remaining = Math.round((budget - spent) * 100) / 100;
  const over = spent > budget;
  const pct = Math.min(100, budget > 0 ? Math.round((spent / budget) * 100) : 0);
  const tab = state.shopTab;
  const cart = state.shopCart;

  const CAT_ORDER = ["Pack","Ammunition","Arcane Focus","Druidic Focus","Holy Symbol","Gear"];
  const items = state.equipCatalog.filter(i => {
    if (tab === "weapon") return i.item_type === "weapon";
    if (tab === "armor")  return i.item_type === "armor" || i.item_type === "shield";
    return ["gear","pack","focus","ammunition"].includes(i.item_type);
  }).sort((a, b) => {
    if (tab === "gear") {
      const ca = CAT_ORDER.indexOf(a.category) === -1 ? 99 : CAT_ORDER.indexOf(a.category);
      const cb = CAT_ORDER.indexOf(b.category) === -1 ? 99 : CAT_ORDER.indexOf(b.category);
      if (ca !== cb) return ca - cb;
    }
    return a.name.localeCompare(b.name);
  });

  container.innerHTML = `
    <div class="shop-panel">
      <h4 style="margin:0 0 10px;font-family:var(--font-display);letter-spacing:.05em;">Spend Your Gold (${budget} GP total)</h4>
      <div class="shop-budget">
        <div class="shop-budget-bar"><div class="shop-budget-fill${over ? " over" : ""}" style="width:${pct}%"></div></div>
        <div class="shop-budget-text${over ? " over" : ""}">
          ${spent} / ${budget} GP spent — <strong>${over ? "OVER BUDGET" : remaining + " GP remaining"}</strong>
        </div>
      </div>
      <div class="shop-tabs">
        <button class="shop-tab${tab === "weapon" ? " active" : ""}" onclick="setShopTab('weapon')">Weapons</button>
        <button class="shop-tab${tab === "armor" ? " active" : ""}" onclick="setShopTab('armor')">Armor &amp; Shield</button>
        <button class="shop-tab${tab === "gear" ? " active" : ""}" onclick="setShopTab('gear')">Gear &amp; Focuses</button>
      </div>
      <div class="shop-items">
        ${items.map(item => {
          const costGP = parseCostGP(item.cost);
          const detail = item.item_type === "weapon"
            ? `${item.damage || "—"} ${item.damage_type || ""}`.trim()
            : item.item_type === "armor" || item.item_type === "shield"
            ? (item.ac_formula || "—")
            : item.description || item.category || "";
          return `<div class="shop-item">
            <span class="shop-item-name">${item.name}</span>
            <span class="shop-item-detail">${detail}</span>
            <span class="shop-item-cost">${item.cost || "—"}</span>
            <button class="shop-add-btn${costGP > remaining ? " unaffordable" : ""}" onclick="shopAddItem('${item.name.replace(/'/g,"\\'")}')">+</button>
          </div>`;
        }).join("")}
      </div>
      ${cart.length ? `
        <div class="shop-cart">
          <div class="shop-cart-title">Cart</div>
          ${cart.map(c => `
            <div class="shop-cart-item">
              <span class="shop-cart-name">${c.name}</span>
              <span class="shop-cart-sub">${(c.qty * parseCostGP(c.cost)).toFixed(1)} GP</span>
              <div class="shop-qty">
                <button onclick="shopRemoveItem('${c.name.replace(/'/g,"\\'")}')">−</button>
                <span>${c.qty}</span>
                <button onclick="shopAddItem('${c.name.replace(/'/g,"\\'")}')">+</button>
              </div>
            </div>`).join("")}
        </div>` : `<p class="hint mt-sm">No items added yet.</p>`}
      <p class="shop-note">Only weapons and armor are in the catalog. Unspent gold will be noted on your sheet.</p>
    </div>`;
}

function renderEquipOptions(containerId, options, prefix) {
  const container = document.getElementById(containerId);
  if (!options.length) { container.innerHTML = `<p class="hint">No equipment options found.</p>`; return; }

  container.innerHTML = options.map((opt, idx) => {
    const isGold = opt.gold && !opt.items?.length;
    const label = isGold
      ? `<strong>Option ${opt.label}:</strong> ${opt.gold} GP — add to shared gold pool`
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
  updateShopVisibility();
}

function resolvePackOption(opt) {
  const items = [];
  for (const item of opt.items || []) {
    if (item.type === "gold") {
      items.push({ name: "Gold", qty: item.qty, equipped: false });
    } else if (item.type === "ref") {
      const toolName = state.currentBackground?.tool_proficiency;
      if (toolName && !toolName.toLowerCase().startsWith("choose")) {
        items.push({ name: toolName, qty: item.qty, equipped: false });
      }
    } else if (item.type === "choice") {
      const selects = document.querySelectorAll(`[id*="-choice-"]`);
      const sel = [...selects].find(s => s.id.includes(item.name.slice(0,6).replace(/\s/g,"")));
      items.push({ name: sel ? sel.value : item.name, qty: item.qty, equipped: false });
    } else {
      items.push({ name: item.name, qty: item.qty, equipped: false });
    }
  }
  return items;
}

async function saveEquipment() {
  const cls = state.currentClass;
  const bg = state.currentBackground;
  const classOptLabel = state.classEquipOption || (cls?.equipment_options?.[0]?.label ?? "A");
  const bgOptLabel = state.bgEquipOption || (bg?.equipment_options?.[0]?.label ?? "A");

  const classOpt = (cls?.equipment_options || []).find(o => o.label === classOptLabel);
  const bgOpt = (bg?.equipment_options || []).find(o => o.label === bgOptLabel);

  const resolvedItems = [];
  const totalBudget = shopGetBudget();

  if (classOpt && !(classOpt.gold && !classOpt.items?.length)) resolvedItems.push(...resolvePackOption(classOpt));
  if (bgOpt && !(bgOpt.gold && !bgOpt.items?.length)) resolvedItems.push(...resolvePackOption(bgOpt));

  if (totalBudget > 0) {
    for (const c of state.shopCart) resolvedItems.push({ name: c.name, qty: c.qty, equipped: false });
    const remaining = Math.round((totalBudget - shopSpent()) * 100) / 100;
    if (remaining > 0) resolvedItems.push({ name: "Gold", qty: remaining, equipped: false });
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
  const [classSpells, ownedSpells] = await Promise.all([
    api("GET", `/api/content/spells?class_name=${encodeURIComponent(cls.name)}`),
    api("GET", `/api/characters/${state.charId}/spells`),
  ]);
  state.allSpells = classSpells;
  state.ownedSpells = ownedSpells; // [{id, name, level, source, notes, ...}]
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

  // Species-granted spells already in this character's spell list
  const ownedIds = new Set((state.ownedSpells || []).map(s => s.id));
  const speciesSpells = (state.ownedSpells || []).filter(s => s.source === "species");

  // Filter class spell lists — remove anything the character already owns
  const allCantrips = state.allSpells.filter(s => s.level === 0);
  const speciesCantripsInClassList = allCantrips.filter(s => ownedIds.has(s.id));
  const cantrips = allCantrips.filter(s => !ownedIds.has(s.id));
  const spells1 = state.allSpells.filter(s => s.level === 1 && !ownedIds.has(s.id));

  const cantripCount = cantripCounts[cls.name] ?? 0;
  const spellCount = spellCounts[cls.name] || 2;

  // Species grants hint
  if (speciesSpells.length > 0) {
    const grantLines = speciesSpells.map(s => {
      const note = s.notes ? ` <em class="species-spell-note">(${s.notes})</em>` : "";
      return `<span class="species-spell-name">${s.name}</span>${note}`;
    });
    document.getElementById("species-spells-granted").innerHTML =
      `<strong>Your species grants:</strong> ${grantLines.join(", ")}`;
    document.getElementById("species-spells-granted").classList.remove("hidden");
  } else {
    document.getElementById("species-spells-granted").classList.add("hidden");
  }

  const hintParts = [];
  if (cantripCount > 0) hintParts.push(`Choose ${cantripCount} cantrip${cantripCount > 1 ? "s" : ""}`);
  hintParts.push(`${spellCount} level 1 spell${spellCount > 1 ? "s" : ""}`);
  document.getElementById("spells-hint").textContent = `Choose ${hintParts.join(" and ")}.`;

  const cantripSec = document.getElementById("cantrips-section");
  cantripSec.innerHTML = (cantripCount > 0 && cantrips.length)
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
  if (state.charId) {
    document.getElementById("btn-view-sheet").href = `/characters/${state.charId}/sheet`;
  }
}


function startNewCharacter() {
  Object.assign(state, {
    charId: null, step: 1, displayName: "", charName: "",
    speciesId: null, speciesLineage: null, speciesSizeChoice: null, backgroundId: null, classId: null,
    selectedRollSet: null,
    assignedStats: { str: null, dex: null, con: null, int: null, wis: null, cha: null },
    backgroundASI: {}, featuresChoices: [], selectedSkills: [], selectedLanguages: [],
    classEquipOption: null, bgEquipOption: null, resolvedItems: [],
    shopCart: [], shopTab: "weapon",
    cantripIds: [], spellIds: [], currentClass: null, currentBackground: null, currentSpecies: null,
  });
  document.getElementById("display-name").value = "";
  document.getElementById("char-name").value = "";
  showStep(1);
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  const res = await fetch("/auth/me");
  if (res.status === 401) {
    window.location.href = "/auth/login";
    return;
  }
  const user = await res.json();

  const badge = document.getElementById("user-badge");
  if (badge) {
    document.getElementById("user-name").textContent = user.name || user.email;
    badge.style.display = "flex";
  }

  const nameInput = document.getElementById("display-name");
  if (nameInput && !nameInput.value) {
    nameInput.value = user.name || "";
    state.displayName = nameInput.value;
  }

  // Resume an existing character if ?char=id is in the URL
  const charParam = new URLSearchParams(window.location.search).get("char");
  if (charParam) {
    await resumeCharacter(parseInt(charParam, 10));
  } else {
    showStep(1);
  }
}

async function resumeCharacter(charId) {
  try {
    const char = await api("GET", `/api/characters/${charId}`);
    if (!char) { showStep(1); return; }

    state.charId = char.id;
    state.displayName = char.created_by_display_name || "";
    state.charName = char.character_name || "";
    const dnInput = document.getElementById("display-name");
    const cnInput = document.getElementById("char-name");
    if (dnInput) dnInput.value = state.displayName;
    if (cnInput) cnInput.value = state.charName;

    const step = char.wizard_step || 1;

    // Pre-load content caches so the grid is ready when the panel shows
    if (step >= 2) loadSpecies();
    if (step >= 3) loadBackgrounds();
    if (step >= 4) loadClasses();

    // For stats/features/skills/equipment/spells, trigger their renderers
    if (step === 5) { showStep(5); renderStatsStep(); return; }
    if (step === 6) { showStep(6); renderFeaturesStep(); return; }
    if (step === 7) { showStep(7); renderSkillsStep(); return; }
    if (step === 8) { showStep(8); renderEquipmentStep(); return; }
    if (step === 9) { showStep(9); loadSpellsStep(); return; }

    showStep(step);
  } catch {
    showStep(1);
  }
}

boot();
