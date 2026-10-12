import * as pagefind from 'pagefind';
import path from 'node:path';
import fs from 'node:fs/promises';
import {publicRoot, loadManuscripts} from './build_folio_pages.mjs';

const {index, errors} = await pagefind.createIndex({forceLanguage:'cs'});
if (errors?.length || !index) throw Error(JSON.stringify(errors));
try {
  const manuscripts = await loadManuscripts();
  let pages = 0;
  for (const {doc, data} of manuscripts) {
    // Only actual scan pages enter the folio index; summaries in the same folder do not.
    for(const header of data.pages){
      const sourcePath='rukopisy/'+doc.id+'/'+header.folio+'.html';
      const result=await index.addHTMLFile({url:'/'+sourcePath.replace(/\.html$/,''),content:await fs.readFile(path.join(publicRoot,sourcePath),'utf8')});
      if(result.errors.length)throw Error(JSON.stringify(result.errors));
      pages++;
    }
  }
  const result = await index.writeFiles({outputPath:path.join(publicRoot, 'pagefind')});
  if (result.errors.length) throw Error(JSON.stringify(result.errors));
  console.log(JSON.stringify({status:'passed',indexed_pages:pages,output:'public/pagefind',pagefind_version:'1.4.0'}));
} finally {await pagefind.close();}
