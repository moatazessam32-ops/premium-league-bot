import json
import os

DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

PLAYER_DATA_FILE = os.path.join(DATA_DIR, "player_data.json")
MATCH_FILE = os.path.join(DATA_DIR, "match_data.json")

DEFAULT_ELO = 50

MAPS = [
    "Sub Base",
    "Black Widow",
    "Mexico",
    "Ankara",
    "Port",
    "Compound",
    "EAGLE EYE 2.0"
]

# ================= MAP NAME NORMALIZATION =================
def normalize_map_name(name):
    """Normalize incoming map name to match MAPS list exactly."""
    if not name:
        return None

    name = name.strip().lower()

    # Exact match
    for m in MAPS:
        if m.lower() == name:
            return m

    # Ignore spaces, underscores
    for m in MAPS:
        if name.replace(" ", "").replace("_", "") == m.lower().replace(" ", "").replace("_", ""):
            return m

    # Fuzzy match
    for m in MAPS:
        if name in m.lower():
            return m

    return None


# ================= JSON HANDLERS =================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================= PLAYER INITIALIZATION =================
def ensure_player(pid):
    pid = str(pid)
    data = load_json(PLAYER_DATA_FILE)

    if pid not in data:
        data[pid] = {
            "elo": DEFAULT_ELO,
            "wins": 0,
            "losses": 0,
            "cancels": 0,
            "games": 0,
            "warnings": 0,
            "cooldown": False,
            "maps": {m: {"wins": 0, "losses": 0, "cancels": 0} for m in MAPS}
        }
        save_json(PLAYER_DATA_FILE, data)

    # Ensure all fields exist for old players
    if "warnings" not in data[pid]:
        data[pid]["warnings"] = 0
    if "cooldown" not in data[pid]:
        data[pid]["cooldown"] = False

    # Ensure maps exist
    if "maps" not in data[pid]:
        data[pid]["maps"] = {m: {"wins": 0, "losses": 0, "cancels": 0} for m in MAPS}

    # Ensure each map has cancel counter
    for m in MAPS:
        if m not in data[pid]["maps"]:
            data[pid]["maps"][m] = {"wins": 0, "losses": 0, "cancels": 0}

        if "cancels" not in data[pid]["maps"][m]:
            data[pid]["maps"][m]["cancels"] = 0

    save_json(PLAYER_DATA_FILE, data)
    return data


# ================= ELO =================
def get_player_elo(pid):
    data = ensure_player(pid)
    return data[str(pid)]["elo"]

def update_player_elo(pid, change):
    data = ensure_player(pid)
    pid = str(pid)

    old = data[pid]["elo"]
    new = old + change

    data[pid]["elo"] = new
    save_json(PLAYER_DATA_FILE, data)

    return old, new


# ================= MATCH STATS =================
def add_win(pid, map_name):
    map_name = normalize_map_name(map_name)
    if map_name is None:
        return

    data = ensure_player(pid)
    pid = str(pid)

    data[pid]["wins"] += 1
    data[pid]["games"] += 1
    data[pid]["maps"][map_name]["wins"] += 1

    save_json(PLAYER_DATA_FILE, data)

def add_loss(pid, map_name):
    map_name = normalize_map_name(map_name)
    if map_name is None:
        return

    data = ensure_player(pid)
    pid = str(pid)

    data[pid]["losses"] += 1
    data[pid]["games"] += 1
    data[pid]["maps"][map_name]["losses"] += 1

    save_json(PLAYER_DATA_FILE, data)

def add_cancel(pid, map_name=None):
    """Record a cancel, including map cancel if map is known."""
    data = ensure_player(pid)
    pid = str(pid)

    data[pid]["cancels"] += 1

    # Cancel on map level
    if map_name:
        map_name = normalize_map_name(map_name)
        if map_name:
            data[pid]["maps"][map_name]["cancels"] += 1

    save_json(PLAYER_DATA_FILE, data)


# ================= PLAYER PROFILE STATS =================
def get_player_stats(pid):
    data = ensure_player(pid)
    pid = str(pid)
    p = data[pid]

    return {
        "wins": p["wins"],
        "losses": p["losses"],
        "cancels": p["cancels"],
        "games": p["games"],
        "warnings": p.get("warnings", 0),
        "cooldown": p.get("cooldown", False)
    }

def get_map_stats(pid):
    data = ensure_player(pid)
    pid = str(pid)
    return data[pid]["maps"]


# ================= AVERAGE ELO =================
def average_elo_from_members(members):
    if not members:
        return 0
    return sum(get_player_elo(m.id) for m in members) // len(members)


# ================= MATCH ID =================
def load_match_id():
    data = load_json(MATCH_FILE)
    return data.get("last_match_id", 0)

def save_match_id(mid):
    save_json(MATCH_FILE, {"last_match_id": mid})
