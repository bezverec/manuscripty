import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {HtmlValidate} from 'html-validate';
import {resolveReaderHash, renderSupplementalReadings, renderReadingAddenda} from './public/reader-core.mjs';
import {loadManuscripts, renderFolio} from './build_folio_pages.mjs';
import {makeProposal} from './public/proposal-core.mjs';
import {makeSegmentationProposal} from './public/segmentation-core.mjs';

const pages = [
  {folio:'83v', lines:[{id:'a'}, {id:'segment-with-hyphen'}]},
  {folio:'extra-83v', lines:[{id:'a'}, {id:'segment-with-hyphen'}]},
  {folio:'extra-84r'},
  {folio:'extra', lines:[{id:'83v'}]}
];
assert.deepEqual(resolveReaderHash(pages,'extra-83v'), {page:1,line:0});
assert.deepEqual(resolveReaderHash(pages,'extra-83v-segment-with-hyphen'), {page:1,line:1});
assert.deepEqual(resolveReaderHash(pages,'extra-84r-segment-with-hyphen'), {page:2,line:'segment-with-hyphen'});
assert.deepEqual(resolveReaderHash(pages,'83v-l2'), {page:0,line:1});
assert.deepEqual(resolveReaderHash(pages,'83v-l99'), {page:0,line:0});
assert.deepEqual(resolveReaderHash(pages,'unknown-83v'), {page:0,line:0});

const supplement = {id:'margin-1',image:'https://rukopisy-data.digitalizaty.cz/v2/vkol-m-i-259/supplement.webp',source_region_xyxy:[0,10,100,200],crop_rotation_ccw_degrees:90,reconstruction:'<script>Quid?</script>',translation_cs:'Co? & proč?',note_cs:'Nejisté čtení.'};
const reading = renderSupplementalReadings([supplement]);
assert.ok(reading.includes('&lt;script&gt;Quid?&lt;/script&gt;'));
assert.ok(reading.includes('Co? &amp; proč?'));
assert.ok(reading.includes('href="'+supplement.image+'"'));
assert.ok(!reading.includes('data-source-id'));
assert.ok(!reading.includes('data-passage'));
assert.ok(!renderSupplementalReadings([supplement], {language:'czech'}).includes('Quid?'));
assert.ok(!renderSupplementalReadings([supplement], {language:'latin'}).includes('Co?'));
assert.throws(()=>renderSupplementalReadings([{...supplement,image:'javascript:alert(1)'}]), /HTTPS/);

const doc = {id:'vkol-m-i-259',shelfmark:'M I 259',uri:'https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-i-259',reader:'https://rukopisy.digitalizaty.cz/rukopis?doc=vkol-m-i-259',repository:{name:'Vědecká knihovna v Olomouci'}};
const data = {document:doc,counts:{pages:1},pages:[{folio:'extra-83v'}]};
const manuscript = {entry:{id:doc.id,default_model:'catmus'},doc,data,origin:'https://rukopisy.digitalizaty.cz'};
const page = {folio:'extra-83v',language:'la',lines:[],passages:[],downloads:[],models:{},preview:supplement.image,supplemental_readings:[supplement]};
const html = renderFolio(manuscript,page,0);
assert.ok(html.includes('/vkol-m-i-259/extra-83v'));
assert.ok(html.includes('Samostatná obrazová čtení a české překlady'));
assert.ok(html.includes(reading));
assert.ok(!html.includes('id="margin-1"'), 'Supplement must not impersonate an HTR line');
const validator = new HtmlValidate({extends:['html-validate:recommended'],rules:{'no-inline-style':'off'}});
const report = await validator.validateString(html);
assert.ok(report.valid, JSON.stringify(report.results.flatMap(result=>result.messages)));

// Exercise the actual rendering functions with lightweight DOM fields. No browser/server.
const reader = await fs.readFile(new URL('./public/rukopis.js',import.meta.url),'utf8');
const readingFunction = reader.slice(reader.indexOf('  function renderReading() {'),reader.indexOf('  function renderProcessing() {'));
const linesFunction = reader.slice(reader.indexOf('  function renderLines() {'),reader.indexOf('  function renderAnalysis() {'));
const escape = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const passage = {id:'p1',title:'Pasáž',line_ids:['line-1'],latin:'Oratio.',czech:'Modlitba.',operations:[]};
const runtimePage = {...page,models:{catmus:'CATMuS'},lines:[{id:'line-1',raw_htr:{catmus:'Raw HTR'}}],passages:[passage]};
for (const scope of ['all','linked']) for (const language of ['both','latin','czech']) {
  const fields = {'#reading-scope':{value:scope},'#reading-language':{value:language},'#reading-passages':{innerHTML:''}};
  vm.runInNewContext(readingFunction+'\nrenderReading();',{$:selector=>fields[selector],page:()=>runtimePage,linkedPassages:()=>[passage],esc:escape,renderSupplementalReadings,renderReadingAddenda,selectedLine:()=>runtimePage.lines[0]});
  const output = fields['#reading-passages'].innerHTML;
  assert.ok(output.includes('id="reading-p1"'));
  assert.ok(output.includes('id="supplemental-margin-1"'));
  assert.ok(output.includes('<h2>Další obrazově čtené úseky strany</h2>'));
  assert.ok(output.includes('<h3>Samostatné čtení výřezu margin-1</h3>'));
  assert.equal(output.includes('Quid?'),language!=='czech');
  assert.equal(output.includes('Co?'),language!=='latin');
  assert.ok(!output.slice(output.indexOf('id="supplemental-')).includes('data-source-id'));
}
const lineFields = Object.fromEntries(['#htr-choice','#line-choice','#row-count','#lines'].map(id=>[id,{}]));
vm.runInNewContext(linesFunction+'\nrenderLines();',{$:selector=>lineFields[selector],page:()=>runtimePage,state:{model:'catmus',line:0},esc:escape,proposalLinks:()=>''});
assert.ok(lineFields['#lines'].innerHTML.includes('Raw HTR'));
assert.ok(!lineFields['#lines'].innerHTML.includes('margin-1'));
assert.ok(!lineFields['#lines'].innerHTML.includes('Quid?'));

const originalHash = 'a'.repeat(64), coordinateHash = 'b'.repeat(64);
const coordinate = {id:'pages/1r/image.png',sha256:coordinateHash,width:300,height:200,frame:0,derived_from_sha256:originalHash,original_tiff_frame:0,rotation_ccw_degrees:90,source_to_coordinate_pixel_edge_affine:[[0,1,0],[-1,0,200],[0,0,1]],bbox_format:'xywh',origin:'top-left'};
const proposalPage = {...runtimePage,document_id:doc.id,width:300,height:200,source_sha256:originalHash,source_original:'0001.tif',coordinate_source:coordinate,tiles:{tilesUrl:'https://example.org/tiles/'}};
proposalPage.lines = [{...runtimePage.lines[0],source_segment_ids:['original-1'],bbox:[5,5,30,20],image:supplement.image}];
const events = [];
const proposingFunctions = reader.slice(reader.indexOf('  function proposeHtr() {'),reader.indexOf('  function applyZoom() {'));
vm.runInNewContext(proposingFunctions+'\nproposeHtr(); proposeSegmentation();',{
  page:()=>proposalPage,selectedLine:()=>proposalPage.lines[0],DATA:{document:doc},state:{model:'catmus'},URL,location:{href:doc.reader},
  CustomEvent:class {constructor(type,options){this.type=type;this.detail=options.detail;}},window:{dispatchEvent:event=>events.push(event)}
});
assert.deepEqual(events.map(event=>event.type),['manuscripty:propose-htr','manuscripty:propose-segmentation']);
const htr = makeProposal(events[0].detail,'catmus','Edited HTR','Ověření podle obrazu.','test','2026-10-19T00:00:00Z');
const segmentation = makeSegmentationProposal(events[1].detail,'resize',['line-1'],[[5,5,31,21]],'Ověření podle obrazu.','test','2026-10-19T00:00:00Z');
assert.equal(htr.schema,'manuscripty-htr-proposal-v2');
assert.equal(segmentation.schema,'manuscripty-segmentation-proposal-v2');
assert.equal(htr.coordinate_source.sha256,coordinateHash);
assert.equal(segmentation.coordinate_source.rotation_ccw_degrees,90);

const temporary = await fs.mkdtemp(path.join(os.tmpdir(),'manuscripty-registry-'));
try {
  const registry = path.join(temporary,'registry.json');
  await fs.writeFile(registry,JSON.stringify({schema:'manuscripty-static-registry-v1',manuscripts:[{id:doc.id,manifest:'manifest.json',default_model:'catmus'}]}));
  await fs.writeFile(path.join(temporary,'manifest.json'),JSON.stringify(data));
  assert.equal((await loadManuscripts({root:temporary,registry}))[0].data.pages[0].folio,'extra-83v');
  data.pages[0].folio='../extra-83v';
  await fs.writeFile(path.join(temporary,'manifest.json'),JSON.stringify(data));
  await assert.rejects(loadManuscripts({root:temporary,registry}), /Unsafe folio/);
} finally { await fs.rm(temporary,{recursive:true,force:true}); }

// Exercise the actual runtime allowlist without network access or a browser.
const loader = await fs.readFile(new URL('./public/document-loader.js', import.meta.url),'utf8');
let fetched = '';
const context = {URL,location:{href:doc.reader},window:{},fetch:async url=>{fetched=url;return {ok:true,json:async()=>({document:doc,pages:[{folio:'1r'}]})};}};
vm.runInNewContext(loader,context);
await context.window.MANUSCRIPT_READY;
assert.equal(fetched,'/data/vkol-m-i-259/manifest.json?v=20261019-1');
assert.equal(context.window.PILOT_DATA.document.id,doc.id);
const homepage = await fs.readFile(new URL('./public/index.html',import.meta.url),'utf8');
const homeReport = await validator.validateString(homepage);
assert.ok(homeReport.valid,JSON.stringify(homeReport.results.flatMap(result=>result.messages)));
assert.equal([...homepage.matchAll(/class="catalogue-card"/g)].length,3);
assert.ok(homepage.includes('3 rukopisy · 1 245 snímků'));
assert.ok(homepage.includes('href="/rukopis?doc=vkol-m-i-259"'));
assert.ok(homepage.includes('/vkol-m-i-259/previews/1r.webp'));
console.log('Reader integration passed: hyphenated IDs, supplemental readings, static HTML, registry and runtime loader.');
