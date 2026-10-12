/** Exercise Pagefind's real browser API and WASM with local fetch, without a server. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {publicRoot,loadManuscripts} from './build_folio_pages.mjs';

const entry=JSON.parse(await fs.readFile(path.join(publicRoot,'pagefind/pagefind-entry.json'),'utf8'));
const manuscripts=await loadManuscripts();const expected=manuscripts.reduce((n,m)=>n+m.data.pages.length,0);
assert.equal(entry.version,'1.4.0');assert.equal(entry.languages.cs.page_count,expected);
const nativeFetch=globalThis.fetch;
globalThis.fetch=async input=>{
 const url=new URL(typeof input==='string' ? input : input.url,'https://local.invalid');
 assert.ok(url.pathname.startsWith('/pagefind/'),'Index must load only its own assets');
 const target=path.resolve(publicRoot,'.'+decodeURIComponent(url.pathname));
 assert.ok(target.startsWith(path.join(publicRoot,'pagefind')+path.sep));
 const bytes=await fs.readFile(target);
 return new Response(bytes,{headers:{'Content-Type':url.pathname.endsWith('.wasm')?'application/wasm':'application/octet-stream'}});
};
let pagefind;
try{
 pagefind=await import(pathToFileURL(path.join(publicRoot,'pagefind/pagefind.js')));
 await pagefind.init('cs');
 const raw=JSON.parse(await fs.readFile(path.join(publicRoot,'data/20v/page.json'),'utf8'));
 assert.ok(raw.lines.some(line=>line.raw_htr.catmus.includes('glosa')),'Acceptance word must exist in raw HTR20v');
 const response=await pagefind.search('glosa',{filters:{rukopis:'vkol-m-ii-220'}});
 const pages=await Promise.all(response.results.map(result=>result.data()));
 assert.ok(pages.some(page=>/^\/rukopisy\/vkol-m-ii-220\/20v(?:\.html)?$/.test(new URL(page.url,'https://local.invalid').pathname)),'Pagefind must find 20v for raw HTR word glosa');
 // Pagefind broadens an unmatched word to a matching prefix. The old sentinel
 // began with "zz", which really occurs in the new 1r raw HTR candidate.
 // Quote this negative control so the engine checks the full exact term.
 const impossible=await pagefind.search('"qzxwvjkplmnsabcdefgh"');
 assert.equal(impossible.results.length,0);
 assert.equal((await pagefind.search('glosa',{filters:{rukopis:'vkol-not-registered'}})).results.length,0,'Separate manuscript filter');
 if(manuscripts.some(m=>m.doc.id==='vkol-m-ii-153')){
  const second=JSON.parse(await fs.readFile(path.join(publicRoot,'data/vkol-m-ii-153/64v/page.json'),'utf8'));
  assert.ok(second.passages.some(p=>p.latin.includes('tribulation')));
  const found=await pagefind.search('tribulationis',{filters:{rukopis:'vkol-m-ii-153'}});
  const results=await Promise.all(found.results.map(r=>r.data()));
  assert.ok(results.some(p=>/\/vkol-m-ii-153\/64v(?:\.html)?$/.test(new URL(p.url,'https://local.invalid').pathname)),'Second manuscript source must be found');
  assert.ok(results.every(p=>new URL(p.url,'https://local.invalid').pathname.includes('/vkol-m-ii-153/')),'Filter must exclude legacy folia');
 }
 console.log(JSON.stringify({status:'passed',indexed_pages:expected,query:'glosa',source:'raw catmus20v',found_20v:true,matching_pages:pages.length,engine:'Pagefind1.4.0 browser API + real WASM'}));
}finally{pagefind?.destroy();globalThis.fetch=nativeFetch;}
