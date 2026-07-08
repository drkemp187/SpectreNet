import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent.deployer import tor, fly
from agent.hunter.capture import CaptureEngine
from agent.hunter.classifier import Classifier
from agent.monitor.scraper import DarkWebMonitor
from agent.alerts.discord import DiscordNotifier
from agent.alerts.telegram import TelegramNotifier

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("spectre")


class SpectreNet:
    def __init__(self):
        self.running = False
        self.nodes = []
        self.capture = CaptureEngine()
        self.classifier = Classifier()
        self.monitor = DarkWebMonitor()
        self.alerts = self._init_alerts()
        self.deployers = [
            tor.TorDeployer(),
            fly.FlyDeployer(),
        ]

    def _init_alerts(self):
        notifiers = []
        if os.getenv("DISCORD_WEBHOOK_URL"):
            notifiers.append(DiscordNotifier())
        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            notifiers.append(TelegramNotifier())
        return notifiers

    async def start(self):
        self.running = True
        log.info("SpectreNet agent starting...")

        await self._announce("startup", "SpectreNet agent is online")

        while self.running:
            try:
                await self._cycle()
                await asyncio.sleep(60)
            except Exception as e:
                log.error(f"Cycle failed: {e}", exc_info=True)
                await self._announce("error", f"Cycle failed: {e}")

    async def _cycle(self):
        log.info("Starting deployment cycle")

        for deployer in self.deployers:
            try:
                node = await deployer.deploy()
                self.nodes.append(node)
                log.info(f"Deployed node: {node.id} at {node.endpoint}")
                await self._announce("deploy", f"Node {node.id} deployed at {node.endpoint}")
            except Exception as e:
                log.warning(f"Deployer {deployer.__class__.__name__} failed: {e}")

        await self._hunt()
        await self._check_burned()
        await self._rotate()

    async def _hunt(self):
        for node in self.nodes:
            if node.status != "active":
                continue
            events = await self.capture.poll(node)
            for event in events:
                classification = await self.classifier.classify(event)
                event.classification = classification
                await self._announce("contact", str(event))
                if classification.intent == "malicious":
                    await self.capture.store_payload(event)

    async def _check_burned(self):
        mentions = await self.monitor.check_mentions(self.nodes)
        for node_id in mentions:
            log.warning(f"Node {node_id} is burned — mentioned on dark web")
            await self._announce("burned", f"Node {node_id} compromised — rotating")

    async def _rotate(self):
        to_rotate = [n for n in self.nodes if n.status in ("burned", "degraded")]
        for node in to_rotate:
            deployer = next(d for d in self.deployers if d.can_handle(node))
            await deployer.destroy(node)
            self.nodes.remove(node)
            log.info(f"Destroyed node: {node.id}")
            await self._announce("destroy", f"Node {node.id} destroyed")

    async def _announce(self, event_type, message):
        for notifier in self.alerts:
            try:
                await notifier.send(event_type, message)
            except Exception as e:
                log.warning(f"Notifier failed: {e}")

    def stop(self):
        self.running = False
        log.info("SpectreNet agent stopping...")


async def main():
    agent = SpectreNet()

    def shutdown():
        agent.stop()

    signal.signal(signal.SIGINT, lambda s, f: shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown())

    try:
        await agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        log.info("SpectreNet agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
