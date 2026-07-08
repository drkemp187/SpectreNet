import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

log = logging.getLogger("spectre.monitor")


DARK_WEB_SITES = [
    "http://exploitivzcm5dawzhe6c67bkg6zckrh2evg7tb4x3qhzdyta6pntyqd.onion",
    "http://breachdbsztftyjhv3k7p2y3l5vryo5o4mhqotd6z2q7k5yq3wxxqzqd.onion",
]

CLEAR_WEB_SITES = [
    "https://cybernews.com/security/",
    "https://thehackernews.com/",
    "https://www.bleepingcomputer.com/",
]


class DarkWebMonitor:
    def __init__(self):
        self.session = None

    async def check_mentions(self, nodes) -> list[str]:
        burned = []
        for site in DARK_WEB_SITES + CLEAR_WEB_SITES:
            try:
                content = await self._fetch(site)
                if content:
                    for node in nodes:
                        if self._is_mentioned(content, node):
                            burned.append(node.id)
            except Exception as e:
                log.debug(f"Failed to check {site}: {e}")
        return burned

    async def _fetch(self, url: str) -> str | None:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status == 200:
                        return await resp.text()
        except Exception:
            pass
        return None

    def _is_mentioned(self, content: str, node) -> bool:
        base = re.escape(node.id.replace("tor_", "").replace("fly_", ""))
        patterns = [
            rf"http[s]?://{base}\.onion",
            rf"{node.id}",
            rf"{node.endpoint}",
            r"honeypot",
            r"honeypot\s+detected",
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)
