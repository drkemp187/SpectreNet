import logging
import os

from discord_webhook import DiscordWebhook

log = logging.getLogger("spectre.alerts.discord")

EMOJI_MAP = {
    "startup": "🟢",
    "deploy": "🌐",
    "contact": "🚨",
    "burned": "🔥",
    "destroy": "💀",
    "error": "❌",
}


class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    async def send(self, event_type: str, message: str):
        if not self.webhook_url:
            return
        try:
            emoji = EMOJI_MAP.get(event_type, "ℹ️")
            webhook = DiscordWebhook(
                url=self.webhook_url,
                content=f"{emoji} **SpectreNet** — {message}",
            )
            webhook.execute()
        except Exception as e:
            log.warning(f"Discord send failed: {e}")
