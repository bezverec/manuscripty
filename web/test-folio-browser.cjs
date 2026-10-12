// Optional visual check: PLAYWRIGHT_MODULE points to an installed Playwright package.
const fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=path.join(__dirname,'public'),artifacts=path.resolve(process.env.FOLIO_SCREENSHOTS || path.join(__dirname,'../docs/validation/phase3-screenshots'));
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.wasm':'application/wasm','.xml':'application/xml'};
const server=http.createServer(async(req,res)=>{
 try{
  let file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));
  if(file!==root&&!file.startsWith(root+path.sep))throw Error('Invalid path');
  if(file===root)file=path.join(root,'index.html');
  try{await fs.access(file);}catch{file+='.html';}
  const raw=await fs.readFile(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)] || 'application/octet-stream'});res.end(raw);
 }catch{res.writeHead(404);res.end('Not found');}
});
async function localMedia(context){
 if(!process.env.MANUSCRIPT_TEST_MEDIA)return;
 const base=path.resolve(process.env.MANUSCRIPT_TEST_MEDIA);
 await context.route('https://rukopisy-data.digitalizaty.cz/**',async route=>{
  const file=path.resolve(base,'.'+decodeURIComponent(new URL(route.request().url()).pathname));
  if(!file.startsWith(base+path.sep))return route.abort();
  try{await route.fulfill({status:200,contentType:'image/webp',body:await fs.readFile(file)});}catch{await route.abort();}
 });
}
(async()=>{
 await fs.mkdir(artifacts,{recursive:true});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const observations=[];
 try{
  for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
   const context=await browser.newContext({viewport,javaScriptEnabled:false});await localMedia(context);const page=await context.newPage();
   await page.goto(origin+'/rukopisy/vkol-m-ii-220/20v.html',{waitUntil:'domcontentloaded'});
   assert.equal(await page.locator('.folio-htr li').count(),82);assert.ok(await page.locator('.reading-card').count());
   const dimensions=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));assert.ok(dimensions.scroll<=dimensions.client,'Folio horizontal overflow');
   await page.waitForFunction(()=>{const img=document.querySelector('.folio-preview');return img.complete&&img.naturalWidth>0;});
   await page.screenshot({path:path.join(artifacts,`20v-${viewport.width}-nojs.png`)});
   await page.locator('.folio-htr').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(artifacts,`20v-text-${viewport.width}-nojs.png`)});
   observations.push({width:viewport.width,no_js:true,folio:'20v',horizontal_overflow:false});await context.close();
  }
  const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();
  await page.goto(origin+'/',{waitUntil:'domcontentloaded'});await page.locator('[data-folio-search] input').fill('glosa');await page.locator('[data-folio-search] form').evaluate(form=>form.requestSubmit());
  await page.waitForSelector('.folio-search-results li',{timeout:20000});
  for(let i=0;i<4&&!await page.locator('.folio-search-results a[href="/rukopisy/vkol-m-ii-220/20v"]').count();i++){
   const before=await page.locator('.folio-search-results li').count();await page.locator('[data-search-more]').click();await page.waitForFunction(n=>document.querySelectorAll('.folio-search-results li').length>n,before);
  }
  assert.equal(await page.locator('.folio-search-results a[href="/rukopisy/vkol-m-ii-220/20v"]').count(),1);
  const searchDimensions=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));assert.ok(searchDimensions.scroll<=searchDimensions.client,'Search horizontal overflow');
  await page.locator('[data-folio-search]').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(artifacts,'search-390.png')});
  observations.push({browser_query:'glosa',found_20v:true,clean_result_url:true});await context.close();
  const report={status:'passed',observations,screenshots:artifacts,media_mode:process.env.MANUSCRIPT_TEST_MEDIA?'Existing local WebP fixtures; no public delivery assertion':'Public R2'};
  await fs.writeFile(path.join(artifacts,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
