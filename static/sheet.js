/* D&D 2024 Live Character Sheet */

// ---------------------------------------------------------------------------
// Spell slot tables (PHB 2024)
// ---------------------------------------------------------------------------
const FULL_SLOTS = {
  1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
  4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
  7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
  10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
  13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
  16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
  19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
};
const HALF_SLOTS = {
  1:[0,0,0,0,0,0,0,0,0], 2:[2,0,0,0,0,0,0,0,0], 3:[3,0,0,0,0,0,0,0,0],
  4:[3,0,0,0,0,0,0,0,0], 5:[4,2,0,0,0,0,0,0,0], 6:[4,2,0,0,0,0,0,0,0],
  7:[4,3,0,0,0,0,0,0,0], 8:[4,3,0,0,0,0,0,0,0], 9:[4,3,2,0,0,0,0,0,0],
  10:[4,3,2,0,0,0,0,0,0],11:[4,3,3,0,0,0,0,0,0],12:[4,3,3,0,0,0,0,0,0],
  13:[4,3,3,1,0,0,0,0,0],14:[4,3,3,1,0,0,0,0,0],15:[4,3,3,2,0,0,0,0,0],
  16:[4,3,3,2,0,0,0,0,0],17:[4,3,3,3,1,0,0,0,0],18:[4,3,3,3,1,0,0,0,0],
  19:[4,3,3,3,2,0,0,0,0],20:[4,3,3,3,2,0,0,0,0],
};
const PACT_SLOTS = {
  1:{c:1,l:1},2:{c:2,l:1},3:{c:2,l:2},4:{c:2,l:2},5:{c:2,l:3},
  6:{c:2,l:3},7:{c:2,l:4},8:{c:2,l:4},9:{c:2,l:5},10:{c:2,l:5},
  11:{c:3,l:5},12:{c:3,l:5},13:{c:3,l:5},14:{c:3,l:5},15:{c:3,l:5},
  16:{c:3,l:5},17:{c:4,l:5},18:{c:4,l:5},19:{c:4,l:5},20:{c:4,l:5},
};

const SKILL_ABILITY = {
  "Acrobatics":"dex","Animal Handling":"wis","Arcana":"int","Athletics":"str",
  "Deception":"cha","History":"int","Insight":"wis","Intimidation":"cha",
  "Investigation":"int","Medicine":"wis","Nature":"int","Perception":"wis",
  "Performance":"cha","Persuasion":"cha","Religion":"int",
  "Sleight of Hand":"dex","Stealth":"dex","Survival":"wis",
};

const ORDINAL = ["","1st","2nd","3rd","4th","5th","6th","7th","8th","9th"];
const SPELL_AB_KEY = { "Intelligence":"int","Wisdom":"wis","Charisma":"cha" };

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
let charId, charData, isDM = false;

function mod(score) { return Math.floor((score - 10) / 2); }
function fmtMod(n) { return (n >= 0 ? "+" : "") + n; }

async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 401) { window.location.href = "/auth/login"; return null; }
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.detail || `HTTP ${res.status}`); }
  return res.json().catch(() => null);
}

function toast(msg, ms = 3000) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), ms);
}

// ---------------------------------------------------------------------------
// Slot reference (read-only)
// ---------------------------------------------------------------------------
function getSlots(char) {
  const type = char.class_spellcasting_type;
  const lvl = char.level || 1;
  if (type === "full")  return (FULL_SLOTS[lvl] || []).map((n,i) => ({level: i+1, total: n})).filter(s => s.total > 0);
  if (type === "half")  return (HALF_SLOTS[lvl] || []).map((n,i) => ({level: i+1, total: n})).filter(s => s.total > 0);
  if (type === "pact") {
    const p = PACT_SLOTS[lvl] || {c:1,l:1};
    return [{level: p.l, total: p.c, pact: true}];
  }
  return [];
}

// ---------------------------------------------------------------------------
// Glossary tooltip system
// ---------------------------------------------------------------------------
let _glossaryMap = null;          // Map<slug, {term, short_description, full_description, category}>
let _glossarySlugByName = null;   // Map<lowercase-term, slug>
let _glossRx = null;              // built once, cached

async function loadGlossary() {
  if (_glossaryMap) return;
  try {
    const list = await api("GET", "/api/content/glossary");
    if (!list) return;
    _glossaryMap = new Map(list.map(t => [t.slug, t]));
    _glossarySlugByName = new Map(list.map(t => [t.term.toLowerCase(), t.slug]));
  } catch (_) { /* glossary optional — degrade gracefully */ }
}

function _buildGlossRx() {
  if (!_glossarySlugByName) return null;
  // Sort longest first so multi-word matches take priority
  const terms = [..._glossarySlugByName.keys()].sort((a, b) => b.length - a.length);
  const escaped = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  return new RegExp('\\b(' + escaped.join('|') + ')\\b', 'gi');
}

function gloss(name, displayText) {
  if (!_glossarySlugByName) return displayText != null ? displayText : name;
  const lower = (name || "").toLowerCase();
  // Try exact match, then strip parenthetical suffix (e.g. "Versatile (1d10)" → "versatile")
  const base = lower.replace(/\s*\(.*$/, '').trim();
  const slug = _glossarySlugByName.get(lower) || _glossarySlugByName.get(base);
  if (!slug) return displayText != null ? displayText : name;
  const label = displayText != null ? displayText : name;
  return `<span class="gloss-term" data-slug="${slug}">${label}</span>`;
}

function glossifyDescription(text) {
  if (!_glossarySlugByName || !text) return text;
  if (!_glossRx) _glossRx = _buildGlossRx();
  const seen = new Set();
  return text.replace(_glossRx, (match) => {
    const slug = _glossarySlugByName.get(match.toLowerCase());
    if (!slug || seen.has(slug)) return match;
    seen.add(slug);
    return `<span class="gloss-term" data-slug="${slug}">${match}</span>`;
  });
}

function _simpleMarkdown(md) {
  return (md || "")
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

function openGlossaryModal(slug) {
  closeGlossPopover();
  const term = _glossaryMap && _glossaryMap.get(slug);
  if (!term) return;
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "gloss-modal-overlay";
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
  overlay.addEventListener("click", e => { if (e.target === overlay) closeGlossaryModal(); });
  document.body.appendChild(overlay);
}

function closeGlossaryModal() {
  const el = document.getElementById("gloss-modal-overlay");
  if (el) el.remove();
}

function closeGlossPopover() {
  const el = document.getElementById("gloss-popover");
  if (el) el.remove();
}

function _showGlossPopover(slug, anchorEl) {
  closeGlossPopover();
  const term = _glossaryMap && _glossaryMap.get(slug);
  if (!term) return;

  const pop = document.createElement("div");
  pop.className = "gloss-popover";
  pop.id = "gloss-popover";
  const hasMore = term.full_description && term.full_description !== term.short_description;
  pop.innerHTML = `<div class="gloss-popover-term">${term.term}</div>
    <div class="gloss-popover-body">${term.short_description}</div>
    ${hasMore ? `<span class="gloss-popover-more" onclick="openGlossaryModal('${slug}')">Read full rule ›</span>` : ""}`;

  document.body.appendChild(pop);

  // Position: prefer below, flip above if off-screen
  const rect = anchorEl.getBoundingClientRect();
  const popW = 300;
  let left = rect.left + window.scrollX;
  let top  = rect.bottom + window.scrollY + 6;
  if (left + popW > window.innerWidth - 8) left = window.innerWidth - popW - 8;
  if (top + pop.offsetHeight > window.innerHeight + window.scrollY - 8) {
    top = rect.top + window.scrollY - pop.offsetHeight - 6;
  }
  pop.style.left = Math.max(8, left) + "px";
  pop.style.top  = top + "px";
}

// Delegated click handler for all .gloss-term spans
document.addEventListener("click", e => {
  const term = e.target.closest(".gloss-term");
  if (term) {
    e.stopPropagation();
    const slug = term.dataset.slug;
    const existing = document.getElementById("gloss-popover");
    // Toggle: close if same slug already open
    if (existing && existing.dataset.forSlug === slug) { closeGlossPopover(); return; }
    _showGlossPopover(slug, term);
    if (document.getElementById("gloss-popover")) {
      document.getElementById("gloss-popover").dataset.forSlug = slug;
    }
    return;
  }
  // Click outside closes popover and modal
  if (!e.target.closest("#gloss-popover") && !e.target.closest(".gloss-popover-more")) {
    closeGlossPopover();
  }
});

document.addEventListener("keydown", e => {
  if (e.key === "Escape") { closeGlossPopover(); closeGlossaryModal(); }
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  const m = window.location.pathname.match(/\/characters\/(\d+)\/sheet/);
  if (!m) { document.getElementById("sheet-loading").textContent = "Invalid URL."; return; }
  charId = parseInt(m[1], 10);

  const me = await api("GET", "/auth/me");
  if (!me) return;
  isDM = me.is_admin || false;
  document.getElementById("sheet-user-name").textContent = me.name || me.email;

  try {
    [charData] = await Promise.all([
      api("GET", `/api/characters/${charId}/sheet-data`),
      loadGlossary(),
    ]);
  } catch(e) {
    document.getElementById("sheet-loading").textContent = "Could not load character: " + e.message;
    return;
  }

  document.title = charData.character_name + " — Character Sheet";
  document.getElementById("sheet-loading").classList.add("hidden");
  document.getElementById("sheet-root").classList.remove("hidden");
  render();
  setInterval(pollHp, 15000);
}

async function pollHp() {
  try {
    const r = await api("GET", `/api/characters/${charId}/hp`);
    if (!r) return;
    if (r.hp_current === charData.hp_current && r.hp_max === charData.hp_max) return;
    charData.hp_current = r.hp_current;
    charData.hp_max = r.hp_max;
    const cell = document.getElementById("hp-cell");
    if (!cell) return;
    const label = cell.querySelector(".sh-combat-label").outerHTML;
    cell.innerHTML = label + renderHpWidget(charData);
  } catch (_) { /* ignore */ }
}

// ---------------------------------------------------------------------------
// Main render
// ---------------------------------------------------------------------------
function render() {
  const c = charData;
  const prof = c.proficiency_bonus || 2;
  const attrs = c.attributes || {};
  const profSkills = new Set(c.prof_skills || []);

  const identity = [
    c.class_name ? `${c.class_name} ${c.level}` : null,
    speciesDisplayName(c.species_name, c.species_lineage),
    c.background_name,
    c.alignment,
  ].filter(Boolean).join(" · ");

  const initiative = fmtMod(c.initiative ?? mod(attrs.dex || 10));
  const initiativeTip = c.initiative_source === "alert" ? ` title="Alert: Dex + Proficiency Bonus"` : "";
  const passivePerc = 10 + mod(attrs.wis || 10) + (profSkills.has("Perception") ? prof : 0);
  const isCaster = !!c.class_spellcasting_type;

  document.getElementById("sheet-root").innerHTML = `
    <div class="sh-header">
      <div>
        <div class="sh-char-name">${c.character_name}</div>
        <div class="sh-identity">${identity}</div>
        <div class="sh-player">Player: ${c.created_by_display_name}</div>
      </div>
    </div>

    <div class="sh-combat-bar">
      <div class="sh-combat-cell" id="hp-cell">
        <div class="sh-combat-label">Hit Points</div>
        ${renderHpWidget(c)}
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Armor Class</div>
        <div class="sh-combat-big" id="sh-ac-val">${c.ac ?? "—"}</div>
        ${c.ac_source && c.ac_source !== "armor" && c.ac_source !== "unarmored"
          ? `<div class="sh-stat-badge">${c.ac_source === "unarmored_defense_barbarian" ? "Unarmored Defense" : "Unarmored Defense (Wis)"}</div>` : ""}
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Speed</div>
        <div class="sh-combat-big">${c.speed ?? "—"} ft</div>
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Initiative</div>
        <div class="sh-combat-big"${initiativeTip}>${initiative}</div>
        ${c.initiative_source === "alert" ? `<div class="sh-stat-badge sh-stat-badge--alert">Alert</div>` : ""}
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Proficiency</div>
        <div class="sh-combat-big">+${prof}</div>
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Passive Perc.</div>
        <div class="sh-combat-big">${passivePerc}</div>
      </div>
    </div>

    <div class="sh-tabs">
      <button class="sh-tab-btn active" onclick="switchSheetTab('stats',this)">Stats &amp; Attacks</button>
      <button class="sh-tab-btn" onclick="switchSheetTab('bio',this)">Biography</button>
      <button class="sh-tab-btn" onclick="switchSheetTab('equipment',this)">Equipment</button>
      ${isCaster ? `<button class="sh-tab-btn" onclick="switchSheetTab('spells',this)">Spells</button>` : ""}
    </div>

    <div id="sh-tab-stats" class="sh-tab-panel">${renderStatsTab(c, prof, attrs)}</div>
    <div id="sh-tab-bio" class="sh-tab-panel hidden">${renderBioTab(c)}</div>
    <div id="sh-tab-equipment" class="sh-tab-panel hidden">${renderEquipmentTab(c)}</div>
    ${isCaster ? `<div id="sh-tab-spells" class="sh-tab-panel hidden">${renderSpellsTab(c, prof, attrs)}</div>` : ""}
  `;

  attachBioSave();
}

// ---------------------------------------------------------------------------
// HP widget
// ---------------------------------------------------------------------------
function renderHpWidget(c) {
  const cur = c.hp_current ?? 0;
  const max = c.hp_max ?? 1;
  const pct = max > 0 ? Math.round((cur / max) * 100) : 0;
  const barColor = pct > 50 ? "#4a8c4a" : pct > 25 ? "#b8860b" : "#8b1a1a";
  const bonusBadge = c.hp_bonus_source
    ? `<div class="sh-stat-badge sh-stat-badge--trait" title="${c.hp_bonus_source}">${c.hp_bonus_source}</div>`
    : "";
  return `
    <div class="hp-bar-wrap">
      <div class="hp-bar" style="width:${pct}%;background:${barColor}"></div>
    </div>
    <div class="hp-numbers">${cur} <span class="hp-max">/ ${max}</span></div>
    ${bonusBadge}`;
}

// ---------------------------------------------------------------------------
// Tab 1: Stats & Attacks
// ---------------------------------------------------------------------------
function renderStatsTab(c, prof, attrs) {
  const profSkills = new Set(c.prof_skills || []);
  const expertSkills = new Set(c.expert_skills || []);
  const saveProfs = new Set(c.save_profs || []);

  return `
    <div class="sh-main">
      <div class="sh-col-left">
        ${renderAbilityScores(attrs)}
        ${renderSavingThrows(attrs, saveProfs, prof)}
        ${renderSkills(attrs, profSkills, expertSkills, prof, c.skill_bonuses || {})}
      </div>
      <div class="sh-col-right">
        ${renderProficiencies(c, prof, attrs)}
        ${renderAttackCards(c)}
        ${renderSneakAttackSection(c)}
        ${renderWeaponsSection(c)}
      </div>
    </div>
    ${renderFeaturesSection(c)}
  `;
}

// ---------------------------------------------------------------------------
// Ability Scores
// ---------------------------------------------------------------------------
function renderAbilityScores(attrs) {
  const STATS = [
    {key:"str",label:"Strength"}, {key:"dex",label:"Dexterity"},
    {key:"con",label:"Constitution"}, {key:"int",label:"Intelligence"},
    {key:"wis",label:"Wisdom"}, {key:"cha",label:"Charisma"},
  ];
  const cards = STATS.map(s => {
    const score = attrs[s.key] || 10;
    const m = mod(score);
    return `<div class="ability-card">
      <div class="ability-label">${s.label.slice(0,3).toUpperCase()}</div>
      <div class="ability-score">${score}</div>
      <div class="ability-mod">${fmtMod(m)}</div>
    </div>`;
  }).join("");
  return `<div class="sh-section"><h4 class="sh-section-title">Ability Scores</h4><div class="ability-grid">${cards}</div></div>`;
}

// ---------------------------------------------------------------------------
// Saving Throws
// ---------------------------------------------------------------------------
function renderSavingThrows(attrs, saveProfs, prof) {
  const STATS = ["Strength","Dexterity","Constitution","Intelligence","Wisdom","Charisma"];
  const KEY = {Strength:"str",Dexterity:"dex",Constitution:"con",Intelligence:"int",Wisdom:"wis",Charisma:"cha"};
  const rows = STATS.map(s => {
    const base = mod(attrs[KEY[s]] || 10);
    const isProficient = saveProfs.has(s);
    const total = base + (isProficient ? prof : 0);
    return `<div class="save-row">
      <span class="prof-dot ${isProficient ? "prof" : ""}"></span>
      <span class="save-name">${s}</span>
      <span class="save-val">${fmtMod(total)}</span>
    </div>`;
  }).join("");
  return `<div class="sh-section"><h4 class="sh-section-title">Saving Throws</h4>${rows}</div>`;
}

// ---------------------------------------------------------------------------
// Skills
// ---------------------------------------------------------------------------
function renderSkills(attrs, profSkills, expertSkills, prof, skillBonuses = {}) {
  const rows = Object.entries(SKILL_ABILITY).sort(([a],[b]) => a.localeCompare(b)).map(([skill, ab]) => {
    const base = mod(attrs[ab] || 10);
    const isProf = profSkills.has(skill);
    const isExpert = expertSkills.has(skill);
    const extra = skillBonuses[skill] || 0;
    const bonus = base + (isExpert ? prof * 2 : isProf ? prof : 0) + extra;
    const dot = isExpert ? "expert" : isProf ? "prof" : "";
    const extraTag = extra ? ` <span class="skill-bonus-tag" title="Thaumaturge: +Wis">+${extra}</span>` : "";
    return `<div class="save-row">
      <span class="prof-dot ${dot}" title="${isExpert ? "Expertise" : isProf ? "Proficient" : ""}"></span>
      <span class="save-name">${gloss(skill)} <span class="skill-ab">(${ab.toUpperCase()})</span>${extraTag}</span>
      <span class="save-val">${fmtMod(bonus)}</span>
    </div>`;
  }).join("");
  return `<div class="sh-section"><h4 class="sh-section-title">Skills</h4>${rows}</div>`;
}

// ---------------------------------------------------------------------------
// Proficiencies + Spellcasting info
// ---------------------------------------------------------------------------
function renderProficiencies(c, prof, attrs) {
  const languages = (c.language_proficiencies || []).join(", ") || "—";
  const tools = (c.tool_proficiencies || []).join(", ") || "—";
  const masteries = (c.weapon_mastery_unlocks || []).length
    ? (c.weapon_mastery_unlocks || []).map(m => gloss(m)).join(", ")
    : "—";

  let spellSection = "";
  if (c.class_spellcasting_type) {
    const ab = c.class_spellcasting_ability || "";
    const abKey = SPELL_AB_KEY[ab] || "int";
    const abMod = mod((attrs || {})[abKey] || 10);
    const dc = 8 + prof + abMod;
    const atk = fmtMod(prof + abMod);
    spellSection = `<div class="sh-section">
      <h4 class="sh-section-title">Spellcasting</h4>
      <p class="sh-prose">Ability: <strong>${ab || "—"}</strong></p>
      <p class="sh-prose">Save DC: <strong>${dc}</strong></p>
      <p class="sh-prose">Attack: <strong>${atk}</strong></p>
    </div>`;
  }

  return `
    <div class="sh-section">
      <h4 class="sh-section-title">Languages</h4>
      <p class="sh-prose">${languages}</p>
    </div>
    <div class="sh-section">
      <h4 class="sh-section-title">Tool Proficiencies</h4>
      <p class="sh-prose">${tools}</p>
    </div>
    ${c.weapon_mastery_unlocks?.length ? `<div class="sh-section">
      <h4 class="sh-section-title">Weapon Masteries</h4>
      <p class="sh-prose">${masteries}</p>
    </div>` : ""}
    ${spellSection}
  `;
}

// ---------------------------------------------------------------------------
// Attack cards
// ---------------------------------------------------------------------------
function renderAttackCards(c) {
  const attacks = c.attacks || [];
  if (!attacks.length) return "";

  const cards = attacks.map(a => {
    const propTags = (a.properties || []).slice(0, 4)
      .map(p => `<span class="attack-prop">${gloss(p)}</span>`).join("");
    const masteryTag = a.mastery_property
      ? `<span class="attack-mastery">${gloss(a.mastery_property)}</span>` : "";
    const unarmedClass = a.is_unarmed ? " attack-card--unarmed" : "";
    return `<div class="attack-card${unarmedClass}">
      <div class="attack-name">${a.name}</div>
      <div class="attack-stats">
        <div class="attack-stat"><span class="attack-label">ATK</span>${fmtMod(a.attack_bonus)}</div>
        <div class="attack-stat"><span class="attack-label">DMG</span>${a.damage}</div>
      </div>
      ${(propTags || masteryTag) ? `<div class="attack-props">${propTags}${masteryTag}</div>` : ""}
    </div>`;
  }).join("");

  return `<div class="sh-section">
    <h4 class="sh-section-title">Attacks</h4>
    <div class="attack-cards">${cards}</div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Sneak Attack (Rogue only)
// ---------------------------------------------------------------------------
function renderSneakAttackSection(c) {
  if ((c.class_name || "").toLowerCase() !== "rogue") return "";

  const level = c.level || 1;
  const dexMod = mod(c.attributes?.dex || 10);
  const prof = c.proficiency_bonus || 2;
  const dc = 8 + dexMod + prof;
  const sneakDice = Math.ceil(level / 2);

  const CUNNING_STRIKES = [
    { minLevel: 5,  cost: "1d6", name: "Poison",    desc: "Con save or Poisoned until the start of your next turn." },
    { minLevel: 5,  cost: "1d6", name: "Trip",      desc: "Dex save or Prone (Large or smaller targets only)." },
    { minLevel: 5,  cost: "1d6", name: "Withdraw",  desc: "Move up to half your Speed without provoking Opportunity Attacks." },
    { minLevel: 14, cost: "2d6", name: "Daze",      desc: "Con save or Incapacitated until the start of your next turn." },
    { minLevel: 14, cost: "3d6", name: "Obscure",   desc: "Dex save or Blinded until the start of your next turn." },
    { minLevel: 14, cost: "6d6", name: "Knock Out", desc: "Con save or Unconscious for 1 minute (ends if target takes damage or is shaken awake)." },
  ];

  const available = CUNNING_STRIKES.filter(o => level >= o.minLevel);

  const strikeRows = available.map(o => `
    <div class="sh-sneak-option">
      <span class="sh-sneak-cost">${o.cost}</span>
      <div class="sh-sneak-option-body">
        <span class="sh-sneak-name">${o.name}</span>
        <span class="sh-sneak-desc">${o.desc}</span>
      </div>
    </div>`).join("");

  const cunningBlock = available.length ? `
    <div class="sh-sneak-subtitle">Cunning Strike — Save DC ${dc}
      ${level >= 11 ? `<span class="sh-sneak-improved">two effects at once</span>` : ""}
    </div>
    <div class="sh-sneak-options">${strikeRows}</div>
  ` : `<p class="sh-sneak-unlocks">Cunning Strike unlocks at level 5.</p>`;

  return `<div class="sh-section">
    <h4 class="sh-section-title">Sneak Attack</h4>
    <div class="sh-sneak-damage">${sneakDice}d6 <span class="sh-sneak-damage-label">extra damage</span></div>
    ${cunningBlock}
  </div>`;
}

// ---------------------------------------------------------------------------
// Weapon Proficiencies & Masteries
// ---------------------------------------------------------------------------
function renderWeaponsSection(c) {
  const weapons = c.weapons_display || [];
  const categories = c.weapon_prof_categories || [];
  if (!weapons.length && !categories.length) return "";

  const catLine = categories.length
    ? `<p class="sh-weapons-cats">${categories.join(" · ")}</p>`
    : "";

  const rows = weapons.map(w => {
    const masteryTag = w.mastery
      ? `<span class="sh-weapon-mastery">${gloss(w.mastery)}</span>`
      : "";
    const profBadge = w.proficient
      ? `<span class="sh-weapon-prof">Prof</span>`
      : `<span class="sh-weapon-noprof">—</span>`;
    return `<div class="sh-weapon-row">
      <span class="sh-weapon-name">${w.name}</span>
      ${profBadge}
      ${masteryTag}
    </div>`;
  }).join("");

  return `<div class="sh-section">
    <h4 class="sh-section-title">Weapon Proficiencies &amp; Masteries</h4>
    ${catLine}
    <div class="sh-weapon-grid">${rows}</div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Features & Traits (below the two-column layout)
// ---------------------------------------------------------------------------
function renderFeaturesSection(c) {
  const renderEntry = (name, desc, badge) => `
    <div class="feature-card">
      <div class="feature-card-header">
        <span class="feature-name">${name}</span>
        ${badge ? `<span class="feature-badge">${badge}</span>` : ""}
      </div>
      ${desc ? `<div class="feature-desc">${glossifyDescription(desc)}</div>` : ""}
    </div>`;

  const classFeatures = (c.class_features || []).map(f =>
    renderEntry(f.name, f.description, `${c.class_name} Lv ${f.level}`)).join("");
  const speciesTraits = (c.species_traits || []).map(t =>
    renderEntry(t.name, t.description, speciesDisplayName(c.species_name, c.species_lineage))).join("");
  const feats = (c.feats || []).map(f =>
    renderEntry(f.name, f.description, "Feat")).join("");

  if (!classFeatures && !speciesTraits && !feats) return "";

  return `<div class="sh-features-section">
    <div class="sh-features-inner">
      ${classFeatures ? `<h4 class="sh-section-title">Class Features</h4>${classFeatures}` : ""}
      ${speciesTraits ? `<h4 class="sh-section-title ${classFeatures ? "mt-md" : ""}">Species Traits</h4>${speciesTraits}` : ""}
      ${feats ? `<h4 class="sh-section-title mt-md">Feats</h4>${feats}` : ""}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Species height/weight ranges — height in total inches, weight in lbs
// ---------------------------------------------------------------------------
const SPECIES_RANGES = {
  "halfling":        { hMin: 24,  hMax: 36,  wMin: 30,  wMax: 50  },
  "gnome":           { hMin: 36,  hMax: 48,  wMin: 40,  wMax: 80  },
  "dwarf":           { hMin: 48,  hMax: 60,  wMin: 130, wMax: 200 },
  "elf":             { hMin: 60,  hMax: 72,  wMin: 100, wMax: 160 },
  "dragonborn":      { hMin: 60,  hMax: 84,  wMin: 200, wMax: 400 },
  "orc":             { hMin: 72,  hMax: 84,  wMin: 180, wMax: 330 },
  "goliath":         { hMin: 84,  hMax: 96,  wMin: 280, wMax: 450 },
  "human_medium":    { hMin: 48,  hMax: 84,  wMin: 100, wMax: 280 },
  "tiefling_medium": { hMin: 48,  hMax: 84,  wMin: 100, wMax: 250 },
  "aasimar_medium":  { hMin: 48,  hMax: 84,  wMin: 100, wMax: 260 },
  "human_small":     { hMin: 24,  hMax: 48,  wMin: 30,  wMax: 100 },
  "tiefling_small":  { hMin: 36,  hMax: 48,  wMin: 60,  wMax: 120 },
  "aasimar_small":   { hMin: 24,  hMax: 48,  wMin: 30,  wMax: 100 },
};
const SIZE_CHOICE_SPECIES = ["human", "tiefling", "aasimar"];
const DEFAULT_RANGE = { hMin: 24, hMax: 108, wMin: 20, wMax: 500 };

function getSpeciesRange(speciesName, speciesSize) {
  const name = (speciesName || "").toLowerCase();
  const small = (speciesSize || "Medium").toLowerCase() === "small";
  const key = SIZE_CHOICE_SPECIES.includes(name)
    ? `${name}_${small ? "small" : "medium"}`
    : name;
  return SPECIES_RANGES[key] || DEFAULT_RANGE;
}

function parseHeight(val) {
  if (!val) return { ft: null, in: 0 };
  const m = val.match(/(\d+)[''′]?\s*(\d*)/);
  if (m && m[1]) return { ft: parseInt(m[1]), in: m[2] ? parseInt(m[2]) : 0 };
  return { ft: null, in: 0 };
}

function parseWeight(val) {
  if (!val) return null;
  const m = val.match(/(\d+)/);
  return m ? parseInt(m[1]) : null;
}

// ---------------------------------------------------------------------------
// Tab 2: Biography
// ---------------------------------------------------------------------------
function buildHeightOptions(range, currentVal) {
  const parsed = parseHeight(currentVal);
  const currentTotal = parsed.ft !== null ? parsed.ft * 12 + parsed.in : -1;
  let opts = `<option value="">— select —</option>`;
  for (let total = range.hMin; total <= range.hMax; total++) {
    const ft  = Math.floor(total / 12);
    const inc = total % 12;
    const val = `${ft}'${inc}"`;
    const label = inc === 0 ? `${ft}' 0"` : `${ft}' ${inc}"`;
    const sel = total === currentTotal ? " selected" : "";
    opts += `<option value="${val}"${sel}>${label}</option>`;
  }
  return opts;
}

const SPECIES_AGE = {
  "Human":      { min: 16, max:  80, ya: 30, ad: 45, oa: 65 },
  "Elf":        { min: 50, max:1000, ya:200, ad:450, oa:600 },
  "Dwarf":      { min: 30, max: 350, ya:100, ad:200, oa:280 },
  "Gnome":      { min: 25, max: 500, ya: 80, ad:250, oa:350 },
  "Halfling":   { min: 20, max: 150, ya: 35, ad: 85, oa:120 },
  "Dragonborn": { min: 15, max: 200, ya: 25, ad: 50, oa: 99 },
  "Orc":        { min: 14, max:  60, ya: 20, ad: 35, oa: 50 },
  "Tiefling":   { min: 16, max: 120, ya: 30, ad: 45, oa: 65 },
  "Aasimar":    { min: 16, max: 120, ya: 30, ad: 45, oa: 65 },
  "Goliath":    { min: 15, max: 150, ya: 30, ad: 70, oa:100 },
};
const SPECIES_AGE_DEFAULT = { min: 1, max: 9999, ya: 25, ad: 50, oa: 75 };

function getSpeciesAge(speciesName) {
  return SPECIES_AGE[speciesName] || SPECIES_AGE_DEFAULT;
}

function ageLabel(age, speciesName) {
  if (!age || age < 1) return "";
  const s = getSpeciesAge(speciesName);
  if (age <= s.ya) return " (Young Adult)";
  if (age <= s.ad) return " (Adult)";
  if (age <= s.oa) return " (Older Adult)";
  return " (Elder)";
}

function speciesDisplayName(speciesName, speciesLineage) {
  if (speciesName === "Dragonborn" && speciesLineage) return `${speciesLineage} Dragonborn`;
  return speciesLineage || speciesName || "";
}

function renderBioTab(c) {
  const sizeHint = c.species_size ? ` <span class="bio-hint">(${c.species_size})</span>` : "";
  const range    = getSpeciesRange(c.species_name, c.species_size);
  const parsedW  = parseWeight(c.weight);
  const locked   = c.physical_locked;

  if (locked) {
    // Read-only physical details — same style as Alignment/Background
    const ageDisplay    = c.age ? `${c.age}${ageLabel(c.age, c.species_name)}` : "—";
    const heightDisplay = c.height || "—";
    const weightDisplay = c.weight ? `${c.weight} lbs` : "—";
    const deityDisplay  = c.deity  || "None";

    return `<div class="bio-grid">
    <div class="bio-details-col">
      <div class="sh-section">
        <h4 class="sh-section-title">Identity</h4>
        <div class="bio-identity-grid">
          <div class="bio-identity-col">
            <div class="bio-field-row">
              <label class="bio-field-label">Alignment</label>
              <span class="bio-field-value">${c.alignment || "—"}</span>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Background</label>
              <span class="bio-field-value">${c.background_name || "—"}</span>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Deity / Patron</label>
              <span class="bio-field-value">${deityDisplay}</span>
            </div>
          </div>
          <div class="bio-identity-col">
            <div class="bio-field-row">
              <label class="bio-field-label">Age</label>
              <span class="bio-field-value">${ageDisplay}</span>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Height${sizeHint}</label>
              <span class="bio-field-value">${heightDisplay}</span>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Weight</label>
              <span class="bio-field-value">${weightDisplay}</span>
            </div>
          </div>
        </div>
      </div>

      ${c.bio ? `<div class="sh-section">
        <h4 class="sh-section-title">Backstory</h4>
        <div class="sh-prose bio-text">${c.bio.replace(/\n/g,"<br>")}</div>
      </div>` : ""}
    </div>

    <div class="bio-journal-col">
      <div class="sh-section" style="height:100%">
        <h4 class="sh-section-title">Journal <span class="bio-hint">(your notes)</span></h4>
        <textarea id="bio-journal" class="bio-journal" placeholder="Write anything here — session notes, character thoughts, reminders…">${c.journal || ""}</textarea>
        <div class="bio-save-row">
          <span id="bio-save-status" class="bio-save-status"></span>
          <button class="btn-secondary btn-sm" onclick="saveJournal()">Save Journal</button>
        </div>
      </div>
    </div>
  </div>`;
  }

  // Editable — dropdown height, counter weight, text deity
  const heightOpts = buildHeightOptions(range, c.height);
  const initW = parsedW !== null ? parsedW : range.wMin;

  return `<div class="bio-grid">
    <div class="bio-details-col">
      <div class="sh-section">
        <h4 class="sh-section-title">Identity</h4>
        <div class="bio-identity-grid">
          <div class="bio-identity-col">
            <div class="bio-field-row">
              <label class="bio-field-label">Alignment</label>
              <span class="bio-field-value">${c.alignment || "—"}</span>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Background</label>
              <span class="bio-field-value">${c.background_name || "—"}</span>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Deity / Patron</label>
              <input class="bio-input" id="bio-deity" type="text" placeholder="None" value="${c.deity || ""}">
            </div>
          </div>
          <div class="bio-identity-col">
            <div class="bio-field-row">
              <label class="bio-field-label">Age</label>
              <div class="bio-counter">
                <input id="bio-age-val" class="bio-counter-input" type="number"
                       min="${getSpeciesAge(c.species_name).min}" max="${getSpeciesAge(c.species_name).max}" step="1" value="${c.age || ""}">
                <span id="bio-age-label" class="bio-range-hint">${ageLabel(c.age, c.species_name)}</span>
              </div>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Height${sizeHint}</label>
              <select id="bio-height-sel" class="bio-select">
                ${heightOpts}
              </select>
            </div>
            <div class="bio-field-row">
              <label class="bio-field-label">Weight</label>
              <div class="bio-counter">
                <button class="bio-counter-btn" onclick="adjustWeight(-1)" type="button">−</button>
                <input id="bio-weight-val" class="bio-counter-input" type="number"
                       min="${range.wMin}" max="${range.wMax}" step="1" value="${initW}">
                <button class="bio-counter-btn" onclick="adjustWeight(1)" type="button">+</button>
                <span class="bio-unit">lbs</span>
                <span class="bio-range-hint">${range.wMin}–${range.wMax}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="bio-lock-row">
          <button class="btn-gold bio-lock-btn" onclick="saveAndLockPhysical()" type="button">
            Save &amp; Lock Physical Details
          </button>
          <span class="bio-lock-hint">Once saved, only the DM can edit age, height, weight &amp; deity.</span>
        </div>
      </div>

      ${c.bio ? `<div class="sh-section">
        <h4 class="sh-section-title">Backstory</h4>
        <div class="sh-prose bio-text">${c.bio.replace(/\n/g,"<br>")}</div>
      </div>` : ""}
    </div>

    <div class="bio-journal-col">
      <div class="sh-section" style="height:100%">
        <h4 class="sh-section-title">Journal <span class="bio-hint">(your notes)</span></h4>
        <textarea id="bio-journal" class="bio-journal" placeholder="Write anything here — session notes, character thoughts, reminders…" data-field="journal">${c.journal || ""}</textarea>
        <div class="bio-save-row">
          <span id="bio-save-status" class="bio-save-status"></span>
          <button class="btn-secondary btn-sm" onclick="saveJournal()">Save Journal</button>
        </div>
      </div>
    </div>
  </div>`;
}

let _journalTimer = null;
function attachBioSave() {
  // Age input — update label live, save on blur
  const ageInput = document.getElementById("bio-age-val");
  if (ageInput) {
    ageInput.addEventListener("input", () => {
      const lbl = document.getElementById("bio-age-label");
      if (lbl) lbl.textContent = ageLabel(parseInt(ageInput.value) || 0, charData.species_name);
    });
    ageInput.addEventListener("blur", async () => {
      const sa = getSpeciesAge(charData.species_name);
      let val = parseInt(ageInput.value) || null;
      if (val !== null) {
        val = Math.max(sa.min, Math.min(sa.max, val));
        ageInput.value = val;
      }
      try {
        await api("PATCH", `/api/characters/${charId}/bio`, { age: val });
        charData.age = val;
      } catch(e) { toast("⚠ Save failed: " + e.message, 4000); }
    });
  }

  // Height dropdown — save on change
  const heightSel = document.getElementById("bio-height-sel");
  if (heightSel) {
    heightSel.addEventListener("change", async () => {
      const val = heightSel.value;
      if (!val) return;
      try {
        await api("PATCH", `/api/characters/${charId}/bio`, { height: val });
        charData.height = val;
      } catch(e) { toast("⚠ Save failed: " + e.message, 4000); }
    });
  }

  // Weight counter input — save on blur
  const weightInput = document.getElementById("bio-weight-val");
  if (weightInput) {
    weightInput.addEventListener("blur", async () => {
      const range = getSpeciesRange(charData.species_name, charData.species_size);
      let lbs = parseInt(weightInput.value) || range.wMin;
      lbs = Math.max(range.wMin, Math.min(range.wMax, lbs));
      weightInput.value = lbs;
      try {
        await api("PATCH", `/api/characters/${charId}/bio`, { weight: String(lbs) });
        charData.weight = String(lbs);
      } catch(e) { toast("⚠ Save failed: " + e.message, 4000); }
    });
  }

  // Deity — save on blur
  const deity = document.getElementById("bio-deity");
  if (deity) {
    deity.addEventListener("blur", async () => {
      const value = deity.value.trim();
      try {
        await api("PATCH", `/api/characters/${charId}/bio`, { deity: value });
        charData.deity = value;
      } catch(e) { toast("⚠ Save failed: " + e.message, 4000); }
    });
  }

  // Journal — autosave on keystroke
  const journal = document.getElementById("bio-journal");
  if (journal) {
    journal.addEventListener("input", () => {
      clearTimeout(_journalTimer);
      document.getElementById("bio-save-status").textContent = "Unsaved…";
      _journalTimer = setTimeout(saveJournal, 2000);
    });
  }
}

function adjustWeight(delta) {
  const el = document.getElementById("bio-weight-val");
  if (!el) return;
  const range = getSpeciesRange(charData.species_name, charData.species_size);
  let val = (parseInt(el.value) || range.wMin) + delta;
  val = Math.max(range.wMin, Math.min(range.wMax, val));
  el.value = val;
  el.dispatchEvent(new Event("blur"));
}

async function saveAndLockPhysical() {
  const ageEl      = document.getElementById("bio-age-val");
  const heightSel  = document.getElementById("bio-height-sel");
  const weightEl   = document.getElementById("bio-weight-val");
  const deityEl    = document.getElementById("bio-deity");

  if (!heightSel?.value) { toast("Please select a height before locking.", 3000); return; }
  if (!weightEl?.value)  { toast("Please enter a weight before locking.", 3000); return; }

  const age    = ageEl?.value ? parseInt(ageEl.value) : null;
  const height = heightSel.value;
  const weight = String(parseInt(weightEl.value) || 0);
  const deity  = deityEl?.value.trim() || "";

  try {
    await api("PATCH", `/api/characters/${charId}/bio`, { age, height, weight, deity });
    await api("POST", `/api/characters/${charId}/bio/lock`);
    charData.age    = age;
    charData.height = height;
    charData.weight = weight;
    charData.deity  = deity;
    charData.physical_locked = true;
    // Re-render bio tab in locked state
    document.getElementById("sh-tab-bio").innerHTML = renderBioTab(charData);
    attachBioSave();
    toast("Physical details saved and locked.");
  } catch(e) { toast("⚠ " + e.message, 4000); }
}

async function saveJournal() {
  const el = document.getElementById("bio-journal");
  if (!el) return;
  const status = document.getElementById("bio-save-status");
  try {
    await api("PATCH", `/api/characters/${charId}/bio`, { journal: el.value });
    charData.journal = el.value;
    status.textContent = "Saved";
    setTimeout(() => { if (status) status.textContent = ""; }, 2000);
  } catch(e) { toast("⚠ Could not save journal: " + e.message, 4000); }
}

// ---------------------------------------------------------------------------
// Tab 3: Equipment
// ---------------------------------------------------------------------------
function renderEquipmentTab(c) {
  const items = (c.equipment || []).filter(e => e.name?.toLowerCase() !== "gold");
  const weapons = items.filter(e => e.item_type === "weapon");
  const armor   = items.filter(e => e.item_type === "armor" || e.item_type === "shield");
  const gear    = items.filter(e => !["weapon","armor","shield"].includes(e.item_type));

  const delBtn = (e) => isDM
    ? `<td class="equip-del-cell"><button class="equip-del-btn" onclick="removeEquipment(${e.entry_id},'${e.name.replace(/'/g,"\\'")}',event)" title="Remove item">✕</button></td>`
    : "";

  const renderRow = (e) => {
    const propSpans = (e.properties || []).map(p => gloss(p)).join(", ");
    const detail = [
      e.damage ? `${e.damage}${e.damage_type ? " " + e.damage_type : ""}` : null,
      e.ac_formula ? `AC ${e.ac_formula}` : null,
      propSpans || null,
    ].filter(Boolean).join(" · ");
    return `<tr>
      <td>${e.quantity > 1 ? `<span class="equip-qty">${e.quantity}×</span> ` : ""}<strong>${e.name}</strong></td>
      <td class="text-muted">${e.category || e.item_type || ""}</td>
      <td class="text-muted">${detail}</td>
      ${delBtn(e)}
    </tr>`;
  };

  const renderArmorRow = (e) => {
    const detail = [
      e.ac_formula ? `AC ${e.ac_formula}` : null,
      e.item_type === "shield" ? "+2 AC" : null,
    ].filter(Boolean).join(" · ");
    const equipToggle = `<button class="equip-toggle-btn${e.equipped ? " is-equipped" : ""}"
      onclick="toggleEquipped(${e.entry_id},${!e.equipped},event)">
      ${e.equipped ? "✓ Equipped" : "Equip"}
    </button>`;
    return `<tr>
      <td><strong>${e.name}</strong></td>
      <td class="text-muted">${e.category || (e.item_type === "shield" ? "Shield" : "Armor")}</td>
      <td class="text-muted">${detail}</td>
      <td>${equipToggle}</td>
      ${delBtn(e)}
    </tr>`;
  };

  const renderSection = (title, rows, renderer = renderRow) => rows.length ? `
    <h4 class="sh-section-title ${title !== "Weapons" ? "mt-md" : ""}">${title}</h4>
    <table class="data-table sh-equip-table"><tbody>${rows.map(renderer).join("")}</tbody></table>` : "";

  const cur = c.currency || {pp:0,gp:0,sp:0,cp:0};
  const currencyHtml = `
    <div class="sh-section mt-md">
      <h4 class="sh-section-title">Currency</h4>
      <div class="currency-row">
        <div class="currency-coin currency-pp"><span class="currency-val">${cur.pp ?? 0}</span><span class="currency-label">PP</span></div>
        <div class="currency-coin currency-gp"><span class="currency-val">${cur.gp ?? 0}</span><span class="currency-label">GP</span></div>
        <div class="currency-coin currency-sp"><span class="currency-val">${cur.sp ?? 0}</span><span class="currency-label">SP</span></div>
        <div class="currency-coin currency-cp"><span class="currency-val">${cur.cp ?? 0}</span><span class="currency-label">CP</span></div>
      </div>
    </div>`;

  const dmBar = isDM ? `<div class="equip-dm-bar">
    <button class="equip-add-btn" onclick="openAddEquipModal()">+ Add Item</button>
  </div>` : "";

  if (!items.length) return `${dmBar}<p class="hint">No equipment recorded.</p>${currencyHtml}`;

  return `${dmBar}<div class="sh-section">
    ${renderSection("Weapons", weapons)}
    ${renderSection("Armor & Shields", armor, renderArmorRow)}
    ${renderSection("Gear", gear)}
  </div>${currencyHtml}`;
}

// ---------------------------------------------------------------------------
// Equipment management (DM only)
// ---------------------------------------------------------------------------
let _equipCache = null;

async function toggleEquipped(entryId, equip, evt) {
  evt.stopPropagation();
  try {
    const r = await api("PATCH", `/api/characters/${charId}/equipment/${entryId}/equip`, { equipped: equip });
    if (!r) return;
    // If equipping armor, auto-clear old armor in local state
    charData.equipment.forEach(e => {
      if (e.entry_id === entryId) {
        e.equipped = r.equipped;
      } else if (equip && e.item_type === "armor") {
        e.equipped = false;
      }
    });
    charData.ac = r.ac;
    const acEl = document.getElementById("sh-ac-val");
    if (acEl) acEl.textContent = r.ac;
    document.getElementById("sh-tab-equipment").innerHTML = renderEquipmentTab(charData);
  } catch(e) { toast("Error: " + e.message); }
}

async function removeEquipment(entryId, name, evt) {
  evt.stopPropagation();
  try {
    await api("DELETE", `/api/characters/${charId}/equipment/${entryId}`);
    charData.equipment = charData.equipment.filter(e => e.entry_id !== entryId);
    document.getElementById("sh-tab-equipment").innerHTML = renderEquipmentTab(charData);
    toast(`Removed: ${name}`);
  } catch(e) { toast("Error: " + e.message); }
}

async function openAddEquipModal() {
  if (!_equipCache) {
    try {
      _equipCache = await api("GET", "/api/content/equipment");
    } catch(e) { toast("Could not load equipment list"); return; }
  }

  const overlay = document.createElement("div");
  overlay.id = "add-equip-overlay";
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal-box add-equip-modal">
      <div class="modal-header">
        <h3>Add Item to Inventory</h3>
        <button class="modal-close-btn" onclick="closeAddEquipModal()">✕</button>
      </div>
      <div class="add-equip-tabs">
        <button class="add-equip-tab active" onclick="switchAddTab('db',this)">From Database</button>
        <button class="add-equip-tab" onclick="switchAddTab('custom',this)">Custom Item</button>
      </div>
      <div class="modal-body">
        <div id="add-equip-db">
          <input type="text" id="equip-search" class="equip-search-input" placeholder="Search items…" oninput="filterEquipList(this.value)">
          <div id="equip-list" class="equip-pick-list"></div>
          <div class="equip-qty-row">
            <label>Qty:</label>
            <input type="number" id="equip-db-qty" class="equip-qty-input" value="1" min="1">
          </div>
        </div>
        <div id="add-equip-custom" class="hidden">
          <input type="text" id="equip-custom-name" class="equip-search-input" placeholder="Item name">
          <div class="equip-qty-row">
            <label>Type:</label>
            <select id="equip-custom-type" class="equip-type-select">
              <option value="">— none —</option>
              <option value="weapon">Weapon</option>
              <option value="armor">Armor</option>
              <option value="shield">Shield</option>
              <option value="gear">Gear</option>
              <option value="tool">Tool</option>
              <option value="focus">Focus</option>
            </select>
          </div>
          <div class="equip-qty-row">
            <label>Qty:</label>
            <input type="number" id="equip-custom-qty" class="equip-qty-input" value="1" min="1">
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="sr-btn-cancel" onclick="closeAddEquipModal()">Cancel</button>
        <button class="sr-btn-done" onclick="confirmAddEquip()">Add to Inventory</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // Populate list
  _selectedEquipId = null;
  filterEquipList("");
}

let _selectedEquipId = null;
let _addEquipTab = "db";

function switchAddTab(tab, btn) {
  _addEquipTab = tab;
  document.querySelectorAll(".add-equip-tab").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("add-equip-db").classList.toggle("hidden", tab !== "db");
  document.getElementById("add-equip-custom").classList.toggle("hidden", tab !== "custom");
}

function filterEquipList(query) {
  const q = query.toLowerCase();
  const list = document.getElementById("equip-list");
  if (!list) return;
  const filtered = (_equipCache || []).filter(e =>
    !q || e.name.toLowerCase().includes(q)
  ).slice(0, 60);
  list.innerHTML = filtered.map(e => `
    <div class="equip-pick-row${_selectedEquipId === e.id ? " selected" : ""}"
      onclick="selectEquipItem(${e.id}, this)">
      <span class="equip-pick-name">${e.name}</span>
      <span class="equip-pick-type">${e.category || e.item_type || ""}</span>
    </div>`).join("") || `<p class="hint">No items match.</p>`;
}

function selectEquipItem(id, el) {
  _selectedEquipId = id;
  document.querySelectorAll(".equip-pick-row").forEach(r => r.classList.remove("selected"));
  el.classList.add("selected");
}

async function confirmAddEquip() {
  let body;
  if (_addEquipTab === "db") {
    if (!_selectedEquipId) { toast("Select an item first"); return; }
    const qty = parseInt(document.getElementById("equip-db-qty").value, 10) || 1;
    body = { equipment_id: _selectedEquipId, quantity: qty };
  } else {
    const name = (document.getElementById("equip-custom-name").value || "").trim();
    if (!name) { toast("Enter an item name"); return; }
    const qty = parseInt(document.getElementById("equip-custom-qty").value, 10) || 1;
    const type = document.getElementById("equip-custom-type").value || null;
    body = { custom_name: name, quantity: qty, item_type: type };
  }

  try {
    const entry = await api("POST", `/api/characters/${charId}/equipment`, body);
    if (!entry) return;
    charData.equipment.push(entry);
    closeAddEquipModal();
    document.getElementById("sh-tab-equipment").innerHTML = renderEquipmentTab(charData);
    toast(`Added: ${entry.name}`);
  } catch(e) { toast("Error: " + e.message); }
}

function closeAddEquipModal() {
  const overlay = document.getElementById("add-equip-overlay");
  if (overlay) overlay.remove();
  _selectedEquipId = null;
  _addEquipTab = "db";
}

// ---------------------------------------------------------------------------
// Tab 4: Spells
// ---------------------------------------------------------------------------
function renderSpellsTab(c, prof, attrs) {
  const ab = c.class_spellcasting_ability || "";
  const abKey = SPELL_AB_KEY[ab] || "int";
  const abMod = mod((attrs || {})[abKey] || 10);
  const dc = 8 + prof + abMod;
  const atk = fmtMod(prof + abMod);

  const className = (c.class_name || "").toLowerCase();
  const isWizard = className === "wizard";
  const isPact = c.class_spellcasting_type === "pact";
  const isPrepCaster = c.is_prep_caster || false;

  const slots = getSlots(c);
  const slotRef = slots.length ? `
    <div class="slot-ref-bar">
      <span class="slot-ref-title">${isPact ? "Pact Magic" : "Spell Slots"}</span>
      ${slots.map(s => `<div class="slot-ref-group">
        <div class="slot-ref-label">${s.pact ? "Pact" : ORDINAL[s.level]}</div>
        <div class="slot-ref-count">${s.total}</div>
      </div>`).join("")}
      ${isPact ? `<div class="slot-ref-note">Recover on short rest</div>` : ""}
    </div>` : "";

  const allSpells = c.spells || [];
  const arcanumSpells = allSpells.filter(s => s.source === "arcanum");
  const regularSpells = allSpells.filter(s => s.source !== "arcanum");

  if (!regularSpells.length && !arcanumSpells.length) {
    return `<div class="sh-section">
      <p class="spell-cast-line"><strong>${ab}</strong> · Save DC <strong>${dc}</strong> · Atk <strong>${atk}</strong></p>
      ${slotRef}
      <p class="hint mt-md">No spells recorded.</p>
    </div>`;
  }

  // Build a spell card
  const renderSpell = (s, opts = {}) => {
    const levelLabel = s.level === 0 ? "Cantrip" : `${ORDINAL[s.level]} Level`;
    let prepBadge = "";

    if (opts.arcanum) {
      prepBadge = `<span class="spell-badge spell-badge--arcanum">1/Long Rest</span>`;
    } else if (s.source === "species") {
      prepBadge = `<span class="spell-badge spell-badge--species">Species</span>`;
    } else if (s.always_prepared) {
      prepBadge = `<span class="spell-badge spell-badge--always-prep">Always Prepared</span>`;
    } else if (isWizard && s.source === "class" && s.level > 0) {
      prepBadge = `<span class="spell-badge spell-badge--spellbook">Spellbook</span>`;
      if (s.prepared) prepBadge += `<span class="spell-badge spell-badge--prepared">Prepared</span>`;
    } else if (isPrepCaster && s.level > 0 && s.prepared) {
      prepBadge = `<span class="spell-badge spell-badge--prepared">Prepared</span>`;
    }

    const flags = [
      s.concentration ? "Concentration" : null,
      s.ritual ? "Ritual" : null,
    ].filter(Boolean).map(t => `<span class="spell-flag">${gloss(t)}</span>`).join("");

    const stats = [
      { label: "School",     value: s.school },
      { label: "Cast Time",  value: s.casting_time },
      { label: "Range",      value: s.range },
      { label: "Duration",   value: s.duration },
      { label: "Components", value: s.components },
    ].filter(r => r.value).map(r =>
      `<div class="spell-stat"><span class="spell-stat-label">${r.label}</span>${r.value}</div>`
    ).join("");

    const notesLine = (s.source === "species" && s.notes)
      ? `<div class="spell-notes">${s.notes}</div>` : "";
    const desc = s.description ? `<div class="spell-desc">${glossifyDescription(s.description)}</div>` : "";

    return `<div class="spell-card" onclick="this.classList.toggle('open')">
      <div class="spell-card-header">
        <div class="spell-header-top">
          <span class="spell-name">${s.name}</span>
          <span class="spell-level-label">${levelLabel}</span>
          ${prepBadge ? `<div class="spell-badges">${prepBadge}</div>` : ""}
          ${flags}
          <span class="spell-chevron">▶</span>
        </div>
      </div>
      <div class="spell-card-body">
        ${stats ? `<div class="spell-stats-row">${stats}</div>` : ""}
        ${notesLine}${desc}
      </div>
    </div>`;
  };

  // Mystic Arcanum section (Warlock)
  const arcanumSection = arcanumSpells.length ? `
    <div class="sh-resource-block">
      <h4 class="sh-section-title">Mystic Arcanum <span class="sh-resource-note-inline">· 1/long rest each</span></h4>
      ${arcanumSpells.map(s => renderSpell(s, { arcanum: true })).join("")}
    </div>` : "";

  // Class resource notes
  let resourceNotes = "";
  if (isWizard) {
    const arSlots = Math.ceil((c.level || 1) / 2);
    resourceNotes = `<div class="sh-resource-note-bar">
      <strong>Arcane Recovery:</strong> Once per day on a short rest, recover spell slots totaling up to ${arSlots} levels (max 5th).
    </div>`;
  } else if (className === "paladin") {
    resourceNotes = `<div class="sh-resource-note-bar">
      <strong>Lay on Hands:</strong> ${(c.level || 1) * 5} HP pool per long rest.
    </div>`;
  }

  // Prepare bar (prep casters only)
  let prepBar = "";
  if (isPrepCaster && c.prepared_max != null) {
    const prepCount = c.prepared_count ?? 0;
    const overLimit = prepCount > c.prepared_max;
    prepBar = `<div class="prep-bar">
      <span class="prep-count${overLimit ? " prep-over" : ""}">
        Prepared <strong>${prepCount}</strong> / <strong>${c.prepared_max}</strong>
      </span>
      <button class="prep-edit-btn" onclick="openPrepModal()">✎ Prepare Spells</button>
    </div>`;
  }

  // Section label for non-prep casters
  let sectionLabel = "";
  if (isPact) {
    sectionLabel = `<p class="sh-known-label${arcanumSpells.length ? " mt-sm" : ""}">Known Spells — Pact Magic</p>`;
  } else if (!isPrepCaster) {
    sectionLabel = `<p class="sh-known-label">Known Spells — always available</p>`;
  }

  // Group regular spells by level
  const byLevel = {};
  regularSpells.forEach(s => {
    if (!byLevel[s.level]) byLevel[s.level] = [];
    byLevel[s.level].push(s);
  });

  const levelGroups = Object.keys(byLevel).sort((a,b) => a-b).map(lvl => {
    const levelName = lvl === "0" ? "Cantrips" : `${ORDINAL[lvl]} Level`;
    const gid = `sg-${lvl}`;
    const count = byLevel[lvl].length;
    return `<div class="spell-level-group">
      <h4 class="sh-section-title mt-md spell-group-toggle" onclick="toggleSpellGroup('${gid}',this)">
        ${levelName} <span class="spell-group-count">(${count})</span>
        <span class="spell-group-chevron">▾</span>
      </h4>
      <div class="spell-group-body" id="${gid}">
        ${byLevel[lvl].map(s => renderSpell(s)).join("")}
      </div>
    </div>`;
  }).join("");

  return `<div class="sh-section">
    <p class="spell-cast-line"><strong>${ab}</strong> · Save DC <strong>${dc}</strong> · Atk <strong>${atk}</strong></p>
    ${slotRef}
    ${arcanumSection}
    ${resourceNotes}
    ${prepBar}
    ${sectionLabel}
    ${levelGroups}
  </div>`;
}

// ---------------------------------------------------------------------------
// Prepare Spells modal
// ---------------------------------------------------------------------------
function openPrepModal() {
  const c = charData;
  if (!c || !c.is_prep_caster) return;

  const className = (c.class_name || "").toLowerCase();
  const isWizard = className === "wizard";
  const allSpells = c.spells || [];

  const alwaysPrepSpells = allSpells.filter(s =>
    s.always_prepared && s.level > 0 && s.source !== "species" && s.source !== "arcanum"
  );
  const selectableSpells = allSpells.filter(s =>
    !s.always_prepared && s.level > 0 && s.source !== "species" && s.source !== "arcanum"
  );
  const cantrips = allSpells.filter(s => s.level === 0 && s.source !== "species");

  const prepMax = c.prepared_max || 0;
  window._prepSelected = new Set(selectableSpells.filter(s => s.prepared).map(s => s.spell_id));
  window._prepMax = prepMax;

  const alwaysPrepSection = alwaysPrepSpells.length ? `
    <div class="modal-section">
      <div class="modal-section-title">Always Prepared — doesn't count against limit</div>
      ${alwaysPrepSpells.map(s => `
        <div class="modal-spell-row locked">
          <span class="modal-spell-check-locked">✓</span>
          <label class="modal-spell-name">${s.name} <span class="modal-spell-level">${ORDINAL[s.level]}</span></label>
          <span class="modal-spell-always">Always Prepared</span>
        </div>`).join("")}
    </div>` : "";

  const selectableSection = `
    <div class="modal-section">
      <div class="modal-section-title">Prepare from ${isWizard ? "Spellbook" : "Class List"}</div>
      ${selectableSpells.length ? selectableSpells.map(s => `
        <div class="modal-spell-row">
          <input type="checkbox" class="modal-spell-cb" id="ms-${s.spell_id}" value="${s.spell_id}"
            ${window._prepSelected.has(s.spell_id) ? "checked" : ""}
            onchange="prepModalChange(this)">
          <label for="ms-${s.spell_id}" class="modal-spell-name">${s.name} <span class="modal-spell-level">${ORDINAL[s.level]}</span></label>
        </div>`).join("") : `<p class="hint">No spells available.</p>`}
    </div>`;

  const cantripSection = cantrips.length ? `
    <div class="modal-section">
      <div class="modal-section-title">Cantrips — always prepared</div>
      ${cantrips.map(s => `
        <div class="modal-spell-row locked">
          <span class="modal-spell-check-locked">✓</span>
          <label class="modal-spell-name">${s.name}</label>
        </div>`).join("")}
    </div>` : "";

  const overlay = document.createElement("div");
  overlay.id = "prep-modal-overlay";
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal-box prep-modal">
      <div class="modal-header">
        <h3>Prepare Spells — Long Rest</h3>
        <button class="modal-close-btn" onclick="closePrepModal()">✕</button>
      </div>
      <div class="modal-prep-counter">
        <span>Select up to <strong>${prepMax}</strong> spells</span>
        <span id="prep-modal-count"><strong>${window._prepSelected.size}</strong> selected</span>
      </div>
      <div class="modal-body">
        ${alwaysPrepSection}
        ${selectableSection}
        ${cantripSection}
      </div>
      <div class="modal-footer">
        <button class="prep-modal-cancel" onclick="closePrepModal()">Cancel</button>
        <button class="prep-modal-save" onclick="savePreparedSpells()">Save Preparation</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
}

function prepModalChange(cb) {
  const id = parseInt(cb.value);
  if (cb.checked) {
    if (window._prepSelected.size >= window._prepMax) {
      cb.checked = false;
      toast(`Maximum ${window._prepMax} spells can be prepared`);
      return;
    }
    window._prepSelected.add(id);
  } else {
    window._prepSelected.delete(id);
  }
  const el = document.getElementById("prep-modal-count");
  if (el) el.innerHTML = `<strong>${window._prepSelected.size}</strong> selected`;
}

function closePrepModal() {
  const overlay = document.getElementById("prep-modal-overlay");
  if (overlay) overlay.remove();
}

async function savePreparedSpells() {
  const c = charData;
  const alwaysPrepIds = (c.spells || [])
    .filter(s => s.always_prepared && s.level > 0 && s.source !== "species" && s.source !== "arcanum")
    .map(s => s.spell_id);

  const spellIds = [...window._prepSelected, ...alwaysPrepIds];

  try {
    const result = await api("PATCH", `/api/characters/${charId}/prepared-spells`, { spell_ids: spellIds });
    if (!result) return;

    // Update local charData
    const preparedSet = new Set(spellIds);
    (c.spells || []).forEach(s => {
      if (!s.always_prepared && s.source !== "species" && s.source !== "arcanum" && s.level > 0) {
        s.prepared = preparedSet.has(s.spell_id);
      }
    });
    c.prepared_count = result.prepared_count;

    closePrepModal();

    // Re-render spells tab
    const panel = document.getElementById("sh-tab-spells");
    if (panel) panel.innerHTML = renderSpellsTab(c, c.proficiency_bonus, c.attributes);

    toast("Spell preparation saved");
  } catch (e) {
    toast("Error: " + e.message);
  }
}

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------
function toggleSpellGroup(id, headerEl) {
  const body = document.getElementById(id);
  if (!body) return;
  const collapsed = body.classList.toggle("collapsed");
  headerEl.classList.toggle("collapsed", collapsed);
}

function switchSheetTab(tab, btn) {
  ["stats","bio","equipment","spells"].forEach(t => {
    const el = document.getElementById(`sh-tab-${t}`);
    if (el) el.classList.toggle("hidden", t !== tab);
  });
  document.querySelectorAll(".sh-tab-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
}

boot();
