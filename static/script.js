let currentPool = []; // Store the dice rolls globally
let chosenSetIndex = null; // Track which set they picked

window.onload = async function() {
    await checkAuth(); 
    await loadOptions();
};

async function checkAuth() {
    const res = await fetch("/auth/me");
    const data = await res.json();

    if (data.authenticated) {
        document.getElementById("login-btn-container").style.display = "none";
        document.getElementById("user-info-container").style.display = "block";
        document.getElementById("display-username").innerText = data.user.username;

        // NEW: Check Admin Status
        if (data.is_admin) {
            document.getElementById("admin-controls").style.display = "block";
        }

        // Check if they already have a character
        await loadMyCharacter();
    } else {
        document.getElementById("login-btn-container").style.display = "block";
        document.getElementById("user-info-container").style.display = "none";
        document.getElementById("creator-section").style.display = "none"; 
        document.getElementById("character-sheet").style.display = "none";
    }
}

async function loadMyCharacter() {
    const res = await fetch("/my-character");
    const result = await res.json();

    if (result.found) {
        // HIDE Creator, SHOW Sheet
        document.getElementById("creator-section").style.display = "none";
        document.getElementById("creator-controls").style.display = "none"; // Hide name input
        document.getElementById("character-sheet").style.display = "block";

        renderSheet(result.data);
    } else {
        // SHOW Creator, HIDE Sheet
        document.getElementById("creator-section").style.display = "block";
        document.getElementById("creator-controls").style.display = "block";
        document.getElementById("character-sheet").style.display = "none";
    }
}

function renderSheet(char) {
    document.getElementById("sheet-name").innerText = char.character_name;
    document.getElementById("sheet-subtitle").innerText = `${char.species_name} ${char.class_name}`;
    document.getElementById("sheet-hitdie").innerText = char.hit_die;
    document.getElementById("sheet-speed").innerText = char.speed;

    const container = document.getElementById("sheet-stats");
    container.innerHTML = "";

    // Standard order
    const order = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];

    order.forEach(attr => {
        const score = char.attributes[attr];
        const modifier = Math.floor((score - 10) / 2);
        const sign = modifier >= 0 ? "+" : "";

        container.innerHTML += `
            <div style="background: #fff; border: 1px solid #bdc3c7; padding: 10px; border-radius: 5px;">
                <div style="font-size: 0.8rem; color: #7f8c8d; text-transform: uppercase; font-weight:bold;">${attr.substring(0,3)}</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #2c3e50;">${score}</div>
                <div style="font-size: 1rem; color: #e67e22; font-weight: bold;">${sign}${modifier}</div>
            </div>
        `;
    });
}

async function loadOptions() {
    try {
        const classRes = await fetch("/options/classes");
        const classes = await classRes.json();
        const classSelect = document.getElementById("class-select");
        classes.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.innerText = c.name;
            classSelect.appendChild(opt);
        });

        const speciesRes = await fetch("/options/species");
        const speciesList = await speciesRes.json();
        const speciesSelect = document.getElementById("species-select");
        speciesList.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.innerText = s.name;
            speciesSelect.appendChild(opt);
        });
    } catch (error) { console.error("Error loading options:", error); }
}

async function rollStats() {
    const charName = document.getElementById("char_name").value;

    if (!charName) {
        alert("Please enter a Character Name.");
        return;
    }

    const response = await fetch("/roll-stats/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ character_name: charName })
    });

    const data = await response.json();
    currentPool = data.pool; 
    
    const container = document.getElementById("output");
    container.innerHTML = "";
    
    document.getElementById("assignment-section").style.display = "none";

    if (data.pool) {
        data.pool.forEach((set, index) => {
            const setDiv = document.createElement("div");
            setDiv.className = "stat-set";
            let html = `<h3 class="set-title">Set ${index + 1}</h3>`;
            set.forEach(stat => { html += `<div class="stat-box">${stat}</div>`; });
            
            html += `<button style="margin-top:10px; width:100%;" onclick="startAssignment(${index})">Select Set</button>`;
            
            setDiv.innerHTML = html;
            container.appendChild(setDiv);
        });
    }
}

function startAssignment(index) {
    chosenSetIndex = index;
    const selectedStats = currentPool[index];
    
    document.getElementById("output").style.display = "none";
    const assignSection = document.getElementById("assignment-section");
    assignSection.style.display = "block";
    
    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    const container = document.getElementById("stat-rows");
    container.innerHTML = "";

    attributes.forEach(attr => {
        const row = document.createElement("div");
        row.style.margin = "10px 0";
        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.alignItems = "center";

        let optionsHtml = `<option value="">--</option>`;
        selectedStats.forEach(num => {
            optionsHtml += `<option value="${num}">${num}</option>`;
        });

        row.innerHTML = `
            <label style="font-weight:bold; width: 120px; text-align:left;">${attr}:</label>
            <select class="attr-select" id="attr-${attr}" style="width: 100px;">
                ${optionsHtml}
            </select>
        `;
        container.appendChild(row);
    });
}

function cancelAssignment() {
    document.getElementById("assignment-section").style.display = "none";
    document.getElementById("output").style.display = "flex";
}

async function finalizeCharacter() {
    const classId = document.getElementById("class-select").value;
    const speciesId = document.getElementById("species-select").value;

    const attributes = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];
    const selectionMap = {};
    const usedValues = [];

    for (let attr of attributes) {
        const val = document.getElementById(`attr-${attr}`).value;
        if (!val) {
            alert(`Please assign a value for ${attr}`);
            return;
        }
        selectionMap[attr] = parseInt(val);
        usedValues.push(parseInt(val));
    }

    const originalSet = [...currentPool[chosenSetIndex]].sort((a,b) => a-b);
    const selectedSet = [...usedValues].sort((a,b) => a-b);

    if (JSON.stringify(originalSet) !== JSON.stringify(selectedSet)) {
        alert("You must use the exact numbers from your rolled set! (Check for duplicates)");
        return;
    }

    const response = await fetch("/confirm-selection/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            chosen_set_index: chosenSetIndex,
            class_id: parseInt(classId),
            species_id: parseInt(speciesId),
            attributes: selectionMap
        })
    });

    const result = await response.json();
    if (result.status === "success") {
        document.body.innerHTML = `
            <div class="container">
                <h1 style="color:#2ecc71">Character Complete!</h1>
                <p>Stats Assigned and Saved.</p>
                <button onclick="location.reload()">View Character Sheet</button>
            </div>
        `;
    } else {
        alert("Error: " + (result.detail || "Could not save character"));
    }
}