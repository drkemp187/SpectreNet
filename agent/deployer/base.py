from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NodeStatus(Enum):
    DEPLOYING = "deploying"
    ACTIVE = "active"
    DEGRADED = "degraded"
    BURNED = "burned"
    DESTROYED = "destroyed"


@dataclass
class Node:
    id: str
    endpoint: str
    node_type: str
    status: NodeStatus = NodeStatus.DEPLOYING
    metadata: dict = field(default_factory=dict)
    deployed_at: Optional[float] = None


class BaseDeployer:
    async def deploy(self) -> Node:
        raise NotImplementedError

    async def destroy(self, node: Node):
        raise NotImplementedError

    def can_handle(self, node: Node) -> bool:
        raise NotImplementedError
