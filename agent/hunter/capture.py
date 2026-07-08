import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

log = logging.getLogger("spectre.hunter.capture")


@dataclass
class AttackEvent:
    node_id: str
    timestamp: float
    source_ip: str
    method: str
    path: str
    headers: dict
    body: Optional[str]
    payload: Optional[bytes] = None
    classification: Optional[dict] = None


class CaptureEngine:
    def __init__(self):
        self.captured = []

    async def poll(self, node) -> list[AttackEvent]:
        events = []

        try:
            async with aiohttp.ClientSession() as session:
                proc = await asyncio.create_subprocess_exec(
                    "journalctl", "-u", f"spectre-{node.id}",
                    "--since", "5 minutes ago",
                    "--no-pager",
                    stdout=asyncio.PIPE,
                    stderr=asyncio.DEVNULL,
                )
                stdout, _ = await proc.communicate()

                for line in stdout.decode().splitlines():
                    if "[CAPTURE]" in line:
                        events.append(self._parse_line(line, node.id))

        except Exception as e:
            log.debug(f"Poll failed for {node.id}: {e}")

        self.captured.extend(events)
        return events

    def _parse_line(self, line: str, node_id: str) -> AttackEvent:
        return AttackEvent(
            node_id=node_id,
            timestamp=time.time(),
            source_ip="unknown",
            method="UNKNOWN",
            path="/",
            headers={},
            body=line,
        )

    async def store_payload(self, event: AttackEvent):
        path = f"data/payloads/{event.node_id}_{int(event.timestamp)}.bin"
        import aiofiles
        async with aiofiles.open(path, "wb") as f:
            if event.payload:
                await f.write(event.payload)
        log.info(f"Payload stored: {path}")
