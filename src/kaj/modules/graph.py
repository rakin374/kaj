from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kaj.ast import (
    BindingDeclaration,
    FunctionDeclaration,
    ImportDeclaration,
    Program,
    TaskDeclaration,
)
from kaj.diagnostics import Diagnostic
from kaj.modules.names import ModuleName
from kaj.pipeline import parse_source
from kaj.semantic import (
    ModuleType,
    ResolutionResult,
    Resolver,
    SemanticType,
    TypeChecker,
    TypeCheckResult,
    ValueType,
)


@dataclass(frozen=True)
class ModuleDiagnostic:
    path: Path
    diagnostic: Diagnostic


@dataclass(frozen=True)
class LoadedModule:
    name: ModuleName | None
    path: Path
    program: Program
    imports: tuple[ImportDeclaration, ...]


@dataclass(frozen=True)
class ModuleCompilation:
    loaded: LoadedModule
    resolution: ResolutionResult
    types: TypeCheckResult
    namespace: ModuleType
    imported_namespaces: tuple[tuple[ImportDeclaration, ModuleType], ...]


@dataclass(frozen=True)
class ModuleGraphResult:
    modules: tuple[ModuleCompilation, ...]
    diagnostics: tuple[ModuleDiagnostic, ...]

    @property
    def entry(self) -> ModuleCompilation | None:
        return self.modules[-1] if self.modules else None


def compile_module_graph(entry_path: Path, source: str) -> ModuleGraphResult:
    root = entry_path.parent.resolve()
    diagnostics: list[ModuleDiagnostic] = []
    loaded_by_path: dict[Path, LoadedModule] = {}
    loaded_by_name: dict[str, LoadedModule] = {}
    order: list[LoadedModule] = []
    active: list[str] = []

    def parse_module(name: ModuleName | None, path: Path, text: str) -> LoadedModule | None:
        parsed = parse_source(text, str(path))
        diagnostics.extend(ModuleDiagnostic(path, item) for item in parsed.diagnostics)
        if parsed.diagnostics:
            return None
        imports = tuple(
            statement
            for statement in parsed.program.statements
            if isinstance(statement, ImportDeclaration)
        )
        seen: set[tuple[str, ...]] = set()
        for declaration in imports:
            if declaration.path in seen:
                diagnostics.append(
                    ModuleDiagnostic(
                        path,
                        Diagnostic(
                            "IMPORT_DUPLICATE",
                            f"Module '{'.'.join(declaration.path)}' is imported more than once.",
                            declaration.span,
                        ),
                    )
                )
            seen.add(declaration.path)
        return LoadedModule(name, path, parsed.program, imports)

    entry = parse_module(None, entry_path.resolve(), source)
    if entry is None:
        return ModuleGraphResult((), tuple(diagnostics))
    loaded_by_path[entry.path] = entry

    def visit(module: LoadedModule) -> None:
        key = "<entry>" if module.name is None else module.name.dotted
        if key in active:
            cycle = active[active.index(key) :] + [key]
            declaration = module.imports[0] if module.imports else module.program
            diagnostics.append(
                ModuleDiagnostic(
                    module.path,
                    Diagnostic(
                        "IMPORT_CYCLE", "Import cycle: " + " -> ".join(cycle), declaration.span
                    ),
                )
            )
            return
        if module in order:
            return
        active.append(key)
        for declaration in module.imports:
            name = ModuleName(declaration.path)
            if name.dotted in active:
                cycle = active[active.index(name.dotted) :] + [name.dotted]
                diagnostics.append(
                    ModuleDiagnostic(
                        module.path,
                        Diagnostic(
                            "IMPORT_CYCLE", "Import cycle: " + " -> ".join(cycle), declaration.span
                        ),
                    )
                )
                continue
            candidate = (root / name.relative_path()).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                diagnostics.append(
                    ModuleDiagnostic(
                        module.path,
                        Diagnostic(
                            "IMPORT_OUTSIDE_PROJECT",
                            f"Import '{name.dotted}' resolves outside the project root.",
                            declaration.span,
                        ),
                    )
                )
                continue
            dependency = loaded_by_name.get(name.dotted)
            if dependency is None:
                if not candidate.is_file():
                    diagnostics.append(
                        ModuleDiagnostic(
                            module.path,
                            Diagnostic(
                                "IMPORT_NOT_FOUND",
                                f"Local module '{name.dotted}' was not found at {candidate}.",
                                declaration.span,
                            ),
                        )
                    )
                    continue
                try:
                    text = candidate.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    diagnostics.append(
                        ModuleDiagnostic(
                            module.path,
                            Diagnostic(
                                "IMPORT_NOT_FOUND",
                                f"Local module '{name.dotted}' could not be read at {candidate}.",
                                declaration.span,
                            ),
                        )
                    )
                    continue
                dependency = parse_module(name, candidate, text)
                if dependency is None:
                    continue
                existing = loaded_by_path.get(candidate)
                if existing is not None and existing.name != name:
                    dependency = existing
                else:
                    loaded_by_path[candidate] = dependency
                loaded_by_name[name.dotted] = dependency
            visit(dependency)
        active.pop()
        if module not in order:
            order.append(module)

    visit(entry)
    if diagnostics:
        return ModuleGraphResult((), tuple(diagnostics))

    compiled: dict[str, ModuleCompilation] = {}
    results: list[ModuleCompilation] = []
    for index, module in enumerate(order):
        imported: list[tuple[ImportDeclaration, ModuleType]] = []
        for declaration in module.imports:
            target = compiled[".".join(declaration.path)].namespace
            imported.append((declaration, _namespace_chain(declaration.path, target)))
        resolver = Resolver(include_builtins=True)
        resolution = resolver.resolve(module.program)
        imported_by_id = {id(declaration): namespace for declaration, namespace in imported}
        checker = TypeChecker(
            resolution,
            imported_modules=imported_by_id,
            type_id_base=(index + 1) * 1_000_000,
        )
        types = checker.check(module.program)
        diagnostics.extend(
            ModuleDiagnostic(module.path, item)
            for item in (*resolution.diagnostics, *types.diagnostics)
        )
        namespace = _exports(module, resolution, types)
        compilation = ModuleCompilation(module, resolution, types, namespace, tuple(imported))
        results.append(compilation)
        if module.name is not None:
            compiled[module.name.dotted] = compilation
    return ModuleGraphResult(tuple(results), tuple(diagnostics))


def _namespace_chain(path: tuple[str, ...], target: ModuleType) -> ModuleType:
    namespace = target
    for index in range(len(path) - 2, -1, -1):
        namespace = ModuleType(".".join(path[: index + 1]), (), (), ((path[index + 1], namespace),))
    return namespace


def _exports(
    module: LoadedModule, resolution: ResolutionResult, types: TypeCheckResult
) -> ModuleType:
    values: list[tuple[str, SemanticType]] = []
    for statement in module.program.statements:
        if isinstance(statement, (FunctionDeclaration, TaskDeclaration, BindingDeclaration)):
            symbol = resolution.symbol_for_declaration(statement)
            semantic_type = None if symbol is None else types.type_of_symbol(symbol)
            if semantic_type is not None:
                values.append((statement.name, semantic_type))
    exported_types: list[tuple[str, ValueType]] = []
    exported_types.extend((item.type.symbol.name, item.type) for item in types.records)
    exported_types.extend((item.type.symbol.name, item.type) for item in types.enums)
    exported_types.extend((item.type.symbol.name, item.type) for item in types.newtypes)
    name = "<entry>" if module.name is None else module.name.dotted
    return ModuleType(
        name,
        tuple(values),
        tuple(exported_types),
        records=types.records,
        enums=types.enums,
        newtypes=types.newtypes,
    )
