from pathlib import Path
from dataclasses import dataclass, field

import orjson

from scrapling.core.utils import log
from scrapling.core._types import Any, Iterator, Dict, List, Tuple, Union


class ItemList(list):
    """A list of scraped items with export capabilities."""

    def to_json(self, path: Union[str, Path], *, indent: bool = False):
        """Export items to a JSON file.

        :param path: Path to the output file
        :param indent: Pretty-print with 2-space indentation (slightly slower)
        """
        pass

    def to_jsonl(self, path: Union[str, Path]):
        """Export items as JSON Lines (one JSON object per line).

        :param path: Path to the output file
        """
        pass


@dataclass
class CrawlStats:
    """Statistics for a crawl run."""

    requests_count: int = 0
    concurrent_requests: int = 0
    concurrent_requests_per_domain: int = 0
    failed_requests_count: int = 0
    offsite_requests_count: int = 0
    response_bytes: int = 0
    items_scraped: int = 0
    items_dropped: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    download_delay: float = 0.0
    blocked_requests_count: int = 0
    custom_stats: Dict = field(default_factory=dict)
    response_status_count: Dict = field(default_factory=dict)
    domains_response_bytes: Dict = field(default_factory=dict)
    sessions_requests_count: Dict = field(default_factory=dict)
    proxies: List[str | Dict | Tuple] = field(default_factory=list)
    log_levels_counter: Dict = field(default_factory=dict)

    @property
    def elapsed_seconds(self) -> float:
        pass

    @property
    def requests_per_second(self) -> float:
        pass

    def increment_status(self, status: int) -> None:
        pass

    def increment_response_bytes(self, domain: str, count: int) -> None:
        pass

    def increment_requests_count(self, sid: str) -> None:
        pass

    def to_dict(self) -> dict[str, Any]:
        pass


@dataclass
class CrawlResult:
    """Complete result from a spider run."""

    stats: CrawlStats
    items: ItemList
    paused: bool = False

    @property
    def completed(self) -> bool:
        """True if the crawl completed normally (not paused)."""
        pass

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.items)
