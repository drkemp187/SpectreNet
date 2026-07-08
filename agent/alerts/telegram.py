import logging
import os

import aiohttp

log = logging.getLogger("spectre.alerts.telegram")


class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    async def send(self, event_type: str, message: str):
        if not self.token or not self.chat_id:
            return
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": f"SpectreNet — {event_type}: {message}",
                "parse_mode": "HTML",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        log.warning(f"Telegram API returned {resp.status}")
        except Exception as e:
            log.warning(f"Telegram send failed: {e}")
