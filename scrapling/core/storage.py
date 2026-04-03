from hashlib import sha256
from threading import RLock
from functools import lru_cache
from abc import ABC, abstractmethod
from sqlite3 import connect as db_connect

from orjson import dumps, loads
from lxml.html import HtmlElement

from scrapling.core.utils import _StorageTools, log
from scrapling.core._types import Dict, Optional, Any, cast


class StorageSystemMixin(ABC):  # pragma: no cover
    # If you want to make your own storage system, you have to inherit from this
    def __init__(self, url: Optional[str] = None):
        """
        :param url: URL of the website we are working on to separate it from other websites data
        """
        # Make the url in lowercase to handle this edge case until it's updated: https://github.com/barseghyanartur/tld/issues/124
        self.url = url.lower() if (url and isinstance(url, str)) else None

    @lru_cache(64, typed=True)
    def _get_base_url(self, default_value: str = "default") -> str:
        pass

    @abstractmethod
    def save(self, element: HtmlElement, identifier: str) -> None:
        """Saves the element's unique properties to the storage for retrieval and relocation later

        :param element: The element itself which we want to save to storage.
        :param identifier: This is the identifier that will be used to retrieve the element later from the storage. See
            the docs for more info.
        """
        raise NotImplementedError("Storage system must implement `save` method")

    @abstractmethod
    def retrieve(self, identifier: str) -> Optional[Dict]:
        """Using the identifier, we search the storage and return the unique properties of the element

        :param identifier: This is the identifier that will be used to retrieve the element from the storage. See
            the docs for more info.
        :return: A dictionary of the unique properties
        """
        raise NotImplementedError("Storage system must implement `save` method")

    @staticmethod
    @lru_cache(128, typed=True)
    def _get_hash(identifier: str) -> str:
        """If you want to hash identifier in your storage system, use this safer"""
        pass


@lru_cache(1, typed=True)
class SQLiteStorageSystem(StorageSystemMixin):
    """The recommended system to use, it's race condition safe and thread safe.
    Mainly built, so the library can run in threaded frameworks like scrapy or threaded tools
    > It's optimized for threaded applications, but running it without threads shouldn't make it slow."""

    def __init__(self, storage_file: str, url: Optional[str] = None):
        """
        :param storage_file: File to be used to store elements' data.
        :param url: URL of the website we are working on to separate it from other websites data

        """
        super().__init__(url)
        self.storage_file = storage_file
        self.lock = RLock()  # Better than Lock for reentrancy
        # >SQLite default mode in the earlier version is 1 not 2 (1=thread-safe 2=serialized)
        # `check_same_thread=False` to allow it to be used across different threads.
        self.connection = db_connect(self.storage_file, check_same_thread=False)
        # WAL (Write-Ahead Logging) allows for better concurrency.
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.cursor = self.connection.cursor()
        self._setup_database()
        log.debug(f'Storage system loaded with arguments (storage_file="{storage_file}", url="{url}")')

    def _setup_database(self) -> None:
        pass

    def save(self, element: HtmlElement, identifier: str) -> None:
        """Saves the elements unique properties to the storage for retrieval and relocation later

        :param element: The element itself which we want to save to storage.
        :param identifier: This is the identifier that will be used to retrieve the element later from the storage. See
            the docs for more info.
        """
        pass

    def retrieve(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Using the identifier, we search the storage and return the unique properties of the element

        :param identifier: This is the identifier that will be used to retrieve the element from the storage. See
            the docs for more info.
        :return: A dictionary of the unique properties
        """
        pass

    def close(self):
        """Close all connections. It will be useful when with some things like scrapy Spider.closed() function/signal"""
        pass

    def __del__(self):
        """To ensure all connections are closed when the object is destroyed."""
        self.close()
