"""Whole-description TEI fidelity, IDs and protection of edition content."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from lxml import etree as ET
import enrich_document_tei as e


class EnrichTEI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Path(__file__).resolve().parents[1]/'public'
        cls.rng=ET.RelaxNG(ET.parse(str(cls.base/'schemas/tei-p5-4.12.0/tei_all.rng'),e.parser()))

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.public=Path(self.tmp.name)/'public'
        for ident in e.IDS:
            for rel in ('tei/'+ident+'.xml','metadata/'+ident+'/supplier.xml'):
                dest=self.public/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(self.base/rel,dest)

    def run_conversion(self):
        return e.convert(self.public,schema_path=self.base/'schemas/tei-p5-4.12.0/tei_all.rng',validator=self.rng)

    def test_complete_valid_descriptions_and_idempotence(self):
        before={i:(self.public/'tei'/(i+'.xml')).read_bytes() for i in e.IDS}
        report=self.run_conversion()
        self.assertEqual([r['msItems'] for r in report['manuscripts']],[64,16])
        after={i:(self.public/'tei'/(i+'.xml')).read_bytes() for i in e.IDS}
        self.run_conversion()
        self.assertEqual(after,{i:(self.public/'tei'/(i+'.xml')).read_bytes() for i in e.IDS})
        for i in e.IDS:
            original=ET.fromstring(before[i]);result=ET.fromstring(after[i])
            self.rng.assertValid(result)
            for tag in ('text','facsimile'):
                self.assertEqual(e.canonical(original.find(e.Q(tag))),e.canonical(result.find(e.Q(tag))))
            for tag in ('physDesc','bindingDesc','history','additional','msContents'):
                self.assertIsNotNone(result.find('.//'+e.Q(tag)))
            self.assertTrue(result.findall('.//'+e.Q('note')))
            self.assertIsNotNone(result.find('.//'+e.Q('classDecl')))
        first=ET.fromstring(after[e.IDS[0]])
        self.assertTrue(first.xpath('//t:locus[@from="#surface_F001v"]',namespaces=e.NS))

    def test_changed_supplier_rejected_without_writing_either_tei(self):
        before={i:(self.public/'tei'/(i+'.xml')).read_bytes() for i in e.IDS}
        source=self.public/'metadata'/e.IDS[1]/'supplier.xml';source.write_bytes(source.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Supplier source mismatch'):self.run_conversion()
        self.assertEqual(before,{i:(self.public/'tei'/(i+'.xml')).read_bytes() for i in e.IDS})


if __name__=='__main__':unittest.main()
