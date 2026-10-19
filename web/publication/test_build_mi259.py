"""Offline contracts for the third-manuscript adapter; fixtures are synthetic."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from lxml import etree as E
import build_mi259 as b

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='mi259-adapter-');self.root=Path(self.tmp.name)
        self.entry={'folio':'extra-83v','source':r'Z:\source\extra.TIF','original_sha256':'a'*64,'width':5600,'height':3900,'language':'la'}
        self.coord={'id':'vkol-m-i-259_extra-83v_coordinate','sha256':'b'*64,'width':5600,'height':3900,'frame':0,'derived_from_sha256':'a'*64,'original_tiff_frame':0,'rotation_ccw_degrees':90,'source_to_coordinate_pixel_edge_affine':[[0,1,0],[-1,0,3900],[0,0,1]],'bbox_format':'xywh','origin':'top-left','local_path':'private.png','model_input':{'sha256':'c'*64,'masked_pilot':True}}
        self.comparison={'lines':[{'id':'fextra-83v_l001','bbox_xyxy':[10,20,110,50],'boundary':[],'baseline':[],'candidates':{'catmus':{'raw':'ꝑ ã\n'},'medusa':{'raw':'per a','hit_token_limit':True,'decoding_recovery':{'repetition_penalty':1.08}}}}]}
        self.interpretation={'units':[{'id':'u_extra-83v_001','start':1,'end':1,'reconstruction':'[per?] a','translation_cs':'[skrze?] a','note_cs':'Nejisté.'}],'language':'la','supplemental_readings':[{'id':'margin','source_region_xyxy':[0,0,10,20],'crop_rotation_ccw_degrees':90,'image':'local-native.png','reconstruction':'[…]','translation_cs':'[…]','note_cs':'Samostatný obrazový návrh.'}]}
    def tearDown(self):self.tmp.cleanup()
    def test_physical_order_is_complete_and_does_not_merge_extras(self):
        ids=b.physical_ids();self.assertEqual(len(ids),371);self.assertEqual(len(set(ids)),371)
        self.assertEqual(ids[:4],['FC','FS','F001R','F001V']);self.assertEqual(ids[-5:],['B001R','B001V','BS','BC','SP'])
        self.assertEqual(ids[ids.index('83v'):ids.index('84v')+1],['83v','extra-83v','84r','extra-84r','84v'])
    def test_coordinate_whitelist_and_pixel_edge_rotation(self):
        c=b.coordinate_source(self.coord,self.entry);self.assertEqual(set(c),set(b.COORD_FIELDS));self.assertNotIn('local_path',c);self.assertNotIn('model_input',c)
        c['source_to_coordinate_pixel_edge_affine'][0][0]=3;self.assertEqual(self.coord['source_to_coordinate_pixel_edge_affine'][0][0],0)
        broken=copy.deepcopy(self.coord);broken['source_to_coordinate_pixel_edge_affine'][1][2]=3899
        with self.assertRaisesRegex(ValueError,'pixel-edge'):b.coordinate_source(broken,self.entry)
    def test_unicode_ids_ranges_and_supplemental_stay_separate(self):
        page=b.page_data(self.entry,self.comparison,self.interpretation,b.coordinate_source(self.coord,self.entry));line=page['lines'][0];p=page['passages'][0]
        self.assertEqual(line['bbox'],[10,20,100,30]);self.assertEqual(line['raw_htr']['catmus'],'ꝑ ã\n')
        self.assertEqual(p['line_ids'],['fextra-83v_l001']);self.assertEqual(p['latin'],self.interpretation['units'][0]['reconstruction'])
        self.assertEqual(p['czech'],self.interpretation['units'][0]['translation_cs']);self.assertEqual(page['source_original'],'EX/extra.TIF')
        self.assertIn('medusa_token_limit',line['flags']);self.assertIn('medusa_changed_decoding_unreviewed',line['flags']);self.assertIn('1,08',line['note'])
        supplemental=page['supplemental_readings'][0];self.assertNotIn('line_ids',supplemental);self.assertNotIn('raw_htr',supplemental)
        self.assertEqual(supplemental['image'],b.MEDIA+'/supplemental/extra-83v/margin.webp')
        self.assertEqual(page['tiles']['tilesUrl'],b.MEDIA+'/tiles/extra-83v/')
    def test_bad_coverage_and_geometry_rejected(self):
        bad=copy.deepcopy(self.interpretation);bad['units'][0]['start']=2
        with self.assertRaisesRegex(ValueError,'coverage'):b.page_data(self.entry,self.comparison,bad,{})
        bad=copy.deepcopy(self.comparison);bad['lines'][0]['bbox_xyxy']=[0,0,5601,10]
        with self.assertRaisesRegex(ValueError,'box'):b.page_data(self.entry,bad,self.interpretation,{})
    def gate_fixture(self):
        ids=b.physical_ids();pilots=set(ids[4:14]);entries=[{'folio':f,'reused_pilot':f in pilots} for f in ids]
        b.dump(self.root/'manifest.json',{'pages':entries})
        b.dump(self.root/'progress.json',{'status':'complete_with_review','total_scans':371,'both_models':371,'author_drafts':371,'interpretation_exported':371,'pages':[{'folio':f,'both_models':True,'author_draft_available':True,'interpretation_exported':True} for f in ids]})
        for name,key in [('full-output-validation.json','validated_pages'),('final-source-validation.json','validated_sources')]:b.dump(self.root/name,{'status':'passed','errors':[],key:371,'pages':[{'folio':f} for f in ids]})
        audited=[]
        for f in ids:
            p=self.root/'interpretation'/f'{f}.author.json';b.dump(p,{'units':[]});b.dump(self.root/'pages'/f/'comparison.json',{'lines':[]})
            if f not in pilots:audited.append({'folio':f,'author_sha256':b.sha(p)})
        b.dump(self.root/'interpretation-validation.json',{'validated_drafts':361,'errors':[],'pages':audited,'complete_manuscript':False})
        b.dump(self.root/'pilot-evidence-validation.json',{'status':'passed','pages':[{'folio':f} for f in pilots]})
        b.dump(self.root/'publication-coordinate-sources/index.json',{'status':'passed','pages':{f:{} for f in ids}})
    def test_complete_gates_and_stale_draft_rejection(self):
        self.gate_fixture();self.assertEqual(len(b.publication_gate(self.root)[1]),371)
        b.dump(self.root/'interpretation/15r.author.json',{'units':['changed']})
        with self.assertRaisesRegex(ValueError,'changed after audit'):b.publication_gate(self.root)
    def test_partial_audits_and_processing_fail_closed(self):
        self.gate_fixture();p=b.read(self.root/'progress.json');p['status']='in_progress';b.dump(self.root/'progress.json',p)
        with self.assertRaisesRegex(ValueError,'not complete'):b.publication_gate(self.root)
        p['status']='complete';b.dump(self.root/'progress.json',p);a=b.read(self.root/'full-output-validation.json');a['status']='passed_partial';b.dump(self.root/'full-output-validation.json',a)
        with self.assertRaisesRegex(ValueError,'Final audit'):b.publication_gate(self.root)
    def test_output_cannot_overlap_existing_or_research_directories(self):
        base=self.root/'base';source=self.root/'source';base.mkdir();source.mkdir();anchor=base/'old.txt';anchor.write_text('unchanged')
        args=SimpleNamespace(source=source,base_public=base,out=source/'overlay',report_dir=self.root/'reports',rng=self.root/'unused.rng')
        with self.assertRaisesRegex(ValueError,'disjoint'):b.build(args)
        self.assertEqual(anchor.read_text(),'unchanged');self.assertFalse(args.out.exists())
    def test_supplier_html_keeps_hand_binding_history_and_unmapped_loci(self):
        xml='<TEI><teiHeader><msDesc><msIdentifier><idno>M I 259</idno></msIdentifier><msContents><msItem n="1"><locus from="87r" to="88r">87r–88r</locus><title>Text</title></msItem></msContents><physDesc><handDesc><p>Několik rukou.</p></handDesc><bindingDesc><p>Vazba.</p></bindingDesc></physDesc><history><p>Historie.</p></history></msDesc></teiHeader></TEI>'
        path=self.root/'supplier.xml';path.write_text(xml,encoding='utf8');catalogue,description,structured=b.catalogue_html(path)
        self.assertIn('Několik rukou.',description);self.assertIn('Vazba.',description);self.assertIn('Historie.',description);self.assertNotIn('href=',catalogue);self.assertIn('87r–88r',catalogue)
        self.assertEqual(structured['description']['tag'],'msDesc')
    def test_web_tei_retains_msdesc_and_page_text(self):
        rng=Path(__file__).resolve().parents[1]/'public/schemas/tei-p5-4.12.0/tei_all.rng';validator=E.RelaxNG(b.parse(rng))
        xml='<TEI xmlns="'+b.TEI+'" version="4.12.0"><teiHeader><fileDesc><titleStmt><title>Fixture</title></titleStmt><publicationStmt><p>Local.</p></publicationStmt><sourceDesc><msDesc xml:id="ms-vkol-m-i-259"><msIdentifier><repository>VKOL</repository><idno>M I 259</idno></msIdentifier><physDesc><p>Binding and hand.</p></physDesc></msDesc></sourceDesc></fileDesc><encodingDesc><p>Original.</p></encodingDesc></teiHeader><facsimile><surface n="55v"><graphic url="../pages/55v/image.png"/></surface></facsimile><text><body><p>ꝑ ã [dubium?]</p></body></text></TEI>'
        path=self.root/'local.xml';path.write_text(xml,encoding='utf8');original=b.parse(path)
        b.web_tei(path,self.root/'page.web.xml','55v',{},validator)
        converted=b.parse(self.root/'page.web.xml');self.assertEqual(E.tostring(original.find('.//'+b.q('text')),method='c14n'),E.tostring(converted.find('.//'+b.q('text')),method='c14n'))
        b.web_tei(path,self.root/'document.xml',None,None,validator,document=True)
        converted=b.parse(self.root/'document.xml');self.assertEqual(E.tostring(original.find('.//'+b.q('msDesc')),method='c14n'),E.tostring(converted.find('.//'+b.q('msDesc')),method='c14n'))
        self.assertIn('not a complete scholarly edition',str(converted.xpath('//t:encodingDesc/t:p/text()',namespaces=b.NS)))
    def test_record_has_one_credit_and_theme(self):
        summary={'sections':[{'id':'ai-section-1','title':'AI','text_cs':'Výklad.','sources':[]}],'limits_cs':['Nejisté.']}
        text=b.render_record({'title':'M I259'},summary,'<article>Katalog</article>','<article>Popis</article>')
        self.assertEqual(text.count('class="digitization-support"'),1);self.assertLess(text.index('id="ai-shrnuti"'),text.index('class="digitization-support"'))
        self.assertIn('/theme.js?',text);self.assertIn('/theme.css?',text)

if __name__=='__main__':unittest.main()
