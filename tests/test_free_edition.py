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

    def test_navigation_preserves_selection_and_search(self):
        self.assertIn("self.search_query = self.search.get()", self.ui)
        self.assertIn("self.risk_ack = bool(self.risk_ok.get())", self.ui)
        self.assertIn("def set_cat(self, m):", self.ui)
        category_method = self.ui.split("def set_cat(self, m):", 1)[1].split("def fill_list", 1)[0]
        self.assertNotIn('self.search_query = ""', category_method)

    def test_new_workspace_sidebar_layout(self):
        self.assertIn('self.navbar.grid(row=1, column=0, sticky="nsew")', self.ui)
        self.assertIn("MENÚ PRINCIPAL", self.ui)

    def test_category_navigation_updates_content_without_rebuilding_page(self):
        method = self.ui.split("def set_cat(self, m):", 1)[1].split("def fill_list", 1)[0]
        self.assertIn("self.fill_list()", method)
        self.assertNotIn('self.show("opt")', method)
        self.assertIn('getattr(self, "cat_buttons"', method)
        self.assertIn("self.category_title.configure(text=m)", method)

    def test_free_ui_has_refined_dashboard_and_tweak_cards(self):
        self.assertIn("Tu PC. Tu rendimiento.", self.ui)
        self.assertIn("ESTADO DEL SISTEMA", self.ui)
        self.assertIn("Resultados de búsqueda", self.ui)
        self.assertIn("status_bg =", self.ui)
        self.assertIn("LOCAL MODE", self.ui)
        self.assertIn("Controlá cada cambio", self.ui)

    def test_private_timer_and_ram_actions_are_not_in_free_core(self):
        self.assertNotIn("NtSetTimerResolution", self.core)
        self.assertNotIn("purge_standby", self.core)
        self.assertNotIn("memory_state", self.core)

    def test_python_sources_compile(self):
        for path in (UI, CORE, BUILD):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")


if __name__ == "__main__":
    unittest.main()
