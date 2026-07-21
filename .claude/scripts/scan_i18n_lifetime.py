#!/usr/bin/env python3
"""Find persistent storage of borrowed i18n strings in C++ sources.

``T_`` and ``C_`` return pointers into an i18n cache.  Those pointers are only
borrowed: after ``i18n_cache_clear()`` a pointer retained by static storage is
dangling.  This scanner uses tree-sitter (rather than matching C++ with regular
expressions) to follow the value from translation calls, through simple helper
functions, into persistent declarations and mutations.

The owning-string findings are intentionally warnings.  A ``std::string`` copy
does not dangle, but a persistent copy freezes the translation selected when it
was first constructed.

Exit status is 1 when a HIGH finding is emitted, 0 otherwise, and 2 for parser
or input failures.  Parser failures are fail-closed even without
``--require-parser``; that flag is retained for CLI compatibility with the
other tree-sitter scanners.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple



try:
    import tree_sitter_cpp as _tscpp
    from tree_sitter import Language as _Language
    from tree_sitter import Parser as _Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    _tscpp = _Language = _Parser = None


CPP_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
SKIP_DIRS = {
    "contrib", ".git", "worktrees", ".worktrees", "__pycache__",
    "catch2-tests", "rltiles", "util",
}
SKIP_FILES = {"catch_amalgamated.cc"}
KNOWN_PRODUCTION_LEXICAL_DEBT = {
    ("branch-data.h", "unmatched } at offset 12640"),
    ("end.cc", "unmatched } at offset 12112"),
    ("macros.h", "unmatched ) at offset 1874"),
    ("threads.h", "unclosed ( at offset 1016"),
    ("xom.cc", "unmatched ) at offset 177033"),
}


def _production_lexical_prerequisite(relative_path: str,
                                     lexical_error: Optional[str]) -> Optional[str]:
    """Accept only an exact, reviewed production-tree lexical prerequisite."""
    if not lexical_error:
        return None
    debt = (relative_path, lexical_error)
    if debt not in KNOWN_PRODUCTION_LEXICAL_DEBT:
        raise ValueError(
            f"unrecognized production lexical error: {relative_path}: "
            f"{lexical_error}")
    return f"{relative_path}: {lexical_error}"
TRANSLATION_CALLS = {"T_", "C_"}
CONTAINER_MUTATORS = {
    "push_back", "push_front", "emplace", "emplace_back", "emplace_front",
    "insert", "assign", "try_emplace", "insert_or_assign",
}
OWNING_NAMES = {
    "string", "wstring", "u8string", "u16string", "u32string",
    "basic_string",
}
CONTAINER_NAMES = {
    "array", "vector", "deque", "list", "forward_list", "set", "multiset",
    "unordered_set", "unordered_multiset", "map", "multimap",
    "unordered_map", "unordered_multimap", "optional", "pair", "tuple",
}


@dataclass
class FieldInfo:
    name: str
    type_text: str
    raw: bool
    owning: bool
    aggregate: str = ""


@dataclass
class TypeInfo:
    text: str
    raw: bool = False
    owning: bool = False
    container: bool = False
    aggregate: str = ""
    raw_paths: List[str] = field(default_factory=list)
    owning_paths: List[str] = field(default_factory=list)
    unresolved: bool = False


@dataclass
class VariableInfo:
    name: str
    type_info: TypeInfo
    storage: str
    file: str
    node_start: int


@dataclass
class ParsedFile:
    path: str
    source: bytes
    tree: object

    @property
    def root(self):
        # Never retain a native Node alongside its Tree.  In older bindings the
        # Python object clear order can release Tree storage before the Node.
        return self.tree.root_node


@dataclass(frozen=True)
class SourceFact:
    start_byte: int
    end_byte: int
    line: int
    column: int
    text: str


def _source_fact(node, source: bytes) -> SourceFact:
    start = node.start_byte
    end = node.end_byte
    point = node.start_point
    return SourceFact(start, end, point.row + 1, point.column + 1,
                      source[start:end].decode("utf-8", errors="replace"))


def _text(node, source: bytes) -> str:
    start = node.start_byte
    end = node.end_byte
    return source[start:end].decode("utf-8", errors="replace")


def _named_children(node) -> Iterator[object]:
    """Safely enumerate named children without the binding's bulk accessor.

    The installed tree-sitter Python binding crashes natively when
    ``named_children`` materialises very large C++ initializer declarations.
    Indexed ``child(i)`` access is stable.
    """
    for index in range(node.child_count):
        child = node.child(index)
        if child is not None and child.is_named:
            yield child


def _walk(node) -> Iterator[object]:
    if node is None:
        return
    yield node
    for child in _named_children(node):
        if child is not None:
            yield from _walk(child)


def _walk_runtime_expression(node) -> Iterator[object]:
    """Walk an initializer without entering deferred lambda/function bodies."""
    if node is None:
        return
    # A lambda expression is a value created by the initializer; its body does
    # not execute while a static callback is initialized.  Stop before yielding
    # it so a T_()/C_() anywhere in the deferred body cannot taint the sink.
    if node.type in {"lambda_expression", "function_definition"}:
        return
    yield node
    invoked_lambda = None
    if node.type == "call_expression":
        function = node.child_by_field_name("function")
        if function is not None and function.type == "lambda_expression":
            invoked_lambda = function
            body = function.child_by_field_name("body")
            if body is not None:
                yield from _walk_runtime_expression(body)
    for child in _named_children(node):
        if (child is None or child.type in {"lambda_expression", "function_definition"}
                or (invoked_lambda is not None
                    and child.start_byte == invoked_lambda.start_byte
                    and child.end_byte == invoked_lambda.end_byte)):
            continue
        yield from _walk_runtime_expression(child)


def _simple_name(node, source: bytes) -> str:
    if node is None:
        return ""
    if node.type in {"identifier", "field_identifier", "type_identifier"}:
        return _text(node, source)
    name = node.child_by_field_name("name")
    if name is not None:
        return _simple_name(name, source)
    result = ""
    for child in _named_children(node):
        candidate = _simple_name(child, source)
        if candidate:
            result = candidate
    return result


def _call_fact(call, source: bytes) -> Tuple[str, str]:
    """Return (written callee, simple name) without letting a Node escape."""
    # Slice the call node itself; asking this old binding for a child Node of a
    # call inside a huge initializer is intermittently unsafe even when consumed
    # immediately.  The callee is the expression prefix before its argument list.
    raw = _text(call, source)
    written = re.sub(r"\s+", "", raw.split("(", 1)[0])
    names = re.findall(r"[A-Za-z_]\w*", written)
    return written, (names[-1] if names else "")


def _runtime_call_facts(node, source: bytes
                        ) -> Iterator[Tuple[SourceFact, str, str]]:
    """Yield only pure facts; native child Nodes never cross this boundary."""
    if node is None or node.type in {"lambda_expression", "function_definition"}:
        return
    if node.type == "call_expression":
        written, simple = _call_fact(node, source)
        yield _source_fact(node, source), written, simple
        function = node.child_by_field_name("function")
        if function is not None and function.type == "lambda_expression":
            body = function.child_by_field_name("body")
            if body is not None:
                yield from _runtime_call_facts(body, source)
            function_start, function_end = function.start_byte, function.end_byte
        else:
            function_start = function_end = -1
    else:
        function_start = function_end = -1
    for position in range(node.child_count):
        child = node.child(position)
        if (child is not None and child.is_named
                and not (child.start_byte == function_start
                         and child.end_byte == function_end)):
            yield from _runtime_call_facts(child, source)


def _callee_name(call, source: bytes) -> str:
    return _call_fact(call, source)[1]


def _declarator_name(node, source: bytes) -> str:
    if node is None:
        return ""
    if node.type in {"identifier", "field_identifier"}:
        return _text(node, source)
    inner = node.child_by_field_name("declarator")
    if inner is not None:
        return _declarator_name(inner, source)
    for child in _named_children(node):
        value = _declarator_name(child, source)
        if value:
            return value
    return ""


def _declaration_parts(node) -> Iterator[Tuple[object, Optional[object]]]:
    """Yield (declarator, initializer) for a declaration's bindings."""
    type_node = node.child_by_field_name("type")
    for child in _named_children(node):
        is_type = (type_node is not None and child.type == type_node.type
                   and child.start_byte == type_node.start_byte
                   and child.end_byte == type_node.end_byte)
        if is_type or child.type in {
            "storage_class_specifier", "type_qualifier", "attribute_specifier",
            "attribute_declaration",
        }:
            continue
        if child.type == "init_declarator":
            yield child.child_by_field_name("declarator"), child.child_by_field_name("value")
        elif child.type not in {"ERROR"}:
            yield child, None


def _is_static(node, source: bytes) -> bool:
    return any(c.type == "storage_class_specifier" and _text(c, source) == "static"
               for c in _named_children(node))


def _inside_function(node) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.type in {"function_definition", "lambda_expression"}:
            return True
        if parent.type in {"translation_unit", "namespace_definition"}:
            return False
        parent = parent.parent
    return False


def _inside_class(node) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.type in {"class_specifier", "struct_specifier", "union_specifier"}:
            return True
        if parent.type in {"translation_unit", "namespace_definition", "function_definition"}:
            return False
        parent = parent.parent
    return False


def _storage(node, source: bytes) -> str:
    if _inside_class(node):
        return "member"
    if _inside_function(node):
        return "function-static" if _is_static(node, source) else "automatic"
    return "namespace-static" if _is_static(node, source) else "namespace/global"


def _declarator_shape(declarator, source: bytes) -> str:
    return _text(declarator, source) if declarator is not None else ""


def _base_type_text(declaration, source: bytes) -> str:
    type_node = declaration.child_by_field_name("type")
    return _text(type_node, source) if type_node is not None else ""


def _last_type_name(type_text: str) -> str:
    names = re.findall(r"[A-Za-z_]\w*", type_text)
    ignored = {"const", "volatile", "struct", "class", "typename", "std"}
    names = [name for name in names if name not in ignored]
    return names[-1] if names else ""


def _has_char_pointer(text: str) -> bool:
    # This regex only classifies the already parsed type/declarator; it is not
    # used to locate declarations or expressions.
    return bool(re.search(r"\bchar\s*(?:const\s*)?\*", text)
                or re.search(r"\bconst\s+char\s*\*", text))


def _has_owning_string(text: str) -> bool:
    names = set(re.findall(r"[A-Za-z_]\w*", text))
    return bool(names & OWNING_NAMES)


def _has_container(text: str) -> bool:
    names = set(re.findall(r"[A-Za-z_]\w*", text))
    return bool(names & CONTAINER_NAMES) or "[" in text


class Index:
    def __init__(self) -> None:
        self.fields: Dict[str, List[FieldInfo]] = {}
        self.borrowed_helpers: Set[str] = set()
        self.helper_facts: Dict[str, List[Tuple[bool, Set[str]]]] = {}
        self.helper_definition_counts: Dict[str, int] = {}
        self.borrowed_call_names: Set[str] = set()
        self.ambiguous_call_names: Set[str] = set()
        self.variables: Dict[str, List[VariableInfo]] = {}
        self.pending_variables: List[Tuple[str, str, str, str, str, int]] = []

    def type_info(self, base: str, shape: str = "") -> TypeInfo:
        full = (base + " " + shape).strip()
        raw = _has_char_pointer(full)
        owning = _has_owning_string(full)
        container = _has_container(full)
        aggregate = ""
        tokens = re.findall(r"[A-Za-z_]\w*", base)
        for token in reversed(tokens):
            if (token in self.fields and token not in OWNING_NAMES
                    and token not in CONTAINER_NAMES):
                aggregate = token
                break

        raw_paths: List[str] = []
        owning_paths: List[str] = []
        seen: Set[str] = set()

        def add_aggregate(name: str, prefix: str = "", depth: int = 0) -> None:
            if depth > 6 or name in seen:
                return
            seen.add(name)
            for item in self.fields.get(name, []):
                path = f"{prefix}.{item.name}" if prefix else item.name
                if item.raw:
                    raw_paths.append(path)
                if item.owning:
                    owning_paths.append(path)
                if item.aggregate:
                    add_aggregate(item.aggregate, path, depth + 1)
            seen.discard(name)

        if aggregate:
            add_aggregate(aggregate)
        if container and aggregate:
            raw_paths = [f"[].{path}" for path in raw_paths]
            owning_paths = [f"[].{path}" for path in owning_paths]
        if raw and not raw_paths:
            raw_paths.append("[]" if container else "")
        if owning and not owning_paths:
            owning_paths.append("[]" if container else "")

        auto_like = bool(re.search(r"\bauto\b", full))
        unresolved = auto_like or (container and not raw_paths and not owning_paths
                                   and not aggregate)
        return TypeInfo(full, raw or bool(raw_paths), owning or bool(owning_paths),
                        container, aggregate, raw_paths, owning_paths, unresolved)


def _collect_aggregate_types(parsed: Sequence[ParsedFile], index: Index) -> None:
    # First collect names so fields may refer to a type declared later/file-wise.
    for pf in parsed:
        for node in _walk(pf.root):
            if node.type in {"struct_specifier", "class_specifier", "union_specifier"}:
                name = node.child_by_field_name("name")
                if name is not None:
                    index.fields.setdefault(_text(name, pf.source), [])

    for pf in parsed:
        for node in _walk(pf.root):
            if node.type not in {"struct_specifier", "class_specifier", "union_specifier"}:
                continue
            name_node = node.child_by_field_name("name")
            body = node.child_by_field_name("body")
            if name_node is None or body is None:
                continue
            aggregate_name = _text(name_node, pf.source)
            fields: List[FieldInfo] = []
            for decl in _named_children(body):
                if decl.type != "field_declaration":
                    continue
                base = _base_type_text(decl, pf.source)
                for declarator, _ in _declaration_parts(decl):
                    field_name = _declarator_name(declarator, pf.source)
                    if not field_name:
                        continue
                    full = base + " " + _declarator_shape(declarator, pf.source)
                    nested = ""
                    for token in reversed(re.findall(r"[A-Za-z_]\w*", base)):
                        if token in index.fields:
                            nested = token
                            break
                    fields.append(FieldInfo(field_name, full, _has_char_pointer(full),
                                            _has_owning_string(full), nested))
            index.fields[aggregate_name] = fields


def _collect_aggregate_names(pf: ParsedFile, index: Index) -> None:
    for node in _walk(pf.root):
        if node.type in {"struct_specifier", "class_specifier", "union_specifier"}:
            name = node.child_by_field_name("name")
            if name is not None:
                index.fields.setdefault(_text(name, pf.source), [])


def _function_name(node, source: bytes) -> str:
    declarator = node.child_by_field_name("declarator")
    while declarator is not None:
        if declarator.type == "function_declarator":
            return _declarator_name(declarator.child_by_field_name("declarator"), source)
        declarator = declarator.child_by_field_name("declarator")
    return ""


def _function_returns_pointer(node, source: bytes) -> bool:
    """Check pointer layers on the return declarator, not in parameters."""
    declarator = node.child_by_field_name("declarator")
    current = declarator
    while current is not None and current.type != "function_declarator":
        if current.type in {"pointer_declarator", "abstract_pointer_declarator"}:
            return True
        current = current.child_by_field_name("declarator")
    if current is not None:
        trailing = current.child_by_field_name("return_type")
        if trailing is not None and "*" in _text(trailing, source):
            return True
    return False


def _qualified_function_name(node, source: bytes) -> str:
    """Return a namespace/class-qualified function key when available."""
    declarator = node.child_by_field_name("declarator")
    current = declarator
    while current is not None and current.type != "function_declarator":
        current = current.child_by_field_name("declarator")
    name_node = current.child_by_field_name("declarator") if current is not None else None
    if name_node is None:
        return ""
    written = re.sub(r"\s+", "", _text(name_node, source))
    if "::" in written:
        return written
    namespaces = []
    parent = node.parent
    while parent is not None:
        if parent.type == "namespace_definition":
            name = parent.child_by_field_name("name")
            if name is not None:
                namespaces.append(_text(name, source))
        parent = parent.parent
    return "::".join(list(reversed(namespaces)) + [written]) if namespaces else written


def _return_fact(expression, source: bytes) -> Tuple[bool, Set[str]]:
    direct = False
    calls: Set[str] = set()
    for _fact, name, simple in _runtime_call_facts(expression, source):
        if simple in TRANSLATION_CALLS:
            direct = True
        elif name:
            calls.add(name)
    return direct, calls


def _collect_helpers(parsed: Sequence[ParsedFile], index: Index) -> None:
    for pf in parsed:
        for node in _walk(pf.root):
            if node.type != "function_definition" or not _function_returns_pointer(node, pf.source):
                continue
            name = _qualified_function_name(node, pf.source)
            if not name:
                continue
            index.helper_definition_counts[name] = index.helper_definition_counts.get(name, 0) + 1
            returns: List[Tuple[bool, Set[str]]] = []
            body = node.child_by_field_name("body")
            if body is not None:
                for child in _walk(body):
                    if child.type != "return_statement":
                        continue
                    for expression in _named_children(child):
                        returns.append(_return_fact(expression, pf.source))
                        break
            index.helper_facts.setdefault(name, []).extend(returns)


def _finalize_helpers(index: Index) -> None:
    """Resolve pure-Python helper dependency facts to a borrowed-call index."""

    index.borrowed_helpers.clear()
    index.borrowed_call_names.clear()
    index.ambiguous_call_names.clear()

    simple_to_keys: Dict[str, Set[str]] = {}
    for key in index.helper_facts:
        simple_to_keys.setdefault(key.rsplit("::", 1)[-1], set()).add(key)
    index.ambiguous_call_names = {name for name, keys in simple_to_keys.items()
                                  if (len(keys) > 1 or any(
                                      index.helper_definition_counts.get(key, 0) > 1
                                      for key in keys))}

    def resolve(call: str) -> Optional[str]:
        if call in index.helper_facts:
            return call
        simple = call.rsplit("::", 1)[-1]
        keys = simple_to_keys.get(simple, set())
        return next(iter(keys)) if len(keys) == 1 else None

    # Fixed point supports chains h3() -> h2() -> h1() -> T_().
    changed = True
    while changed:
        changed = False
        for name, returns in index.helper_facts.items():
            if name in index.borrowed_helpers:
                continue
            for direct, calls in returns:
                if direct or any(resolve(call) in index.borrowed_helpers for call in calls):
                    index.borrowed_helpers.add(name)
                    changed = True
                    break

    for simple, keys in simple_to_keys.items():
        if (len(keys) == 1 and simple not in index.ambiguous_call_names
                and next(iter(keys)) in index.borrowed_helpers):
            index.borrowed_call_names.add(simple)
    index.borrowed_call_names.update(index.borrowed_helpers)


def _borrowed_sources(node, source: bytes, helpers) -> List[SourceFact]:
    found = []
    borrowed_names = (helpers.borrowed_call_names
                      if isinstance(helpers, Index) else helpers)
    for fact, written, simple in _runtime_call_facts(node, source):
        if (simple in TRANSLATION_CALLS | borrowed_names
                or written in borrowed_names):
            found.append(fact)
    return found


def _ambiguous_sources(node, source: bytes, index: Index) -> List[SourceFact]:
    found = []
    for fact, written, simple in _runtime_call_facts(node, source):
        if "::" not in written and simple in index.ambiguous_call_names:
            found.append(fact)
    return found


def _all_call_facts(node, source: bytes) -> List[Tuple[SourceFact, str, str]]:
    facts = []
    for fact, written, simple in _runtime_call_facts(node, source):
        facts.append((fact, written, simple))
    return facts


def _cross_file_decl_candidates(pf: ParsedFile, local_index: Index) -> List[dict]:
    candidates = []
    known = TRANSLATION_CALLS | local_index.borrowed_call_names
    for node in _walk(pf.root):
        if node.type != "declaration" or _inside_class(node):
            continue
        storage = _storage(node, pf.source)
        if storage == "automatic":
            continue
        base = _base_type_text(node, pf.source)
        for declarator, value in _declaration_parts(node):
            if value is None:
                continue
            shape = _declarator_shape(declarator, pf.source)
            info = local_index.type_info(base, shape)
            for fact, written, simple in _all_call_facts(value, pf.source):
                if simple in known or written in known:
                    continue
                candidates.append({"pf": pf, "source": fact, "written": written,
                                   "simple": simple, "storage": storage,
                                   "base": base, "shape": shape,
                                   "path": _field_path_for_source(
                                       value, fact, info, local_index, pf.source)})
    return candidates


def _collect_variables(parsed: Sequence[ParsedFile], index: Index) -> None:
    for pf in parsed:
        for node in _walk(pf.root):
            if node.type != "declaration" or _inside_class(node):
                continue
            storage = _storage(node, pf.source)
            if storage == "automatic":
                continue
            base = _base_type_text(node, pf.source)
            for declarator, _ in _declaration_parts(node):
                name = _declarator_name(declarator, pf.source)
                if not name:
                    continue
                index.pending_variables.append((
                    name, base, _declarator_shape(declarator, pf.source),
                    storage, pf.path, node.start_byte))


def _finalize_variables(index: Index) -> None:
    for name, base, shape, storage, path, start in index.pending_variables:
        info = index.type_info(base, shape)
        index.variables.setdefault(name, []).append(
            VariableInfo(name, info, storage, path, start))
    index.pending_variables.clear()


def _field_path_for_source(value, source_node, info: TypeInfo,
                           index: Index, source: bytes) -> str:
    """Map a source in aggregate initialization to its raw/owning field."""
    if not info.aggregate:
        if info.raw_paths:
            return info.raw_paths[0]
        if info.owning_paths:
            return info.owning_paths[0]
        return ""

    # Walk initializer lists by positional aggregate fields.  Designated
    # initializers are represented with a designator; their text gives a useful
    # fallback path even on grammar versions that do not expose a field name.
    def locate(init, aggregate: str, prefix: str = "",
               unwrap_container: bool = False) -> str:
        fields = index.fields.get(aggregate, [])
        if init.type not in {"initializer_list", "argument_list"}:
            return prefix
        position = 0
        for child in _named_children(init):
            contains = (child.start_byte <= source_node.start_byte < child.end_byte)
            if contains:
                if (unwrap_container and child.type == "initializer_list"):
                    return locate(child, aggregate, prefix, False)
                if position >= len(fields):
                    return prefix
                field = fields[position]
                path = f"{prefix}.{field.name}" if prefix else field.name
                if field.aggregate and child.type == "initializer_list":
                    return locate(child, field.aggregate, path, False)
                return path
            position += 1
        return prefix

    result = locate(value, info.aggregate, "", info.container)
    return f"[].{result}" if info.container and result else result


def _path_kind(info: TypeInfo, path: str) -> str:
    """Return raw/owning/unresolved for the selected aggregate field path."""
    if path:
        if path in info.raw_paths:
            return "raw"
        if path in info.owning_paths:
            return "owning"
    if info.raw and not info.owning:
        return "raw"
    if info.owning and not info.raw:
        return "owning"
    return "unresolved"


def _sink_kind(info: TypeInfo, path: str) -> str:
    if info.container or path.startswith("[]"):
        return "container"
    if info.aggregate or path:
        return "aggregate-field"
    if info.raw:
        return "raw-pointer"
    if info.owning:
        return "owning-string"
    return "unresolved"


def _line_column(node) -> Tuple[int, int]:
    if isinstance(node, SourceFact):
        return node.line, node.column
    return node.start_point.row + 1, node.start_point.column + 1


def _source_text(source_node, source: bytes) -> str:
    return source_node.text if isinstance(source_node, SourceFact) else _text(source_node, source)


def _make_finding(rule: str, risk: str, pf: ParsedFile, node, storage: str,
                  sink_type: str, field_path: str, source_expr: str,
                  message: str) -> dict:
    line, column = _line_column(node)
    return {
        "rule": rule,
        "risk": risk,
        "file": pf.path,
        "line": line,
        "column": column,
        "storage": storage,
        "sink_type": sink_type,
        "field_path": field_path,
        "source_expr": source_expr[:240],
        "message": message,
    }


def _fingerprint(finding: dict) -> str:
    """Build a location-stable fingerprint from the rendered relative path."""
    normalized_source = " ".join(finding["source_expr"].split())
    identity = "\0".join((
        finding["rule"], finding["file"].replace(os.sep, "/"),
        finding["storage"], finding["sink_type"], finding["field_path"],
        normalized_source,
    ))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _classify_declaration(storage: str, info: TypeInfo,
                          path: str) -> Tuple[str, str, str]:
    kind = _path_kind(info, path)
    if kind == "raw":
        if storage == "function-static":
            return "LIFE001", "HIGH", "borrowed translation stored in static raw storage"
        return "LIFE101", "WARN", "borrowed translation initializes namespace/global raw storage"
    if kind == "owning":
        return "LIFE102", "WARN", "persistent owning string freezes the current translation"
    return "LIFE103", "WARN", "persistent sink type could not be resolved"


def _scan_declarations(pf: ParsedFile, index: Index) -> List[dict]:
    findings = []
    for node in _walk(pf.root):
        if node.type != "declaration" or _inside_class(node):
            continue
        storage = _storage(node, pf.source)
        if storage == "automatic":
            continue
        base = _base_type_text(node, pf.source)
        for declarator, value in _declaration_parts(node):
            if value is None:
                continue
            sources = _borrowed_sources(value, pf.source, index)
            ambiguous = _ambiguous_sources(value, pf.source, index)
            if not sources and not ambiguous:
                continue
            info = index.type_info(base, _declarator_shape(declarator, pf.source))
            for source_node in sources:
                path = _field_path_for_source(value, source_node, info, index, pf.source)
                rule, risk, message = _classify_declaration(storage, info, path)
                findings.append(_make_finding(
                    rule, risk, pf, source_node, storage, _sink_kind(info, path),
                    path, _source_text(source_node, pf.source), message))
            for source_node in ambiguous:
                path = _field_path_for_source(value, source_node, info, index, pf.source)
                findings.append(_make_finding(
                    "LIFE103", "WARN", pf, source_node, storage,
                    _sink_kind(info, path), path, _source_text(source_node, pf.source),
                    "overloaded or namespace-ambiguous helper may return a borrowed translation"))
    return findings


def _field_receiver_and_name(node, source: bytes) -> Tuple[str, str]:
    if node.type != "field_expression":
        return "", ""
    receiver = node.child_by_field_name("argument")
    field_node = node.child_by_field_name("field")
    return (_text(receiver, source) if receiver is not None else "",
            _text(field_node, source) if field_node is not None else "")


def _member_field_info(field_name: str, index: Index) -> Optional[FieldInfo]:
    matches = [item for fields in index.fields.values() for item in fields
               if item.name == field_name]
    if len(matches) == 1:
        return matches[0]
    raw = [item for item in matches if item.raw]
    return raw[0] if raw else (matches[0] if matches else None)


def _in_member_function(node, source: bytes) -> bool:
    """Whether node is inside an inline or qualified out-of-class method."""
    parent = node.parent
    while parent is not None:
        if parent.type in {"class_specifier", "struct_specifier", "union_specifier"}:
            return True
        if parent.type == "function_definition":
            declarator = parent.child_by_field_name("declarator")
            if declarator is not None and "::" in _text(declarator, source):
                return True
        parent = parent.parent
    return False


def _lookup_persistent(name: str, index: Index) -> Optional[VariableInfo]:
    entries = index.variables.get(name, [])
    if not entries:
        return None
    # A namespace/global binding is visible cross-file; otherwise prefer the
    # most recently indexed static.  This conservative choice only affects
    # unresolved same-name shadowing and produces a warning rather than HIGH.
    globals_ = [entry for entry in entries if entry.storage.startswith("namespace")]
    return globals_[0] if globals_ else entries[-1]


def _scan_assignments(pf: ParsedFile, index: Index) -> List[dict]:
    findings = []
    for node in _walk(pf.root):
        if node.type != "assignment_expression":
            continue
        right = node.child_by_field_name("right")
        left = node.child_by_field_name("left")
        if right is None or left is None:
            continue
        sources = _borrowed_sources(right, pf.source, index)
        ambiguous = _ambiguous_sources(right, pf.source, index)
        if not sources and not ambiguous:
            continue
        if left.type == "field_expression":
            receiver, field_name = _field_receiver_and_name(left, pf.source)
            field_info = _member_field_info(field_name, index)
            # ``this->field`` and unqualified member writes have instance
            # lifetime; writes through a known persistent object do as well.
            receiver_root = receiver.split(".", 1)[0].split("->", 1)[0]
            persistent_receiver = receiver == "this" or _lookup_persistent(receiver_root, index)
            if not persistent_receiver:
                continue
            if field_info and field_info.raw:
                rule, risk = "LIFE002", "HIGH"
                message = "borrowed translation assigned to a persistent raw pointer member"
                sink = "member-raw-pointer"
            elif field_info and field_info.owning:
                rule, risk = "LIFE102", "WARN"
                message = "persistent owning member freezes the current translation"
                sink = "member-owning-string"
            else:
                rule, risk = "LIFE103", "WARN"
                message = "persistent member sink type could not be resolved"
                sink = "member-unresolved"
            for source_node in sources:
                findings.append(_make_finding(rule, risk, pf, source_node,
                    "persistent-member", sink, field_name,
                    _source_text(source_node, pf.source), message))
            for source_node in ambiguous:
                findings.append(_make_finding(
                    "LIFE103", "WARN", pf, source_node, "persistent-member",
                    "member-unresolved", field_name, _source_text(source_node, pf.source),
                    "overloaded or namespace-ambiguous helper may return a borrowed translation"))
            continue

        if left.type == "identifier":
            name = _text(left, pf.source)
            field_info = (_member_field_info(name, index)
                          if _in_member_function(node, pf.source) else None)
            if field_info is not None:
                if field_info.raw:
                    rule, risk = "LIFE002", "HIGH"
                    message = "borrowed translation assigned to a persistent raw pointer member"
                    sink = "member-raw-pointer"
                elif field_info.owning:
                    rule, risk = "LIFE102", "WARN"
                    message = "persistent owning member freezes the current translation"
                    sink = "member-owning-string"
                else:
                    rule, risk = "LIFE103", "WARN"
                    message = "persistent member sink type could not be resolved"
                    sink = "member-unresolved"
                for source_node in sources:
                    findings.append(_make_finding(rule, risk, pf, source_node,
                        "persistent-member", sink, name,
                        _source_text(source_node, pf.source), message))
                for source_node in ambiguous:
                    findings.append(_make_finding(
                        "LIFE103", "WARN", pf, source_node, "persistent-member",
                        "member-unresolved", name, _source_text(source_node, pf.source),
                        "overloaded or namespace-ambiguous helper may return a borrowed translation"))
                continue
            variable = _lookup_persistent(name, index)
            if variable is None:
                continue
            info = variable.type_info
            if info.raw:
                if variable.storage == "function-static":
                    rule, risk = "LIFE001", "HIGH"
                    message = "borrowed translation assigned to function-static raw storage"
                else:
                    rule, risk = "LIFE101", "WARN"
                    message = "borrowed translation assigned to namespace/global raw storage"
            elif info.owning:
                rule, risk = "LIFE102", "WARN"
                message = "persistent owning string freezes the current translation"
            else:
                rule, risk = "LIFE103", "WARN"
                message = "persistent assignment sink type could not be resolved"
            for source_node in sources:
                findings.append(_make_finding(rule, risk, pf, source_node,
                    variable.storage, _sink_kind(info, ""), "",
                    _source_text(source_node, pf.source), message))
            for source_node in ambiguous:
                findings.append(_make_finding(
                    "LIFE103", "WARN", pf, source_node, variable.storage,
                    "unresolved", "", _source_text(source_node, pf.source),
                    "overloaded or namespace-ambiguous helper may return a borrowed translation"))
    return findings


def _scan_container_calls(pf: ParsedFile, index: Index) -> List[dict]:
    findings = []
    for node in _walk(pf.root):
        if node.type != "call_expression":
            continue
        function = node.child_by_field_name("function")
        arguments = node.child_by_field_name("arguments")
        if function is None or function.type != "field_expression" or arguments is None:
            continue
        receiver_node = function.child_by_field_name("argument")
        method_node = function.child_by_field_name("field")
        if receiver_node is None or method_node is None:
            continue
        method = _text(method_node, pf.source)
        receiver_text = _text(receiver_node, pf.source)
        # Do not retain child Nodes beyond immediate text extraction.
        receiver_node = method_node = function = None
        if method not in CONTAINER_MUTATORS:
            continue
        receiver_root = receiver_text.split(".", 1)[0].split("->", 1)[0]
        variable = _lookup_persistent(receiver_root, index)
        receiver_fields = re.findall(r"(?:\.|->)([A-Za-z_]\w*)", receiver_text)
        member_name = receiver_fields[-1] if receiver_fields else receiver_root
        member_info = _member_field_info(member_name, index)
        member_context = (receiver_root == "this"
                          or (not receiver_fields
                              and _in_member_function(node, pf.source)))
        if receiver_fields and variable is not None and member_info is not None:
            # ``global_cache.items.push_back``: classify the selected member's
            # element type, rather than the enclosing aggregate's first field.
            info = index.type_info(member_info.type_text)
            storage = variable.storage
            path_prefix = member_name
        elif variable is not None:
            info = variable.type_info
            storage = variable.storage
            path_prefix = ""
        elif member_context and member_info is not None:
            # ``this->items`` or unqualified ``items`` inside a method.
            info = index.type_info(member_info.type_text)
            storage = "persistent-member"
            path_prefix = member_name
        else:
            continue
        sources = _borrowed_sources(arguments, pf.source, index)
        ambiguous = _ambiguous_sources(arguments, pf.source, index)
        if not sources and not ambiguous:
            continue
        for source_node in sources:
            path = _field_path_for_source(arguments, source_node, info, index, pf.source)
            if path_prefix:
                path = (f"{path_prefix}{path}" if path.startswith("[]")
                        else (f"{path_prefix}.{path}" if path else path_prefix))
            # Classification uses paths relative to ``info``; the prefix is
            # presentation context for the enclosing persistent object.
            if path_prefix and path.startswith(path_prefix + "[]"):
                kind_path = path[len(path_prefix):]
            elif path_prefix and path.startswith(path_prefix + "."):
                kind_path = path[len(path_prefix) + 1:]
            else:
                kind_path = "" if path == path_prefix else path
            kind = _path_kind(info, kind_path)
            if kind == "raw":
                rule, risk = "LIFE003", "HIGH"
                message = "borrowed translation inserted into a persistent container"
            elif kind == "owning":
                rule, risk = "LIFE102", "WARN"
                message = "persistent owning container freezes the current translation"
            else:
                rule, risk = "LIFE103", "WARN"
                message = "persistent container element type could not be resolved"
            findings.append(_make_finding(rule, risk, pf, source_node,
                storage, "container-mutation", path,
                _source_text(source_node, pf.source), message))
        for source_node in ambiguous:
            findings.append(_make_finding(
                "LIFE103", "WARN", pf, source_node, storage,
                "container-mutation", path_prefix, _source_text(source_node, pf.source),
                "overloaded or namespace-ambiguous helper may return a borrowed translation"))
    return findings


def _deduplicate(findings: Iterable[dict]) -> List[dict]:
    by_key = {}
    for finding in findings:
        key = (finding["rule"], finding["file"], finding["line"],
               finding["column"], finding["storage"], finding["field_path"])
        by_key.setdefault(key, finding)
    return sorted(by_key.values(), key=lambda f: (
        os.path.normcase(f["file"]), f["line"], f["column"], f["rule"],
        f["field_path"], f["source_expr"],
    ))


def _discover(root: str) -> List[str]:
    paths = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name in SKIP_FILES or os.path.splitext(name)[1].lower() not in CPP_EXTENSIONS:
                continue
            paths.append(os.path.abspath(os.path.join(directory, name)))
    return paths


def _parse_files(paths: Sequence[str], parser) -> Tuple[List[ParsedFile], List[str]]:
    parsed = []
    errors = []
    for path in paths:
        try:
            with open(path, "rb") as handle:
                source = handle.read()
        except OSError as exc:
            errors.append(f"cannot read {path}: {exc}")
            continue
        try:
            tree = parser.parse(source)
            root = tree.root_node
        except Exception as exc:
            errors.append(f"tree-sitter failed for {path}: {exc}")
            continue
        # C/C++ files containing project macros commonly have recoverable ERROR
        # nodes before preprocessing.  Tree-sitter still supplies the useful
        # declarations around them, as relied on by the repository's existing
        # scanners.  Fail only when parsing produced no usable syntax tree.
        if root is None:
            errors.append(f"tree-sitter produced no syntax tree for {path}")
            continue
        # Keep the Tree alive: Node objects retain offsets into its native
        # storage and some tree-sitter versions can crash after Tree GC.
        parsed.append(ParsedFile(path, source, tree))
    return parsed, errors


def _parse_one(path: str, parser, target: bool = False) -> Tuple[Optional[ParsedFile], Optional[str]]:
    try:
        with open(path, "rb") as handle:
            source = handle.read()
        tree = parser.parse(source)
        root = tree.root_node
    except (OSError, Exception) as exc:
        return None, f"cannot parse {path}: {exc}"
    if root is None:
        return None, f"tree-sitter produced no syntax tree for {path}"
    if target and root.has_error:
        return None, f"tree-sitter parse error in target {path}"
    return ParsedFile(path, source, tree), None


def _build_index(paths: Sequence[str], language,
                 retain_paths: Optional[Set[str]] = None,
                 strict_paths: Optional[Set[str]] = None,
                 helper_ast: bool = True,
                 ) -> Tuple[Optional[Index], List[str], List[object], Dict[str, ParsedFile]]:
    """Build the cross-file index without retaining any native Tree/Node."""
    index = Index()
    errors: List[str] = []
    tree_keepalive: List[object] = []
    retained: Dict[str, ParsedFile] = {}

    # Names are a lexical pre-index only; semantic field and expression work
    # remains AST based.  Pre-indexing names lets one parser pass resolve
    # aggregates declared later without retaining Trees or reparsing the repo.
    retained_paths = {os.path.abspath(path) for path in (retain_paths or set())}
    strict_paths = {os.path.abspath(path) for path in (strict_paths or set())}
    for path in paths:
        try:
            with open(path, "rb") as handle:
                header = handle.read().decode("utf-8", errors="replace")
            for name in re.findall(r"\b(?:struct|class|union)\s+([A-Za-z_]\w*)", header):
                index.fields.setdefault(name, [])
        except OSError as exc:
            errors.append(f"cannot read {path}: {exc}")

    for path in paths:
        # Isolate parser recovery state: several generated/macro-heavy DCSS
        # files parse as a top-level ERROR before preprocessing.
        file_parser = _Parser(language)
        absolute = os.path.abspath(path)
        # Read root.has_error immediately while parse-local native objects are
        # alive.  This old binding is not reliable when the root Node check is
        # deferred until after the repository index has been built.
        pf, error = _parse_one(path, file_parser, target=absolute in strict_paths)
        if error:
            errors.append(error)
            continue
        _collect_aggregate_types([pf], index)
        if helper_ast:
            _collect_helpers([pf], index)
        else:
            text_source = pf.source.decode("utf-8", errors="replace")
            pattern = re.compile(
                r"(?:const\s+char\s*\*|char\s+const\s*\*)\s*"
                r"([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{([^{}]*)\}", re.S)
            for match in pattern.finditer(text_source):
                name, body = match.group(1), match.group(2)
                direct = bool(re.search(r"\b(?:T_|C_)\s*\(", body))
                calls = set(re.findall(
                    r"\breturn\s+([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)\s*\(", body))
                index.helper_definition_counts[name] = (
                    index.helper_definition_counts.get(name, 0) + 1)
                index.helper_facts.setdefault(name, []).append((direct, calls))
        _collect_variables([pf], index)
        if absolute in retained_paths:
            retained[absolute] = pf
        else:
            tree_keepalive.append(pf.tree)
            del pf
    _finalize_helpers(index)
    _finalize_variables(index)
    return (None if errors else index), errors, tree_keepalive, retained


def _build_lexical_index(paths: Sequence[str]) -> Index:
    """Pure-stdlib facts for large files that cannot safely enter this TS ABI."""
    index = Index()
    for path in paths:
        try:
            source = open(path, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        masked = _mask_cpp_comments(source)
        for match in re.finditer(r"\bstruct\s+([A-Za-z_]\w*)\s*\{(.*?)\}\s*;",
                                 masked, re.S):
            name, body = match.group(1), match.group(2)
            fields = []
            for declaration in body.split(";"):
                identifiers = re.findall(r"[A-Za-z_]\w*", declaration)
                if not identifiers:
                    continue
                field_name = identifiers[-1]
                fields.append(FieldInfo(
                    field_name, declaration, _has_char_pointer(declaration),
                    _has_owning_string(declaration), ""))
            index.fields[name] = fields
        helper_pattern = re.compile(
            r"(?:const\s+char\s*\*|char\s+const\s*\*)\s*"
            r"([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{([^{}]*)\}", re.S)
        for match in helper_pattern.finditer(masked):
            name, body = match.group(1), match.group(2)
            direct = bool(re.search(r"\b(?:T_|C_)\s*\(", body))
            calls = set(re.findall(
                r"\breturn\s+([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)\s*\(", body))
            index.helper_definition_counts[name] = index.helper_definition_counts.get(name, 0) + 1
            index.helper_facts.setdefault(name, []).append((direct, calls))
    _finalize_helpers(index)
    return index


def _lex_cpp(source: str) -> Tuple[str, Optional[str]]:
    """Mask non-code text and validate basic C++ lexical completeness."""
    out = list(source)
    position, state = 0, "code"
    stack: List[Tuple[str, int]] = []
    first_error: Optional[str] = None
    pairs = {")": "(", "}": "{", "]": "["}
    while position < len(source):
        char = source[position]
        nxt = source[position + 1] if position + 1 < len(source) else ""
        if state == "code":
            if char == "/" and nxt == "/":
                out[position] = out[position + 1] = " "
                position += 2
                state = "line"
                continue
            if char == "/" and nxt == "*":
                out[position] = out[position + 1] = " "
                position += 2
                state = "block"
                continue
            if char == "R" and nxt == '"':
                delimiter_end = source.find("(", position + 2,
                                            min(len(source), position + 19))
                if delimiter_end < 0:
                    return "".join(out), f"invalid raw string at offset {position}"
                delimiter = source[position + 2:delimiter_end]
                if any(c.isspace() or c in "()\\" for c in delimiter):
                    return "".join(out), f"invalid raw string delimiter at offset {position}"
                terminator = ")" + delimiter + '"'
                raw_end = source.find(terminator, delimiter_end + 1)
                if raw_end < 0:
                    return "".join(out), f"unclosed raw string at offset {position}"
                end = raw_end + len(terminator)
                for index in range(position, end):
                    if source[index] != "\n": out[index] = " "
                position = end
                continue
            if char == '"':
                out[position] = " "
                state = "string"
            elif char == "'":
                out[position] = " "
                state = "char"
            elif char in "({[":
                stack.append((char, position))
            elif char in ")}]":
                if not stack or stack[-1][0] != pairs[char]:
                    if first_error is None:
                        first_error = f"unmatched {char} at offset {position}"
                else:
                    stack.pop()
        elif state == "line":
            if char == "\n": state = "code"
            else: out[position] = " "
        elif state == "block":
            if char == "*" and nxt == "/":
                out[position] = out[position + 1] = " "
                position += 2
                state = "code"
                continue
            if char != "\n": out[position] = " "
        else:
            if char == "\n":
                return "".join(out), f"unclosed {state} literal at offset {position}"
            out[position] = " "
            if char == "\\":
                if position + 1 >= len(source):
                    return "".join(out), f"unclosed {state} literal at offset {position}"
                if source[position + 1] != "\n": out[position + 1] = " "
                position += 2
                continue
            if (state == "string" and char == '"') or (state == "char" and char == "'"):
                state = "code"
        position += 1
    if state == "block":
        return "".join(out), "unclosed block comment"
    if state in {"string", "char"}:
        return "".join(out), f"unclosed {state} literal"
    if stack:
        opener, offset = stack[-1]
        if first_error is None:
            first_error = f"unclosed {opener} at offset {offset}"
    return "".join(out), first_error


def _mask_cpp_comments(source: str) -> str:
    return _lex_cpp(source)[0]


def _find_matching_paren(source: str, opening: int) -> Optional[int]:
    depth = 0
    for position in range(opening, len(source)):
        if source[position] == "(": depth += 1
        elif source[position] == ")":
            depth -= 1
            if depth == 0: return position
    return None


def _matching_brace(masked: str, opening: int) -> Optional[int]:
    depth = 0
    for position in range(opening, len(masked)):
        if masked[position] == "{":
            depth += 1
        elif masked[position] == "}":
            depth -= 1
            if depth == 0:
                return position
    return None


def _function_ranges(masked: str) -> List[Tuple[int, int]]:
    """Approximate function bodies from balanced, already-masked C++ text."""
    stack: List[Tuple[int, bool]] = []
    ranges: List[Tuple[int, int]] = []
    controls = {"if", "for", "while", "switch", "catch"}
    for position, character in enumerate(masked):
        if character == "{":
            prefix = masked[max(0, position - 500):position]
            header = re.search(
                r"\)\s*(?:(?:const|noexcept|override|final)\s*)*"
                r"(?:->\s*[^{};]+)?$", prefix)
            is_function = False
            if header:
                before = prefix[:header.start()]
                word = re.search(r"([A-Za-z_]\w*)\s*$", before)
                is_function = not word or word.group(1) not in controls
            stack.append((position, is_function))
        elif character == "}" and stack:
            opening, is_function = stack.pop()
            if is_function:
                ranges.append((opening, position))
    return ranges


def _inside_lexical_function(position: int,
                             ranges: Sequence[Tuple[int, int]]) -> bool:
    return any(opening < position < closing for opening, closing in ranges)


def _initializer_end(masked: str, opening: int) -> int:
    """Return the semicolon/end of an initializer starting at '=' or '{'."""
    paren = brace = bracket = 0
    for position in range(opening, len(masked)):
        character = masked[position]
        if character == "(": paren += 1
        elif character == ")": paren -= 1
        elif character == "{": brace += 1
        elif character == "}":
            if brace == 0:
                return position
            brace -= 1
        elif character == "[": bracket += 1
        elif character == "]": bracket -= 1
        elif character == ";" and paren == brace == bracket == 0:
            return position
    return len(masked)


def _inside_parentheses(masked: str, position: int) -> bool:
    depth = 0
    for character in masked[:position]:
        if character == "(": depth += 1
        elif character == ")" and depth: depth -= 1
    return depth > 0


def _without_deferred_lambdas(masked: str) -> str:
    """Blank lambda bodies so persistent containers don't scan runtime text."""
    out = list(masked)
    lambda_re = re.compile(
        r"\[[^\]]*\]\s*(?:\([^{};]*\))?\s*"
        r"(?:(?:mutable|noexcept)\s*)*(?:->\s*[^{}]+)?\{")
    position = 0
    while True:
        match = lambda_re.search(masked, position)
        if not match:
            break
        opening = masked.find("{", match.start(), match.end())
        closing = _matching_brace(masked, opening)
        if closing is None:
            break
        # An immediately invoked lambda evaluates its body as part of the
        # initializer; its returned borrowed pointer is therefore not deferred.
        if re.match(r"\s*\(", masked[closing + 1:]):
            position = closing + 1
            continue
        for index in range(opening, closing + 1):
            if out[index] != "\n": out[index] = " "
        position = closing + 1
    return "".join(out)


def _borrowed_call_match(masked: str, index: Index,
                         start: int = 0, end: Optional[int] = None):
    names = {"T_", "C_"}
    names.update(name for name in index.borrowed_call_names
                 if re.fullmatch(r"[A-Za-z_]\w*", name))
    pattern = r"\b(?:" + "|".join(
        re.escape(name) for name in sorted(names, key=len, reverse=True)) + r")\s*\("
    return re.search(pattern, masked[start:end])


def _aggregate_slot(initializer: str, call_start: int) -> int:
    """Return the positional field containing a call in a braced element."""
    brace_stack = []
    for pos, char in enumerate(initializer[:call_start]):
        if char == "{":
            brace_stack.append(pos)
        elif char == "}" and brace_stack:
            brace_stack.pop()
    if not brace_stack:
        return -1
    opening = brace_stack[-1]
    brace = paren = bracket = 0
    slot = 0
    for char in initializer[opening + 1:call_start]:
        if char == "{": brace += 1
        elif char == "}" and brace: brace -= 1
        elif char == "(": paren += 1
        elif char == ")" and paren: paren -= 1
        elif char == "[": bracket += 1
        elif char == "]" and bracket: bracket -= 1
        elif char == "," and brace == paren == bracket == 0:
            slot += 1
    return slot


def _raw_container_path(type_text: str, index: Index) -> Optional[str]:
    """Resolve a container's raw element, including aggregate element fields."""
    container_pattern = "|".join(
        re.escape(name) for name in sorted(CONTAINER_NAMES, key=len, reverse=True))
    if not re.search(r"\b(?:" + container_pattern + r")\s*<", type_text):
        return None
    if _has_char_pointer(type_text):
        return "[]"
    for type_name in re.findall(r"[A-Za-z_]\w*", type_text):
        for field in index.fields.get(type_name, []):
            if field.raw:
                return f"[].{field.name}"
    return None


def _lexical_source_fact(source: str, masked: str, absolute: int) -> SourceFact:
    opening = masked.find("(", absolute)
    closing = _find_matching_paren(masked, opening) if opening >= 0 else None
    end = closing + 1 if closing is not None else absolute + 2
    line = source.count("\n", 0, absolute) + 1
    column = absolute - source.rfind("\n", 0, absolute)
    return SourceFact(absolute, end, line, column, source[absolute:end])


def _scan_large_lexical(path: str, index: Index,
                        validate: bool = True) -> List[dict]:
    source = open(path, "r", encoding="utf-8", errors="replace").read()
    masked, lexical_error = _lex_cpp(source)
    if lexical_error and validate:
        raise ValueError(f"lexical integrity error in target {path}: {lexical_error}")
    findings = []
    function_ranges = _function_ranges(masked)
    fake = ParsedFile(os.path.abspath(path), source.encode(), None)
    aggregate_ranges: List[Tuple[int, int, Set[str], Set[str]]] = []
    for aggregate in re.finditer(
            r"\b(?:struct|class|union)\s+([A-Za-z_]\w*)[^;{]*\{", masked):
        opening = masked.find("{", aggregate.start(), aggregate.end())
        closing = _matching_brace(masked, opening)
        if closing is None:
            continue
        fields = index.fields.get(aggregate.group(1), [])
        raw_names = {field.name for field in fields if field.raw}
        container_names = {
            field.name for field in fields
            if _raw_container_path(field.type_text, index) is not None
        }
        aggregate_ranges.append(
            (opening, closing, raw_names, container_names))
    qualified_method_ranges: List[Tuple[int, int, str]] = []
    qualified_method_re = re.compile(
        r"\b(?:[A-Za-z_]\w*::)*(?P<class>[A-Za-z_]\w*)::"
        r"(?:~?[A-Za-z_]\w*|operator\s*[^\s(]+)\s*\([^;{}]*\)\s*"
        r"(?:(?:const|noexcept|override|final)\s*)*(?:->\s*[^{};]+)?\{")
    for method in qualified_method_re.finditer(masked):
        opening = masked.find("{", method.start(), method.end())
        closing = _matching_brace(masked, opening)
        if closing is not None:
            qualified_method_ranges.append(
                (opening, closing, method.group("class")))

    # Direct raw pointer variables/arrays.  One finding per persistent sink,
    # even when an array initializer contains many translated elements.
    raw_re = re.compile(
        r"(?P<static>\bstatic\s+)?(?:const\s+char|char\s+const)\s*\*\s*"
        r"(?:const\s+)?(?P<name>[A-Za-z_]\w*)\s*"
        r"(?:\[[^\]]*\]\s*)*(?P<assign>=|\{)", re.S)
    for declaration in raw_re.finditer(masked):
        if _inside_parentheses(masked, declaration.start("assign")):
            continue
        end = _initializer_end(masked, declaration.start("assign"))
        initializer = _without_deferred_lambdas(
            masked[declaration.start("assign"):end])
        call = _borrowed_call_match(initializer, index)
        if not call:
            continue
        absolute = declaration.start("assign") + call.start()
        local = _inside_lexical_function(declaration.start(), function_ranges)
        if local and not declaration.group("static"):
            continue
        fact = _lexical_source_fact(source, masked, absolute)
        if local:
            rule, risk, storage = "LIFE001", "HIGH", "function-static"
            message = "borrowed translation stored in static raw storage"
        else:
            rule, risk, storage = "LIFE101", "WARN", "namespace-global"
            message = "borrowed translation stored in namespace/global raw storage"
        findings.append(_make_finding(
            rule, risk, fake, fact, storage, "raw-pointer-array", "",
            fact.text, message))

    # Owning strings/containers are memory-safe but freeze the active
    # translation at persistent initialization time.
    owning_re = re.compile(
        r"(?P<static>\bstatic\s+)?(?:const\s+)?(?:std::)?"
        r"(?P<kind>string|vector\s*<[^;{}=]+>|array\s*<[^;{}=]+>|"
        r"map\s*<[^;{}=]+>|unordered_map\s*<[^;{}=]+>)\s+"
        r"(?P<name>[A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*"
        r"(?P<assign>=|\{)", re.S)
    for declaration in owning_re.finditer(masked):
        if _inside_parentheses(masked, declaration.start("assign")):
            continue
        local = _inside_lexical_function(declaration.start(), function_ranges)
        if local and not declaration.group("static"):
            continue
        end = _initializer_end(masked, declaration.start("assign"))
        initializer = _without_deferred_lambdas(
            masked[declaration.start("assign"):end])
        call = _borrowed_call_match(initializer, index)
        if not call:
            continue
        kind = declaration.group("kind")
        aggregate_names = re.findall(r"[A-Za-z_]\w*", kind)
        aggregate_fields = next((index.fields[name] for name in aggregate_names
                                 if index.fields.get(name)), None)
        if aggregate_fields:
            cursor = 0
            while True:
                aggregate_call = _borrowed_call_match(initializer, index,
                                                      cursor)
                if not aggregate_call:
                    break
                call_start = cursor + aggregate_call.start()
                slot = _aggregate_slot(initializer, call_start)
                cursor = cursor + aggregate_call.end()
                if slot < 0 or slot >= len(aggregate_fields):
                    continue
                field = aggregate_fields[slot]
                if not field.raw and not field.owning:
                    continue
                absolute = declaration.start("assign") + call_start
                fact = _lexical_source_fact(source, masked, absolute)
                storage = "function-static" if local else "namespace-global"
                field_path = f"[].{field.name}"
                if field.raw:
                    rule, risk = (("LIFE001", "HIGH") if local
                                  else ("LIFE101", "WARN"))
                    findings.append(_make_finding(
                        rule, risk, fake, fact, storage, "raw-pointer-container",
                        field_path, fact.text,
                        "borrowed translation stored in persistent raw storage"))
                else:
                    findings.append(_make_finding(
                        "LIFE102", "WARN", fake, fact, storage,
                        "owning-container", field_path, fact.text,
                        "persistent owning storage freezes the active translation"))
            continue
        absolute = declaration.start("assign") + call.start()
        fact = _lexical_source_fact(source, masked, absolute)
        storage = "function-static" if local else "namespace-global"
        if _has_char_pointer(kind):
            rule = "LIFE001" if local else "LIFE101"
            risk = "HIGH" if local else "WARN"
            findings.append(_make_finding(
                rule, risk, fake, fact, storage, "raw-pointer-container",
                "[]", fact.text,
                "borrowed translation stored in persistent raw storage"))
            continue
        sink = "owning-string" if kind.strip().endswith("string") else "owning-container"
        findings.append(_make_finding(
            "LIFE102", "WARN", fake, fact, storage, sink, "", fact.text,
            "persistent owning storage freezes the active translation"))

    # `auto` deduces `const char *` for a direct T_()/C_() initializer.
    auto_re = re.compile(
        r"(?P<static>\bstatic\s+)?\bauto\s+[A-Za-z_]\w*\s*"
        r"(?P<assign>=|\{)")
    for declaration in auto_re.finditer(masked):
        if _inside_parentheses(masked, declaration.start("assign")):
            continue
        local = _inside_lexical_function(declaration.start(), function_ranges)
        if local and not declaration.group("static"):
            continue
        end = _initializer_end(masked, declaration.start("assign"))
        initializer = _without_deferred_lambdas(
            masked[declaration.start("assign"):end])
        helper_names = {"T_", "C_"} | {
            name for name in index.borrowed_call_names
            if re.fullmatch(r"[A-Za-z_]\w*", name)}
        direct_re = (r"[={]\s*(?:" + "|".join(
            re.escape(name) for name in sorted(helper_names, key=len, reverse=True))
                     + r")\s*\(")
        direct = re.match(direct_re, initializer)
        if not direct:
            continue
        call = _borrowed_call_match(initializer, index)
        absolute = declaration.start("assign") + call.start()
        fact = _lexical_source_fact(source, masked, absolute)
        rule, risk = (("LIFE001", "HIGH") if local
                      else ("LIFE101", "WARN"))
        storage = "function-static" if local else "namespace-global"
        findings.append(_make_finding(
            rule, risk, fake, fact, storage, "raw-pointer", "", fact.text,
            "borrowed translation stored in persistent deduced raw storage"))

    # Persistent raw members assigned after construction.
    raw_member_names = {
        field.name for fields in index.fields.values() for field in fields
        if field.raw
    }
    for name in sorted(raw_member_names, key=len, reverse=True):
        assignment_re = re.compile(
            r"(?<![A-Za-z0-9_])(?P<lhs>(?:this\s*->\s*)?" +
            re.escape(name) + r")\s*=\s*")
        for assignment in assignment_re.finditer(masked):
            explicit_this = assignment.group("lhs").lstrip().startswith("this")
            in_owning_type = any(
                opening < assignment.start() < closing and name in names
                for opening, closing, names, _containers in aggregate_ranges)
            in_qualified_method = any(
                opening < assignment.start() < closing
                and any(field.name == name and field.raw
                        for field in index.fields.get(class_name, []))
                for opening, closing, class_name in qualified_method_ranges)
            if not explicit_this and not in_owning_type and not in_qualified_method:
                continue
            # A typed declaration is an initializer, not a member assignment.
            prefix = masked[max(0, assignment.start() - 100):assignment.start()]
            if re.search(r"(?:char|string|auto|\*)\s*$", prefix):
                continue
            end = _initializer_end(masked, assignment.end() - 1)
            call = _borrowed_call_match(
                _without_deferred_lambdas(masked[assignment.end():end]), index)
            if not call:
                continue
            absolute = assignment.end() + call.start()
            fact = _lexical_source_fact(source, masked, absolute)
            findings.append(_make_finding(
                "LIFE002", "HIGH", fake, fact, "member", "raw-pointer",
                name, fact.text,
                "borrowed translation assigned to persistent raw member"))

    # Mutations of static/global or member containers whose element storage is
    # raw.  The declaration contributes only a name fact; the call contributes
    # the borrowed source fact.
    raw_container_names = set()
    member_container_names = set().union(
        *(containers for _opening, _closing, _names, containers
          in aggregate_ranges)) if aggregate_ranges else set()
    container_paths: Dict[str, str] = {}
    for _opening, _closing, _names, containers in aggregate_ranges:
        for container_name in containers:
            member_field = next((field for fields in index.fields.values()
                                 for field in fields
                                 if field.name == container_name), None)
            if member_field is not None:
                path_value = _raw_container_path(member_field.type_text, index)
                if path_value:
                    container_paths[container_name] = path_value
    declaration_scopes: Dict[str, List[Optional[Tuple[int, int]]]] = {}
    container_decl_re = re.compile(
        r"(?P<static>\bstatic\s+)?(?:const\s+)?(?:std::)?"
        r"(?P<type>(?:" + "|".join(
            re.escape(name) for name in sorted(CONTAINER_NAMES,
                                                key=len, reverse=True)) +
        r")\s*<[^;{}=]+>)\s*"
        r"(?P<name>[A-Za-z_]\w*)")
    for declaration in container_decl_re.finditer(masked):
        path_value = _raw_container_path(declaration.group("type"), index)
        if path_value is None:
            continue
        local_ranges = [scope for scope in function_ranges
                        if scope[0] < declaration.start() < scope[1]]
        if local_ranges and not declaration.group("static"):
            continue
        name = declaration.group("name")
        raw_container_names.add(name)
        container_paths[name] = path_value
        declaration_scopes.setdefault(name, []).append(
            min(local_ranges, key=lambda scope: scope[1] - scope[0])
            if local_ranges else None)
    all_container_names = raw_container_names | member_container_names
    for name in sorted(all_container_names, key=len, reverse=True):
        mutators = "|".join(re.escape(method) for method in sorted(
            CONTAINER_MUTATORS, key=len, reverse=True))
        mutation_re = re.compile(
            r"(?<![A-Za-z0-9_])(?P<this>this\s*->\s*)?" + re.escape(name) +
            r"\s*\.\s*(?:" + mutators + r")\s*\(")
        for mutation in mutation_re.finditer(masked):
            member_ok = (bool(mutation.group("this"))
                         or any(opening < mutation.start() < closing
                                and name in containers
                                for opening, closing, _names, containers
                                in aggregate_ranges)
                         or any(opening < mutation.start() < closing
                                and any(field.name == name
                                        and _raw_container_path(
                                            field.type_text, index) is not None
                                        for field in index.fields.get(
                                            class_name, []))
                                for opening, closing, class_name
                                in qualified_method_ranges))
            declaration_ok = any(
                scope is None or scope[0] < mutation.start() < scope[1]
                for scope in declaration_scopes.get(name, []))
            if not member_ok and not declaration_ok:
                continue
            opening = masked.find("(", mutation.start(), mutation.end())
            closing = _find_matching_paren(masked, opening)
            if closing is None:
                raise ValueError(f"unbalanced container mutation in {path}")
            call = _borrowed_call_match(masked, index, opening + 1, closing)
            if not call:
                continue
            absolute = opening + 1 + call.start()
            fact = _lexical_source_fact(source, masked, absolute)
            field_path = container_paths.get(name, "[]")
            findings.append(_make_finding(
                "LIFE003", "HIGH", fake, fact, "persistent-container",
                "raw-pointer-container", field_path, fact.text,
                "borrowed translation inserted into persistent raw container"))

    declaration_re = re.compile(
        r"\bstatic\s+(?:std::)?vector\s*<\s*([A-Za-z_]\w*)\s*>\s*"
        r"([A-Za-z_]\w*)\s*=\s*\{")
    for declaration in declaration_re.finditer(masked):
        aggregate = declaration.group(1)
        opening = masked.find("{", declaration.start(), declaration.end())
        closing = _matching_brace(masked, opening)
        if closing is None:
            raise ValueError(f"unbalanced static initializer in {path}")
        fields = index.fields.get(aggregate, [])
        for call in re.finditer(r"\b(?:T_|C_)\s*\(", masked[opening:closing]):
            absolute = opening + call.start()
            element_open = masked.rfind("{", opening + 1, absolute)
            if element_open < 0:
                continue
            segment = masked[element_open + 1:absolute]
            field_index = 0
            paren = brace = bracket = 0
            for character in segment:
                if character == "(": paren += 1
                elif character == ")": paren -= 1
                elif character == "{": brace += 1
                elif character == "}": brace -= 1
                elif character == "[": bracket += 1
                elif character == "]": bracket -= 1
                elif character == "," and paren == brace == bracket == 0:
                    field_index += 1
            if field_index >= len(fields) or not fields[field_index].raw:
                continue
            close_paren = _find_matching_paren(masked, masked.find("(", absolute))
            if close_paren is None:
                raise ValueError(f"unbalanced translation call in {path}")
            fact = _lexical_source_fact(source, masked, absolute)
            findings.append(_make_finding(
                "LIFE001", "HIGH", fake, fact, "function-static", "container",
                f"[].{fields[field_index].name}", fact.text,
                "borrowed translation stored in static raw storage"))
    return findings


def _split_files(values: Optional[Sequence[str]]) -> List[str]:
    result = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return result


def _display_path(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path


def _stable_index_root(paths: Sequence[str], fallback: str) -> str:
    """Locate crawl-ref/source so --files and directory scans share identity."""
    for path in paths:
        current = os.path.abspath(path if os.path.isdir(path) else os.path.dirname(path))
        while current != os.path.dirname(current):
            if (os.path.basename(current) == "source"
                    and os.path.basename(os.path.dirname(current)) == "crawl-ref"):
                return current
            current = os.path.dirname(current)
    return os.path.abspath(fallback)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser_cli = argparse.ArgumentParser(
        description="Scan for persistent storage of borrowed T_()/C_() results")
    group = parser_cli.add_mutually_exclusive_group(required=True)
    group.add_argument("source", nargs="?", help="C++ source file or directory")
    group.add_argument("--files", nargs="+", help="files to scan (space/comma separated)")
    parser_cli.add_argument("--format", choices=("text", "json"), default="text")
    parser_cli.add_argument("--include-warn", action="store_true",
                            help="include LIFE1xx advisory findings")
    parser_cli.add_argument("--require-parser", action="store_true",
                            help="compatibility flag; parser failures always exit 2")
    args = parser_cli.parse_args(argv)

    if not TREE_SITTER_AVAILABLE:
        print("ERROR: tree-sitter and tree-sitter-cpp are required", file=sys.stderr)
        return 2

    if args.files:
        raw_targets = _split_files(args.files)
        missing = [path for path in raw_targets if not os.path.isfile(path)]
        invalid = [path for path in raw_targets
                   if os.path.splitext(path)[1].lower() not in CPP_EXTENSIONS]
        if missing or invalid:
            for path in missing:
                print(f"ERROR: input file does not exist: {path}", file=sys.stderr)
            for path in invalid:
                print(f"ERROR: not a C++ source file: {path}", file=sys.stderr)
            return 2
        targets = sorted(set(os.path.abspath(path) for path in raw_targets))
        common = os.path.commonpath([os.path.dirname(path) for path in targets])
        output_root = _stable_index_root(targets, common)
        index_paths = _discover(output_root)
    else:
        source = os.path.abspath(args.source)
        if not os.path.exists(source):
            print(f"ERROR: input path does not exist: {args.source}", file=sys.stderr)
            return 2
        if os.path.isfile(source):
            if os.path.splitext(source)[1].lower() not in CPP_EXTENSIONS:
                print(f"ERROR: not a C++ source file: {args.source}", file=sys.stderr)
                return 2
            targets = [source]
            output_root = _stable_index_root(targets, os.path.dirname(source))
            index_paths = _discover(output_root)
        else:
            targets = _discover(source)
            output_root = _stable_index_root([source], source)
            index_paths = _discover(output_root)

    if not targets:
        print("ERROR: no C++ source files found", file=sys.stderr)
        return 2

    retained_targets = {os.path.abspath(path) for path in targets}
    pre_findings: List[dict] = []
    cross_candidates: List[dict] = []
    lexical_prerequisites: List[str] = []
    try:
        source_arg = os.path.abspath(args.source or "")
        explicit_subset = bool(args.files or os.path.isfile(source_arg))
        production_root = (os.path.basename(source_arg) == "source"
                           and os.path.basename(os.path.dirname(source_arg))
                           == "crawl-ref")
        validate_lexical = explicit_subset or not production_root
        # Use one scanner engine for every invocation size.  The previous
        # >200-file switch made a finding depend on whether the same file was
        # scanned alone or as part of the source root.
        index = _build_lexical_index(index_paths)
        errors, index_trees, parsed_targets = [], [], {}
        for target in targets:
            if production_root:
                with open(target, "r", encoding="utf-8",
                          errors="strict") as source_stream:
                    source_text = source_stream.read()
                _masked, lexical_error = _lex_cpp(source_text)
                if lexical_error:
                    prerequisite = _production_lexical_prerequisite(
                        os.path.relpath(target, source_arg), lexical_error)
                    lexical_prerequisites.append(prerequisite)
            pre_findings.extend(_scan_large_lexical(
                target, index, validate=validate_lexical))
        language = None
    except Exception as exc:
        print(f"ERROR: cannot initialize/build tree-sitter index: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    findings = []
    findings.extend(pre_findings)
    for candidate in cross_candidates:
        if (candidate["written"] in index.borrowed_call_names
                or candidate["simple"] in index.borrowed_call_names):
            info = index.type_info(candidate["base"], candidate["shape"])
            path = candidate["path"]
            rule, risk, message = _classify_declaration(
                candidate["storage"], info, path)
            findings.append(_make_finding(
                rule, risk, candidate["pf"], candidate["source"],
                candidate["storage"], _sink_kind(info, path), path,
                candidate["source"].text, message))
    target_parser = None
    for path in targets:
        # All targets were handled by the scope-independent lexical engine.
        if language is None:
            continue
        pf = parsed_targets.get(os.path.abspath(path))
        if pf is not None and explicit_subset and pf.root.has_error:
            print(f"ERROR: tree-sitter parse error in target {path}", file=sys.stderr)
            return 2
        if pf is None:
            if target_parser is None:
                target_parser = _Parser(language)
            pf, error = _parse_one(path, target_parser, target=True)
            if error:
                print(f"ERROR: {error}", file=sys.stderr)
                return 2
            _collect_aggregate_types([pf], index)
            _collect_helpers([pf], index)
            _finalize_helpers(index)
            _collect_variables([pf], index)
            _finalize_variables(index)
        findings.extend(_scan_declarations(pf, index))
        findings.extend(_scan_assignments(pf, index))
        findings.extend(_scan_container_calls(pf, index))
        del pf
    findings = _deduplicate(findings)
    if not args.include_warn:
        findings = [finding for finding in findings if finding["risk"] == "HIGH"]

    rendered = []
    for finding in findings:
        item = dict(finding)
        item["file"] = _display_path(item["file"], output_root)
        item["fingerprint"] = _fingerprint(item)
        rendered.append(item)
    summary = {
        "HIGH": sum(item["risk"] == "HIGH" for item in rendered),
        "WARN": sum(item["risk"] == "WARN" for item in rendered),
        "total": len(rendered),
    }

    if args.format == "json":
        print(json.dumps({
            "scanner": "scan_i18n_lifetime.py",
            "findings": rendered,
            "summary": summary,
            "coverage": {
                "discovered": len(targets),
                "scanned": len(targets),
                "failed": [],
                "prerequisites": lexical_prerequisites,
            },
        }, ensure_ascii=False, indent=2, sort_keys=False))
    elif rendered:
        print("=== Persistent i18n lifetime findings ===")
        for item in rendered:
            suffix = f" field={item['field_path']}" if item["field_path"] else ""
            print(f"[{item['risk']}] {item['file']}:{item['line']}:{item['column']} "
                  f"{item['rule']} {item['storage']}/{item['sink_type']}{suffix}: "
                  f"{item['source_expr']}")
            print(f"  {item['message']}")
        print(f"Summary: {summary['HIGH']} HIGH (blocking), "
              f"{summary['WARN']} WARN")
    else:
        print("OK: no persistent borrowed i18n strings found.")

    return 1 if summary["HIGH"] else 0


if __name__ == "__main__":
    sys.exit(main())
