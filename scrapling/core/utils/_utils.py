import logging
from itertools import chain
from re import compile as re_compile
from contextvars import ContextVar, Token

from lxml import html

from scrapling.core._types import Any, Dict, Iterable, List

# Using cache on top of a class is a brilliant way to achieve a Singleton design pattern without much code
from functools import lru_cache  # isort:skip

html_forbidden = (html.HtmlComment,)

__CLEANING_TABLE__ = str.maketrans({"\t": " ", "\n": None, "\r": None})
__CONSECUTIVE_SPACES_REGEX__ = re_compile(r" +")


@lru_cache(1, typed=True)
def setup_logger():
    """Create and configure a logger with a standard format.

    :returns: logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("scrapling")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handler to logger (if not already added)
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


_current_logger: ContextVar[logging.Logger] = ContextVar("scrapling_logger", default=setup_logger())


class LoggerProxy:
    def __getattr__(self, name: str):
        return getattr(_current_logger.get(), name)


log = LoggerProxy()


def set_logger(logger: logging.Logger) -> Token:
    """Set the current context logger. Returns token for reset."""
    pass


def reset_logger(token: Token) -> None:
    """Reset logger to previous state using token."""
    pass


def flatten(lst: Iterable[Any]) -> List[Any]:
    pass


def _is_iterable(obj: Any) -> bool:
    # This will be used only in regex functions to make sure it's iterable but not string/bytes
    pass


class _StorageTools:
    @staticmethod
    def __clean_attributes(element: html.HtmlElement, forbidden: tuple = ()) -> Dict:
        pass

    @classmethod
    def element_to_dict(cls, element: html.HtmlElement) -> Dict:
        pass

    @classmethod
    def _get_element_path(cls, element: html.HtmlElement):
        pass


@lru_cache(128, typed=True)
def clean_spaces(string):
    pass
