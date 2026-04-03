import json
import pprint
from pathlib import Path

import anyio
from anyio import Path as AsyncPath
from anyio import create_task_group, CapacityLimiter, create_memory_object_stream, EndOfStream

from scrapling.core.utils import log
from scrapling.spiders.request import Request
from scrapling.spiders.scheduler import Scheduler
from scrapling.spiders.session import SessionManager
from scrapling.spiders.result import CrawlStats, ItemList
from scrapling.spiders.checkpoint import CheckpointManager, CheckpointData
from scrapling.core._types import Dict, Union, Optional, TYPE_CHECKING, Any, AsyncGenerator

if TYPE_CHECKING:
    from scrapling.spiders.spider import Spider


def _dump(obj: Dict) -> str:
    pass


class CrawlerEngine:
    """Orchestrates the crawling process."""

    def __init__(
        self,
        spider: "Spider",
        session_manager: SessionManager,
        crawldir: Optional[Union[str, Path, AsyncPath]] = None,
        interval: float = 300.0,
    ):
        self.spider = spider
        self.session_manager = session_manager
        self.scheduler = Scheduler(
            include_kwargs=spider.fp_include_kwargs,
            include_headers=spider.fp_include_headers,
            keep_fragments=spider.fp_keep_fragments,
        )
        self.stats = CrawlStats()

        self._global_limiter = CapacityLimiter(spider.concurrent_requests)
        self._domain_limiters: dict[str, CapacityLimiter] = {}
        self._allowed_domains: set[str] = spider.allowed_domains or set()

        self._active_tasks: int = 0
        self._running: bool = False
        self._items: ItemList = ItemList()
        self._item_stream: Any = None

        self._checkpoint_system_enabled = bool(crawldir)
        self._checkpoint_manager = CheckpointManager(crawldir or "", interval)
        self._last_checkpoint_time: float = 0.0
        self._pause_requested: bool = False
        self._force_stop: bool = False
        self.paused: bool = False

    def _is_domain_allowed(self, request: Request) -> bool:
        """Check if the request's domain is in allowed_domains."""
        pass

    def _rate_limiter(self, domain: str) -> CapacityLimiter:
        """Get or create a per-domain concurrency limiter if enabled, otherwise use the global limiter."""
        pass

    def _normalize_request(self, request: Request) -> None:
        """Normalize request fields before enqueueing.

        Resolves empty sid to the session manager's default session ID.
        This ensures consistent fingerprinting for requests using the same session.
        """
        pass

    async def _process_request(self, request: Request) -> None:
        """Download and process a single request."""
        pass

    async def _task_wrapper(self, request: Request) -> None:
        """Wrapper to track active task count."""
        pass

    def request_pause(self) -> None:
        """Request a graceful pause of the crawl.

        First call: requests graceful pause (waits for active tasks).
        Second call: forces immediate stop.
        """
        pass

    async def _save_checkpoint(self) -> None:
        """Save current state to checkpoint files."""
        pass

    def _is_checkpoint_time(self) -> bool:
        """Check if it's time for the periodic checkpoint."""
        pass

    async def _restore_from_checkpoint(self) -> bool:
        """Attempt to restore state from checkpoint.

        Returns True if successfully restored, False otherwise.
        """
        pass

    async def crawl(self) -> CrawlStats:
        """Run the spider and return CrawlStats."""
        pass

    @property
    def items(self) -> ItemList:
        """Access scraped items."""
        pass

    def __aiter__(self) -> AsyncGenerator[dict, None]:
        return self._stream()

    async def _stream(self) -> AsyncGenerator[dict, None]:
        """Async generator that runs crawl and yields items."""
        pass
