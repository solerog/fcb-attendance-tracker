#!/usr/bin/env python3
"""
Reset de la base de dades a Supabase:
1. Executa tables.sql (taules, RLS i polítiques)
2. Executa views.sql (vistes i permisos)
3. Executa rpcs.sql (funcions PL/pgSQL)
4. Crida a populate_db() per inicialitzar dades base
"""

import os
from pathlib import Path
from typing import Any, cast

import psycopg
from dotenv import load_dotenv

from actions.fetch_matches import sync_matches

load_dotenv()

# Directori on es troben els fitxers SQL
BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = Path.joinpath(BASE_DIR, "sql")

SQL_FILES = [
    SQL_DIR / "tables.sql",
    SQL_DIR / "views.sql",
    SQL_DIR / "rpcs.sql",
]


def get_db_connection() -> psycopg.Connection[Any]:
    print("📦 Connectant a Supabase...")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "Falta la variable d'entorn DATABASE_URL amb la cadena de connexió a Supabase."
        )
    return psycopg.connect(db_url)


def run_sql_file(cursor: psycopg.Cursor[Any], file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"No s'ha trobat el fitxer SQL: {file_path}")

    print(f"🔄 Creant {file_path.name}...")
    sql_content = file_path.read_text(encoding="utf-8")

    cursor.execute(cast(Any, sql_content))
    print(f"  ✅ {file_path.name} executat correctament.")


def reset_and_populate_database() -> None:
    conn = get_db_connection()
    print("  ✅ Connexió establerta.")

    try:
        with conn, conn.cursor() as cur:
            for sql_file in SQL_FILES:
                run_sql_file(cur, sql_file)

            print("\n📦 Poblant base de dades amb dades per defecte...")
            cur.execute("SELECT populate_db();")
            result = cur.fetchone()
            output_msg = result[0] if result else "Dades inserides."
            print(f"  {output_msg}")

    except Exception as error:
        print(f"\n❌ Error durant el reset de la base de dades: {error}")
        raise

    finally:
        conn.close()

    print("\n📦 Afegint partits, equips i competicions...")
    sync_matches()

    print("\n✨ Base de dades reinicialitzada i poblada amb èxit!")


if __name__ == "__main__":
    reset_and_populate_database()
