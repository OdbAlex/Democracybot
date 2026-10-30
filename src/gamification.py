"""
gamification.py – Gamification-Schicht für den Ella-Bot (DemocracyBot, Masterarbeit Alex Odebrecht)

Grundsatz: Dieses Modul ändert KEINE Inhalte des Ella-Bots. Es hängt nur zusätzliche,
vorlagenbasierte Nachrichten an (Badges, Streak, Etappenreise, Rückschau) und protokolliert,
was es tut. Es ruft kein LLM auf und ist damit unabhängig vom Modell (Azure, Mistral, ...).

Steuerung über das Feld `gamification_arm` pro Teilnehmer*in:
    "gamified" -> volle Gamification
    "plain"    -> aktive Kontrolle: nur neutrale Tagesangabe ("Tag 3 von 10.")
    None       -> Modul ist aus; Ella läuft exakt wie bisher (Milènes Studie)

Das Feld ist unabhängig von Milènes `condition`-Feld.

Andockpunkte in Ella (eingebaut in demokratiebot_main.py, siehe GamificationBridge):
    1. engine.day_intro(pid, arm, study_day)            -> vor dem Tagesimpuls senden
    2. engine.on_user_message(pid, arm, text, ts, day)  -> nach Ellas Antwort senden
    3. engine.status_text(pid, arm)                     -> beim Befehl "progress"/"status"
    4. engine.rueckschau(pid, arm)                      -> an Tag 10 nach der letzten Übung

Alle Rückgaben sind Listen von Strings (0..n Nachrichten). Leere Liste = nichts senden.
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable, Optional
from zoneinfo import ZoneInfo

ARM_GAMIFIED = "gamified"
ARM_PLAIN = "plain"
VALID_ARMS = (ARM_GAMIFIED, ARM_PLAIN, None)

STUDY_DAYS = 10
MILESTONES = (3, 6, 10)
TZ = ZoneInfo("Europe/Berlin")

# Bot-Befehle zählen nicht als Antwort (nicht aktiv, keine Wortzahl, keine Badges).
# Enthält Ellas tatsächliche Befehle (start/help/progress/...) plus die deutschen Aliasse.
COMMANDS = {
    # Ella
    "start", "help", "stop", "info", "progress", "bereit", "ready", "be", "reset",
    "advance_day", "trigger_intervention", "trigger_reevaluation", "debug", "mygroup",
    # deutsche Aliasse
    "hallo", "hilfe", "status", "hilf mir",
}

# ---------------------------------------------------------------------------
# Texte (Du-Form, kurz, ohne Inhalt zur Intervention). Alles hier anpassbar.
# ---------------------------------------------------------------------------

PLAIN_ACK = "Danke, deine Antwort ist angekommen."

ETAPPEN = [
    "Aufbruch",
    "Erste Weggabelung",
    "Aussichtspunkt",
    "Über den Fluss",
    "Halbzeit-Rast",
    "Durch den Wald",
    "Bergpass",
    "Gipfelblick",
    "Der Weg zurück",
    "Ziel",
]

BADGES = {
    # Meilensteine (aktive Tage kumuliert)
    "meilenstein_3": ("🥾", "Etappen-Läufer*in", "Du warst an 3 Tagen dabei."),
    "meilenstein_6": ("🧭", "Weg-Finder*in", "Du warst an 6 Tagen dabei."),
    "meilenstein_10": ("🏁", "Ziel erreicht", "Du warst an allen 10 Tagen dabei."),
    # Qualität (regelbasiert, je einmal)
    "beidseitig": ("⚖️", "Beidseitig-Denker*in", "Du hast mehr als eine Seite betrachtet."),
    "konkret": ("🔧", "Konkret-Macher*in", "Du hast ein konkretes Beispiel oder einen Plan genannt."),
    "gefuehl": ("💬", "Gefühls-Benenner*in", "Du hast ein Gefühl beim Namen genannt."),
    # Comeback
    "comeback": ("🔄", "Comeback", "Schön, dass du wieder da bist."),
    # Zeit-Gimmicks (nur sinnvoll bei eigenen Geräten)
    "nachteule": ("🦉", "Nachteule", "Antwort spät am Abend."),
    "fruehaufsteher": ("🌅", "Frühaufsteher*in", "Antwort früh am Morgen."),
    "wochenende": ("🛹", "Wochenend-Krieger*in", "Antwort am Wochenende."),
}

# ---------------------------------------------------------------------------
# Regeln für Qualitäts-Badges. ARBEITSFASSUNG – von Alex zu prüfen.
# Bewusst KEINE Längenkriterien (Tiefgänger wurde wegen H2-Konfundierung gestrichen).
# ---------------------------------------------------------------------------

_BEIDSEITIG = [
    r"\beinerseits\b.*\banderer(seits)?\b",
    r"\bauf der anderen seite\b",
    r"\bandere(n)? (sehen|denken|finden|meinen)\b",
    r"\b(verstehe|kann verstehen)\b.*\b(aber|trotzdem|auch wenn)\b",
    r"\b(aber|jedoch|trotzdem)\b.*\b(verstehe|nachvollziehen|recht)\b",
    r"\bbeide seiten\b",
    r"\bsowohl\b.*\bals auch\b",
    r"\baus (der|deren|ihrer|seiner) sicht\b",
]

_KONKRET = [
    r"\bzum beispiel\b",
    r"\bz\.\s?b\.",
    r"\bbeispielsweise\b",
    r"\b(neulich|gestern|letzte woche|letztens|heute)\b",
    r"\b(in meiner klasse|bei uns|in der schule|meine[rm]? (freund|freundin|mutter|vater|schwester|bruder))\b",
    r"\bich (werde|würde|will|könnte)\b.*\b(nächstes mal|morgen|demnächst|ab jetzt|versuchen)\b",
    r"\bnächstes mal\b",
]

_GEFUEHL = [
    r"\b(ich )?fühl(e|te)?\b",
    r"\bgefühl\b",
    r"\b(wütend|sauer|genervt|ärger(lich)?|frustriert)\b",
    r"\b(traurig|enttäuscht|verletzt|einsam)\b",
    r"\b(angst|ängstlich|nervös|unsicher|besorgt)\b",
    r"\b(froh|glücklich|erleichtert|stolz|freue mich|gefreut)\b",
    r"\b(schäme|peinlich|schuldig)\b",
]


def _match_any(patterns: list[str], text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def quality_badges_for(text: str) -> list[str]:
    """Welche Qualitäts-Badges erfüllt diese Antwort? (regelbasiert, ohne LLM)"""
    found = []
    if _match_any(_BEIDSEITIG, text):
        found.append("beidseitig")
    if _match_any(_KONKRET, text):
        found.append("konkret")
    if _match_any(_GEFUEHL, text):
        found.append("gefuehl")
    return found


def time_badges_for(ts: datetime) -> list[str]:
    local = ts.astimezone(TZ)
    found = []
    if local.hour >= 22 or local.hour < 5:
        found.append("nachteule")
    elif 5 <= local.hour < 8:
        found.append("fruehaufsteher")
    if local.weekday() >= 5:
        found.append("wochenende")
    return found


def is_command(text: str) -> bool:
    t = text.strip().lower().lstrip("/").rstrip("!.?")
    return t in COMMANDS


def word_count(text: str) -> int:
    """Wortzahl wie für H2: Wörter mit mind. einem Buchstaben oder einer Ziffer.
    Reine Emojis und Links zählen nicht. [OFFEN in Präregistrierung, hier so umgesetzt]"""
    tokens = re.findall(r"\S+", text)
    return sum(1 for t in tokens if not t.startswith("http") and re.search(r"[\wÄÖÜäöüß]", t))


# ---------------------------------------------------------------------------
# Zustand pro Teilnehmer*in
# ---------------------------------------------------------------------------

@dataclass
class State:
    pid: str
    arm: Optional[str]
    active_days: list[int] = field(default_factory=list)  # Studientage 1..10 mit mind. 1 Antwort
    badges: list[str] = field(default_factory=list)
    joker_used: bool = False
    joker_day: Optional[int] = None  # welcher Tag wurde überbrückt
    streak: int = 0
    streak_broken: bool = False      # Streak war gerissen -> nächster aktiver Tag = Comeback
    snippets: dict = field(default_factory=dict)  # Tag -> erster Satz der ersten Antwort (für Rückschau)
    rueckschau_sent: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "State":
        d = json.loads(s)
        d["snippets"] = {int(k): v for k, v in d.get("snippets", {}).items()}
        return State(**d)


class Store:
    """Minimaler SQLite-Speicher. Kann durch Ellas eigene DB ersetzt werden,
    solange get()/put() gleich bleiben."""

    def __init__(self, path: str = "gamification.sqlite"):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS state (pid TEXT PRIMARY KEY, data TEXT NOT NULL)")
        self._db.commit()

    def get(self, pid: str) -> Optional[State]:
        with self._lock:
            row = self._db.execute("SELECT data FROM state WHERE pid = ?", (pid,)).fetchone()
        return State.from_json(row[0]) if row else None

    def put(self, st: State) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO state (pid, data) VALUES (?, ?) ON CONFLICT(pid) DO UPDATE SET data = excluded.data",
                (st.pid, st.to_json()),
            )
            self._db.commit()


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _badge_msg(key: str) -> str:
    icon, name, why = BADGES[key]
    return f"{icon} Neues Abzeichen: {name}. {why}"


def _first_sentence(text: str, limit: int = 140) -> str:
    s = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


class GamificationEngine:
    def __init__(self, store: Store, log: Optional[Callable[[dict], None]] = None):
        self.store = store
        self.log = log or (lambda event: None)
        # Sperre pro Engine: Ella ruft aus Polling- und Scheduler-Thread auf
        self._lock = threading.RLock()

    # -- intern ------------------------------------------------------------
    def _state(self, pid: str, arm: Optional[str]) -> State:
        if arm not in VALID_ARMS:
            raise ValueError(f"Unbekannter gamification_arm: {arm!r}")
        st = self.store.get(pid)
        if st is None:
            st = State(pid=pid, arm=arm)
        elif st.arm != arm:
            # Arm darf sich während der Studie nicht ändern -> laut protokollieren, alten behalten
            self._emit(pid, st.arm, "arm_mismatch", requested=arm)
        return st

    def _emit(self, pid: str, arm: Optional[str], event: str, **data) -> None:
        self.log({
            "ts": datetime.now(TZ).isoformat(),
            "pid": pid,
            "gamification_arm": arm,
            "event": event,
            **data,
        })

    def _award(self, st: State, key: str, out: list[str], day: int) -> None:
        if key not in st.badges:
            st.badges.append(key)
            out.append(_badge_msg(key))
            self._emit(st.pid, st.arm, "badge", badge=key, study_day=day)

    def _update_streak(self, st: State, day: int) -> tuple[bool, bool]:
        """Aktualisiert Streak für neuen aktiven Tag. Gibt (joker_eingesetzt, comeback) zurück.
        Kein harter Reset im Text: Ein Abriss wird nie gemeldet, nur das Comeback."""
        prev = max(st.active_days) if st.active_days else None
        joker_now = comeback = False
        if prev is None:
            st.streak = 1
        else:
            gap = day - prev - 1  # verpasste Tage dazwischen
            if gap <= 0:
                st.streak += 1
            elif gap == 1 and not st.joker_used:
                st.joker_used, st.joker_day = True, prev + 1
                st.streak += 1
                joker_now = True
            else:
                st.streak = 1
                comeback = True
        return joker_now, comeback

    # -- Andockpunkt 1: vor dem Tagesimpuls --------------------------------
    def day_intro(self, pid: str, arm: Optional[str], study_day: int) -> list[str]:
        if arm is None:
            return []
        with self._lock:
            st = self._state(pid, arm)
            self.store.put(st)
        self._emit(pid, st.arm, "day_intro", study_day=study_day)
        if st.arm == ARM_PLAIN:
            return [f"Tag {study_day} von {STUDY_DAYS}."]
        etappe = ETAPPEN[min(max(study_day, 1), STUDY_DAYS) - 1]
        msgs = [f"🗺️ Etappe {study_day} von {STUDY_DAYS}: {etappe}"]
        if study_day == 1:
            msgs.append("An Tag 10 bekommst du eine Rückschau auf deine Reise, mit deinen eigenen Gedanken.")
        if st.streak >= 2 and st.active_days and max(st.active_days) == study_day - 1:
            msgs.append(f"🔥 Du bist {st.streak} Tage in Folge dabei.")
        return msgs

    # -- Andockpunkt 2: nach Ellas Antwort auf eine Nachricht ---------------
    def on_user_message(self, pid: str, arm: Optional[str], text: str,
                        ts: datetime, study_day: int) -> list[str]:
        if arm is None or not text or is_command(text):
            return []
        if not 1 <= study_day <= STUDY_DAYS:
            return []
        with self._lock:
            st = self._state(pid, arm)
            out: list[str] = []
            new_day = study_day not in st.active_days

            # Logging für H1/H2 in BEIDEN Armen gleich
            self._emit(pid, st.arm, "user_message", study_day=study_day,
                       words=word_count(text), new_active_day=new_day)

            if new_day:
                joker_now, comeback = self._update_streak(st, study_day)
                st.active_days.append(study_day)
                st.active_days.sort()
                st.snippets.setdefault(study_day, _first_sentence(text))
                self._emit(pid, st.arm, "active_day", study_day=study_day,
                           n_active=len(st.active_days), streak=st.streak,
                           joker_used_now=joker_now, comeback=comeback)

                if st.arm == ARM_GAMIFIED:
                    if joker_now:
                        out.append("🃏 Dein Joker hat einen verpassten Tag überbrückt. Deine Serie läuft weiter.")
                    if comeback:
                        self._award(st, "comeback", out, study_day)
                    n = len(st.active_days)
                    if n in MILESTONES:
                        self._award(st, f"meilenstein_{n}", out, study_day)
                    for key in time_badges_for(ts):
                        self._award(st, key, out, study_day)
                elif st.arm == ARM_PLAIN and len(st.active_days) in MILESTONES:
                    # Kontrolle: neutrale Bestätigung statt Abzeichen (laut Design-Tabelle)
                    out.append(PLAIN_ACK)

            if st.arm == ARM_GAMIFIED:
                for key in quality_badges_for(text):
                    self._award(st, key, out, study_day)

            self.store.put(st)
        return out

    # -- Andockpunkt 3: Befehl "progress"/"status" ---------------------------
    def status_text(self, pid: str, arm: Optional[str]) -> list[str]:
        if arm is None:
            return []
        st = self._state(pid, arm)
        n = len(st.active_days)
        if st.arm == ARM_PLAIN:
            return [f"Du hast bisher an {n} von {STUDY_DAYS} Tagen geantwortet."]
        icons = " ".join(BADGES[b][0] for b in st.badges) or "noch keine"
        joker = "schon eingesetzt" if st.joker_used else "noch verfügbar"
        return [f"🗺️ {n} von {STUDY_DAYS} Etappen geschafft · 🔥 Serie: {st.streak} · "
                f"🃏 Joker: {joker} · Abzeichen: {icons}"]

    # -- Andockpunkt 4: Rückschau an Tag 10 ----------------------------------
    def rueckschau(self, pid: str, arm: Optional[str]) -> list[str]:
        if arm != ARM_GAMIFIED:
            return []
        with self._lock:
            st = self._state(pid, arm)
            if st.rueckschau_sent:
                return []
            n = len(st.active_days)
            msgs = [f"🏁 Deine Rückschau: Du warst an {n} von {STUDY_DAYS} Tagen unterwegs."]
            if st.badges:
                msgs.append("Deine Abzeichen: " + ", ".join(f"{BADGES[b][0]} {BADGES[b][1]}" for b in st.badges))
            days = sorted(st.snippets)
            picks = sorted({days[0], days[len(days) // 2], days[-1]}) if days else []
            if picks:
                lines = [f"Tag {d}: „{st.snippets[d]}“" for d in picks]
                msgs.append("Ein paar deiner eigenen Gedanken:\n" + "\n".join(lines))
            msgs.append("Danke, dass du mitgemacht hast!")
            st.rueckschau_sent = True
            self.store.put(st)
        self._emit(pid, st.arm, "rueckschau", n_active=n, badges=list(st.badges))
        return msgs
