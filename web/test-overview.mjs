/** Test the combined overview and the real browser behaviour of former URLs. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {chromium} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {HtmlValidate} from 'html-validate';

const root=path.resolve('public');
const rules=(await fs.readFile(path.join(root,'_redirects'),'utf8')).trim().split('\n').map(r=>r.trim().split(/\s+/));
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'};
const server=http.createServer(async(req,res)=>{
 try{
  const u=new URL(req.url,'http://localhost'),rule=rules.find(r=>r[0]===u.pathname);
  if(rule){res.writeHead(Number(rule[2]),{Location:rule[1]});res.end();return;}
  let relative=u.pathname==='/'?'/index.html':u.pathname;
  if(!path.extname(relative))relative+='.html';
  const file=path.resolve(root,'.'+decodeURIComponent(relative));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  const raw=await fs.readFile(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});res.end(raw);
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
const checks=[],validator=new HtmlValidate({extends:['html-validate:recommended']});
try{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext(),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const origin='http://127.0.0.1:'+server.address().port;
 for(const [id,alias,theme,items] of [['220','/summary','kazani',64],['153','/rukopisy/vkol-m-ii-153/shrnuti','laska',16]]){
  const file='public/rukopisy/vkol-m-ii-'+id+'.html';
  const markup=await validator.validateFile(file);assert.ok(markup.valid,JSON.stringify(markup.results));
  await page.setViewportSize({width:1440,height:900});
  await page.goto(origin+alias+'#'+theme);
  await page.waitForURL('**/rukopisy/vkol-m-ii-'+id+'#'+theme);
  assert.ok(await page.locator('#'+theme).getAttribute('open')!==null,'Former fragment must open theme');
  assert.equal(await page.locator('.ai-theme').count(),7);
  assert.equal(await page.locator('.source-entry').count(),items);
  assert.equal(await page.locator('.source-label').count(),2);
  assert.equal(await page.locator('.digitization-support').count(),1);
  assert.equal(await page.locator('.digitization-support p').innerText(),'Zdigitalizováno ve VISK 6');
  await page.locator('.digitization-support img').waitFor({state:'visible'});
  assert.ok(await page.locator('.digitization-support img').evaluate(img=>img.complete && img.naturalWidth>0 && img.getBoundingClientRect().width<=150),'Official logo must load at a modest size');
  assert.equal(await page.locator('link[rel=canonical]').getAttribute('href'),'https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-'+id);
  await page.locator('#prehled-navigace a[href="#ai-shrnuti"]').click();
  await page.locator('#ai-shrnuti a[href^="#catalogue-item-"]').first().click();
  await page.locator(':target.source-entry[open]').waitFor();
  assert.ok(await page.locator(':target.source-entry').getAttribute('open')!==null,'Catalogue evidence link must open entry');
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:width===390?844:900});
   await page.goto(origin+'/rukopisy/vkol-m-ii-'+id+'#ai-shrnuti');
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');
   const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
   assert.deepEqual(axe.violations,[]);
   checks.push({document_id:'vkol-m-ii-'+id,width,html_valid:true,axe_violations:0,theme_links:7,catalogue_items:items});
  }
  const withoutJS=await browser.newContext({javaScriptEnabled:false}),plain=await withoutJS.newPage();
  await plain.goto(origin+'/rukopisy/vkol-m-ii-'+id);
  assert.ok(await plain.locator('#ai-shrnuti').isVisible());
  await plain.locator('#'+theme+' > summary').click();
  assert.ok(await plain.locator('#'+theme+' .summary-sources').isVisible());
  await withoutJS.close();
 }
 assert.deepEqual(errors,[]);
 const report={status:'passed',checks,former_summary_redirects_preserve_fragments:true,catalogue_links_open_exact_items:true,no_js_readable:true,browser_pageerrors:errors};
 await fs.writeFile(process.env.OVERVIEW_REPORT||'../docs/validation/combined-overview-ui-20261014.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report));
}finally{await browser?.close();server.close();}
