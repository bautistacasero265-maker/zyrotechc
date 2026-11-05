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


if __name__ == "__main__":
    unittest.main()
