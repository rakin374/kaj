from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


class ClickActionKind(Enum):
    NAVIGATE = "navigate"
    REFRESH = "refresh"
    FAIL = "fail"


@dataclass(frozen=True)
class NavigateClick:
    page_key: str


@dataclass(frozen=True)
class RefreshClick:
    reveal: tuple[str, str, str]


@dataclass(frozen=True)
class FailClick:
    message: str


ClickAction = NavigateClick | RefreshClick | FailClick


@dataclass
class ReferenceElement:
    key: str
    role: str
    text: str
    enabled: bool = True
    visible: bool = True
    text_entry: bool = False
    selectable: bool = False
    select_options: tuple[str, ...] = ()
    sensitive: bool = False
    typed_value: str = ""
    selected_value: str = ""
    click_action: ClickAction | None = None

    def clone(self) -> ReferenceElement:
        return replace(self)


@dataclass(frozen=True)
class ReferencePage:
    key: str
    url: str
    title: str
    content_width: int
    content_height: int
    elements: tuple[ReferenceElement, ...]


@dataclass
class PendingCapabilityWork:
    operation: str
    arguments: tuple[Any, ...]


@dataclass
class ReferenceBrowser:
    host_binding_id: str
    available: bool = True
    generation: int = 1
    current_page_key: str = "home"
    viewport_width: int = 1280
    viewport_height: int = 720
    scroll_x: int = 0
    scroll_y: int = 0
    elements: dict[str, ReferenceElement] = field(default_factory=dict)
    pending_work: dict[str, PendingCapabilityWork] = field(default_factory=dict)

    def element_id(self, element_key: str) -> str:
        return f"{self.current_page_key}:{element_key}:{self.generation}"

    def parse_element_id(self, element_id: str) -> tuple[str, str, int] | None:
        parts = element_id.split(":")
        if len(parts) != 3:
            return None
        page_key, element_key, generation_text = parts
        if not generation_text.isdigit():
            return None
        return page_key, element_key, int(generation_text)
