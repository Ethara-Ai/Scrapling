from random import randint
from re import compile as re_compile
from time import sleep as time_sleep
from asyncio import sleep as asyncio_sleep

from playwright.sync_api import Locator, Page
from playwright.async_api import Page as async_Page, Locator as AsyncLocator
from patchright.sync_api import sync_playwright
from patchright.async_api import async_playwright

from scrapling.core.utils import log
from scrapling.core._types import Any, List, Optional, ProxyType, Unpack
from scrapling.engines.toolbelt.proxy_rotation import is_proxy_error
from scrapling.engines.toolbelt.convertor import Response, ResponseFactory
from scrapling.engines._browsers._types import StealthSession, StealthFetchParams
from scrapling.engines._browsers._base import SyncSession, AsyncSession, StealthySessionMixin
from scrapling.engines._browsers._validators import validate_fetch as _validate, StealthConfig

__CF_PATTERN__ = re_compile(r"^https?://challenges\.cloudflare\.com/cdn-cgi/challenge-platform/.*")


class StealthySession(SyncSession, StealthySessionMixin):
    """A Stealthy Browser session manager with page pooling."""

    __slots__ = (
        "_config",
        "_context_options",
        "_browser_options",
        "_user_data_dir",
        "_headers_keys",
        "max_pages",
        "page_pool",
        "_max_wait_for_page",
        "playwright",
        "context",
    )

    def __init__(self, **kwargs: Unpack[StealthSession]):
        """A Browser session manager with page pooling, it's using a persistent browser Context by default with a temporary user profile directory.

        :param headless: Run the browser in headless/hidden (default), or headful/visible mode.
        :param disable_resources: Drop requests for unnecessary resources for a speed boost.
            Requests dropped are of type `font`, `image`, `media`, `beacon`, `object`, `imageset`, `texttrack`, `websocket`, `csp_report`, and `stylesheet`.
        :param blocked_domains: A set of domain names to block requests to. Subdomains are also matched (e.g., ``"example.com"`` blocks ``"sub.example.com"`` too).
        :param useragent: Pass a useragent string to be used. Otherwise the fetcher will generate a real Useragent of the same browser and use it.
        :param cookies: Set cookies for the next request.
        :param network_idle: Wait for the page until there are no network connections for at least 500 ms.
        :param timeout: The timeout in milliseconds that is used in all operations and waits through the page. The default is 30,000
        :param wait: The time (milliseconds) the fetcher will wait after everything finishes before closing the page and returning the ` Response ` object.
        :param page_action: Added for automation. A function that takes the `page` object and does the automation you need.
        :param wait_selector: Wait for a specific CSS selector to be in a specific state.
        :param init_script: An absolute path to a JavaScript file to be executed on page creation for all pages in this session.
        :param locale: Specify user locale, for example, `en-GB`, `de-DE`, etc. Locale will affect navigator.language value, Accept-Language request header value as well as number and date formatting
            rules. Defaults to the system default locale.
        :param timezone_id: Changes the timezone of the browser. Defaults to the system timezone.
        :param wait_selector_state: The state to wait for the selector given with `wait_selector`. The default state is `attached`.
        :param solve_cloudflare: Solves all types of the Cloudflare's Turnstile/Interstitial challenges before returning the response to you.
        :param real_chrome: If you have a Chrome browser installed on your device, enable this, and the Fetcher will launch an instance of your browser and use it.
        :param hide_canvas: Add random noise to canvas operations to prevent fingerprinting.
        :param block_webrtc: Forces WebRTC to respect proxy settings to prevent local IP address leak.
        :param allow_webgl: Enabled by default. Disabling it disables WebGL and WebGL 2.0 support entirely. Disabling WebGL is not recommended as many WAFs now check if WebGL is enabled.
        :param load_dom: Enabled by default, wait for all JavaScript on page(s) to fully load and execute.
        :param cdp_url: Instead of launching a new browser instance, connect to this CDP URL to control real browsers through CDP.
        :param google_search: Enabled by default, Scrapling will set a Google referer header.
        :param extra_headers: A dictionary of extra headers to add to the request. _The referer set by `google_search` takes priority over the referer set here if used together._
        :param proxy: The proxy to be used with requests, it can be a string or a dictionary with the keys 'server', 'username', and 'password' only.
        :param user_data_dir: Path to a User Data Directory, which stores browser session data like cookies and local storage. The default is to create a temporary directory.
        :param extra_flags: A list of additional browser flags to pass to the browser on launch.
        :param selector_config: The arguments that will be passed in the end while creating the final Selector's class.
        :param additional_args: Additional arguments to be passed to Playwright's context as additional settings, and it takes higher priority than Scrapling's settings.
        """
        self.__validate__(**kwargs)
        super().__init__()

    def start(self) -> None:
        """Create a browser for this instance and context."""
        pass

    def _cloudflare_solver(self, page: Page) -> None:  # pragma: no cover
        """Solve the cloudflare challenge displayed on the playwright page passed

        :param page: The targeted page
        :return:
        """
        pass

    def fetch(self, url: str, **kwargs: Unpack[StealthFetchParams]) -> Response:
        """Opens up the browser and do your request based on your chosen options.

        :param url: The Target url.
        :param google_search: Enabled by default, Scrapling will set a Google referer header.
        :param timeout: The timeout in milliseconds that is used in all operations and waits through the page. The default is 30,000
        :param wait: The time (milliseconds) the fetcher will wait after everything finishes before closing the page and returning the ` Response ` object.
        :param page_action: Added for automation. A function that takes the `page` object and does the automation you need.
        :param extra_headers: A dictionary of extra headers to add to the request. _The referer set by `google_search` takes priority over the referer set here if used together._
        :param disable_resources: Drop requests for unnecessary resources for a speed boost.
            Requests dropped are of type `font`, `image`, `media`, `beacon`, `object`, `imageset`, `texttrack`, `websocket`, `csp_report`, and `stylesheet`.
        :param blocked_domains: A set of domain names to block requests to. Subdomains are also matched (e.g., ``"example.com"`` blocks ``"sub.example.com"`` too).
        :param wait_selector: Wait for a specific CSS selector to be in a specific state.
        :param wait_selector_state: The state to wait for the selector given with `wait_selector`. The default state is `attached`.
        :param network_idle: Wait for the page until there are no network connections for at least 500 ms.
        :param load_dom: Enabled by default, wait for all JavaScript on page(s) to fully load and execute.
        :param solve_cloudflare: Solves all types of the Cloudflare's Turnstile/Interstitial challenges before returning the response to you.
        :param selector_config: The arguments that will be passed in the end while creating the final Selector's class.
        :param proxy: Static proxy to override rotator and session proxy. A new browser context will be created and used with it.
        :return: A `Response` object.
        """
        pass


class AsyncStealthySession(AsyncSession, StealthySessionMixin):
    """An async Stealthy Browser session manager with page pooling."""

    __slots__ = (
        "_config",
        "_context_options",
        "_browser_options",
        "_user_data_dir",
        "_headers_keys",
    )

    def __init__(self, **kwargs: Unpack[StealthSession]):
        """A Browser session manager with page pooling, it's using a persistent browser Context by default with a temporary user profile directory.

        :param headless: Run the browser in headless/hidden (default), or headful/visible mode.
        :param disable_resources: Drop requests for unnecessary resources for a speed boost.
            Requests dropped are of type `font`, `image`, `media`, `beacon`, `object`, `imageset`, `texttrack`, `websocket`, `csp_report`, and `stylesheet`.
        :param blocked_domains: A set of domain names to block requests to. Subdomains are also matched (e.g., ``"example.com"`` blocks ``"sub.example.com"`` too).
        :param useragent: Pass a useragent string to be used. Otherwise the fetcher will generate a real Useragent of the same browser and use it.
        :param cookies: Set cookies for the next request.
        :param network_idle: Wait for the page until there are no network connections for at least 500 ms.
        :param timeout: The timeout in milliseconds that is used in all operations and waits through the page. The default is 30,000
        :param wait: The time (milliseconds) the fetcher will wait after everything finishes before closing the page and returning the ` Response ` object.
        :param page_action: Added for automation. A function that takes the `page` object and does the automation you need.
        :param wait_selector: Wait for a specific CSS selector to be in a specific state.
        :param init_script: An absolute path to a JavaScript file to be executed on page creation for all pages in this session.
        :param locale: Specify user locale, for example, `en-GB`, `de-DE`, etc. Locale will affect navigator.language value, Accept-Language request header value as well as number and date formatting
            rules. Defaults to the system default locale.
        :param timezone_id: Changes the timezone of the browser. Defaults to the system timezone.
        :param wait_selector_state: The state to wait for the selector given with `wait_selector`. The default state is `attached`.
        :param solve_cloudflare: Solves all types of the Cloudflare's Turnstile/Interstitial challenges before returning the response to you.
        :param real_chrome: If you have a Chrome browser installed on your device, enable this, and the Fetcher will launch an instance of your browser and use it.
        :param hide_canvas: Add random noise to canvas operations to prevent fingerprinting.
        :param block_webrtc: Forces WebRTC to respect proxy settings to prevent local IP address leak.
        :param allow_webgl: Enabled by default. Disabling it disables WebGL and WebGL 2.0 support entirely. Disabling WebGL is not recommended as many WAFs now check if WebGL is enabled.
        :param load_dom: Enabled by default, wait for all JavaScript on page(s) to fully load and execute.
        :param cdp_url: Instead of launching a new browser instance, connect to this CDP URL to control real browsers through CDP.
        :param google_search: Enabled by default, Scrapling will set a Google referer header.
        :param extra_headers: A dictionary of extra headers to add to the request. _The referer set by `google_search` takes priority over the referer set here if used together._
        :param proxy: The proxy to be used with requests, it can be a string or a dictionary with the keys 'server', 'username', and 'password' only.
        :param user_data_dir: Path to a User Data Directory, which stores browser session data like cookies and local storage. The default is to create a temporary directory.
        :param extra_flags: A list of additional browser flags to pass to the browser on launch.
        :param selector_config: The arguments that will be passed in the end while creating the final Selector's class.
        :param additional_args: Additional arguments to be passed to Playwright's context as additional settings, and it takes higher priority than Scrapling's settings.
        """
        self.__validate__(**kwargs)
        super().__init__(max_pages=self._config.max_pages)

    async def start(self) -> None:
        """Create a browser for this instance and context."""
        pass

    async def _cloudflare_solver(self, page: async_Page) -> None:  # pragma: no cover
        """Solve the cloudflare challenge displayed on the playwright page passed

        :param page: The targeted page
        :return:
        """
        pass

    async def fetch(self, url: str, **kwargs: Unpack[StealthFetchParams]) -> Response:
        """Opens up the browser and do your request based on your chosen options.

        :param url: The Target url.
        :param google_search: Enabled by default, Scrapling will set a Google referer header.
        :param timeout: The timeout in milliseconds that is used in all operations and waits through the page. The default is 30,000
        :param wait: The time (milliseconds) the fetcher will wait after everything finishes before closing the page and returning the ` Response ` object.
        :param page_action: Added for automation. A function that takes the `page` object and does the automation you need.
        :param extra_headers: A dictionary of extra headers to add to the request. _The referer set by `google_search` takes priority over the referer set here if used together._
        :param disable_resources: Drop requests for unnecessary resources for a speed boost.
            Requests dropped are of type `font`, `image`, `media`, `beacon`, `object`, `imageset`, `texttrack`, `websocket`, `csp_report`, and `stylesheet`.
        :param blocked_domains: A set of domain names to block requests to. Subdomains are also matched (e.g., ``"example.com"`` blocks ``"sub.example.com"`` too).
        :param wait_selector: Wait for a specific CSS selector to be in a specific state.
        :param wait_selector_state: The state to wait for the selector given with `wait_selector`. The default state is `attached`.
        :param network_idle: Wait for the page until there are no network connections for at least 500 ms.
        :param load_dom: Enabled by default, wait for all JavaScript on page(s) to fully load and execute.
        :param solve_cloudflare: Solves all types of the Cloudflare's Turnstile/Interstitial challenges before returning the response to you.
        :param selector_config: The arguments that will be passed in the end while creating the final Selector's class.
        :param proxy: Static proxy to override rotator and session proxy. A new browser context will be created and used with it.
        :return: A `Response` object.
        """
        pass
