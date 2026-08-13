from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, cast

from kaj.runtime.values import (
    KajEnumValue,
    KajList,
    KajMap,
    KajMapKey,
    KajNewtypeValue,
    KajRecord,
    KajTaskHandle,
    RuntimeValue,
)
from kaj.semantic import (
    EnumType,
    ListType,
    MapType,
    NewtypeType,
    OptionalType,
    PrimitiveType,
    RecordType,
    ResultType,
    TaskHandleType,
    TypeCheckResult,
    ValueType,
)
from kaj.serialization import ast_to_json

SNAPSHOT_SCHEMA_VERSION = 1
JSONValue = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


class TaskPersistenceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class TaskSnapshot:
    schema_version: int
    task_id: str
    module_identity: str
    task_name: str
    task_definition_fingerprint: str
    task_state: str
    inputs: tuple[JSONValue, ...]
    execution_position: int
    environment: tuple[dict[str, JSONValue], ...]
    step_states: tuple[tuple[str, str], ...]
    interaction_responses: tuple[tuple[str, JSONValue], ...] = ()
    interactions: tuple[dict[str, JSONValue], ...] = ()
    capability_bindings: tuple[dict[str, JSONValue], ...] = ()
    capability_responses: tuple[tuple[str, JSONValue], ...] = ()
    capability_requests: tuple[dict[str, JSONValue], ...] = ()
    pending_interaction: dict[str, JSONValue] | None = None
    pending_capability_request: dict[str, JSONValue] | None = None
    result: JSONValue = None
    failure: dict[str, JSONValue] | None = None
    goal: str | None = None
    cancellation_reason: str | None = None
    parent_task_id: str | None = None
    child_task_ids: tuple[str, ...] = ()
    waiting_on_task_id: str | None = None
    composition_values: tuple[tuple[str, JSONValue], ...] = ()
    planning_attempt: dict[str, JSONValue] | None = None
    accepted_plan_json: str | None = None
    accepted_plan_fingerprint: str | None = None
    plan_revision: int = 0
    planning_attempts: tuple[dict[str, JSONValue], ...] = ()

    def to_json_value(self) -> dict[str, JSONValue]:
        return cast(
            dict[str, JSONValue],
            {
                "schema_version": self.schema_version,
                "task_id": self.task_id,
                "module_identity": self.module_identity,
                "task_name": self.task_name,
                "task_definition_fingerprint": self.task_definition_fingerprint,
                "task_state": self.task_state,
                "inputs": list(self.inputs),
                "execution_position": self.execution_position,
                "environment": list(self.environment),
                "step_states": [[name, state] for name, state in self.step_states],
                "interaction_responses": [
                    [key, value] for key, value in self.interaction_responses
                ],
                "interactions": list(self.interactions),
                "capability_bindings": list(self.capability_bindings),
                "capability_responses": [[key, value] for key, value in self.capability_responses],
                "capability_requests": list(self.capability_requests),
                "pending_interaction": self.pending_interaction,
                "pending_capability_request": self.pending_capability_request,
                "result": self.result,
                "failure": self.failure,
                "goal": self.goal,
                "cancellation_reason": self.cancellation_reason,
                "parent_task_id": self.parent_task_id,
                "child_task_ids": list(self.child_task_ids),
                "waiting_on_task_id": self.waiting_on_task_id,
                "composition_values": [list(item) for item in self.composition_values],
                "planning_attempt": self.planning_attempt,
                "accepted_plan_json": self.accepted_plan_json,
                "accepted_plan_fingerprint": self.accepted_plan_fingerprint,
                "plan_revision": self.plan_revision,
                "planning_attempts": list(self.planning_attempts),
            },
        )

    @classmethod
    def from_json_value(cls, value: object) -> TaskSnapshot:
        if not isinstance(value, dict):
            raise TaskPersistenceError("TASK_PERSISTENCE_CORRUPT", "Snapshot must be an object.")
        try:
            version = value["schema_version"]
            if type(version) is not int:
                raise TypeError
            if version != SNAPSHOT_SCHEMA_VERSION:
                raise TaskPersistenceError(
                    "TASK_PERSISTENCE_VERSION_UNSUPPORTED",
                    f"Unsupported task snapshot version: {version}.",
                )
            return cls(
                version,
                _string(value, "task_id"),
                _string(value, "module_identity"),
                _string(value, "task_name"),
                _string(value, "task_definition_fingerprint"),
                _string(value, "task_state"),
                tuple(cast(list[JSONValue], value["inputs"])),
                _integer(value, "execution_position"),
                tuple(cast(list[dict[str, JSONValue]], value["environment"])),
                tuple(
                    (str(item[0]), str(item[1]))
                    for item in cast(list[list[object]], value["step_states"])
                ),
                tuple(
                    (str(item[0]), cast(JSONValue, item[1]))
                    for item in cast(list[list[object]], value.get("interaction_responses", []))
                ),
                tuple(cast(list[dict[str, JSONValue]], value.get("interactions", []))),
                tuple(cast(list[dict[str, JSONValue]], value.get("capability_bindings", []))),
                tuple(
                    (str(item[0]), cast(JSONValue, item[1]))
                    for item in cast(list[list[object]], value.get("capability_responses", []))
                ),
                tuple(cast(list[dict[str, JSONValue]], value.get("capability_requests", []))),
                cast(dict[str, JSONValue] | None, value.get("pending_interaction")),
                cast(
                    dict[str, JSONValue] | None,
                    value.get("pending_capability_request"),
                ),
                cast(JSONValue, value.get("result")),
                cast(dict[str, JSONValue] | None, value.get("failure")),
                cast(str | None, value.get("goal")),
                cast(str | None, value.get("cancellation_reason")),
                cast(str | None, value.get("parent_task_id")),
                tuple(str(item) for item in cast(list[object], value.get("child_task_ids", []))),
                cast(str | None, value.get("waiting_on_task_id")),
                tuple(
                    (str(item[0]), cast(JSONValue, item[1]))
                    for item in cast(list[list[object]], value.get("composition_values", []))
                ),
                cast(dict[str, JSONValue] | None, value.get("planning_attempt")),
                cast(str | None, value.get("accepted_plan_json")),
                cast(str | None, value.get("accepted_plan_fingerprint")),
                int(value.get("plan_revision", 0)),
                tuple(cast(list[dict[str, JSONValue]], value.get("planning_attempts", []))),
            )
        except TaskPersistenceError:
            raise
        except (KeyError, TypeError, ValueError, IndexError) as error:
            raise TaskPersistenceError(
                "TASK_PERSISTENCE_CORRUPT", f"Invalid task snapshot: {error}."
            ) from None


class TaskStore(ABC):
    @abstractmethod
    def save(self, snapshot: TaskSnapshot) -> None: ...

    @abstractmethod
    def load(self, task_id: str) -> TaskSnapshot: ...

    @abstractmethod
    def list(self) -> tuple[TaskSnapshot, ...]: ...

    @abstractmethod
    def delete(self, task_id: str) -> None: ...


class InMemoryTaskStore(TaskStore):
    def __init__(self) -> None:
        self._snapshots: dict[str, str] = {}

    def save(self, snapshot: TaskSnapshot) -> None:
        self._snapshots[snapshot.task_id] = json.dumps(snapshot.to_json_value(), ensure_ascii=False)

    def load(self, task_id: str) -> TaskSnapshot:
        text = self._snapshots.get(task_id)
        if text is None:
            raise TaskPersistenceError(
                "TASK_PERSISTENCE_NOT_FOUND", f"Task '{task_id}' was not found."
            )
        return _parse_snapshot(text)

    def list(self) -> tuple[TaskSnapshot, ...]:
        return tuple(_parse_snapshot(text) for _, text in sorted(self._snapshots.items()))

    def delete(self, task_id: str) -> None:
        self._snapshots.pop(task_id, None)


class JSONDirectoryTaskStore(TaskStore):
    """Atomic JSON-file reference backend, one snapshot per task."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        if not task_id or any(
            character not in "0123456789abcdef-" for character in task_id.lower()
        ):
            raise TaskPersistenceError("TASK_PERSISTENCE_INVALID_STATE", "Invalid TaskId.")
        return self.directory / f"{task_id}.json"

    def save(self, snapshot: TaskSnapshot) -> None:
        destination = self._path(snapshot.task_id)
        text = json.dumps(snapshot.to_json_value(), ensure_ascii=False, separators=(",", ":"))
        try:
            with NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.directory, delete=False
            ) as temporary:
                temporary.write(text)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError as error:
            raise TaskPersistenceError("TASK_PERSISTENCE_WRITE_FAILED", str(error)) from None

    def load(self, task_id: str) -> TaskSnapshot:
        try:
            text = self._path(task_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise TaskPersistenceError(
                "TASK_PERSISTENCE_NOT_FOUND", f"Task '{task_id}' was not found."
            ) from None
        except OSError as error:
            raise TaskPersistenceError("TASK_PERSISTENCE_READ_FAILED", str(error)) from None
        return _parse_snapshot(text)

    def list(self) -> tuple[TaskSnapshot, ...]:
        snapshots: list[TaskSnapshot] = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                snapshots.append(_parse_snapshot(path.read_text(encoding="utf-8")))
            except OSError as error:
                raise TaskPersistenceError("TASK_PERSISTENCE_READ_FAILED", str(error)) from None
        return tuple(snapshots)

    def delete(self, task_id: str) -> None:
        try:
            self._path(task_id).unlink(missing_ok=True)
        except OSError as error:
            raise TaskPersistenceError("TASK_PERSISTENCE_WRITE_FAILED", str(error)) from None


class KajValueCodec:
    def __init__(self, types: TypeCheckResult) -> None:
        self._types = types

    def encode(self, value: RuntimeValue) -> JSONValue:
        if value is None:
            return {"kind": "none"}
        if type(value) is bool:
            return {"kind": "bool", "value": value}
        if type(value) is int:
            return {"kind": "int", "value": str(value)}
        if isinstance(value, Decimal):
            return {"kind": "decimal", "value": str(value)}
        if isinstance(value, str):
            return {"kind": "string", "value": value}
        if isinstance(value, bytes):
            return {"kind": "bytes", "value": value.hex()}
        if isinstance(value, KajList):
            return {"kind": "list", "elements": [self.encode(item) for item in value.elements]}
        if isinstance(value, KajMap):
            return {
                "kind": "map",
                "type": self.encode_type(value.type),
                "entries": [
                    [self._encode_map_key(key), self.encode(item)] for key, item in value.entries
                ],
            }
        if isinstance(value, KajRecord):
            return {
                "kind": "record",
                "type": self.encode_type(value.type),
                "fields": [[name, self.encode(item)] for name, item in value.fields],
            }
        if isinstance(value, KajEnumValue):
            return {
                "kind": "enum",
                "type": self.encode_type(value.type),
                "variant": value.variant,
                "payload": [self.encode(item) for item in value.payload],
            }
        if isinstance(value, KajNewtypeValue):
            return {
                "kind": "newtype",
                "type": self.encode_type(value.type),
                "value": self.encode(value.value),
            }
        if isinstance(value, KajTaskHandle):
            return {
                "kind": "task_handle",
                "task_id": value.task_id,
                "result_type": self.encode_type(value.result_type),
            }
        raise TaskPersistenceError(
            "TASK_PERSISTENCE_VALUE_NOT_SERIALIZABLE",
            f"Runtime value of type {type(value).__name__} is not persistable.",
        )

    def decode(self, data: JSONValue) -> RuntimeValue:
        item = _object(data)
        kind = _string(item, "kind")
        if kind == "none":
            return None
        if kind == "bool":
            return cast(bool, item["value"])
        if kind == "int":
            return int(_string(item, "value"))
        if kind == "decimal":
            return Decimal(_string(item, "value"))
        if kind == "string":
            return _string(item, "value")
        if kind == "bytes":
            return bytes.fromhex(_string(item, "value"))
        if kind == "list":
            return KajList(
                tuple(self.decode(value) for value in cast(list[JSONValue], item["elements"]))
            )
        if kind == "map":
            map_type = self.decode_type(item["type"])
            if not isinstance(map_type, MapType):
                raise ValueError("map value has non-map type")
            entries = tuple(
                (
                    self._decode_map_key(pair[0]),
                    self.decode(pair[1]),
                )
                for pair in cast(list[list[JSONValue]], item["entries"])
            )
            return KajMap(map_type, entries)
        if kind == "record":
            value_type = self.decode_type(item["type"])
            if not isinstance(value_type, RecordType):
                raise ValueError("record value has non-record type")
            return KajRecord(
                value_type,
                tuple(
                    (str(pair[0]), self.decode(pair[1]))
                    for pair in cast(list[list[JSONValue]], item["fields"])
                ),
            )
        if kind == "enum":
            value_type = self.decode_type(item["type"])
            if not isinstance(value_type, (EnumType, OptionalType, ResultType)):
                raise ValueError("enum value has non-enum type")
            return KajEnumValue(
                value_type,
                _string(item, "variant"),
                tuple(self.decode(value) for value in cast(list[JSONValue], item["payload"])),
            )
        if kind == "newtype":
            value_type = self.decode_type(item["type"])
            if not isinstance(value_type, NewtypeType):
                raise ValueError("newtype value has non-newtype type")
            return KajNewtypeValue(value_type, self.decode(item["value"]))
        if kind == "task_handle":
            return KajTaskHandle(
                _string(item, "task_id"),
                self.decode_type(item["result_type"]),
            )
        raise ValueError(f"unknown Kaj value kind: {kind}")

    def encode_type(self, value_type: ValueType) -> JSONValue:
        if isinstance(value_type, PrimitiveType):
            return {"kind": "primitive", "name": value_type.value}
        if isinstance(value_type, ListType):
            return {"kind": "list", "element": self.encode_type(value_type.element_type)}
        if isinstance(value_type, MapType):
            return {
                "kind": "map",
                "key": self.encode_type(value_type.key_type),
                "value": self.encode_type(value_type.value_type),
            }
        if isinstance(value_type, OptionalType):
            return {"kind": "optional", "value": self.encode_type(value_type.value_type)}
        if isinstance(value_type, ResultType):
            return {
                "kind": "result",
                "ok": self.encode_type(value_type.ok_type),
                "err": self.encode_type(value_type.err_type),
            }
        if isinstance(value_type, TaskHandleType):
            return {"kind": "task_handle", "result": self.encode_type(value_type.result_type)}
        if isinstance(value_type, (RecordType, EnumType, NewtypeType)):
            return {
                "kind": type(value_type).__name__.removesuffix("Type").lower(),
                "name": value_type.symbol.name,
            }
        raise TaskPersistenceError(
            "TASK_PERSISTENCE_VALUE_NOT_SERIALIZABLE", f"Type {value_type!s} is not persistable."
        )

    def decode_type(self, data: JSONValue) -> ValueType:
        item = _object(data)
        kind = _string(item, "kind")
        if kind == "primitive":
            return PrimitiveType(_string(item, "name"))
        if kind == "list":
            return ListType(self.decode_type(item["element"]))
        if kind == "map":
            return MapType(
                self.decode_type(item["key"]),
                self.decode_type(item["value"]),
            )
        if kind == "optional":
            return OptionalType(self.decode_type(item["value"]))
        if kind == "result":
            return ResultType(
                self.decode_type(item["ok"]),
                self.decode_type(item["err"]),
            )
        if kind == "task_handle":
            return TaskHandleType(self.decode_type(item["result"]))
        name = _string(item, "name")
        candidates: tuple[Any, ...]
        if kind == "record":
            candidates = (*self._types.records, *self._types.imported_records)
        elif kind == "enum":
            candidates = (*self._types.enums, *self._types.imported_enums)
        elif kind == "newtype":
            candidates = (*self._types.newtypes, *self._types.imported_newtypes)
        else:
            raise ValueError(f"unknown Kaj type kind: {kind}")
        match = next(
            (definition.type for definition in candidates if definition.type.symbol.name == name),
            None,
        )
        if match is None:
            raise ValueError(f"unknown nominal Kaj type: {name}")
        return cast(ValueType, match)

    def _encode_map_key(self, key: KajMapKey) -> JSONValue:
        value: JSONValue
        if isinstance(key.value, KajMapKey):
            value = self._encode_map_key(key.value)
        elif isinstance(key.value, Decimal):
            value = {"decimal": str(key.value)}
        elif isinstance(key.value, bytes):
            value = {"bytes": key.value.hex()}
        else:
            value = cast(JSONValue, key.value)
        return {"type": self.encode_type(key.type), "value": value}

    def _decode_map_key(self, data: JSONValue) -> KajMapKey:
        item = _object(data)
        key_type = self.decode_type(item["type"])
        raw = item["value"]
        if not isinstance(key_type, (PrimitiveType, NewtypeType)):
            raise TypeError("invalid map key type")
        if isinstance(raw, dict) and "decimal" in raw:
            value: Any = Decimal(str(raw["decimal"]))
        elif isinstance(raw, dict) and "bytes" in raw:
            value = bytes.fromhex(str(raw["bytes"]))
        elif isinstance(raw, dict) and "type" in raw:
            value = self._decode_map_key(raw)
        else:
            value = raw
        return KajMapKey(key_type, value)


def task_definition_fingerprint(program: Any, task_name: str) -> str:
    canonical = ast_to_json(program)
    return sha256((task_name + "\0" + canonical).encode("utf-8")).hexdigest()


def _parse_snapshot(text: str) -> TaskSnapshot:
    try:
        return TaskSnapshot.from_json_value(json.loads(text))
    except json.JSONDecodeError as error:
        raise TaskPersistenceError(
            "TASK_PERSISTENCE_CORRUPT", f"Invalid snapshot JSON: {error.msg}."
        ) from None


def _object(value: JSONValue) -> dict[str, JSONValue]:
    if not isinstance(value, dict):
        raise TypeError("expected object")
    return value


def _string(value: dict[str, Any], key: str) -> str:
    result = value[key]
    if not isinstance(result, str):
        raise TypeError(f"{key} must be a string")
    return result


def _integer(value: dict[str, Any], key: str) -> int:
    result = value[key]
    if type(result) is not int:
        raise TypeError(f"{key} must be an integer")
    return result
