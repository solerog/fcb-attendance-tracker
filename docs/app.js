const supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);

const state = {
    user: null,
    initialized: false,

    homeTeamId: null,
    currentSeasonId: null,

    people: [],
    seats: [],

    upcomingMatches: [],
    calendarMatches: [],
    pastMatches: [],

    calendarVisible: 5,
    pastVisible: 2,

    homeOnly: false,
};


const loginScreen = document.getElementById("login-screen");
const appScreen = document.getElementById("app-screen");

const loginForm = document.getElementById("login-form");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const loginError = document.getElementById("login-error");
const loginButton = document.getElementById("login-button");

const logoutButton = document.getElementById("logout-button");
const userEmail = document.getElementById("user-email");

const upcomingMatchesContainer =
    document.getElementById("upcoming-matches");

const upcomingCount =
    document.getElementById("upcoming-count");

const calendarMatchesContainer =
    document.getElementById("calendar-matches");

const calendarLoadMoreButton =
    document.getElementById("calendar-load-more");

const calendarCount =
    document.getElementById("calendar-count");

const homeOnlyToggle =
    document.getElementById("home-only-toggle");

const statsSummary =
    document.getElementById("stats-summary");

const statsAttendance =
    document.getElementById("stats-attendance");

const pastMatchesContainer =
    document.getElementById("past-matches");

const pastLoadMoreButton =
    document.getElementById("past-load-more");


initializeAuth();


async function initializeAuth() {
    console.log("Inicialitzant autenticació");

    const {
        data: { session },
        error,
    } = await supabaseClient.auth.getSession();

    if (error) {
        console.error("Error obtenint sessió:", error);
        showLogin();
        return;
    }

    if (session?.user) {
        console.log(
            "Sessió existent:",
            session.user.email
        );

        state.user = session.user;

        await showApp();
    } else {
        showLogin();
    }

    supabaseClient.auth.onAuthStateChange(
        async (event, session) => {
            console.log(
                "Auth state changed:",
                event
            );

            if (
                event === "SIGNED_IN" &&
                session?.user
            ) {
                state.user = session.user;

                if (!state.initialized) {
                    await showApp();
                }
            }

            if (event === "SIGNED_OUT") {
                state.user = null;
                state.initialized = false;

                showLogin();
            }
        }
    );
}


async function handleLogin(event) {
    event.preventDefault();

    loginError.hidden = true;

    loginButton.disabled = true;
    loginButton.textContent =
        "Iniciant sessió...";

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    try {
        const {
            data,
            error,
        } = await supabaseClient.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            throw error;
        }

        if (!data.user) {
            throw new Error(
                "No s'ha pogut iniciar sessió."
            );
        }

        state.user = data.user;

        await showApp();
    } catch (error) {
        console.error(
            "Error iniciant sessió:",
            error
        );

        loginError.textContent =
            error.message ||
            "No s'ha pogut iniciar sessió.";

        loginError.hidden = false;
    } finally {
        loginButton.disabled = false;
        loginButton.textContent =
            "Iniciar sessió";
    }
}


async function handleLogout() {
    await supabaseClient.auth.signOut();
}


function showLogin() {
    console.log(
        "Mostrant pantalla de login"
    );

    state.user = null;
    state.initialized = false;

    appScreen.classList.add("hidden");
    loginScreen.classList.remove("hidden");

    passwordInput.value = "";
}


async function showApp() {
    console.log(
        "Mostrant aplicació"
    );

    if (!state.user) {
        showLogin();
        return;
    }

    loginScreen.classList.add("hidden");
    appScreen.classList.remove("hidden");

    userEmail.textContent =
        state.user.email ?? "";

    if (!state.initialized) {
        state.initialized = true;

        await initializeApp();
    }
}


async function initializeApp() {
    console.log(
        "Inicialitzant dades de l'aplicació"
    );

    try {
        await loadInitialData();

        renderUpcomingMatches();
        renderCalendarMatches();
        renderPastMatches();
        renderStats();

        await attachUpcomingAttendance();
    } catch (error) {
        console.error(
            "Error carregant l'aplicació:",
            error
        );

        upcomingMatchesContainer.innerHTML =
            renderErrorState(
                "No s'han pogut carregar les dades."
            );
    }
}


async function loadInitialData() {
    const [
        settingsResponse,
        peopleResponse,
        seatsResponse,
        upcomingResponse,
        calendarResponse,
        pastResponse,
        statsResponse,
    ] = await Promise.all([
        supabaseClient
            .from("settings")
            .select("*"),

        supabaseClient
            .from("people")
            .select("*")
            .order("id"),

        supabaseClient
            .from("seat_details")
            .select("*")
            .order("id"),

        supabaseClient
            .from("match_details")
            .select("*")
            .gte("date", new Date().toISOString())
            .or(
                "tickets_open.eq.true,tickets_requested.eq.true"
            )
            .order("date"),

        supabaseClient
            .from("match_details")
            .select("*")
            .gte("date", new Date().toISOString())
            .eq("tickets_open", false)
            .order("date"),

        supabaseClient
            .from("match_details")
            .select("*")
            .lt("date", new Date().toISOString())
            .order("date", {
                ascending: false,
            }),

        supabaseClient
            .from("attendance_stats")
            .select("*"),
    ]);

    const responses = [
        settingsResponse,
        peopleResponse,
        seatsResponse,
        upcomingResponse,
        calendarResponse,
        pastResponse,
        statsResponse,
    ];

    for (const response of responses) {
        if (response.error) {
            throw response.error;
        }
    }

    state.people =
        peopleResponse.data ?? [];

    state.seats =
        seatsResponse.data ?? [];

    const settings =
        settingsResponse.data ?? [];

    if (settings.length > 0) {
        state.homeTeamId =
            settings[0].home_team_id;

        state.currentSeasonId =
            settings[0].season_id;
    }

    state.upcomingMatches =
        upcomingResponse.data ?? [];

    state.calendarMatches =
        calendarResponse.data ?? [];

    state.pastMatches =
        pastResponse.data ?? [];

    state.attendanceStats =
        statsResponse.data ?? [];
}


async function attachUpcomingAttendance() {
    const matchIds =
        state.upcomingMatches.map(
            match => match.id
        );

    if (matchIds.length === 0) {
        return;
    }

    const {
        data,
        error,
    } = await supabaseClient
        .from("attendance")
        .select("*")
        .in("match_id", matchIds);

    if (error) {
        console.error(
            "Error carregant assistències:",
            error
        );

        return;
    }

    const attendanceByMatch =
        new Map();

    for (const item of data ?? []) {
        if (
            !attendanceByMatch.has(
                item.match_id
            )
        ) {
            attendanceByMatch.set(
                item.match_id,
                new Map()
            );
        }

        attendanceByMatch
            .get(item.match_id)
            .set(
                item.seat_id,
                item.person_id
            );
    }

    for (const match of state.upcomingMatches) {
        renderMatchAttendance(
            match.id,
            attendanceByMatch.get(
                match.id
            ) ?? new Map(),
            match.tickets_requested === true
        );
    }
}


async function loadMatchAttendance(
    matchId
) {
    const {
        data,
        error,
    } = await supabaseClient
        .from("attendance")
        .select("*")
        .eq("match_id", matchId);

    if (error) {
        console.error(error);
        return;
    }

    const attendanceBySeat =
        new Map(
            (data ?? []).map(item => [
                item.seat_id,
                item.person_id,
            ])
        );

    const match = state.upcomingMatches.find(m => m.id === matchId);
    const isLocked = match ? match.tickets_requested === true : false;

    renderMatchAttendance(
        matchId,
        attendanceBySeat,
        isLocked
    );
}


function renderMatchAttendance(
    matchId,
    attendanceBySeat,
    isLocked
) {
    const container =
        document.querySelector(
            `[data-attendance-match="${matchId}"]`
        );

    if (!container) {
        return;
    }

    // Obtenim totes les persones que tenen un seient assignat en aquest partit
    const allAssignedPersons = new Set(
        Array.from(attendanceBySeat.values())
            .filter(id => id !== null && id !== undefined)
            .map(Number)
    );

    container.innerHTML =
        state.seats
            .map(seat => {
                const currentSeatPersonId = attendanceBySeat.get(seat.id);

                // Persones assignades a la resta de seients (excloent l'actual)
                const otherSeatsAssigned = new Set(allAssignedPersons);
                if (currentSeatPersonId) {
                    otherSeatsAssigned.delete(Number(currentSeatPersonId));
                }

                return renderSeatSelector(
                    matchId,
                    seat,
                    currentSeatPersonId,
                    isLocked,
                    otherSeatsAssigned
                );
            })
            .join("");

    container
        .querySelectorAll(
            "select[data-seat-id]"
        )
        .forEach(select => {
            select.addEventListener(
                "change",
                handleAttendanceChange
            );
        });
}


function renderSeatSelector(
    matchId,
    seat,
    personId,
    isLocked,
    selectedPersonIdsInOtherSeats = new Set()
) {
    const options = [
        `
        <option value="">
            No assignat
        </option>
        `,
        ...state.people.map(person => {
            const isSelected = Number(personId) === Number(person.id);
            const isAlreadyTaken = !isSelected && selectedPersonIdsInOtherSeats.has(Number(person.id));

            return `
                <option
                    value="${person.id}"
                    ${isSelected ? "selected" : ""}
                    ${isAlreadyTaken ? "disabled" : ""}
                >
                    ${escapeHtml(`${person.name} ${person.first_surname}`)}${person.description ? escapeHtml(`\(${person.description}\)`) : ""}${isAlreadyTaken ? " (Ja assignat/da)" : ""}
                </option>
            `;
        }),
    ].join("");

    return `
        <div class="seat-assignment">
            <label>
                Seient ${seat.id} (${seat.owner_name})
            </label>

            <select
                data-match-id="${matchId}"
                data-seat-id="${seat.id}"
                ${isLocked ? "disabled" : ""}
            >
                ${options}
            </select>
        </div>
    `;
}


async function handleAttendanceChange(
    event
) {
    const select = event.target;

    const matchId =
        Number(
            select.dataset.matchId
        );

    const seatId =
        Number(
            select.dataset.seatId
        );

    const personId =
        select.value
            ? Number(select.value)
            : null;

    select.disabled = true;

    try {
        if (personId === null) {
            const { error } =
                await supabaseClient
                    .from("attendance")
                    .delete()
                    .eq(
                        "match_id",
                        matchId
                    )
                    .eq(
                        "seat_id",
                        seatId
                    );

            if (error) {
                throw error;
            }
        } else {
            const { error } =
                await supabaseClient
                    .from("attendance")
                    .upsert(
                        {
                            match_id: matchId,
                            seat_id: seatId,
                            person_id: personId,
                        },
                        {
                            onConflict:
                                "match_id,seat_id",
                        }
                    );

            if (error) {
                throw error;
            }
        }

        await loadMatchAttendance(
            matchId
        );

        await refreshStats();
    } catch (error) {
        console.error(
            "Error actualitzant assistència:",
            error
        );

        alert(
            error.message ||
            "No s'ha pogut actualitzar l'assistència."
        );

        await loadMatchAttendance(
            matchId
        );
    } finally {
        select.disabled = false;
    }
}


function renderUpcomingMatches() {
    const matches =
        state.upcomingMatches;

    upcomingCount.textContent =
        `${matches.length} partits`;

    if (matches.length === 0) {
        upcomingMatchesContainer.innerHTML =
            renderEmptyState(
                "No hi ha cap partit proper amb entrades obertes o demanades."
            );

        return;
    }

    upcomingMatchesContainer.innerHTML =
        matches
            .map(renderUpcomingMatch)
            .join("");

    document.querySelectorAll(".edit-match-button").forEach((button) => {
        button.addEventListener("click", () => {
            const matchCard = button.closest(".match-card");

            if (!matchCard) {
                console.error("No s'ha trobat el contenidor del partit");
                return;
            }

            // Desbloquejar dropdowns
            matchCard.querySelectorAll("select").forEach((select) => {
                select.disabled = false;
            });

            const ticketsToggle = matchCard.querySelector(".tickets-requested-toggle");

            ticketsToggle
                ?.closest(".toggle-control")
                ?.classList.remove("hidden");

            // Amagar el botó Editar
            button.classList.add("hidden");
        });
    });

    document
        .querySelectorAll(
            ".tickets-requested-toggle"
        )
        .forEach(toggle => {
            toggle.addEventListener(
                "change",
                handleTicketsRequestedChange
            );
        });
}


function renderUpcomingMatch(match) {
    const isHome =
        match.home_team_id ===
        state.homeTeamId;

    const competitionName =
        match.competition_shortname ??
        match.competition_name ??
        "";

    const ticketStatus =
        match.tickets_requested
            ? "Entrades demanades"
            : match.tickets_open
                ? "Entrades obertes"
                : "";

    const isLocked = match.tickets_requested === true;

    return `
        <article class="match-card match-card--visual">

            <div class="match-card-header">

                <div class="competition-info">

                    ${renderImage(
        match.competition_emblem,
        competitionName,
        "competition-emblem"
    )}

                    <span class="competition">
                        ${escapeHtml(
        competitionName
    )}
                    </span>

                </div>

                <span class="location-badge ${isHome
            ? "home"
            : "away"
        }">
                    ${isHome
            ? "🏠 Casa"
            : "✈️ Fora"
        }
                </span>

            </div>


            <div class="match-showcase">

                <div class="team">

                    ${renderImage(
            match.home_team_crest,
            match.home_team_name,
            "team-crest"
        )}

                    <span>
                        ${escapeHtml(
            match.home_team_shortname ??
            match.home_team_name
        )}
                    </span>

                </div>


                <div class="match-kickoff">

                    <time
                        datetime="${escapeHtml(
            match.date
        )}"
                    >
                        <strong>
                            ${formatMatchWeekday(
            match.date
        )}
                        </strong>
                        <strong>
                            ${formatMatchDay(
            match.date
        )}
                        </strong>

                        <span>
                            ${formatMatchTime(
            match.date
        )}
                        </span>

                    </time>

                </div>


                <div class="team">

                    ${renderImage(
            match.away_team_crest,
            match.away_team_name,
            "team-crest"
        )}

                    <span>
                        ${escapeHtml(
            match.away_team_shortname ??
            match.away_team_name
        )}
                    </span>

                </div>

            </div>


            <div class="match-card-footer">

                <div class="ticket-status ${match.tickets_requested
            ? "is-requested"
            : match.tickets_open
                ? "is-open"
                : ""
        }">

                    ${escapeHtml(
            ticketStatus ||
            "Sense entrades obertes"
        )}

                </div>

                <button
                    type="button"
                    class="edit-match-button ${isLocked ? "" : "hidden"}"
                    data-match-id="${match.id}"
                >
                    ✏️ Editar
                </button>

                <label class="toggle-control ${isLocked ? "hidden" : ""}">
                    <input
                        type="checkbox"
                        class="tickets-requested-toggle
                        ${match.tickets_requested ? "checked" : ""}"
                        data-match-id="${match.id}"
                    >

                    <span class="toggle-label">
                        Entrades demanades
                    </span>

                </label>

            </div>


            <div
                class="attendance-section attendance-selectors"
                data-attendance-match="${match.id}"
            >

                <div class="loading">
                    Carregant assistència...
                </div>

            </div>

        </article>
    `;
}


async function handleTicketsRequestedChange(
    event
) {
    const checkbox =
        event.target;

    const matchId =
        Number(
            checkbox.dataset.matchId
        );

    const requested =
        checkbox.checked;

    checkbox.disabled = true;

    try {
        const { error } =
            await supabaseClient.rpc(
                "set_tickets_requested",
                {
                    p_match_id: matchId,
                    p_requested: requested,
                }
            );

        if (error) {
            throw error;
        }

        const match =
            state.upcomingMatches.find(
                item =>
                    item.id === matchId
            );

        if (match) {
            match.tickets_requested =
                requested;
        }

        renderUpcomingMatches();

        await attachUpcomingAttendance();
    } catch (error) {
        console.error(
            "Error actualitzant les entrades:",
            error
        );

        checkbox.checked =
            !requested;

        alert(
            error.message ||
            "No s'ha pogut actualitzar l'estat de les entrades."
        );
    } finally {
        checkbox.disabled = false;
    }
}


function renderCalendarMatches() {
    let matches =
        [...state.calendarMatches];

    if (state.homeOnly) {
        matches = matches.filter(
            match =>
                match.home_team_id ===
                state.homeTeamId
        );
    }

    calendarCount.textContent =
        `${matches.length} partits`;

    const visibleMatches =
        matches.slice(
            0,
            state.calendarVisible
        );

    if (visibleMatches.length === 0) {
        calendarMatchesContainer.innerHTML =
            renderEmptyState(
                "No hi ha cap partit disponible."
            );

        calendarLoadMoreButton.hidden = true;

        return;
    }

    calendarMatchesContainer.innerHTML =
        visibleMatches
            .map(renderCalendarMatch)
            .join("");

    calendarLoadMoreButton.hidden =
        visibleMatches.length >=
        matches.length;
}


function renderCalendarMatch(match) {
    const isHome =
        match.home_team_id ===
        state.homeTeamId;

    const competitionName =
        match.competition_shortname ??
        match.competition_name ??
        "";

    return `
        <article class="match-row ${isHome
            ? "home-match"
            : "away-match"
        }">

            <div class="match-row-date">
                <strong>
                    ${formatMatchWeekday(match.date)}
                    ${formatMatchDay(match.date)}
                </strong>

                ${match.status === "TIMED"
            ? `<span>${formatMatchTime(match.date)}</span>`
            : ""
        }
            </div>


            <div class="match-row-teams">

                <div class="match-row-team">

                    <img
                        src="${match.home_team_crest || ""}"
                        alt="${match.home_team_name}"
                        class="match-row-crest"
                    >

                    <span>
                        ${match.home_team_shortname || match.home_team_name}
                    </span>
                </div>

                <div class="match-row-separator">-</div>

                <div class="match-row-team">

                    <img
                        src="${match.away_team_crest || ""}"
                        alt="${match.away_team_name}"
                        class="match-row-crest"
                    >

                    <span>
                        ${match.away_team_shortname || match.away_team_name}
                    </span>
                </div>
            </div>

            <div class="match-row-info">

                <div class="match-row-competition">

                    ${match.competition_emblem
            ? `
                            <img
                                src="${match.competition_emblem}"
                                alt=""
                                class="competition-emblem"
                            >
                        `
            : ""
        }

                    <span>
                        ${match.competition_shortname || match.competition_name}
                    </span>

                </div>

                <span class="home-away-badge ${isHome ? "is-home" : "is-away"}">
                    ${isHome ? "🏠 Casa" : "✈️ Fora"}
                </span>

            </div>

        </article>
    `;
}


function renderPastMatches() {
    const matches =
        state.pastMatches;

    const visibleMatches =
        matches.slice(
            0,
            state.pastVisible
        );

    if (visibleMatches.length === 0) {
        pastMatchesContainer.innerHTML =
            renderEmptyState(
                "Encara no hi ha partits anteriors."
            );

        pastLoadMoreButton.hidden = true;

        return;
    }

    pastMatchesContainer.innerHTML =
        visibleMatches
            .map(renderPastMatch)
            .join("");

    pastLoadMoreButton.hidden =
        visibleMatches.length >=
        matches.length;

    document
        .querySelectorAll(
            ".edit-attendance-button"
        )
        .forEach(button => {
            button.addEventListener(
                "click",
                () => {
                    openAttendanceEditor(
                        Number(
                            button.dataset.matchId
                        )
                    );
                }
            );
        });
}


function renderPastMatch(match) {
    return `
        <article class="match-row match-row--past">

            <div class="match-row-date">

                <strong>
                    ${formatMatchDay(
        match.date
    )}
                </strong>

                <span>
                    ${formatMatchTime(
        match.date
    )}
                </span>

            </div>


            <div class="match-row-main">

                <div class="match-row-teams match-row-teams--visual">

                    ${renderImage(
        match.home_team_crest,
        match.home_team_name,
        "match-row-crest"
    )}

                    <span>
                        ${escapeHtml(
        match.home_team_shortname ??
        match.home_team_name
    )}
                    </span>

                    <strong>—</strong>

                    <span>
                        ${escapeHtml(
        match.away_team_shortname ??
        match.away_team_name
    )}
                    </span>

                    ${renderImage(
        match.away_team_crest,
        match.away_team_name,
        "match-row-crest"
    )}

                </div>

            </div>


            <button
                class="secondary-button edit-attendance-button"
                type="button"
                data-match-id="${match.id}"
            >
                Editar assistència
            </button>

        </article>
    `;
}


function renderStats() {
    const totalMatches =
        state.pastMatches.filter(
            match =>
                match.home_team_id ===
                state.homeTeamId
        ).length;

    const totalAttendance =
        state.attendanceStats
            .reduce(
                (
                    total,
                    person
                ) =>
                    total +
                    Number(
                        person.matches_attended
                    ),
                0
            );

    statsSummary.innerHTML = `
        ${renderStatCard(
        "Partits jugats",
        totalMatches
    )}

        ${renderStatCard(
        "Assistències",
        totalAttendance
    )}
    `;

    const statsByPerson =
        new Map(
            state.attendanceStats.map(
                item => [
                    item.person_id,
                    item,
                ]
            )
        );

    statsAttendance.innerHTML =
        state.people
            .map(person => {
                const stat =
                    statsByPerson.get(
                        person.id
                    );

                const attended =
                    Number(
                        stat?.matches_attended ?? 0
                    );

                return `
                    <div class="stats-row">

                        <div class="stats-person">

                            <div class="person-avatar">
                                ${getInitials(
                    person.name,
                    person.first_surname
                )}
                            </div>

                            <span class="person-name">
                                ${escapeHtml(
                    `${person.name} ${person.first_surname}`
                )}
                            </span>

                        </div>

                        <span class="stats-value">
                            ${attended}
                        </span>

                    </div>
                `;
            })
            .join("");
}


function renderStatCard(
    label,
    value
) {
    return `
        <div class="stat-card">

            <span class="stat-label">
                ${escapeHtml(label)}
            </span>

            <strong>
                ${escapeHtml(
        String(value)
    )}
            </strong>

        </div>
    `;
}


async function refreshStats() {
    const {
        data,
        error,
    } = await supabaseClient
        .from("attendance_stats")
        .select("*");

    if (error) {
        console.error(
            "Error actualitzant estadístiques:",
            error
        );

        return;
    }

    state.attendanceStats =
        data ?? [];

    renderStats();
}


async function openAttendanceEditor(
    matchId
) {
    alert(
        `L'editor d'assistència del partit ${matchId} es pot afegir com a següent pas.`
    );
}


function renderImage(
    src,
    alt,
    className
) {
    if (!src) {
        return `
            <span
                class="${className} image-placeholder"
                aria-hidden="true"
            ></span>
        `;
    }

    return `
        <img
            class="${className}"
            src="${escapeHtml(src)}"
            alt="${escapeHtml(
        alt ?? ""
    )}"
            loading="lazy"
        >
    `;
}

function formatMatchWeekday(date) {
    return new Intl.DateTimeFormat(
        "ca-ES",
        {
            weekday: "long",
        }
    )
        .format(
            new Date(date)
        )
        .replace(",", "");
}


function formatMatchDay(date) {
    return new Intl.DateTimeFormat(
        "ca-ES",
        {
            day: "2-digit",
            month: "2-digit",
            year: "2-digit",
        }
    )
        .format(
            new Date(date)
        )
        .replace(",", "");
}


function formatMatchTime(date) {
    return new Intl.DateTimeFormat(
        "ca-ES",
        {
            hour: "2-digit",
            minute: "2-digit",
            hourCycle: "h23",
        }
    ).format(
        new Date(date)
    );
}


function formatDate(date) {
    return new Intl.DateTimeFormat(
        "ca-ES",
        {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        }
    ).format(
        new Date(date)
    );
}


function getInitials(
    name,
    surname
) {
    return (
        `${name?.[0] ?? ""}${surname?.[0] ?? ""}`
    ).toUpperCase();
}


function renderEmptyState(message) {
    return `
        <div class="empty-state">
            ${escapeHtml(message)}
        </div>
    `;
}


function renderErrorState(message) {
    return `
        <div class="error-state">
            ${escapeHtml(message)}
        </div>
    `;
}


function escapeHtml(value) {
    const element =
        document.createElement("div");

    element.textContent =
        value ?? "";

    return element.innerHTML;
}


/*
=========================================
EVENT LISTENERS
=========================================
*/

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await handleLogin(event);
});


logoutButton.addEventListener(
    "click",
    handleLogout
);


homeOnlyToggle.addEventListener(
    "change",
    event => {
        state.homeOnly =
            event.target.checked;

        state.calendarVisible = 5;

        renderCalendarMatches();
    }
);


calendarLoadMoreButton.addEventListener(
    "click",
    () => {
        state.calendarVisible += 5;

        renderCalendarMatches();
    }
);


pastLoadMoreButton.addEventListener(
    "click",
    () => {
        state.pastVisible += 2;

        renderPastMatches();
    }
);