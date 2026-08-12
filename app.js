const TEAM_CREST = "https://crests.football-data.org/81.png";
const matchesGrid = document.getElementById("matchesGrid");
const summaryCards = document.getElementById("summaryCards");
const matchCount = document.getElementById("matchCount");
const clubCrest = document.getElementById("clubCrest");
const template = document.getElementById("matchCardTemplate");

async function loadData() {
    try {
        const [matchesResponse, teamResponse] = await Promise.all([
            fetch("./data/matches.json"),
            fetch("./data/fcb.json")
        ]);

        if (!matchesResponse.ok) {
            throw new Error("No s'ha pogut carregar la llista de partits.");
        }

        if (!teamResponse.ok) {
            throw new Error("No s'ha pogut carregar la informació del club.");
        }

        const matches = await matchesResponse.json();
        const team = await teamResponse.json();

        clubCrest.src = team.crest || TEAM_CREST;
        clubCrest.alt = team.name || "FC Barcelona";

        const upcoming = matches
            .filter((match) => new Date(match.date) > Date.now())
            .sort((a, b) => new Date(a.date) - new Date(b.date));

        if (!upcoming.length) {
            matchesGrid.innerHTML = '<div class="empty-state">No hi ha partits futurs programats.</div>';
            matchCount.textContent = "0 partits";
            summaryCards.innerHTML = "";
            return;
        }

        renderSummary(upcoming, team);
        renderMatches(upcoming, team);
        updateCountdowns();
        setInterval(updateCountdowns, 60000);
    } catch (error) {
        matchesGrid.innerHTML = `<div class="empty-state">${error.message}</div>`;
    }
}

function renderSummary(matches, team) {
    const nextMatch = matches[0];
    const nextDate = new Date(nextMatch.date);

    const cards = [
        { label: "Pròxim", value: formatShortDate(nextDate) },
        { label: "Rival", value: nextMatch.away_shortname || nextMatch.away_name },
        { label: "Partits", value: `${matches.length}` }
    ];

    summaryCards.innerHTML = cards
        .map(
            (card) => `
        <div class="summary-card">
          <span class="label">${card.label}</span>
          <strong>${card.value}</strong>
        </div>
      `
        )
        .join("");

    matchCount.textContent = `${matches.length} partits`;
}

function renderMatches(matches, team) {
    matchesGrid.innerHTML = "";

    matches.forEach((match) => {
        const card = template.content.cloneNode(true);

        const status = card.querySelector(".status-pill");
        const leagueTag = card.querySelector(".league-tag");
        const dateValue = card.querySelector(".date-value");
        const timeValue = card.querySelector(".time-value");
        const countdownValue = card.querySelector(".countdown-value");
        const homeName = card.querySelector(".team-block.home .team-name");
        const awayName = card.querySelector(".team-block.away .team-name");
        const homeCrest = card.querySelector(".team-block.home .team-crest");
        const awayCrest = card.querySelector(".team-block.away .team-crest");

        const kickoff = new Date(match.date);

        status.textContent = match.status ? normalizeStatus(match.status) : "Programat";
        leagueTag.textContent = match.league || "Lliga";
        homeName.textContent = team.shortname || team.name || "Barça";
        awayName.textContent = match.away_shortname || match.away_name || "Rival";
        homeCrest.src = team.crest || TEAM_CREST;
        homeCrest.alt = team.name || "FC Barcelona";
        awayCrest.src = match.away_crest || TEAM_CREST;
        awayCrest.alt = match.away_name || "Rival";

        dateValue.textContent = formatLongDate(kickoff);
        timeValue.textContent = formatTime(kickoff);
        countdownValue.dataset.target = kickoff.toISOString();

        matchesGrid.appendChild(card);
    });
}

function updateCountdowns() {
    const countdownEls = document.querySelectorAll(".countdown-value");

    countdownEls.forEach((el) => {
        const target = new Date(el.dataset.target);
        const diff = target.getTime() - Date.now();

        if (diff <= 0) {
            el.textContent = "Ja s’ha jugat";
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((diff / (1000 * 60)) % 60);

        if (days > 0) {
            el.textContent = `${days}d ${hours}h`;
            return;
        }

        if (hours > 0) {
            el.textContent = `${hours}h ${minutes}m`;
            return;
        }

        el.textContent = `${minutes}m`;
    });
}

function formatLongDate(date) {
    return new Intl.DateTimeFormat("ca-ES", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    }).format(date);
}

function formatShortDate(date) {
    return new Intl.DateTimeFormat("ca-ES", {
        day: "2-digit",
        month: "short"
    }).format(date);
}

function formatTime(date) {
    return new Intl.DateTimeFormat("ca-ES", {
        hour: "2-digit",
        minute: "2-digit"
    }).format(date);
}

function normalizeStatus(status) {
    const statusMap = {
        TIMED: "Programat",
        SCHEDULED: "Programat",
        LIVE: "En directe",
        FINISHED: "Finalitzat",
        CANCELLED: "Cancel·lat",
        POSTPONED: "Aplaçat"
    };

    return statusMap[status] || status;
}

loadData();
