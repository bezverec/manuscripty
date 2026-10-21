import assert from 'node:assert/strict';
import {publicationPlan,verifyRedirect} from './verify_publication.mjs';

const plan=await publicationPlan();
assert.deepEqual(plan.documents.map(d=>[d.id,d.pages]),[
  ['vkol-m-ii-220',677],['vkol-m-ii-153',197],['vkol-m-i-259',371]
]);
assert.equal(plan.documents.reduce((n,d)=>n+d.pages,0),1245);
assert.equal(plan.files.find(f=>f.path==='index.html').url_path,'/');
assert(plan.files.some(f=>f.path==='data/vkol-m-i-259/119v/page.json'));
assert(!plan.files.some(f=>f.path==='summary.html'||f.path.endsWith('/shrnuti.html')));
assert.equal(plan.redirects.length,6);
const origin='https://rukopisy.digitalizaty.cz',rule=plan.redirects[0];
let calls=0;
await verifyRedirect(rule,origin,async(url,options)=>{
  calls++;assert.equal(url.href,origin+rule.from);assert.equal(options.redirect,'manual');
  return new Response(null,{status:301,headers:{location:rule.to}});
});
assert.equal(calls,1,'Old summary must not be followed and compared to fallback bytes');
await assert.rejects(()=>verifyRedirect(rule,origin,async()=>new Response('different canonical HTML',{status:200})),/Redirect mismatch/);
await assert.rejects(()=>verifyRedirect(rule,origin,async()=>new Response(null,{status:301,headers:{location:'/wrong-document'}})),/Redirect mismatch/);
console.log('Publication verifier: 3 documents / 1245 pages; redirected summaries checked separately.');
