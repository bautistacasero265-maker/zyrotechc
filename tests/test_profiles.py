import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import core
import pro_features

spec = importlib.util.spec_from_file_location("zyrotech_build", ROOT / "tools" / "build.py")
build_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_module)


def tweak(tid, name="Test tweak", module="Gaming", **extra):
    item = {
        "id": tid,
        "name": name,
        "module": module,
        "mode": "track",
        "risk": "normal",
        "badge": "",
        "locked": False,
        "req": {},
        "actions": [],
        "detect": [],
    }
    item.update(extra)
    return item


class ProfilePreviewTests(unittest.TestCase):
    def setUp(self):
        self.hw = {"nvidia": True, "amd": False, "intel": True, "cpu_intel": True,
                   "cpu_amd": False, "ram": 16, "ssd": True, "laptop": False,
                   "win11": True, "wifi": True}

    def test_profiles_are_nested(self):
        lite = pro_features.PROFILE_MODULES["Lite"]
        medium = pro_features.PROFILE_MODULES["Medio"]
        advanced = pro_features.PROFILE_MODULES["Avanzado"]
        self.assertLessEqual(lite, medium)
        self.assertLessEqual(medium, advanced)

    def test_active_partial_unknown_and_unsafe_states(self):
        items = [
            tweak("active"),
            tweak("partial"),
            tweak("inactive"),
            tweak("unknown"),
            tweak("unsafe", risk="extreme"),
            tweak("once", mode="once"),
            tweak("locked", locked=True),
        ]
        statuses = {"active": "active", "partial": "partial",
                    "inactive": "inactive", "unknown": "unknown"}
        with patch.object(core, "applicable", return_value=True):
            result = pro_features.profile_preview("Lite", items, self.hw, statuses)
        self.assertEqual([x["id"] for x in result["active"]], ["active"])
        self.assertEqual([x["id"] for x in result["partial"]], ["partial"])
        self.assertEqual({x["id"] for x in result["apply"]}, {"partial", "inactive"})
        self.assertEqual({x["id"] for x in result["incompatible"]}, {"unknown"})
        self.assertEqual({x["id"] for x in result["unsafe"]}, {"unsafe"})
        self.assertEqual({x["id"] for x in result["once"]}, {"once"})
        self.assertEqual({x["id"] for x in result["locked"]}, {"locked"})

    def test_incompatible_hardware_is_never_proposed(self):
        item = tweak("nvidia-only", req={"gpu": "nvidia"})
        with patch.object(core, "applicable", return_value=False):
            result = pro_features.profile_preview("Lite", [item], self.hw, {"nvidia-only": "inactive"})
        self.assertEqual(result["apply"], [])
        self.assertEqual([x["id"] for x in result["incompatible"]], ["nvidia-only"])


class FreeEditionPackagingTests(unittest.TestCase):
    def test_locked_pro_tweaks_keep_read_only_detection_but_not_actions(self):
        catalog = [
            {"id": "free", "tier": "free", "actions": [{"type": "reg"}], "detect": [{"type": "reg"}]},
            {"id": "pro", "tier": "pro", "actions": [{"type": "reg", "value": 1}], "detect": [{"type": "reg", "value": 1}]},
        ]
        staged = build_module.free_tweaks(catalog)
        self.assertIn("actions", staged[0])
        self.assertNotIn("actions", staged[1])
        self.assertTrue(staged[1]["locked"])
        self.assertEqual(staged[1]["detect"], [{"type": "reg", "value": 1}])



class DetectionPerformanceTests(unittest.TestCase):
    def test_scheduled_task_states_share_one_powershell_read_per_scan(self):
        import json

        core.clear_tweak_detection_cache()
        payload = json.dumps([
            {"TaskPath": "\\Microsoft\\Windows\\A", "TaskName": "TaskA", "State": "Disabled"},
            {"TaskPath": "\\Microsoft\\Windows\\B", "TaskName": "TaskB", "State": "Ready"},
        ])
        with patch.object(core, "IS_WIN", True), patch.object(core, "ps", return_value=payload) as powershell:
            self.assertEqual(core._scheduled_task_state("\\Microsoft\\Windows\\A", "TaskA"), "disabled")
            self.assertEqual(core._scheduled_task_state("\\Microsoft\\Windows\\B", "TaskB"), "ready")
            self.assertEqual(powershell.call_count, 1)
        core.clear_tweak_detection_cache()


class LightweightUiImportTests(unittest.TestCase):
    def test_main_ui_imports_without_starting_window(self):
        import zyrotech
        self.assertTrue(hasattr(zyrotech, "App"))
        self.assertEqual(zyrotech.BG, "#080D13")


class PublicKeyExportTests(unittest.TestCase):
    def test_export_public_uses_existing_private_key_without_rotating_it(self):
        import tempfile
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        key = Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as directory:
            private_path = Path(directory) / "seller.pem"
            public_path = Path(directory) / "public_key.py"
            private_bytes = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
            private_path.write_bytes(private_bytes)
            keygen_spec = importlib.util.spec_from_file_location(
                "zyrotech_keygen", ROOT / "tools" / "keygen.py"
            )
            keygen = importlib.util.module_from_spec(keygen_spec)
            keygen_spec.loader.exec_module(keygen)
            with patch.object(keygen, "PRIV", str(private_path)), patch.object(keygen, "PUBPY", str(public_path)):
                keygen.export_public()
                generated = {}
                exec(public_path.read_text(encoding="utf-8"), generated)
                expected = key.public_key().public_bytes(
                    serialization.Encoding.Raw, serialization.PublicFormat.Raw
                )
                import base64
                expected_b32 = base64.b32encode(expected).decode().rstrip("=")
                self.assertEqual(generated["PUBLIC_KEY_B32"], expected_b32)
                self.assertEqual(private_path.read_bytes(), private_bytes)


if __name__ == "__main__":
    unittest.main()
