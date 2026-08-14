const TEAM_CREST = "https://crests.football-data.org/81.png";
const matchesGrid = document.getElementById("matchesGrid");
const heroMatchCount = document.getElementById("heroMatchCount");
const calendarMatchCount = document.getElementById("calendarMatchCount");
const clubCrest = document.getElementById("clubCrest");
const featuredMatchContainer = document.getElementById("featuredMatch");
const template = document.getElementById("matchCardTemplate");

async function loadData() {
    try {
        const [matchesResponse, teamResponse, openRequestsResponse, competitionsResponse] = await Promise.all([
            fetch("./data/matches.json"),
            fetch("./data/fcb.json"),
            fetch("./data/open_ticket_requests.json").catch(() => ({ ok: false })),
            fetch("./data/competitions.json").catch(() => ({ ok: false }))
        ]);

        if (!matchesResponse.ok) {
            throw new Error("No s'ha pogut carregar la llista de partits.");
        }

        if (!teamResponse.ok) {
            throw new Error("No s'ha pogut carregar la informació del club.");
        }

        const matches = await matchesResponse.json();
        const team = await teamResponse.json();
        const openRequests = openRequestsResponse.ok ? await openRequestsResponse.json() : [];
        const competitions = competitionsResponse.ok ? await competitionsResponse.json() : [];

        const openRequestMap = new Map(
            openRequests.map((item) => [Number(item.match_id), item.request_deadline_local])
        );

        const competitionsMap = new Map(
            competitions.map((comp) => [String(comp.id).toUpperCase(), comp])
        );

        clubCrest.src = team.crest || TEAM_CREST;
        clubCrest.alt = team.name || "FC Barcelona";

        const upcoming = matches
            .filter((match) => new Date(match.date) > Date.now())
            .sort((a, b) => new Date(a.date) - new Date(b.date));

        if (!upcoming.length) {
            matchesGrid.innerHTML = '<div class="empty-state">No hi ha partits futurs programats.</div>';
            heroMatchCount.textContent = "0 partits";
            calendarMatchCount.textContent = "0 partits";
            featuredMatchContainer.innerHTML = '<div class="empty-state">No hi ha partits amb entrades obertes o demanades.</div>';
            return;
        }

        const openRequestedMatches = upcoming.filter((match) => openRequestMap.has(Number(match.id)));
        const listMatches = upcoming.filter((match) => !openRequestMap.has(Number(match.id)));

        renderFeaturedMatch(openRequestedMatches, team, openRequestMap, competitionsMap);
        renderMatches(listMatches, team, openRequestMap, competitionsMap);
        heroMatchCount.textContent = `${openRequestedMatches.length} partits`;
        calendarMatchCount.textContent = `${listMatches.length} partits`;
        updateCountdowns();
        setInterval(updateCountdowns, 60000);
    } catch (error) {
        matchesGrid.innerHTML = `<div class="empty-state">${error.message}</div>`;
        featuredMatchContainer.innerHTML = `<div class="empty-state">${error.message}</div>`;
    }
}

function renderFeaturedMatch(matches, team, openRequestMap, competitionsMap) {
    if (!matches.length) {
        featuredMatchContainer.innerHTML = '<div class="empty-state">No hi ha partits futurs amb entrades obertes o demanades.</div>';
        return;
    }

    featuredMatchContainer.innerHTML = matches
        .map((match) => {
            const competitionKey = String(match.competition_code || match.competition_id || "").toUpperCase();
            const competition = competitionsMap.get(competitionKey) || {};
            const competitionName = competition.name || competition.alias || "Competició";
            const competitionCrest = competition.crest || "";

            const kickoff = new Date(match.date);
            const deadline = openRequestMap.get(Number(match.id));
            const deadlineValue = deadline ? formatLongDateTime(new Date(deadline)) : "Per confirmar";

            return `
                <div class="featured-card">
                    <div class="featured-header">
                        <span class="featured-badge">
                        ${competitionCrest ? `<img src="${competitionCrest}" alt="${competitionName}" class="featured-comp-crest" />` : `<span class="featured-badge-icon">🏆</span>`}
                        ${competitionName}</span>
                        <span class="featured-tag">Entrades obertes</span>
                    </div>

                    <div class="featured-teams">
                        <div class="featured-team">
                            <img src="${team.crest || TEAM_CREST}" alt="${team.name || "FC Barcelona"}" />
                            <span>${team.shortname || team.name || "Barça"}</span>
                        </div>
                        <div class="featured-vs">VS</div>
                        <div class="featured-team">
                            <img src="${match.away_crest || TEAM_CREST}" alt="${match.away_name || "Rival"}" />
                            <span>${match.away_shortname || match.away_name || "Rival"}</span>
                        </div>
                    </div>

                    <div class="featured-meta">
                        <div class="featured-box">
                            <span class="label">Dia</span>
                            <strong>${formatLongDate(kickoff)}</strong>
                        </div>
                        <div class="featured-box">
                            <span class="label">Hora</span>
                            <strong>${formatTime(kickoff)}</strong>
                        </div>
                        <div class="featured-box">
                            <span class="label">Queda</span>
                            <strong class="countdown-value" data-target="${kickoff.toISOString()}">${getCountdownText(kickoff)}</strong>
                        </div>
                    </div>

                    <div class="featured-deadline">
                        <span>Data límit per demanar entrades</span>
                        <strong>${deadlineValue}</strong>
                    </div>
                </div>
            `;
        })
        .join("");
}

function renderMatches(matches, team, openRequestMap, competitionsMap) {
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

        const competitionKey = String(match.competition_code || match.competition_id || "").toUpperCase();
        const competition = competitionsMap.get(competitionKey) || {};
        const competitionName = competition.name || competition.alias || "Competició";

        const kickoff = new Date(match.date);
        const isTimed = match.status === "TIMED";
        const hasOpenRequests = openRequestMap.has(Number(match.id));

        status.textContent = isTimed ? "Horari confirmat" : normalizeStatus(match.status || "Programat");
        leagueTag.textContent = competitionName;
        homeName.textContent = team.shortname || team.name || "Barça";
        awayName.textContent = match.away_shortname || match.away_name || "Rival";
        homeCrest.src = team.crest || TEAM_CREST;
        homeCrest.alt = team.name || "FC Barcelona";
        awayCrest.src = match.away_crest || TEAM_CREST;
        awayCrest.alt = match.away_name || "Rival";

        dateValue.textContent = formatLongDate(kickoff);
        timeValue.textContent = isTimed ? formatTime(kickoff) : "Per confirmar";
        countdownValue.dataset.target = kickoff.toISOString();
        countdownValue.textContent = isTimed ? getCountdownText(kickoff) : "Hora pendent";

        if (hasOpenRequests) {
            const badge = card.querySelector(".status-pill");
            badge.textContent = "Entrades obertes";
            badge.style.background = "rgba(83, 209, 141, 0.15)";
            badge.style.color = "#53d18d";
        }

        matchesGrid.appendChild(card);
    });
}

function updateCountdowns() {
    const countdownEls = document.querySelectorAll(".countdown-value");

    countdownEls.forEach((el) => {
        const target = new Date(el.dataset.target);
        el.textContent = getCountdownText(target);
    });
}

function getCountdownText(date) {
    const diff = new Date(date).getTime() - Date.now();

    if (diff <= 0) {
        return "Ja s’ha jugat";
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((diff / (1000 * 60)) % 60);

    if (days > 0) {
        return `${days}d ${hours}h`;
    }

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }

    return `${minutes}m`;
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

function formatLongDateTime(date) {
    return new Intl.DateTimeFormat("ca-ES", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
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
