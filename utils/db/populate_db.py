from postgrest import APIError

from utils.db.supabase import supabase


def populate_db():
    try:
        response = supabase.rpc("populate_db").execute()
    except APIError as e:
        print(f"(!) ERROR: Occurred while populating the database: {e}")
    else:
        print(response.data)


if __name__ == "__main__":
    populate_db()
