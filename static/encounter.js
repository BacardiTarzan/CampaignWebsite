// encounter.js — player encounter page
let myCharIds = [];
let encounterState = { encounter_active: false, initiative_phase: false, current_round: 1, combatants: [] };
let pollTimer = null;
let myCharId = null;       // first own character in current encounter (set on render)
let myActions = [];        // cached from API
let actionsLoaded = false; // avoid re-fetching on every render

function toast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

async function init() {
  // Verify auth
  const meRes = await fetch('/auth/me');
  if (!meRes.ok) { window.location.href = '/'; return; }

  // Load this player's character IDs
  const charsRes = await fetch('/api/characters');
  if (charsRes.ok) {
    const chars = await charsRes.json();
    myCharIds = chars.filter(c => c.is_complete).map(c => c.id);
  }

  await poll();
  pollTimer = setInterval(poll, 2000);
  window.addEventListener('beforeunload', () => clearInterval(pollTimer));
}

async function poll() {
  try {
    const res = await fetch('/api/encounter/state');
    if (!res.ok) {
      if (res.status === 401) window.location.href = '/';
      return;
    }
    encounterState = await res.json();
    render();
  } catch (e) { /* ignore network errors */ }
}

function render() {
  const { encounter_active, initiative_phase, current_round, current_turn_combatant_id, combatants } = encounterState;

  const statusEl = document.getElementById('enc-status');
  const bannerEl = document.getElementById('enc-turn-banner');
  const economyEl = document.getElementById('enc-economy');
  const orderEl = document.getElementById('enc-order');

  if (!encounter_active) {
    statusEl.innerHTML = `<h2>No encounter in progress</h2><p style="color:var(--ink-soft)">The DM will start an encounter when combat begins.</p>`;
    bannerEl.innerHTML = '';
    economyEl.innerHTML = '';
    orderEl.innerHTML = '';
    return;
  }

  if (initiative_phase) {
    statusEl.innerHTML = `<h2>Initiative Phase</h2><p style="color:var(--ink-soft)">The DM is collecting initiative rolls. Stand by...</p>`;
    bannerEl.innerHTML = '';
    economyEl.innerHTML = '';
    orderEl.innerHTML = '';
    return;
  }

  // Active encounter
  statusEl.innerHTML = '';  // clear loading/no-encounter message

  // Find the current combatant and whether it's my turn
  const currentCombatant = combatants.find(c => c.combatant_id === current_turn_combatant_id);
  const myActiveCombatant = combatants.find(
    c => myCharIds.includes(c.character_id) && c.combatant_id === current_turn_combatant_id
  );
  const isMyTurn = !!myActiveCombatant;

  // Turn banner
  if (isMyTurn) {
    bannerEl.innerHTML = `<div style="background:var(--gold);color:#2a1a00;padding:0.75rem 1rem;border-radius:6px;font-weight:bold;font-size:1.1rem">
      ⚔ YOUR TURN — Round ${current_round}
    </div>`;
    // Economy buttons
    economyEl.innerHTML = renderEconomy(myActiveCombatant);
    // Load actions once per turn
    if (!actionsLoaded && myActiveCombatant.character_id) {
      loadActions(myActiveCombatant.character_id);
    }
    renderActionSelector();
  } else {
    const whose = currentCombatant ? currentCombatant.name : '—';
    bannerEl.innerHTML = `<div style="font-size:1rem;color:var(--ink-soft)">Round ${current_round} — <em>${_esc(whose)}'s</em> turn</div>`;
    economyEl.innerHTML = '';
    // Clear actions panel when it's not my turn
    const actEl = document.getElementById('enc-actions');
    if (actEl) actEl.innerHTML = '';
    const ap = document.getElementById('enc-action-panel');
    if (ap) ap.style.display = 'none';
    actionsLoaded = false;
    myActions = [];
  }

  // Initiative order list
  orderEl.innerHTML = `<h3 style="margin-bottom:0.5rem">Initiative Order</h3>` +
    combatants.map(c => {
      const isActive = c.combatant_id === current_turn_combatant_id;
      const isMine = myCharIds.includes(c.character_id);
      const hpStr = c.hp_current != null && c.hp_max != null
        ? `${c.hp_current}/${c.hp_max} HP` : '';
      const conds = (c.conditions || []).map(cd => {
        const label = cd.startsWith('Exhaustion:') ? `Exhaustion ${cd.split(':')[1]}` : cd;
        return `<span style="font-size:0.75rem;padding:0.1rem 0.3rem;background:var(--rubric);color:white;border-radius:3px">${label}</span>`;
      }).join(' ');
      return `<div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0.5rem;border-radius:4px;margin-bottom:0.2rem;background:${isActive ? 'var(--parchment-bright, #f4e8c8)' : 'transparent'};${isActive ? 'border:1px solid var(--gold)' : ''}">
        <span style="font-weight:bold;min-width:1.5rem">${c.turn_order ?? '—'}.</span>
        <span style="${isActive ? 'font-weight:bold' : ''}">${_esc(c.name)}</span>
        ${isMine ? '<span style="font-size:0.75rem;color:var(--ink-soft)">(You)</span>' : ''}
        ${hpStr ? `<span style="font-size:0.85rem;color:var(--ink-soft)">${hpStr}</span>` : ''}
        ${conds}
      </div>`;
    }).join('');
}

function renderEconomy(combatant) {
  const { combatant_id, action_used, bonus_action_used, reaction_used, movement_remaining } = combatant;
  const btn = (label, field, used) => `
    <button onclick="toggleEcon(${combatant_id}, '${field}', ${!used})"
      style="padding:0.4rem 0.8rem;border:2px solid var(--gold);border-radius:4px;cursor:pointer;
             background:${used ? 'var(--ink-soft)' : 'var(--gold)'};
             color:${used ? 'var(--light)' : '#2a1a00'};
             text-decoration:${used ? 'line-through' : 'none'};opacity:${used ? '0.6' : '1'}">
      ${used ? '✓' : '○'} ${label}
    </button>`;
  const mvStr = movement_remaining != null ? `<span style="padding:0.4rem;color:var(--ink-soft)">${movement_remaining} ft. move</span>` : '';
  return `<div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center">
    ${btn('Action', 'action_used', action_used)}
    ${btn('Bonus Action', 'bonus_action_used', bonus_action_used)}
    ${btn('Reaction', 'reaction_used', reaction_used)}
    ${mvStr}
  </div>`;
}

async function toggleEcon(combatantId, field, value) {
  try {
    const res = await fetch('/api/characters/encounter/action-economy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: combatantId, [field]: value }),
    });
    if (!res.ok) { toast('Could not update — not your turn or not your character'); return; }
    // Optimistic update
    const c = encounterState.combatants.find(x => x.combatant_id === combatantId);
    if (c) c[field] = value;
    render();
  } catch (e) {
    toast('Connection error');
  }
}

async function loadActions(charId) {
  try {
    const res = await fetch(`/api/characters/${charId}/encounter-actions`);
    if (!res.ok) return;
    myActions = await res.json();
    actionsLoaded = true;
    renderActionSelector();
  } catch (e) { /* ignore */ }
}

function renderActionSelector() {
  const el = document.getElementById('enc-actions');
  if (!el) return;
  if (!myActions.length) { el.innerHTML = ''; return; }

  const attacks = myActions.reduce((acc, a, i) => a.type === 'attack' ? [...acc, i] : acc, []);
  const spells = myActions.reduce((acc, a, i) => a.type === 'spell' && a.cost.action ? [...acc, i] : acc, []);
  const bonusSpells = myActions.reduce((acc, a, i) => a.type === 'spell' && a.cost.bonus_action ? [...acc, i] : acc, []);

  const actionBtns = (indices) => indices.map(i => {
    const a = myActions[i];
    return `<button onclick="showAction(${i})"
      style="padding:0.3rem 0.6rem;margin:0.15rem;border:1px solid var(--gold);border-radius:4px;cursor:pointer;background:var(--parchment-bright,#f4e8c8);font-size:0.85rem">
      ${_esc(a.name)}${a.level > 0 ? ` <small>(L${a.level})</small>` : ''}
    </button>`;
  }).join('');

  let html = '';
  if (attacks.length) html += `<div style="margin-bottom:0.4rem"><strong>Attacks</strong><br>${actionBtns(attacks)}</div>`;
  if (spells.length) html += `<div style="margin-bottom:0.4rem"><strong>Spells (Action)</strong><br>${actionBtns(spells)}</div>`;
  if (bonusSpells.length) html += `<div style="margin-bottom:0.4rem"><strong>Spells (Bonus)</strong><br>${actionBtns(bonusSpells)}</div>`;
  el.innerHTML = html;
}

function showAction(idx) {
  const action = myActions[idx];
  if (!action) return;
  const panel = document.getElementById('enc-action-panel');
  if (!panel) return;
  panel.style.display = 'block';

  let html = `<div style="display:flex;justify-content:space-between;align-items:start">
    <strong style="font-size:1rem">${_esc(action.name)}</strong>
    <button onclick="document.getElementById('enc-action-panel').style.display='none'" style="cursor:pointer;font-size:0.8rem">✕</button>
  </div>`;

  if (action.type === 'attack') {
    html += `<p style="margin:0.25rem 0"><strong>Attack Bonus:</strong> ${_esc(action.attack_bonus_display || '—')}</p>`;
    html += `<p style="margin:0.25rem 0"><strong>Damage:</strong> ${_esc(action.damage) || '—'}</p>`;
    html += `<p style="margin:0.25rem 0"><strong>Range:</strong> ${_esc(action.range || '5 ft.')}</p>`;
    if (action.properties?.length) {
      html += `<p style="margin:0.25rem 0"><strong>Properties:</strong> ${action.properties.map(_esc).join(', ')}</p>`;
    }
    if (action.mastery_property) {
      html += `<p style="margin:0.25rem 0"><strong>Mastery:</strong> ${_esc(action.mastery_property)}</p>`;
    }
  } else {
    // spell
    const lvlStr = action.level === 0 ? 'Cantrip' : `Level ${action.level}`;
    html += `<p style="margin:0.25rem 0"><em>${lvlStr} ${_esc(action.school || '')}</em></p>`;
    html += `<p style="margin:0.25rem 0"><strong>Range:</strong> ${_esc(action.range || '—')}</p>`;
    if (action.duration) html += `<p style="margin:0.25rem 0"><strong>Duration:</strong> ${_esc(action.duration)}${action.concentration ? ' (Concentration)' : ''}</p>`;
    if (action.save_dc) html += `<p style="margin:0.25rem 0"><strong>Save DC:</strong> ${action.save_dc} ${_esc(action.save_ability || '')}</p>`;
    if (action.attack_bonus_display) html += `<p style="margin:0.25rem 0"><strong>Spell Attack:</strong> ${_esc(action.attack_bonus_display)}</p>`;
    if (action.description) {
      const desc = action.description.length > 300
        ? action.description.slice(0, 297) + '...'
        : action.description;
      html += `<details style="margin-top:0.4rem"><summary>Description</summary><p style="font-size:0.85rem;white-space:pre-wrap">${_esc(desc)}</p></details>`;
    }
  }

  panel.innerHTML = html;
}

// Escape HTML to prevent XSS from server-returned names
function _esc(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

init();
