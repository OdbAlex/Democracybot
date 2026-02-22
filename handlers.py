# =============================================================================
# handlers.py  (~290 Zeilen)
# -----------------------------------------------------------------------------
# Ablauflogik: Was passiert bei welchem Telegram-Befehl oder welcher Nachricht?
# =============================================================================

from telegram import Update
from telegram.ext import ContextTypes

import data_manager as db
import ai_service   as ai
import gamification as gami
from study_content import MODULES, TTM_FRAGEN, TTM_RESULT_TEXTS, SKALEN


# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid      = update.effective_user.id
    username = update.effective_user.first_name or "Teilnehmer:in"
    user     = db.get_user(tid)

    if user is None:
        user = db.create_user(tid, username)
        await update.message.reply_text(
            f"Hallo {username}! 👋\n\n"
            "Willkommen in einer psychologischen Studie über demokratische "
            "Teilhabe und emotionale Selbstwahrnehmung.\n\n"
            "Wir werden 5 Gesprächssessions führen – je ca. 10–15 Minuten. "
            "Deine Antworten werden anonymisiert ausgewertet.\n\n"
            "Stimmst du der Teilnahme zu?\n"
            "Antworte mit /ja um fortzufahren, oder /nein um abzubrechen."
        )
    else:
        modul = user.get("aktuelles_modul", 1)
        await update.message.reply_text(
            f"Schön, dass du wieder da bist, {username}! 👋\n\n"
            f"Du bist bei Session {modul}/5.\n"
            "Schreib /session um weiterzumachen."
        )


# ─── /ja – Einwilligung ────────────────────────────────────────────────────────

async def cmd_ja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid  = update.effective_user.id
    user = db.get_user(tid)
    if not user:
        await update.message.reply_text("Bitte starte mit /start."); return

    db.update_user(tid, {"einwilligung": True, "ttm_phase": 0})
    await update.message.reply_text(
        "Danke! ✓\n\n"
        "Bevor wir beginnen, stelle ich dir 3 kurze Einstiegsfragen. "
        "Es gibt keine richtigen oder falschen Antworten.\n\n" +
        TTM_FRAGEN[0]
    )


# ─── /nein – Ablehnung ────────────────────────────────────────────────────────

async def cmd_nein(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kein Problem – du kannst jederzeit mit /start neu beginnen."
    )


# ─── Normale Nachrichten – Routing ────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid  = update.effective_user.id
    text = update.message.text
    user = db.get_user(tid)

    if not user:
        await update.message.reply_text("Bitte starte mit /start."); return
    if not user.get("einwilligung"):
        await update.message.reply_text(
            "Bitte bestätige zuerst deine Teilnahme mit /ja."
        ); return

    # TTM-Onboarding läuft noch
    if user.get("ttm_stage") is None:
        await _handle_ttm(update, tid, user, text); return

    # Session aktiv
    if user.get("session_aktiv"):
        await _handle_session_msg(update, context, tid, user, text); return

    await update.message.reply_text("Schreib /session um eine Session zu starten.")


async def _handle_ttm(update, tid: int, user: dict, text: str):
    """Verarbeitet Antworten während TTM-Onboarding (3 Fragen)."""
    antworten = user.get("ttm_antworten", [])
    antworten.append(text)
    phase     = len(antworten)

    db.update_user(tid, {"ttm_antworten": antworten, "ttm_phase": phase})

    if phase < len(TTM_FRAGEN):
        await update.message.reply_text(TTM_FRAGEN[phase])
    else:
        # Alle Fragen beantwortet → klassifizieren
        stage       = ai.classify_ttm(antworten)
        result_text = TTM_RESULT_TEXTS.get(stage, TTM_RESULT_TEXTS["contemplation"])
        db.update_user(tid, {"ttm_stage": stage})

        await update.message.reply_text(
            f"Danke für deine Offenheit.\n\n{result_text}\n\n"
            "Schreib /session wenn du bereit bist, mit der ersten Session zu beginnen."
        )


async def _handle_session_msg(update, context, tid: int, user: dict, text: str):
    """Verarbeitet Nachrichten während einer aktiven Session."""
    modul_nr = user.get("aktuelles_modul", 1)

    # History speichern
    db.add_message(tid, "user", text)

    # Letzten Bot-Turn für Badge-Detection
    history  = db.get_history(tid)
    bot_last = next(
        (m["content"] for m in reversed(history) if m["role"] == "assistant"),
        ""
    )

    # Mid-session Badge Trigger (Gamification-Gruppe)
    if user["gruppe"] == "gamification":
        trigger = ai.detect_badge_trigger(text, bot_last, modul_nr)
        if trigger:
            badge_text = gami.try_mid_session_badge(user, trigger)
            if badge_text:
                db.update_user(tid, {"badges": user["badges"]})
                await update.message.reply_text(badge_text)

    # KI-Antwort
    ttm_stage  = user.get("ttm_stage", "contemplation")
    ki_prompt  = MODULES.get(modul_nr, {}).get("ki_prompt", {}).get(ttm_stage, "")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    response = ai.get_response(history, ki_prompt)
    db.add_message(tid, "assistant", response)
    await update.message.reply_text(response)


# ─── /session ─────────────────────────────────────────────────────────────────

async def cmd_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid  = update.effective_user.id
    user = db.get_user(tid)

    if not user:
        await update.message.reply_text("Bitte starte mit /start."); return
    if not user.get("einwilligung"):
        await update.message.reply_text("Bitte bestätige mit /ja."); return
    if user.get("ttm_stage") is None:
        await update.message.reply_text(
            "Bitte beantworte zuerst die Einstiegsfragen. Schreib /start."
        ); return
    if user.get("session_aktiv"):
        await update.message.reply_text(
            "Du bist gerade in einer aktiven Session. "
            "Schreib einfach weiter oder beende mit /beenden."
        ); return

    modul_nr = user.get("aktuelles_modul", 1)
    if modul_nr > len(MODULES):
        await update.message.reply_text(
            "🎓 Du hast alle Sessions abgeschlossen. Vielen Dank!"
        ); return

    modul = MODULES[modul_nr]
    user  = db.update_user(tid, gami.update_streak(user))

    # Gamification: Start-Summary + Quest
    if user["gruppe"] == "gamification" and user.get("abgeschlossene_module", 0) > 0:
        await update.message.reply_text(gami.get_start_summary(user))
        streak_msg = gami.get_streak_message(user["streak"])
        if streak_msg:
            await update.message.reply_text(streak_msg)
        quest = gami.get_quest_intro(modul_nr)
        if quest:
            await update.message.reply_text(f"🗺️ Quest für heute:\n\n{quest}")

    db.update_user(tid, {"session_aktiv": True})
    db.clear_history(tid)

    await update.message.reply_text(
        f"📖 Session {modul_nr}/5: {modul['titel']}\n\n{modul['intro']}"
    )


# ─── /beenden ─────────────────────────────────────────────────────────────────

async def cmd_beenden(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid  = update.effective_user.id
    user = db.get_user(tid)

    if not user or not user.get("session_aktiv"):
        await update.message.reply_text("Keine aktive Session."); return

    modul_nr = user.get("aktuelles_modul", 1)
    modul    = MODULES.get(modul_nr, {})

    # Reflexionsfrage
    await update.message.reply_text(f"💭 {modul.get('reflexion', '...')}")

    # Inline-Skala falls fällig
    for skala in SKALEN:
        if skala["nach_modul"] == modul_nr:
            await update.message.reply_text(skala["frage"])
            # Skalenwert kommt als nächste Nachricht → gesondert verarbeiten
            # TODO: State-Machine für Skalenabfrage implementieren

    # Daten speichern
    history = db.get_history(tid)
    summary = ai.summarize_session(history)
    db.save_session(tid, modul_nr, history, summary)
    db.clear_history(tid)

    neu  = user.get("abgeschlossene_module", 0) + 1
    user = db.update_user(tid, {
        "session_aktiv":         False,
        "aktuelles_modul":       modul_nr + 1,
        "abgeschlossene_module": neu,
    })

    # Gamification: Badges + Gesamtprogress + Quest-Abschluss + Cliffhanger
    if user["gruppe"] == "gamification":
        for badge in gami.check_new_badges(user):
            await update.message.reply_text(badge)
        db.update_user(tid, {"badges": user["badges"]})

        quest_done = gami.get_quest_completion(modul_nr)
        if quest_done:
            db.update_user(tid, {"quests_gesamt": user.get("quests_gesamt", 0) + 1})
            await update.message.reply_text(quest_done)

        await update.message.reply_text(gami.overall_progress_bar(neu))

        cliff = gami.get_cliffhanger(modul_nr)
        if cliff:
            await update.message.reply_text(cliff)

    await update.message.reply_text(
        f"✅ Session {modul_nr} abgeschlossen!\n\n"
        "Bis zur nächsten Session. Schreib /session wenn du bereit bist."
    )


# ─── /status ──────────────────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid  = update.effective_user.id
    user = db.get_user(tid)
    if not user:
        await update.message.reply_text("Bitte starte mit /start."); return

    abg = user.get("abgeschlossene_module", 0)
    if user["gruppe"] == "gamification":
        bar    = gami.overall_progress_bar(abg)
        streak = user.get("streak", 0)
        badges = user.get("badges", [])
        ttm    = user.get("ttm_stage", "–")
        await update.message.reply_text(
            f"{bar}\n🔥 Streak: {streak} Tag(e)\n"
            f"🏅 Abzeichen: {len(badges)}\n🧭 TTM-Stufe: {ttm}"
        )
    else:
        await update.message.reply_text(
            f"Dein Fortschritt: {abg}/5 Sessions abgeschlossen.\n"
            "Schreib /session um weiterzumachen."
        )
