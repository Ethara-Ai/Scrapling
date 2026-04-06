import asyncio
from itertools import count

from scrapling.core.utils import log
from scrapling.spiders.request import Request
from scrapling.core._types import List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from scrapling.spiders.checkpoint import CheckpointData


class Scheduler:
    """
    Priority queue with URL deduplication. (heapq)

    Higher priority requests are processed first.
    Duplicate URLs are filtered unless dont_filter=True.
    """

    def __init__(self, include_kwargs: bool = False, include_headers: bool = False, keep_fragments: bool = False):
        self._queue: asyncio.PriorityQueue[tuple[int, int, Request]] = asyncio.PriorityQueue()
        self._seen: set[bytes] = set()
        self._counter = count()
        # Mirror dict for snapshot without draining queue
        self._pending: dict[int, tuple[int, int, Request]] = {}
        self._include_kwargs = include_kwargs
        self._include_headers = include_headers
        self._keep_fragments = keep_fragments

    async def enqueue(self, request: Request) -> bool:
        """Add a request to the queue."""
        pass

    async def dequeue(self) -> Request:
        """Get the next request to process."""
        pass

    def __len__(self) -> int:
        return self._queue.qsize()

    @property
    def is_empty(self) -> bool:
        pass

    def snapshot(self) -> Tuple[List[Request], Set[bytes]]:
        """Create a snapshot of the current state for checkpoints."""
        pass

    def restore(self, data: "CheckpointData") -> None:
        """Restore scheduler state from checkpoint data.

        :param data: CheckpointData containing requests and seen set
        """
        pass
