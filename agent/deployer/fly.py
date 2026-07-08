import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

from agent.deployer.base import BaseDeployer, Node, NodeStatus

log = logging.getLogger("spectre.deployer.fly")


APP_TEMPLATE = """
const http = require('http');
const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    console.log(`[CAPTURE] ${req.method} ${req.url} from ${req.socket.remoteAddress}`);
    console.log(`[CAPTURE] headers: ${JSON.stringify(req.headers)}`);
    if (body) console.log(`[CAPTURE] body: ${body}`);
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end('<html><body><h1>System Dashboard</h1><form method=POST action=/login><input name=username><input name=password type=password><button>Login</button></form></body></html>');
  });
});
server.listen(process.env.PORT || 3000);
"""


class FlyDeployer(BaseDeployer):
    def __init__(self):
        self.token = os.getenv("FLY_API_TOKEN")
        self.apps = []

    async def deploy(self) -> Node:
        if not self.token:
            raise RuntimeError("FLY_API_TOKEN not set")

        app_name = f"spectre-{os.urandom(4).hex()}"

        deploy_dir = Path(tempfile.mkdtemp(prefix="spectre_fly_"))
        (deploy_dir / "index.js").write_text(APP_TEMPLATE)
        (deploy_dir / "package.json").write_text(
            json.dumps({"name": app_name, "main": "index.js", "scripts": {"start": "node index.js"}})
        )
        (deploy_dir / "Dockerfile").write_text(
            "FROM node:20-alpine\nWORKDIR /app\nCOPY package.json index.js ./\nRUN npm install\nCMD [\"npm\", \"start\"]\n"
        )

        proc = await asyncio.create_subprocess_exec(
            "fly", "apps", "create", app_name,
            "--org", "personal",
            cwd=str(deploy_dir),
            stdout=asyncio.PIPE,
            stderr=asyncio.PIPE,
        )
        await proc.wait()

        proc = await asyncio.create_subprocess_exec(
            "fly", "deploy",
            "--app", app_name,
            "--strategy", "immediate",
            "--no-cache",
            cwd=str(deploy_dir),
            stdout=asyncio.PIPE,
            stderr=asyncio.PIPE,
        )
        await proc.wait()

        node = Node(
            id=app_name,
            endpoint=f"https://{app_name}.fly.dev",
            node_type="fly",
            status=NodeStatus.ACTIVE,
            metadata={"deploy_dir": str(deploy_dir)},
        )
        self.apps.append(node)
        log.info(f"Fly node deployed: {node.endpoint}")
        return node

    async def destroy(self, node: Node):
        proc = await asyncio.create_subprocess_exec(
            "fly", "apps", "destroy", node.id, "--yes",
            stdout=asyncio.DEVNULL,
            stderr=asyncio.DEVNULL,
        )
        await proc.wait()
        node.status = NodeStatus.DESTROYED
        log.info(f"Fly node {node.id} destroyed")

    def can_handle(self, node: Node) -> bool:
        return node.node_type == "fly"
