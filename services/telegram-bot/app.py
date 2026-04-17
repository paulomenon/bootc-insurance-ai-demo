import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import requests
import time
from shared.config import TELEGRAM_BOT_TOKEN, LLM_SERVICE_URL, AGENTIC_AI_URL
from shared.logger import get_logger

log = get_logger("telegram-bot")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def get_updates(offset: int = 0) -> list:
    try:
        resp = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35,
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("result", [])
    except requests.RequestException as e:
        log.error(f"Failed to get updates: {e}")
    return []


def send_message(chat_id: int, text: str):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
    except requests.RequestException as e:
        log.error(f"Failed to send message to {chat_id}: {e}")


def analyze_message(text: str) -> dict:
    """Send message to the Dummy LLM for intent detection."""
    try:
        resp = requests.post(
            f"{LLM_SERVICE_URL}/analyze",
            json={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error(f"LLM service call failed: {e}")
        return {"intent": "unknown", "confidence": 0, "entities": {}, "routing": "none"}


def process_with_agentic_ai(llm_result: dict) -> dict:
    """Send the LLM analysis to the Agentic AI for agent coordination."""
    try:
        resp = requests.post(
            f"{AGENTIC_AI_URL}/process",
            json=llm_result,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error(f"Agentic AI call failed: {e}")
        return {
            "success": False,
            "message": "⚠️ System is temporarily unavailable. Please try again or call local emergency services.",
        }


def handle_message(chat_id: int, text: str, user_name: str):
    log.info(f"Message from {user_name} ({chat_id}): {text}")

    send_message(chat_id, "⏳ Processing your request...")

    llm_result = analyze_message(text)
    log.info(f"LLM analysis: {llm_result}")

    if llm_result["intent"] == "unknown":
        send_message(
            chat_id,
            "I'm sorry, I didn't understand your request.\n\n"
            "Try describing an emergency situation, for example:\n"
            "• _I had a ski accident in the Alps, I need an ambulance_\n"
            "• _I want a helicopter_\n"
            "• _Is my policy covering helicopter transport?_",
        )
        return

    result = process_with_agentic_ai(llm_result)
    send_message(chat_id, result.get("message", "Something went wrong. Please try again."))


def main():
    if not TELEGRAM_BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN is not set. Exiting.")
        log.error("Set it in .env or as an environment variable.")
        sys.exit(1)

    log.info("Telegram bot starting (long polling mode)...")
    log.info(f"LLM Service: {LLM_SERVICE_URL}")
    log.info(f"Agentic AI: {AGENTIC_AI_URL}")

    offset = 0
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                user = message.get("from", {})
                user_name = user.get("first_name", "Unknown")

                if chat_id and text:
                    handle_message(chat_id, text, user_name)

        except KeyboardInterrupt:
            log.info("Bot stopped by user")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
