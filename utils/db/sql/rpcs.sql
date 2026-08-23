create or replace function populate_db ()
returns text
language plpgsql
as $$
declare
  v_count integer;
begin

  insert into seasons (id, name)
  values
    (2026, '2026/27'),
    (2025, '2025/26')
  on conflict do nothing;
  get diagnostics v_count = row_count;
  raise notice '  📅 Temporades processades (% noves files inserides)', v_count;

  insert into people (id, name, first_surname, second_surname, email, description, clau_soci)
  values
    (1, 'Aina', 'Solé', 'Sotillo', 'ainasole22@gmail.com', null, null),
    (2, 'Víctor', 'Arbó', 'Sangüesa', 'victorarbo@gmail.com', null, null),
    (3, 'Xavier', 'Solé', 'Palacín', 'fxavsp@gmail.com', null, 78670),
    (4, 'Roger', 'Solé', 'Sotillo', 'rogersolesotillo@gmail.com', null, 174260),
    (5, 'Marisa', 'Solé', 'Palacín', null, null, 34205),
    (6, 'Sara', 'Pascual', 'Luna', null, null, null),
    (7, 'Arlet', 'Solé', 'Pascual', null, null, null),
    (8, 'Iolanda', 'Sotillo', 'Sáez', null, null, null),
    (9, 'Sergi', 'Solé', 'Palacín', null, 'Gran', null)
  on conflict do nothing;
  get diagnostics v_count = row_count;
  raise notice '  👤 Persones processades (% noves files inserides)', v_count;

  insert into seats (id, owner_id)
  values
    (1, 3),
    (2, 4),
    (3, 5)
  on conflict do nothing;
  get diagnostics v_count = row_count;
  raise notice '  💺 Seients processats (% noves files inserides)', v_count;

  insert into teams (id, name, shortname, tla)
  values (81, 'FC Barcelona', 'Barça', 'FCB')
  on conflict do nothing;
  get diagnostics v_count = row_count;
  raise notice '  ⚽ Equips processats (% noves files inserides)', v_count;

  insert into settings (home_team_id, season_id, open_requests_url) 
  values
    (81, 2026, 'https://www.fcbarcelona.cat/ca/fitxa/4510674'),
    (81, 2025, null)
  on conflict do nothing;
  get diagnostics v_count = row_count;
  raise notice '  ⚙️ Configuració processada (% noves files inserides)', v_count;

  insert into competitions (code, name, shortname, emblem)
  values
    ('PD', 'Primera Division', 'La Liga', 'https://crests.football-data.org/laliga.png'),
    ('CL', 'UEFA Champions League', 'Champions', 'https://crests.football-data.org/CL.png'),
    ('CDR', 'Copa Del Rey', 'Copa', 'https://upload.wikimedia.org/wikipedia/commons/b/ba/Copa_Del_Rey_Official_Logo.png'),
    ('SDE', 'Supercopa de España', 'Supercopa', 'https://es.wikipedia.org/wiki/Archivo:Supercopa_de_Espa%C3%B1a_Logo.png')
  on conflict do nothing;
  get diagnostics v_count = row_count;
  raise notice '🏆 Competicions processades (% noves files inserides)', v_count;

  insert into matches (id, season_id, competition_code, home_team_id, away_team_id, date, status) values (544470, 2025, 'CDR', 81, 78, '2026-03-03 19:00:00+00', 'FINISHED')
  on conflict do nothing;

  return '✅ Base de dades poblada correctament';
end;
$$;

revoke execute on function populate_db()
from public;


create or replace function set_tickets_requested (
    p_match_id bigint,
    p_requested boolean
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
    updated_rows int;
begin
    update matches m
    set tickets_requested = p_requested
    where m.id = p_match_id
      and exists (
          select 1
          from settings s
          where s.home_team_id = m.home_team_id
            and s.season_id = m.season_id
      );

    get diagnostics updated_rows = row_count;

    return updated_rows > 0;
end;
$$;

revoke execute on function set_tickets_requested(bigint, boolean)
from public;
grant execute on function set_tickets_requested(bigint, boolean)
to authenticated;


create or replace function add_missing_matches()
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
    inserted_rows int;
begin
    insert into matches (id, season_id, competition_code, home_team_id, away_team_id, date, status) values (544470, 2025, 'CDR', 81, 78, '2026-03-03 19:00:00+00', 'FINISHED')
    on conflict do nothing;

    get diagnostics inserted_rows = row_count;
    return inserted_rows > 0;
end;
$$;

revoke execute on function add_missing_matches()
from public;
grant execute on function add_missing_matches()
to authenticated;