from __future__ import annotations

import json
from typing import Any

from kaj.capabilities import CapabilityIdentity, HostBindingId
from kaj.runtime.capabilities import CapabilityRegistry
from kaj.testing.browser.adapter import ReferenceBrowserAdapter
from kaj.testing.browser.fixtures import PAGE_REGISTRY, initialize_browser
from kaj.testing.browser.model import ReferenceBrowser, ReferenceElement
from kaj.testing.browser.types import BrowserTypeCatalog, browser_type_catalog

BROWSER_IDENTITY = CapabilityIdentity("std.capabilities.browser", "Browser", 1)


class ReferenceBrowserRegistry:
    def __init__(self, *, types: BrowserTypeCatalog | None = None) -> None:
        self._types = browser_type_catalog() if types is None else types
        self._browsers: dict[str, ReferenceBrowser] = {}

    @property
    def types(self) -> BrowserTypeCatalog:
        return self._types

    def create(self, binding_id: str, *, page_key: str = "home", available: bool = True) -> ReferenceBrowser:
        browser = ReferenceBrowser(host_binding_id=binding_id, available=available)
        initialize_browser(browser, page_key=page_key)
        self._browsers[binding_id] = browser
        return browser

    def get(self, binding_id: str) -> ReferenceBrowser | None:
        return self._browsers.get(binding_id)

    def require(self, binding_id: str) -> ReferenceBrowser:
        browser = self.get(binding_id)
        if browser is None:
            raise KeyError(f"Reference browser '{binding_id}' was not found.")
        return browser

    def adapter_for(self, binding_id: str) -> ReferenceBrowserAdapter:
        return ReferenceBrowserAdapter(self.require(binding_id), self._types)

    def register_with(self, registry: CapabilityRegistry) -> None:
        registry.register_factory(self._factory)

    def _factory(self, identity: CapabilityIdentity, host_binding_id: HostBindingId) -> ReferenceBrowserAdapter | None:
        if not identity.is_compatible_with(BROWSER_IDENTITY):
            return None
        browser = self.get(host_binding_id.value)
        if browser is None:
            return None
        return ReferenceBrowserAdapter(browser, self._types)

    def snapshot_state(self, binding_id: str) -> dict[str, Any]:
        browser = self.require(binding_id)
        return {
            "host_binding_id": browser.host_binding_id,
            "available": browser.available,
            "generation": browser.generation,
            "current_page_key": browser.current_page_key,
            "viewport_width": browser.viewport_width,
            "viewport_height": browser.viewport_height,
            "scroll_x": browser.scroll_x,
            "scroll_y": browser.scroll_y,
            "elements": {
                key: {
                    "key": element.key,
                    "role": element.role,
                    "text": element.text,
                    "enabled": element.enabled,
                    "visible": element.visible,
                    "text_entry": element.text_entry,
                    "selectable": element.selectable,
                    "select_options": list(element.select_options),
                    "sensitive": element.sensitive,
                    "typed_value": element.typed_value,
                    "selected_value": element.selected_value,
                }
                for key, element in browser.elements.items()
            },
        }

    def restore_state(self, state: dict[str, Any]) -> ReferenceBrowser:
        binding_id = str(state["host_binding_id"])
        browser = ReferenceBrowser(
            binding_id,
            bool(state["available"]),
            int(state["generation"]),
            str(state["current_page_key"]),
            int(state["viewport_width"]),
            int(state["viewport_height"]),
            int(state["scroll_x"]),
            int(state["scroll_y"]),
        )
        elements: dict[str, ReferenceElement] = {}
        raw_elements = state["elements"]
        if not isinstance(raw_elements, dict):
            raise ValueError("elements must be an object")
        for key, raw in raw_elements.items():
            if not isinstance(raw, dict):
                raise ValueError("element state must be an object")
            template_page = PAGE_REGISTRY.get(browser.current_page_key)
            base = None
            if template_page is not None:
                base = next((item for item in template_page.elements if item.key == key), None)
            click_action = None if base is None else base.click_action
            elements[key] = ReferenceElement(
                str(raw["key"]),
                str(raw["role"]),
                str(raw["text"]),
                bool(raw["enabled"]),
                bool(raw["visible"]),
                bool(raw["text_entry"]),
                bool(raw["selectable"]),
                tuple(str(item) for item in raw["select_options"]),
                bool(raw["sensitive"]),
                str(raw["typed_value"]),
                str(raw["selected_value"]),
                click_action,
            )
        browser.elements = elements
        self._browsers[binding_id] = browser
        return browser

    def snapshot_json(self, binding_id: str) -> str:
        return json.dumps(self.snapshot_state(binding_id), sort_keys=True)

    def restore_json(self, text: str) -> ReferenceBrowser:
        state = json.loads(text)
        if not isinstance(state, dict):
            raise ValueError("browser state must be an object")
        return self.restore_state(state)
