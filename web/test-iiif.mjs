import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import {buildManifest,loadInputs} from './build_iiif.mjs';
const schemaRaw=await readFile(new URL('./schemas/iiif-presentation-3.json',import.meta.url));
assert.equal(createHash('sha256').update(schemaRaw).digest('hex'),'14dd7ee8aee25d959be4b12feddb4179c726909fc85b925f6707f4ab3bfe2ad6');
const ajv=new Ajv({strict:false,allErrors:true});addFormats(ajv);
const validate=ajv.compile(JSON.parse(schemaRaw));
const inputs=await loadInputs(),manifest=buildManifest(inputs);
assert(validate(manifest),JSON.stringify(validate.errors?.slice(0,5)));
const published=JSON.parse(await readFile(new URL('./public/iiif/vkol-m-ii-220/manifest.json',import.meta.url),'utf8'));
assert.deepEqual(published,manifest,'Regenerate the checked-in manifest after source changes.');
assert.equal(manifest.items.length,677);assert(!('rights' in manifest));assert(!('requiredStatement' in manifest));
const canvasIds=new Set(manifest.items.map(c=>c.id));assert.equal(canvasIds.size,677);
for(let i=0;i<677;i++) {
 const canvas=manifest.items[i],page=inputs.pages[i].page;
 assert.equal(canvas.width,page.width);assert.equal(canvas.height,page.height);
 assert.equal(canvas.items[0].items[0].target,canvas.id);
 assert.equal(canvas.items[0].items[0].body.width,canvas.width);
 assert.equal(canvas.rendering[0].id,`https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-220/${page.folio}`);
}
const rangeCanvas=manifest.structures.flatMap(r=>r.items.map(c=>c.id));
assert.deepEqual(new Set(rangeCanvas),canvasIds);assert.equal(rangeCanvas.length,677);
for(const mutate of [m=>delete m.label,m=>m.items[0].width=0,m=>m.items[0].items[0].items[0].motivation='invalid-motivation']) {
 const broken=structuredClone(manifest);mutate(broken);
 // The upstream schema permits arbitrary motivation strings; constrain our image-only profile.
 const localValid=validate(broken)&&broken.items.every(c=>c.items.every(p=>p.items.every(a=>a.motivation==='painting')));
 assert.equal(localValid,false);
}
assert.throws(()=>buildManifest({...inputs,structure:{groups:[{id:'x',label:'x',pages:[{folio:'missing'}]}]}}),/Unknown range/);
const extra=buildManifest({...inputs,document:{...inputs.document,id:'test-second'},imageNamespace:'test-second'});
assert(extra.items[0].id.includes('/test-second/'));assert(extra.items[0].items[0].items[0].body.service[0].id.includes('/iiif/test-second/'));
const code=await readFile(new URL('./public/iiif-link.js',import.meta.url),'utf8');
for(const enabled of [false,true]) {
 const link={hidden:false,href:'#',removeAttribute(name){delete this[name];}};
 vm.runInNewContext(code,{document:{getElementById:()=>link},window:{MANUSCRIPT_FEATURES:{iiifManifest:enabled}}});
 assert.equal(link.hidden,!enabled);assert.equal(link.href,enabled?'/iiif/vkol-m-ii-220/manifest.json':undefined);
}
const flags=await readFile(new URL('./public/feature-config.js',import.meta.url),'utf8');
const context={window:{}};vm.runInNewContext(flags,context);assert.equal(context.window.MANUSCRIPT_FEATURES.iiifManifest,false);
console.log('IIIF: pinned official Presentation 3 JSON Schema + 677 canvas/link/range/flag checks passed. HTTP/JSON-LD/media not validated.');
