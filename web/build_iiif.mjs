import {readFile, mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const read=async file=>JSON.parse(await readFile(file,'utf8'));
const safe=value=>{if(!/^[A-Za-z0-9_-]+$/.test(value))throw new Error('Unsafe IIIF identifier: '+value);return value;};
export function buildManifest({document, pages, structure, site='https://rukopisy.digitalizaty.cz', imageBase='https://rukopisy-data.digitalizaty.cz/iiif', imageNamespace=null}) {
 const id=safe(document.id), base=`${site}/iiif/${id}`, canvasId=f=>`${base}/canvas/${safe(f)}`;
 const canvases=pages.map(({entry,page})=>{
  const f=safe(entry.folio),service=`${imageBase}/${imageNamespace?safe(imageNamespace)+'/':''}${f}`;
  if(page.folio!==f || !Number.isInteger(page.width) || !Number.isInteger(page.height) || page.width<1 || page.height<1)throw new Error('Invalid page '+f);
  return {id:canvasId(f),type:'Canvas',label:{cs:[entry.label||f]},width:page.width,height:page.height,
   rendering:[{id:`${site}/rukopisy/${id}/${f}`,type:'Text',format:'text/html',label:{cs:['Stránka folia']}}],
   items:[{id:`${base}/page/${f}`,type:'AnnotationPage',items:[{id:`${base}/annotation/${f}`,type:'Annotation',motivation:'painting',target:canvasId(f),body:{id:`${service}/full/max/0/default.webp`,type:'Image',format:'image/webp',width:page.width,height:page.height,service:[{id:service,type:'ImageService3',profile:'level0'}]}}]}]};
 });
 const known=new Set(canvases.map(c=>c.id));
 const ranges=(structure.groups||[]).map(group=>({id:`${base}/range/${safe(group.id)}`,type:'Range',label:{cs:[group.label]},items:group.pages.map(p=>{const id=canvasId(p.folio);if(!known.has(id))throw new Error('Unknown range canvas '+id);return {id,type:'Canvas'};})}));
 return {'@context':'http://iiif.io/api/presentation/3/context.json',id:`${base}/manifest.json`,type:'Manifest',label:{cs:[document.title]},
  summary:{cs:['Pracovní výzkumná data bez odborné revize. Struktura slouží navigaci a netvrdí ověřené hranice děl.']},
  metadata:[{label:{cs:['Uložení']},value:{cs:[document.repository.name]}},{label:{cs:['Signatura']},value:{cs:[document.shelfmark]}}],
  homepage:[{id:document.uri,type:'Text',format:'text/html',label:{cs:['Záznam rukopisu']}}],
  seeAlso:[{id:document.tei,type:'Dataset',format:'application/tei+xml',profile:'http://www.tei-c.org/ns/1.0',label:{cs:['TEI P5']}}],
  items:canvases,structures:ranges};
}
export async function loadInputs({publicDir=path.join(here,'public'), documentFile='document.json', indexFile='pilot-data.js', structureFile='structure.json'}={}) {
 const raw=await readFile(path.join(publicDir,indexFile),'utf8');
 const index=JSON.parse(raw.slice(raw.indexOf('=')+1).trim().replace(/;$/,''));
 const document=await read(path.join(publicDir,documentFile)),structure=await read(path.join(publicDir,structureFile));
 const pages=await Promise.all(index.pages.map(async entry=>({entry,page:await read(path.join(publicDir,entry.data))})));
 return {document,structure,pages};
}
export async function generate(options={}) {
 const inputs=await loadInputs(options),manifest=buildManifest({...inputs,...options});
 const destination=options.destination||path.join(options.publicDir||path.join(here,'public'),'iiif',inputs.document.id,'manifest.json');
 await mkdir(path.dirname(destination),{recursive:true});await writeFile(destination,JSON.stringify(manifest,null,2)+'\n');return manifest;
}
if(process.argv[1]===fileURLToPath(import.meta.url)) {
 const options=process.argv[2]?await read(path.resolve(process.argv[2])):{};
 const manifest=await generate(options);console.log(`IIIF draft: ${manifest.items.length} canvases; media not built or uploaded.`);
}
