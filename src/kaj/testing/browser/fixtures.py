from __future__ import annotations

from kaj.testing.browser.model import (
    FailClick,
    NavigateClick,
    ReferenceBrowser,
    ReferenceElement,
    ReferencePage,
    RefreshClick,
)

HOME_PAGE = ReferencePage(
    key="home",
    url="https://fixture.test/home",
    title="Home",
    content_width=2000,
    content_height=3000,
    elements=(
        ReferenceElement("search", "textbox", "Search", text_entry=True),
        ReferenceElement(
            "search-btn",
            "button",
            "Search",
            click_action=NavigateClick("results"),
        ),
        ReferenceElement("fail-btn", "button", "Fail", click_action=FailClick("boom")),
        ReferenceElement(
            "refresh-btn",
            "button",
            "Load more",
            click_action=RefreshClick(("extra", "link", "Extra item")),
        ),
        ReferenceElement("disabled-btn", "button", "Disabled", enabled=False),
        ReferenceElement("hidden-btn", "button", "Hidden", visible=False),
    ),
)

RESULTS_PAGE = ReferencePage(
    key="results",
    url="https://fixture.test/results",
    title="Results",
    content_width=1800,
    content_height=2400,
    elements=(
        ReferenceElement(
            "product-a",
            "link",
            "Product A",
            click_action=NavigateClick("product"),
        ),
        ReferenceElement("product-b", "link", "Product B"),
    ),
)

PRODUCT_PAGE = ReferencePage(
    key="product",
    url="https://fixture.test/product",
    title="Product",
    content_width=1600,
    content_height=2000,
    elements=(ReferenceElement("buy", "button", "Buy"),),
)

PASSWORD_PAGE = ReferencePage(
    key="password",
    url="https://fixture.test/password",
    title="Password",
    content_width=1200,
    content_height=900,
    elements=(
        ReferenceElement(
            "password",
            "textbox",
            "Password",
            text_entry=True,
            sensitive=True,
        ),
    ),
)

SELECT_PAGE = ReferencePage(
    key="select",
    url="https://fixture.test/select",
    title="Select",
    content_width=1200,
    content_height=900,
    elements=(
        ReferenceElement(
            "country",
            "combobox",
            "Country",
            selectable=True,
            select_options=("ca", "us", "uk"),
        ),
    ),
)

PAGE_REGISTRY: dict[str, ReferencePage] = {
    page.key: page
    for page in (
        HOME_PAGE,
        RESULTS_PAGE,
        PRODUCT_PAGE,
        PASSWORD_PAGE,
        SELECT_PAGE,
    )
}

FIXTURE_URLS = {page.url: page.key for page in PAGE_REGISTRY.values()}
ASYNC_NAVIGATE_URL = "async:https://fixture.test/results"
INVALID_URL = "invalid:not-a-url"
UNKNOWN_URL = "unknown:https://fixture.test/missing"


def initialize_browser(browser: ReferenceBrowser, *, page_key: str = "home") -> None:
    browser.generation = 1
    load_page(browser, page_key, increment_generation=False)


def load_page(
    browser: ReferenceBrowser, page_key: str, *, increment_generation: bool = True
) -> None:
    page = PAGE_REGISTRY[page_key]
    if increment_generation:
        browser.generation += 1
    browser.current_page_key = page.key
    browser.scroll_x = 0
    browser.scroll_y = 0
    browser.elements = {element.key: element.clone() for element in page.elements}


def page_for_url(url: str) -> ReferencePage | None:
    if url == ASYNC_NAVIGATE_URL:
        return RESULTS_PAGE
    if url.startswith("invalid:") or url.startswith("unknown:"):
        return None
    page_key = FIXTURE_URLS.get(url)
    return None if page_key is None else PAGE_REGISTRY[page_key]
