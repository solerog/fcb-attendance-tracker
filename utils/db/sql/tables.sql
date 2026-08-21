drop table if exists seasons cascade;
create table seasons (
    id smallint primary key,
    name text not null unique
);
alter table seasons enable row level security;
grant select on seasons to authenticated;
create policy "Authenticated users can read seasons"
on seasons
for select
to authenticated
using (true);

drop table if exists people cascade;
create table people (
    id smallint primary key,
    name text not null,
    first_surname text not null,
    second_surname text not null,
    email text,
    description text,
    clau_soci int
);
alter table people enable row level security;
grant select on people to authenticated;
create policy "Authenticated users can read people"
on people
for select
to authenticated
using (true);

drop table if exists competitions cascade;
create table competitions (
    code text not null primary key,
    name text not null,
    shortname text,
    emblem text
);
alter table competitions enable row level security;
grant select on competitions to authenticated;
create policy "Authenticated users can read competitions"
on competitions
for select
to authenticated
using (true);

drop table if exists teams cascade;
create table teams (
    id int primary key,
    name text not null,
    shortname text not null,
    tla text not null,
    crest text
);
alter table teams enable row level security;
grant select on teams to authenticated;
create policy "Authenticated users can read teams"
on teams
for select
to authenticated
using (true);

drop table if exists matches cascade;
create table matches (
    id bigint primary key,
    season_id smallint not null references seasons(id),
    competition_code text not null references competitions(code),
    home_team_id int not null references teams(id),
    away_team_id int not null references teams(id),
    date timestamptz not null,
    status text not null,
    matchday smallint,
    tickets_open boolean not null default false,
    tickets_requested boolean not null default false,
    request_deadline timestamptz,
    constraint different_teams
        check (home_team_id <> away_team_id)
);
alter table matches enable row level security;
grant select on matches to authenticated;
create policy "Authenticated users can read matches"
on matches
for select
to authenticated
using (true);

drop table if exists seats cascade;
create table seats (
  id smallint primary key,
  owner_id smallint not null references people(id)
);
alter table seats enable row level security;
grant select on seats to authenticated;
create policy "Authenticated users can read seats"
on seats
for select
to authenticated
using (true);

drop table if exists attendance cascade;
create table attendance (
    match_id bigint not null references matches(id) on delete cascade,
    seat_id smallint not null references seats(id) on delete cascade,
    person_id smallint references people(id),
    primary key (match_id, seat_id),
    constraint attendance_one_seat_per_person
        unique (match_id, person_id)
);
alter table attendance enable row level security;
grant select, insert, update, delete on attendance to authenticated;
create policy "Authenticated users can read attendance"
on attendance
for select
to authenticated
using (true);
create policy "Authenticated users can insert attendance"
on attendance
for insert
to authenticated
with check (true);
create policy "Authenticated users can update attendance"
on attendance
for update
to authenticated
using (true)
with check (true);
create policy "Authenticated users can delete attendance"
on attendance
for delete
to authenticated
using (true);

drop table if exists settings cascade;
create table settings (
    home_team_id int not null references teams(id) on delete cascade,
    season_id smallint not null references seasons(id) on delete cascade,
    open_requests_url text,
    primary key (home_team_id, season_id)
);
alter table settings enable row level security;
grant select on settings to authenticated;
create policy "Authenticated users can read settings"
on settings
for select
to authenticated
using (true);

drop table if exists processed_emails cascade;
create table processed_emails (
    locator text primary key,
    match_id bigint references matches(id) on delete set null,
    registration_date timestamptz,
    processed_at timestamptz not null default now()
);
alter table processed_emails enable row level security;
grant select on processed_emails to authenticated;
create policy "Authenticated users can manage processed emails"
on processed_emails
for all
to authenticated
using (true)
with check (true);
