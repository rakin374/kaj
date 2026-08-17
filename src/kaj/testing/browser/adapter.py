from __future__ import annotations

from kaj.capabilities import CapabilityIdentity
from kaj.runtime.capabilities import CapabilityAdapter, CapabilityAdapterResult, CapabilityRequestId
from kaj.runtime.values import KajNewtypeValue, RuntimeValue
from kaj.testing.browser.fixtures import (
    ASYNC_NAVIGATE_URL,
    INVALID_URL,
    PAGE_REGISTRY,
    UNKNOWN_URL,
    initialize_browser,
    load_page,
    page_for_url,
)
from kaj.testing.browser.model import (
    FailClick,
    NavigateClick,
    PendingCapabilityWork,
    ReferenceBrowser,
    ReferenceElement,
    RefreshClick,
)
from kaj.testing.browser.types import BrowserTypeCatalog

BROWSER_IDENTITY = CapabilityIdentity("std.capabilities.browser", "Browser", 1)
SUPPORTED_OPERATIONS = frozenset(
    {"observe", "navigate", "click", "type_text", "select", "scroll"}
)


class ReferenceBrowserAdapter(CapabilityAdapter):
    def __init__(self, browser: ReferenceBrowser, types: BrowserTypeCatalog) -> None:
        self._browser = browser
        self._types = types
        self.invocation_log: list[tuple[str, tuple[RuntimeValue, ...]]] = []

    @property
    def capability_identity(self) -> CapabilityIdentity:
        return BROWSER_IDENTITY

    @property
    def host_binding_id(self) -> str:
        return self._browser.host_binding_id

    @property
    def supported_operations(self) -> frozenset[str]:
        return SUPPORTED_OPERATIONS

    @property
    def browser(self) -> ReferenceBrowser:
        return self._browser

    def invoke(
        self,
        request_id: CapabilityRequestId,
        operation: str,
        arguments: tuple[RuntimeValue, ...],
    ) -> CapabilityAdapterResult:
        self.invocation_log.append((operation, arguments))
        if operation not in SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported browser operation '{operation}'.")
        if not self._browser.available:
            return CapabilityAdapterResult.immediate(
                self._types.err("unavailable")
            )
        if operation == "navigate" and self._string(arguments, 0) == ASYNC_NAVIGATE_URL:
            self._browser.pending_work[str(request_id)] = PendingCapabilityWork(
                operation, arguments
            )
            return CapabilityAdapterResult.pending()
        result = self._execute(operation, arguments)
        return CapabilityAdapterResult.immediate(result)

    def complete_pending(self, request_id: str) -> RuntimeValue:
        work = self._browser.pending_work.pop(request_id)
        return self._execute(work.operation, work.arguments)

    def _execute(self, operation: str, arguments: tuple[RuntimeValue, ...]) -> RuntimeValue:
        if operation == "observe":
            return self._observe()
        if operation == "navigate":
            return self._navigate(self._string(arguments, 0))
        if operation == "click":
            return self._click(self._string(arguments, 0), self._generation(arguments, 1))
        if operation == "type_text":
            return self._type_text(
                self._string(arguments, 0),
                self._generation(arguments, 1),
                self._string(arguments, 2),
            )
        if operation == "select":
            return self._select(
                self._string(arguments, 0),
                self._generation(arguments, 1),
                self._string(arguments, 2),
            )
        if operation == "scroll":
            return self._scroll(self._int(arguments, 0), self._int(arguments, 1))
        raise ValueError(f"Unsupported browser operation '{operation}'.")

    def _observe(self) -> RuntimeValue:
        page = PAGE_REGISTRY[self._browser.current_page_key]
        return self._types.ok(self._types.observation_for(self._browser))

    def _navigate(self, url: str) -> RuntimeValue:
        if url == INVALID_URL or url.startswith("invalid:"):
            return self._types.err("invalid_url")
        if url == UNKNOWN_URL or url.startswith("unknown:"):
            return self._types.err("navigation_failed", ("unknown destination",))
        page = page_for_url(url)
        if page is None:
            return self._types.err("navigation_failed", (url,))
        load_page(self._browser, page.key)
        return self._types.ok(self._types.observation_for(self._browser))

    def _click(self, element_id: str, generation: int) -> RuntimeValue:
        element, error = self._resolve_element(element_id, generation, clickable=True)
        if error is not None:
            return error
        assert element is not None
        action = element.click_action
        if isinstance(action, FailClick):
            return self._types.err("action_failed", (action.message,))
        if isinstance(action, NavigateClick):
            load_page(self._browser, action.page_key)
            return self._types.ok(self._types.observation_for(self._browser))
        if isinstance(action, RefreshClick):
            key, role, text = action.reveal
            self._browser.elements[key] = ReferenceElement(key, role, text)
            self._browser.generation += 1
            return self._types.ok(self._types.observation_for(self._browser))
        return self._types.ok(self._types.observation_for(self._browser))

    def _type_text(self, element_id: str, generation: int, text: str) -> RuntimeValue:
        element, error = self._resolve_element(element_id, generation, text_entry=True)
        if error is not None:
            return error
        assert element is not None
        element.typed_value = text
        return self._types.ok(self._types.observation_for(self._browser))

    def _select(self, element_id: str, generation: int, value: str) -> RuntimeValue:
        element, error = self._resolve_element(element_id, generation, selectable=True)
        if error is not None:
            return error
        assert element is not None
        if value not in element.select_options:
            return self._types.err("invalid_selection")
        element.selected_value = value
        return self._types.ok(self._types.observation_for(self._browser))

    def _scroll(self, delta_x: int, delta_y: int) -> RuntimeValue:
        page = PAGE_REGISTRY[self._browser.current_page_key]
        max_x = max(page.content_width - self._browser.viewport_width, 0)
        max_y = max(page.content_height - self._browser.viewport_height, 0)
        self._browser.scroll_x = min(max(self._browser.scroll_x + delta_x, 0), max_x)
        self._browser.scroll_y = min(max(self._browser.scroll_y + delta_y, 0), max_y)
        return self._types.ok(self._types.observation_for(self._browser))

    def _resolve_element(
        self,
        element_id: str,
        generation: int,
        *,
        clickable: bool = False,
        text_entry: bool = False,
        selectable: bool = False,
    ) -> tuple[ReferenceElement | None, RuntimeValue | None]:
        parsed = self._browser.parse_element_id(element_id)
        if parsed is None:
            return None, self._types.err("element_not_found")
        page_key, element_key, referenced_generation = parsed
        if referenced_generation != self._browser.generation:
            return None, self._types.err("stale_element")
        if page_key != self._browser.current_page_key:
            return None, self._types.err("stale_element")
        element = self._browser.elements.get(element_key)
        if element is None:
            return None, self._types.err("element_not_found")
        if not element.visible or not element.enabled:
            return None, self._types.err("element_not_interactable")
        if clickable and element.click_action is None and element.role not in {"button", "link"}:
            return None, self._types.err("element_not_interactable")
        if text_entry and not element.text_entry:
            return None, self._types.err("element_not_interactable")
        if selectable and not element.selectable:
            return None, self._types.err("element_not_interactable")
        return element, None

    @staticmethod
    def _string(arguments: tuple[RuntimeValue, ...], index: int) -> str:
        value = arguments[index]
        if isinstance(value, KajNewtypeValue) and isinstance(value.value, str):
            return value.value
        if isinstance(value, str):
            return value
        raise TypeError("Expected String argument.")

    @staticmethod
    def _int(arguments: tuple[RuntimeValue, ...], index: int) -> int:
        value = arguments[index]
        if type(value) is not int:
            raise TypeError("Expected Int argument.")
        return value

    @staticmethod
    def _generation(arguments: tuple[RuntimeValue, ...], index: int) -> int:
        value = arguments[index]
        if isinstance(value, KajNewtypeValue) and type(value.value) is int:
            return value.value
        if type(value) is int:
            return value
        raise TypeError("Expected PageGeneration argument.")
