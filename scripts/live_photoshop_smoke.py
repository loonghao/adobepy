"""Optional live Photoshop smoke for self-hosted runners.

Normal CI skips this script unless ADOBEPY_LIVE_PHOTOSHOP=1 is set.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import Any, Callable


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from adobe.core import AdobePythonError  # noqa: E402
from adobe.photoshop import Photoshop  # noqa: E402


def run_phase(name: str, callback: Callable[[], Any]) -> Any:
    try:
        result = callback()
    except AdobePythonError as exc:
        print(f"phase={name} status=adobepy-error type={type(exc).__name__} code={exc.code} message={exc}")
        raise
    except Exception as exc:
        print(f"phase={name} status=error type={type(exc).__name__} message={exc}")
        raise
    print(f"phase={name} status=ok")
    return result


def hide_show_descriptor(obj: str, layer_id: int | str | None) -> dict[str, Any]:
    target = [{"_ref": "layer", "_enum": "ordinal", "_value": "targetEnum"}]
    if layer_id is not None:
        target = [{"_ref": "layer", "_id": layer_id}]
    return {"_obj": obj, "_target": target}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an optional live Photoshop adobepy smoke.")
    parser.add_argument("--mutate", action="store_true", help="Temporarily hide/show the active layer through modal batchPlay.")
    args = parser.parse_args(argv)

    if os.getenv("ADOBEPY_LIVE_PHOTOSHOP") != "1":
        print("skipped live Photoshop smoke: set ADOBEPY_LIVE_PHOTOSHOP=1 to enable")
        return 0

    mutate = args.mutate or os.getenv("ADOBEPY_LIVE_PHOTOSHOP_MUTATE") == "1"
    app = Photoshop()

    try:
        capabilities = run_phase("capabilities", app.capabilities)
        version = run_phase("version", lambda: app.version)
        document = run_phase("active-document", lambda: app.active_document)
        layers = run_phase("active-layers", lambda: list(app.active_layers))
        print(f"photoshop version={version!r} target={getattr(app.client, 'target', 'default')!r} capability_sessions={len(capabilities or [])}")
        print(f"active_document={getattr(document, 'name', None)!r} active_layers={[layer.name for layer in layers]}")

        if mutate:
            if not layers:
                print("phase=modal-mutation status=skipped reason=no-active-layer")
            else:
                layer = layers[0]

                def mutate_layer() -> None:
                    with app.execute_as_modal(command_name="adobepy live smoke hide/show"):
                        app.batch_play([hide_show_descriptor("hide", layer.id)], modal=True)
                        app.batch_play([hide_show_descriptor("show", layer.id)], modal=True)

                run_phase("modal-mutation", mutate_layer)
        else:
            print("phase=modal-mutation status=skipped reason=pass --mutate or set ADOBEPY_LIVE_PHOTOSHOP_MUTATE=1")
    except Exception:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
