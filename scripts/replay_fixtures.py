"""Replay small Python facade examples against recorded broker responses."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from adobe.after_effects import AfterEffects  # noqa: E402
from adobe.illustrator import Illustrator  # noqa: E402
from adobe.indesign import InDesign  # noqa: E402
from adobe.photoshop import Photoshop  # noqa: E402
from adobe.premiere import Premiere  # noqa: E402


FACADE_BY_HOST = {
    "after-effects": AfterEffects,
    "illustrator": Illustrator,
    "indesign": InDesign,
    "photoshop": Photoshop,
    "premiere": Premiere,
}


class ReplayError(AssertionError):
    """Raised when a replay fixture no longer matches facade behavior."""


class ReplayClient:
    def __init__(self, fixture_name: str, exchanges: Sequence[Dict[str, Any]], target: str = "default") -> None:
        self.fixture_name = fixture_name
        self.exchanges = list(exchanges)
        self.target = target
        self.calls: List[Dict[str, Any]] = []
        self._index = 0

    def call(
        self,
        host: str,
        namespace: str,
        method: str,
        args: Optional[Sequence[Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
    ) -> Any:
        actual = {
            "host": host,
            "namespace": namespace,
            "method": method,
            "args": list(args or []),
            "options": options or {},
            "target": target,
        }
        self.calls.append(actual)
        if self._index >= len(self.exchanges):
            raise ReplayError(f"{self.fixture_name}: unexpected call {actual}")
        exchange = self.exchanges[self._index]
        self._index += 1
        expected = exchange.get("request", {})
        for key in ("host", "namespace", "method", "args", "options"):
            if actual[key] != expected.get(key, [] if key == "args" else {} if key == "options" else None):
                raise ReplayError(
                    f"{self.fixture_name}: call {self._index} field {key} expected {expected.get(key)!r}, got {actual[key]!r}"
                )
        if "target" in expected and actual["target"] != expected["target"]:
            raise ReplayError(
                f"{self.fixture_name}: call {self._index} target expected {expected['target']!r}, got {actual['target']!r}"
            )
        return exchange.get("response", {}).get("result")

    def assert_consumed(self) -> None:
        if self._index != len(self.exchanges):
            raise ReplayError(
                f"{self.fixture_name}: consumed {self._index} exchanges, expected {len(self.exchanges)}"
            )


def load_fixture(path: pathlib.Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReplayError(f"{path}: fixture must be an object")
    return payload


def run_fixture(path: pathlib.Path) -> Dict[str, Any]:
    fixture = load_fixture(path)
    name = str(fixture.get("name") or path.stem)
    host = fixture.get("host")
    if host not in FACADE_BY_HOST:
        raise ReplayError(f"{name}: unsupported host {host!r}")
    exchanges = fixture.get("exchanges")
    if not isinstance(exchanges, list):
        raise ReplayError(f"{name}: exchanges must be a list")
    script = fixture.get("script")
    if not isinstance(script, str) or not script.strip():
        raise ReplayError(f"{name}: script must be a non-empty string")

    client = ReplayClient(name, exchanges, target=str(fixture.get("target", "default")))
    app = FACADE_BY_HOST[host](client=client)
    stdout = io.StringIO()
    globals_payload = {"app": app}
    with contextlib.redirect_stdout(stdout):
        exec(compile(script, str(path), "exec"), globals_payload, {})
    client.assert_consumed()

    stdout_lines = stdout.getvalue().splitlines()
    expected_stdout = fixture.get("expectedStdout", [])
    if stdout_lines != expected_stdout:
        raise ReplayError(f"{name}: stdout expected {expected_stdout!r}, got {stdout_lines!r}")
    return {"name": name, "calls": client.calls, "stdout": stdout_lines}


def iter_fixture_paths(paths: Sequence[pathlib.Path]) -> Iterable[pathlib.Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(path.glob("*.json"))
        elif path.suffix == ".json":
            yield path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Replay Python facade fixtures")
    parser.add_argument("paths", nargs="+", type=pathlib.Path)
    args = parser.parse_args(argv)

    paths = list(iter_fixture_paths(args.paths))
    if not paths:
        print("no replay fixtures found", file=sys.stderr)
        return 1
    try:
        results = [run_fixture(path) for path in paths]
    except ReplayError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for result in results:
        print(f"replayed {result['name']}: {len(result['calls'])} calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
