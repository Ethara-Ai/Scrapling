"""
Most of this file is an adapted version of the parsel library's translator with some modifications simply for 1 important reason...

To add pseudo-elements ``::text`` and ``::attr(ATTR_NAME)`` so we match the Parsel/Scrapy selectors format which will be important in future releases but most importantly...

So you don't have to learn a new selectors/api method like what bs4 done with soupsieve :)

    If you want to learn about this, head to https://cssselect.readthedocs.io/en/latest/#cssselect.FunctionalPseudoElement
"""

from functools import lru_cache

from cssselect import HTMLTranslator as OriginalHTMLTranslator
from cssselect.xpath import ExpressionError, XPathExpr as OriginalXPathExpr
from cssselect.parser import Element, FunctionalPseudoElement, PseudoElement

from scrapling.core._types import Any, Protocol, Self


class XPathExpr(OriginalXPathExpr):
    textnode: bool = False
    attribute: str | None = None

    @classmethod
    def from_xpath(
        cls,
        xpath: OriginalXPathExpr,
        textnode: bool = False,
        attribute: str | None = None,
    ) -> Self:
        pass

    def __str__(self) -> str:
        path = super().__str__()
        if self.textnode:
            if path == "*":  # pragma: no cover
                path = "text()"
            elif path.endswith("::*/*"):  # pragma: no cover
                path = path[:-3] + "text()"
            else:
                path += "/text()"

        if self.attribute is not None:
            if path.endswith("::*/*"):  # pragma: no cover
                path = path[:-2]
            path += f"/@{self.attribute}"

        return path

    def join(
        self: Self,
        combiner: str,
        other: OriginalXPathExpr,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        if not isinstance(other, XPathExpr):
            raise ValueError(  # pragma: no cover
                f"Expressions of type {__name__}.XPathExpr can ony join expressions"
                f" of the same type (or its descendants), got {type(other)}"
            )
        super().join(combiner, other, *args, **kwargs)
        self.textnode = other.textnode
        self.attribute = other.attribute
        return self


# e.g. cssselect.GenericTranslator, cssselect.HTMLTranslator
class TranslatorProtocol(Protocol):
    def xpath_element(self, selector: Element) -> OriginalXPathExpr:  # pyright: ignore # pragma: no cover
        pass

    def css_to_xpath(self, css: str, prefix: str = ...) -> str:  # pyright: ignore # pragma: no cover
        pass


class TranslatorMixin:
    """This mixin adds support to CSS pseudo elements via dynamic dispatch.

    Currently supported pseudo-elements are ``::text`` and ``::attr(ATTR_NAME)``.
    """

    def xpath_element(self: TranslatorProtocol, selector: Element) -> XPathExpr:
        # https://github.com/python/mypy/issues/14757
        pass

    def xpath_pseudo_element(self, xpath: OriginalXPathExpr, pseudo_element: PseudoElement) -> OriginalXPathExpr:
        """
        Dispatch method that transforms XPath to support the pseudo-element.
        """
        pass

    @staticmethod
    def xpath_attr_functional_pseudo_element(xpath: OriginalXPathExpr, function: FunctionalPseudoElement) -> XPathExpr:
        """Support selecting attribute values using ::attr() pseudo-element"""
        pass

    @staticmethod
    def xpath_text_simple_pseudo_element(xpath: OriginalXPathExpr) -> XPathExpr:
        """Support selecting text nodes using ::text pseudo-element"""
        pass


class HTMLTranslator(TranslatorMixin, OriginalHTMLTranslator):
    def css_to_xpath(self, css: str, prefix: str = "descendant-or-self::") -> str:
        pass


translator = HTMLTranslator()
# Using a function instead of the translator directly to avoid Pyright override error


@lru_cache(maxsize=256)
def css_to_xpath(query: str) -> str:
    """Return the translated XPath version of a given CSS query"""
    pass
