from collections.abc import Mapping
from types import MappingProxyType
from re import compile as re_compile, UNICODE, IGNORECASE

from orjson import dumps, loads
from w3lib.html import replace_entities as _replace_entities

from scrapling.core._types import (
    Any,
    cast,
    Dict,
    List,
    Union,
    overload,
    TypeVar,
    Literal,
    Pattern,
    Iterable,
    Generator,
    SupportsIndex,
)
from scrapling.core.utils import _is_iterable, flatten, __CONSECUTIVE_SPACES_REGEX__

# Define type variable for AttributeHandler value type
_TextHandlerType = TypeVar("_TextHandlerType", bound="TextHandler")
__CLEANING_TABLE__ = str.maketrans("\t\r\n", "   ")


class TextHandler(str):
    """Extends standard Python string by adding more functionality"""

    __slots__ = ()

    def __getitem__(self, key: SupportsIndex | slice) -> "TextHandler":  # pragma: no cover
        lst = super().__getitem__(key)
        return TextHandler(lst)

    def split(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list[Any]:  # pragma: no cover
        pass

    def strip(self, chars: str | None = None) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def lstrip(self, chars: str | None = None) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def rstrip(self, chars: str | None = None) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def capitalize(self) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def casefold(self) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def center(self, width: SupportsIndex, fillchar: str = " ") -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def expandtabs(self, tabsize: SupportsIndex = 8) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def format(self, *args: object, **kwargs: object) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def format_map(self, mapping) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def join(self, iterable: Iterable[str]) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def ljust(self, width: SupportsIndex, fillchar: str = " ") -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def rjust(self, width: SupportsIndex, fillchar: str = " ") -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def swapcase(self) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def title(self) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def translate(self, table) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def zfill(self, width: SupportsIndex) -> Union[str, "TextHandler"]:  # pragma: no cover
        pass

    def replace(self, old: str, new: str, count: SupportsIndex = -1) -> Union[str, "TextHandler"]:
        pass

    def upper(self) -> Union[str, "TextHandler"]:
        pass

    def lower(self) -> Union[str, "TextHandler"]:
        pass

    ##############

    def sort(self, reverse: bool = False) -> Union[str, "TextHandler"]:
        """Return a sorted version of the string"""
        pass

    def clean(self, remove_entities=False) -> Union[str, "TextHandler"]:
        """Return a new version of the string after removing all white spaces and consecutive spaces"""
        pass

    # For easy copy-paste from Scrapy/parsel code when needed :)
    def get(self, default=None):  # pragma: no cover
        return self

    def getall(self):  # pragma: no cover
        pass

    extract = getall
    extract_first = get

    def json(self) -> Dict:
        """Return JSON response if the response is jsonable otherwise throw error"""
        pass

    @overload
    def re(
        self,
        regex: str | Pattern,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
        *,
        check_match: Literal[True],
    ) -> bool: ...

    @overload
    def re(
        self,
        regex: str | Pattern,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
        check_match: Literal[False] = False,
    ) -> "TextHandlers": ...

    def re(
        self,
        regex: str | Pattern,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
        check_match: bool = False,
    ) -> Union["TextHandlers", bool]:
        """Apply the given regex to the current text and return a list of strings with the matches.

        :param regex: Can be either a compiled regular expression or a string.
        :param replace_entities: If enabled character entity references are replaced by their corresponding character
        :param clean_match: If enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: If disabled, function will set the regex to ignore the letters-case while compiling it
        :param check_match: Used to quickly check if this regex matches or not without any operations on the results

        """
        pass

    def re_first(
        self,
        regex: str | Pattern,
        default: Any = None,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> "TextHandler":
        """Apply the given regex to text and return the first match if found, otherwise return the default value.

        :param regex: Can be either a compiled regular expression or a string.
        :param default: The default value to be returned if there is no match
        :param replace_entities: If enabled character entity references are replaced by their corresponding character
        :param clean_match: If enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: If disabled, function will set the regex to ignore the letters-case while compiling it

        """
        pass


class TextHandlers(List[TextHandler]):
    """
    The :class:`TextHandlers` class is a subclass of the builtin ``List`` class, which provides a few additional methods.
    """

    __slots__ = ()

    @overload
    def __getitem__(self, pos: SupportsIndex) -> TextHandler:  # pragma: no cover
        pass

    @overload
    def __getitem__(self, pos: slice) -> "TextHandlers":  # pragma: no cover
        pass

    def __getitem__(self, pos: SupportsIndex | slice) -> Union[TextHandler, "TextHandlers"]:
        lst = super().__getitem__(pos)
        if isinstance(pos, slice):
            return TextHandlers(cast(List[TextHandler], lst))
        return TextHandler(cast(TextHandler, lst))

    def re(
        self,
        regex: str | Pattern,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> "TextHandlers":
        """Call the ``.re()`` method for each element in this list and return
        their results flattened as TextHandlers.

        :param regex: Can be either a compiled regular expression or a string.
        :param replace_entities: If enabled character entity references are replaced by their corresponding character
        :param clean_match: if enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: if disabled, the function will set the regex to ignore the letters-case while compiling it
        """
        pass

    def re_first(
        self,
        regex: str | Pattern,
        default: Any = None,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> TextHandler:  # pragma: no cover
        """Call the ``.re_first()`` method for each element in this list and return
        the first result or the default value otherwise.

        :param regex: Can be either a compiled regular expression or a string.
        :param default: The default value to be returned if there is no match
        :param replace_entities: If enabled character entity references are replaced by their corresponding character
        :param clean_match: If enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: If disabled, function will set the regex to ignore the letters-case while compiling it
        """
        pass

    # For easy copy-paste from Scrapy/parsel code when needed :)
    def get(self, default=None):
        """Returns the first item of the current list
        :param default: the default value to return if the current list is empty
        """
        return self[0] if len(self) > 0 else default

    def extract(self):
        pass

    extract_first = get
    getall = extract


class AttributesHandler(Mapping[str, _TextHandlerType]):
    """A read-only mapping to use instead of the standard dictionary for the speed boost, but at the same time I use it to add more functionalities.
    If the standard dictionary is needed, convert this class to a dictionary with the `dict` function
    """

    __slots__ = ("_data",)

    def __init__(self, mapping: Any = None, **kwargs: Any) -> None:
        mapping = (
            {key: TextHandler(value) if isinstance(value, str) else value for key, value in mapping.items()}
            if mapping is not None
            else {}
        )

        if kwargs:
            mapping.update(
                {key: TextHandler(value) if isinstance(value, str) else value for key, value in kwargs.items()}
            )

        # Fastest read-only mapping type
        self._data: Mapping[str, Any] = MappingProxyType(mapping)

    def get(self, key: str, default: Any = None) -> _TextHandlerType:
        """Acts like the standard dictionary `.get()` method"""
        return self._data.get(key, default)

    def search_values(self, keyword: str, partial: bool = False) -> Generator["AttributesHandler", None, None]:
        """Search current attributes by values and return a dictionary of each matching item
        :param keyword: The keyword to search for in the attribute values
        :param partial: If True, the function will search if keyword in each value instead of perfect match
        """
        pass

    @property
    def json_string(self) -> bytes:
        """Convert current attributes to JSON bytes if the attributes are JSON serializable otherwise throws error"""
        pass

    def __getitem__(self, key: str) -> _TextHandlerType:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"

    def __str__(self):
        return str(self._data)

    def __contains__(self, key):
        return key in self._data
