import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {HtmlValidate} from 'html-validate';
import {loadManuscripts, publicRoot, publicFile, renderFolio, folioUrl, readerUrl} from './build_folio_pages.mjs';

const validator = new HtmlValidate({extends:['html-validate:recommended'],rules:{'no-inline-style':'off'}});
const manuscripts = await loadManuscripts();
let count=0, links=0;
for (const manuscript of manuscripts) {
 const {data,doc}=manuscript;
 const folios = new Set(data.pages.map(p=>p.folio+'.html'));
 const generated = (await fs.readdir(path.join(publicRoot,'rukopisy',doc.id))).filter(f=>folios.has(f));
 assert.equal(generated.length,data.pages.length);
 for(let i=0;i<data.pages.length;i++){
  const header=data.pages[i],page=JSON.parse(await fs.readFile(await publicFile(header.data.replace(/^\//, '')),'utf8'));
  const file=path.join(publicRoot,'rukopisy',doc.id,header.folio+'.html'),html=await fs.readFile(file,'utf8');
  const report=await validator.validateString(html,file);
  assert.ok(report.valid,JSON.stringify(report.results.flatMap(r=>r.messages).slice(0,5))+' '+header.folio);
  assert.equal(html,renderFolio(manuscript,page,i),'Generated output drift');
  assert.ok(html.includes('rel="canonical" href="'+folioUrl(doc,page.folio)+'"'));
  assert.ok(!html.includes('<script'),'Folio must be readable without JavaScript');
  assert.ok(html.includes('href="'+readerUrl(doc,page.folio)+'"'));
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(ids.length,new Set(ids).size,'Duplicate HTML IDs');
  for(const line of page.lines) assert.ok(ids.includes(line.id),'Missing source anchor');
  if(page.blank)assert.ok(html.includes('Bez vybraného hlavního textu.'));
  else if(page.kind==='binding'&&!page.lines.length)assert.ok(html.includes('Zatím nepřepsáno.'));
  for(const match of html.matchAll(/href="([^"]+)"/g)){
   const href=match[1].replaceAll('&amp;','&'),url=new URL(href,folioUrl(doc,page.folio));
   if(url.origin!==manuscript.origin)continue;
   if(!url.pathname.includes('.')){
    assert.ok(url.pathname==='/' || url.pathname==='/rukopis' || url.pathname==='/summary' || await fs.access(path.join(publicRoot,url.pathname+'.html')).then(()=>true,()=>false),'Missing clean URL '+href);
   }else assert.ok(await fs.access(path.join(publicRoot,url.pathname)).then(()=>true,()=>false),'Missing asset '+href);
   if(href.startsWith('#'))assert.ok(ids.includes(url.hash.slice(1)),'Missing fragment anchor '+href);
   links++;
  }
  count++;
 }
}
assert.equal(manuscripts.find(m=>m.doc.id==='vkol-m-ii-220').data.pages.length,677,'M II 220 acceptance corpus');
const sitemap=await fs.readFile(path.join(publicRoot,'sitemap.xml'),'utf8');
const sitemapUrls=new Set(manuscripts.flatMap(m=>[m.doc.uri,m.doc.reader,...m.data.pages.map(p=>folioUrl(m.doc,p.folio))]));sitemapUrls.add(manuscripts[0].origin+'/');sitemapUrls.add(manuscripts[0].origin+'/summary');
for(const {data,origin} of manuscripts) if(data.summary_url)sitemapUrls.add(new URL(data.summary_url,origin).href);
assert.equal((sitemap.match(/<url>/g)||[]).length,sitemapUrls.size);
assert.ok((await fs.readFile(path.join(publicRoot,'robots.txt'),'utf8')).includes('Sitemap: https://rukopisy.digitalizaty.cz/sitemap.xml'));
await assert.rejects(publicFile('../package.json'),/escapes/);
const doc={id:'vkol-m-ii-153',uri:'https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-153',reader:'https://rukopisy.digitalizaty.cz/rukopis?doc=vkol-m-ii-153'};
assert.equal(folioUrl(doc,'39r','f39r_l001'),'https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-153/39r#f39r_l001');
assert.equal(readerUrl(doc,'39r','f39r_l001'),'https://rukopisy.digitalizaty.cz/rukopis?doc=vkol-m-ii-153#39r-f39r_l001');
const viewer=await fs.readFile(path.join(publicRoot,'rukopis.js'),'utf8');
assert.match(viewer,/function folioCanonicalUrl/);assert.match(viewer,/history\.replaceState\(null, '', permalink\(\)\)/,'Legacy viewer state must remain');
assert.match(viewer,/\$\('#permalink'\)\.value = folioCanonicalUrl\(\)/);
console.log(JSON.stringify({status:'passed',html_pages:count,resolved_local_links:links,no_js_folio_pages:true,registry_ready:true}));
