# =============================================================================
# data_manager.py  (~130 Zeilen)
# =============================================================================

import json, os, random
from pathlib import Path
from datetime import date

DATA_DIR      = Path(__file__).parent.parent / "data"
USERS_FILE    = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

def _load(fp): return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
def _save(fp, d):
    DATA_DIR.mkdir(exist_ok=True)
    fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── User ─────────────────────────────────────────────────────────────────────

def get_user(tid: int) -> dict | None:
    return _load(USERS_FILE).get(str(tid))

def create_user(tid: int, username: str = None) -> dict:
    users  = _load(USERS_FILE)
    gruppe = random.choice(["gamification", "kontrolle"])
    user   = {
        "telegram_id":           tid,
        "username":              username or "Anonym",
        "gruppe":                gruppe,
        "ttm_stage":             None,
        "ttm_antworten":         [],
        "ttm_phase":             0,       # 0–2 während Onboarding
        "aktuelles_modul":       1,
        "abgeschlossene_module": 0,
        "session_aktiv":         False,
        "streak":                0,
        "last_active":           None,
        "badges":                [],
        "quests_gesamt":         0,
        "einwilligung":          False,
        "registriert_am":        date.today().isoformat(),
        "skalen_werte":          {},      # item_id → Antwort
    }
    users[str(tid)] = user
    _save(USERS_FILE, users)
    print(f"[DATA] Neuer Nutzer {tid} → {gruppe}")
    return user

def update_user(tid: int, updates: dict) -> dict:
    users = _load(USERS_FILE)
    key   = str(tid)
    if key not in users:
        raise ValueError(f"Nutzer {tid} nicht gefunden.")
    users[key].update(updates)
    _save(USERS_FILE, users)
    return users[key]


# ─── Session History (temporär) ───────────────────────────────────────────────

def get_history(tid: int) -> list:
    f = DATA_DIR / f"temp_{tid}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []

def add_message(tid: int, role: str, content: str):
    DATA_DIR.mkdir(exist_ok=True)
    h = get_history(tid)
    h.append({"role": role, "content": content})
    (DATA_DIR / f"temp_{tid}.json").write_text(
        json.dumps(h, ensure_ascii=False, indent=2), encoding="utf-8")

def clear_history(tid: int):
    f = DATA_DIR / f"temp_{tid}.json"
    if f.exists(): f.unlink()


# ─── Sessions (permanent) ─────────────────────────────────────────────────────

def save_session(tid: int, modul_nr: int, history: list,
                 summary: str = "", emotion_log: list = None):
    sessions = _load(SESSIONS_FILE)
    key      = str(tid)
    if key not in sessions:
        sessions[key] = []
    sessions[key].append({
        "modul":     modul_nr,
        "datum":     date.today().isoformat(),
        "n_msgs":    len(history),
        "summary":   summary,
        "emotions":  emotion_log or [],
        "history":   history,
    })
    _save(SESSIONS_FILE, sessions)


# ─── Export ───────────────────────────────────────────────────────────────────

def export_study_data() -> dict:
    users    = _load(USERS_FILE)
    sessions = _load(SESSIONS_FILE)
    out      = {"gamification": [], "kontrolle": []}
    for uid, user in users.items():
        g = user.get("gruppe", "kontrolle")
        if g in out:
            out[g].append({"user": user, "sessions": sessions.get(uid, [])})
    return out
