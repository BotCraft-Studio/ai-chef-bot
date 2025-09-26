# app/storage.py
import json
import os
import threading
from typing import List, Tuple, Optional

# data.json будет лежать рядом с папкой app
DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
_LOCK = threading.Lock()

_DEFAULT = {
    "users": {},
    "next_recipe_id": 1
}

def init_db():
    """Создаёт файл data.json если не существует (вызывается в main.py)."""
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(_DEFAULT, f, ensure_ascii=False, indent=2)

def _read():
    init_db()
    with _LOCK:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                # если файл повреждён — перезапишем дефолтом
                return _DEFAULT.copy()

def _write(data):
    with _LOCK:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def upsert_user(user_id: int, daily_time: Optional[str]=None, enabled: Optional[int]=None):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "daily_time": None,
            "enabled": 0,
            "ingredients": [],
            "saved_recipes": [],
            "flags": {"await_manual": False, "busy": False, "last_ingredients": []}
        }
    if daily_time is not None:
        data["users"][uid]["daily_time"] = daily_time
    if enabled is not None:
        data["users"][uid]["enabled"] = enabled
    _write(data)

def add_ingredients(user_id: int, items: List[str]):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        upsert_user(user_id)
        data = _read()
    current = data["users"][uid]["ingredients"]
    for it in items:
        if it not in current:
            current.append(it)
    data["users"][uid]["flags"]["last_ingredients"] = items
    _write(data)

def list_ingredients(user_id: int) -> List[Tuple[int, str, Optional[str]]]:
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        return []
    return [(i+1, name, None) for i, name in enumerate(data["users"][uid]["ingredients"])]

def clear_ingredients(user_id: int):
    data = _read()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]["ingredients"] = []
        data["users"][uid]["flags"]["last_ingredients"] = []
        _write(data)

def set_flag(user_id: int, name: str, value):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        upsert_user(user_id)
        data = _read()
    data["users"][uid]["flags"][name] = value
    _write(data)

def get_flag(user_id: int, name: str):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        return None
    return data["users"][uid]["flags"].get(name)

def save_recipe_for_user(user_id: int, title: str, text: str, ingredients: List[str]):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        upsert_user(user_id)
        data = _read()
    rid = data.get("next_recipe_id", 1)
    rec = {"id": rid, "title": title, "text": text, "ingredients": ingredients}
    data["users"][uid]["saved_recipes"].append(rec)
    data["next_recipe_id"] = rid + 1
    _write(data)
    return rec

def list_saved_recipes(user_id: int):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        return []
    return data["users"][uid]["saved_recipes"]

def get_last_ingredients(user_id: int):
    data = _read()
    uid = str(user_id)
    if uid not in data["users"]:
        return []
    return data["users"][uid]["flags"].get("last_ingredients", [])
