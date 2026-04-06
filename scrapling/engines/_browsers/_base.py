from time import time
from re import search as re_search
from asyncio import sleep as asyncio_sleep, Lock
from contextlib import contextmanager, asynccontextmanager

from playwright.sync_api._generated import Page
from playwright.sync_api import (
    Frame,
    BrowserContext,
    Response as SyncPlaywrightResponse,
)
from playwright.async_api._generated import Page as AsyncPage
from playwright.async_api import (
    Frame as AsyncFrame,
    Response as AsyncPlaywrightResponse,
    BrowserContext as AsyncBrowserContext,
)
from playwright._impl._errors import Error as PlaywrightError

from scrapling.parser import Selector
from scrapling.engines._browsers._page import PageInfo, PagePool
from scrapling.engines._browsers._validators import validate, PlaywrightConfig, StealthConfig
from scrapling.engines._browsers._config_tools import __default_chrome_useragent__, __default_useragent__
from scrapling.engines.toolbelt.navigation import (
    construct_proxy_dict,
    create_intercept_handler,
    create_async_intercept_handler,
)
from scrapling.core._types import (
    Any,
    Awaitable,
    Dict,
    List,
    Set,
    Optional,
    Callable,
    TYPE_CHECKING,
    cast,
    overload,
    Tuple,
    ProxyType,
    Generator,
    AsyncGenerator,
)
from scrapling.engines.constants import STEALTH_ARGS, HARMFUL_ARGS, DEFAULT_ARGS


class SyncSession:
    _config: "PlaywrightConfig | StealthConfig"
    _context_options: Dict[str, Any]

    def _build_context_with_proxy(self, proxy: Optional[ProxyType] = None) -> Dict[str, Any]:
        raise NotImplementedError  # pragma: no cover

    def __init__(self, max_pages: int = 1):
        self.max_pages = max_pages
        self.page_pool = PagePool(max_pages)
        self._max_wait_for_page = 60
        self.playwright: Any = None
        self.context: Any = None
        self.browser: Any = None
        self._is_alive = False

    def start(self) -> None:
        pass

    def close(self):  # pragma: no cover
        """Close all resources"""
        if not self._is_alive:
            return

        if self.context:
            self.context.close()
            self.context = None

        if self.browser:
            self.browser.close()
            self.browser = None

        if self.playwright:
            self.playwright.stop()
            self.playwright = None  # pyright: ignore

        self._is_alive = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _initialize_context(self, config: PlaywrightConfig | StealthConfig, ctx: BrowserContext) -> BrowserContext:
        """Initialize the browser context."""
        pass

    def _get_page(
        self,
        timeout: int | float,
        extra_headers: Optional[Dict[str, str]],
        disable_resources: bool,
        blocked_domains: Optional[Set[str]] = None,
        context: Optional[BrowserContext] = None,
    ) -> PageInfo[Page]:  # pragma: no cover
        """Get a new page to use"""
        pass

    def get_pool_stats(self) -> Dict[str, int]:
        """Get statistics about the current page pool"""
        pass

    @staticmethod
    def _wait_for_networkidle(page: Page | Frame, timeout: Optional[int] = None):
        """Wait for the page to become idle (no network activity) even if there are never-ending requests."""
        pass

    def _wait_for_page_stability(self, page: Page | Frame, load_dom: bool, network_idle: bool):
        pass

    @staticmethod
    def _create_response_handler(
        page_info: PageInfo[Page],
        response_container: List,
        xhr_pattern: Optional[str] = None,
        xhr_container: Optional[List] = None,
    ) -> Callable[[SyncPlaywrightResponse], None]:
        """Create a response handler that captures the final navigation response and optionally XHR/fetch responses.

        :param page_info: The PageInfo object containing the page
        :param response_container: A list to store the final response (mutable container)
        :param xhr_pattern: Optional regex pattern to match XHR/fetch response URLs
        :param xhr_container: Optional list to store captured XHR/fetch responses
        :return: A callback function for page.on("response", ...)
        """
        pass

    @contextmanager
    def _page_generator(
        self,
        timeout: int | float,
        extra_headers: Optional[Dict[str, str]],
        disable_resources: bool,
        proxy: Optional[ProxyType] = None,
        blocked_domains: Optional[Set[str]] = None,
    ) -> Generator["PageInfo[Page]", None, None]:
        """Acquire a page - either from persistent context or fresh context with proxy."""
        pass


class AsyncSession:
    _config: "PlaywrightConfig | StealthConfig"
    _context_options: Dict[str, Any]

    def _build_context_with_proxy(self, proxy: Optional[ProxyType] = None) -> Dict[str, Any]:
        raise NotImplementedError  # pragma: no cover

    def __init__(self, max_pages: int = 1):
        self.max_pages = max_pages
        self.page_pool = PagePool(max_pages)
        self._max_wait_for_page = 60
        self.playwright: Any = None
        self.context: Any = None
        self.browser: Any = None
        self._is_alive = False
        self._lock = Lock()

    async def start(self) -> None:
        pass

    async def close(self):
        """Close all resources"""
        if not self._is_alive:  # pragma: no cover
            return

        if self.context:
            await self.context.close()
            self.context = None  # pyright: ignore

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None  # pyright: ignore

        self._is_alive = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _initialize_context(
        self, config: PlaywrightConfig | StealthConfig, ctx: AsyncBrowserContext
    ) -> AsyncBrowserContext:
        """Initialize the browser context."""
        pass

    async def _get_page(
        self,
        timeout: int | float,
        extra_headers: Optional[Dict[str, str]],
        disable_resources: bool,
        blocked_domains: Optional[Set[str]] = None,
        context: Optional[AsyncBrowserContext] = None,
    ) -> PageInfo[AsyncPage]:  # pragma: no cover
        """Get a new page to use"""
        pass

    def get_pool_stats(self) -> Dict[str, int]:
        """Get statistics about the current page pool"""
        pass

    @staticmethod
    async def _wait_for_networkidle(page: AsyncPage | AsyncFrame, timeout: Optional[int] = None):
        """Wait for the page to become idle (no network activity) even if there are never-ending requests."""
        pass

    async def _wait_for_page_stability(self, page: AsyncPage | AsyncFrame, load_dom: bool, network_idle: bool):
        pass

    @staticmethod
    def _create_response_handler(
        page_info: PageInfo[AsyncPage],
        response_container: List,
        xhr_pattern: Optional[str] = None,
        xhr_container: Optional[List] = None,
    ) -> Callable[[AsyncPlaywrightResponse], Awaitable[None]]:
        """Create an async response handler that captures the final navigation response and optionally XHR/fetch responses.

        :param page_info: The PageInfo object containing the page
        :param response_container: A list to store the final response (mutable container)
        :param xhr_pattern: Optional regex pattern to match XHR/fetch response URLs
        :param xhr_container: Optional list to store captured XHR/fetch responses
        :return: A callback function for page.on("response", ...)
        """
        pass

    @asynccontextmanager
    async def _page_generator(
        self,
        timeout: int | float,
        extra_headers: Optional[Dict[str, str]],
        disable_resources: bool,
        proxy: Optional[ProxyType] = None,
        blocked_domains: Optional[Set[str]] = None,
    ) -> AsyncGenerator["PageInfo[AsyncPage]", None]:
        """Acquire a page - either from persistent context or fresh context with proxy."""
        pass


class BaseSessionMixin:
    _config: "PlaywrightConfig | StealthConfig"

    @overload
    def __validate_routine__(self, params: Dict, model: type[StealthConfig]) -> StealthConfig: ...

    @overload
    def __validate_routine__(self, params: Dict, model: type[PlaywrightConfig]) -> PlaywrightConfig: ...

    def __validate_routine__(
        self, params: Dict, model: type[PlaywrightConfig] | type[StealthConfig]
    ) -> PlaywrightConfig | StealthConfig:
        # Dark color scheme bypasses the 'prefersLightColor' check in creepjs
        self._context_options: Dict[str, Any] = {"color_scheme": "dark", "device_scale_factor": 2}
        self._browser_options: Dict[str, Any] = {
            "args": DEFAULT_ARGS,
            "ignore_default_args": HARMFUL_ARGS,
        }
        if "__max_pages" in params:
            params["max_pages"] = params.pop("__max_pages")

        config = validate(params, model=model)
        self._headers_keys = (
            {header.lower() for header in config.extra_headers.keys()} if config.extra_headers else set()
        )

        return config

    def __generate_options__(self, extra_flags: Tuple | None = None) -> None:
        config: PlaywrightConfig | StealthConfig = self._config
        self._context_options.update(
            {
                "proxy": config.proxy,
                "locale": config.locale,
                "timezone_id": config.timezone_id,
                "extra_http_headers": config.extra_headers,
            }
        )
        # The default useragent in the headful is always correct now in the current versions of Playwright
        if config.useragent:
            self._context_options["user_agent"] = config.useragent
        elif not config.useragent and config.headless:
            self._context_options["user_agent"] = (
                __default_chrome_useragent__ if config.real_chrome else __default_useragent__
            )

        if not config.cdp_url:
            flags = self._browser_options["args"]
            if config.extra_flags or extra_flags:
                flags = list(set(tuple(flags) + tuple(config.extra_flags or extra_flags or ())))

            self._browser_options.update(
                {
                    "args": flags,
                    "headless": config.headless,
                    "channel": "chrome" if config.real_chrome else "chromium",
                }
            )
            if config.executable_path:
                self._browser_options["executable_path"] = config.executable_path

            self._user_data_dir = config.user_data_dir
        else:
            self._browser_options = {}

        if config.additional_args:
            self._context_options.update(config.additional_args)

    def _build_context_with_proxy(self, proxy: Optional[ProxyType] = None) -> Dict[str, Any]:
        """
        Build context options with a specific proxy for rotation mode.

        :param proxy: Proxy URL string or Playwright-style proxy dict to use for this context.
        :return: Dictionary of context options for browser.new_context().
        """
        pass


class DynamicSessionMixin(BaseSessionMixin):
    def __validate__(self, **params):
        self._config = self.__validate_routine__(params, model=PlaywrightConfig)
        self.__generate_options__()


class StealthySessionMixin(BaseSessionMixin):
    def __validate__(self, **params):
        self._config = self.__validate_routine__(params, model=StealthConfig)
        self._context_options.update(
            {
                "is_mobile": False,
                "has_touch": False,
                # I'm thinking about disabling it to rest from all Service Workers' headache, but let's keep it as it is for now
                "service_workers": "allow",
                "ignore_https_errors": True,
                "screen": {"width": 1920, "height": 1080},
                "viewport": {"width": 1920, "height": 1080},
                "permissions": ["geolocation", "notifications"],
            }
        )
        self.__generate_stealth_options()

    def __generate_stealth_options(self) -> None:
        pass

    @staticmethod
    def _detect_cloudflare(page_content: str) -> str | None:
        """
        Detect the type of Cloudflare challenge present in the provided page content.

        This function analyzes the given page content to identify whether a specific
        type of Cloudflare challenge is present. It checks for three predefined
        challenge types: non-interactive, managed, and interactive. If a challenge
        type is detected, it returns the corresponding type as a string. If no
        challenge type is detected, it returns None.

        Args:
            page_content (str): The content of the page to analyze for Cloudflare
                challenge types.

        Returns:
            str: A string representing the detected Cloudflare challenge type, if
                found. Returns None if no challenge matches.
        """
        pass
