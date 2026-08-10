#!/usr/bin/env python3
"""Compute basic attendance stats and prepare assignment placeholders."""

import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_json(name, default):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name, data):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compute_stats(matches, attendance, members):
    counts = {m: 0 for m in members}
    total_played = 0
    for m in matches:
        mid = str(m.get("id"))
        if mid in attendance:
            total_played += 1
            for p in attendance[mid]:
                if p in counts:
                    counts[p] += 1
    stats = []
    for p in members:
        played = counts.get(p, 0)
        pct = (played / total_played * 100) if total_played else 0
        stats.append({"person": p, "played": played, "pct": round(pct, 1)})
    return {"total_matches": total_played, "by_person": stats}


def main():
    matches = load_json("matches.json", [])
    attendance = load_json("attendance.json", {})
    settings = load_json("settings.json", {})
    members = settings.get("members", [])
    stats = compute_stats(matches, attendance, members)
    save_json("stats.json", stats)
    print("Wrote data/stats.json")


if __name__ == "__main__":
    main()
