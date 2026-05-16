/* D&D 2024 Level-Up Wizard — Dynamic Step Runner */

const charId = parseInt(location.pathname.split("/")[2]);

let opts = null;       // levelup-options response
let allSpells = [];    // class spell list
let stepIdx = 0;       // 0 = features info; 1..n = steps
let steps = [];        // opts.steps array

// Accumulated choices: step_id → payload
const choices = {};

// HP roll tracker
let hpMethod = "average";
let hpDieValue = null;

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const o = { method, headers: { "Content-Type": "application/json" } };
  if (body) o.body = JSON.stringify(body);
  const res = await fetch(path, o);
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

function show(id) { document.getElementById(id)?.classList.remove("hidden"); }
function hide(id) { document.getElementById(id)?.classList.add("hidden"); }

function setHtml(id, html) { const el = document.getElementById(id); if (el) el.innerHTML = html; }

function abilityName(k) {
  return {str:"Strength",dex:"Dexterity",con:"Constitution",int:"Intelligence",wis:"Wisdom",cha:"Charisma"}[k] || k;
}

function ordinalLabel(n) {
  const s = ["","1st","2nd","3rd","4th","5th","6th","7th","8th","9th"];
  return s[n] || `${n}th`;
}

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
    window.location.href = "/portal";
    return;
  }

  document.title = `Level Up — ${opts.character_name}`;
  document.getElementById("lu-title").textContent = opts.character_name;
  document.getElementById("lu-subtitle").textContent =
    `${opts.class_name} · Level ${opts.current_level} → ${opts.next_level}`;

  // Load class spells for spell-picker steps
  if (opts.class_spellcasting) {
    try {
      allSpells = await api("GET", `/api/content/spells?class_name=${encodeURIComponent(opts.class_name)}`);
    } catch(_) { allSpells = []; }
  }

  steps = opts.steps || [];
  renderFeatures();
  hide("lu-loading");
  show("lu-root");
  renderPips();
  showPanel("features");
}

// ---------------------------------------------------------------------------
// Features info step (always first panel)
// ---------------------------------------------------------------------------
function renderFeatures() {
  const all = [...(opts.new_features || []), ...(opts.subclass_features || [])];
  const el = document.getElementById("lu-features-list");
  if (!all.length) {
    el.innerHTML = `<p class="lu-no-features">No automatic new features at this level — but your power grows.</p>`;
  } else {
    el.innerHTML = all.map(f => `
      <div class="lu-feature-card">
        <div class="lu-feature-name">${f.name}</div>
        <div class="lu-feature-desc">${f.description || ""}</div>
        ${f.choice_required && f.options?.length ? `
          <div class="lu-feature-choice-note">
            <span class="lu-choice-tag">You will choose below</span>
          </div>` : ""}
      </div>`).join("");
  }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
function luNext() {
  // Validate current step
  if (stepIdx > 0) {
    const step = steps[stepIdx - 1];
    if (!validateStep(step)) return;
  }
  stepIdx++;
  if (stepIdx > steps.length) {
    renderConfirm();
    return;
  }
  const step = steps[stepIdx - 1];
  renderPips();
  renderStep(step);
  showPanel("host");
}

function luBack() {
  if (stepIdx === 0) return;
  stepIdx--;
  renderPips();
  if (stepIdx === 0) {
    showPanel("features");
  } else {
    renderStep(steps[stepIdx - 1]);
    showPanel("host");
  }
}

function showPanel(name) {
  // name: "features" | "host" | "done"
  document.getElementById("lu-step-features")?.classList.add("hidden");
  document.getElementById("lu-step-host")?.classList.add("hidden");
  document.getElementById("lu-step-done")?.classList.add("hidden");
  if (name === "features") document.getElementById("lu-step-features")?.classList.remove("hidden");
  if (name === "host") document.getElementById("lu-step-host")?.classList.remove("hidden");
  if (name === "done") document.getElementById("lu-step-done")?.classList.remove("hidden");
}

function renderPips() {
  // stepIdx 0 = features
  const labels = [{label: "Features"}];
  for (const s of steps) labels.push({label: s.label});
  labels.push({label: "Confirm"});

  const confirmIdx = steps.length + 1;
  document.getElementById("lu-steps").innerHTML = labels.map((l, i) => {
    let cls = "lu-pip";
    if (i === stepIdx) cls += " lu-pip--active";
    else if (i < stepIdx) cls += " lu-pip--done";
    return `<span class="${cls}">${l.label}</span>`;
  }).join('<span class="lu-pip-sep">›</span>');
}

// ---------------------------------------------------------------------------
// Step dispatcher
// ---------------------------------------------------------------------------
function renderStep(step) {
  const host = document.getElementById("lu-step-host");
  const kind = step.kind;

  if (kind === "hp")               host.innerHTML = buildHpStep(step);
  else if (kind === "subclass")    host.innerHTML = buildSubclassStep(step);
  else if (kind === "asi")         host.innerHTML = buildAsiStep(step);
  else if (kind === "epic_boon")   host.innerHTML = buildFeatPickStep(step, opts.epic_boons, "feat_id");
  else if (kind === "fighting_style")      host.innerHTML = buildFeatPickStep(step, opts.fighting_styles, "feat_id");
  else if (kind === "fighting_style_swap") host.innerHTML = buildFightingStyleSwapStep(step);
  else if (kind === "expertise")   host.innerHTML = buildExpertiseStep(step);
  else if (kind === "cantrips_new")  host.innerHTML = buildSpellPickStep(step, cantripsAvailable());
  else if (kind === "spells_new" || kind === "wizard_spellbook") host.innerHTML = buildSpellPickStep(step, spellsAvailable(step));
  else if (kind === "spell_swap")  host.innerHTML = buildSpellSwapStep(step);
  else if (kind === "cantrip_swap") host.innerHTML = buildCantripSwapStep(step);
  else if (kind === "metamagic")   host.innerHTML = buildCardPickStep(step, step.options || []);
  else if (kind === "invocations_new")  host.innerHTML = buildCardPickStep(step, step.options || []);
  else if (kind === "invocation_swap")  host.innerHTML = buildInvocationSwapStep(step);
  else if (kind === "mystic_arcanum") host.innerHTML = buildMysticArcanumStep(step);
  else if (kind === "feature_choice")    host.innerHTML = buildFeatureChoiceStep(step);
  else if (kind === "species_revelation") host.innerHTML = buildSpeciesRevelationStep(step);
  else if (kind === "species_spell_info") host.innerHTML = buildSpeciesSpellInfoStep(step);
  else host.innerHTML = buildUnknownStep(step);

  attachStepListeners(step);
}

function validateStep(step) {
  const payload = choices[step.id];
  if (!step.required) return true;

  const kind = step.kind;
  if (kind === "hp") {
    if (hpMethod !== "average" && hpDieValue === null) {
      toast("Enter your HP roll first."); return false;
    }
    return true;
  }
  if (kind === "subclass") {
    if (!payload?.subclass_id) { toast("Choose a subclass."); return false; }
    return true;
  }
  if (kind === "asi") {
    if (!payload?.mode) { toast("Choose an ability score improvement."); return false; }
    if (payload.mode === "+2" && !payload.ability) { toast("Choose which ability to increase."); return false; }
    if (payload.mode === "+1+1" && (payload.abilities || []).length < 2) { toast("Choose two abilities."); return false; }
    if (payload.mode === "feat" && !payload.feat_id) { toast("Choose a feat."); return false; }
    return true;
  }
  if (kind === "epic_boon" || kind === "fighting_style") {
    if (!payload?.feat_id) { toast("Make a selection."); return false; }
    return true;
  }
  if (kind === "expertise") {
    const needed = step.pick || 1;
    if ((payload?.skills || []).length < needed) { toast(`Choose ${needed} skill(s) for expertise.`); return false; }
    return true;
  }
  if (kind === "cantrips_new") {
    const needed = step.pick || 1;
    if ((payload?.spell_ids || []).length < needed) { toast(`Choose ${needed} cantrip(s).`); return false; }
    return true;
  }
  if (kind === "spells_new" || kind === "wizard_spellbook") {
    const needed = step.pick || 1;
    if ((payload?.spell_ids || []).length < needed) { toast(`Choose ${needed} spell(s).`); return false; }
    return true;
  }
  if (kind === "metamagic") {
    const needed = step.pick || 2;
    if ((payload?.keys || []).length < needed) { toast(`Choose ${needed} metamagic option(s).`); return false; }
    return true;
  }
  if (kind === "invocations_new") {
    const needed = step.pick || 1;
    if ((payload?.keys || []).length < needed) { toast(`Choose ${needed} invocation(s).`); return false; }
    return true;
  }
  if (kind === "mystic_arcanum") {
    if (!payload?.spell_id) { toast("Choose a spell for Mystic Arcanum."); return false; }
    return true;
  }
  if (kind === "feature_choice") {
    if (!payload?.choice) { toast("Make a choice."); return false; }
    return true;
  }
  if (kind === "species_revelation") {
    if (!payload?.key) { toast("Choose your Celestial Revelation."); return false; }
    return true;
  }
  return true;
}

// ---------------------------------------------------------------------------
// Spell helpers
// ---------------------------------------------------------------------------
function ownedIds() { return new Set(opts.owned_spell_ids || []); }

function cantripsAvailable() {
  const owned = ownedIds();
  return allSpells.filter(s => s.level === 0 && !owned.has(s.id));
}

function spellsAvailable(step) {
  const owned = ownedIds();
  const maxSl = step.max_spell_level || opts.max_spell_level || 9;
  return allSpells.filter(s => s.level >= 1 && s.level <= maxSl && !owned.has(s.id));
}

// ---------------------------------------------------------------------------
// Step Builders
// ---------------------------------------------------------------------------

function navRow(backLabel = "← Back", nextLabel = "Continue →", nextId = "lu-step-next", requiredOk = true, skipLabel = null) {
  const skip = skipLabel ? `<button class="btn-secondary" onclick="skipStep()">${skipLabel}</button>` : "";
  return `
    <div class="lu-nav">
      <button class="btn-secondary" onclick="luBack()">${backLabel}</button>
      ${skip}
      <button class="btn-primary" id="${nextId}" onclick="luNext()">${nextLabel}</button>
    </div>`;
}

// HP Step
function buildHpStep(step) {
  const avg = step.average;
  const draconic = step.draconic_bonus || 0;
  const draconicNote = draconic ? `<span class="lu-hp-bonus">+ Draconic Resilience <strong>+${draconic}</strong></span>` : "";
  const conSign = step.con_mod >= 0 ? `+${step.con_mod}` : `${step.con_mod}`;
  const curMethod = hpMethod;
  return `
    <h2 class="lu-step-heading">Hit Points</h2>
    <p class="lu-step-desc">How would you like to determine your HP gain this level?</p>
    <div class="lu-hp-ref">
      <span class="lu-hp-die">d${step.hit_die}</span>
      <span class="lu-hp-detail">Average: <strong>${avg}</strong> &nbsp;|&nbsp; CON: <strong>${conSign}</strong>${draconicNote}</span>
    </div>
    <div class="lu-hp-methods">
      <label class="lu-hp-method ${curMethod==='average'?'selected':''}">
        <input type="radio" name="hp_method" value="average" ${curMethod==='average'?'checked':''} onchange="setHpMethod('average')">
        <div class="lu-hp-method-body">
          <div class="lu-hp-method-title">Take Average</div>
          <div class="lu-hp-method-desc">Guaranteed <strong>${avg} + ${conSign} CON${draconic?` + ${draconic}`:""}</strong> = <strong>${avg + step.con_mod + draconic} HP</strong></div>
        </div>
      </label>
      <label class="lu-hp-method ${curMethod==='roll'?'selected':''}">
        <input type="radio" name="hp_method" value="roll" ${curMethod==='roll'?'checked':''} onchange="setHpMethod('roll')">
        <div class="lu-hp-method-body">
          <div class="lu-hp-method-title">Roll d${step.hit_die} <em class="lu-hp-floor">(uses average if lower)</em></div>
          <div class="lu-hp-roll-row" id="hp-roll-row">
            <button class="btn-secondary lu-roll-btn" onclick="rollHpDie(${step.hit_die})" type="button">Roll d${step.hit_die}</button>
            <span class="lu-roll-result" id="hp-roll-result">${hpDieValue !== null && curMethod==='roll' ? `Rolled: <strong>${hpDieValue}</strong>` : "—"}</span>
          </div>
        </div>
      </label>
      <label class="lu-hp-method ${curMethod==='manual'?'selected':''}">
        <input type="radio" name="hp_method" value="manual" ${curMethod==='manual'?'checked':''} onchange="setHpMethod('manual')">
        <div class="lu-hp-method-body">
          <div class="lu-hp-method-title">Manual Entry</div>
          <div class="lu-hp-method-desc">Enter raw die result (CON mod applied automatically)</div>
          <div class="lu-hp-roll-row" id="hp-manual-row">
            <input type="number" min="1" max="${step.hit_die}" id="hp-manual-input"
              class="lu-manual-input" placeholder="1–${step.hit_die}"
              value="${hpDieValue !== null && curMethod==='manual' ? hpDieValue : ''}"
              oninput="setHpManual(this.value)">
          </div>
        </div>
      </label>
    </div>
    <div id="hp-total-preview" class="lu-hp-total">${buildHpPreview(step)}</div>
    ${navRow("← Back", "Continue →")}`;
}

function buildHpPreview(step) {
  const draconic = step.draconic_bonus || 0;
  let die = hpMethod === "average" ? step.average : (hpDieValue ?? null);
  if (die === null) return '<span class="lu-hp-total-label">Awaiting roll…</span>';
  const effective = hpMethod === "roll" ? Math.max(die, step.average) : die;
  const total = effective + step.con_mod + draconic;
  return `<span class="lu-hp-total-label">HP this level: <strong>+${total}</strong></span>
    <span class="lu-hp-total-detail">(${effective} die${step.con_mod !== 0 ? ` ${step.con_mod >= 0 ? "+" : ""}${step.con_mod} CON` : ""}${draconic ? ` +${draconic} Draconic` : ""})</span>`;
}

// Subclass Step
function buildSubclassStep(step) {
  const prev = choices[step.id];
  return `
    <h2 class="lu-step-heading">Choose Your Subclass</h2>
    <p class="lu-step-desc">Your path diverges. Choose a subclass to define your specialization.</p>
    <div class="lu-subclass-grid" id="subclass-grid">
      ${(step.options || []).map(s => `
        <div class="lu-subclass-card ${prev?.subclass_id === s.id ? 'chosen' : ''}"
             onclick="pickSubclass(${s.id}, '${escQ(s.name)}', this)" data-id="${s.id}">
          <div class="lu-subclass-name">${s.name}</div>
          <div class="lu-subclass-desc">${s.description || ""}</div>
          ${s.features?.length ? `<div class="lu-subclass-features">
            ${s.features.map(f => `<div class="lu-sub-feat"><strong>${f.name}:</strong> ${f.description || ""}</div>`).join("")}
          </div>` : ""}
        </div>`).join("")}
    </div>
    ${navRow()}`;
}

// ASI Step
function buildAsiStep(step) {
  const prev = choices[step.id] || {};
  const mode = prev.mode || null;
  const attrs = step.current_attributes || opts.current_attributes || {};
  const abilityKeys = ["str","dex","con","int","wis","cha"];

  return `
    <h2 class="lu-step-heading">Ability Score Improvement</h2>
    <p class="lu-step-desc">Choose how to spend your Ability Score Improvement.</p>
    <div class="lu-asi-modes">

      <label class="lu-asi-mode ${mode==='+2'?'active':''}">
        <input type="radio" name="asi_mode" value="+2" onchange="setAsiMode('+2')">
        <div><strong>+2 to one ability</strong></div>
      </label>
      <div class="lu-asi-sub" id="asi-sub-plus2" ${mode==='+2'?'':'style="display:none"'}>
        <div class="lu-ability-grid">
          ${abilityKeys.map(k => {
            const cur = attrs[k] || 10;
            const capped = cur >= 20;
            return `<button class="lu-ability-btn ${prev.ability === k ? 'chosen' : ''} ${capped ? 'capped' : ''}"
              onclick="setAsiAbility('${k}')" data-ability="${k}" ${capped ? 'title="Already at maximum"' : ''}>
              <span class="lu-ab-name">${abilityName(k)}</span>
              <span class="lu-ab-val">${cur}${capped ? ' ✓' : ''}</span>
              ${!capped ? `<span class="lu-ab-new">→ ${Math.min(20, cur + 2)}</span>` : ''}
            </button>`;
          }).join("")}
        </div>
      </div>

      <label class="lu-asi-mode ${mode==='+1+1'?'active':''}">
        <input type="radio" name="asi_mode" value="+1+1" onchange="setAsiMode('+1+1')">
        <div><strong>+1 to two different abilities</strong></div>
      </label>
      <div class="lu-asi-sub" id="asi-sub-plus1" ${mode==='+1+1'?'':'style="display:none"'}>
        <div class="lu-ability-grid">
          ${abilityKeys.map(k => {
            const cur = attrs[k] || 10;
            const capped = cur >= 20;
            const chosen = (prev.abilities || []).includes(k);
            return `<button class="lu-ability-btn ${chosen ? 'chosen' : ''} ${capped ? 'capped' : ''}"
              onclick="toggleAsiAbility('${k}')" data-ability="${k}" ${capped ? 'title="Already at maximum"' : ''}>
              <span class="lu-ab-name">${abilityName(k)}</span>
              <span class="lu-ab-val">${cur}${capped ? ' ✓' : ''}</span>
              ${!capped ? `<span class="lu-ab-new">→ ${Math.min(20, cur + 1)}</span>` : ''}
            </button>`;
          }).join("")}
        </div>
        <p class="lu-step-desc" style="margin-top:8px">Choose 2 abilities (${(prev.abilities||[]).length}/2 chosen).</p>
      </div>

      <label class="lu-asi-mode ${mode==='feat'?'active':''}">
        <input type="radio" name="asi_mode" value="feat" onchange="setAsiMode('feat')">
        <div><strong>Take a General Feat</strong></div>
      </label>
      <div class="lu-asi-sub" id="asi-sub-feat" ${mode==='feat'?'':'style="display:none"'}>
        <div class="lu-feat-grid">
          ${(opts.general_feats || []).map(f => `
            <div class="lu-feat-card ${prev.feat_id === f.id ? 'chosen' : ''}"
                 onclick="pickAsiFeat(${f.id}, this)" data-id="${f.id}">
              <div class="lu-feat-name">${f.name}</div>
              <div class="lu-feat-desc">${f.description || ""}</div>
              ${f.prerequisites ? `<div class="lu-feat-prereq">Requires: ${JSON.stringify(f.prerequisites)}</div>` : ""}
            </div>`).join("")}
        </div>
      </div>

    </div>
    ${navRow()}`;
}

// Generic feat-pick step (fighting style, epic boon)
function buildFeatPickStep(step, feats, keyName) {
  const prev = choices[step.id] || {};
  return `
    <h2 class="lu-step-heading">${step.label}</h2>
    <p class="lu-step-desc">${step.description || ""}</p>
    <div class="lu-feat-grid" id="feat-pick-grid">
      ${(feats || []).map(f => `
        <div class="lu-feat-card ${prev[keyName] === f.id ? 'chosen' : ''}"
             onclick="pickFeat('${step.id}', '${keyName}', ${f.id}, this)">
          <div class="lu-feat-name">${f.name}</div>
          <div class="lu-feat-desc">${f.description || ""}</div>
        </div>`).join("")}
    </div>
    ${navRow()}`;
}

// Fighting style swap step (Fighter, optional)
function buildFightingStyleSwapStep(step) {
  const prev = choices[step.id] || {};
  // Show currently chosen style (from prev selections or opts)
  const currentStyle = choices[`fighting_style_l1`] || null;
  return `
    <h2 class="lu-step-heading">Fighting Style</h2>
    <p class="lu-step-desc">As a Fighter, you may replace your Fighting Style with a different one this level (optional).</p>
    <div class="lu-feat-grid" id="feat-pick-grid">
      ${(opts.fighting_styles || []).map(f => `
        <div class="lu-feat-card ${prev.feat_id === f.id ? 'chosen' : ''}"
             onclick="pickFeat('${step.id}', 'feat_id', ${f.id}, this)">
          <div class="lu-feat-name">${f.name}</div>
          <div class="lu-feat-desc">${f.description || ""}</div>
        </div>`).join("")}
    </div>
    ${navRow("← Back", "Continue →", "lu-step-next", false, "Skip (keep current)")}`;
}

// Expertise step
function buildExpertiseStep(step) {
  const prev = choices[step.id] || { skills: [] };
  const skills = step.eligible_skills || [];
  return `
    <h2 class="lu-step-heading">Expertise</h2>
    <p class="lu-step-desc">Choose ${step.pick} skill${step.pick > 1 ? "s" : ""} to gain Expertise in (double your proficiency bonus).</p>
    <div class="lu-skill-grid" id="skill-grid">
      ${skills.map(name => `
        <button class="lu-skill-btn ${prev.skills.includes(name) ? 'chosen' : ''}"
                onclick="toggleSkill('${step.id}', '${name}', ${step.pick}, this)">${name}</button>
      `).join("")}
    </div>
    <p class="lu-step-desc" style="margin-top:8px">${(prev.skills || []).length}/${step.pick} chosen.</p>
    ${navRow()}`;
}

// Spell pick step (cantrips, spells, wizard spellbook, mystic arcanum list)
function buildSpellPickStep(step, spellList) {
  const prev = choices[step.id] || { spell_ids: [] };
  const levels = [...new Set(spellList.map(s => s.level))].sort((a, b) => a - b);
  const filterHtml = levels.length > 1
    ? `<div class="lu-spell-filter" id="spell-filter">
        <button class="lu-filter-btn active" onclick="setSpellFilter(null, this)">All</button>
        ${levels.map(l => `<button class="lu-filter-btn" onclick="setSpellFilter(${l}, this)">${l === 0 ? 'Cantrip' : `Level ${l}`}</button>`).join("")}
      </div>` : "";
  return `
    <h2 class="lu-step-heading">${step.label}</h2>
    <p class="lu-step-desc">${step.kind === "wizard_spellbook"
      ? `Add ${step.pick} spell${step.pick > 1 ? "s" : ""} to your spellbook (free — up to spell level ${step.max_spell_level || ""}).`
      : `Choose ${step.pick} spell${step.pick > 1 ? "s" : ""} to learn (up to level ${step.max_spell_level || ""}).`}</p>
    ${filterHtml}
    <div class="lu-spell-grid" id="spell-grid">
      ${spellList.map(s => spellCard(s, step.id, prev.spell_ids.includes(s.id))).join("")}
    </div>
    <p class="lu-spell-count" id="spell-count">${(prev.spell_ids || []).length}/${step.pick} chosen</p>
    ${navRow()}`;
}

// Spell swap step (optional)
function buildSpellSwapStep(step) {
  const prev = choices[step.id] || {};
  const owned = (opts.owned_spell_ids || []);
  const ownedSpells = allSpells.filter(s => owned.includes(s.id) && s.level >= 1);
  const maxSl = step.max_spell_level || 9;
  const available = allSpells.filter(s => s.level >= 1 && s.level <= maxSl && !owned.includes(s.id));
  return `
    <h2 class="lu-step-heading">Swap a Known Spell <em style="font-size:0.8em;opacity:0.7">(optional)</em></h2>
    <p class="lu-step-desc">You may replace one known spell with a different one. Skip if you want to keep your current spells.</p>
    <div class="lu-swap-cols">
      <div class="lu-swap-col">
        <div class="lu-swap-label">Remove (current spell)</div>
        <div class="lu-spell-grid lu-swap-grid" id="swap-remove-grid">
          ${ownedSpells.map(s => `<div class="lu-spell-card ${prev.remove_id === s.id ? 'chosen' : ''}"
            onclick="swapPick('remove', ${s.id}, this)" data-id="${s.id}">
            <div class="lu-spell-name">${s.name}</div>
            <div class="lu-spell-meta">${s.level === 0 ? "Cantrip" : `Level ${s.level}`}${s.school ? " · " + s.school : ""}</div>
          </div>`).join("")}
        </div>
      </div>
      <div class="lu-swap-col">
        <div class="lu-swap-label">Add (new spell, up to level ${maxSl})</div>
        <div class="lu-spell-grid lu-swap-grid" id="swap-add-grid">
          ${available.map(s => `<div class="lu-spell-card ${prev.add_id === s.id ? 'chosen' : ''}"
            onclick="swapPick('add', ${s.id}, this)" data-id="${s.id}">
            <div class="lu-spell-name">${s.name}</div>
            <div class="lu-spell-meta">${s.level === 0 ? "Cantrip" : `Level ${s.level}`}${s.school ? " · " + s.school : ""}</div>
          </div>`).join("")}
        </div>
      </div>
    </div>
    ${navRow("← Back", "Continue →", "lu-step-next", false, "Skip")}`;
}

// Cantrip swap step (optional)
function buildCantripSwapStep(step) {
  const prev = choices[step.id] || {};
  const owned = (opts.owned_spell_ids || []);
  const ownedCantrips = allSpells.filter(s => s.level === 0 && owned.includes(s.id));
  const available = allSpells.filter(s => s.level === 0 && !owned.includes(s.id));
  return `
    <h2 class="lu-step-heading">Swap a Cantrip <em style="font-size:0.8em;opacity:0.7">(optional)</em></h2>
    <p class="lu-step-desc">You may replace one known cantrip with a different one.</p>
    <div class="lu-swap-cols">
      <div class="lu-swap-col">
        <div class="lu-swap-label">Remove</div>
        <div class="lu-spell-grid lu-swap-grid">
          ${ownedCantrips.map(s => `<div class="lu-spell-card ${prev.remove_id === s.id ? 'chosen' : ''}"
            onclick="swapPick('remove', ${s.id}, this)" data-id="${s.id}">
            <div class="lu-spell-name">${s.name}</div>
            <div class="lu-spell-meta">Cantrip${s.school ? " · " + s.school : ""}</div>
          </div>`).join("")}
        </div>
      </div>
      <div class="lu-swap-col">
        <div class="lu-swap-label">Add</div>
        <div class="lu-spell-grid lu-swap-grid">
          ${available.map(s => `<div class="lu-spell-card ${prev.add_id === s.id ? 'chosen' : ''}"
            onclick="swapPick('add', ${s.id}, this)" data-id="${s.id}">
            <div class="lu-spell-name">${s.name}</div>
            <div class="lu-spell-meta">Cantrip${s.school ? " · " + s.school : ""}</div>
          </div>`).join("")}
        </div>
      </div>
    </div>
    ${navRow("← Back", "Continue →", "lu-step-next", false, "Skip")}`;
}

// Card pick step (metamagic, invocations)
function buildCardPickStep(step, options) {
  const prev = choices[step.id] || { keys: [] };
  const owned = step.owned || [];
  return `
    <h2 class="lu-step-heading">${step.label}</h2>
    <p class="lu-step-desc">${step.description || `Choose ${step.pick}.`}</p>
    ${owned.length ? `<div class="lu-owned-tags"><strong>Currently known:</strong> ${owned.map(o => `<span class="lu-choice-tag">${o.name}</span>`).join(" ")}</div>` : ""}
    <div class="lu-feat-grid" id="card-pick-grid">
      ${options.map(opt => `
        <div class="lu-feat-card ${prev.keys.includes(opt.key) ? 'chosen' : ''}"
             onclick="toggleCardPick('${step.id}', '${opt.key}', ${step.pick}, this)" data-key="${opt.key}">
          <div class="lu-feat-name">${opt.name}</div>
          ${opt.cost ? `<div class="lu-feat-cost">${opt.cost}</div>` : ""}
          <div class="lu-feat-desc">${opt.desc || opt.description || ""}</div>
        </div>`).join("")}
    </div>
    <p class="lu-step-desc" style="margin-top:8px">${(prev.keys || []).length}/${step.pick} chosen.</p>
    ${navRow()}`;
}

// Invocation swap step (optional)
function buildInvocationSwapStep(step) {
  const prev = choices[step.id] || {};
  const owned = step.owned || [];
  const available = step.options || [];
  return `
    <h2 class="lu-step-heading">Replace an Invocation <em style="font-size:0.8em;opacity:0.7">(optional)</em></h2>
    <p class="lu-step-desc">You may replace one known Eldritch Invocation with a different eligible one.</p>
    <div class="lu-swap-cols">
      <div class="lu-swap-col">
        <div class="lu-swap-label">Remove (current invocation)</div>
        <div class="lu-feat-grid lu-swap-feat-grid">
          ${owned.map(o => `<div class="lu-feat-card ${prev.remove_key === o.key ? 'chosen' : ''}"
            onclick="invocSwapPick('remove', '${o.key}', this)">
            <div class="lu-feat-name">${o.name}</div>
            <div class="lu-feat-desc">${o.desc || ""}</div>
          </div>`).join("")}
        </div>
      </div>
      <div class="lu-swap-col">
        <div class="lu-swap-label">Add (new invocation)</div>
        <div class="lu-feat-grid lu-swap-feat-grid">
          ${available.map(o => `<div class="lu-feat-card ${prev.add_key === o.key ? 'chosen' : ''}"
            onclick="invocSwapPick('add', '${o.key}', this)">
            <div class="lu-feat-name">${o.name}</div>
            ${o.prereq_level ? `<div class="lu-feat-prereq">Requires Warlock ${o.prereq_level}+${o.prereq_pact ? " + Pact of the " + o.prereq_pact[0].toUpperCase() + o.prereq_pact.slice(1) : ""}</div>` : ""}
            <div class="lu-feat-desc">${o.desc || ""}</div>
          </div>`).join("")}
        </div>
      </div>
    </div>
    ${navRow("← Back", "Continue →", "lu-step-next", false, "Skip")}`;
}

// Mystic Arcanum step (pick 1 high-level Warlock spell)
function buildMysticArcanumStep(step) {
  const prev = choices[step.id] || {};
  const owned = ownedIds();
  const arcSpells = allSpells.filter(s => s.level === step.spell_level && !owned.has(s.id));
  return `
    <h2 class="lu-step-heading">${step.label}</h2>
    <p class="lu-step-desc">${step.description}</p>
    <div class="lu-spell-grid" id="spell-grid">
      ${arcSpells.map(s => `
        <div class="lu-spell-card ${prev.spell_id === s.id ? 'chosen' : ''}"
             onclick="pickArcanum('${step.id}', ${s.id}, this)" data-id="${s.id}">
          <div class="lu-spell-name">${s.name}</div>
          <div class="lu-spell-meta">${ordinalLabel(s.level)} level${s.school ? " · " + s.school : ""}</div>
          ${s.description ? `<div class="lu-spell-desc lu-spell-expand hidden">${s.description}</div>` : ""}
        </div>`).join("")}
    </div>
    ${navRow()}`;
}

// Generic feature choice step
function buildFeatureChoiceStep(step) {
  const prev = choices[step.id] || {};
  return `
    <h2 class="lu-step-heading">${step.feature_name || step.label}</h2>
    <p class="lu-step-desc">${step.description || ""}</p>
    <div class="lu-feat-grid">
      ${(step.options || []).map(o => `
        <div class="lu-feat-card ${prev.choice === o.name ? 'chosen' : ''}"
             onclick="pickFeatureChoice('${step.id}', '${escQ(o.name)}', this)">
          <div class="lu-feat-name">${o.name}</div>
          <div class="lu-feat-desc">${o.description || ""}</div>
        </div>`).join("")}
    </div>
    ${navRow()}`;
}

function buildUnknownStep(step) {
  return `<h2 class="lu-step-heading">${step.label}</h2>
    <p class="lu-step-desc">This step is handled automatically.</p>
    ${navRow()}`;
}

// Aasimar Celestial Revelation — pick 1 of 3
function buildSpeciesRevelationStep(step) {
  const prev = choices[step.id] || {};
  return `
    <h2 class="lu-step-heading">${step.title || step.label}</h2>
    <p class="lu-step-desc">${step.description || ""}</p>
    <div class="lu-feat-grid" id="revelation-grid">
      ${(step.options || []).map(opt => `
        <div class="lu-feat-card ${prev.key === opt.key ? 'chosen' : ''}"
             onclick="pickRevelation('${step.id}', '${opt.key}', '${escQ(opt.name)}', '${escQ(opt.description)}', this)">
          <div class="lu-feat-name">${opt.name}</div>
          <div class="lu-feat-desc">${opt.description}</div>
        </div>`).join("")}
    </div>
    ${navRow()}`;
}

// Species lineage spell notification (informational — spell auto-granted)
function buildSpeciesSpellInfoStep(step) {
  return `
    <h2 class="lu-step-heading">Lineage Spell Granted</h2>
    <div class="lu-info-notice">
      <p>Your lineage grants you <strong>${step.spell_name}</strong> at this level. It has been added to your spell list as Always Prepared.</p>
    </div>
    ${navRow()}`;
}

// Shared spell card
function spellCard(s, stepId, preChosen = false) {
  const lvlLabel = s.level === 0 ? "Cantrip" : `Level ${s.level}`;
  return `<div class="lu-spell-card ${preChosen ? "chosen" : ""}" data-id="${s.id}"
    onclick="toggleSpellPick('${stepId}', ${s.id}, this)">
    <div class="lu-spell-name">${s.name}</div>
    <div class="lu-spell-meta">${lvlLabel}${s.school ? " · " + s.school : ""}${s.concentration ? " · Conc." : ""}${s.ritual ? " · Ritual" : ""}</div>
    <div class="lu-spell-stats">
      ${s.casting_time ? `<span>${s.casting_time}</span>` : ""}
      ${s.spell_range ? `<span>${s.spell_range}</span>` : ""}
      ${s.duration ? `<span>${s.duration}</span>` : ""}
    </div>
  </div>`;
}

// Escape single quotes for inline handlers
function escQ(s) { return (s || "").replace(/'/g, "\\'"); }

// ---------------------------------------------------------------------------
// Step Listeners (attach after innerHTML set)
// ---------------------------------------------------------------------------
function attachStepListeners(step) {
  // Spell filter buttons
  const filterEl = document.getElementById("spell-filter");
  if (filterEl) {
    filterEl.querySelectorAll(".lu-filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        filterEl.querySelectorAll(".lu-filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
      });
    });
  }
  // HP method display
  if (step.kind === "hp") {
    updateHpDisplay();
  }
}

// ---------------------------------------------------------------------------
// Choice handlers
// ---------------------------------------------------------------------------

function setHpMethod(method) {
  hpMethod = method;
  choices["hp"] = { method, die_value: hpDieValue };
  const step = steps.find(s => s.kind === "hp");
  if (step) {
    document.getElementById("lu-step-host").innerHTML = buildHpStep(step);
    attachStepListeners(step);
  }
}

function rollHpDie(hitDie) {
  hpDieValue = Math.ceil(Math.random() * hitDie);
  choices["hp"] = { method: hpMethod, die_value: hpDieValue };
  const step = steps.find(s => s.kind === "hp");
  if (step) {
    document.getElementById("lu-step-host").innerHTML = buildHpStep(step);
    attachStepListeners(step);
  }
}

function setHpManual(val) {
  hpDieValue = parseInt(val) || null;
  choices["hp"] = { method: hpMethod, die_value: hpDieValue };
  const step = steps.find(s => s.kind === "hp");
  if (step) {
    const preview = document.getElementById("hp-total-preview");
    if (preview) preview.innerHTML = buildHpPreview(step);
  }
}

function updateHpDisplay() {
  const step = steps.find(s => s.kind === "hp");
  if (!step) return;
  document.querySelectorAll('.lu-hp-method').forEach(el => {
    const input = el.querySelector('input[type="radio"]');
    if (input) el.classList.toggle('selected', input.value === hpMethod);
  });
}

function pickSubclass(id, name, el) {
  const stepId = steps.find(s => s.kind === "subclass")?.id;
  if (!stepId) return;
  choices[stepId] = { subclass_id: id, subclass_name: name };
  document.querySelectorAll(".lu-subclass-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function setAsiMode(mode) {
  const stepId = steps.find(s => s.kind === "asi")?.id;
  if (!stepId) return;
  choices[stepId] = { ...(choices[stepId] || {}), mode };
  document.querySelectorAll(".lu-asi-mode").forEach(m => m.classList.remove("active"));
  document.querySelectorAll(`input[value="${mode}"]`)[0]?.closest(".lu-asi-mode")?.classList.add("active");
  document.getElementById("asi-sub-plus2").style.display = mode === "+2" ? "" : "none";
  document.getElementById("asi-sub-plus1").style.display = mode === "+1+1" ? "" : "none";
  document.getElementById("asi-sub-feat").style.display = mode === "feat" ? "" : "none";
}

function setAsiAbility(ab) {
  const stepId = steps.find(s => s.kind === "asi")?.id;
  if (!stepId) return;
  choices[stepId] = { ...(choices[stepId] || {}), ability: ab };
  document.querySelectorAll("#asi-sub-plus2 .lu-ability-btn").forEach(b => {
    b.classList.toggle("chosen", b.dataset.ability === ab);
  });
}

function toggleAsiAbility(ab) {
  const stepId = steps.find(s => s.kind === "asi")?.id;
  if (!stepId) return;
  const cur = choices[stepId] || {};
  const abilities = cur.abilities ? [...cur.abilities] : [];
  const idx = abilities.indexOf(ab);
  if (idx >= 0) {
    abilities.splice(idx, 1);
  } else {
    if (abilities.length >= 2) { toast("Only 2 abilities for +1/+1."); return; }
    abilities.push(ab);
  }
  choices[stepId] = { ...cur, abilities };
  document.querySelectorAll("#asi-sub-plus1 .lu-ability-btn").forEach(b => {
    b.classList.toggle("chosen", abilities.includes(b.dataset.ability));
  });
}

function pickAsiFeat(featId, el) {
  const stepId = steps.find(s => s.kind === "asi")?.id;
  if (!stepId) return;
  choices[stepId] = { ...(choices[stepId] || {}), feat_id: featId };
  document.querySelectorAll("#asi-sub-feat .lu-feat-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function pickFeat(stepId, keyName, featId, el) {
  choices[stepId] = { [keyName]: featId };
  el.closest(".lu-feat-grid").querySelectorAll(".lu-feat-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function toggleSkill(stepId, skill, max, el) {
  const cur = choices[stepId] || { skills: [] };
  const skills = [...cur.skills];
  const idx = skills.indexOf(skill);
  if (idx >= 0) {
    skills.splice(idx, 1);
    el.classList.remove("chosen");
  } else {
    if (skills.length >= max) { toast(`Only ${max} skill(s) allowed.`); return; }
    skills.push(skill);
    el.classList.add("chosen");
  }
  choices[stepId] = { skills };
  const step = steps.find(s => s.id === stepId);
  document.querySelector(".lu-step-desc:last-of-type") && null;
  // Update count display - rebuild desc
  const descs = document.querySelectorAll(".lu-step-desc");
  descs.forEach(d => { if (d.textContent.includes("/")) d.textContent = `${skills.length}/${max} chosen.`; });
}

function setSpellFilter(level, btn) {
  document.querySelectorAll(".lu-filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  const grid = document.getElementById("spell-grid");
  if (!grid) return;
  grid.querySelectorAll(".lu-spell-card").forEach(card => {
    const name = card.querySelector(".lu-spell-meta")?.textContent || "";
    const isCantrip = name.startsWith("Cantrip");
    const slMatch = name.match(/Level (\d+)/);
    const cardLevel = isCantrip ? 0 : (slMatch ? parseInt(slMatch[1]) : null);
    card.style.display = (level === null || cardLevel === level) ? "" : "none";
  });
}

function toggleSpellPick(stepId, spellId, el) {
  const step = steps.find(s => s.id === stepId);
  if (!step) return;
  const cur = choices[stepId] || { spell_ids: [] };
  const ids = [...cur.spell_ids];
  const idx = ids.indexOf(spellId);
  if (idx >= 0) {
    ids.splice(idx, 1);
    el.classList.remove("chosen");
  } else {
    const needed = step.pick || 1;
    if (ids.length >= needed) { toast(`You can only choose ${needed} spell(s) here.`); return; }
    ids.push(spellId);
    el.classList.add("chosen");
  }
  choices[stepId] = { spell_ids: ids };
  const countEl = document.getElementById("spell-count");
  if (countEl) countEl.textContent = `${ids.length}/${step.pick || 1} chosen`;
}

function swapPick(side, spellId, el) {
  const step = steps[stepIdx - 1];
  if (!step) return;
  const cur = choices[step.id] || {};
  const key = side === "remove" ? "remove_id" : "add_id";
  choices[step.id] = { ...cur, [key]: spellId };
  const gridId = side === "remove" ? "swap-remove-grid" : "swap-add-grid";
  document.getElementById(gridId)?.querySelectorAll(".lu-spell-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function toggleCardPick(stepId, key, max, el) {
  const cur = choices[stepId] || { keys: [] };
  const keys = [...cur.keys];
  const idx = keys.indexOf(key);
  if (idx >= 0) {
    keys.splice(idx, 1);
    el.classList.remove("chosen");
  } else {
    if (keys.length >= max) { toast(`Only ${max} option(s) allowed.`); return; }
    keys.push(key);
    el.classList.add("chosen");
  }
  choices[stepId] = { keys };
  const descs = document.querySelectorAll(".lu-step-desc");
  descs.forEach(d => { if (d.textContent.includes("/")) d.textContent = `${keys.length}/${max} chosen.`; });
}

function invocSwapPick(side, key, el) {
  const step = steps[stepIdx - 1];
  if (!step) return;
  const cur = choices[step.id] || {};
  const k = side === "remove" ? "remove_key" : "add_key";
  choices[step.id] = { ...cur, [k]: key };
  const colClass = side === "remove" ? ".lu-swap-col:first-child" : ".lu-swap-col:last-child";
  document.querySelector(colClass)?.querySelectorAll(".lu-feat-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function pickArcanum(stepId, spellId, el) {
  choices[stepId] = { spell_id: spellId };
  document.getElementById("spell-grid")?.querySelectorAll(".lu-spell-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function pickFeatureChoice(stepId, choiceValue, el) {
  choices[stepId] = { choice: choiceValue };
  el.closest(".lu-feat-grid")?.querySelectorAll(".lu-feat-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function pickRevelation(stepId, key, name, description, el) {
  choices[stepId] = { key, name, description };
  document.getElementById("revelation-grid")?.querySelectorAll(".lu-feat-card").forEach(c => c.classList.remove("chosen"));
  el.classList.add("chosen");
}

function skipStep() {
  const step = steps[stepIdx - 1];
  if (step) delete choices[step.id];
  stepIdx++;
  if (stepIdx > steps.length) {
    renderConfirm();
    return;
  }
  renderPips();
  renderStep(steps[stepIdx - 1]);
  showPanel("host");
}

// ---------------------------------------------------------------------------
// Confirm step
// ---------------------------------------------------------------------------
function renderConfirm() {
  renderPips();
  const lines = [];

  // HP
  const hpPayload = choices["hp"] || {};
  const hpStep = steps.find(s => s.kind === "hp");
  if (hpStep) {
    const avg = hpStep.average;
    const draconic = hpStep.draconic_bonus || 0;
    let die = hpPayload.method === "average" ? avg : (hpPayload.die_value || avg);
    if (hpPayload.method === "roll") die = Math.max(die, avg);
    const total = die + hpStep.con_mod + draconic;
    const con = hpStep.con_mod >= 0 ? `+${hpStep.con_mod}` : `${hpStep.con_mod}`;
    lines.push(confirmRow("Hit Points", `+${total} (${die} die ${con} CON${draconic?` +${draconic} Draconic`:""})`));
  }

  // Subclass
  for (const step of steps.filter(s => s.kind === "subclass")) {
    const p = choices[step.id];
    if (p?.subclass_name) lines.push(confirmRow("Subclass", p.subclass_name));
  }

  // ASI
  for (const step of steps.filter(s => s.kind === "asi")) {
    const p = choices[step.id];
    if (!p) continue;
    if (p.mode === "+2") lines.push(confirmRow("ASI", `+2 ${abilityName(p.ability)}`));
    else if (p.mode === "+1+1") lines.push(confirmRow("ASI", `+1 ${p.abilities?.map(abilityName).join(", +1 ") || ""}`));
    else if (p.mode === "feat") {
      const feat = opts.general_feats?.find(f => f.id === p.feat_id);
      lines.push(confirmRow("Feat", feat?.name || p.feat_id));
    }
  }

  // Epic Boon
  for (const step of steps.filter(s => s.kind === "epic_boon")) {
    const p = choices[step.id];
    const feat = opts.epic_boons?.find(f => f.id === p?.feat_id);
    if (feat) lines.push(confirmRow("Epic Boon", feat.name));
  }

  // Fighting Style
  for (const step of steps.filter(s => s.kind === "fighting_style" || s.kind === "fighting_style_swap")) {
    const p = choices[step.id];
    const feat = opts.fighting_styles?.find(f => f.id === p?.feat_id);
    if (feat) lines.push(confirmRow("Fighting Style", feat.name));
  }

  // Expertise
  for (const step of steps.filter(s => s.kind === "expertise")) {
    const p = choices[step.id];
    if (p?.skills?.length) lines.push(confirmRow("Expertise", p.skills.join(", ")));
  }

  // Cantrips
  for (const step of steps.filter(s => s.kind === "cantrips_new")) {
    const p = choices[step.id];
    const names = (p?.spell_ids || []).map(id => allSpells.find(s => s.id === id)?.name || id).join(", ");
    if (names) lines.push(confirmRow("New Cantrips", names));
  }

  // Spells / Spellbook
  for (const step of steps.filter(s => s.kind === "spells_new" || s.kind === "wizard_spellbook")) {
    const p = choices[step.id];
    const names = (p?.spell_ids || []).map(id => allSpells.find(s => s.id === id)?.name || id).join(", ");
    if (names) lines.push(confirmRow(step.kind === "wizard_spellbook" ? "Spellbook" : "New Spells", names));
  }

  // Spell swap
  for (const step of steps.filter(s => s.kind === "spell_swap")) {
    const p = choices[step.id];
    if (p?.remove_id && p?.add_id) {
      const from = allSpells.find(s => s.id === p.remove_id)?.name;
      const to   = allSpells.find(s => s.id === p.add_id)?.name;
      if (from && to) lines.push(confirmRow("Spell Swap", `${from} → ${to}`));
    }
  }

  // Metamagic
  for (const step of steps.filter(s => s.kind === "metamagic")) {
    const p = choices[step.id];
    if (p?.keys?.length) lines.push(confirmRow("Metamagic", p.keys.join(", ")));
  }

  // Invocations
  for (const step of steps.filter(s => s.kind === "invocations_new")) {
    const p = choices[step.id];
    if (p?.keys?.length) lines.push(confirmRow("New Invocations", p.keys.join(", ")));
  }

  // Invocation swap
  for (const step of steps.filter(s => s.kind === "invocation_swap")) {
    const p = choices[step.id];
    if (p?.remove_key && p?.add_key) lines.push(confirmRow("Invocation Swap", `${p.remove_key} → ${p.add_key}`));
  }

  // Mystic Arcanum
  for (const step of steps.filter(s => s.kind === "mystic_arcanum")) {
    const p = choices[step.id];
    if (p?.spell_id) {
      const name = allSpells.find(s => s.id === p.spell_id)?.name || p.spell_id;
      lines.push(confirmRow("Mystic Arcanum", name));
    }
  }

  // Feature choices
  for (const step of steps.filter(s => s.kind === "feature_choice")) {
    const p = choices[step.id];
    if (p?.choice) lines.push(confirmRow(step.feature_name || step.label, p.choice));
  }

  lines.push(confirmRow("New Level", `<span style="font-size:1.4rem;color:var(--color-gold)">${opts.next_level}</span>`));

  document.getElementById("lu-step-host").innerHTML = `
    <h2 class="lu-step-heading">Ready to Level Up</h2>
    <div class="lu-confirm-summary">${lines.join("")}</div>
    <div class="lu-nav">
      <button class="btn-secondary" onclick="luBack()">← Back</button>
      <button class="btn-levelup" onclick="luApply()" id="lu-apply-btn">⬆ Level Up</button>
    </div>`;
  showPanel("host");
}

function confirmRow(label, value) {
  return `<div class="lu-confirm-row">
    <span class="lu-confirm-label">${label}</span>
    <span>${value}</span>
  </div>`;
}

// ---------------------------------------------------------------------------
// Apply level-up
// ---------------------------------------------------------------------------
async function luApply() {
  const btn = document.getElementById("lu-apply-btn");
  btn.disabled = true;
  btn.textContent = "Applying…";

  // Build HP payload
  const hpStep = steps.find(s => s.kind === "hp");
  const hpPayload = choices["hp"] || {};
  const hpData = {
    method: hpPayload.method || "average",
    die_value: hpPayload.die_value || null,
    draconic_bonus: hpStep?.draconic_bonus || 0,
  };

  // Build choices payload (exclude the transient "hp" key used locally)
  const finalChoices = {};
  for (const [k, v] of Object.entries(choices)) {
    if (k !== "hp") finalChoices[k] = v;
  }

  try {
    const result = await api("POST", `/api/characters/${charId}/levelup`, {
      hp: hpData,
      choices: finalChoices,
    });

    document.getElementById("lu-step-done").querySelector(".lu-done-title").textContent =
      `${opts.character_name} is now Level ${result.new_level}!`;
    document.getElementById("lu-done-sub").textContent =
      `HP maximum is now ${result.hp_max}. (+${result.hp_gained} this level)`;

    const autoEl = document.getElementById("lu-done-auto-spells");
    if (result.auto_added_spells?.length) {
      autoEl.innerHTML = `<p class="lu-auto-spell-label">Auto-granted always-prepared spells:</p>
        ${result.auto_added_spells.map(n => `<span class="lu-choice-tag">${n}</span>`).join("")}`;
      autoEl.classList.remove("hidden");
    }

    document.getElementById("lu-sheet-link").href = `/characters/${charId}/sheet`;
    document.getElementById("lu-steps").innerHTML = "";
    document.getElementById("lu-subtitle").textContent = `${opts.class_name} · Level ${result.new_level}`;
    showPanel("done");
    show("lu-step-done");
  } catch(e) {
    toast("⚠ " + e.message, 5000);
    btn.disabled = false;
    btn.textContent = "⬆ Level Up";
  }
}

boot();
