// encounter.js — Phase 5.5 — token-first mobile encounter page
// ─────────────────────────────────────────────────────────────

// ── State ────────────────────────────────────────────────────
let myCharIds = [];           // character IDs belonging to this player
let encounterState = { encounter_active: false, initiative_phase: false, current_round: 1, combatants: [] };
let myActions = [];           // cached from /encounter-actions (Tasks 9+)
let actionsLoaded = false;
let resourcesLoaded = false;
let myEncResources = [];
let activeToken = null;       // 'action'|'bonus'|'reaction'|'move'|null  (Tasks 9+)
let selectedActionIdx = null; // index into myActions  (Tasks 9+)
let movementAmount = 5;       // current move stepper value  (Task 10)
let myActiveCombatantId = null; // combatant_id when it's my turn

// ── WebSocket ─────────────────────────────────────────────────
let ws = null;
let wsReconnectDelay = 1000;
let wsActive = false;

function connectWS() {
  if (!wsActive) return;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${proto}//${location.host}/ws/encounter`);

  ws.onopen = () => {
    wsReconnectDelay = 1000;
    document.getElementById('enc-reconnect').style.display = 'none';
  };

  ws.onmessage = (event) => {
    try {
      encounterState = JSON.parse(event.data);
      render();
    } catch (e) { /* ignore parse errors */ }
  };

  ws.onclose = () => {
    if (!wsActive) return;
    document.getElementById('enc-reconnect').style.display = 'block';
    setTimeout(() => {
      wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000);
      connectWS();
    }, wsReconnectDelay);
  };

  ws.onerror = () => ws.close();
}

// ── Toast ────────────────────────────────────────────────────
function toast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

// ── HTML escape ───────────────────────────────────────────────
function _esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ──────────────────────────────────────────────────────
async function init() {
  const meRes = await fetch('/auth/me');
  if (!meRes.ok) { window.location.href = '/'; return; }

  const charsRes = await fetch('/api/characters');
  if (charsRes.ok) {
    const chars = await charsRes.json();
    myCharIds = chars.filter(c => c.is_complete).map(c => c.id);
  }

  // Fetch initial state via HTTP before WS connects
  try {
    const stateRes = await fetch('/api/encounter/state');
    if (stateRes.ok) {
      encounterState = await stateRes.json();
      render();
    }
  } catch (e) { /* ignore */ }

  wsActive = true;
  connectWS();
  window.addEventListener('beforeunload', () => {
    wsActive = false;
    if (ws) ws.close();
  });
}

// ── Main render ───────────────────────────────────────────────
function render() {
  const { encounter_active, initiative_phase, current_round, current_turn_combatant_id, combatants } = encounterState;

  const statusEl = document.getElementById('enc-status');
  const bannerEl = document.getElementById('enc-turn-banner');
  const tokenGrid = document.getElementById('enc-token-grid');
  const endTurnEl = document.getElementById('enc-end-turn');
  const orderEl = document.getElementById('enc-order');

  if (!encounter_active) {
    _clearActivePanels();
    statusEl.innerHTML = `<h2 style="text-align:center;margin:2rem 0 0.5rem">No encounter in progress</h2><p style="text-align:center;color:var(--ink-soft)">The DM will start an encounter when combat begins.</p>`;
    bannerEl.innerHTML = '';
    tokenGrid.style.display = 'none';
    endTurnEl.style.display = 'none';
    orderEl.innerHTML = '';
    return;
  }

  if (initiative_phase) {
    _clearActivePanels();
    statusEl.innerHTML = `<h2 style="text-align:center;margin:2rem 0 0.5rem">Initiative Phase</h2><p style="text-align:center;color:var(--ink-soft)">The DM is collecting initiative rolls. Stand by…</p>`;
    bannerEl.innerHTML = '';
    tokenGrid.style.display = 'none';
    endTurnEl.style.display = 'none';
    orderEl.innerHTML = '';
    return;
  }

  statusEl.innerHTML = '';

  // Determine if it's my turn
  const currentCombatant = combatants.find(c => c.combatant_id === current_turn_combatant_id);
  const myActiveCombatant = combatants.find(
    c => myCharIds.includes(c.character_id) && c.combatant_id === current_turn_combatant_id
  );
  const isMyTurn = !!myActiveCombatant;

  if (isMyTurn) {
    myActiveCombatantId = myActiveCombatant.combatant_id;
    bannerEl.innerHTML = `<div style="background:var(--gold,#c8a84b);color:#1a0e00;padding:0.65rem;border-radius:6px;font-weight:bold;font-size:1.05rem;text-align:center">⚔ YOUR TURN — Round ${current_round}</div>`;
    tokenGrid.style.display = 'grid';
    endTurnEl.style.display = 'block';
    _updateTokens(myActiveCombatant);

    if (!actionsLoaded && myActiveCombatant.character_id) {
      loadActions(myActiveCombatant.character_id);
    }
    if (!resourcesLoaded && myActiveCombatant.character_id) {
      loadEncResources(myActiveCombatant.character_id);
    }
  } else {
    myActiveCombatantId = null;
    _clearActivePanels();
    const whose = currentCombatant ? _esc(currentCombatant.name) : '—';
    bannerEl.innerHTML = `<div style="text-align:center;color:var(--ink-soft);padding:0.4rem">Round ${current_round} — <em>${whose}</em>'s turn</div>`;
    tokenGrid.style.display = 'none';
    endTurnEl.style.display = 'none';
  }

  // Initiative order list (always shown when encounter is active)
  orderEl.innerHTML = `<div style="font-size:0.8rem;font-weight:bold;color:var(--ink-soft);margin-bottom:0.25rem">INITIATIVE ORDER</div>` +
    combatants.map(c => {
      const isActive = c.combatant_id === current_turn_combatant_id;
      const isMine = myCharIds.includes(c.character_id);
      const hp = c.hp_current != null && c.hp_max != null ? ` ${c.hp_current}/${c.hp_max} HP` : '';
      const conds = (c.conditions || []).map(cd => {
        const label = cd.startsWith('Exhaustion:') ? `Exhaustion ${cd.split(':')[1]}` : cd;
        return `<span style="font-size:0.7rem;padding:0.1rem 0.3rem;background:var(--rubric,#8b0000);color:white;border-radius:2px">${_esc(label)}</span>`;
      }).join(' ');
      return `<div style="display:flex;align-items:center;gap:0.4rem;padding:0.3rem 0.4rem;border-radius:4px;${isActive ? 'background:var(--parchment-bright,#f4e8c8);border:1px solid var(--gold)' : ''}">
        <span style="min-width:1.4rem;font-weight:bold;color:var(--ink-soft)">${c.turn_order ?? '—'}.</span>
        <span style="${isActive ? 'font-weight:bold' : ''}">${_esc(c.name)}${isMine ? ' <small style="color:var(--ink-soft)">(You)</small>' : ''}</span>
        ${hp ? `<span style="font-size:0.8rem;color:var(--ink-soft);margin-left:auto">${hp}</span>` : ''}
        ${conds}
      </div>`;
    }).join('');
}

// ── Panel helpers ─────────────────────────────────────────────
function _clearActivePanels() {
  const actionList = document.getElementById('enc-action-list');
  const movePanel = document.getElementById('enc-move-panel');
  const confirm = document.getElementById('enc-confirm');
  const resourcePanel = document.getElementById('enc-resource-panel');
  if (actionList) { actionList.style.display = 'none'; actionList.innerHTML = ''; }
  if (movePanel) movePanel.style.display = 'none';
  if (confirm) confirm.style.display = 'none';
  if (resourcePanel) resourcePanel.innerHTML = '';
  activeToken = null;
  selectedActionIdx = null;
  actionsLoaded = false;
  myActions = [];
  resourcesLoaded = false;
  myEncResources = [];
}

function _updateTokens(combatant) {
  const { action_used, bonus_action_used, reaction_used, movement_remaining } = combatant;
  const tokAction = document.getElementById('tok-action');
  const tokBonus = document.getElementById('tok-bonus');
  const tokReaction = document.getElementById('tok-reaction');
  const tokMove = document.getElementById('tok-move');
  const tokMoveFt = document.getElementById('tok-move-ft');

  _setTokenState(tokAction, action_used, 'action');
  _setTokenState(tokBonus, bonus_action_used, 'bonus');
  _setTokenState(tokReaction, reaction_used, 'reaction');

  const moveExhausted = (movement_remaining ?? 0) <= 0;
  _setTokenState(tokMove, moveExhausted, 'move');
  if (tokMoveFt) tokMoveFt.textContent = movement_remaining != null ? `${movement_remaining} ft left` : '';
}

function _setTokenState(btn, used, type) {
  if (!btn) return;
  if (used) {
    btn.className = 'enc-token used';
    btn.onclick = null;
  } else if (activeToken === type) {
    btn.className = 'enc-token active';
    btn.onclick = () => tapToken(type);
  } else {
    btn.className = 'enc-token';
    btn.onclick = () => tapToken(type);
  }
}

// ── Resources ─────────────────────────────────────────────────
async function loadEncResources(charId) {
  try {
    const res = await fetch(`/api/characters/${charId}/resources`);
    if (!res.ok) return;
    myEncResources = await res.json();
    resourcesLoaded = true;
    renderEncResources(charId);
  } catch (e) { /* ignore */ }
}

function renderEncResources(charId) {
  const panel = document.getElementById('enc-resource-panel');
  if (!panel || !myEncResources.length) return;
  panel.innerHTML = `<div style="font-size:0.8rem;font-weight:bold;color:var(--ink-soft);margin-bottom:0.25rem">RESOURCES</div>` +
    myEncResources.map(r => `
      <div style="display:flex;align-items:center;gap:0.35rem;margin-bottom:0.2rem;font-size:0.85rem">
        <span style="min-width:8rem;font-weight:bold">${_esc(r.label)}</span>
        <span>${Array.from({length: r.max_uses}, (_, i) => `<button
          onclick="spendEncResource(${charId}, ${r.id}, ${i < r.remaining})"
          style="background:none;border:none;font-size:1rem;cursor:${i < r.remaining ? 'pointer' : 'default'};color:${i < r.remaining ? 'var(--gold-deep,#6b4a18)' : 'var(--ink-faded,#9a8070)'}">●</button>`
        ).join('')}</span>
        <small style="color:var(--ink-soft)">(${_esc(r.rest_type)})</small>
      </div>`
    ).join('');
}

async function spendEncResource(charId, resourceId, available) {
  if (!available) return;
  try {
    const res = await fetch(`/api/characters/${charId}/resources/spend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_id: resourceId, amount: 1 }),
    });
    if (!res.ok) { toast('Could not spend resource'); return; }
    await loadEncResources(charId);
  } catch (e) { toast('Connection error'); }
}

// ── End Turn ─────────────────────────────────────────────────
async function doEndTurn() {
  if (!myActiveCombatantId) return;
  try {
    const res = await fetch('/api/characters/encounter/end-turn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: myActiveCombatantId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      toast(err.detail || 'Could not end turn');
    }
    // WS will push the state update automatically
  } catch (e) { toast('Connection error'); }
}

// ── Action loading ────────────────────────────────────────────
async function loadActions(charId) {
  try {
    const res = await fetch(`/api/characters/${charId}/encounter-actions`);
    if (!res.ok) return;
    myActions = await res.json();
    actionsLoaded = true;
    // Inject class ability resources as action list entries
    _injectResourceAbilities();
  } catch (e) { /* ignore */ }
}

function _injectResourceAbilities() {
  for (const r of myEncResources) {
    const key = `ability:${r.resource_key}`;
    if (myActions.find(a => a._key === key)) continue;
    myActions.push({
      _key: key,
      type: 'ability',
      name: r.label,
      resource_id: r.id,
      resource_key: r.resource_key,
      cost: { action: true, bonus_action: false, spell_slot: null },
      max_uses: r.max_uses,
      remaining: r.remaining,
      rest_type: r.rest_type,
      description: '',
      attack_bonus: null,
      attack_bonus_display: null,
      save_dc: null,
      save_ability: null,
      damage: '',
      range: '',
      level: null,
      school: null,
    });
  }
}

// ── Token tap ─────────────────────────────────────────────────
function tapToken(tokenType) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  if (!combatant) return;

  // Don't allow tapping already-used tokens
  if (tokenType === 'action' && combatant.action_used) return;
  if (tokenType === 'bonus' && combatant.bonus_action_used) return;
  if (tokenType === 'reaction' && combatant.reaction_used) return;
  if (tokenType === 'move' && (combatant.movement_remaining ?? 0) <= 0) return;

  // Toggle: tapping the active token closes the panel
  if (activeToken === tokenType) {
    activeToken = null;
    selectedActionIdx = null;
    document.getElementById('enc-action-list').style.display = 'none';
    document.getElementById('enc-move-panel').style.display = 'none';
    document.getElementById('enc-confirm').style.display = 'none';
    _updateTokens(combatant);
    return;
  }

  activeToken = tokenType;
  selectedActionIdx = null;
  document.getElementById('enc-confirm').style.display = 'none';
  _updateTokens(combatant);

  if (tokenType === 'move') {
    document.getElementById('enc-action-list').style.display = 'none';
    renderMovePanel(combatant);  // implemented in Task 10
  } else {
    document.getElementById('enc-move-panel').style.display = 'none';
    renderActionList(tokenType, combatant);
  }
}

// ── Action list ───────────────────────────────────────────────
function renderActionList(tokenType, combatant) {
  const el = document.getElementById('enc-action-list');
  el.style.display = 'block';

  const isAction = tokenType === 'action';
  const isBonus = tokenType === 'bonus';

  // Filter myActions by which token is tapped
  const attacks = isAction ? myActions.filter(a => a.type === 'attack') : [];
  const cantrips = isAction ? myActions.filter(a => a.type === 'spell' && a.level === 0) : [];
  const spells = (isAction || isBonus)
    ? myActions.filter(a => a.type === 'spell' && a.level > 0 && (isAction ? a.cost.action : a.cost.bonus_action))
    : [];
  const abilities = myActions.filter(a =>
    a.type === 'ability' && (isAction ? a.cost.action : (isBonus ? a.cost.bonus_action : a.cost.reaction))
  );

  const section = (title, items) => {
    if (!items.length) return '';
    return `<div style="background:var(--parchment-bright,#f4e8c8);padding:0.25rem 0.5rem;font-size:0.7rem;font-weight:bold;letter-spacing:0.05em;color:var(--ink-soft)">${_esc(title)}</div>` +
      items.map(a => {
        const globalIdx = myActions.indexOf(a);
        const exhausted = a.type === 'ability' && (a.remaining ?? 1) <= 0;
        const statStr = a.attack_bonus_display
          ? `${a.attack_bonus_display} · ${a.damage || '—'}`
          : (a.save_dc ? `DC ${a.save_dc} ${a.save_ability || ''}` : (a.damage || ''));
        const rightLabel = a.type === 'ability'
          ? `<span style="font-size:0.75rem;color:${exhausted ? '#ccc' : 'var(--ink-soft)'}">${a.remaining ?? 0}/${a.max_uses ?? 1}</span>`
          : (statStr ? `<span style="font-size:0.75rem;color:var(--ink-soft)">${_esc(statStr)}</span>` : '');
        return `<div onclick="${exhausted ? '' : `selectAction(${globalIdx})`}"
          style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.5rem;border-bottom:1px solid #eee;cursor:${exhausted ? 'default' : 'pointer'};opacity:${exhausted ? '0.4' : '1'}">
          <span style="flex:1">${_esc(a.name)}${a.level > 0 ? ` <small>(L${a.level})</small>` : ''}</span>
          ${rightLabel}
        </div>`;
      }).join('');
  };

  let html = `<div style="border:1px solid var(--gold);border-radius:6px;overflow:hidden;background:white">`;
  html += section('ATTACKS', attacks);
  html += section('CANTRIPS', cantrips);
  html += section('SPELLS', spells);
  html += section('ABILITIES', abilities);
  html += `<div onclick="selectAction(-1)" style="padding:0.4rem 0.5rem;color:var(--ink-soft);cursor:pointer;font-style:italic;border-top:1px solid #eee">— Skip (use ${_esc(tokenType)}, do nothing)</div>`;
  html += '</div>';
  el.innerHTML = html;
}

// ── Confirm panel ─────────────────────────────────────────────
function selectAction(idx) {
  selectedActionIdx = idx;
  const confirmEl = document.getElementById('enc-confirm');
  confirmEl.style.display = 'block';

  if (idx === -1) {
    confirmEl.innerHTML = `<div style="border:1px solid var(--gold);border-radius:6px;padding:0.6rem">
      <div style="font-weight:bold;margin-bottom:0.4rem">— Skip</div>
      <div style="font-size:0.8rem;color:var(--ink-soft);margin-bottom:0.5rem">Use your ${_esc(activeToken)} without doing anything.</div>
      <div style="display:flex;gap:0.4rem">
        <button onclick="doUseAction(-1)" style="flex:1;padding:0.5rem;background:var(--ink);color:white;border:none;border-radius:4px;cursor:pointer;font-weight:bold">✓ Confirm Skip</button>
        <button onclick="closeConfirm()" style="padding:0.5rem 0.7rem;background:#eee;border:1px solid #ccc;border-radius:4px;cursor:pointer">← Back</button>
      </div>
    </div>`;
    return;
  }

  const action = myActions[idx];
  if (!action) return;

  let statsHtml = '';
  let slotPickerHtml = '';

  if (action.type === 'attack') {
    statsHtml = `
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Attack Bonus:</strong> ${_esc(action.attack_bonus_display || '—')}</p>
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Damage:</strong> ${_esc(action.damage || '—')}</p>
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Range:</strong> ${_esc(action.range || '5 ft.')}</p>
      ${(action.properties || []).length ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Properties:</strong> ${action.properties.map(_esc).join(', ')}</p>` : ''}
      ${action.mastery_property ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Mastery:</strong> ${_esc(action.mastery_property)}</p>` : ''}`;
  } else if (action.type === 'spell') {
    const lvlStr = action.level === 0 ? 'Cantrip' : `Level ${action.level}`;
    statsHtml = `
      <p style="margin:0.2rem 0;font-size:0.78rem;color:var(--ink-soft)"><em>${_esc(lvlStr)} ${_esc(action.school || '')}</em></p>
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Range:</strong> ${_esc(action.range || '—')}</p>
      ${action.duration ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Duration:</strong> ${_esc(action.duration)}${action.concentration ? ' (Concentration)' : ''}</p>` : ''}
      ${action.save_dc ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Save DC:</strong> ${action.save_dc} ${_esc(action.save_ability || '')}</p>` : ''}
      ${action.attack_bonus_display ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Spell Attack:</strong> ${_esc(action.attack_bonus_display)}</p>` : ''}`;

    if (action.level > 0) {
      slotPickerHtml = `<div style="margin:0.4rem 0;font-size:0.82rem"><strong>Slot:</strong>
        <select id="slot-pick" style="margin-left:0.3rem;font-size:0.82rem">
          ${_buildSlotOptions(action.level)}
        </select>
      </div>`;
    }

    if (action.description) {
      const desc = action.description.length > 300 ? action.description.slice(0, 297) + '…' : action.description;
      statsHtml += `<details style="margin-top:0.4rem"><summary style="font-size:0.8rem;cursor:pointer">Description</summary><p style="font-size:0.78rem;white-space:pre-wrap">${_esc(desc)}</p></details>`;
    }
  } else if (action.type === 'ability') {
    statsHtml = `
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Uses:</strong> ${action.remaining ?? 0}/${action.max_uses ?? 1} (${_esc(action.rest_type || '')} rest)</p>
      ${action.description ? `<p style="margin:0.2rem 0;font-size:0.82rem">${_esc(action.description)}</p>` : ''}`;
  }

  const costParts = [];
  if (activeToken === 'action') costParts.push('1 Action');
  if (activeToken === 'bonus') costParts.push('1 Bonus Action');
  if (activeToken === 'reaction') costParts.push('1 Reaction');
  if (action.type === 'ability' && action.resource_id) costParts.push(`1 ${_esc(action.name)} use`);

  confirmEl.innerHTML = `<div style="border:2px solid var(--gold);border-radius:6px;padding:0.6rem">
    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:0.35rem">
      <strong style="font-size:1rem">${_esc(action.name)}</strong>
      <button onclick="closeConfirm()" style="background:none;border:none;cursor:pointer;font-size:0.85rem">✕</button>
    </div>
    ${statsHtml}
    ${slotPickerHtml}
    <p style="font-size:0.75rem;color:var(--ink-soft);margin:0.4rem 0">Costs: ${costParts.join(' + ') || '—'}</p>
    <div style="display:flex;gap:0.4rem;margin-top:0.5rem">
      <button onclick="doUseAction(${idx})" style="flex:1;padding:0.55rem;background:var(--gold,#c8a84b);color:#1a0e00;border:none;border-radius:5px;font-weight:bold;cursor:pointer">✓ Use It</button>
      <button onclick="closeConfirm()" style="padding:0.55rem 0.8rem;background:#eee;border:1px solid #ccc;border-radius:5px;cursor:pointer">← Back</button>
    </div>
  </div>`;
}

function _buildSlotOptions(minLevel) {
  let opts = '';
  for (let lvl = minLevel; lvl <= 9; lvl++) {
    opts += `<option value="${lvl}">Level ${lvl}</option>`;
  }
  return opts;
}

function closeConfirm() {
  document.getElementById('enc-confirm').style.display = 'none';
  selectedActionIdx = null;
}

// ── Use It ────────────────────────────────────────────────────
async function doUseAction(idx) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  if (!combatant) return;

  const action = idx >= 0 ? myActions[idx] : null;
  const updates = {};

  // Mark the token used
  if (activeToken === 'action') updates.action_used = true;
  else if (activeToken === 'bonus') updates.bonus_action_used = true;
  else if (activeToken === 'reaction') updates.reaction_used = true;

  try {
    // 1. Mark action economy (triggers WS broadcast)
    const econRes = await fetch('/api/characters/encounter/action-economy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: myActiveCombatantId, ...updates }),
    });
    if (!econRes.ok) { toast('Could not mark action — try again'); return; }

    // 2. Spend spell slot if leveled spell
    if (action && action.type === 'spell' && action.level > 0) {
      const slotEl = document.getElementById('slot-pick');
      const slotLevel = slotEl ? parseInt(slotEl.value) : action.level;
      const charId = combatant.character_id;
      // GET sheet-data (which includes spell_slots_used), then increment the chosen level
      const sheetRes = await fetch(`/api/characters/${charId}/sheet-data`).catch(() => null);
      if (sheetRes && sheetRes.ok) {
        const sheetData = await sheetRes.json();
        const used = { ...(sheetData.spell_slots_used || {}) };
        used[String(slotLevel)] = (used[String(slotLevel)] || 0) + 1;
        await fetch(`/api/characters/${charId}/spell-slots`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ used }),
        }).catch(() => {});
      }
    }

    // 3. Spend class ability use
    if (action && action.type === 'ability' && action.resource_id) {
      await fetch(`/api/characters/${combatant.character_id}/resources/spend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resource_id: action.resource_id, amount: 1 }),
      });
      // Refresh resource panel
      await loadEncResources(combatant.character_id);
    }

    // Close panels — WS broadcast from step 1 will update token states
    document.getElementById('enc-action-list').style.display = 'none';
    document.getElementById('enc-confirm').style.display = 'none';
    activeToken = null;
    selectedActionIdx = null;

  } catch (e) {
    toast('Action failed — try again');
  }
}

// ── Move stepper ──────────────────────────────────────────────
function renderMovePanel(combatant) {
  const el = document.getElementById('enc-move-panel');
  el.style.display = 'block';

  const remaining = combatant.movement_remaining ?? 0;
  movementAmount = Math.min(5, remaining > 0 ? 5 : 0);

  // Quick buttons: 5ft increments up to remaining (max 6 buttons shown)
  const maxQuick = Math.min(remaining, 30);
  const quickBtns = [];
  for (let v = 5; v <= maxQuick; v += 5) {
    quickBtns.push(`<button id="qbtn-${v}" onclick="setMoveAmount(${v})"
      style="padding:0.35rem 0.55rem;border:1px solid var(--ink-soft);border-radius:4px;cursor:pointer;font-size:0.85rem;background:${movementAmount===v ? 'var(--ink)' : '#f5f5f5'};color:${movementAmount===v ? 'white' : 'inherit'}">${v} ft</button>`);
  }

  el.innerHTML = `<div style="border:1px solid var(--ink-soft);border-radius:6px;padding:0.6rem">
    <div style="font-weight:bold;margin-bottom:0.4rem">Move how far?
      <span style="font-weight:normal;color:var(--ink-soft)">(${remaining} ft remaining)</span>
    </div>
    <div style="display:flex;gap:0.3rem;flex-wrap:wrap;margin-bottom:0.5rem" id="move-quick-btns">
      ${quickBtns.join('')}
    </div>
    <div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.5rem">
      <button onclick="stepMove(-5)" style="padding:0.3rem 0.7rem;border:1px solid #ccc;border-radius:4px;font-size:1.1rem;cursor:pointer">−</button>
      <span id="move-amount-display" style="min-width:5rem;text-align:center;font-weight:bold">${movementAmount} ft</span>
      <button onclick="stepMove(5)" style="padding:0.3rem 0.7rem;border:1px solid #ccc;border-radius:4px;font-size:1.1rem;cursor:pointer">+</button>
      <span style="font-size:0.75rem;color:var(--ink-soft)">(5 ft steps)</span>
    </div>
    <div style="display:flex;gap:0.4rem">
      <button id="spend-move-btn" onclick="doSpendMovement(${combatant.combatant_id})"
        style="flex:1;padding:0.5rem;background:var(--ink);color:white;border:none;border-radius:4px;cursor:pointer;font-weight:bold">
        Spend ${movementAmount} ft
      </button>
      <button onclick="closeMovePanel()" style="padding:0.5rem 0.7rem;background:#eee;border:1px solid #ccc;border-radius:4px;cursor:pointer">← Back</button>
    </div>
  </div>`;
}

function setMoveAmount(val) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  const remaining = combatant?.movement_remaining ?? 0;
  movementAmount = Math.max(5, Math.min(val, remaining));
  // Update display
  const display = document.getElementById('move-amount-display');
  if (display) display.textContent = `${movementAmount} ft`;
  const spendBtn = document.getElementById('spend-move-btn');
  if (spendBtn) spendBtn.textContent = `Spend ${movementAmount} ft`;
  // Update quick button highlights
  document.querySelectorAll('#move-quick-btns button').forEach(b => {
    const bVal = parseInt(b.textContent);
    b.style.background = bVal === movementAmount ? 'var(--ink)' : '#f5f5f5';
    b.style.color = bVal === movementAmount ? 'white' : 'inherit';
  });
}

function stepMove(delta) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  const remaining = combatant?.movement_remaining ?? 0;
  const newVal = Math.max(5, Math.min(movementAmount + delta, remaining));
  setMoveAmount(newVal);
}

async function doSpendMovement(combatantId) {
  if (movementAmount <= 0) return;
  try {
    const res = await fetch('/api/characters/encounter/spend-movement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: combatantId, amount: movementAmount }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      toast(err.detail || 'Could not spend movement');
      return;
    }
    // WS push will update movement_remaining; close the panel
    closeMovePanel();
  } catch (e) { toast('Connection error'); }
}

function closeMovePanel() {
  document.getElementById('enc-move-panel').style.display = 'none';
  activeToken = null;
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  if (combatant) _updateTokens(combatant);
}

init();
