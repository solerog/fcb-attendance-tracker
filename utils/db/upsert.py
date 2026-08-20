import argparse

from postgrest import APIError

from utils.db.supabase import supabase
from utils.helper import load_data_dir_file


def upsert_json_supabase(table: str, filename: str):
    if not table or not filename:
        raise ValueError("Both table and file names must be provided.")
    if not filename.endswith(".json"):
        raise ValueError("File name must be a JSON file with the extension")
    try:
        response = supabase.table(table).upsert(load_data_dir_file(filename)).execute()
    except APIError as e:
        print(f"(!) ERROR: Occurred while upserting data into {table}: {e}")
    else:
        print(response.data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Insert JSON data into a Supabase table."
    )
    parser.add_argument("table", type=str, help="The name of the Supabase table.")
    parser.add_argument(
        "filename",
        type=str,
        help="The name of the JSON file to insert.",
    )
    args = parser.parse_args()
    upsert_json_supabase(args.table, args.filename)
