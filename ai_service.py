# =============================================================================
# ai_service.py  (~160 Zeilen)
# -----------------------------------------------------------------------------
# Alle Kommunikation mit OpenAI. Andere Module importieren nur diese Datei.
# =============================================================================

import os, json
from openai import OpenAI
from study_content import SYSTEM_PROMPT

client      = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL       = "gpt-4o-mini"
TEMPERATURE = 0.7
MAX_TOKENS  = 300


# ─── Hauptantwort ─────────────────────────────────────────────────────────────

def get_response(history: list[dict], module_prompt: str = None) -> str:
    """Generiert Bot-Antwort auf Basis der Gesprächshistorie."""
    system = SYSTEM_PROMPT
    if module_prompt:
        system += f"\n\nFokus dieser Session:\n{module_prompt}"

    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}] + history,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"[AI] get_response error: {e}")
        return "Ich kann gerade leider nicht antworten. Bitte kurz warten."


# ─── TTM-Klassifikation ────────────────────────────────────────────────────────

def classify_ttm(antworten: list[str]) -> str:
    """
    Klassifiziert 3 Einstiegsantworten in eine TTM-Stufe.
    Rückgabe: 'precontemplation' | 'contemplation' | 'preparation'
              | 'action' | 'maintenance'
    """
    valid = ["precontemplation", "contemplation", "preparation",
             "action", "maintenance"]

    prompt = f"""
Du klassifizierst Antworten für eine psychologische Studie nach dem
Transtheoretischen Modell (TTM), angewendet auf demokratische Teilhabe.

Stufen:
- precontemplation: kein Veränderungswunsch, politische Teilhabe irrelevant
- contemplation: Nachdenken, Ambivalenz, aber keine Handlung
- preparation: Veränderungsabsicht vorhanden, erste kleine Schritte
- action: aktiv, aber unsicher oder neu dabei
- maintenance: etabliert aktiv, reflektiert und stabil

Antworten des Nutzers:
1. {antworten[0] if len(antworten) > 0 else '–'}
2. {antworten[1] if len(antworten) > 1 else '–'}
3. {antworten[2] if len(antworten) > 2 else '–'}

Antworte NUR mit einem der fünf englischen Begriffe. Keine Erklärung.
"""
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        result = r.choices[0].message.content.strip().lower()
        return result if result in valid else "contemplation"
    except Exception as e:
        print(f"[AI] classify_ttm error: {e}")
        return "contemplation"


# ─── Mid-Session Badge Trigger ─────────────────────────────────────────────────

def detect_badge_trigger(user_text: str, bot_last: str, modul_nr: int) -> str | None:
    """
    Analysiert eine Nutzerantwort und entscheidet ob ein Badge-Trigger ausgelöst wird.
    Gibt Trigger-String zurück oder None.

    Trigger-Optionen (aus study_content.BADGE_TRIGGERS):
      'tiefes_gespraech'       – Nutzer offenbart etwas Persönliches/Verletzliches
      'perspektivwechsel'      – Nutzer zeigt echtes Verständnis einer Gegenposition
      'widerspruch_gehalten'   – Nutzer hält Meinungsverschiedenheit aus ohne zuzustimmen
    """
    prompt = f"""
Du analysierst eine Antwort in einer psychologischen Studie über Scham
und demokratische Teilhabe (Modul {modul_nr}/5: Perspektivwechsel).

Letzte Bot-Frage: "{bot_last}"
Nutzerantwort: "{user_text}"

Prüfe ob EINER dieser Trigger zutrifft:
- tiefes_gespraech: Nutzer teilt etwas Persönliches oder Verletzliches mit
- perspektivwechsel: Nutzer zeigt echtes Verständnis einer fremden Perspektive
  (nicht nur oberflächliche Zustimmung)
- widerspruch_gehalten: Nutzer hält eine Meinungsverschiedenheit aus,
  ohne einfach zuzustimmen

Wenn ein Trigger zutrifft: antworte NUR mit dem Trigger-Namen.
Wenn keiner zutrifft: antworte NUR mit "none".
Keine Erklärung.
"""
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        result = r.choices[0].message.content.strip().lower()
        valid_triggers = ["tiefes_gespraech", "perspektivwechsel", "widerspruch_gehalten"]
        return result if result in valid_triggers else None
    except Exception as e:
        print(f"[AI] detect_badge_trigger error: {e}")
        return None


# ─── Zusammenfassung für Forschungsdaten ──────────────────────────────────────

def summarize_session(history: list[dict]) -> str:
    """Unsichtbare Session-Zusammenfassung für Auswertung."""
    if not history:
        return "Keine History."
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": (
                    "Fasse das Gespräch in 2–3 Sätzen zusammen. "
                    "Fokus: Welche Emotionen wurden genannt? "
                    "Gab es einen Perspektivwechsel? "
                    "Wie offen war die Person? Neutral und sachlich."
                )},
                *history,
            ],
            temperature=0.2,
            max_tokens=150,
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"[AI] summarize error: {e}")
        return "Nicht verfügbar."
