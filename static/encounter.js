// encounter.js — player encounter page
let myCharIds = [];
let encounterState = { encounter_active: false, initiative_phase: false, current_round: 1, combatants: [] };
let pollTimer = null;

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
  } else {
    const whose = currentCombatant ? currentCombatant.name : '—';
    bannerEl.innerHTML = `<div style="font-size:1rem;color:var(--ink-soft)">Round ${current_round} — <em>${_esc(whose)}'s</em> turn</div>`;
    economyEl.innerHTML = '';
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

// Escape HTML to prevent XSS from server-returned names
function _esc(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

init();
