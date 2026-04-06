from functools import lru_cache
from re import compile as re_compile

from curl_cffi.requests import Response as CurlResponse
from playwright._impl._errors import Error as PlaywrightError
from playwright.sync_api import Page as SyncPage, Response as SyncResponse
from playwright.async_api import Page as AsyncPage, Response as AsyncResponse

from scrapling.core.utils import log
from .custom import Response, StatusText
from scrapling.core._types import Dict, List, Optional

__CHARSET_RE__ = re_compile(r"charset=([\w-]+)")


class ResponseFactory:
    """
    Factory class for creating `Response` objects from various sources.

    This class provides multiple static and instance methods for building standardized `Response` objects
    from diverse input sources such as Playwright responses, asynchronous Playwright responses,
    and raw HTTP request responses. It supports handling response histories, constructing the proper
    response objects, and managing encoding, headers, cookies, and other attributes.
    """

    @classmethod
    @lru_cache(maxsize=16)
    def __extract_browser_encoding(cls, content_type: str | None, default: str = "utf-8") -> str:
        """Extract browser encoding from headers.
        Ex: from header "content-type: text/html; charset=utf-8" -> "utf-8
        """
        pass

    @classmethod
    def _process_response_history(cls, first_response: SyncResponse, parser_arguments: Dict) -> list[Response]:
        """Process response history to build a list of `Response` objects"""
        pass

    @classmethod
    def from_playwright_response(
        cls,
        page: Optional[SyncPage],
        first_response: SyncResponse,
        final_response: Optional[SyncResponse],
        parser_arguments: Dict,
        meta: Optional[Dict] = None,
        xhr_captured: Optional[List[SyncResponse]] = None,
        collect_history: bool = True,
    ) -> Response:
        """
        Transforms a Playwright response into an internal `Response` object, encapsulating
        the page's content, response status, headers, and relevant metadata.

        The function handles potential issues, such as empty or missing final responses,
        by falling back to the first response if necessary. Encoding and status text
        are also derived from the provided response headers or reasonable defaults.
        Additionally, the page content and cookies are extracted for further use.

        :param page: A synchronous Playwright `Page` instance that represents the current browser page. Required to retrieve the page's URL, cookies, and content.
        :param final_response: The last response received for the given request from the Playwright instance. Typically used as the main response object to derive status, headers, and other metadata.
        :param first_response: An earlier or initial Playwright `Response` object that may serve as a fallback response in the absence of the final one.
        :param parser_arguments: A dictionary containing additional arguments needed for parsing or further customization of the returned `Response`. These arguments are dynamically unpacked into
            the `Response` object.
        :param meta: Additional meta data to be saved with the response.
        :param xhr_captured: Optional list of captured Playwright XHR/fetch responses to convert and attach to the returned Response.
        :param collect_history: Optional boolean indicating whether to collect redirections history or not.
        :return: A fully populated `Response` object containing the page's URL, content, status, headers, cookies, and other derived metadata.
        :rtype: Response
        """
        pass

    @classmethod
    async def _async_process_response_history(
        cls, first_response: AsyncResponse, parser_arguments: Dict
    ) -> list[Response]:
        """Process response history to build a list of `Response` objects"""
        pass

    @classmethod
    def _get_page_content(cls, page: SyncPage, max_retries: int = 20) -> str:
        """
        A workaround for the Playwright issue with `page.content()` on Windows. Ref.: https://github.com/microsoft/playwright/issues/16108
        :param page: The page to extract content from.
        :param max_retries: Maximum number of retry attempts before raising `RuntimeError`.
        :return:
        """
        pass

    @classmethod
    async def _get_async_page_content(cls, page: AsyncPage, max_retries: int = 20) -> str:
        """
        A workaround for the Playwright issue with `page.content()` on Windows. Ref.: https://github.com/microsoft/playwright/issues/16108
        :param page: The page to extract content from.
        :param max_retries: Maximum number of retry attempts before raising `RuntimeError`.
        :return:
        """
        pass

    @classmethod
    async def from_async_playwright_response(
        cls,
        page: Optional[AsyncPage],
        first_response: AsyncResponse,
        final_response: Optional[AsyncResponse],
        parser_arguments: Dict,
        meta: Optional[Dict] = None,
        xhr_captured: Optional[List[AsyncResponse]] = None,
        collect_history: bool = True,
    ) -> Response:
        """
        Transforms a Playwright response into an internal `Response` object, encapsulating
        the page's content, response status, headers, and relevant metadata.

        The function handles potential issues, such as empty or missing final responses,
        by falling back to the first response if necessary. Encoding and status text
        are also derived from the provided response headers or reasonable defaults.
        Additionally, the page content and cookies are extracted for further use.

        :param page: An asynchronous Playwright `Page` instance that represents the current browser page. Required to retrieve the page's URL, cookies, and content.
        :param final_response: The last response received for the given request from the Playwright instance. Typically used as the main response object to derive status, headers, and other metadata.
        :param first_response: An earlier or initial Playwright `Response` object that may serve as a fallback response in the absence of the final one.
        :param parser_arguments: A dictionary containing additional arguments needed for parsing or further customization of the returned `Response`. These arguments are dynamically unpacked into
            the `Response` object.
        :param meta: Additional meta data to be saved with the response.
        :param xhr_captured: Optional list of captured async Playwright XHR/fetch responses to convert and attach to the returned Response.
        :param collect_history: Optional boolean indicating whether to collect redirections history or not.

        :return: A fully populated `Response` object containing the page's URL, content, status, headers, cookies, and other derived metadata.
        :rtype: Response
        """
        pass

    @staticmethod
    def from_http_request(response: CurlResponse, parser_arguments: Dict, meta: Optional[Dict] = None) -> Response:
        """Takes `curl_cffi` response and generates `Response` object from it.

        :param response: `curl_cffi` response object
        :param parser_arguments: Additional arguments to be passed to the `Response` object constructor.
        :param meta: Optional metadata dictionary to attach to the Response.
        :return: A `Response` object that is the same as `Selector` object except it has these added attributes: `status`, `reason`, `cookies`, `headers`, and `request_headers`
        """
        return Response(
            **{
                "url": response.url,
                "content": response.content,
                "status": response.status_code,
                "reason": response.reason,
                "encoding": response.encoding or "utf-8",
                "cookies": dict(response.cookies),
                "headers": dict(response.headers),
                "request_headers": dict(response.request.headers) if response.request else {},
                "method": response.request.method if response.request else "GET",
                "history": response.history,  # https://github.com/lexiforest/curl_cffi/issues/82
                "meta": meta,
                **parser_arguments,
            }
        )
