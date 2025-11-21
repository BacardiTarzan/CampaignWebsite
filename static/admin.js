window.onload = async function() {
    loadDashboard();
};

async function loadDashboard() {
    const response = await fetch("/admin/dashboard");
    const characters = await response.json();
    const tbody = document.querySelector("#char-table tbody");
    tbody.innerHTML = "";

    characters.forEach(char => {
        const tr = document.createElement("tr");

        // 1. Format the Stats
        let statsDisplay = "Not Selected";
        if (char.chosen_set !== null && char.stat_pool) {
            // Grab the specific array the user chose (0, 1, or 2)
            const chosenStats = char.stat_pool[char.chosen_set];
            statsDisplay = `<span class="stat-summary">[ ${chosenStats.join(", ")} ]</span>`;
        }

        // 2. Format Status
        const status = char.is_locked ? "🔒 Locked" : "🔓 Open";

        tr.innerHTML = `
            <td>${char.discord_id}</td>
            <td>${char.character_name}</td>
            <td>${char.species_name || "-"} ${char.class_name || "-"}</td>
            <td>${statsDisplay}</td>
            <td>${status}</td>
            <td>
                <button class="unlock-btn" onclick="unlockPlayer('${char.discord_id}')">
                    Unlock / Reroll
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function unlockPlayer(discordId) {
    if(!confirm(`Are you sure you want to wipe data for ${discordId} and let them reroll?`)) return;

    const response = await fetch("/admin/unlock-player", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_discord_id: discordId })
    });
    
    const result = await response.json();
    if(result.status === "success") {
        alert("Player Unlocked!");
        loadDashboard(); // Refresh table
    }
}