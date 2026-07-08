import asyncio
import logging
import tempfile
from pathlib import Path

from agent.deployer.base import BaseDeployer, Node, NodeStatus

log = logging.getLogger("spectre.deployer.tor")


class TorDeployer(BaseDeployer):
    def __init__(self):
        self.hidden_services = []
        self.tor_process = None

    async def deploy(self) -> Node:
        hs_dir = tempfile.mkdtemp(prefix="spectre_")

        html = """<!DOCTYPE html>
<html><head><title>Dashboard</title></head>
<body><h1>System Dashboard</h1>
<form method="POST" action="/login">
<input name="username" placeholder="admin">
<input name="password" type="password">
<button type="submit">Login</button>
</form></body></html>"""

        index_path = Path(hs_dir) / "index.html"
        index_path.write_text(html)

        torrc = f"""HiddenServiceDir {hs_dir}
HiddenServicePort 80 127.0.0.1:8080
"""

        torrc_path = Path(hs_dir) / "torrc"
        torrc_path.write_text(torrc)

        self.tor_process = await asyncio.create_subprocess_exec(
            "tor", "-f", str(torrc_path),
            stdout=asyncio.DEVNULL,
            stderr=asyncio.DEVNULL,
        )

        hostname_path = Path(hs_dir) / "hostname"
        for _ in range(30):
            if hostname_path.exists():
                break
            await asyncio.sleep(1)

        onion = hostname_path.read_text().strip() if hostname_path.exists() else "unknown.onion"

        node = Node(
            id=f"tor_{len(self.hidden_services)}",
            endpoint=f"http://{onion}",
            node_type="tor",
            status=NodeStatus.ACTIVE,
            metadata={"hs_dir": hs_dir, "port": 8080},
        )
        self.hidden_services.append(node)
        log.info(f"Tor hidden service deployed: {node.endpoint}")
        return node

    async def destroy(self, node: Node):
        if self.tor_process:
            self.tor_process.terminate()
            await self.tor_process.wait()
            self.tor_process = None
        node.status = NodeStatus.DESTROYED
        log.info(f"Tor node {node.id} destroyed")

    def can_handle(self, node: Node) -> bool:
        return node.node_type == "tor"
