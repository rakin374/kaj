from __future__ import annotations

from functools import lru_cache

from kaj.modules import compile_module_graph
from kaj.modules.stdlib import stdlib_root
from kaj.runtime.values import KajEnumValue, KajList, KajNewtypeValue, KajRecord, RuntimeValue
from kaj.semantic.types import CapabilityType, EnumType, NewtypeType, RecordType, ResultType
from kaj.testing.browser.fixtures import PAGE_REGISTRY
from kaj.testing.browser.model import ReferenceBrowser, ReferenceElement


class BrowserTypeCatalog:
    def __init__(self, module) -> None:  # type: ignore[no-untyped-def]
        types = module.types
        capability = next(
            export_type
            for _, export_type in module.namespace.values
            if isinstance(export_type, CapabilityType)
        )
        observe = next(item for item in capability.operations if item.name == "observe")
        if not isinstance(observe.return_type, ResultType):
            raise TypeError("observe must return Result")
        self.result_type = observe.return_type
        self.browser_error = self._enum_type(types, "BrowserError")
        self.page_observation = self._record_type(types, "PageObservation")
        self.browser_element = self._record_type(types, "BrowserElement")
        self.browser_viewport = self._record_type(types, "BrowserViewport")
        self.element_id = self._newtype_type(types, "ElementId")
        self.page_generation = self._newtype_type(types, "PageGeneration")

    @staticmethod
    def _record_type(types, name: str) -> RecordType:  # type: ignore[no-untyped-def]
        return next(
            item.type
            for item in (*types.records, *types.imported_records)
            if item.type.symbol.name == name
        )

    @staticmethod
    def _enum_type(types, name: str) -> EnumType:  # type: ignore[no-untyped-def]
        return next(
            item.type
            for item in (*types.enums, *types.imported_enums)
            if item.type.symbol.name == name
        )

    @staticmethod
    def _newtype_type(types, name: str) -> NewtypeType:  # type: ignore[no-untyped-def]
        return next(
            item.type
            for item in (*types.newtypes, *types.imported_newtypes)
            if item.type.symbol.name == name
        )

    def make_element_id(self, value: str) -> KajNewtypeValue:
        return KajNewtypeValue(self.element_id, value)

    def make_page_generation(self, value: int) -> KajNewtypeValue:
        return KajNewtypeValue(self.page_generation, value)

    def make_browser_error(self, variant: str, payload: tuple[RuntimeValue, ...] = ()) -> KajEnumValue:
        return KajEnumValue(self.browser_error, variant, payload)

    def ok(self, observation: KajRecord) -> KajEnumValue:
        return KajEnumValue(self.result_type, "ok", (observation,))

    def err(self, variant: str, payload: tuple[RuntimeValue, ...] = ()) -> KajEnumValue:
        return KajEnumValue(self.result_type, "err", (self.make_browser_error(variant, payload),))

    def observation_for(self, browser: ReferenceBrowser) -> KajRecord:
        page = PAGE_REGISTRY[browser.current_page_key]
        viewport = KajRecord(
            self.browser_viewport,
            (
                ("width", browser.viewport_width),
                ("height", browser.viewport_height),
                ("scroll_x", browser.scroll_x),
                ("scroll_y", browser.scroll_y),
            ),
        )
        elements = KajList(
            tuple(self.element_record(browser, element) for element in visible_elements(browser))
        )
        return KajRecord(
            self.page_observation,
            (
                ("url", page.url),
                ("title", page.title),
                ("generation", self.make_page_generation(browser.generation)),
                ("viewport", viewport),
                ("elements", elements),
            ),
        )

    def element_record(self, browser: ReferenceBrowser, element: ReferenceElement) -> KajRecord:
        return KajRecord(
            self.browser_element,
            (
                ("id", self.make_element_id(browser.element_id(element.key))),
                ("role", element.role),
                ("text", element.text),
                ("enabled", element.enabled),
                ("visible", element.visible),
            ),
        )


def visible_elements(browser: ReferenceBrowser) -> tuple[ReferenceElement, ...]:
    page = PAGE_REGISTRY[browser.current_page_key]
    ordered: list[ReferenceElement] = []
    for template in page.elements:
        current = browser.elements.get(template.key)
        if current is None or not current.visible:
            continue
        ordered.append(current)
    extras = [
        browser.elements[key]
        for key in sorted(browser.elements)
        if key not in {item.key for item in page.elements}
    ]
    ordered.extend(item for item in extras if item.visible)
    return tuple(ordered)


def browser_module():  # type: ignore[no-untyped-def]
    graph = compile_module_graph(
        stdlib_root() / "capabilities" / "_catalog.kaj",
        "import std.capabilities.browser\n",
    )
    if graph.diagnostics:
        raise RuntimeError(graph.diagnostics)
    return next(
        item
        for item in graph.modules
        if item.loaded.name is not None and item.loaded.name.dotted == "std.capabilities.browser"
    )


@lru_cache
def browser_type_catalog() -> BrowserTypeCatalog:
    return BrowserTypeCatalog(browser_module())
