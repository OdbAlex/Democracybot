# =============================================================================
# study_content.py  (~350 Zeilen)
# -----------------------------------------------------------------------------
# Alle Studieninhalte. Modul 4 (Perspektivwechsel) ist vollständig ausgearbeitet.
# Module 1–3 und 5 sind Placeholder bis Inhalte feststehen.
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Du bist ein einfühlsamer Gesprächsbegleiter in einer psychologischen Studie
über demokratische Teilhabe und Scham.

Deine Grundhaltung:
- Stelle pro Nachricht genau EINE Frage
- Validiere zuerst, bevor du nachfragst
- Bleibe neugierig, nie bewertend
- Verbinde persönliche Erfahrungen mit gesellschaftlichen Mustern
- Antworte auf Deutsch, in 2–4 kurzen Sätzen

Kontext: Viele Menschen ziehen sich aus demokratischen Prozessen zurück,
weil Scham und Angst vor Ablehnung ihre Stimme zum Schweigen bringen.
Du hilfst, diesen Kreislauf zu unterbrechen – durch Gespräch, nicht durch Ratschlag.
"""

# ─────────────────────────────────────────────────────────────────────────────
# TTM-EINSTIEGSFRAGEN
# ─────────────────────────────────────────────────────────────────────────────

TTM_FRAGEN = [
    (
        "Wenn du an politische Teilhabe denkst – Wählen, Diskutieren, "
        "Engagement – wie würdest du deine aktuelle Haltung beschreiben?\n\n"
        "A) Das ist wirklich nichts für mich\n"
        "B) Ich denke manchmal darüber nach, aber tue nichts\n"
        "C) Ich möchte aktiver werden, weiß aber nicht wie\n"
        "D) Ich tue bereits etwas, aber fühle mich unsicher\n"
        "E) Ich bin aktiv und möchte das besser verstehen"
    ),
    (
        "Gab es in den letzten Wochen eine Situation, in der du eine "
        "politische Meinung hattest – sie aber nicht ausgesprochen hast?"
    ),
    (
        "Was hält dich davon ab, dich mehr einzubringen – "
        "wenn du jetzt ganz ehrlich bist?"
    ),
]

TTM_RESULT_TEXTS = {
    "precontemplation": (
        "Du befindest dich in einer Phase, in der politische Teilhabe "
        "sich noch weit weg anfühlt – das ist völlig in Ordnung. "
        "In unseren Gesprächen werden wir nicht versuchen, dich zu überzeugen, "
        "sondern einfach gemeinsam schauen, was dahintersteckt."
    ),
    "contemplation": (
        "Du nimmst wahr, dass etwas nicht ganz stimmt – ein leises Unbehagen "
        "zwischen dem, was du denkst, und dem, was du tust. "
        "Genau dieser Zwischenraum ist unser Ausgangspunkt."
    ),
    "preparation": (
        "Du möchtest etwas verändern und hast eine klare Intention – "
        "aber die Hemmschwelle ist noch hoch. "
        "In unseren Sessions werden wir konkret schauen, was diese Schwelle ausmacht."
    ),
    "action": (
        "Du bist bereits aktiv, aber das Gefühl der Unsicherheit begleitet dich. "
        "Das ist normal – Mut und Scham schließen sich nicht aus. "
        "Wir werden diesen Widerspruch genauer anschauen."
    ),
    "maintenance": (
        "Du bist regelmäßig engagiert und möchtest das besser verstehen. "
        "In unseren Gesprächen gehen wir tiefer – was hält dich am Laufen, "
        "und was kostet dich am meisten Kraft?"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# MODULE
# ─────────────────────────────────────────────────────────────────────────────

MODULES = {

    # ── Modul 1–3: Placeholder ───────────────────────────────────────────────

    1: {
        "titel":      "Ankommen & Einstieg",
        "intro":      "texttexttext",
        "ki_prompt":  {s: "texttexttext" for s in
                       ["precontemplation","contemplation","preparation","action","maintenance"]},
        "reflexion":  "texttexttext",
    },
    2: {
        "titel":      "Schweigen & Rückzug",
        "intro":      "texttexttext",
        "ki_prompt":  {s: "texttexttext" for s in
                       ["precontemplation","contemplation","preparation","action","maintenance"]},
        "reflexion":  "texttexttext",
    },
    3: {
        "titel":      "Scham & Zugehörigkeit",
        "intro":      "texttexttext",
        "ki_prompt":  {s: "texttexttext" for s in
                       ["precontemplation","contemplation","preparation","action","maintenance"]},
        "reflexion":  "texttexttext",
    },

    # ── Modul 4: PERSPEKTIVWECHSEL – vollständig ausgearbeitet ───────────────

    4: {
        "titel": "Perspektivwechsel",

        "intro": (
            "Heute üben wir etwas Konkretes. 🔄\n\n"
            "Perspektivwechsel gilt in der Demokratieforschung als eine der "
            "wichtigsten Fähigkeiten für gesellschaftliches Miteinander – "
            "und gleichzeitig als eine der schwierigsten.\n\n"
            "Ich werde dich bitten, ein Thema aus einer Perspektive zu betrachten, "
            "die nicht deine eigene ist. Nicht um deine Meinung zu ändern – "
            "sondern um zu verstehen, wie andere zu ihrer Sichtweise kommen.\n\n"
            "Gibt es gerade ein gesellschaftliches Thema, bei dem du eine "
            "klare Meinung hast?"
        ),

        # TTM-angepasste KI-Prompts für Modul 4
        "ki_prompt": {

            "precontemplation": (
                "Der Nutzer steht politischer Teilhabe distanziert gegenüber. "
                "Wähle ein sehr alltagsnahes, nicht-polarisierendes Thema für den Perspektivwechsel "
                "(z.B. Nachbarschaftskonflikt, Schulregeln, Arbeitszeiten). "
                "Formuliere die Gegenposition extrem konkret und menschlich – "
                "nicht als abstrakte Meinung, sondern als nachvollziehbares Erleben einer Person. "
                "Frage nach einer sehr kleinen Öffnung: 'Gibt es irgendetwas an dieser "
                "Perspektive, das du nachvollziehen kannst?' – nicht mehr."
            ),

            "contemplation": (
                "Der Nutzer ist ambivalent und denkt nach. "
                "Wähle ein moderat kontroverses Thema, das er selbst eingebracht hat oder "
                "das zu seinem bisherigen Gesprächsverlauf passt. "
                "Führe den Perspektivwechsel in zwei Schritten: erst die sachliche Gegenposition, "
                "dann die emotionale Motivation dahinter. "
                "Frage explizit: 'Was würde sich an deiner eigenen Haltung ändern, "
                "wenn du diese Perspektive wirklich ernst nimmst?'"
            ),

            "preparation": (
                "Der Nutzer möchte aktiver werden. "
                "Nutze den Perspektivwechsel als Brücke zur Handlung: "
                "Wähle ein Thema, bei dem Verstehen direkt mit Kommunikationsfähigkeit "
                "zusammenhängt. "
                "Frage nach einem konkreten Gesprächspartner im echten Leben, "
                "der diese Gegenposition vertreten könnte – und was es bräuchte, "
                "um mit genau dieser Person in einen echten Austausch zu kommen."
            ),

            "action": (
                "Der Nutzer ist bereits aktiv, aber unsicher. "
                "Wähle ein Thema, das er bereits erlebt hat – wo er eine Position "
                "vertreten und dabei Widerstand gespürt hat. "
                "Lade ihn ein, die Perspektive des Widerstands zu rekonstruieren: "
                "nicht als Angriff, sondern als Reaktion auf eine eigene Erfahrung. "
                "Frage: 'Was erfährst du über deine eigene Kommunikation, "
                "wenn du dir diese Reaktion genau anschaust?'"
            ),

            "maintenance": (
                "Der Nutzer ist erfahren und engagiert. "
                "Wähle ein strukturell komplexes Thema (z.B. Interessenkonflikte, "
                "systemische Benachteiligung, competing values). "
                "Führe einen echten Drei-Perspektiven-Wechsel durch: eigene Position, "
                "direkte Gegenposition, und eine dritte strukturelle Perspektive "
                "(z.B. Systemzwang statt persönlicher Schuld). "
                "Frage nach der politischen Implikation: 'Verändert diese dritte "
                "Perspektive, wie du über wirksames Engagement nachdenken würdest?'"
            ),
        },

        "reflexion": (
            "Letzte Frage für heute:\n\n"
            "Hat sich deine eigene Haltung durch den Perspektivwechsel verändert – "
            "auch nur ein kleines bisschen? Und wenn ja: was genau hat sich verschoben?"
        ),
    },

    # ── Modul 5: Placeholder ─────────────────────────────────────────────────

    5: {
        "titel":     "Handlungsspielräume",
        "intro":     "texttexttext",
        "ki_prompt": {s: "texttexttext" for s in
                      ["precontemplation","contemplation","preparation","action","maintenance"]},
        "reflexion": "texttexttext",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# INLINE-SKALEN
# ─────────────────────────────────────────────────────────────────────────────

SKALEN = [
    {
        "id":         "political_efficacy_pre",
        "frage":      (
            "Kurze Zwischenfrage:\n\n"
            "»Meine Meinung hat Einfluss auf politische Entscheidungen.«\n\n"
            "1 – stimme gar nicht zu\n"
            "2 – eher nicht\n"
            "3 – neutral\n"
            "4 – eher schon\n"
            "5 – stimme voll zu"
        ),
        "nach_modul": 1,
    },
    {
        "id":         "perspective_taking_mid",
        "frage":      (
            "Kurze Zwischenfrage:\n\n"
            "»Es fällt mir leicht, politische Standpunkte "
            "zu verstehen, die ich nicht teile.«\n\n"
            "1 – stimme gar nicht zu\n"
            "2 – eher nicht\n"
            "3 – neutral\n"
            "4 – eher schon\n"
            "5 – stimme voll zu"
        ),
        "nach_modul": 4,   # direkt nach Perspektivwechsel-Modul
    },
    {
        "id":         "political_efficacy_post",
        "frage":      (
            "Abschlussfrage der Studie:\n\n"
            "»Meine Meinung hat Einfluss auf politische Entscheidungen.«\n\n"
            "1 – stimme gar nicht zu\n"
            "2 – eher nicht\n"
            "3 – neutral\n"
            "4 – eher schon\n"
            "5 – stimme voll zu"
        ),
        "nach_modul": 5,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# QUESTS (Gamification-Gruppe)
# ─────────────────────────────────────────────────────────────────────────────

QUESTS = {
    1: {
        "titel":        "texttexttext",
        "beschreibung": "texttexttext",
        "abschluss":    "texttexttext",
    },
    2: {
        "titel":        "texttexttext",
        "beschreibung": "texttexttext",
        "abschluss":    "texttexttext",
    },
    3: {
        "titel":        "texttexttext",
        "beschreibung": "texttexttext",
        "abschluss":    "texttexttext",
    },
    4: {
        "titel":        "🔄 Quest: Der Perspektiv-Tausch",
        "beschreibung": (
            "Suche heute ein Gespräch, einen Text oder einen Post zu einem Thema, "
            "bei dem du eine klare Meinung hast.\n\n"
            "Versuche, die Gegenseite ehrlich zu verstehen – nicht um zuzustimmen, "
            "sondern um zu verstehen, *wie* jemand dazu kommen kann.\n\n"
            "Komm morgen zurück und berichte, was du entdeckt hast."
        ),
        "abschluss": (
            "Quest abgeschlossen! 🔄\n"
            "Du hast heute etwas getan, das die meisten Menschen vermeiden: "
            "eine unbequeme Perspektive wirklich ernst genommen."
        ),
    },
    5: {
        "titel":        "texttexttext",
        "beschreibung": "texttexttext",
        "abschluss":    "texttexttext",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# BADGES
# ─────────────────────────────────────────────────────────────────────────────

BADGES = {
    "erster_start":   "🌟 Pionier:in – Du hast die Reise begonnen.",
    "offenheit":      "💬 Offen geblieben – Du hast etwas Persönliches geteilt.",
    "perspektive":    "🔄 Perspektivwechsel – Du hast eine fremde Sichtweise wirklich ernst genommen.",
    "widerspruch":    "⚡ Im Widerspruch geblieben – Du hast nicht zugestimmt, aber zugehört.",
    "streak_3":       "🔥 3 Tage dabei – Dein Engagement macht den Unterschied.",
    "streak_7":       "🔥 Eine Woche – Das ist beeindruckend.",
    "modul_3":        "🎯 Halbzeit – Du bist tiefer eingetaucht als die meisten.",
    "alle_quests":    "🏆 Alle Quests abgeschlossen.",
    "abschluss":      "🎓 Studie abgeschlossen – Danke für deinen Beitrag zur Wissenschaft.",
}

# ─────────────────────────────────────────────────────────────────────────────
# BADGE-TRIGGER (wann wird welches Badge mid-session ausgelöst?)
# ─────────────────────────────────────────────────────────────────────────────
# Schlüssel = Trigger-Name (wird von handlers.py gesetzt)
# Wert = Badge-Key aus BADGES

BADGE_TRIGGERS = {
    "tiefes_gespraech":    "offenheit",
    "perspektivwechsel":   "perspektive",
    "widerspruch_gehalten": "widerspruch",
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIFFHANGER
# ─────────────────────────────────────────────────────────────────────────────

CLIFFHANGER = {
    1: "texttexttext",
    2: "texttexttext",
    3: (
        "🔮 Nächste Woche: Du wirst deine eigene Perspektive herausfordern. "
        "Nicht um sie aufzugeben – sondern um zu verstehen, warum du sie hast."
    ),
    4: "texttexttext",
}
