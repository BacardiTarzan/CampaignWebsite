window.onload = async function() { 
    loadDashboard();
    loadClassOptions(); 
    loadSpellList();    
};

// --- TABS ---
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');
    const navIndex = ['roster', 'grimoire', 'codex'].indexOf(tabName);
    document.querySelectorAll('.nav-item')[navIndex].classList.add('active');
}

// --- ROSTER LOGIC ---
async function loadDashboard() {
    const response = await fetch("/admin/dashboard");
    if(response.status === 403) { alert("Access Denied"); return; }
    
    const characters = await response.json();
    const tbody = document.querySelector("#char-table tbody");
    tbody.innerHTML = "";

    characters.forEach(char => {
        const tr = document.createElement("tr");
        let statsDisplay = char.chosen_set !== null ? "Stats Selected" : "Rolling...";
        const status = char.is_locked ? "🔒" : "🔓";

        tr.innerHTML = `
            <td>${char.discord_id}</td>
            <td>${char.character_name}<br><small>Lvl ${char.level || 1}</small></td>
            <td>${char.species_name || "-"} ${char.class_name || "-"}</td>
            <td>${statsDisplay}</td>
            <td>${status}</td>
            <td>
                <button onclick="unlockPlayer('${char.discord_id}')" style="background:#f39c12; padding:2px 5px; font-size:0.7rem;">Reset</button>
                <button onclick="deletePlayer('${char.discord_id}')" style="background:#c0392b; padding:2px 5px; font-size:0.7rem; color:white;">Del</button>
                <button onclick="levelUp('${char.discord_id}')" style="background:#2ecc71; padding:2px 5px; font-size:0.7rem; color:white;">+Lvl</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function unlockPlayer(id) { if(confirm("Reset stats?")) await fetch("/admin/unlock-player", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_discord_id: id }) }); loadDashboard(); }
async function deletePlayer(id) { if(confirm("Delete permanently?")) await fetch("/admin/delete-player", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_discord_id: id }) }); loadDashboard(); }
async function levelUp(id) { if(confirm("Level up?")) await fetch("/admin/level-up", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_discord_id: id }) }); loadDashboard(); }


// --- GRIMOIRE LOGIC ---
async function loadClassOptions() {
    const res = await fetch("/options/classes");
    const classes = await res.json();
    const container = document.getElementById("class-checkboxes");
    container.innerHTML = "";
    classes.forEach(c => {
        container.innerHTML += `
            <label style="display:flex; align-items:center; gap:5px; font-size:0.8rem; background:#333; padding:2px 6px; border-radius:4px;">
                <input type="checkbox" value="${c.name}" class="cls-check"> ${c.name}
            </label>`;
    });
}

async function loadSpellList() {
    const res = await fetch("/admin/list-spells");
    if(res.status !== 200) return;
    const spells = await res.json();
    const tbody = document.querySelector("#spell-table tbody");
    tbody.innerHTML = "";
    spells.forEach(s => {
        const classes = JSON.parse(s.classes_allowed).join(", ");
        tbody.innerHTML += `<tr><td>${s.level}</td><td><strong>${s.name}</strong></td><td>${classes}</td></tr>`;
    });
}

async function submitSpell() {
    const checkedBoxes = document.querySelectorAll('.cls-check:checked');
    const classesAllowed = Array.from(checkedBoxes).map(cb => cb.value);
    if(classesAllowed.length === 0) { alert("Select at least one class!"); return; }

    const payload = {
        name: document.getElementById("spell-name").value,
        level: parseInt(document.getElementById("spell-level").value),
        school: document.getElementById("spell-school").value,
        casting_time: document.getElementById("spell-cast").value,
        range: document.getElementById("spell-range").value,
        components: document.getElementById("spell-comp").value,
        duration: document.getElementById("spell-dur").value,
        description: document.getElementById("spell-desc").value,
        classes_allowed: classesAllowed
    };

    const res = await fetch("/admin/add-spell", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
    const data = await res.json();
    alert(data.message);
    if(data.status === "success") { loadSpellList(); }
}

// --- CODEX LOGIC ---

async function submitSpecies() {
    const payload = {
        name: document.getElementById("spec-name").value,
        speed: parseInt(document.getElementById("spec-speed").value),
        size: document.getElementById("spec-size").value,
        description: document.getElementById("spec-desc").value,
        flavor_text: document.getElementById("spec-flavor").value // NEW: Added Flavor
    };
    const res = await fetch("/admin/add-species", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
    const data = await res.json();
    alert(data.message);
}

async function submitClass() {
    const payload = {
        name: document.getElementById("cls-name").value,
        hit_die: parseInt(document.getElementById("cls-hitdie").value),
        primary_ability: document.getElementById("cls-primary").value,
        spellcasting_ability: document.getElementById("cls-spell-stat").value || null,
        description: document.getElementById("cls-desc").value,
        flavor_text: document.getElementById("cls-flavor").value // NEW: Added Flavor
    };
    const res = await fetch("/admin/add-class", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
    const data = await res.json();
    alert(data.message);
    loadClassOptions(); 
}