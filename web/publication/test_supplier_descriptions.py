"""Check source fidelity, completeness, repeatability and safe catalogue links."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from lxml import etree as ET
import supplier_descriptions as s


class SupplierDescriptions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.public=Path(self.tmp.name)/'public'
        original=Path(__file__).resolve().parents[1]/'public'
        for relative in ('document.json','pilot-data.js','data/vkol-m-ii-153/document.json','data/vkol-m-ii-153/manifest.json','rukopisy/vkol-m-ii-220.html','rukopisy/vkol-m-ii-153.html'):
            target=self.public/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(original/relative,target)

    def test_complete_sources_and_idempotent_update(self):
        reports=s.update_descriptions(self.public)
        self.assertEqual([r['total_items'] for r in reports],[64,16])
        before={p.relative_to(self.public):p.read_bytes() for p in self.public.rglob('*') if p.is_file()}
        s.update_descriptions(self.public)
        self.assertEqual(before,{p.relative_to(self.public):p.read_bytes() for p in self.public.rglob('*') if p.is_file()})
        for ident in s.IDS:
            raw=(s.PACKAGE/'source-metadata'/(ident+'.xml')).read_bytes()
            self.assertEqual(raw,(self.public/'metadata'/ident/'supplier.xml').read_bytes())
            root=ET.fromstring(raw)
            data=json.loads((self.public/'metadata'/ident/'description.json').read_text(encoding='utf8'))
            self.assertEqual(data['header'],s.tree(root.find('teiHeader')))
            body=ET.HTML((self.public/'rukopisy'/(ident+'.html')).read_text(encoding='utf8'))
            visible=s.normalized(''.join(body.itertext()))
            for phrase in ('Fyzický popis','Vazba','Bibliografie','Skladba','Rozměry listu','Incipit','Explicit','Kolofon'):
                self.assertIn(phrase,visible)

    def test_identity_mismatch_rejected(self):
        path=self.public/'document.json'
        data=json.loads(path.read_text(encoding='utf8'));data['source_metadata']['sha256']='0'*64
        path.write_text(json.dumps(data),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'document identity'):
            s.update_descriptions(self.public)

    def test_link_mapping_and_escaped_metadata(self):
        block,item=s.renderer('vkol-m-ii-220',{'F001v','1r'})
        node=ET.fromstring('<note>&lt;script&gt;alert(1)&lt;/script&gt; <locus from="#IDf001v">předsádka</locus><author ref="javascript:alert(1)">autor</author></note>')
        markup=block(node);root=ET.HTML(markup)
        self.assertEqual(len(root.findall('.//script')),0)
        self.assertEqual([a.get('href') for a in root.findall('.//a')],['/rukopis#F001v'])
        self.assertIn('<script>alert(1)</script>',''.join(root.itertext()))

    def test_unknown_field_requires_explicit_mapping(self):
        block,_=s.renderer('vkol-m-ii-153',{'1r'})
        with self.assertRaisesRegex(ValueError,'Unmapped'):
            block(ET.fromstring('<unknown>Important new source field</unknown>'))


if __name__=='__main__':unittest.main()
