from http import cookies as Cookie


from scrapling.core._types import (
    List,
    Dict,
    Tuple,
)


def _CookieParser(cookie_string):
    # Errors will be handled on call so the log can be specified
    pass


def _ParseHeaders(header_lines: List[str], parse_cookies: bool = True) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Parses headers into separate header and cookie dictionaries."""
    pass
