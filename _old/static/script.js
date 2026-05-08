let currentPool = []; 
let chosenSetIndex = null; 
let classDetails = null; 

window.onload = async function() { await checkAuth(); await loadOptions(); };

// --- DRAG & DROP HANDLERS (NEW) ---
function allowDrop(ev) {
    ev.preventDefault(); // Necessary to allow dropping
    ev.currentTarget.classList.add('drag-over');
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.id);
}

function drop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    
    const data = ev.dataTransfer.getData("text");
    const token = document.getElementById(data);
    const target = ev.currentTarget;

    // If dropping into a slot that already has a token...
    if (target.classList.contains('stat-slot') && target.children.length > 1) {
        // Swap Logic: Move the existing token back to pool (or swap positions)
        // For simplicity V1: Return existing token to pool
        const existingToken = target.querySelector('.stat-token');
        document.getElementById('token-pool').appendChild(existingToken);
    }
    
    target.appendChild(token);
}

// --- AUTH & LOAD (Unchanged) ---
async function checkAuth() {
    const res = await fetch("/auth/me");
    const data = await res.json();
    const loginContainer = document.getElementById("login-btn-container");
    const userContainer = document.getElementById("user-info-container");
    const adminControls = document.getElementById("admin-controls");

    if (data.authenticated) {
        loginContainer.classList.add("hidden");
        userContainer.classList.remove("hidden");
        document.getElementById("display-username").innerText = data.user.username;
        if (data.is_admin) adminControls.classList.remove("hidden");
        else adminControls.classList.add("hidden");
        await loadMyCharacter();
    } else {
        loginContainer.classList.remove("hidden");
        userContainer.classList.add("hidden");
        document.getElementById("creator-section").classList.add("hidden");
        document.getElementById("character-sheet").classList.add("hidden");
    }
}

async function loadMyCharacter() {
    const res = await fetch("/my-character");
    const result = await res.json();
    if (result.found) {
        document.getElementById("creator-section").classList.add("hidden");
        document.getElementById("character-sheet").classList.remove("hidden");
        renderSheet(result.data);
    } else {
        document.getElementById("creator-section").classList.remove("hidden");
        document.getElementById("character-sheet").classList.add("hidden");
    }
}

// --- SPELLBOOK UI ---
let mySpells = [];

function openGrimoire() {
    document.getElementById("grimoire-modal").classList.remove("hidden");
    renderGrimoire();
}

function closeGrimoire() {
    document.getElementById("grimoire-modal").classList.add("hidden");
    loadMyCharacter(); // Refresh main sheet
}

function renderGrimoire() {
    const knownDiv = document.getElementById("known-list");
    const prepDiv = document.getElementById("prepared-list");
    knownDiv.innerHTML = "";
    prepDiv.innerHTML = "";

    // We rely on the global 'mySpells' fetched by loadMyCharacter
    // (See update below to ensure mySpells is populated)
    
    mySpells.forEach(spell => {
        const card = createSpellCard(spell);
        
        if(spell.prepared) {
            prepDiv.appendChild(card);
        } else {
            knownDiv.appendChild(card);
        }
    });
}

function createSpellCard(spell) {
    const el = document.createElement("div");
    el.className = "spell-card";
    el.draggable = true;
    el.id = `spell-${spell.id}`;
    el.innerHTML = `
        <span style="font-weight:bold;">${spell.name}</span>
        <span class="spell-level-badge">${spell.level === 0 ? 'C' : spell.level}</span>
    `;
    
    el.ondragstart = (ev) => {
        ev.dataTransfer.setData("text/plain", JSON.stringify({id: spell.id, origin: spell.prepared ? 'prep' : 'known'}));
    };
    
    return el;
}

// --- SPELL DRAG HANDLERS ---
async function dropPrepare(ev) {
    ev.preventDefault();
    const data = JSON.parse(ev.dataTransfer.getData("text/plain"));
    
    // Only act if coming from 'known' (unprepared) list
    if(data.origin === 'known') {
        await togglePrepare(data.id, true);
    }
}

async function dropUnprepare(ev) {
    ev.preventDefault();
    const data = JSON.parse(ev.dataTransfer.getData("text/plain"));
    
    // Only act if coming from 'prep' list
    if(data.origin === 'prep') {
        await togglePrepare(data.id, false);
    }
}

async function togglePrepare(spellId, isPrepared) {
    // Optimistic UI Update
    const spell = mySpells.find(s => s.id === spellId);
    if(spell) spell.prepared = isPrepared;
    renderGrimoire();

    // Backend Update
    await fetch("/prepare-spell", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spell_id: spellId, prepared: isPrepared })
    });
}

// --- UPDATE loadMyCharacter TO SAVE SPELLS GLOBALLY ---
async function loadMyCharacter() {
    const res = await fetch("/my-character");
    const result = await res.json();
    if (result.found) {
        // ... (hide creator/show sheet logic) ...
        document.getElementById("creator-section").classList.add("hidden");
        document.getElementById("character-sheet").classList.remove("hidden");
        
        // SAVE SPELLS TO GLOBAL VAR
        mySpells = result.data.spells || [];
        
        renderSheet(result.data);
    } else {
        // ...
        document.getElementById("creator-section").classList.remove("hidden");
        document.getElementById("character-sheet").classList.add("hidden");
    }
}

// --- WIZARD NAVIGATION ---
function hideAllSteps() {
    for(let i=1; i<=4; i++) {
        const el = document.getElementById(`step-${i}`) || document.getElementById(["step-1","step-class","step-stats","step-build","step-bio"][i-1]); 
        // Handling inconsistent naming in previous iterations, ensuring robustness
    }
    document.getElementById("step-1").classList.add("hidden");
    document.getElementById("step-class").classList.add("hidden");
    document.getElementById("step-stats").classList.add("hidden");
    document.getElementById("step-build").classList.add("hidden");
    document.getElementById("step-bio").classList.add("hidden");
}

function goToStep(stepNum) { /* Legacy helper */ }

function goToStepClass() {
    const name = document.getElementById("char_name").value;
    const sp = document.getElementById("species-select").value;
    if(!name) { alert("Name is required."); return; }
    if(!sp) { alert("Species selection is required."); return; }
    hideAllSteps();
    document.getElementById("step-class").classList.remove("hidden");
}

async function goToStepStats() {
    const cl = document.getElementById("class-select").value;
    if(!cl) { alert("Class selection is required."); return; }
    const res = await fetch(`/options/class-details/${cl}`);
    classDetails = await res.json();
    hideAllSteps();
    document.getElementById("step-stats").classList.remove("hidden");
}

function goToStepBuild() {
    // VALIDATE DRAG & DROP
    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    for (let attr of attributes) {
        const slot = document.getElementById(`slot-${attr}`);
        if (slot.querySelectorAll('.stat-token').length === 0) {
            alert(`Please drag a token into ${attr}.`);
            return;
        }
    }
    
    hideAllSteps();
    document.getElementById("step-build").classList.remove("hidden");
    
    // RENDER BUILD (Features)
    const featContainer = document.getElementById("feature-selection-container");
    featContainer.innerHTML = "<h3>Class Features</h3>";
    if(classDetails.features.length > 0) {
        classDetails.features.forEach(f => {
            if(f.options.length > 0) {
                let opts = `<option value="">-- Select Option --</option>`;
                f.options.forEach(o => { opts += `<option value="${o.id}">${o.name}</option>`; });
                featContainer.innerHTML += `<div style="margin-bottom:10px; background:rgba(0,0,0,0.2); padding:10px; border-radius:4px;"><label>${f.name}</label><select class="feature-choice" data-feature-id="${f.id}" style="margin-top:5px;">${opts}</select></div>`;
            } else {
                featContainer.innerHTML += `<div style="margin-bottom:5px;">✓ <strong>${f.name}</strong>: ${f.description}</div>`;
            }
        });
    } else { featContainer.innerHTML += "<p>No special choices at Level 1.</p>"; }

    // RENDER SPELLS
    const spellContainer = document.getElementById("spell-selection-container");
    const spellList = document.getElementById("spell-checkboxes");
    spellList.innerHTML = "";
    
    if(classDetails.spellcasting_ability) {
        spellContainer.classList.remove("hidden");
        classDetails.spells.forEach(s => {
            spellList.innerHTML += `<label style="font-size:0.9rem;"><input type="checkbox" class="spell-choice" value="${s.id}"> ${s.name} (Lvl ${s.level})</label>`;
        });
    } else {
        spellContainer.classList.add("hidden");
    }
}

function goToStepBio() {
    const selects = document.querySelectorAll(".feature-choice");
    for(let s of selects) { if(!s.value) { alert("Please make all class feature choices."); return; } }
    hideAllSteps();
    document.getElementById("step-bio").classList.remove("hidden");
}

// --- STAT ROLLING ---
async function rollStats() {
    const charName = document.getElementById("char_name").value;
    const response = await fetch("/roll-stats/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ character_name: charName }) });
    const data = await response.json();
    currentPool = data.pool;
    
    const container = document.getElementById("output");
    container.innerHTML = "";
    document.getElementById("assignment-area").classList.add("hidden");
    
    if(data.pool) {
        data.pool.forEach((set, index) => {
            let html = `<div class="stat-set"><h3 style="color:var(--accent-gold); font-size:1.1rem;">Set ${index + 1}</h3>`;
            set.forEach(stat => { html += `<div class="stat-box">${stat}</div>`; });
            html += `<button style="margin-top:10px; width:100%;" onclick="selectSet(${index})">Select</button></div>`;
            container.innerHTML += html;
        });
        if(data.locked) alert("Locked: Displaying previously rolled stats.");
    }
}

function selectSet(index) {
    chosenSetIndex = index;
    const selectedStats = currentPool[index];
    document.getElementById("output").innerHTML = ""; 
    document.getElementById("assignment-area").classList.remove("hidden");
    
    // --- POPULATE DRAG POOL ---
    const pool = document.getElementById("token-pool");
    pool.innerHTML = "";
    
    selectedStats.forEach((val, i) => {
        const token = document.createElement("div");
        token.className = "stat-token";
        token.id = `token-${i}`; // Unique ID for drag event
        token.draggable = true;
        token.innerText = val;
        token.ondragstart = drag;
        pool.appendChild(token);
    });
}

// --- FINAL SAVE (Updated for D&D Reading) ---
async function finalizeCharacter() {
    const bg = document.getElementById("char-background").value;
    const align = document.getElementById("char-alignment").value;
    const bio = document.getElementById("char-bio").value;
    if(!bg || !align) { alert("Please fill in Background and Alignment."); return; }

    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    const selectionMap = {};
    const usedValues = [];
    
    // READ FROM DROP SLOTS
    for (let attr of attributes) {
        const slot = document.getElementById(`slot-${attr}`);
        const token = slot.querySelector('.stat-token');
        
        if (!token) { alert(`Missing token for ${attr}`); return; }
        
        const val = parseInt(token.innerText);
        selectionMap[attr] = val;
        usedValues.push(val);
    }
    
    const originalSet = [...currentPool[chosenSetIndex]].sort((a,b) => a-b);
    const selectedSet = [...usedValues].sort((a,b) => a-b);
    if (JSON.stringify(originalSet) !== JSON.stringify(selectedSet)) { alert("Stat verification failed."); return; }

    const resMain = await fetch("/confirm-selection/", { 
        method: "POST", 
        headers: { "Content-Type": "application/json" }, 
        body: JSON.stringify({ 
            chosen_set_index: chosenSetIndex, 
            class_id: parseInt(document.getElementById("class-select").value), 
            species_id: parseInt(document.getElementById("species-select").value), 
            attributes: selectionMap,
            background: bg, alignment: align, bio: bio
        }) 
    });
    const dataMain = await resMain.json();
    if(dataMain.status !== "success") { alert("Error saving character base."); return; }

    const featureSelects = document.querySelectorAll(".feature-choice");
    for(let s of featureSelects) {
        await fetch("/select-feature", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ feature_id: parseInt(s.dataset.featureId), option_id: parseInt(s.value) })
        });
    }

    const spellChecks = document.querySelectorAll(".spell-choice:checked");
    for(let c of spellChecks) {
        await fetch("/learn-spell", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ spell_id: parseInt(c.value) })
        });
    }

    location.reload();
}

// --- UTILS ---
async function loadOptions() {
    try {
        const cRes = await fetch("/options/classes");
        const classes = await cRes.json();
        const cList = document.getElementById("class-list");
        cList.innerHTML = ""; 
        classes.forEach(c => { 
            const btn = document.createElement("button");
            btn.className = "class-btn";
            btn.id = `class-btn-${c.id}`;
            btn.innerText = c.name;
            btn.style.textAlign = "left";
            btn.onclick = () => pickClass(c.id, c.name, c.description, c.flavor_text || "");
            cList.appendChild(btn);
            const opt = document.createElement("option"); opt.value = c.id; opt.innerText = c.name; document.getElementById("class-select").appendChild(opt);
        });

        const sRes = await fetch("/options/species");
        const species = await sRes.json();
        const sList = document.getElementById("species-list");
        sList.innerHTML = ""; 
        species.forEach(s => { 
            const btn = document.createElement("button");
            btn.className = "species-btn";
            btn.id = `species-btn-${s.id}`;
            btn.innerText = s.name;
            btn.style.textAlign = "left";
            btn.onclick = () => pickSpecies(s.id, s.name, s.description, s.flavor_text || "");
            sList.appendChild(btn);
            const opt = document.createElement("option"); opt.value = s.id; opt.innerText = s.name; document.getElementById("species-select").appendChild(opt);
        });
    } catch (e) { console.error(e); }
}

function pickSpecies(id, name, desc, flavor) {
    document.getElementById("species-select").value = id;
    document.querySelectorAll('.species-btn').forEach(b => { b.style.background = 'rgba(204, 164, 59, 0.1)'; b.style.color = 'var(--accent-gold)'; b.style.borderColor = 'var(--accent-gold)'; });
    const btn = document.getElementById(`species-btn-${id}`);
    if(btn) { btn.style.background = 'var(--accent-gold)'; btn.style.color = 'black'; btn.style.borderColor = 'white'; }
    document.getElementById("species-name-display").innerText = name;
    document.getElementById("species-desc-display").innerText = desc;
    document.getElementById("species-flavor-display").innerText = flavor;
}

function pickClass(id, name, desc, flavor) {
    document.getElementById("class-select").value = id;
    document.querySelectorAll('.class-btn').forEach(b => { b.style.background = 'rgba(204, 164, 59, 0.1)'; b.style.color = 'var(--accent-gold)'; b.style.borderColor = 'var(--accent-gold)'; });
    const btn = document.getElementById(`class-btn-${id}`);
    if(btn) { btn.style.background = 'var(--accent-gold)'; btn.style.color = 'black'; btn.style.borderColor = 'white'; }
    document.getElementById("class-name-display").innerText = name;
    document.getElementById("class-desc-display").innerText = desc;
    document.getElementById("class-flavor-display").innerText = flavor;
}

function renderSheet(char) {
    document.getElementById("sheet-name").innerText = char.character_name;
    document.getElementById("sheet-subtitle").innerText = `Level ${char.level} ${char.species_name} ${char.class_name}`;
    document.getElementById("sheet-bio-header").innerText = `${char.alignment || ""} • ${char.background || ""}`;
    document.getElementById("sheet-bio-text").innerText = char.bio || "";
    document.getElementById("sheet-hitdie").innerText = char.hit_die;
    document.getElementById("sheet-hp").innerText = char.hp_max;
    const container = document.getElementById("sheet-stats");
    container.innerHTML = "";
    const order = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    order.forEach(attr => {
        const score = char.attributes[attr];
        const modifier = Math.floor((score - 10) / 2);
        const sign = modifier >= 0 ? "+" : "";
        container.innerHTML += `<div class="ability-card"><div class="ability-label">${attr.substring(0,3)}</div><div class="ability-score">${score}</div><div class="ability-mod">${sign}${modifier}</div></div>`;
    });
    const featList = document.getElementById("features-list");
    featList.innerHTML = "";
    if(char.features) {
        char.features.forEach(f => {
            let txt = f.selected ? `<strong>${f.name}: ${f.selected.name}</strong>` : `<strong>${f.name}</strong>`;
            featList.innerHTML += `<div style="margin-bottom:5px;">${txt} - ${f.description}</div>`;
        });
    }
    const spellContainer = document.getElementById("spells-container");
    const spellList = document.getElementById("known-spells-list");
    spellList.innerHTML = "";
    if(char.spellcasting_ability) {
        spellContainer.classList.remove("hidden");
        if(char.spells) char.spells.forEach(s => spellList.innerHTML += `<div class="stat-box">${s.name}</div>`);
    } else {
        spellContainer.classList.add("hidden");
    }
}
async function openSpellManager() { }
async function learnSelectedSpell() { }
async function forgetSpell(id) { }