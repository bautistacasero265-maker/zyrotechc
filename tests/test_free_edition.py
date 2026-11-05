import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
CATALOG = APP / "tweaks_free.json"
UI = APP / "zyrotech.py"
CORE = APP / "core.py"
BUILD = ROOT / "tools" / "build.py"


class FreeReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.ui = UI.read_text(encoding="utf-8")
        cls.core = CORE.read_text(encoding="utf-8")
        cls.build = BUILD.read_text(encoding="utf-8")

    def test_catalog_contains_only_free_tweaks(self):
        self.assertTrue(self.catalog)
        self.assertTrue(all(item.get("tier") == "free" for item in self.catalog))
        ids = [item.get("id") for item in self.catalog]
        self.assertEqual(len(ids), len(set(ids)))
        for item in self.catalog:
            self.assertTrue(item.get("name"))
            self.assertTrue(item.get("module"))
            self.assertIn(item.get("mode"), ("track", "once"))
            self.assertIsInstance(item.get("actions"), list)
            self.assertTrue(item["actions"])

    def test_public_ui_has_no_activation_or_private_modules(self):
        prohibited = (
            r"pro_features",
            r"public_key",
            r"machine_code",
            r"fingerprint\(",
            r"\blicense\b",
            r"\blicencia\b",
            r"\bactivaci[oó]n\b",
        )
        for pattern in prohibited:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.ui, flags=re.IGNORECASE))

    def test_free_build_packages_only_free_files(self):
        self.assertIn("tweaks_free.json", self.build)
        self.assertIn("ZyroTech-Free", self.build)
        self.assertNotIn("pro_features.py", self.build)
        self.assertNotIn("keygen", self.build)
        self.assertNotIn("cryptography", self.build)

    def test_free_applies_one_tweak_at_a_time(self):
        self.assertIn("if len(ap) > 1:", self.ui)
        self.assertIn("Aplicar uno", self.ui)

    def test_private_timer_and_ram_actions_are_not_in_free_core(self):
        self.assertNotIn("NtSetTimerResolution", self.core)
        self.assertNotIn("purge_standby", self.core)
        self.assertNotIn("memory_state", self.core)

    def test_python_sources_compile(self):
        for path in (UI, CORE, BUILD):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")


if __name__ == "__main__":
    unittest.main()
