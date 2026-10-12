"""Standard library smoke tests for the reference exporter."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("medieval_export", ROOT / "scripts" / "export.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExporterTests(unittest.TestCase):
    def example(self):
        return json.loads((ROOT / "assets" / "demo.json").read_text(encoding="utf-8"))

    def test_word_level_and_unicode(self):
        with tempfile.TemporaryDirectory() as tmp:
            word_level, pending = module.export(self.example(), tmp)
            self.assertTrue(word_level)
            self.assertEqual(pending, 3)
            alto = ET.parse(Path(tmp) / "diplomatic.alto.xml")
            tei = ET.parse(Path(tmp) / "edition.tei.xml")
            a = "{http://www.loc.gov/standards/alto/ns-v4#}"
            t = "{http://www.tei-c.org/ns/1.0}"
            strings = alto.findall(f".//{a}String")
            self.assertEqual(len(strings), 3)
            self.assertEqual(strings[1].get("SUBS_TYPE"), "Abbreviation")
            self.assertEqual(strings[1].get("SUBS_CONTENT"), "qualitates")
            self.assertEqual(strings[1].get("CONTENT"), "q̃litates")
            self.assertEqual(len(tei.findall(f".//{t}choice")), 2)
            self.assertIn("q̃litates", (Path(tmp) / "diplomatic.txt").read_text(encoding="utf-8"))
            self.assertIn("qualitates", (Path(tmp) / "expanded.txt").read_text(encoding="utf-8"))

    def test_line_level_fallback_no_fabricated_word_boxes(self):
        data = self.example()
        data["lines"][0]["words"][0]["bbox"] = None
        with tempfile.TemporaryDirectory() as tmp:
            word_level, _ = module.export(data, tmp)
            self.assertFalse(word_level)
            alto = ET.parse(Path(tmp) / "diplomatic.alto.xml")
            ns = "{http://www.loc.gov/standards/alto/ns-v4#}"
            tokens = alto.findall(f".//{ns}String")
            self.assertEqual(len(tokens), 1)
            self.assertNotIn("SUBS_TYPE", tokens[0].attrib)

    def test_non_abbreviation_correction_rejected(self):
        data = self.example()
        word = data["lines"][0]["words"][1]
        word["change_type"] = "none"
        with self.assertRaisesRegex(ValueError, "explicit abbreviation"):
            module.validate(data)

    def test_missing_geometry_rejected(self):
        data = self.example()
        data["lines"][0]["bbox"] = None
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "line bbox"):
                module.export(data, tmp)

    def test_duplicate_id_rejected(self):
        data = self.example()
        data["lines"][0]["words"][0]["id"] = data["lines"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            module.validate(data)

    def test_offline_tei_4_12_schema_accepts_export_and_rejects_unknown_element(self):
        with tempfile.TemporaryDirectory() as tmp:
            module.export(self.example(), tmp)
            output = Path(tmp) / "edition.tei.xml"
            result = module.validate_tei_file(output)
            self.assertTrue(result["relaxng_valid"])
            self.assertTrue(result["offline"])
            self.assertEqual(result["tei_version"], "4.12.0")
            self.assertFalse(result["schematron_checked"])
            cache = {}
            self.assertEqual(module.validate_tei_file(output, cache), result)
            self.assertEqual(module.validate_tei_file(output, cache), result)
            self.assertEqual(len(cache), 1)
            tree = ET.parse(output)
            ET.SubElement(tree.getroot(), "{http://www.tei-c.org/ns/1.0}notATEIElement")
            module.write_tei(tree, output)
            with self.assertRaises(ValueError):
                module.validate_tei_file(output)
            with self.assertRaises(ValueError):
                module.validate_tei_file(output, cache)

    def test_bad_box_rejected(self):
        data = self.example()
        data["lines"][0]["bbox"] = [10, 10, 1100, 40]
        with self.assertRaisesRegex(ValueError, "out of bounds"):
            module.validate(data)


if __name__ == "__main__":
    unittest.main()
