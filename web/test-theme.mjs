/** Exercise persisted, system and cross-tab themes plus real dark-mode contrast. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {chromium} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root=path.resolve('public'),mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.webp':'image/webp','.wasm':'application/wasm'};
const server=http.createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost');let relative=url.pathname==='/'?'/index.html':url.pathname;
  if(!path.extname(relative))relative+='.html';
  const file=path.resolve(root,'.'+decodeURIComponent(relative));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  const raw=await fs.readFile(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});res.end(raw);
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin='http://127.0.0.1:'+server.address().port;
let browser;
try{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext({colorScheme:'dark'}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 // Pixel content is inspected on the live site; this test concerns UI and image styles.
 await context.route('https://rukopisy-data.digitalizaty.cz/**',route=>route.abort());
 await page.goto(origin+'/');
 const toggle=page.getByRole('button',{name:'Noční režim',exact:true});
 await toggle.waitFor();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
 assert.equal(await toggle.getAttribute('aria-pressed'),'true');
 await toggle.click();assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
 await page.reload();assert.equal(await toggle.getAttribute('aria-pressed'),'false');
 await page.goto(origin+'/rukopisy/vkol-m-ii-153');assert.equal(await toggle.getAttribute('aria-pressed'),'false');
 await toggle.click();
 const peer=await context.newPage();await peer.goto(origin+'/rukopisy/vkol-m-ii-220');
 await peer.getByRole('button',{name:'Noční režim',exact:true}).click();
 await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
 await peer.close();await toggle.click();
 const checks=[];
 for(const url of ['/','/rukopisy/vkol-m-ii-220','/rukopisy/vkol-m-ii-153#ai-shrnuti','/rukopisy/vkol-m-ii-220/20v','/rukopisy/vkol-m-ii-153/5r','/rukopis#20v','/rukopis?doc=vkol-m-ii-153#5r']){
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:900});await page.goto(origin+url,{waitUntil:'domcontentloaded'});
   await toggle.waitFor();assert.equal(await toggle.getAttribute('aria-pressed'),'true');
   if(url.startsWith('/rukopis?')||url.startsWith('/rukopis#'))await page.locator('#page-choice option').first().waitFor({state:'attached'});
   assert.ok(await toggle.isVisible());
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Theme toggle must fit at '+url+' '+width);
   assert.ok(await page.locator('img').evaluateAll(images=>images.every(img=>getComputedStyle(img).filter==='none')),'Never filter manuscript or logo images');
   const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
   assert.deepEqual(axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),[],url+' '+width);
   checks.push({url,width,theme:'dark',axe_violations:0,no_horizontal_overflow:true});
  }
 }
 // Keyboard operation and a visible correction dialog use the same theme.
 await page.setViewportSize({width:1440,height:900});await page.goto(origin+'/rukopis?doc=vkol-m-ii-153#5r');
 await page.locator('#page-choice option').first().waitFor({state:'attached'});
 await toggle.focus();await page.keyboard.press('Space');assert.equal(await toggle.getAttribute('aria-pressed'),'false');
 await page.keyboard.press('Space');assert.equal(await toggle.getAttribute('aria-pressed'),'true');
 await page.locator('#suggest-btn').click();await page.locator('#correction-dialog').waitFor();
 assert.equal(await page.locator('#correction-dialog').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(28, 34, 43)');
 const blocked=await browser.newContext({colorScheme:'dark'});
 await blocked.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('storage blocked');}});});
 const plain=await blocked.newPage();await plain.goto(origin+'/');
 await plain.getByRole('button',{name:'Noční režim',exact:true}).click();assert.equal(await plain.locator('html').getAttribute('data-theme'),'light');
 await blocked.close();
 const noJS=await browser.newContext({javaScriptEnabled:false}),staticPage=await noJS.newPage();
 await noJS.route('https://rukopisy-data.digitalizaty.cz/**',route=>route.abort());
 for(const url of ['/rukopisy/vkol-m-ii-220/20v','/rukopisy/vkol-m-ii-153/5r']){
  await staticPage.goto(origin+url);assert.ok(await staticPage.locator('.folio-htr li').count()>0);assert.ok(await staticPage.locator('.reading-card').count()>0);
 }
 await noJS.close();
 const system=await browser.newContext({colorScheme:'light'}),systemPage=await system.newPage();await systemPage.goto(origin+'/');
 assert.equal(await systemPage.locator('html').getAttribute('data-theme'),'light');
 await systemPage.emulateMedia({colorScheme:'dark'});await systemPage.waitForFunction(()=>document.documentElement.dataset.theme==='dark');
 await system.close();assert.deepEqual(errors,[]);
 const report={status:'passed',checks,saved_choice_survives_reload_and_navigation:true,system_default_and_live_change:true,cross_tab_updates:true,storage_unavailable_toggle_works:true,keyboard_toggle:true,dark_correction_dialog:true,folio_text_readable_without_javascript:true,image_filters:'none',browser_pageerrors:errors};
 await fs.writeFile('../docs/validation/night-mode-ui-20261016.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser?.close();server.close();}
