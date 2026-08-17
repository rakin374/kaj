from __future__ import annotations

from pathlib import Path

import pytest

from kaj.ast import PlanRegion, TaskDeclaration
from kaj.capabilities import CapabilityIdentity
from kaj.modules import compile_module_graph
from kaj.pipeline import parse_source
from kaj.runtime import (
    CapabilityRegistry,
    CapabilityRequestId,
    InMemoryTaskStore,
    PlannerAdapter,
    PlannerAdapterResult,
    PlannerProposal,
    TaskPersistenceError,
    TaskRuntime,
    TaskStartError,
    TaskState,
)
from kaj.testing.browser import (
    BROWSER_IDENTITY,
    FIXTURE_URLS,
    ReferenceBrowserRegistry,
    browser_type_catalog,
)
from kaj.testing.browser.fixtures import ASYNC_NAVIGATE_URL, INVALID_URL, UNKNOWN_URL
from kaj.runtime.values import KajEnumValue, KajList, KajRecord

NAVIGATE_RESULTS_TASK = """import std.capabilities.browser

task NavigateResults() -> String {
    use std.capabilities.browser.Browser as browser
    match browser.navigate("https://fixture.test/results") {
        ok(page) => return page.title
        err(error) => return "error"
    }
}
"""

RESULTS_URL = "https://fixture.test/results"
MISSING_URL = "https://fixture.test/missing"


def compile_task(source: str, tmp_path: Path):  # type: ignore[no-untyped-def]
    entry = tmp_path / "task.kaj"
    entry.write_text(source, encoding="utf-8")
    graph = compile_module_graph(entry, source)
    assert graph.diagnostics == ()
    assert graph.entry is not None
    return graph.entry


def browser_runtime(
    source: str,
    tmp_path: Path,
    registry: ReferenceBrowserRegistry,
    binding_id: str = "browser-a",
    *,
    capability_registry: CapabilityRegistry | None = None,
    ensure_binding: bool = True,
    **kwargs,
) -> TaskRuntime:
    entry = compile_task(source, tmp_path)
    if capability_registry is None:
        capability_registry = CapabilityRegistry()
        registry.register_with(capability_registry)
    if ensure_binding and registry.get(binding_id) is None:
        registry.create(binding_id)
    return TaskRuntime(
        entry.loaded.program,
        entry.resolution,
        entry.types,
        capability_registry=capability_registry,
        module_identity="task",
        **kwargs,
    )


def bind_browser(runtime: TaskRuntime, instance, registry: ReferenceBrowserRegistry, binding_id: str, **kwargs):  # type: ignore[no-untyped-def]
    return runtime.bind_capability(
        instance, "browser", registry.adapter_for(binding_id), **kwargs
    )


def page_elements(page: KajRecord) -> tuple[KajRecord, ...]:
    elements = page.fields[4][1]
    assert isinstance(elements, KajList)
    return elements.elements  # type: ignore[return-value]


@pytest.fixture
def registry() -> ReferenceBrowserRegistry:
    return ReferenceBrowserRegistry(types=browser_type_catalog())


def test_reference_model_and_deterministic_ids(registry: ReferenceBrowserRegistry) -> None:
    browser = registry.create("browser-a")
    adapter = registry.adapter_for("browser-a")
    first = adapter.invoke(CapabilityRequestId("1"), "observe", ()).value
    second = adapter.invoke(CapabilityRequestId("2"), "observe", ()).value
    assert isinstance(first, KajEnumValue) and first.variant == "ok"
    assert first.payload == second.payload
    assert browser.element_id("search") == "home:search:1"


def test_observe_repeat_and_unavailable(registry: ReferenceBrowserRegistry) -> None:
    adapter = registry.adapter_for(registry.create("browser-a").host_binding_id)
    ok = adapter.invoke(CapabilityRequestId("1"), "observe", ()).value
    assert isinstance(ok, KajEnumValue) and ok.variant == "ok"
    browser = registry.get("browser-a")
    assert browser is not None
    browser.available = False
    err = adapter.invoke(CapabilityRequestId("2"), "observe", ()).value
    assert isinstance(err, KajEnumValue) and err.variant == "err"
    assert err.payload[0].variant == "unavailable"


@pytest.mark.parametrize(
    ("url", "variant"),
    [
        (RESULTS_URL, "ok"),
        (INVALID_URL, "invalid_url"),
        (UNKNOWN_URL, "navigation_failed"),
        (MISSING_URL, "navigation_failed"),
    ],
)
def test_navigate_outcomes(registry: ReferenceBrowserRegistry, url: str, variant: str) -> None:
    browser = registry.create("browser-a")
    adapter = registry.adapter_for("browser-a")
    before = browser.generation
    result = adapter.invoke(CapabilityRequestId("1"), "navigate", (url,)).value
    assert isinstance(result, KajEnumValue)
    if variant == "ok":
        assert result.variant == "ok"
        assert browser.generation == before + 1
    else:
        assert result.variant == "err"
        assert result.payload[0].variant == variant


def test_click_navigation_stale_and_interactable_errors(registry: ReferenceBrowserRegistry) -> None:
    registry.create("browser-a")
    adapter = registry.adapter_for("browser-a")
    types = registry.types
    observe = adapter.invoke(CapabilityRequestId("1"), "observe", ()).value
    assert isinstance(observe, KajEnumValue)
    page = observe.payload[0]
    assert isinstance(page, KajRecord)
    search_btn = next(
        element
        for element in page_elements(page)
        if element.fields[2][1] == "Search" and element.fields[0][1].value.endswith(":search-btn:1")
    )
    element_id = search_btn.fields[0][1].value
    generation = page.fields[2][1].value
    clicked = adapter.invoke(
        CapabilityRequestId("2"),
        "click",
        (types.make_element_id(element_id), generation),
    ).value
    assert isinstance(clicked, KajEnumValue) and clicked.variant == "ok"
    stale = adapter.invoke(
        CapabilityRequestId("3"),
        "click",
        (types.make_element_id(element_id), generation),
    ).value
    assert isinstance(stale, KajEnumValue) and stale.payload[0].variant == "stale_element"

    home = registry.create("browser-home")
    home_adapter = registry.adapter_for("browser-home")
    fail = home_adapter.invoke(
        CapabilityRequestId("4"),
        "click",
        (types.make_element_id("home:fail-btn:1"), types.make_page_generation(1)),
    ).value
    assert isinstance(fail, KajEnumValue) and fail.payload[0].variant == "action_failed"
    missing = home_adapter.invoke(
        CapabilityRequestId("5"),
        "click",
        (types.make_element_id("home:missing:1"), types.make_page_generation(1)),
    ).value
    assert isinstance(missing, KajEnumValue) and missing.payload[0].variant == "element_not_found"
    disabled = home_adapter.invoke(
        CapabilityRequestId("6"),
        "click",
        (types.make_element_id("home:disabled-btn:1"), types.make_page_generation(1)),
    ).value
    assert isinstance(disabled, KajEnumValue) and disabled.payload[0].variant == "element_not_interactable"


def test_type_text_select_and_scroll(registry: ReferenceBrowserRegistry) -> None:
    registry.create("browser-a")
    adapter = registry.adapter_for("browser-a")
    types = registry.types
    registry.create("browser-password", page_key="password")
    password = registry.adapter_for("browser-password")
    typed = password.invoke(
        CapabilityRequestId("1"),
        "type_text",
        (
            types.make_element_id("password:password:1"),
            types.make_page_generation(1),
            "secret-value",
        ),
    ).value
    assert isinstance(typed, KajEnumValue) and typed.variant == "ok"
    browser = registry.get("browser-password")
    assert browser is not None
    assert browser.elements["password"].typed_value == "secret-value"
    observed = password.invoke(CapabilityRequestId("2"), "observe", ()).value
    assert isinstance(observed, KajEnumValue)
    element = page_elements(observed.payload[0])[0]
    assert element.fields[2][1] == "Password"

    registry.create("browser-select", page_key="select")
    select_adapter = registry.adapter_for("browser-select")
    invalid = select_adapter.invoke(
        CapabilityRequestId("3"),
        "select",
        (
            types.make_element_id("select:country:1"),
            types.make_page_generation(1),
            "fr",
        ),
    ).value
    assert isinstance(invalid, KajEnumValue) and invalid.payload[0].variant == "invalid_selection"
    valid = select_adapter.invoke(
        CapabilityRequestId("4"),
        "select",
        (
            types.make_element_id("select:country:1"),
            types.make_page_generation(1),
            "ca",
        ),
    ).value
    assert isinstance(valid, KajEnumValue) and valid.variant == "ok"

    scrolled = adapter.invoke(CapabilityRequestId("5"), "scroll", (0, 500)).value
    assert isinstance(scrolled, KajEnumValue) and scrolled.variant == "ok"
    browser = registry.get("browser-a")
    assert browser is not None
    assert browser.scroll_y == 500
    assert browser.generation == 1


def test_sync_task_execution_and_grants(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    denied_runtime = browser_runtime(NAVIGATE_RESULTS_TASK, tmp_path, registry)
    denied = denied_runtime.create_task("NavigateResults")
    adapter = registry.adapter_for("browser-a")
    bind_browser(
        denied_runtime, denied, registry, "browser-a", granted_operations={"observe"}
    )
    denied_runtime.run_task(denied)
    assert denied.failure is not None
    assert denied.failure.code == "CAPABILITY_OPERATION_DENIED"
    assert adapter.invocation_log == []

    allowed_runtime = browser_runtime(NAVIGATE_RESULTS_TASK, tmp_path, registry)
    allowed = allowed_runtime.create_task("NavigateResults")
    allowed_adapter = registry.adapter_for("browser-a")
    allowed_runtime.bind_capability(allowed, "browser", allowed_adapter)
    allowed_runtime.run_task(allowed)
    assert allowed.state is TaskState.COMPLETED
    assert allowed.result == "Results"
    assert allowed_adapter.invocation_log


def test_async_wait_resume_and_duplicate_rejection(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    source = f"""import std.capabilities.browser

task AsyncNavigate() -> String {{
    use std.capabilities.browser.Browser as browser
    match browser.navigate("{ASYNC_NAVIGATE_URL}") {{
        ok(page) => return page.title
        err(error) => return "error"
    }}
}}
"""
    runtime = browser_runtime(source, tmp_path, registry)
    instance = runtime.create_task("AsyncNavigate")
    adapter = registry.adapter_for("browser-a")
    bind_browser(runtime, instance, registry, "browser-a")
    runtime.run_task(instance)
    request = instance.pending_capability_request
    assert request is not None
    assert instance.state is TaskState.WAITING_FOR_CAPABILITY
    result = adapter.complete_pending(str(request.id))
    runtime.complete_capability_request(instance.id, request.id, result)
    assert instance.state is TaskState.COMPLETED
    assert instance.result == "Results"
    with pytest.raises(TaskStartError) as duplicate:
        runtime.complete_capability_request(instance.id, request.id, result)
    assert duplicate.value.code == "CAPABILITY_REQUEST_ALREADY_COMPLETED"


def test_persistence_and_rebind(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    source = NAVIGATE_RESULTS_TASK
    store = InMemoryTaskStore()
    capability_registry = CapabilityRegistry()
    registry.register_with(capability_registry)
    registry.create("browser-a")
    first = browser_runtime(
        source, tmp_path, registry, store=store, capability_registry=capability_registry
    )
    instance = first.create_task("NavigateResults")
    bind_browser(first, instance, registry, "browser-a")
    first.run_task(instance)
    assert instance.state is TaskState.COMPLETED

    saved = registry.snapshot_json("browser-a")
    second_registry = ReferenceBrowserRegistry(types=browser_type_catalog())
    second_registry.restore_json(saved)
    second_registry.register_with(capability_registry)
    second = browser_runtime(
        source,
        tmp_path,
        second_registry,
        store=store,
        capability_registry=capability_registry,
    )
    restored = second.restore_task(instance.id)
    assert restored.state is TaskState.COMPLETED
    assert restored.result == "Results"

    third_registry = ReferenceBrowserRegistry(types=browser_type_catalog())
    third_capability_registry = CapabilityRegistry()
    third_registry.register_with(third_capability_registry)
    third = browser_runtime(
        source,
        tmp_path,
        third_registry,
        store=store,
        capability_registry=third_capability_registry,
        ensure_binding=False,
    )
    with pytest.raises(TaskPersistenceError) as missing:
        third.restore_task(instance.id)
    assert missing.value.code == "CAPABILITY_REBIND_FAILED"


def test_multi_session_isolation(registry: ReferenceBrowserRegistry) -> None:
    registry.create("browser-a")
    registry.create("browser-b")
    adapter_a = registry.adapter_for("browser-a")
    adapter_b = registry.adapter_for("browser-b")
    adapter_a.invoke(CapabilityRequestId("1"), "navigate", (RESULTS_URL,))
    title_b = adapter_b.invoke(CapabilityRequestId("2"), "observe", ()).value
    assert isinstance(title_b, KajEnumValue)
    assert title_b.payload[0].fields[1][1] == "Home"
    assert registry.get("browser-a") is not None and registry.get("browser-a").generation == 2
    assert registry.get("browser-b") is not None and registry.get("browser-b").generation == 1


def test_shared_host_binding_policy(registry: ReferenceBrowserRegistry) -> None:
    registry.create("shared")
    adapter_one = registry.adapter_for("shared")
    adapter_two = registry.adapter_for("shared")
    adapter_one.invoke(CapabilityRequestId("1"), "navigate", (RESULTS_URL,))
    title = adapter_two.invoke(CapabilityRequestId("2"), "observe", ()).value
    assert isinstance(title, KajEnumValue)
    assert title.payload[0].fields[1][1] == "Results"
    assert registry.get("shared") is not None and registry.get("shared").generation == 2


class PendingPlanner(PlannerAdapter):
    def request_plan(self, request):  # type: ignore[no-untyped-def]
        del request
        return PlannerAdapterResult.pending_result()


def test_planner_compatible_workflow(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    source = """import std.capabilities.browser

task Planned() -> None {
    goal "browse"
    use std.capabilities.browser.Browser as browser
    plan {
    }
    return none
}
"""
    runtime = browser_runtime(source, tmp_path, registry, planner_adapter=PendingPlanner())
    instance = runtime.create_task("Planned")
    bind_browser(
        runtime,
        instance,
        registry,
        "browser-a",
        granted_operations={"observe", "navigate", "scroll"},
    )
    runtime.run_task(instance)
    assert instance.state is TaskState.WAITING_FOR_PLANNER
    request = runtime.get_planner_request(instance.id)
    assert request is not None
    assert request.capability_grants == (("browser", ("navigate", "observe", "scroll")),)


def test_event_trace_for_async_browser_workflow(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    source = f"""import std.capabilities.browser

task AsyncNavigate() -> String {{
    use std.capabilities.browser.Browser as browser
    match browser.navigate("{ASYNC_NAVIGATE_URL}") {{
        ok(page) => return page.title
        err(error) => return "error"
    }}
}}
"""
    events: list[str] = []
    runtime = browser_runtime(
        source,
        tmp_path,
        registry,
        event_sink=lambda event: events.append(event.kind),
    )
    instance = runtime.create_task("AsyncNavigate")
    adapter = registry.adapter_for("browser-a")
    bind_browser(runtime, instance, registry, "browser-a")
    runtime.run_task(instance)
    assert "capability_requested" in events
    request = instance.pending_capability_request
    assert request is not None
    runtime.complete_capability_request(
        instance.id, request.id, adapter.complete_pending(str(request.id))
    )
    assert "capability_completed" in events
    assert instance.state is TaskState.COMPLETED


def test_browser_identity_in_binding_descriptor(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    runtime = browser_runtime(NAVIGATE_RESULTS_TASK, tmp_path, registry)
    instance = runtime.create_task("NavigateResults")
    descriptor = bind_browser(runtime, instance, registry, "browser-a")
    assert descriptor.capability_identity == BROWSER_IDENTITY


def test_cross_feature_navigate_observe_click(tmp_path: Path, registry: ReferenceBrowserRegistry) -> None:
    source = """import std.capabilities.browser

task Browse() -> String {
    use std.capabilities.browser.Browser as browser
    step navigate {
        match browser.navigate("https://fixture.test/home") {
            ok(page) => {}
            err(error) => return "navigate-failed"
        }
    }
    step observe {
        match browser.observe() {
            ok(page) => {
                for element in page.elements {
                    if element.text == "Search" and element.role == "button" {
                        match browser.click(element.id, page.generation) {
                            ok(next_page) => return next_page.title
                            err(error) => return "click-failed"
                        }
                    }
                }
            }
            err(error) => return "observe-failed"
        }
    }
    return "missing-button"
}
"""
    runtime = browser_runtime(source, tmp_path, registry)
    instance = runtime.create_task("Browse")
    bind_browser(runtime, instance, registry, "browser-a")
    runtime.run_task(instance)
    assert instance.state is TaskState.COMPLETED
    assert instance.result == "Results"
