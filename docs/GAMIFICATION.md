# Gamification-Studie (Masterarbeit Alex Odebrecht)

## Einschalten
In der `.env`: `GAMIFICATION_STUDY=true`. Ohne das Flag ändert sich an Ella nichts.

Optional für Cluster-Randomisierung: `data/klassen_arme.json`
```json
{"7A": "gamified", "7B": "plain"}
```
Liegt die Datei vor, fragt das Onboarding nach dem Klassen-Code (vor dem ID-Code) und vergibt den Arm pro Klasse.
Sonst wird individuell 50/50 randomisiert.

## Was sich mit dem Flag ändert
| | Ella normal | GAMIFICATION_STUDY=true |
|---|---|---|
| Ellas Kontrollbedingung (control) | 50/50 | aus, alle bekommen Ella-Inhalte |
| Punkte-/Level-Nachrichten | ja | aus (beide Arme) |
| Morgengruß | „Tag X/10 … Schreibe bereit“ | neutraler Gruß, Tagesangabe aus dem Modul |
| `progress` / `status` | Punkte, Level | Studientag + Status aus dem Modul |
| Hilfetext, Onboarding, stop | erwähnen Punkte | ohne Punkte |

## Andockpunkte (demokratiebot_main.py)
1. `day_intro` im Morgen-Job (und bei `trigger_intervention`)
2. `after_message` nur, wenn eine laufende Übung die Nachricht verarbeitet hat.
   Befehle, Onboarding, Re-Evaluation und Krisennachrichten zählen damit nie als Antwort.
3. `status` bei `progress`/`status`
4. `rueckschau` nach Abschluss der Übung an Tag 10; Fallback beim Studienende-Check um 00:01

## Daten (data/)
- `gamification_arms.jsonl`: pid, id_code, klasse, arm (Verknüpfung mit Fragebögen über id_code)
- `gamification_events.jsonl`: Events für H1/H2 (`user_message` mit Wortzahl, `active_day`, `badge`, `rueckschau`)
- `gamification.sqlite`: Zustand pro Person
- pid = gesalzener Hash der Matrix-ID; Matrix-IDs stehen nicht in den Gamification-Logs.

## Tests
`python -m pytest -q tests`
