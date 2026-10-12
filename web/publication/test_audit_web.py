"""Small synthetic fixtures test independent failure modes, without research media."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from audit_web import audit, report_path, sha, MEDIA, DOC


class OverlayAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source, self.base, self.staged = [root / name for name in ('source', 'base', 'staged')]
        for p in (self.source, self.base, self.staged):
            p.mkdir()
        self.report = root / 'build-report.json'
        self.raw = {'lines': [{'id':'f5r_l001','bbox':[1,2,3,4], 'candidates':{'catmus':{'raw':'⁊ ꝰ'},'medusa':{'raw':'amoris'}}}]}
        self.dump(self.source/'manifest.json', {'pages':[{'folio':'5r','original_sha256':'a'*64,'width':100,'height':200}]})
        self.dump(self.source/'pages/5r/comparison.json', self.raw)
        self.page = {'folio':'5r','document_id':DOC,'source_sha256':'a'*64,'width':100,'height':200,
                     'preview':MEDIA+'previews/5r.webp','tiles':{'tilesUrl':MEDIA+'tiles/5r/'},
                     'lines':[{'id':'f5r_l001','source_segment_ids':['f5r_l001'],'bbox':[1,2,3,4],
                               'raw_htr':{'catmus':'⁊ ꝰ','medusa':'amoris'},'image':MEDIA+'crops/5r/f5r_l001.webp'}],
                     'passages':[{'line_ids':['f5r_l001'],'latin':'amoris','czech':'lásky'}],
                     'downloads':[{'name':'JSON','href':'/data/'+DOC+'/5r/comparison.json'}]}
        self.page_path = self.staged/('data/'+DOC+'/5r/page.json')
        self.dump(self.page_path, self.page)
        self.dump(self.staged/('data/'+DOC+'/5r/comparison.json'),self.raw)
        self.dump(self.staged/('data/'+DOC+'/manifest.json'),{'document':{'id':DOC},'publication_ready':False,
                  'pages':[{'folio':'5r','data':'/data/'+DOC+'/5r/page.json','segments':1}], 'counts':{'lines':1}})
        legacy = {'pages':[{'folio':str(i)} for i in range(677)],'counts':{'pages':677},'document':{'id':'vkol-m-ii-220'}}
        for p in (self.base, self.staged):
            (p/'pilot-data.js').write_text('window.PILOT_DATA = '+json.dumps(legacy)+';\n',encoding='utf8')
            self.text(p/'tei/vkol-m-ii-220.xml','<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>unchanged</p></body></text></TEI>')
        self.text(self.base/'styles.css','body{}')
        self.text(self.base/'index.html','<!doctype html><html><body></body></html>')
        self.text(self.staged/'index.html','<!doctype html><html><head><link href="/styles.css"></head><body><a href="/">Home</a></body></html>')
        self.dump(self.report,{'status':'passed','source':str(self.source),'output':str(self.staged),'publication_ready':False,
                  'counts':{'lines':1},'required_missing':[], 'base_files_sha256':{'index.html':sha(self.base/'index.html')}})

    def text(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(value,encoding='utf8')

    def dump(self,path,value):
        self.text(path,json.dumps(value,ensure_ascii=False))

    def run_audit(self):
        return audit(self.source,self.base,self.staged,self.report)

    def change_page(self,change):
        p=copy.deepcopy(self.page)
        change(p)
        self.dump(self.page_path,p)

    def test_valid_overlay_uses_base_dependencies(self):
        result=self.run_audit()
        self.assertEqual(result['status'],'passed')
        self.assertEqual(result['source_segments_unchanged'],1)
        self.assertEqual(result['legacy_pages_unchanged'],677)
        self.assertEqual(result['resolved_html_links'],2)

    def test_both_raw_outputs_and_bbox_are_checked(self):
        for model in ('catmus','medusa'):
            with self.subTest(model=model):
                self.change_page(lambda p:p['lines'][0]['raw_htr'].__setitem__(model,'changed'))
                with self.assertRaisesRegex(ValueError,'Raw HTR changed'):
                    self.run_audit()
        self.change_page(lambda p:p['lines'][0]['bbox'].__setitem__(0,99))
        with self.assertRaisesRegex(ValueError,'Bounding box changed'):
            self.run_audit()

    def test_coverage_requires_exact_ids(self):
        self.change_page(lambda p:p['passages'][0].__setitem__('line_ids',['another-id']))
        with self.assertRaisesRegex(ValueError,'exact source ID'):
            self.run_audit()

    def test_download_bytes_and_local_links_are_checked(self):
        download=self.staged/('data/'+DOC+'/5r/comparison.json')
        self.text(download,'{}')
        with self.assertRaisesRegex(ValueError,'Copied raw source bytes changed'):
            self.run_audit()
        self.dump(download,self.raw)
        self.text(self.staged/'index.html','<a href="/missing">Missing</a>')
        with self.assertRaisesRegex(ValueError,'Missing local link'):
            self.run_audit()

    def test_namespace_and_paths_cannot_escape(self):
        self.change_page(lambda p:p['downloads'][0].__setitem__('href','/data/vkol-m-ii-220/secret.txt'))
        with self.assertRaisesRegex(ValueError,'Download namespace mismatch'):
            self.run_audit()
        self.dump(self.page_path,self.page)
        self.text(self.staged/'index.html','<a href="../../outside.txt">Outside</a>')
        with self.assertRaisesRegex(ValueError,'escapes'):
            self.run_audit()

    def test_base_and_legacy_data_are_protected(self):
        self.text(self.base/'index.html','changed baseline')
        with self.assertRaisesRegex(ValueError,'Baseline changed'):
            self.run_audit()
        build=json.loads(self.report.read_text())
        build['base_files_sha256']['index.html']=sha(self.base/'index.html')
        self.dump(self.report,build)
        self.text(self.base/'data/20v.json','{"raw":"unchanged"}')
        self.text(self.staged/'data/20v.json','{"raw":"changed"}')
        with self.assertRaisesRegex(ValueError,'Legacy underlying data overwritten'):
            self.run_audit()

    def test_media_and_credentials_are_rejected_without_echo(self):
        self.text(self.staged/'unexpected.webp','not an actual image')
        with self.assertRaisesRegex(ValueError,'Forbidden media'):
            self.run_audit()
        (self.staged/'unexpected.webp').unlink()
        synthetic='github'+'_pat_'+'x'*50
        self.text(self.staged/'accidental.txt',synthetic)
        with self.assertRaisesRegex(ValueError,'Credential signature found in') as ctx:
            self.run_audit()
        self.assertNotIn(synthetic,str(ctx.exception))

    def test_report_path_cannot_overwrite_inputs(self):
        with self.assertRaisesRegex(ValueError,'overlaps'):
            report_path(self.source/'reports',self.source,self.base,self.staged)


if __name__=='__main__':
    unittest.main()
