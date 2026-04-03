import pickle
from pathlib import Path
from dataclasses import dataclass, field

import anyio
from anyio import Path as AsyncPath

from scrapling.core.utils import log
from scrapling.core._types import Set, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from scrapling.spiders.request import Request


@dataclass
class CheckpointData:
    """Container for checkpoint state."""

    requests: List["Request"] = field(default_factory=list)
    seen: Set[bytes] = field(default_factory=set)


class CheckpointManager:
    """Manages saving and loading checkpoint state to/from disk."""

    CHECKPOINT_FILE = "checkpoint.pkl"

    def __init__(self, crawldir: str | Path | AsyncPath, interval: float = 300.0):
        self.crawldir = AsyncPath(crawldir)
        self._checkpoint_path = self.crawldir / self.CHECKPOINT_FILE
        self.interval = interval
        if not isinstance(interval, (int, float)):
            raise TypeError("Checkpoints interval must be integer or float.")
        else:
            if interval < 0:
                raise ValueError("Checkpoints interval must be equal or greater than 0.")

    async def has_checkpoint(self) -> bool:
        """Check if a checkpoint exists."""
        pass

    async def save(self, data: CheckpointData) -> None:
        """Save checkpoint data to disk atomically."""
        pass

    async def load(self) -> Optional[CheckpointData]:
        """Load checkpoint data from disk.

        Returns None if no checkpoint exists or if loading fails.
        """
        pass

    async def cleanup(self) -> None:
        """Delete checkpoint file after successful completion."""
        pass
