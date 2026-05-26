import unittest

from adobe.core.errors import BrokerConnectionError, CapabilityError, UnauthorizedError
from adobe.dcc_mcp import (
    action_result,
    adobe_error,
    adobe_error_context,
    adobe_exception,
    adobe_success,
    recovery_suggestions,
    with_adobe,
)
from adobe.photoshop import Photoshop


class CapturingClient:
    target = "default"

    def __init__(self, fail=None):
        self.fail = fail
        self.calls = []

    def call(self, host, namespace, method, args=None, options=None, target=None):
        self.calls.append((host, namespace, method, list(args or []), options or {}, target))
        if self.fail is not None:
            raise self.fail
        if namespace == "document" and method == "getActive":
            return {"id": 1, "name": "Mock.psd"}
        if namespace == "document" and method == "getActiveLayers":
            return [{"id": 11, "name": "Hero"}, {"id": 12, "name": "Shadow"}]
        return {"ok": True}


class DccMcpIntegrationTests(unittest.TestCase):
    def test_dcc_style_skill_calls_photoshop_without_host(self):
        app = Photoshop(client=CapturingClient())

        result = action_result(
            "Listed active Photoshop layers",
            lambda: {"layers": [layer.name for layer in app.activeLayers]},
            prompt="Use the layer names in the next Photoshop operation.",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Listed active Photoshop layers")
        self.assertEqual(result["context"]["layers"], ["Hero", "Shadow"])
        self.assertEqual(result["prompt"], "Use the layer names in the next Photoshop operation.")

    def test_action_result_maps_adobepy_errors(self):
        app = Photoshop(client=CapturingClient(BrokerConnectionError("broker down")))

        result = action_result("Listed layers", lambda: list(app.activeLayers))

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Adobe operation failed")
        self.assertEqual(result["context"]["adobepy"]["error_type"], "BrokerConnectionError")
        self.assertTrue(result["context"]["adobepy"]["retryable"])
        self.assertIn("ADOBEPY_BROKER_URL", result["context"]["possible_solutions"][0])

    def test_error_context_exposes_codes_and_diagnostics(self):
        error = CapabilityError(
            "missing method",
            data={"namespace": "document"},
            diagnostics={"traceId": "trace-1"},
        )

        context = adobe_error_context(error)

        self.assertEqual(context["error_code"], -32003)
        self.assertEqual(context["data"], {"namespace": "document"})
        self.assertEqual(context["diagnostics"], {"traceId": "trace-1"})
        self.assertFalse(context["retryable"])

    def test_error_helpers_accept_exceptions_and_decorator(self):
        success_result = adobe_success("Done", count=1)
        self.assertTrue(success_result["success"])
        self.assertEqual(success_result["context"], {"count": 1})

        raw_error = adobe_error(
            "Plain error",
            "bad input",
            possible_solutions=["Use a valid layer name"],
            layer_name="x",
        )
        self.assertFalse(raw_error["success"])
        self.assertEqual(raw_error["context"]["layer_name"], "x")
        self.assertEqual(raw_error["context"]["possible_solutions"], ["Use a valid layer name"])

        error_result = adobe_error("Unauthorized", UnauthorizedError("bad token"))
        self.assertFalse(error_result["success"])
        self.assertEqual(error_result["context"]["adobepy"]["error_code"], -32009)

        exception_result = adobe_exception(CapabilityError("missing"), include_traceback=False)
        self.assertFalse(exception_result["success"])
        self.assertEqual(exception_result["context"]["adobepy"]["error_type"], "CapabilityError")

        @with_adobe("Photoshop skill failed")
        def fail():
            raise CapabilityError("unsupported")

        self.assertEqual(fail()["message"], "Photoshop skill failed")

        @with_adobe()
        def succeed():
            return adobe_success("Still ok")

        self.assertTrue(succeed()["success"])

    def test_scalar_results_and_generic_recovery(self):
        scalar_result = action_result("Got count", lambda: 3, result_key="count", host="photoshop")
        self.assertEqual(scalar_result["context"]["count"], 3)
        self.assertEqual(scalar_result["context"]["host"], "photoshop")

        empty_result = action_result("No payload", lambda: None, result_key=None)
        self.assertEqual(empty_result["context"], {})

        generic_error = RuntimeError("boom")
        self.assertEqual(adobe_error_context(generic_error), {"error_type": "RuntimeError", "retryable": False})
        self.assertEqual(
            recovery_suggestions(generic_error),
            ["Check the exception details and retry if the host state changed."],
        )


if __name__ == "__main__":
    unittest.main()
