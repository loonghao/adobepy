"""Verify Rust, TypeScript, and Python protocol surfaces share one wire contract."""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Iterable


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "adobepy_protocol_contract.json"
RUST_PROTOCOL = ROOT / "crates" / "adobepy-protocol" / "src" / "lib.rs"
PYTHON_ERRORS = ROOT / "python" / "adobe" / "core" / "errors.py"
TYPESCRIPT_PROTOCOLS = (
    ROOT / "bridges" / "uxp" / "core" / "src" / "protocol.ts",
    ROOT / "bridges" / "cep" / "core" / "src" / "protocol.ts",
)


class ContractError(AssertionError):
    """Raised when a protocol implementation drifts from the shared contract."""


def snake_case(value: str) -> str:
    value = value.replace("-", "_")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def require(pattern: str, text: str, message: str) -> None:
    if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
        raise ContractError(message)


def rust_struct_body(text: str, name: str) -> str:
    match = re.search(rf"pub struct {re.escape(name)}\s*{{(?P<body>.*?)\n}}", text, re.DOTALL)
    if not match:
        raise ContractError(f"Rust protocol is missing struct {name}")
    return match.group("body")


def ts_interface_body(text: str, name: str, path: pathlib.Path) -> str:
    match = re.search(rf"export interface {re.escape(name)}\s*{{(?P<body>.*?)\n}}", text, re.DOTALL)
    if not match:
        raise ContractError(f"{path}: missing TypeScript interface {name}")
    return match.group("body")


def assert_fields(label: str, body: str, fields: Iterable[str], *, rust: bool = False) -> None:
    for field in fields:
        name = snake_case(field) if rust else field
        require(rf"\b{re.escape(name)}\??\s*:", body, f"{label}: missing field {name}")


def check_rust(contract: dict) -> list[str]:
    text = RUST_PROTOCOL.read_text(encoding="utf-8")
    require(
        rf'pub const JSONRPC_VERSION: &str = "{re.escape(contract["jsonrpcVersion"])}";',
        text,
        "Rust JSONRPC_VERSION drifted from contract",
    )
    require(
        rf'pub const DEFAULT_TARGET: &str = "{re.escape(contract["defaultTarget"])}";',
        text,
        "Rust DEFAULT_TARGET drifted from contract",
    )
    for name, code in contract["errorCodes"].items():
        require(rf"pub const {name}: i32 = {code};", text, f"Rust error code {name} drifted from contract")

    for struct_name, fields in contract["wireTypes"].items():
        body = rust_struct_body(text, struct_name)
        assert_fields(f"Rust {struct_name}", body, fields, rust=True)

    for variant in ("Hello", "Response", "Error"):
        require(rf"\b{variant}\s*{{", text, f"Rust BridgeInbound is missing {variant}")
    require(r"\bRequest\s*{\s*request: RpcRequest\s*}", text, "Rust BridgeOutbound is missing Request")
    return ["rust protocol constants, fields, and bridge envelopes"]


def check_typescript(contract: dict) -> list[str]:
    messages: list[str] = []
    for path in TYPESCRIPT_PROTOCOLS:
        text = path.read_text(encoding="utf-8")
        for name, code in contract["errorCodes"].items():
            require(rf"\b{name}\s*:\s*{code}\b", text, f"{path}: error code {name} drifted from contract")
        for interface_name, fields in contract["wireTypes"].items():
            body = ts_interface_body(text, interface_name, path)
            assert_fields(f"{path}:{interface_name}", body, fields)
        for tag in contract["bridgeInboundTypes"] + contract["bridgeOutboundTypes"]:
            require(rf'type:\s*"{re.escape(tag)}"', text, f"{path}: missing bridge envelope type {tag}")
        messages.append(f"{path.relative_to(ROOT)}")
    return messages


def check_python(contract: dict) -> list[str]:
    text = PYTHON_ERRORS.read_text(encoding="utf-8")
    for code_name, class_name in contract["pythonErrorClasses"].items():
        code = contract["errorCodes"][code_name]
        require(
            rf"class {class_name}\(AdobePythonError\):\s+code = {code}",
            text,
            f"Python {class_name} drifted from {code_name}={code}",
        )
    return ["python error class mapping"]


def main() -> int:
    try:
        contract = load_contract()
        messages = []
        messages.extend(check_rust(contract))
        messages.extend(check_typescript(contract))
        messages.extend(check_python(contract))
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for message in messages:
        print(f"protocol contract ok: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
