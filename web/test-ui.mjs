import {chromium} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const root=path.dirname(fileURLToPath(import.meta.url));
const publicRoot=path.join(root,'public');
const output=path.resolve(root,process.env.UI_REPORT_DIR||'../docs/validation/ui');
const localMedia=process.env.MANUSCRIPT_TEST_MEDIA ? path.resolve(process.env.MANUSCRIPT_TEST_MEDIA) : null;
await fs.mkdir(output,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.json':'application/json','.css':'text/css','.svg':'image/svg+xml','.xml':'application/xml','.png':'image/png','.webp':'image/webp'};
// A local test server with the same clean-URL resolution as the published site.
const server=http.createServer(async(req,res)=>{
  try{
    const url=new URL(req.url,'http://localhost');
    let rel=decodeURIComponent(url.pathname).replace(/^\/+/, '')||'index.html';
    let target=path.resolve(publicRoot,rel);
    if(!target.startsWith(publicRoot+path.sep)){res.writeHead(403);res.end();return;}
    try{await fs.access(target);}catch{if(!path.extname(target))target+='.html';}
    let status=200;
    try{if(!(await fs.stat(target)).isFile())throw Error();}catch{target=path.join(publicRoot,'404.html');status=404;}
    const body=await fs.readFile(target);res.writeHead(status,{'Content-Type':mime[path.extname(target)]||'application/octet-stream'});res.end(body);
  }catch{res.writeHead(500);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROME_PATH?{executablePath:process.env.PLAYWRIGHT_CHROME_PATH}:{channel:'chrome'})});
const report=[];
let failure;
try{
 for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
  const context=await browser.newContext({viewport});
  if(localMedia)await context.route('https://rukopisy-data.digitalizaty.cz/**',async route=>{
   const relative=decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\/+/, '');
   const file=path.resolve(localMedia,relative);
   if(!file.startsWith(localMedia+path.sep))return route.abort();
   try{await route.fulfill({status:200,contentType:'image/webp',body:await fs.readFile(file)});}catch{await route.abort();}
  });
  for(const [name,url] of [['index','/'],['20v','/rukopis.html#20v'],['9r','/rukopis.html?vrstva=radky#9r'],['summary','/summary.html'],['document','/rukopisy/vkol-m-ii-220.html']]){
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(origin+url,{waitUntil:'load'});
   if(name==='20v'||name==='9r'){
    await page.waitForFunction(()=>{const x=document.getElementById('load-status');return x&&!x.textContent.startsWith('Načítám');});
    await page.waitForFunction(()=>document.querySelectorAll('.scan-zone').length>0);
    await page.waitForFunction(()=>[...document.querySelectorAll('#osd canvas')].some(c=>{
     try{const x=c.getContext('2d');if(!x||!c.width||!c.height)return false;
      return [.35,.5,.65].some(t=>{const a=x.getImageData(Math.floor(c.width*t),Math.floor(c.height*.5),1,1).data;return a[3]>0&&a[0]+a[1]+a[2]>400;});
     }catch{return false;}
    }),{},{timeout:30000});
   }
   await page.waitForTimeout(700);
   const metrics=await page.evaluate(()=>({scrollY:scrollY,scrollWidth:document.documentElement.scrollWidth,width:innerWidth,scanTop:document.getElementById('osd')?.getBoundingClientRect().top??null}));
   const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa']).analyze();
   const best=await new AxeBuilder({page}).withRules(['region']).analyze();
   const serious=scan.violations.filter(v=>['serious','critical'].includes(v.impact));
   report.push({name,viewport,metrics,errors,violations:scan.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),region:best.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),incomplete_rules:scan.incomplete.map(v=>v.id)});
   await page.screenshot({path:path.join(output,`${name}-${viewport.width}x${viewport.height}.png`)});
   assert.equal(serious.length,0,JSON.stringify({name,viewport,serious:report.at(-1).violations},null,2));
   assert.equal(errors.length,0,'Browser JS errors: '+errors.join(', '));
   assert.ok(!best.violations.some(v=>v.nodes.some(n=>n.target.some(x=>x.includes('panel-resizer')))), 'Resizer must be inside a landmark');
   if(viewport.width===390){
    assert.ok(metrics.scrollWidth<=metrics.width,`${name}: horizontal overflow ${metrics.scrollWidth}`);
    if(name==='20v'||name==='9r'){
     assert.equal(metrics.scrollY,0,`${name}: page scrolled on load`);
     assert.ok(metrics.scanTop<=140,`${name}: scan begins at${metrics.scanTop}px`);
     await page.getByRole('button',{name:'Další akce',exact:true}).click();
     assert.equal(await page.locator('#more-actions-toggle').getAttribute('aria-expanded'),'true');
     await page.keyboard.press('Escape');
     assert.equal(await page.locator('#more-actions-toggle').getAttribute('aria-expanded'),'false');
    }
   }
   if(name==='20v'&&await page.locator('#tab-text').count()){
    const expected={prepis:'text',radky:'text',vyklad:'text',analyza:'about',popis:'about',struktura:'about',citace:'citace'};
    for(const [legacy,group] of Object.entries(expected)){
     await page.goto(origin+'/rukopis.html?vrstva='+legacy+'#20v-f20v_l001');
     await page.waitForFunction(()=>!document.getElementById('load-status').textContent.startsWith('Načítám'));
     assert.equal(await page.locator('#tab-'+group).getAttribute('aria-selected'),'true',legacy);
     assert.ok(await page.locator('#panel-'+group).isVisible(),legacy);
     assert.ok(await page.locator('#panel-'+legacy).isVisible(),legacy);
     assert.ok(page.url().includes('#20v-f20v_l001'),'Stable source line retained');
    }
    await page.locator('#tab-citace').press('ArrowRight');
    assert.equal(await page.locator('#tab-text').getAttribute('aria-selected'),'true');
    await page.locator('#tab-text').press('End');
    assert.equal(await page.locator('#tab-citace').getAttribute('aria-selected'),'true');
    await page.locator('#tab-citace').press('Home');
    await page.locator('#view-vyklad').press('ArrowRight');
    assert.equal(await page.locator('#view-prepis').getAttribute('aria-selected'),'true');
    assert.equal(await page.locator('#panel-prepis').isVisible(),true);
    assert.equal(await page.locator('#panel-vyklad').isVisible(),false);
    const tabs=await page.locator('.tabs').evaluate(e=>({width:e.clientWidth,scroll:e.scrollWidth}));
    assert.ok(tabs.scroll<=tabs.width,'Three primary tabs fit');
    report.at(-1).legacy_views_checked=Object.keys(expected);
    report.at(-1).tab_keyboard_checked=true;
   }
   console.log(`${name} ${viewport.width}x${viewport.height}: axe serious/critical0; overflow0; scrollY${metrics.scrollY}`);
   await page.close();
  }
  await context.close();
 }
 const page=await browser.newPage();
 const response=await page.goto(origin+'/nonexistent-test-page');assert.equal(response.status(),404);
 await page.close();
}catch(e){failure=e;}
finally{
 await fs.writeFile(path.join(output,'report.json'),JSON.stringify({passed:!failure,media_mode:localMedia?'Existing local presentation WebP fixtures; does not verify public R2 delivery':'Public R2 requests',scope:'Automated axe WCAG2A/AA checks, region resizer check, two viewports, load scroll and clean-URL local server. Not a full manual WCAG conformance audit.',pages:report},null,2)+'\n');
 await browser.close();await new Promise(resolve=>server.close(resolve));
}
if(failure)throw failure;
