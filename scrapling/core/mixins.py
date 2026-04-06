from scrapling.core._types import Any, Dict


class SelectorsGeneration:
    """
    Functions for generating selectors
    Trying to generate selectors like Firefox or maybe cleaner ones!? Ehm
    Inspiration: https://searchfox.org/mozilla-central/source/devtools/shared/inspector/css-logic.js#591
    """

    # Note: This is a mixin class meant to be used with Selector.
    # The methods access Selector attributes (._root, .parent, .attrib, .tag, etc.)
    # through self, which will be a Selector instance at runtime.

    def _general_selection(self: Any, selection: str = "css", full_path: bool = False) -> str:
        """Generate a selector for the current element.
        :return: A string of the generated selector.
        """
        pass

    @property
    def generate_css_selector(self: Any) -> str:
        """Generate a CSS selector for the current element
        :return: A string of the generated selector.
        """
        pass

    @property
    def generate_full_css_selector(self: Any) -> str:
        """Generate a complete CSS selector for the current element
        :return: A string of the generated selector.
        """
        pass

    @property
    def generate_xpath_selector(self: Any) -> str:
        """Generate an XPath selector for the current element
        :return: A string of the generated selector.
        """
        pass

    @property
    def generate_full_xpath_selector(self: Any) -> str:
        """Generate a complete XPath selector for the current element
        :return: A string of the generated selector.
        """
        pass
