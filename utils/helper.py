import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError, FileNotFoundError:
        return {}


def load_data_dir_file(filename: str):
    path = os.path.join(DATA_DIR, filename)
    return load_file(path)


def load_settings():
    return load_data_dir_file("settings.json")


def load_matches():
    return load_data_dir_file("matches.json")


def load_people():
    return load_data_dir_file("people.json")


def save_data(data, filename, directory=DATA_DIR):
    out = os.path.join(directory, filename)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_list_dicts_updated(
    new_data: list[dict], filename: str, directory: str = DATA_DIR
) -> bool:
    """Check if the new info is different from the existing info in the specified file."""
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return True
    existing_data = load_file(path)
    if not isinstance(existing_data, list) or not all(
        isinstance(item, dict) for item in existing_data
    ):
        raise TypeError(
            f"Expected a list of dicts in {filename}, but got "
            f"{type(existing_data).__name__}"
        )
    for new_item in new_data:
        if not any(
            all(
                k in existing_item and existing_item[k] == new_item[k] for k in new_item
            )
            for existing_item in existing_data
        ):
            return True
    return False


def is_dict_updated(new_data: dict, filename: str, directory: str = DATA_DIR) -> bool:
    """Check if the new info is different from the existing info in the specified file."""
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return True

    existing_data = load_file(path)
    if not isinstance(existing_data, dict):
        raise TypeError(
            f"Expected a dict in {filename}, but got {type(existing_data).__name__}"
        )
    for key, value in new_data.items():
        if key not in existing_data or value != existing_data[key]:
            return True
    return False
