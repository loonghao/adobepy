"""Keep generated host stubs in sync with IR and runtime facade names."""

from __future__ import annotations

import argparse
import ast
import difflib
import pathlib
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python" / "adobe"
IR_DIR = ROOT / "generators" / "ir"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generators.ir_to_python import HostIr, load_ir, render_pyi, snake_case


class StubCheckError(AssertionError):
    """Raised when a committed stub no longer matches the IR/runtime surface."""


def public_members_from_source(source: str, filename: str) -> Dict[str, Set[str]]:
    tree = ast.parse(source, filename=filename)
    classes: Dict[str, Set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        members: Set[str] = set()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                members.add(item.name)
        classes[node.name] = members
    return classes


def public_members(path: pathlib.Path) -> Dict[str, Set[str]]:
    return public_members_from_source(path.read_text(encoding="utf-8"), str(path))


def expected_stub_path(contract: HostIr) -> pathlib.Path:
    return PYTHON_ROOT / snake_case(contract.host) / "session.pyi"


def iter_contracts() -> Iterable[HostIr]:
    for path in sorted(IR_DIR.glob("*.json")):
        yield load_ir(path)


def write_stub(contract: HostIr) -> pathlib.Path:
    target = expected_stub_path(contract)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_pyi(contract), encoding="utf-8")
    return target


def compare_committed_stub(contract: HostIr) -> List[str]:
    target = expected_stub_path(contract)
    expected = render_pyi(contract)
    if not target.exists():
        return [f"{target.relative_to(ROOT)}: missing generated stub; run python scripts/check_generated_stubs.py --write"]
    actual = target.read_text(encoding="utf-8")
    if actual == expected:
        return []
    diff = "\n".join(
        difflib.unified_diff(
            actual.splitlines(),
            expected.splitlines(),
            fromfile=str(target.relative_to(ROOT)),
            tofile=f"generated:{target.relative_to(ROOT)}",
            lineterm="",
        )
    )
    return [f"{target.relative_to(ROOT)} is out of date:\n{diff}"]


def compare_runtime_members(contract: HostIr) -> List[str]:
    stub_classes = public_members_from_source(render_pyi(contract), f"{contract.host}.pyi")
    runtime_path = expected_stub_path(contract).with_suffix(".py")
    runtime_classes = public_members(runtime_path)
    failures: List[str] = []
    for class_name, generated_members in sorted(stub_classes.items()):
        runtime_members = runtime_classes.get(class_name)
        if runtime_members is None:
            failures.append(f"{runtime_path.relative_to(ROOT)}: missing runtime class {class_name}")
            continue
        missing = generated_members - runtime_members
        if missing:
            failures.append(
                f"{runtime_path.relative_to(ROOT)}:{class_name} missing generated stub members {sorted(missing)}"
            )
    return failures


def check_stubs() -> List[str]:
    errors: List[str] = []
    messages: List[str] = []
    for contract in iter_contracts():
        errors.extend(compare_committed_stub(contract))
        errors.extend(compare_runtime_members(contract))
        messages.append(f"{contract.host}: generated stub matches IR and runtime facade")
    if errors:
        raise StubCheckError("\n".join(errors))
    return messages


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check generated Adobe facade stubs")
    parser.add_argument("--write", action="store_true", help="rewrite committed stubs from the IR")
    args = parser.parse_args(argv)

    if args.write:
        for contract in iter_contracts():
            print(write_stub(contract).relative_to(ROOT))
        return 0

    try:
        messages = check_stubs()
    except StubCheckError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for message in messages:
        print(f"stubs ok: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
