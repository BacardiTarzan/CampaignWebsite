let currentPool = []; 
let chosenSetIndex = null; 
let classDetails = null; 

window.onload = async function() { await checkAuth(); await loadOptions(); };

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

// --- WIZARD NAVIGATION ---
function goToStep(stepNum) {
    for(let i=1; i<=4; i++) document.getElementById(`step-${i}`).classList.add("hidden");
    document.getElementById(`step-${stepNum}`).classList.remove("hidden");
}

async function goToStep2() {
    const name = document.getElementById("char_name").value;
    const sp = document.getElementById("species-select").value;
    const cl = document.getElementById("class-select").value;
    if(!name || !sp || !cl) { alert("Please complete all fields."); return; }
    
    const res = await fetch(`/options/class-details/${cl}`);
    classDetails = await res.json();
    
    goToStep(2);
}

function goToStep3() {
    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    for (let attr of attributes) {
        if (!document.getElementById(`attr-${attr}`).value) { alert(`Assign ${attr} first.`); return; }
    }
    
    const featContainer = document.getElementById("feature-selection-container");
    featContainer.innerHTML = "<h3>Class Features</h3>";
    
    if(classDetails.features.length > 0) {
        classDetails.features.forEach(f => {
            if(f.options.length > 0) {
                let opts = `<option value="">-- Select Option --</option>`;
                f.options.forEach(o => { opts += `<option value="${o.id}">${o.name}</option>`; });
                featContainer.innerHTML += `
                    <div style="margin-bottom:10px; background:rgba(0,0,0,0.2); padding:10px; border-radius:4px;">
                        <label>${f.name}</label>
                        <select class="feature-choice" data-feature-id="${f.id}" style="margin-top:5px;">${opts}</select>
                    </div>`;
            } else {
                featContainer.innerHTML += `<div style="margin-bottom:5px;">✓ <strong>${f.name}</strong>: ${f.description}</div>`;
            }
        });
    } else { featContainer.innerHTML += "<p>No special choices at Level 1.</p>"; }

    const spellContainer = document.getElementById("spell-selection-container");
    const spellList = document.getElementById("spell-checkboxes");
    spellList.innerHTML = "";
    
    if(classDetails.spellcasting_ability) {
        spellContainer.classList.remove("hidden");
        classDetails.spells.forEach(s => {
            spellList.innerHTML += `
                <label style="font-size:0.9rem;">
                    <input type="checkbox" class="spell-choice" value="${s.id}"> ${s.name} (Lvl ${s.level})
                </label>`;
        });
    } else {
        spellContainer.classList.add("hidden");
    }

    goToStep(3);
}

function goToStep4() {
    const selects = document.querySelectorAll(".feature-choice");
    for(let s of selects) {
        if(!s.value) { alert("Please make all class feature choices."); return; }
    }
    goToStep(4);
}

// --- STAT ROLLING ---
async function rollStats() {
    const charName = document.getElementById("char_name").value;
    const response = await fetch("/roll-stats/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ character_name: charName }) });
    const data = await response.json();
    currentPool = data.pool;
    
    const container = document.getElementById("output");
    container.innerHTML = "";
    
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
    
    const container = document.getElementById("stat-rows");
    container.innerHTML = "";
    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    
    attributes.forEach(attr => {
        let opts = `<option value="">--</option>`;
        selectedStats.forEach(num => { opts += `<option value="${num}">${num}</option>`; });
        container.innerHTML += `
            <div style="display:grid; grid-template-columns: 100px 1fr; gap:10px; margin-bottom:5px; align-items:center;">
                <label class="ability-label">${attr}</label>
                <select id="attr-${attr}">${opts}</select>
            </div>`;
    });
}

// --- FINAL SAVE ---
async function finalizeCharacter() {
    const bg = document.getElementById("char-background").value;
    const align = document.getElementById("char-alignment").value;
    const bio = document.getElementById("char-bio").value;
    if(!bg || !align) { alert("Please fill in Background and Alignment."); return; }

    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    const selectionMap = {};
    const usedValues = [];
    for (let attr of attributes) {
        const val = document.getElementById(`attr-${attr}`).value;
        selectionMap[attr] = parseInt(val);
        usedValues.push(parseInt(val));
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

async function loadOptions() {
    try {
        const cRes = await fetch("/options/classes");
        const classes = await cRes.json();
        const cSel = document.getElementById("class-select");
        classes.forEach(c => { cSel.innerHTML += `<option value="${c.id}">${c.name}</option>`; });

        const sRes = await fetch("/options/species");
        const species = await sRes.json();
        const sSel = document.getElementById("species-select");
        species.forEach(s => { sSel.innerHTML += `<option value="${s.id}">${s.name}</option>`; });
    } catch (e) { console.error(e); }
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
// Helper Placeholders
async function openSpellManager() { /* Logic can be re-added for Level Up */ }
async function learnSelectedSpell() { }
async function forgetSpell(id) { }