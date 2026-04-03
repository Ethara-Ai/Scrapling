from pathlib import Path
from inspect import signature
from urllib.parse import urljoin
from difflib import SequenceMatcher
from re import Pattern as re_Pattern

from lxml.html import HtmlElement, HTMLParser
from cssselect import SelectorError, SelectorSyntaxError, parse as split_selectors
from lxml.etree import (
    XPath,
    tostring,
    fromstring,
    XPathError,
    XPathEvalError,
    _ElementUnicodeResult,
)

from scrapling.core._types import (
    Any,
    Set,
    Dict,
    cast,
    List,
    Tuple,
    Union,
    TypeVar,
    Pattern,
    Callable,
    Literal,
    Optional,
    Iterable,
    overload,
    Generator,
    SupportsIndex,
    TYPE_CHECKING,
)
from scrapling.core.custom_types import AttributesHandler, TextHandler, TextHandlers
from scrapling.core.mixins import SelectorsGeneration
from scrapling.core.storage import (
    SQLiteStorageSystem,
    StorageSystemMixin,
    _StorageTools,
)
from scrapling.core.translator import css_to_xpath as _css_to_xpath
from scrapling.core.utils import clean_spaces, flatten, html_forbidden, log

__DEFAULT_DB_FILE__ = str(Path(__file__).parent / "elements_storage.db")
# Attributes that are Python reserved words and can't be used directly
# Ex: find_all('a', class="blah") -> find_all('a', class_="blah")
# https://www.w3schools.com/python/python_ref_keywords.asp
_whitelisted = {
    "class_": "class",
    "for_": "for",
}
_T = TypeVar("_T")
# Pre-compiled selectors for efficiency
_find_all_elements = XPath(".//*")
_find_all_elements_with_spaces = XPath(
    ".//*[normalize-space(text())]"
)  # This selector gets all elements with text content
_find_all_text_nodes = XPath(".//text()")


class Selector(SelectorsGeneration):
    __slots__ = (
        "url",
        "encoding",
        "__adaptive_enabled",
        "_root",
        "_storage",
        "__keep_comments",
        "__huge_tree_enabled",
        "__attributes",
        "__text",
        "__tag",
        "__keep_cdata",
        "_raw_body",
    )

    def __init__(
        self,
        content: Optional[str | bytes] = None,
        url: str = "",
        encoding: str = "utf-8",
        huge_tree: bool = True,
        root: Optional[HtmlElement] = None,
        keep_comments: Optional[bool] = False,
        keep_cdata: Optional[bool] = False,
        adaptive: Optional[bool] = False,
        _storage: Optional[StorageSystemMixin] = None,
        storage: Any = SQLiteStorageSystem,
        storage_args: Optional[Dict] = None,
        **_,
    ):
        """The main class that works as a wrapper for the HTML input data. Using this class, you can search for elements
        with expressions in CSS, XPath, or with simply text. Check the docs for more info.

        Here we try to extend module ``lxml.html.HtmlElement`` while maintaining a simpler interface, We are not
        inheriting from the ``lxml.html.HtmlElement`` because it's not pickleable, which makes a lot of reference jobs
        not possible. You can test it here and see code explodes with `AssertionError: invalid Element proxy at...`.
        It's an old issue with lxml, see `this entry <https://bugs.launchpad.net/lxml/+bug/736708>`

        :param content: HTML content as either string or bytes.
        :param url: It allows storing a URL with the HTML data for retrieving later.
        :param encoding: The encoding type that will be used in HTML parsing, default is `UTF-8`
        :param huge_tree: Enabled by default, should always be enabled when parsing large HTML documents. This controls
             the libxml2 feature that forbids parsing certain large documents to protect from possible memory exhaustion.
        :param root: Used internally to pass etree objects instead of text/body arguments, it takes the highest priority.
            Don't use it unless you know what you are doing!
        :param keep_comments: While parsing the HTML body, drop comments or not. Disabled by default for obvious reasons
        :param keep_cdata: While parsing the HTML body, drop cdata or not. Disabled by default for cleaner HTML.
        :param adaptive: Globally turn off the adaptive feature in all functions, this argument takes higher
            priority over all adaptive related arguments/functions in the class.
        :param storage: The storage class to be passed for adaptive functionalities, see ``Docs`` for more info.
        :param storage_args: A dictionary of ``argument->value`` pairs to be passed for the storage class.
            If empty, default values will be used.
        """
        if root is None and content is None:
            raise ValueError("Selector class needs HTML content, or root arguments to work")

        self.url = url
        self._raw_body: str | bytes = ""
        self.encoding = encoding
        self.__keep_cdata = keep_cdata
        self.__huge_tree_enabled = huge_tree
        self.__keep_comments = keep_comments
        # For selector stuff
        self.__text: Optional[TextHandler] = None
        self.__attributes: Optional[AttributesHandler] = None
        self.__tag: Optional[str] = None
        self._storage: Optional[StorageSystemMixin] = None
        if root is None:
            body: str | bytes
            if isinstance(content, str):
                body = content.strip().replace("\x00", "") or "<html/>"
            elif isinstance(content, bytes):
                body = content.replace(b"\x00", b"")
            else:
                raise TypeError(f"content argument must be str or bytes, got {type(content)}")

            # https://lxml.de/api/lxml.etree.HTMLParser-class.html
            _parser_kwargs: Dict[str, Any] = dict(
                recover=True,
                remove_blank_text=True,
                remove_comments=(not keep_comments),
                encoding=encoding,
                compact=True,
                huge_tree=huge_tree,
                default_doctype=True,  # Supported by lxml but missing from stubs
                strip_cdata=(not keep_cdata),
            )
            parser = HTMLParser(**_parser_kwargs)
            self._root = cast(HtmlElement, fromstring(body or "<html/>", parser=parser, base_url=url or ""))
            self._raw_body = content

        else:
            self._root = cast(HtmlElement, root)

            if self._is_text_node(root):
                self.__adaptive_enabled = False
                return

        self.__adaptive_enabled = bool(adaptive)

        if self.__adaptive_enabled:
            if _storage is not None:
                self._storage = _storage
            else:
                if not storage_args:
                    storage_args = {
                        "storage_file": __DEFAULT_DB_FILE__,
                        "url": url,
                    }

                if not hasattr(storage, "__wrapped__"):
                    raise ValueError("Storage class must be wrapped with lru_cache decorator, see docs for info")

                if not issubclass(storage.__wrapped__, StorageSystemMixin):  # pragma: no cover
                    raise ValueError("Storage system must be inherited from class `StorageSystemMixin`")

                self._storage = storage(**storage_args)

    def __getitem__(self, key: str) -> TextHandler:
        if self._is_text_node(self._root):
            raise TypeError("Text nodes do not have attributes")
        return self.attrib[key]

    def __contains__(self, key: str) -> bool:
        if self._is_text_node(self._root):
            return False
        return key in self.attrib

    # Node functionalities, I wanted to move to a separate Mixin class, but it had a slight impact on performance
    @staticmethod
    def _is_text_node(
        element: HtmlElement | _ElementUnicodeResult,
    ) -> bool:
        """Return True if the given element is a result of a string expression
        Examples:
            XPath -> '/text()', '/@attribute', etc...
            CSS3 -> '::text', '::attr(attrib)'...
        """
        pass

    def __element_convertor(self, element: HtmlElement | _ElementUnicodeResult) -> "Selector":
        """Used internally to convert a single HtmlElement or text node to Selector directly without checks"""
        pass

    def __elements_convertor(self, elements: List[HtmlElement | _ElementUnicodeResult]) -> "Selectors":
        # Store them for non-repeated call-ups
        pass

    def __handle_elements(self, result: List[HtmlElement | _ElementUnicodeResult]) -> "Selectors":
        """Used internally in all functions to convert results to Selectors in bulk"""
        pass

    def __getstate__(self) -> Any:
        # lxml don't like it :)
        raise TypeError("Can't pickle Selector objects")

    # The following four properties I made them into functions instead of variables directly
    # So they don't slow down the process of initializing many instances of the class and gets executed only
    # when the user needs them for the first time for that specific element and gets cached for next times
    # Doing that only made the library performance test sky rocked multiple times faster than before
    # because I was executing them on initialization before :))
    @property
    def tag(self) -> str:
        """Get the tag name of the element"""
        pass

    @property
    def text(self) -> TextHandler:
        """Get text content of the element"""
        pass

    def get_all_text(
        self,
        separator: str = "\n",
        strip: bool = False,
        ignore_tags: Tuple = (
            "script",
            "style",
        ),
        valid_values: bool = True,
    ) -> TextHandler:
        """Get all child strings of this element, concatenated using the given separator.

        :param separator: Strings will be concatenated using this separator.
        :param strip: If True, strings will be stripped before being concatenated.
        :param ignore_tags: A tuple of all tag names you want to ignore
        :param valid_values: If enabled, elements with text-content that is empty or only whitespaces will be ignored

        :return: A TextHandler
        """
        pass

    def urljoin(self, relative_url: str) -> str:
        """Join this Selector's url with a relative url to form an absolute full URL."""
        pass

    @property
    def attrib(self) -> AttributesHandler:
        """Get attributes of the element"""
        pass

    @property
    def html_content(self) -> TextHandler:
        """Return the inner HTML code of the element"""
        pass

    @property
    def body(self) -> str | bytes:
        """Return the raw body of the current `Selector` without any processing. Useful for binary and non-HTML requests."""
        pass

    def prettify(self) -> TextHandler:
        """Return a prettified version of the element's inner html-code"""
        pass

    def has_class(self, class_name: str) -> bool:
        """Check if the element has a specific class
        :param class_name: The class name to check for
        :return: True if element has class with that name otherwise False
        """
        pass

    @property
    def parent(self) -> Optional["Selector"]:
        """Return the direct parent of the element or ``None`` otherwise"""
        pass

    @property
    def below_elements(self) -> "Selectors":
        """Return all elements under the current element in the DOM tree"""
        pass

    @property
    def children(self) -> "Selectors":
        """Return the children elements of the current element or empty list otherwise"""
        pass

    @property
    def siblings(self) -> "Selectors":
        """Return other children of the current element's parent or empty list otherwise"""
        pass

    def iterancestors(self) -> Generator["Selector", None, None]:
        """Return a generator that loops over all ancestors of the element, starting with the element's parent."""
        pass

    def find_ancestor(self, func: Callable[["Selector"], bool]) -> Optional["Selector"]:
        """Loop over all ancestors of the element till one match the passed function
        :param func: A function that takes each ancestor as an argument and returns True/False
        :return: The first ancestor that match the function or ``None`` otherwise.
        """
        pass

    @property
    def path(self) -> "Selectors":
        """Returns a list of type `Selectors` that contains the path leading to the current element from the root."""
        pass

    @property
    def next(self) -> Optional["Selector"]:
        """Returns the next element of the current element in the children of the parent or ``None`` otherwise."""
        pass

    @property
    def previous(self) -> Optional["Selector"]:
        """Returns the previous element of the current element in the children of the parent or ``None`` otherwise."""
        pass

    def get(self) -> TextHandler:
        """
        Serialize this element to a string.
        For text nodes, returns the text value. For HTML elements, returns the outer HTML.
        """
        if self._is_text_node(self._root):
            return TextHandler(str(self._root))
        return self.html_content

    def getall(self) -> TextHandlers:
        """Return a single-element list containing this element's serialized string."""
        pass

    extract = getall
    extract_first = get

    def __str__(self) -> str:
        if self._is_text_node(self._root):
            return str(self._root)
        return self.html_content

    def __repr__(self) -> str:
        length_limit = 40

        if self._is_text_node(self._root):
            text = str(self._root)
            if len(text) > length_limit:
                text = text[:length_limit].strip() + "..."
            return f"<text='{text}'>"

        content = clean_spaces(self.html_content)
        if len(content) > length_limit:
            content = content[:length_limit].strip() + "..."
        data = f"<data='{content}'"

        if self.parent:
            parent_content = clean_spaces(self.parent.html_content)
            if len(parent_content) > length_limit:
                parent_content = parent_content[:length_limit].strip() + "..."

            data += f" parent='{parent_content}'"

        return data + ">"

    # From here we start with the selecting functions
    @overload
    def relocate(
        self, element: Union[Dict, HtmlElement, "Selector"], percentage: int, selector_type: Literal[True]
    ) -> "Selectors": ...

    @overload
    def relocate(
        self, element: Union[Dict, HtmlElement, "Selector"], percentage: int, selector_type: Literal[False] = False
    ) -> List[HtmlElement]: ...

    def relocate(
        self,
        element: Union[Dict, HtmlElement, "Selector"],
        percentage: int = 0,
        selector_type: bool = False,
    ) -> Union[List[HtmlElement], "Selectors"]:
        """This function will search again for the element in the page tree, used automatically on page structure change

        :param element: The element we want to relocate in the tree
        :param percentage: The minimum percentage to accept and not going lower than that. Be aware that the percentage
         calculation depends solely on the page structure, so don't play with this number unless you must know
         what you are doing!
        :param selector_type: If True, the return result will be converted to `Selectors` object
        :return: List of pure HTML elements that got the highest matching score or 'Selectors' object
        """
        pass

    def css(
        self,
        selector: str,
        identifier: str = "",
        adaptive: bool = False,
        auto_save: bool = False,
        percentage: int = 0,
    ) -> "Selectors":
        """Search the current tree with CSS3 selectors

        **Important:
        It's recommended to use the identifier argument if you plan to use a different selector later
        and want to relocate the same element(s)**

        :param selector: The CSS3 selector to be used.
        :param adaptive: Enabled will make the function try to relocate the element if it was 'saved' before
        :param identifier: A string that will be used to save/retrieve element's data in adaptive,
         otherwise the selector will be used.
        :param auto_save: Automatically save new elements for `adaptive` later
        :param percentage: The minimum percentage to accept while `adaptive` is working and not going lower than that.
         Be aware that the percentage calculation depends solely on the page structure, so don't play with this
         number unless you must know what you are doing!

        :return: `Selectors` class.
        """
        pass

    def xpath(
        self,
        selector: str,
        identifier: str = "",
        adaptive: bool = False,
        auto_save: bool = False,
        percentage: int = 0,
        **kwargs: Any,
    ) -> "Selectors":
        """Search the current tree with XPath selectors

        **Important:
        It's recommended to use the identifier argument if you plan to use a different selector later
        and want to relocate the same element(s)**

         Note: **Additional keyword arguments will be passed as XPath variables in the XPath expression!**

        :param selector: The XPath selector to be used.
        :param adaptive: Enabled will make the function try to relocate the element if it was 'saved' before
        :param identifier: A string that will be used to save/retrieve element's data in adaptive,
         otherwise the selector will be used.
        :param auto_save: Automatically save new elements for `adaptive` later
        :param percentage: The minimum percentage to accept while `adaptive` is working and not going lower than that.
         Be aware that the percentage calculation depends solely on the page structure, so don't play with this
         number unless you must know what you are doing!

        :return: `Selectors` class.
        """
        pass

    def find_all(
        self,
        *args: str | Iterable[str] | Pattern | Callable | Dict[str, str],
        **kwargs: str,
    ) -> "Selectors":
        """Find elements by filters of your creations for ease.

        :param args: Tag name(s), iterable of tag names, regex patterns, function, or a dictionary of elements' attributes. Leave empty for selecting all.
        :param kwargs: The attributes you want to filter elements based on it.
        :return: The `Selectors` object of the elements or empty list
        """
        pass

    def find(
        self,
        *args: str | Iterable[str] | Pattern | Callable | Dict[str, str],
        **kwargs: str,
    ) -> Optional["Selector"]:
        """Find elements by filters of your creations for ease, then return the first result. Otherwise return `None`.

        :param args: Tag name(s), iterable of tag names, regex patterns, function, or a dictionary of elements' attributes. Leave empty for selecting all.
        :param kwargs: The attributes you want to filter elements based on it.
        :return: The `Selector` object of the element or `None` if the result didn't match
        """
        pass

    def __calculate_similarity_score(self, original: Dict, candidate: HtmlElement) -> float:
        """Used internally to calculate a score that shows how a candidate element similar to the original one

        :param original: The original element in the form of the dictionary generated from `element_to_dict` function
        :param candidate: The element to compare with the original element.
        :return: A percentage score of how similar is the candidate to the original element
        """
        pass

    @staticmethod
    def __calculate_dict_diff(dict1: Dict, dict2: Dict) -> float:
        """Used internally to calculate similarity between two dictionaries as SequenceMatcher doesn't accept dictionaries"""
        pass

    def save(self, element: HtmlElement, identifier: str) -> None:
        """Saves the element's unique properties to the storage for retrieval and relocation later

        :param element: The element itself that we want to save to storage, it can be a ` Selector ` or pure ` HtmlElement `
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

    # Operations on text functions
    def json(self) -> Dict:
        """Return JSON response if the response is jsonable otherwise throws error"""
        pass

    def re(
        self,
        regex: str | Pattern[str],
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> TextHandlers:
        """Apply the given regex to the current text and return a list of strings with the matches.

        :param regex: Can be either a compiled regular expression or a string.
        :param replace_entities: If enabled character entity references are replaced by their corresponding character
        :param clean_match: if enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: if disabled, the function will set the regex to ignore the letters case while compiling it
        """
        pass

    def re_first(
        self,
        regex: str | Pattern[str],
        default=None,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> TextHandler:
        """Apply the given regex to text and return the first match if found, otherwise return the default value.

        :param regex: Can be either a compiled regular expression or a string.
        :param default: The default value to be returned if there is no match
        :param replace_entities: if enabled character entity references are replaced by their corresponding character
        :param clean_match: if enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: if disabled, the function will set the regex to ignore the letters case while compiling it
        """
        pass

    @staticmethod
    def __get_attributes(element: HtmlElement, ignore_attributes: List | Tuple) -> Dict:
        """Return attributes dictionary without the ignored list"""
        pass

    def __are_alike(
        self,
        original: HtmlElement,
        original_attributes: Dict,
        candidate: HtmlElement,
        ignore_attributes: List | Tuple,
        similarity_threshold: float,
        match_text: bool = False,
    ) -> bool:
        """Calculate a score of how much these elements are alike and return True
        if the score is higher or equals the threshold"""
        pass

    def find_similar(
        self,
        similarity_threshold: float = 0.2,
        ignore_attributes: List | Tuple = (
            "href",
            "src",
        ),
        match_text: bool = False,
    ) -> "Selectors":
        """Find elements that are in the same tree depth in the page with the same tag name and same parent tag etc...
        then return the ones that match the current element attributes with a percentage higher than the input threshold.

        This function is inspired by AutoScraper and made for cases where you, for example, found a product div inside
        a products-list container and want to find other products using that element as a starting point EXCEPT
        this function works in any case without depending on the element type.

        :param similarity_threshold: The percentage to use while comparing element attributes.
            Note: Elements found before attributes matching/comparison will be sharing the same depth, same tag name,
            same parent tag name, and same grand parent tag name. So they are 99% likely to be correct unless you are
            extremely unlucky, then attributes matching comes into play, so don't play with this number unless
            you are getting the results you don't want.
            Also, if the current element doesn't have attributes and the similar element as well, then it's a 100% match.
        :param ignore_attributes: Attribute names passed will be ignored while matching the attributes in the last step.
            The default value is to ignore `href` and `src` as URLs can change a lot between elements, so it's unreliable
        :param match_text: If True, element text content will be taken into calculation while matching.
            Not recommended to use in normal cases, but it depends.

        :return: A ``Selectors`` container of ``Selector`` objects or empty list
        """
        pass

    @overload
    def find_by_text(
        self,
        text: str,
        first_match: Literal[True] = ...,
        partial: bool = ...,
        case_sensitive: bool = ...,
        clean_match: bool = ...,
    ) -> "Selector": ...

    @overload
    def find_by_text(
        self,
        text: str,
        first_match: Literal[False],
        partial: bool = ...,
        case_sensitive: bool = ...,
        clean_match: bool = ...,
    ) -> "Selectors": ...

    def find_by_text(
        self,
        text: str,
        first_match: bool = True,
        partial: bool = False,
        case_sensitive: bool = False,
        clean_match: bool = True,
    ) -> Union["Selectors", "Selector"]:
        """Find elements that its text content fully/partially matches input.
        :param text: Text query to match
        :param first_match: Returns the first element that matches conditions, enabled by default
        :param partial: If enabled, the function returns elements that contain the input text
        :param case_sensitive: if enabled, the letters case will be taken into consideration
        :param clean_match: if enabled, this will ignore all whitespaces and consecutive spaces while matching
        """
        pass

    @overload
    def find_by_regex(
        self,
        query: str | Pattern[str],
        first_match: Literal[True] = ...,
        case_sensitive: bool = ...,
        clean_match: bool = ...,
    ) -> "Selector": ...

    @overload
    def find_by_regex(
        self,
        query: str | Pattern[str],
        first_match: Literal[False],
        case_sensitive: bool = ...,
        clean_match: bool = ...,
    ) -> "Selectors": ...

    def find_by_regex(
        self,
        query: str | Pattern[str],
        first_match: bool = True,
        case_sensitive: bool = False,
        clean_match: bool = True,
    ) -> Union["Selectors", "Selector"]:
        """Find elements that its text content matches the input regex pattern.
        :param query: Regex query/pattern to match
        :param first_match: Return the first element that matches conditions; enabled by default.
        :param case_sensitive: If enabled, the letters case will be taken into consideration in the regex.
        :param clean_match: If enabled, this will ignore all whitespaces and consecutive spaces while matching.
        """
        pass


class Selectors(List[Selector]):
    """
    The `Selectors` class is a subclass of the builtin ``List`` class, which provides a few additional methods.
    """

    __slots__ = ()

    @overload
    def __getitem__(self, pos: SupportsIndex) -> Selector:
        pass

    @overload
    def __getitem__(self, pos: slice) -> "Selectors":
        pass

    def __getitem__(self, pos: SupportsIndex | slice) -> Union[Selector, "Selectors"]:
        lst = super().__getitem__(pos)
        if isinstance(pos, slice):
            return self.__class__(cast(List[Selector], lst))
        else:
            return cast(Selector, lst)

    def xpath(
        self,
        selector: str,
        identifier: str = "",
        auto_save: bool = False,
        percentage: int = 0,
        **kwargs: Any,
    ) -> "Selectors":
        """
        Call the ``.xpath()`` method for each element in this list and return
        their results as another `Selectors` class.

        **Important:
        It's recommended to use the identifier argument if you plan to use a different selector later
        and want to relocate the same element(s)**

         Note: **Additional keyword arguments will be passed as XPath variables in the XPath expression!**

        :param selector: The XPath selector to be used.
        :param identifier: A string that will be used to retrieve element's data in adaptive,
         otherwise the selector will be used.
        :param auto_save: Automatically save new elements for `adaptive` later
        :param percentage: The minimum percentage to accept while `adaptive` is working and not going lower than that.
         Be aware that the percentage calculation depends solely on the page structure, so don't play with this
         number unless you must know what you are doing!

        :return: `Selectors` class.
        """
        pass

    def css(
        self,
        selector: str,
        identifier: str = "",
        auto_save: bool = False,
        percentage: int = 0,
    ) -> "Selectors":
        """
        Call the ``.css()`` method for each element in this list and return
        their results flattened as another `Selectors` class.

        **Important:
        It's recommended to use the identifier argument if you plan to use a different selector later
        and want to relocate the same element(s)**

        :param selector: The CSS3 selector to be used.
        :param identifier: A string that will be used to retrieve element's data in adaptive,
         otherwise the selector will be used.
        :param auto_save: Automatically save new elements for `adaptive` later
        :param percentage: The minimum percentage to accept while `adaptive` is working and not going lower than that.
         Be aware that the percentage calculation depends solely on the page structure, so don't play with this
         number unless you must know what you are doing!

        :return: `Selectors` class.
        """
        pass

    def re(
        self,
        regex: str | Pattern,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> TextHandlers:
        """Call the ``.re()`` method for each element in this list and return
        their results flattened as List of TextHandler.

        :param regex: Can be either a compiled regular expression or a string.
        :param replace_entities: If enabled character entity references are replaced by their corresponding character
        :param clean_match: if enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: if disabled, the function will set the regex to ignore the letters case while compiling it
        """
        pass

    def re_first(
        self,
        regex: str | Pattern,
        default: Any = None,
        replace_entities: bool = True,
        clean_match: bool = False,
        case_sensitive: bool = True,
    ) -> TextHandler:
        """Call the ``.re_first()`` method for each element in this list and return
        the first result or the default value otherwise.

        :param regex: Can be either a compiled regular expression or a string.
        :param default: The default value to be returned if there is no match
        :param replace_entities: if enabled character entity references are replaced by their corresponding character
        :param clean_match: if enabled, this will ignore all whitespaces and consecutive spaces while matching
        :param case_sensitive: if disabled, function will set the regex to ignore the letters case while compiling it
        """
        pass

    def search(self, func: Callable[["Selector"], bool]) -> Optional["Selector"]:
        """Loop over all current elements and return the first element that matches the passed function
        :param func: A function that takes each element as an argument and returns True/False
        :return: The first element that match the function or ``None`` otherwise.
        """
        pass

    def filter(self, func: Callable[["Selector"], bool]) -> "Selectors":
        """Filter current elements based on the passed function
        :param func: A function that takes each element as an argument and returns True/False
        :return: The new `Selectors` object or empty list otherwise.
        """
        pass

    @overload
    def get(self) -> Optional[TextHandler]: ...

    @overload
    def get(self, default: _T) -> Union[TextHandler, _T]: ...

    def get(self, default=None):
        """Returns the serialized string of the first element, or ``default`` if empty.
        :param default: the default value to return if the current list is empty
        """
        for x in self:
            return x.get()
        return default

    def getall(self) -> TextHandlers:
        """Serialize all elements and return as a TextHandlers list."""
        pass

    extract = getall
    extract_first = get

    @property
    def first(self) -> Optional[Selector]:
        """Returns the first Selector item of the current list or `None` if the list is empty"""
        pass

    @property
    def last(self) -> Optional[Selector]:
        """Returns the last Selector item of the current list or `None` if the list is empty"""
        pass

    @property
    def length(self) -> int:
        """Returns the length of the current list"""
        pass

    def __getstate__(self) -> Any:  # pragma: no cover
        # lxml don't like it :)
        raise TypeError("Can't pickle Selectors object")


# For backward compatibility
Adaptor = Selector
Adaptors = Selectors
