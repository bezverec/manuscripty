import * as pagefind from 'pagefind';
import path from 'node:path';
import {publicRoot, loadManuscripts} from './build_folio_pages.mjs';

const {index, errors} = await pagefind.createIndex({forceLanguage:'cs'});
if (errors?.length || !index) throw Error(JSON.stringify(errors));
try {
  const manuscripts = await loadManuscripts();
  let pages = 0;
  for (const {doc, data} of manuscripts) {
    const result = await index.addDirectory({path:publicRoot, glob:'rukopisy/' + doc.id + '/*.html'});
    if (result.errors.length || result.page_count !== data.pages.length) throw Error(JSON.stringify(result));
    pages += result.page_count;
  }
  const result = await index.writeFiles({outputPath:path.join(publicRoot, 'pagefind')});
  if (result.errors.length) throw Error(JSON.stringify(result.errors));
  console.log(JSON.stringify({status:'passed',indexed_pages:pages,output:'public/pagefind',pagefind_version:'1.4.0'}));
} finally {await pagefind.close();}
