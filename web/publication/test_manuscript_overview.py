"""Verify source/AI distinction, stable evidence, fragment routes and atomic guards."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from lxml import etree
import manuscript_overview as m


class Overview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.public = Path(self.tmp.name)/'public'; self.public.mkdir()
        original = Path(__file__).resolve().parents[1]/'public'
        files = list(m.SUMMARY_PATHS.values()) + ['rukopisy/'+i+'.html' for i in m.IDS] + ['metadata/'+i+'/supplier.xml' for i in m.IDS]
        for relative in files:
            target = self.public/relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original/relative, target)
        self.before = {p: (self.public/p).read_bytes() for p in files}
        self.manifest = self.public.parent/'manifest.json'
        self.manifest.write_bytes(m.dump({'files': [{'path':'web/public/'+p, 'sha256':m.sha(self.before[p]), 'bytes':len(self.before[p])} for p in m.SUMMARY_PATHS.values()]}))

    def test_distinct_evidence_and_idempotence(self):
        m.update(self.public, self.manifest)
        first = {p.relative_to(self.public):p.read_bytes() for p in self.public.rglob('*') if p.is_file()}
        m.update(self.public, self.manifest)
        self.assertEqual(first, {p.relative_to(self.public):p.read_bytes() for p in self.public.rglob('*') if p.is_file()})
        for ident in m.IDS:
            before = json.loads(self.before[m.SUMMARY_PATHS[ident]])
            after = m.load(self.public/m.SUMMARY_PATHS[ident])
            key = 'sections' if ident == m.IDS[0] else 'themes'
            self.assertEqual(before[key], after[key])
            self.assertFalse(after['expert_review'])
            self.assertEqual(after['status'], 'proposed')
            xml = 'metadata/'+ident+'/supplier.xml'
            self.assertEqual(self.before[xml], (self.public/xml).read_bytes())
            page = etree.HTML((self.public/'rukopisy'/(ident+'.html')).read_bytes())
            ai = page.xpath('//article[@id="ai-shrnuti"]')[0]
            self.assertEqual(len(ai.xpath('.//details[@class="ai-theme"]')), 7)
            self.assertIn('Podle katalogu:', ''.join(ai.itertext()))
            self.assertIn('Interpretace AI:', ''.join(ai.itertext()))
            self.assertEqual(len(page.xpath('//p[contains(@class,"source-label")]')), 2)
            for anchor in ('zdrojovy-popis', 'katalogovy-obsah'):
                old = etree.HTML(self.before['rukopisy/'+ident+'.html'])
                # Full inherited catalogue prose still present; only labels may be added.
                old_text = ' '.join(''.join(old.xpath('//article[@id=$id]', id=anchor)[0].itertext()).split())
                new_text = ' '.join(''.join(page.xpath('//article[@id=$id]', id=anchor)[0].itertext()).split())
                self.assertIn(old_text, new_text)
        rules = (self.public/'_redirects').read_text('utf8').splitlines()
        self.assertEqual(len(rules), 4)
        self.assertTrue(all('#' not in r for r in rules), 'Incoming theme fragments must remain intact')

    def test_unexpected_second_summary_rejects_before_writes(self):
        p = self.public/m.SUMMARY_PATHS[m.IDS[1]]
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'prior summary hash'):
            m.update(self.public, self.manifest)
        self.assertEqual(self.before[m.SUMMARY_PATHS[m.IDS[0]]], (self.public/m.SUMMARY_PATHS[m.IDS[0]]).read_bytes())
        self.assertFalse((self.public/'_redirects').exists())

    def test_supplier_mismatch_rejects_before_writes(self):
        p = self.public/'metadata'/m.IDS[1]/'supplier.xml'
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'Supplier context SHA'):
            m.update(self.public, self.manifest)
        for path in m.SUMMARY_PATHS.values():
            self.assertEqual(self.before[path], (self.public/path).read_bytes())


if __name__ == '__main__':
    unittest.main()
