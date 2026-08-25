drop view if exists match_details;
create or replace view match_details
with (security_invoker = true)
as
select
    m.id,
    m.season_id,
    m.home_team_id,
    m.away_team_id,
    m.date,
    m.status,
    m.matchday,
    m.tickets_open,
    m.tickets_requested,
    m.request_deadline,

    c.code as competition_code,
    c.name as competition_name,
    c.shortname as competition_shortname,
    c.emblem as competition_emblem,

    home.name as home_team_name,
    home.shortname as home_team_shortname,
    home.tla as home_team_tla,
    home.crest as home_team_crest,

    away.name as away_team_name,
    away.shortname as away_team_shortname,
    away.tla as away_team_tla,
    away.crest as away_team_crest
from matches m
join competitions c
    on c.code = m.competition_code
join teams home
    on home.id = m.home_team_id
join teams away
    on away.id = m.away_team_id;

drop view if exists attendance_stats;
create or replace view attendance_stats
with (security_invoker = true)
as
select
    a.person_id,
    p.name,
    p.first_surname,
    p.second_surname,
    p.description,
    m.season_id,
    count(*) as matches_attended
from attendance a
join people p
    on p.id = a.person_id
join matches m
    on m.id = a.match_id
join settings s
    on s.season_id = m.season_id
    and s.home_team_id = m.home_team_id
<<<<<<< HEAD
where m.status = 'FINISHED'
  and a.person_id is not null
  and m.date > '2025-11-01' --abans no teniem abonament
=======
where a.person_id is not null
    and m.date > '2025-11-01' --abans no teniem abonament
>>>>>>> b443847 (feat: improve stats section, remove FINISHED from attendance)
group by
    a.person_id,
    p.name,
    p.first_surname,
    p.second_surname,
    p.description,
    m.season_id;

drop view if exists attendance_details;
create or replace view attendance_details
with (security_invoker = true)
as
select
    a.match_id,
    a.seat_id,
    a.person_id,
    p.name,
    p.first_surname,
    p.second_surname,
    p.description,
    s.owner_id,
    m.season_id,
    m.date,
    m.status,
    home.name as home_team_name,
    home.shortname as home_team_shortname,
    away.name as away_team_name,
    away.shortname as away_team_shortname,
    c.name as competition_name,
    c.shortname as competition_shortname
from attendance a
join people p
    on p.id = a.person_id
join seats s
    on s.id = a.seat_id
join matches m
    on m.id = a.match_id
join teams home
    on home.id = m.home_team_id
join teams away
    on away.id = m.away_team_id
join competitions c
    on c.code = m.competition_code;

drop view if exists seat_details;
create or replace view seat_details
with (security_invoker = true)
as
select
    s.id,
    s.owner_id,
    p.name as owner_name,
    p.clau_soci
from seats s
join people p
    on p.id = s.owner_id;

drop view if exists match_ticket_stats;
<<<<<<< HEAD
create or replace view match_ticket_stats as
=======
create or replace view match_ticket_stats
with (security_invoker = true)
as
>>>>>>> b443847 (feat: improve stats section, remove FINISHED from attendance)
select 
    s.name as season_name,
    m.season_id,
    count(m.id) as available_matches,
    count(m.id) filter (where m.tickets_requested = true) as requested_matches,
    count(m.id) filter (where m.tickets_requested = false OR m.tickets_requested is null) as not_requested_matches,
    round(
        (count(m.id) filter (where m.tickets_requested = TRUE)::numeric / nullif(count(m.id), 0)) * 100, 
        1
    ) as requested_percentage
from matches m
join seasons s on s.id = m.season_id
where m.home_team_id = 81
and m.date > '2025-11-01'
and (m.date < now() or m.tickets_open or m.tickets_requested)
group by m.season_id, s.name
order by m.season_id desc;

revoke all on match_details from anon;
revoke all on attendance_stats from anon;
revoke all on attendance_details from anon;
revoke all on seat_details from anon;
revoke all on match_ticket_stats from anon;
grant select on match_details to authenticated;
grant select on attendance_stats to authenticated;
grant select on attendance_details to authenticated;
grant select on seat_details to authenticated;
grant select on match_ticket_stats to authenticated;