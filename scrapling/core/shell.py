# -*- coding: utf-8 -*-
from sys import stderr
from copy import deepcopy
from functools import wraps
from re import sub as re_sub, compile as re_compile
from collections import namedtuple
from shlex import split as shlex_split
from inspect import signature, Parameter
from tempfile import mkstemp as make_temp_file
from argparse import ArgumentParser, SUPPRESS
from webbrowser import open as open_in_browser
from urllib.parse import urlparse, urlunparse, parse_qsl
from logging import (
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
    FATAL,
    getLogger,
    getLevelName,
)

from lxml.etree import XPath
from orjson import loads as json_loads, JSONDecodeError

from ._shell_signatures import Signatures_map
from scrapling import __version__
from scrapling.core.utils import log
from scrapling.parser import Selector, Selectors
from scrapling.core.custom_types import TextHandler
from scrapling.engines.toolbelt.custom import Response
from scrapling.core.utils._shell import _ParseHeaders, _CookieParser
from scrapling.core._types import (
    Callable,
    Dict,
    Any,
    cast,
    Optional,
    Generator,
    extraction_types,
)


_known_logging_levels = {
    "debug": DEBUG,
    "info": INFO,
    "warning": WARNING,
    "error": ERROR,
    "critical": CRITICAL,
    "fatal": FATAL,
}


# Define the structure for parsed context - Simplified for Fetcher args
Request = namedtuple(
    "Request",
    [
        "method",
        "url",
        "params",
        "data",  # Can be str, bytes, or dict (for urlencoded)
        "json_data",  # Python object (dict/list) for JSON payload
        "headers",
        "cookies",
        "proxy",
        "follow_redirects",  # Added for -L flag
    ],
)

# Precompiled for the prompt injection sanitizer
_HIDDEN_XPATH = XPath(
    './/*[contains(@style,"display:none") or contains(@style,"display: none")'
    ' or contains(@style,"visibility:hidden") or contains(@style,"visibility: hidden")'
    ' or contains(@style,"opacity:0") or contains(@style,"opacity: 0")'
    ' or contains(@style,"font-size:0") or contains(@style,"font-size: 0")'
    ' or contains(@style,"height:0") or contains(@style,"height: 0")'
    ' or contains(@style,"width:0") or contains(@style,"width: 0")]'
    " | .//*[@aria-hidden='true']"
    " | .//template"
)
_ZWC_PATTERN = re_compile(r"[\u200b\u200c\u200d\ufeff\u2060\u180e]")


# Suppress exit on error to handle parsing errors gracefully
class NoExitArgumentParser(ArgumentParser):  # pragma: no cover
    def error(self, message):
        pass

    def exit(self, status=0, message=None):
        pass


class CurlParser:
    """Builds the argument parser for relevant curl flags from DevTools."""

    def __init__(self) -> None:
        from scrapling.fetchers import Fetcher as __Fetcher

        self.__fetcher = __Fetcher
        # We will use argparse parser to parse the curl command directly instead of regex
        # We will focus more on flags that will show up on curl commands copied from DevTools's network tab
        _parser = NoExitArgumentParser(add_help=False)  # Disable default help
        # Basic curl arguments
        _parser.add_argument("curl_command_placeholder", nargs="?", help=SUPPRESS)
        _parser.add_argument("url")
        _parser.add_argument("-X", "--request", dest="method", default=None)
        _parser.add_argument("-H", "--header", action="append", default=[])
        _parser.add_argument(
            "-A", "--user-agent", help="Will be parsed from -H if present"
        )  # Note: DevTools usually includes this in -H

        # Data arguments (prioritizing types common from DevTools)
        _parser.add_argument("-d", "--data", default=None)
        _parser.add_argument("--data-raw", default=None)  # Often used by browsers for JSON body
        _parser.add_argument("--data-binary", default=None)
        # Keep urlencode for completeness, though less common from browser copy/paste
        _parser.add_argument("--data-urlencode", action="append", default=[])
        _parser.add_argument("-G", "--get", action="store_true")  # Use GET and put data in URL

        _parser.add_argument(
            "-b",
            "--cookie",
            default=None,
            help="Send cookies from string/file (string format used by DevTools)",
        )

        # Proxy
        _parser.add_argument("-x", "--proxy", default=None)
        _parser.add_argument("-U", "--proxy-user", default=None)  # Basic proxy auth

        # Connection/Security
        _parser.add_argument("-k", "--insecure", action="store_true")
        _parser.add_argument("--compressed", action="store_true")  # Very common from browsers

        # Other flags often included but may not map directly to request args
        _parser.add_argument("-i", "--include", action="store_true")
        _parser.add_argument("-s", "--silent", action="store_true")
        _parser.add_argument("-v", "--verbose", action="store_true")

        self.parser: NoExitArgumentParser = _parser
        self._supported_methods = ("get", "post", "put", "delete")

    # --- Main Parsing Logic ---
    def parse(self, curl_command: str) -> Optional[Request]:
        """Parses the curl command string into a structured context for Fetcher."""
        pass

    def convert2fetcher(self, curl_command: Request | str) -> Optional[Response]:
        pass


def _unpack_signature(func, signature_name=None):
    """
    Unpack TypedDict from Unpack[TypedDict] annotations in **kwargs and reconstruct the signature.

    This allows the interactive shell to show individual parameters instead of just **kwargs, similar to how IDEs display them.
    """
    pass


def show_page_in_browser(page: Selector):  # pragma: no cover
    pass


class CustomShell:
    """A custom IPython shell with minimal dependencies"""

    def __init__(self, code, log_level="debug"):
        from IPython.terminal.embed import InteractiveShellEmbed as __InteractiveShellEmbed
        from scrapling.fetchers import (
            Fetcher as __Fetcher,
            AsyncFetcher as __AsyncFetcher,
            FetcherSession as __FetcherSession,
            DynamicFetcher as __DynamicFetcher,
            DynamicSession as __DynamicSession,
            AsyncDynamicSession as __AsyncDynamicSession,
            StealthyFetcher as __StealthyFetcher,
            StealthySession as __StealthySession,
            AsyncStealthySession as __AsyncStealthySession,
        )

        self.__InteractiveShellEmbed = __InteractiveShellEmbed
        self.__Fetcher = __Fetcher
        self.__AsyncFetcher = __AsyncFetcher
        self.__FetcherSession = __FetcherSession
        self.__DynamicFetcher = __DynamicFetcher
        self.__DynamicSession = __DynamicSession
        self.__AsyncDynamicSession = __AsyncDynamicSession
        self.__StealthyFetcher = __StealthyFetcher
        self.__StealthySession = __StealthySession
        self.__AsyncStealthySession = __AsyncStealthySession
        self.code = code
        self.page = None
        self.pages = Selectors([])
        self._curl_parser = CurlParser()
        log_level = log_level.strip().lower()

        if _known_logging_levels.get(log_level):
            self.log_level = _known_logging_levels[log_level]
        else:  # pragma: no cover
            log.warning(f'Unknown log level "{log_level}", defaulting to "DEBUG"')
            self.log_level = DEBUG

        self.shell = None

        # Initialize your application components
        self.init_components()

    def init_components(self):
        """Initialize application components"""
        pass

    @staticmethod
    def banner():
        """Create a custom banner for the shell"""
        pass

    def update_page(self, result):  # pragma: no cover
        """Update the current page and add to pages history"""
        pass

    def create_wrapper(
        self, func: Callable, get_signature: bool = True, signature_name: Optional[str] = None
    ) -> Callable:
        """Create a wrapper that preserves function signature but updates page"""
        pass

    def get_namespace(self):
        """Create a namespace with application-specific objects"""
        pass

    def show_help(self):  # pragma: no cover
        """Show help information"""
        pass

    def start(self):  # pragma: no cover
        """Start the interactive shell"""
        pass


class Convertor:
    """Utils for the extract shell command"""

    _extension_map: Dict[str, extraction_types] = {
        "md": "markdown",
        "html": "html",
        "txt": "text",
    }

    @classmethod
    def _convert_to_markdown(cls, body: TextHandler) -> str:
        """Convert HTML content to Markdown"""
        pass

    @classmethod
    def _strip_noise_tags(cls, page: Selector) -> Selector:
        """Return a copy of the Selector with noise tags removed."""
        pass

    @classmethod
    def _sanitize_for_ai(cls, page: Selector) -> Selector:
        """Strip hidden content that could be used for prompt injection.

        Removes CSS-hidden elements, aria-hidden elements, <template> tags,
        HTML comments, and zero-width Unicode characters.
        """
        pass

    @classmethod
    def _extract_content(
        cls,
        page: Selector,
        extraction_type: extraction_types = "markdown",
        css_selector: Optional[str] = None,
        main_content_only: bool = False,
    ) -> Generator[str, None, None]:
        """Extract the content of a Selector"""
        pass

    @classmethod
    def write_content_to_file(
        cls, page: Selector, filename: str, css_selector: Optional[str] = None, main_content_only: bool = False
    ) -> None:
        """Write a Selector's content to a file"""
        pass
