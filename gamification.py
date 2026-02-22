# =============================================================================
# gamification.py  (~180 Zeilen)
# -----------------------------------------------------------------------------
# Alle Spielmechaniken. Wird NUR aufgerufen wenn user["gruppe"] == "gamification".
# =============================================================================

from datetime import date, timedelta
from study_content import BADGES, BADGE_TRIGGERS, QUESTS, CLIFFHANGER


# ─── Streak ───────────────────────────────────────────────────────────────────

def update_streak(user: dict) -> dict:
    today    = date.today()
    last_str = user.get("last_active")

    if last_str:
        last = date.fromisoformat(last_str)
        if last == today:
            pass
        elif last == today - timedelta(days=1):
            user["streak"] = user.get("streak", 0) + 1
        else:
            user["streak"] = 1
    else:
        user["streak"] = 1

    user["last_active"] = today.isoformat()
    return user


def get_streak_message(streak: int) -> str | None:
    msgs = {
        3:  "🔥 3 Tage in Folge! Du bist auf einem echten Streak.",
        7:  "⚡ Eine Woche ohne Unterbrechung – das ist beeindruckend.",
        14: "💎 Zwei Wochen. Du gehörst zu den engagiertesten Teilnehmenden.",
    }
    return msgs.get(streak)


# ─── Badges ───────────────────────────────────────────────────────────────────

def check_new_badges(user: dict) -> list[str]:
    """Prüft nach Session-Abschluss welche Badges neu verdient wurden."""
    earned     = user.get("badges", [])
    new_badges = []

    def award(key: str):
        if key in BADGES and key not in earned:
            earned.append(key)
            new_badges.append(BADGES[key])

    if user.get("abgeschlossene_module", 0) >= 1: award("erster_start")
    if user.get("streak", 0) >= 3:                award("streak_3")
    if user.get("streak", 0) >= 7:                award("streak_7")
    if user.get("abgeschlossene_module", 0) >= 3: award("modul_3")
    if user.get("quests_gesamt", 0) >= len(QUESTS): award("alle_quests")
    if user.get("abgeschlossene_module", 0) >= len(QUESTS): award("abschluss")

    user["badges"] = earned
    return new_badges


def try_mid_session_badge(user: dict, trigger: str) -> str | None:
    """
    Gibt Badge-Text zurück wenn Trigger neu und noch nicht vergeben.
    Wird mid-conversation aufgerufen – erzeugt den Überraschungseffekt.
    """
    if not trigger:
        return None

    badge_key = BADGE_TRIGGERS.get(trigger)
    if not badge_key:
        return None

    earned = user.get("badges", [])
    if badge_key in earned:
        return None

    earned.append(badge_key)
    user["badges"] = earned
    return BADGES[badge_key]


# ─── Progress Bars ────────────────────────────────────────────────────────────

def session_progress_bar(prozent: int) -> str:
    """Tagesbezogener Fortschritt – wird während Session aktualisiert."""
    filled = round(prozent / 10)
    bar    = "█" * filled + "░" * (10 - filled)
    return f"📅 Session-Fortschritt\n[{bar}] {prozent} %"


def overall_progress_bar(abgeschlossen: int, gesamt: int = 5) -> str:
    """Gesamtfortschritt über alle Sessions – erscheint am Session-Ende."""
    filled = round((abgeschlossen / gesamt) * 10)
    bar    = "█" * filled + "░" * (10 - filled)
    pct    = round((abgeschlossen / gesamt) * 100)
    return f"📊 Gesamtfortschritt\n[{bar}] {abgeschlossen}/{gesamt} ({pct} %)"


# ─── Quests ───────────────────────────────────────────────────────────────────

def get_quest_intro(modul_nr: int) -> str | None:
    q = QUESTS.get(modul_nr)
    if not q or q["titel"] == "texttexttext":
        return None
    return f"🗺️ {q['titel']}\n\n{q['beschreibung']}"


def get_quest_completion(modul_nr: int) -> str | None:
    q = QUESTS.get(modul_nr)
    if not q or q["abschluss"] == "texttexttext":
        return None
    return q["abschluss"]


# ─── Session-Start Summary ────────────────────────────────────────────────────

def get_start_summary(user: dict) -> str:
    streak = user.get("streak", 1)
    abg    = user.get("abgeschlossene_module", 0)
    badges = user.get("badges", [])
    bar    = overall_progress_bar(abg)

    lines  = [f"🔥 Streak: {streak} Tag(e)", bar]
    if badges:
        lines.append(f"🏅 Abzeichen: {len(badges)}")
    return "\n".join(lines)


# ─── Cliffhanger ──────────────────────────────────────────────────────────────

def get_cliffhanger(modul_nr: int) -> str | None:
    c = CLIFFHANGER.get(modul_nr)
    return c if c and c != "texttexttext" else None
