"""Check repository architecture boundaries that keep host support maintainable."""

from __future__ import annotations

import ast
import json
import pathlib
import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python" / "adobe"
IR_DIR = ROOT / "generators" / "ir"
API_SOURCES = ROOT / "generators" / "api_sources" / "adobe_api_sources.json"
SHARED_PACKAGES = ("core", "raw", "dcc_mcp")


class ArchitectureError(AssertionError):
    """Raised when an architecture invariant is violated."""


def snake_case(value: str) -> str:
    value = value.replace("-", "_")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def load_ir_hosts() -> Dict[str, pathlib.Path]:
    hosts: Dict[str, pathlib.Path] = {}
    for path in sorted(IR_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        host = payload.get("host")
        if not isinstance(host, str) or not host:
            raise ArchitectureError(f"{path}: missing host")
        if host in hosts:
            raise ArchitectureError(f"duplicate IR host {host}: {hosts[host]} and {path}")
        hosts[host] = path
    if not hosts:
        raise ArchitectureError("no IR hosts found")
    return hosts


def api_source_hosts() -> Set[str]:
    payload = json.loads(API_SOURCES.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ArchitectureError(f"{API_SOURCES}: sources must be a list")
    hosts: Set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("host"), str) or not source["host"]:
            raise ArchitectureError(f"{API_SOURCES}: every source must declare a host")
        hosts.add(source["host"])
    return hosts


def python_files(paths: Iterable[pathlib.Path]) -> Iterable[pathlib.Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(path.rglob("*.py"))
        elif path.suffix == ".py":
            yield path


def import_roots(path: pathlib.Path) -> Iterable[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def public_class_members(path: pathlib.Path) -> Iterable[tuple[str, Set[str]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        members: Set[str] = set()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("__"):
                members.add(item.name)
        yield node.name, members


def literal_string(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


class RuntimeInvokeVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.direct_pairs: Set[tuple[str, str]] = set()
        self.dynamic_helpers: List[tuple[str, str, str]] = []
        self.helper_calls: List[tuple[str, str, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        previous = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = previous

    def visit_Call(self, node: ast.Call) -> None:
        attr = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if attr == "invoke" and len(node.args) >= 2:
            namespace = literal_string(node.args[0])
            method = literal_string(node.args[1])
            if namespace and method:
                self.direct_pairs.add((namespace, method))
            elif namespace and isinstance(node.args[1], ast.Name) and self.current_class and self.current_function:
                self.dynamic_helpers.append((self.current_class, self.current_function, namespace))

        if attr and node.args and self.current_class:
            method = literal_string(node.args[0])
            if method:
                self.helper_calls.append((self.current_class, attr, method))
        self.generic_visit(node)


def runtime_invoke_pairs_from_source(source: str, filename: str) -> Set[tuple[str, str]]:
    visitor = RuntimeInvokeVisitor()
    visitor.visit(ast.parse(source, filename=filename))
    pairs = set(visitor.direct_pairs)
    for class_name, helper_name, namespace in visitor.dynamic_helpers:
        for call_class, call_name, method in visitor.helper_calls:
            if call_class == class_name and call_name == helper_name:
                pairs.add((namespace, method))
    return pairs


def runtime_invoke_pairs(path: pathlib.Path) -> Set[tuple[str, str]]:
    return runtime_invoke_pairs_from_source(path.read_text(encoding="utf-8"), str(path))


def host_packages(hosts: Iterable[str]) -> Dict[str, str]:
    return {host: snake_case(host) for host in hosts}


def check_host_package_parity(hosts: Dict[str, pathlib.Path]) -> List[str]:
    messages: List[str] = []
    source_hosts = api_source_hosts()
    if source_hosts != set(hosts):
        raise ArchitectureError(f"API source/IR host mismatch: {sorted(source_hosts)} != {sorted(hosts)}")

    for host, package in host_packages(hosts).items():
        package_dir = PYTHON_ROOT / package
        if not package_dir.is_dir():
            raise ArchitectureError(f"{host}: missing Python facade package {package_dir}")
        for filename in ("__init__.py", "session.py", "py.typed"):
            if not (package_dir / filename).exists():
                raise ArchitectureError(f"{host}: missing {filename} in {package_dir}")
        messages.append(f"{host}: facade package {package}")

    for package in SHARED_PACKAGES:
        if not (PYTHON_ROOT / package / "py.typed").exists():
            raise ArchitectureError(f"shared package adobe.{package} must include py.typed")
    return messages


def check_python_import_boundaries(hosts: Dict[str, pathlib.Path]) -> List[str]:
    package_by_host = host_packages(hosts)
    host_package_names = set(package_by_host.values())
    messages: List[str] = []

    for shared in SHARED_PACKAGES:
        shared_dir = PYTHON_ROOT / shared
        for path in python_files([shared_dir]):
            for root in import_roots(path):
                parts = root.split(".")
                if len(parts) >= 2 and parts[0] == "adobe" and parts[1] in host_package_names:
                    raise ArchitectureError(f"{path}: shared package adobe.{shared} must not import {root}")
        messages.append(f"adobe.{shared}: no host-specific imports")

    for host, package in package_by_host.items():
        package_dir = PYTHON_ROOT / package
        for path in python_files([package_dir]):
            for root in import_roots(path):
                parts = root.split(".")
                sibling_packages = host_package_names - {package}
                if len(parts) >= 2 and parts[0] == "adobe" and parts[1] in sibling_packages:
                    raise ArchitectureError(f"{path}: host package {host} must not import sibling facade {root}")
        messages.append(f"adobe.{package}: no sibling facade imports")
    return messages


def check_alias_pairs() -> List[str]:
    messages: List[str] = []
    failures: List[str] = []
    for path in python_files([PYTHON_ROOT]):
        relative = path.relative_to(ROOT)
        for class_name, members in public_class_members(path):
            for member in sorted(members):
                if not any(char.isupper() for char in member):
                    continue
                pythonic = snake_case(member)
                if pythonic != member and pythonic not in members:
                    failures.append(f"{relative}:{class_name}.{member} is missing Pythonic alias {pythonic}")
    if failures:
        raise ArchitectureError("\n".join(failures))
    messages.append("facade aliases: every camelCase member has a snake_case sibling")
    return messages


def check_bridge_core_boundaries(hosts: Dict[str, pathlib.Path]) -> List[str]:
    host_terms = set(hosts) | set(host_packages(hosts).values())
    checked: List[pathlib.Path] = []
    for core_dir in (ROOT / "bridges" / "uxp" / "core" / "src", ROOT / "bridges" / "cep" / "core" / "src"):
        for path in sorted(core_dir.glob("*.ts")):
            text = path.read_text(encoding="utf-8").lower()
            for term in host_terms:
                if term.lower() in text:
                    raise ArchitectureError(f"{path}: bridge core must not mention host-specific term {term}")
            checked.append(path)
    return [f"bridge core boundaries: {len(checked)} TypeScript files checked"]


def ir_method_pairs(path: pathlib.Path) -> Set[tuple[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pairs: Set[tuple[str, str]] = set()
    for namespace in payload.get("namespaces", []):
        if not isinstance(namespace, dict) or not isinstance(namespace.get("name"), str):
            continue
        namespace_name = namespace["name"]
        for method in namespace.get("methods", []):
            if isinstance(method, dict) and isinstance(method.get("name"), str):
                pairs.add((namespace_name, method["name"]))
    return pairs


def check_runtime_invokes_declared_in_ir(hosts: Dict[str, pathlib.Path]) -> List[str]:
    messages: List[str] = []
    failures: List[str] = []
    for host, ir_path in hosts.items():
        session_path = PYTHON_ROOT / snake_case(host) / "session.py"
        declared = ir_method_pairs(ir_path)
        invoked = runtime_invoke_pairs(session_path)
        undeclared = sorted(invoked - declared)
        if undeclared:
            failures.append(f"{session_path.relative_to(ROOT)} invokes methods missing from IR: {undeclared}")
        messages.append(f"{host}: {len(invoked)} runtime invoke pairs declared in IR")
    if failures:
        raise ArchitectureError("\n".join(failures))
    return messages


def check_architecture() -> List[str]:
    hosts = load_ir_hosts()
    messages: List[str] = []
    messages.extend(check_host_package_parity(hosts))
    messages.extend(check_python_import_boundaries(hosts))
    messages.extend(check_alias_pairs())
    messages.extend(check_runtime_invokes_declared_in_ir(hosts))
    messages.extend(check_bridge_core_boundaries(hosts))
    return messages


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ = argv
    try:
        messages = check_architecture()
    except ArchitectureError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for message in messages:
        print(f"architecture ok: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
