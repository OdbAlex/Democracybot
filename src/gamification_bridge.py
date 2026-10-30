"""
gamification_bridge.py – verbindet gamification.py mit dem Ella-Bot.

Aktiv nur mit GAMIFICATION_STUDY=true in der .env. Ohne das Flag tut die Brücke nichts
und Ella läuft exakt wie bisher (Milènes Studie).

Mit dem Flag:
  * Ellas eigene Kontrollbedingung ist aus: alle bekommen dieselben Ella-Inhalte (condition="intervention").
  * Jede*r bekommt einen gamification_arm ("gamified" | "plain").
      - Liegt data/klassen_arme.json vor (z.B. {"7A": "gamified", "7B": "plain"}), fragt das
        Onboarding nach dem Klassen-Code und vergibt den Arm pro Klasse (Cluster-Randomisierung).
      - Sonst: individuelle 50/50-Randomisierung.
  * Ellas Punkte-/Level-Nachrichten sind in BEIDEN Armen aus (Design: keine Punkte).
  * Dateien in data/:
      gamification_arms.jsonl    pid, id_code, klasse, arm  (Zuordnung zu Fragebögen über id_code)
      gamification_events.jsonl  alle Events für H1/H2 (user_message mit Wortzahl, active_day, badge, ...)
      gamification.sqlite        Zustand pro Person (Streak, Badges, Snippets)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import secrets
import threading
from datetime import datetime
from typing import Iterable, Optional

from gamification import GamificationEngine, Store, ARM_GAMIFIED, ARM_PLAIN, TZ

logger = logging.getLogger(__name__)


def gamification_study_enabled() -> bool:
    return os.getenv("GAMIFICATION_STUDY", "false").lower() == "true"


class GamificationBridge:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.enabled = gamification_study_enabled()
        self._lock = threading.Lock()
        self._arms: dict[str, dict] = {}  # pid -> Eintrag
        self.class_arms: dict[str, str] = {}
        self.engine: Optional[GamificationEngine] = None
        if not self.enabled:
            return

        os.makedirs(data_dir, exist_ok=True)
        self._salt = self._load_salt()
        self._arms_file = os.path.join(data_dir, "gamification_arms.jsonl")
        self._events_file = os.path.join(data_dir, "gamification_events.jsonl")
        self._load_arms()
        self._load_class_arms()
        self.engine = GamificationEngine(
            Store(os.path.join(data_dir, "gamification.sqlite")), log=self._log_event
        )
        logger.info(
            f"GAMIFICATION_STUDY aktiv – Randomisierung: "
            f"{'pro Klasse (' + str(len(self.class_arms)) + ' Klassen)' if self.class_mode else 'individuell 50/50'}"
        )

    # ------------------------------------------------------------------ Setup
    def _load_salt(self) -> str:
        path = os.path.join(self.data_dir, ".gamification_salt")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read().strip()
        salt = secrets.token_hex(16)
        with open(path, "w", encoding="utf-8") as f:
            f.write(salt)
        return salt

    def _load_arms(self) -> None:
        if not os.path.exists(self._arms_file):
            return
        with open(self._arms_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    self._arms[entry["pid"]] = entry

    def _load_class_arms(self) -> None:
        path = os.path.join(self.data_dir, "klassen_arme.json")
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for klasse, arm in raw.items():
            if arm not in (ARM_GAMIFIED, ARM_PLAIN):
                raise ValueError(f"klassen_arme.json: ungültiger Arm {arm!r} für Klasse {klasse!r}")
            self.class_arms[self._norm_class(klasse)] = arm

    @staticmethod
    def _norm_class(code: str) -> str:
        return code.strip().upper().replace(" ", "")

    def _log_event(self, event: dict) -> None:
        with self._lock:
            with open(self._events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # --------------------------------------------------------- Zuordnung/Arm
    @property
    def class_mode(self) -> bool:
        return self.enabled and bool(self.class_arms)

    def valid_class(self, code: str) -> bool:
        return self._norm_class(code) in self.class_arms

    def pid(self, matrix_id: str) -> str:
        """Pseudonyme ID (gesalzener Hash der Matrix-ID). Matrix-IDs landen nie in den Gamification-Logs."""
        return hashlib.sha256((self._salt + matrix_id).encode()).hexdigest()[:16]

    def assign(self, matrix_id: str, id_code: str, klasse: Optional[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        pid = self.pid(matrix_id)
        if pid in self._arms:  # Neu-Anmeldung (z.B. nach stop/start): Arm bleibt
            return self._arms[pid]["arm"]
        if self.class_mode:
            klasse = self._norm_class(klasse or "")
            arm = self.class_arms[klasse]
        else:
            arm = random.choice([ARM_GAMIFIED, ARM_PLAIN])
        entry = {
            "ts": datetime.now(TZ).isoformat(),
            "pid": pid,
            "id_code": id_code,
            "klasse": klasse,
            "arm": arm,
            "randomisierung": "klasse" if self.class_mode else "individuell",
        }
        with self._lock:
            self._arms[pid] = entry
            with open(self._arms_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(f"Gamification-Arm zugewiesen: pid={pid} arm={arm}")
        return arm

    def arm_for(self, matrix_id: str) -> Optional[str]:
        if not self.enabled:
            return None
        entry = self._arms.get(self.pid(matrix_id))
        return entry["arm"] if entry else None

    # ------------------------------------------------------------ Andocken
    @staticmethod
    def _send(bot, matrix_id: str, msgs: Iterable[str]) -> None:
        for m in msgs:
            bot.send_message(matrix_id, m)

    def _safe(self, fn, *args):
        """Ein Fehler im Gamification-Modul darf Ella nie lahmlegen."""
        try:
            return fn(*args) or []
        except Exception as e:  # pragma: no cover - Schutznetz
            logger.error(f"Gamification-Fehler in {fn.__name__}: {e}", exc_info=True)
            return []

    def day_intro(self, bot, matrix_id: str, study_day: int) -> None:
        arm = self.arm_for(matrix_id)
        if arm is None:
            return
        self._send(bot, matrix_id, self._safe(self.engine.day_intro, self.pid(matrix_id), arm, study_day))

    def after_message(self, bot, matrix_id: str, text: str, ts_ms: int, study_day: int) -> None:
        arm = self.arm_for(matrix_id)
        if arm is None:
            return
        ts = datetime.fromtimestamp(ts_ms / 1000, TZ) if ts_ms else datetime.now(TZ)
        self._send(bot, matrix_id,
                   self._safe(self.engine.on_user_message, self.pid(matrix_id), arm, text, ts, study_day))

    def status(self, matrix_id: str) -> list[str]:
        arm = self.arm_for(matrix_id)
        if arm is None:
            return []
        return self._safe(self.engine.status_text, self.pid(matrix_id), arm)

    def rueckschau(self, bot, matrix_id: str) -> None:
        arm = self.arm_for(matrix_id)
        if arm is None:
            return
        self._send(bot, matrix_id, self._safe(self.engine.rueckschau, self.pid(matrix_id), arm))
