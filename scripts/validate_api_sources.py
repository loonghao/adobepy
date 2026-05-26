"""Validate the machine-readable Adobe API source registry."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Sequence, Set


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "generators" / "api_sources" / "adobe_api_sources.json"
DEFAULT_IR_DIR = ROOT / "generators" / "ir"
VALID_BRIDGES = {"uxp", "cep", "extendscript"}


class ApiSourceError(ValueError):
    """Raised when the API source registry is incomplete or malformed."""


def load_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def required_string(payload: Dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ApiSourceError(f"{context}: missing string field {key}")
    return value


def validate_url(url: str, context: str) -> None:
    if not url.startswith("https://"):
        raise ApiSourceError(f"{context}: URL must use https: {url}")
    if " " in url:
        raise ApiSourceError(f"{context}: URL must not contain spaces: {url}")


def validate_refs(refs: Any, context: str, *, required: bool) -> None:
    if required and not refs:
        raise ApiSourceError(f"{context}: at least one officialDocs entry is required")
    if refs is None:
        return
    if not isinstance(refs, list):
        raise ApiSourceError(f"{context}: references must be a list")
    for index, ref in enumerate(refs):
        ref_context = f"{context}.refs[{index}]"
        if not isinstance(ref, dict):
            raise ApiSourceError(f"{ref_context}: reference must be an object")
        required_string(ref, "name", ref_context)
        validate_url(required_string(ref, "url", ref_context), ref_context)


def ir_hosts(ir_dir: pathlib.Path) -> Dict[str, pathlib.Path]:
    hosts: Dict[str, pathlib.Path] = {}
    for path in sorted(ir_dir.glob("*.json")):
        payload = load_json(path)
        host = required_string(payload, "host", str(path))
        if host in hosts:
            raise ApiSourceError(f"duplicate IR host {host}: {hosts[host]} and {path}")
        hosts[host] = path
    if not hosts:
        raise ApiSourceError(f"no IR files found under {ir_dir}")
    return hosts


def validate_registry(registry_path: pathlib.Path, ir_dir: pathlib.Path) -> List[str]:
    registry = load_json(registry_path)
    if registry.get("schemaVersion") != 1:
        raise ApiSourceError("schemaVersion must be 1")
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ApiSourceError("sources must be a non-empty list")

    known_hosts = ir_hosts(ir_dir)
    seen_hosts: Set[str] = set()
    messages: List[str] = []
    for index, source in enumerate(sources):
        context = f"sources[{index}]"
        if not isinstance(source, dict):
            raise ApiSourceError(f"{context}: source must be an object")
        host = required_string(source, "host", context)
        if host in seen_hosts:
            raise ApiSourceError(f"{context}: duplicate host {host}")
        seen_hosts.add(host)
        if host not in known_hosts:
            raise ApiSourceError(f"{context}: no matching IR file for host {host}")

        bridge = required_string(source, "bridgeKind", context)
        if bridge not in VALID_BRIDGES:
            raise ApiSourceError(f"{context}: unsupported bridgeKind {bridge}")
        required_string(source, "runtimeModule", context)
        required_string(source, "entryPoint", context)

        ir_path = ROOT / required_string(source, "ir", context)
        if not ir_path.exists():
            raise ApiSourceError(f"{context}: IR path does not exist: {ir_path}")
        if ir_path.resolve() != known_hosts[host].resolve():
            raise ApiSourceError(f"{context}: IR path does not match host {host}: {ir_path}")

        tracked_by = source.get("trackedBy")
        if not isinstance(tracked_by, list) or not tracked_by or not all(isinstance(item, int) and item > 0 for item in tracked_by):
            raise ApiSourceError(f"{context}: trackedBy must contain positive issue numbers")

        validate_refs(source.get("officialDocs"), f"{context}.officialDocs", required=True)
        validate_refs(source.get("secondaryRefs", []), f"{context}.secondaryRefs", required=False)
        notes = source.get("coverageNotes", [])
        if not isinstance(notes, list) or not all(isinstance(item, str) and item for item in notes):
            raise ApiSourceError(f"{context}: coverageNotes must be a list of strings")
        messages.append(f"{host}: {bridge} via {source['runtimeModule']}")

    missing = set(known_hosts) - seen_hosts
    extra = seen_hosts - set(known_hosts)
    if missing or extra:
        raise ApiSourceError(f"source/IR host mismatch; missing={sorted(missing)} extra={sorted(extra)}")
    return messages


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Adobe API source registry")
    parser.add_argument("--registry", type=pathlib.Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--ir-dir", type=pathlib.Path, default=DEFAULT_IR_DIR)
    args = parser.parse_args(argv)

    try:
        messages = validate_registry(args.registry, args.ir_dir)
    except ApiSourceError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for message in messages:
        print(f"valid api source: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
