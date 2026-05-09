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
// Warlock pact magic: {count, level} per character level
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

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
let charId, charData;

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
// Slot calculation
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
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  const m = window.location.pathname.match(/\/characters\/(\d+)\/sheet/);
  if (!m) { document.getElementById("sheet-loading").textContent = "Invalid URL."; return; }
  charId = parseInt(m[1], 10);

  const me = await api("GET", "/auth/me");
  if (!me) return;
  document.getElementById("sheet-user-name").textContent = me.name || me.email;

  try {
    charData = await api("GET", `/api/characters/${charId}/sheet-data`);
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
  } catch (_) { /* ignore poll errors */ }
}

// ---------------------------------------------------------------------------
// Main render
// ---------------------------------------------------------------------------
function render() {
  const c = charData;
  const prof = c.proficiency_bonus || 2;
  const attrs = c.attributes || {};
  const profSkills = new Set(c.prof_skills || []);
  const expertSkills = new Set(c.expert_skills || []);
  const saveProfs = new Set(c.save_profs || []);

  const identity = [
    c.class_name ? `${c.class_name} ${c.level}` : null,
    c.species_lineage ? `${c.species_lineage} ${c.species_name}` : c.species_name,
    c.background_name,
    c.alignment,
  ].filter(Boolean).join(" · ");

  const initiative = fmtMod(mod(attrs.dex || 10));
  const passivePerc = 10 + mod(attrs.wis || 10) + (profSkills.has("Perception") ? prof : 0);

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
        <div class="sh-combat-big">${c.ac ?? "—"}</div>
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Speed</div>
        <div class="sh-combat-big">${c.speed ?? "—"} ft</div>
      </div>
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Initiative</div>
        <div class="sh-combat-big">${initiative}</div>
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

    ${c.class_spellcasting_type ? renderSlotBar(c) : ""}

    <div class="sh-main">
      <div class="sh-col-left">
        ${renderAbilityScores(attrs)}
        ${renderSavingThrows(attrs, saveProfs, prof)}
        ${renderSkills(attrs, profSkills, expertSkills, prof)}
      </div>
      <div class="sh-col-right">
        ${renderProficiencies(c)}
      </div>
    </div>

    <div class="sh-tabs">
      ${c.spells.length ? '<button class="sh-tab-btn active" onclick="switchSheetTab(\'spells\',this)">Spells</button>' : ""}
      <button class="sh-tab-btn ${c.spells.length ? "" : "active"}" onclick="switchSheetTab('features',this)">Features &amp; Traits</button>
      <button class="sh-tab-btn" onclick="switchSheetTab('equipment',this)">Equipment</button>
      <button class="sh-tab-btn" onclick="switchSheetTab('bio',this)">Biography</button>
    </div>

    ${c.spells.length ? `<div id="sh-tab-spells" class="sh-tab-panel">${renderSpellsTab(c)}</div>` : ""}
    <div id="sh-tab-features" class="sh-tab-panel ${c.spells.length ? "hidden" : ""}">${renderFeaturesTab(c)}</div>
    <div id="sh-tab-equipment" class="sh-tab-panel hidden">${renderEquipmentTab(c)}</div>
    <div id="sh-tab-bio" class="sh-tab-panel hidden">${renderBioTab(c)}</div>
  `;

}

// ---------------------------------------------------------------------------
// HP widget (read-only — HP is managed by the DM via the admin panel)
// ---------------------------------------------------------------------------
function renderHpWidget(c) {
  const cur = c.hp_current ?? 0;
  const max = c.hp_max ?? 1;
  const pct = max > 0 ? Math.round((cur / max) * 100) : 0;
  const barColor = pct > 50 ? "#4a8c4a" : pct > 25 ? "#b8860b" : "#8b1a1a";
  return `
    <div class="hp-bar-wrap">
      <div class="hp-bar" style="width:${pct}%;background:${barColor}"></div>
    </div>
    <div class="hp-numbers">${cur} <span class="hp-max">/ ${max}</span></div>`;
}

// ---------------------------------------------------------------------------
// Spell slot bar
// ---------------------------------------------------------------------------
function renderSlotBar(c) {
  const slots = getSlots(c);
  if (!slots.length) return "";
  const used = charData.spell_slots_used || {};
  const pips = slots.map(s => {
    const expended = parseInt(used[String(s.level)] || 0, 10);
    const bubbles = Array.from({length: s.total}, (_, i) => {
      const isUsed = i < expended;
      return `<button class="slot-pip ${isUsed ? "used" : ""}" onclick="toggleSlot(${s.level},${i})" title="${ORDINAL[s.level]} level slot"></button>`;
    }).join("");
    return `<div class="slot-group">
      <span class="slot-label">${s.pact ? "Pact" : ORDINAL[s.level]}</span>
      <div class="slot-pips">${bubbles}</div>
    </div>`;
  }).join("");
  return `<div class="sh-slot-bar"><span class="slot-bar-title">Spell Slots</span>${pips}</div>`;
}

async function toggleSlot(level, index) {
  const used = { ...(charData.spell_slots_used || {}) };
  const key = String(level);
  const slots = getSlots(charData);
  const slotGroup = slots.find(s => s.level === level);
  if (!slotGroup) return;
  const curUsed = parseInt(used[key] || 0, 10);
  // If clicking the last used pip, unuse it; otherwise use the next available pip
  if (index === curUsed - 1) {
    used[key] = curUsed - 1;
  } else {
    used[key] = Math.min(index + 1, slotGroup.total);
  }
  try {
    const r = await api("POST", `/api/characters/${charId}/spell-slots`, { used });
    charData.spell_slots_used = r.spell_slots_used;
    refreshSlotBar();
  } catch(e) { toast("⚠ " + e.message, 4000); }
}

function refreshSlotBar() {
  const container = document.querySelector(".sh-slot-bar");
  if (!container) return;
  container.outerHTML = renderSlotBar(charData);
  // re-query after DOM update
  document.querySelector(".sh-slot-bar")?.querySelectorAll(".slot-pip").forEach((btn, i) => {
    // onclick already inline in renderSlotBar
  });
  // Easier: just re-render the whole slot bar
  const newHtml = renderSlotBar(charData);
  const wrapper = document.querySelector(".sh-slot-bar")?.parentElement;
  if (wrapper) {
    const tmp = document.createElement("div");
    tmp.innerHTML = newHtml;
    document.querySelector(".sh-slot-bar").replaceWith(tmp.firstElementChild || document.createElement("div"));
  }
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
function renderSkills(attrs, profSkills, expertSkills, prof) {
  const rows = Object.entries(SKILL_ABILITY).sort(([a],[b]) => a.localeCompare(b)).map(([skill, ab]) => {
    const base = mod(attrs[ab] || 10);
    const isProf = profSkills.has(skill);
    const isExpert = expertSkills.has(skill);
    const bonus = base + (isExpert ? prof * 2 : isProf ? prof : 0);
    const dot = isExpert ? "expert" : isProf ? "prof" : "";
    return `<div class="save-row">
      <span class="prof-dot ${dot}" title="${isExpert ? "Expertise" : isProf ? "Proficient" : ""}"></span>
      <span class="save-name">${skill} <span class="skill-ab">(${ab.toUpperCase()})</span></span>
      <span class="save-val">${fmtMod(bonus)}</span>
    </div>`;
  }).join("");
  return `<div class="sh-section"><h4 class="sh-section-title">Skills</h4>${rows}</div>`;
}

// ---------------------------------------------------------------------------
// Proficiencies panel (right column)
// ---------------------------------------------------------------------------
function renderProficiencies(c) {
  const languages = (c.language_proficiencies || []).join(", ") || "—";
  const tools = (c.tool_proficiencies || []).join(", ") || "—";
  const masteries = (c.weapon_mastery_unlocks || []).join(", ") || "—";
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
    ${c.class_spellcasting_type ? `<div class="sh-section">
      <h4 class="sh-section-title">Spellcasting</h4>
      <p class="sh-prose">Ability: <strong>${c.class_spellcasting_ability || "—"}</strong></p>
      <p class="sh-prose">Save DC: <strong>${8 + (c.proficiency_bonus||2) + mod((c.attributes||{})[SPELL_AB_KEY[c.class_spellcasting_ability]] || 10)}</strong></p>
      <p class="sh-prose">Attack: <strong>${fmtMod((c.proficiency_bonus||2) + mod((c.attributes||{})[SPELL_AB_KEY[c.class_spellcasting_ability]] || 10))}</strong></p>
    </div>` : ""}
  `;
}

const SPELL_AB_KEY = {
  "Intelligence":"int","Wisdom":"wis","Charisma":"cha"
};

// ---------------------------------------------------------------------------
// Spells tab
// ---------------------------------------------------------------------------
function renderSpellsTab(c) {
  const cantrips = c.spells.filter(s => s.level === 0);
  const leveled = c.spells.filter(s => s.level > 0);

  const renderSpell = (s) => {
    const tags = [
      s.level === 0 ? "Cantrip" : `${ORDINAL[s.level]} Level`,
      s.school,
      s.casting_time,
      s.range ? s.range + " range" : null,
      s.duration,
      s.concentration ? "Concentration" : null,
      s.ritual ? "Ritual" : null,
    ].filter(Boolean).map(t => `<span class="spell-tag">${t}</span>`).join("");

    const compLine = s.components ? `<div class="spell-meta">Components: ${s.components}</div>` : "";
    const desc = s.description ? `<div class="spell-desc">${s.description}</div>` : "";

    return `<div class="spell-card" onclick="this.classList.toggle('open')">
      <div class="spell-card-header">
        <span class="spell-name">${s.name}</span>
        <span class="spell-tags">${tags}</span>
        <span class="spell-chevron">▶</span>
      </div>
      <div class="spell-card-body">
        ${compLine}
        ${desc}
      </div>
    </div>`;
  };

  const cantripHtml = cantrips.length ? `
    <h4 class="sh-section-title">Cantrips</h4>
    ${cantrips.map(renderSpell).join("")}` : "";

  const leveledHtml = leveled.length ? `
    <h4 class="sh-section-title mt-md">Leveled Spells</h4>
    ${leveled.map(renderSpell).join("")}` : "";

  return `<div class="sh-section">${cantripHtml}${leveledHtml}</div>`;
}

// ---------------------------------------------------------------------------
// Features tab
// ---------------------------------------------------------------------------
function renderFeaturesTab(c) {
  const renderEntry = (name, desc, badge) => `
    <div class="feature-card">
      <div class="feature-card-header">
        <span class="feature-name">${name}</span>
        ${badge ? `<span class="feature-badge">${badge}</span>` : ""}
      </div>
      ${desc ? `<div class="feature-desc">${desc}</div>` : ""}
    </div>`;

  const classFeatures = (c.class_features || []).map(f => renderEntry(f.name, f.description, `${c.class_name} Lv ${f.level}`)).join("");
  const speciesTraits = (c.species_traits || []).map(t => renderEntry(t.name, t.description, c.species_name)).join("");
  const feats = (c.feats || []).map(f => renderEntry(f.name, f.description, "Feat")).join("");

  return `<div class="sh-section">
    ${classFeatures.length ? `<h4 class="sh-section-title">Class Features</h4>${classFeatures}` : ""}
    ${speciesTraits.length ? `<h4 class="sh-section-title mt-md">Species Traits</h4>${speciesTraits}` : ""}
    ${feats.length ? `<h4 class="sh-section-title mt-md">Feats</h4>${feats}` : ""}
  </div>`;
}

// ---------------------------------------------------------------------------
// Equipment tab
// ---------------------------------------------------------------------------
function renderEquipmentTab(c) {
  if (!c.equipment.length) return `<p class="hint">No equipment recorded.</p>`;
  const rows = c.equipment.map(e => {
    const detail = [
      e.damage ? `${e.damage} ${e.damage_type || ""}`.trim() : null,
      e.ac_formula ? `AC ${e.ac_formula}` : null,
      (e.properties || []).join(", ") || null,
      e.mastery_property ? `Mastery: ${e.mastery_property}` : null,
    ].filter(Boolean).join(" · ");
    return `<tr>
      <td>${e.quantity > 1 ? `${e.quantity}×` : ""} <strong>${e.name}</strong></td>
      <td class="text-muted">${e.item_type || ""}</td>
      <td class="text-muted">${detail}</td>
    </tr>`;
  }).join("");
  return `<table class="data-table sh-equip-table"><tbody>${rows}</tbody></table>`;
}

// ---------------------------------------------------------------------------
// Bio tab
// ---------------------------------------------------------------------------
function renderBioTab(c) {
  return `<div class="sh-section">
    ${c.alignment ? `<p class="sh-prose"><strong>Alignment:</strong> ${c.alignment}</p>` : ""}
    ${c.bio ? `<div class="sh-prose bio-text">${c.bio.replace(/\n/g, "<br>")}</div>` : '<p class="hint">No backstory recorded.</p>'}
  </div>`;
}

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------
function switchSheetTab(tab, btn) {
  ["spells","features","equipment","bio"].forEach(t => {
    const el = document.getElementById(`sh-tab-${t}`);
    if (el) el.classList.toggle("hidden", t !== tab);
  });
  document.querySelectorAll(".sh-tab-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
}

boot();
