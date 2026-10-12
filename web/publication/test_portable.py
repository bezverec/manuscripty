"""Synthetic contract tests; no manuscript images or deployment involved."""
from pathlib import Path
from types import SimpleNamespace
import tempfile, unittest, json
from lxml import etree as ET
import build_web as b
import audit_interpretation as a


class AcceptForStructureOnly:
    def validate(self, tree):
        return True


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for d in ('source','base','legacy','pilot'):(self.root/d).mkdir()
        for f in ('schema.rng','supplier.xml'):(self.root/f).write_text('<x/>',encoding='utf8')
        self.args=SimpleNamespace(source=self.root/'source',base_public=self.root/'base',out=self.root/'out',rng=self.root/'schema.rng',supplier_metadata=self.root/'supplier.xml',legacy_metadata=self.root/'legacy',report_dir=self.root/'reports',pilot_source=self.root/'pilot',require_complete=True)

    def test_paths_and_no_stale_deletion(self):
        b.validate_paths(self.args)
        for target in (self.args.source,self.args.source/'nested',self.root):
            self.args.out=target
            with self.assertRaises(ValueError):b.validate_paths(self.args)
        self.args.out=self.root/'out';self.args.out.mkdir();(self.args.out/'keep.txt').write_text('keep')
        with self.assertRaises(ValueError):b.validate_paths(self.args)
        self.assertEqual((self.args.out/'keep.txt').read_text(),'keep')

    def test_report_cannot_overwrite_source(self):
        self.args.report_dir=self.args.base_public/'reports'
        with self.assertRaises(ValueError):b.validate_paths(self.args)

    def test_canonical_language_and_all_ids(self):
        obj={'language':'mul','lines':[{'id':'f96v_l004','language':'la','reconstruction_la':'Si vis sanari','include_in_main_text':True},{'id':'f96v_l007','language':'de','reconstruction_la':'Item wer','include_in_main_text':True}], 'translation_units':[{'id':'u1','line_ids':['f96v_l004'],'translation_cs':'Chceš-li'},{'id':'u2','line_ids':['f96v_l007'],'translation_cs':'Dále kdo'},{'id':'u3','line_ids':['f96v_l004','f96v_l007'],'translation_cs':'Směs'}]}
        result=b.adapt_interpretation(obj,[{'id':'f96v_l004'},{'id':'f96v_l007'}])
        self.assertEqual([p['language'] for p in result],['la','de','mul'])
        obj['lines'][1]['id']='WRONG'
        with self.assertRaises(ValueError):b.adapt_interpretation(obj,[{'id':'f96v_l004'},{'id':'f96v_l007'}])

    def test_existing_passage_language_wins(self):
        obj={'language':'la','passages':[{'id':'a','line_ids':['x'],'latin':'Item','czech':'Dále','language':'de'}]}
        self.assertEqual(b.adapt_interpretation(obj,[{'id':'x'}])[0]['language'],'de')

    def test_master_tei_version_and_pi(self):
        doc={'title':'M II153','uri':'https://example.invalid/document','reader':'https://example.invalid/reader','title_note_cs':'Source'}
        b.make_document_tei(self.root/'out',doc,[{'folio':'1r','label':'f.1r'}],[],AcceptForStructureOnly())
        p=self.root/'out/tei/vkol-m-ii-153.xml';raw=p.read_bytes()
        self.assertIn(b'<?xml-model href="/schemas/tei-p5-4.12.0/tei_all.rng"',raw)
        self.assertEqual(ET.parse(str(p)).getroot().get('version'),'4.12.0')
        self.assertIn(b'#1r',raw)

    def test_web_tei_preserves_raw_unicode_and_geometry(self):
        src=self.root/'raw.xml';src.write_text('<TEI xmlns="'+b.TEI+'"><teiHeader><encodingDesc/></teiHeader><facsimile><surface><graphic url="image.png"/><zone ulx="12"/></surface></facsimile><text><body><ab>ꝰ e\u0301 [uncertain?]</ab></body></text></TEI>',encoding='utf8')
        dest=self.root/'web.xml';b.make_web_tei(src,dest,'https://example.invalid/view#1r',AcceptForStructureOnly())
        old=ET.parse(str(src));new=ET.parse(str(dest));q=lambda x:'{'+b.TEI+'}'+x
        self.assertEqual(ET.tostring(old.find(q('text'))),ET.tostring(new.find(q('text'))))
        self.assertEqual(new.find('.//'+q('zone')).get('ulx'),'12')
        self.assertEqual(new.find('.//'+q('graphic')).get('url'),'https://example.invalid/view#1r')

    def test_require_complete_rejects_incomplete_manifest(self):
        b.dump(self.args.source/'manifest.json',{'pages':[],'status':'prepared'})
        # Minimal local RNG is only a synthetic fixture, not TEI validation.
        self.args.rng.write_text('<element xmlns="http://relaxng.org/ns/structure/1.0" name="x"><empty/></element>')
        with self.assertRaisesRegex(ValueError,'not complete'):a.audit(self.args.source,self.args.rng)

    def test_all_cli_paths_required(self):
        required=[x.dest for x in b.parser()._actions if x.required]
        self.assertEqual(set(required),{'source','base_public','out','rng','supplier_metadata','legacy_metadata','report_dir'})


if __name__=='__main__':unittest.main()
