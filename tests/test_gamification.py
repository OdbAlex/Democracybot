"""Tests für gamification.py – ausführen im Repo-Root mit: python -m pytest -q tests"""
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gamification import (GamificationEngine, Store, quality_badges_for, word_count,  # noqa: E402
                          is_command, PLAIN_ACK)

TZ = ZoneInfo("Europe/Berlin")
WEEKDAY_NOON = datetime(2026, 11, 3, 12, 0, tzinfo=TZ)  # Dienstag


@pytest.fixture
def eng(tmp_path):
    events = []
    e = GamificationEngine(Store(str(tmp_path / "g.sqlite")), log=events.append)
    e.events = events
    return e


def test_arm_none_does_nothing(eng):
    assert eng.day_intro("p", None, 1) == []
    assert eng.on_user_message("p", None, "Ich fühle mich gut", WEEKDAY_NOON, 1) == []
    assert eng.status_text("p", None) == []
    assert eng.rueckschau("p", None) == []
    assert eng.events == []


def test_plain_only_neutral(eng):
    assert eng.day_intro("p", "plain", 3) == ["Tag 3 von 10."]
    out = eng.on_user_message("p", "plain", "Ich fühle mich wütend, z.B. gestern", WEEKDAY_NOON, 1)
    assert out == []  # keine Badges in der Kontrolle
    for d in (2, 3):
        out = eng.on_user_message("p", "plain", "Antwort", WEEKDAY_NOON, d)
    assert out == [PLAIN_ACK]  # Meilenstein Tag 3 -> neutrale Bestätigung
    assert eng.rueckschau("p", "plain") == []


def test_milestones_and_quality_once(eng):
    out1 = eng.on_user_message("g", "gamified", "Ich bin traurig.", WEEKDAY_NOON, 1)
    assert any("Gefühls-Benenner" in m for m in out1)
    out2 = eng.on_user_message("g", "gamified", "Wieder traurig.", WEEKDAY_NOON, 2)
    assert not any("Gefühls-Benenner" in m for m in out2)  # nur einmal
    out3 = eng.on_user_message("g", "gamified", "ok", WEEKDAY_NOON, 3)
    assert any("Etappen-Läufer" in m for m in out3)


def test_joker_bridges_one_gap_then_comeback(eng):
    eng.on_user_message("g", "gamified", "a", WEEKDAY_NOON, 1)
    out = eng.on_user_message("g", "gamified", "b", WEEKDAY_NOON, 3)  # Tag 2 verpasst
    assert any("Joker" in m for m in out)
    out = eng.on_user_message("g", "gamified", "c", WEEKDAY_NOON, 6)  # 2 Tage verpasst
    assert any("Comeback" in m for m in out)
    st = eng.store.get("g")
    assert st.streak == 1 and st.joker_used and st.active_days == [1, 3, 6]


def test_commands_not_counted(eng):
    for cmd in ("Status", "hilf mir!", "bereit", "progress", "/help", "Hilfe"):
        assert is_command(cmd), cmd
        assert eng.on_user_message("g", "gamified", cmd, WEEKDAY_NOON, 1) == []
    assert eng.store.get("g") is None


def test_time_badges(eng):
    late = datetime(2026, 11, 7, 23, 30, tzinfo=TZ)  # Samstag spät
    out = eng.on_user_message("g", "gamified", "x", late, 1)
    assert any("Nachteule" in m for m in out) and any("Wochenend" in m for m in out)


def test_rueckschau_once_with_snippets(eng):
    for d, t in [(1, "Erster Gedanke. Mehr."), (5, "Mitte."), (10, "Letzter Gedanke!")]:
        eng.on_user_message("g", "gamified", t, WEEKDAY_NOON, d)
    msgs = eng.rueckschau("g", "gamified")
    joined = "\n".join(msgs)
    assert "3 von 10" in joined and "Erster Gedanke." in joined and "Mehr." not in joined
    assert eng.rueckschau("g", "gamified") == []


def test_logging_same_in_both_arms(eng):
    eng.on_user_message("a", "plain", "drei kleine Wörter", WEEKDAY_NOON, 1)
    eng.on_user_message("b", "gamified", "drei kleine Wörter", WEEKDAY_NOON, 1)
    msgs = [e for e in eng.events if e["event"] == "user_message"]
    assert [m["words"] for m in msgs] == [3, 3]
    assert {m["gamification_arm"] for m in msgs} == {"plain", "gamified"}


def test_word_count_rules():
    assert word_count("Hallo du 😀 https://x.de") == 2


def test_quality_rules():
    assert "beidseitig" in quality_badges_for("Ich verstehe die anderen, aber ich sehe es anders")
    assert "konkret" in quality_badges_for("Zum Beispiel in meiner Klasse")
    assert quality_badges_for("ok") == []


def test_invalid_arm(eng):
    with pytest.raises(ValueError):
        eng.day_intro("p", "gamify", 1)
