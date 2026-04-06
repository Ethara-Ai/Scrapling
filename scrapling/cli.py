from pathlib import Path
from subprocess import check_output
from sys import executable as python_executable

from scrapling.core.utils import log
from scrapling.engines.toolbelt.custom import Response
from scrapling.core.utils._shell import _CookieParser, _ParseHeaders
from scrapling.core._types import List, Optional, Dict, Tuple, Any, Callable

from orjson import loads as json_loads, JSONDecodeError

try:
    from click import command, option, Choice, group, argument
except (ImportError, ModuleNotFoundError) as e:
    raise ModuleNotFoundError(
        "You need to install scrapling with any of the extras to enable Shell commands. See: https://scrapling.readthedocs.io/en/latest/#installation"
    ) from e

__OUTPUT_FILE_HELP__ = "The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively."
__PACKAGE_DIR__ = Path(__file__).parent


def __Execute(cmd: List[str], help_line: str) -> None:  # pragma: no cover
    pass
    # I meant to not use try except here


def __ParseJSONData(json_string: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Parse JSON string into a Python object"""
    if not json_string:
        return None

    try:
        return json_loads(json_string)
    except JSONDecodeError as err:  # pragma: no cover
        raise ValueError(f"Invalid JSON data '{json_string}': {err}")


def __Request_and_Save(
    fetcher_func: Callable[..., Response],
    url: str,
    output_file: str,
    css_selector: Optional[str] = None,
    ai_targeted: bool = False,
    **kwargs,
) -> None:
    """Make a request using the specified fetcher function and save the result"""
    from scrapling.core.shell import Convertor

    # Handle relative paths - convert to an absolute path based on the current working directory
    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_file

    response = fetcher_func(url, **kwargs)
    Convertor.write_content_to_file(response, str(output_path), css_selector, main_content_only=ai_targeted)
    log.info(f"Content successfully saved to '{output_path}'")


def __ParseExtractArguments(
    headers: List[str], cookies: str, params: str, json: Optional[str] = None
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], Optional[Dict[str, str]]]:
    """Parse arguments for extract command"""
    parsed_headers, parsed_cookies = _ParseHeaders(headers)
    if cookies:
        for key, value in _CookieParser(cookies):
            try:
                parsed_cookies[key] = value
            except Exception as err:
                raise ValueError(f"Could not parse cookies '{cookies}': {err}")

    parsed_json = __ParseJSONData(json)
    parsed_params = {}
    for param in params:
        if "=" in param:
            key, value = param.split("=", 1)
            parsed_params[key] = value

    return parsed_headers, parsed_cookies, parsed_params, parsed_json


def __BuildRequest(headers: List[str], cookies: str, params: str, json: Optional[str] = None, **kwargs) -> Dict:
    """Build a request object using the specified arguments"""
    # Parse parameters
    parsed_headers, parsed_cookies, parsed_params, parsed_json = __ParseExtractArguments(headers, cookies, params, json)
    # Build request arguments
    request_kwargs: Dict[str, Any] = {
        "headers": parsed_headers if parsed_headers else None,
        "cookies": parsed_cookies if parsed_cookies else None,
    }
    if parsed_json:
        request_kwargs["json"] = parsed_json
    if parsed_params:
        request_kwargs["params"] = parsed_params
    if "proxy" in kwargs:
        request_kwargs["proxy"] = kwargs.pop("proxy")

    # Parse impersonate parameter if it contains commas (for random selection)
    if "impersonate" in kwargs and "," in (kwargs.get("impersonate") or ""):
        kwargs["impersonate"] = [browser.strip() for browser in kwargs["impersonate"].split(",")]

    return {**request_kwargs, **kwargs}


@command(help="Install all Scrapling's Fetchers dependencies")
@option(
    "-f",
    "--force",
    "force",
    is_flag=True,
    default=False,
    type=bool,
    help="Force Scrapling to reinstall all Fetchers dependencies",
)
def install(force):  # pragma: no cover
    pass


@command(help="Run Scrapling's MCP server (Check the docs for more info).")
@option(
    "--http",
    is_flag=True,
    default=False,
    help="Whether to run the MCP server in streamable-http transport or leave it as stdio (Default: False)",
)
@option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="The host to use if streamable-http transport is enabled (Default: '0.0.0.0')",
)
@option(
    "--port", type=int, default=8000, help="The port to use if streamable-http transport is enabled (Default: 8000)"
)
def mcp(http, host, port):
    pass


@command(help="Interactive scraping console")
@option(
    "-c",
    "--code",
    "code",
    is_flag=False,
    default="",
    type=str,
    help="Evaluate the code in the shell, print the result and exit",
)
@option(
    "-L",
    "--loglevel",
    "level",
    is_flag=False,
    default="debug",
    type=Choice(["debug", "info", "warning", "error", "critical", "fatal"], case_sensitive=False),
    help="Log level (default: DEBUG)",
)
def shell(code, level):
    pass


@group(
    help="Fetch web pages using various fetchers and extract full/selected HTML content as HTML, Markdown, or extract text content."
)
def extract():
    """Extract content from web pages and save to files"""
    pass


####
# Shared Click option decorator factories
####


def _common_http_options(f):
    """Apply shared Click options for all HTTP extract commands (get/post/put/delete)."""
    pass


def _common_browser_options(f):
    """Apply shared Click options for browser-based commands (fetch/stealthy_fetch)."""
    pass


def _data_options(f):
    """Apply data/json options for POST and PUT commands."""
    pass


def __http_command(
    method_name: str, url: str, output_file: str, css_selector: Optional[str], ai_targeted: bool = False, **kwargs
) -> None:
    """Shared implementation for HTTP extract commands."""
    from scrapling.fetchers import Fetcher

    __Request_and_Save(getattr(Fetcher, method_name), url, output_file, css_selector, ai_targeted=ai_targeted, **kwargs)


@extract.command(help=f"Perform a GET request and save the content to a file.\n\n{__OUTPUT_FILE_HELP__}")
@argument("url", required=True)
@argument("output_file", required=True)
@_common_http_options
def get(
    url,
    output_file,
    headers,
    cookies,
    timeout,
    proxy,
    css_selector,
    params,
    follow_redirects,
    verify,
    impersonate,
    stealthy_headers,
    ai_targeted,
):
    """Perform a GET request and save the content to a file."""
    kwargs = __BuildRequest(
        headers,
        cookies,
        params,
        None,
        timeout=timeout,
        follow_redirects=follow_redirects,
        verify=verify,
        stealthy_headers=stealthy_headers,
        impersonate=impersonate,
        proxy=proxy,
    )
    __http_command("get", url, output_file, css_selector, ai_targeted=ai_targeted, **kwargs)


@extract.command(help=f"Perform a POST request and save the content to a file.\n\n{__OUTPUT_FILE_HELP__}")
@argument("url", required=True)
@argument("output_file", required=True)
@_data_options
@_common_http_options
def post(
    url,
    output_file,
    data,
    json,
    headers,
    cookies,
    timeout,
    proxy,
    css_selector,
    params,
    follow_redirects,
    verify,
    impersonate,
    stealthy_headers,
    ai_targeted,
):
    """Perform a POST request and save the content to a file."""
    pass


@extract.command(help=f"Perform a PUT request and save the content to a file.\n\n{__OUTPUT_FILE_HELP__}")
@argument("url", required=True)
@argument("output_file", required=True)
@_data_options
@_common_http_options
def put(
    url,
    output_file,
    data,
    json,
    headers,
    cookies,
    timeout,
    proxy,
    css_selector,
    params,
    follow_redirects,
    verify,
    impersonate,
    stealthy_headers,
    ai_targeted,
):
    """Perform a PUT request and save the content to a file."""
    pass


@extract.command(help=f"Perform a DELETE request and save the content to a file.\n\n{__OUTPUT_FILE_HELP__}")
@argument("url", required=True)
@argument("output_file", required=True)
@_common_http_options
def delete(
    url,
    output_file,
    headers,
    cookies,
    timeout,
    proxy,
    css_selector,
    params,
    follow_redirects,
    verify,
    impersonate,
    stealthy_headers,
    ai_targeted,
):
    """Perform a DELETE request and save the content to a file."""
    pass


def __build_browser_kwargs(
    headless,
    disable_resources,
    network_idle,
    timeout,
    wait,
    wait_selector,
    locale,
    real_chrome,
    proxy,
    parsed_headers,
) -> Dict[str, Any]:
    """Build shared kwargs dict for browser-based commands."""
    pass


@extract.command(help=f"Use DynamicFetcher to fetch content with browser automation.\n\n{__OUTPUT_FILE_HELP__}")
@argument("url", required=True)
@argument("output_file", required=True)
@_common_browser_options
def fetch(
    url,
    output_file,
    headless,
    disable_resources,
    network_idle,
    timeout,
    wait,
    css_selector,
    wait_selector,
    locale,
    real_chrome,
    proxy,
    extra_headers,
    ai_targeted,
):
    """Opens up a browser and fetch content using DynamicFetcher."""
    pass


@extract.command(help=f"Use StealthyFetcher to fetch content with advanced stealth features.\n\n{__OUTPUT_FILE_HELP__}")
@argument("url", required=True)
@argument("output_file", required=True)
@option(
    "--block-webrtc/--allow-webrtc",
    default=False,
    help="Block WebRTC entirely (default: False)",
)
@option(
    "--solve-cloudflare/--no-solve-cloudflare",
    default=False,
    help="Solve Cloudflare challenges (default: False)",
)
@option("--allow-webgl/--block-webgl", default=True, help="Allow WebGL (default: True)")
@option(
    "--hide-canvas/--show-canvas",
    default=False,
    help="Add noise to canvas operations (default: False)",
)
@_common_browser_options
def stealthy_fetch(
    url,
    output_file,
    headless,
    disable_resources,
    network_idle,
    timeout,
    wait,
    css_selector,
    wait_selector,
    locale,
    real_chrome,
    proxy,
    extra_headers,
    block_webrtc,
    solve_cloudflare,
    allow_webgl,
    hide_canvas,
    ai_targeted,
):
    """Opens up a browser with advanced stealth features and fetch content using StealthyFetcher."""
    pass


@group()
def main():
    pass


# Adding commands
main.add_command(install)
main.add_command(shell)
main.add_command(extract)
main.add_command(mcp)
