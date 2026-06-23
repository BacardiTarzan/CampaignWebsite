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

// ── Stubs for Tasks 9+10 ──────────────────────────────────────
// tapToken, loadActions, renderActionList, selectAction, doUseAction,
// renderMovePanel, doSpendMovement — added in Tasks 9 and 10
function tapToken(type) { /* implemented in Task 9 */ }
function loadActions(charId) { /* implemented in Task 9 */ }

init();
