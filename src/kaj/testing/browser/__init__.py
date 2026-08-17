from kaj.capabilities import CapabilityIdentity
from kaj.testing.browser.adapter import ReferenceBrowserAdapter
from kaj.testing.browser.fixtures import FIXTURE_URLS
from kaj.testing.browser.registry import ReferenceBrowserRegistry
from kaj.testing.browser.types import BrowserTypeCatalog, browser_type_catalog

BROWSER_IDENTITY = CapabilityIdentity("std.capabilities.browser", "Browser", 1)

__all__ = [
    "BROWSER_IDENTITY",
    "BrowserTypeCatalog",
    "FIXTURE_URLS",
    "ReferenceBrowserAdapter",
    "ReferenceBrowserRegistry",
    "browser_type_catalog",
]
