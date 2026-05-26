"""Validate that Python wheels keep the project-wide compatibility contract."""

from __future__ import annotations

import argparse
import pathlib
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


PURE_PYTHON_TAG = ("py3", "none", "any")
ABI3_PY38_TAG = ("cp38", "abi3")


class WheelCompatibilityError(ValueError):
    """Raised when a wheel filename does not match the supported tags."""


@dataclass(frozen=True)
class WheelTags:
    python: str
    abi: str
    platform: str


def parse_wheel_tags(filename: str) -> WheelTags:
    if not filename.endswith(".whl"):
        raise WheelCompatibilityError(f"{filename!r} is not a wheel")
    stem = filename[:-4]
    parts = stem.rsplit("-", 3)
    if len(parts) != 4:
        raise WheelCompatibilityError(f"{filename!r} is not a valid wheel filename")
    return WheelTags(python=parts[1], abi=parts[2], platform=parts[3])


def assert_compatible_wheel_name(filename: str) -> None:
    tags = parse_wheel_tags(filename)
    if (tags.python, tags.abi, tags.platform) == PURE_PYTHON_TAG:
        return
    python_tags = set(tags.python.split("."))
    abi_tags = set(tags.abi.split("."))
    if ABI3_PY38_TAG[0] in python_tags and ABI3_PY38_TAG[1] in abi_tags:
        return
    raise WheelCompatibilityError(
        f"{filename!r} must be a pure py3-none-any wheel or a native cp38-abi3 wheel"
    )


def iter_wheels(paths: Sequence[pathlib.Path]) -> Iterable[pathlib.Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(path.glob("*.whl"))
        elif path.suffix == ".whl":
            yield path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check adobepy wheel tags. Native extensions must use abi3-py38."
    )
    parser.add_argument("paths", nargs="+", type=pathlib.Path, help="Wheel files or directories")
    args = parser.parse_args(argv)

    wheels = list(iter_wheels(args.paths))
    if not wheels:
        print("no wheels found", file=sys.stderr)
        return 1

    failures: List[str] = []
    for wheel in wheels:
        try:
            assert_compatible_wheel_name(wheel.name)
        except WheelCompatibilityError as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    for wheel in wheels:
        print(f"compatible wheel: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
