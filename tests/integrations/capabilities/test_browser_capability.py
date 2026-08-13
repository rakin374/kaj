from __future__ import annotations

import json
from pathlib import Path

import pytest

from kaj.capabilities import CapabilityIdentity, HostBindingId
from kaj.formatting import format_program
from kaj.modules import compile_module_graph, resolve_stdlib_module, stdlib_root
from kaj.modules.names import ModuleName
from kaj.pipeline import parse_source
from kaj.runtime import (
    CapabilityAdapter,
    CapabilityAdapterResult,
    CapabilityBindingDescriptor,
    CapabilityRequestId,
    PlannerAdapter,
    PlannerAdapterResult,
    TaskRuntime,
    TaskState,
    decode_binding_descriptor,
    encode_binding_descriptor,
)
from kaj.runtime.values import (
    KajEnumValue,
    KajList,
    KajNewtypeValue,
    KajRecord,
    RuntimeValue,
)
from kaj.semantic.types import (
    CapabilityOperationType,
    CapabilityType,
    PrimitiveType,
    format_type,
)
from kaj.serialization import ast_from_json, ast_to_json

BROWSER_IDENTITY = CapabilityIdentity("std.capabilities.browser", "Browser", 1)
BROWSER_PATH = stdlib_root() / "capabilities" / "browser.kaj"
BROWSER_SOURCE = BROWSER_PATH.read_text(encoding="utf-8")


def browser_module_compilation():  # type: ignore[no-untyped-def]
    entry = BROWSER_PATH.with_name("_browser_test_entry.kaj")
    graph = compile_module_graph(entry, "import std.capabilities.browser\n")
    assert graph.diagnostics == ()
    module = next(
        item
        for item in graph.modules
        if item.loaded.name is not None and item.loaded.name.dotted == "std.capabilities.browser"
    )
    return module


def browser_capability_type() -> CapabilityType:
    module = browser_module_compilation()
    browser = next(
        export_type
        for _, export_type in module.namespace.values
        if isinstance(export_type, CapabilityType)
    )
    return browser


def operation(name: str) -> CapabilityOperationType:
    capability = browser_capability_type()
    match = next(item for item in capability.operations if item.name == name)
    return match


def test_browser_std_module_resolves() -> None:
    assert resolve_stdlib_module(ModuleName(("std", "capabilities", "browser"))) == BROWSER_PATH
    assert resolve_stdlib_module(ModuleName(("std", "capabilities", "missing"))) is None


def test_qualified_browser_use_compiles(tmp_path: Path) -> None:
    entry = tmp_path / "task.kaj"
    entry.write_text(
        """import std.capabilities.browser

task Browse() -> None {
    use std.capabilities.browser.Browser as browser
    return none
}
""",
        encoding="utf-8",
    )
    graph = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    assert graph.diagnostics == ()


def test_unknown_sibling_capability_errors(tmp_path: Path) -> None:
    entry = tmp_path / "task.kaj"
    entry.write_text(
        """import std.capabilities.browser

task Browse() -> None {
    use std.capabilities.browser.Missing as browser
    return none
}
""",
        encoding="utf-8",
    )
    graph = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    assert any(item.diagnostic.code == "CAPABILITY_UNKNOWN_TYPE" for item in graph.diagnostics)


def test_browser_capability_identity() -> None:
    browser = browser_capability_type()
    assert browser.identity == BROWSER_IDENTITY
    assert browser.identity.canonical == "std.capabilities.browser.Browser@1"


def test_supporting_types_resolve_in_standard_module() -> None:
    entry = browser_module_compilation()
    exported_types = {name for name, _ in entry.namespace.types}
    assert exported_types == {
        "ElementId",
        "PageGeneration",
        "BrowserViewport",
        "BrowserElement",
        "PageObservation",
        "BrowserError",
    }
    newtypes = {item.type.symbol.name for item in entry.types.newtypes}
    assert newtypes == {"ElementId", "PageGeneration"}


def test_element_id_and_page_generation_are_nominal_newtypes() -> None:
    entry = browser_module_compilation()
    element_id = next(item for item in entry.types.newtypes if item.type.symbol.name == "ElementId")
    page_generation = next(
        item for item in entry.types.newtypes if item.type.symbol.name == "PageGeneration"
    )
    assert element_id.underlying_type is PrimitiveType.STRING
    assert page_generation.underlying_type is PrimitiveType.INT


@pytest.mark.parametrize(
    ("name", "parameter_types", "return_type"),
    [
        ("observe", (), "Result<PageObservation, BrowserError>"),
        ("navigate", ("String",), "Result<PageObservation, BrowserError>"),
        ("click", ("ElementId", "PageGeneration"), "Result<PageObservation, BrowserError>"),
        (
            "type_text",
            ("ElementId", "PageGeneration", "String"),
            "Result<PageObservation, BrowserError>",
        ),
        (
            "select",
            ("ElementId", "PageGeneration", "String"),
            "Result<PageObservation, BrowserError>",
        ),
        ("scroll", ("Int", "Int"), "Result<PageObservation, BrowserError>"),
    ],
)
def test_browser_operation_signatures(name: str, parameter_types: tuple[str, ...], return_type: str) -> None:
    operation_type = operation(name)
    assert tuple(format_type(item.type) for item in operation_type.parameters) == parameter_types
    assert format_type(operation_type.return_type) == return_type


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (
            """import std.capabilities.browser
task T() -> None {
    use std.capabilities.browser.Browser as browser
    let x = browser.navigate()
    return none
}
""",
            "TYPE_MISSING_ARGUMENT",
        ),
        (
            """import std.capabilities.browser
task T() -> None {
    use std.capabilities.browser.Browser as browser
    let x = browser.click("a", 1, "extra")
    return none
}
""",
            "TYPE_TOO_MANY_ARGUMENTS",
        ),
        (
            """import std.capabilities.browser
task T() -> None {
    use std.capabilities.browser.Browser as browser
    let x = browser.navigate(1)
    return none
}
""",
            "TYPE_MISMATCH",
        ),
        (
            """import std.capabilities.browser
task T() -> None {
    use std.capabilities.browser.Browser as browser
    let x = browser.nope()
    return none
}
""",
            "CAPABILITY_UNKNOWN_OPERATION",
        ),
    ],
)
def test_wrong_browser_arguments_are_rejected(source: str, code: str, tmp_path: Path) -> None:
    entry = tmp_path / "task.kaj"
    entry.write_text(source, encoding="utf-8")
    graph = compile_module_graph(entry, source)
    assert code in {item.diagnostic.code for item in graph.diagnostics}


def test_browser_contract_values_construct() -> None:
    entry = browser_module_compilation()
    element_id = next(item for item in entry.types.newtypes if item.type.symbol.name == "ElementId")
    page_generation = next(
        item for item in entry.types.newtypes if item.type.symbol.name == "PageGeneration"
    )
    viewport_type = next(item.type for item in entry.types.records if item.type.symbol.name == "BrowserViewport")
    element_type = next(item.type for item in entry.types.records if item.type.symbol.name == "BrowserElement")
    observation_type = next(
        item.type for item in entry.types.records if item.type.symbol.name == "PageObservation"
    )
    error_type = next(item.type for item in entry.types.enums if item.type.symbol.name == "BrowserError")

    element_id_value = KajNewtypeValue(element_id.type, "submit")
    generation_value = KajNewtypeValue(page_generation.type, 7)
    viewport = KajRecord(
        viewport_type,
        (("width", 1280), ("height", 720), ("scroll_x", 0), ("scroll_y", 120)),
    )
    element = KajRecord(
        element_type,
        (
            ("id", element_id_value),
            ("role", "button"),
            ("text", "Submit"),
            ("enabled", True),
            ("visible", True),
        ),
    )
    observation = KajRecord(
        observation_type,
        (
            ("url", "https://example.test/"),
            ("title", "Example"),
            ("generation", generation_value),
            ("viewport", viewport),
            ("elements", KajList((element,))),
        ),
    )
    stale_error = KajEnumValue(error_type, "stale_element", ())
    navigation_error = KajEnumValue(error_type, "navigation_failed", ("bad url",))

    assert isinstance(observation, KajRecord)
    assert isinstance(stale_error, KajEnumValue)
    assert navigation_error.variant == "navigation_failed"


def test_browser_binding_descriptor_preserves_identity() -> None:
    descriptor = CapabilityBindingDescriptor(
        BROWSER_IDENTITY,
        "browser",
        HostBindingId("browser-session-1"),
        frozenset({"observe", "navigate"}),
    )
    encoded = encode_binding_descriptor(descriptor)
    restored = decode_binding_descriptor(encoded)
    assert restored.capability_identity == BROWSER_IDENTITY
    assert "adapter" not in encoded


class PendingPlanner(PlannerAdapter):
    def __init__(self) -> None:
        self.last_request = None

    def request_plan(self, request):  # type: ignore[no-untyped-def]
        self.last_request = request
        return PlannerAdapterResult.pending_result()


class MockBrowserAdapter(CapabilityAdapter):
    @property
    def capability_identity(self) -> CapabilityIdentity:
        return BROWSER_IDENTITY

    @property
    def host_binding_id(self) -> str:
        return "browser-1"

    @property
    def supported_operations(self) -> frozenset[str]:
        return frozenset(
            {"observe", "navigate", "click", "type_text", "select", "scroll"}
        )

    def invoke(
        self,
        request_id: CapabilityRequestId,
        operation: str,
        arguments: tuple[RuntimeValue, ...],
    ) -> CapabilityAdapterResult:
        del request_id, operation, arguments
        return CapabilityAdapterResult.immediate(None)


def test_planner_request_exposes_browser_grants_without_adapter_fields(tmp_path: Path) -> None:
    entry = tmp_path / "planned.kaj"
    entry.write_text(
        """import std.capabilities.browser

task Planned() -> None {
    goal "browse"
    use std.capabilities.browser.Browser as browser
    plan {
    }
    return none
}
""",
        encoding="utf-8",
    )
    graph = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    assert graph.diagnostics == ()
    assert graph.entry is not None
    planner = PendingPlanner()
    runtime = TaskRuntime(
        graph.entry.loaded.program,
        graph.entry.resolution,
        graph.entry.types,
        planner_adapter=planner,
        module_identity="planned",
    )
    instance = runtime.create_task("Planned")
    runtime.bind_capability(
        instance,
        "browser",
        MockBrowserAdapter(),
        granted_operations={"observe", "navigate", "scroll"},
    )
    runtime.run_task(instance)
    assert instance.state is TaskState.WAITING_FOR_PLANNER
    request = runtime.get_planner_request(instance.id)
    assert request is not None
    assert request.capability_grants == (("browser", ("navigate", "observe", "scroll")),)
    payload = request.__dict__
    assert "adapter" not in payload
    assert "host_binding_id" not in payload


def test_browser_ast_json_is_deterministic() -> None:
    parsed = parse_source(BROWSER_SOURCE, str(BROWSER_PATH))
    assert parsed.diagnostics == ()
    encoded = ast_to_json(parsed.program)
    document = json.loads(encoded)
    assert document["program"]["statements"][-1]["kind"] == "capability_declaration"
    assert ast_from_json(encoded) == parsed.program


def test_browser_formatter_is_idempotent() -> None:
    parsed = parse_source(BROWSER_SOURCE, str(BROWSER_PATH))
    assert parsed.diagnostics == ()
    formatted_once = format_program(parsed.program)
    formatted_twice = format_program(parse_source(formatted_once).program)
    assert formatted_once == formatted_twice
    assert formatted_once == BROWSER_SOURCE


def test_browser_import_graph_is_deterministic(tmp_path: Path) -> None:
    entry = tmp_path / "task.kaj"
    entry.write_text("import std.capabilities.browser\n", encoding="utf-8")
    first = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    second = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    assert first.diagnostics == second.diagnostics == ()
    assert [module.loaded.path for module in first.modules] == [
        module.loaded.path for module in second.modules
    ]
