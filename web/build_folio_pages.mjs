/** Deterministic, offline folio renderer. Source readings are never rewritten. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const webRoot = path.dirname(fileURLToPath(import.meta.url));
export const publicRoot = path.join(webRoot, 'public');
export const revision = '20261012-6';
export const themeRevision = '20261016-3';
export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export async function publicFile(relative, root = publicRoot) {
  if (typeof relative !== 'string' || path.isAbsolute(relative)) throw Error('Expected relative public path');
  const target = path.resolve(root, relative);
  const realRoot = await fs.realpath(root);
  const realTarget = await fs.realpath(target);
  if (!realTarget.startsWith(realRoot + path.sep)) throw Error('Path escapes public/: ' + relative);
  return realTarget;
}

export async function loadManuscripts({root = publicRoot, registry = path.join(webRoot, 'manuscripts.json')} = {}) {
  const config = JSON.parse(await fs.readFile(registry, 'utf8'));
  if (config.schema !== 'manuscripty-static-registry-v1' || !Array.isArray(config.manuscripts)) throw Error('Invalid registry');
  const seen = new Set();
  const result = [];
  for (const entry of config.manuscripts) {
    if (!/^vkol-[a-z0-9-]+$/.test(entry.id) || seen.has(entry.id)) throw Error('Unsafe or duplicate document ID');
    seen.add(entry.id);
    const raw = await fs.readFile(await publicFile(entry.manifest, root), 'utf8');
    const data = entry.manifest.endsWith('.js') ? JSON.parse(raw.match(/^\s*window\.PILOT_DATA\s*=\s*(\{[\s\S]*\});\s*$/)?.[1] || 'null') : JSON.parse(raw);
    if (data?.document?.id !== entry.id || !data.pages?.length) throw Error('Registry/manifest identity mismatch');
    if (new Set(data.pages.map(p => p.folio)).size !== data.pages.length) throw Error('Duplicate folio');
    if (data.counts?.pages !== data.pages.length) throw Error('Manifest count mismatch');
    for (const p of data.pages) if (!/^[A-Za-z0-9_]+$/.test(p.folio)) throw Error('Unsafe folio');
    const doc = data.document;
    const origin = new URL(doc.uri).origin;
    if (new URL(doc.uri).protocol !== 'https:') throw Error('Document URI must use HTTPS');
    result.push({entry, data, doc, origin, root});
  }
  return result;
}

export function readerUrl(doc, folio, line = '') {
  const url = new URL(doc.reader);
  url.pathname = url.pathname.replace(/\.html$/, "");
  url.hash = folio + (line ? '-' + line : '');
  return url.href;
}

export function folioUrl(doc, folio, line = '') {
  const url = new URL(doc.uri.replace(/\/$/, '') + '/' + encodeURIComponent(folio));
  if (line) url.hash = line;
  return url.href;
}

function mediaUrl(value, origin) {
  const url = new URL(value, origin + '/');
  if (!['https:', 'http:'].includes(url.protocol)) throw Error('Unsupported image URL');
  return url.href;
}

export function renderFolio({entry, data, doc, origin}, page, index) {
  const e = escapeHtml, folio = page.folio, label = page.label || 'f. ' + folio;
  const canonical = folioUrl(doc, folio), title = `${doc.shelfmark} · ${label} · HTR, rekonstrukce a překlad`;
  const hasText = Boolean(page.lines.length), description = `${doc.repository.name}, ${doc.shelfmark}, ${label}. ` + (hasText ? 'Původní HTR a pracovní rekonstrukce s českým překladem, bez odborné revize.' : (page.blank ? 'Digitalizovaný snímek bez vybraného hlavního textu.' : 'Digitalizovaný snímek; zatím nepřepsáno.'));
  const preview = mediaUrl(page.preview, origin), model = entry.default_model;
  if (hasText && !page.models[model]) throw Error('Default HTR model unavailable: ' + folio);
  const prev = data.pages[index - 1], next = data.pages[index + 1];
  const navigation = '<nav class="folio-pagination" aria-label="Předchozí a další snímek">' + (prev ? `<a class="btn" rel="prev" href="${e(new URL(folioUrl(doc, prev.folio)).pathname)}">← ${e(prev.label || prev.folio)}</a>` : '<span>Začátek dokumentu</span>') + (next ? `<a class="btn" rel="next" href="${e(new URL(folioUrl(doc, next.folio)).pathname)}">${e(next.label || next.folio)} →</a>` : '<span>Konec dokumentu</span>') + '</nav>';
  const lines = page.lines.map((line, i) => `<li id="${e(line.id)}"><span class="layer-id">${e(line.id)}</span><p class="layer-raw" lang="${e(page.language || 'la')}">${e(line.raw_htr[model])}</p><a href="${e(readerUrl(doc, folio, line.id))}" data-pagefind-ignore>Řádek ${i + 1} v prohlížeči</a></li>`).join('\n');
  const passages = page.passages.map(p => `<article class="reading-card" id="passage-${e(p.id)}"><h3>${e(p.title)}</h3><p class="layer-id">${e(p.id)} · pracovní návrh, bez odborné revize</p><section lang="${e(p.language || page.language || 'la')}"><h4>Rekonstrukce (jazyk předlohy)</h4><p class="layer-reading">${e(p.latin)}</p></section><section lang="cs"><h4>Český překlad</h4><p class="layer-reading">${e(p.czech)}</p></section>${p.notes ? `<h4>Poznámky a nejistoty</h4><p class="layer-notes">${e(p.notes)}</p>` : ''}<p data-pagefind-ignore>Zdrojové řádky: ${p.line_ids.map(id => `<a href="#${e(id)}">${e(id)}</a>`).join(' · ')}</p></article>`).join('\n');
  const downloads = page.downloads.map(d => `<li><a href="${e(new URL(d.href, origin + '/').href)}">${e(d.name)}</a></li>`).join('');
  return `<!DOCTYPE html>
<html lang="cs"><head><meta charset="utf-8"><script src="/theme.js?v=${themeRevision}"></script><meta name="viewport" content="width=device-width, initial-scale=1"><title>${e(title)}</title><meta name="description" content="${e(description)}"><link rel="canonical" href="${e(canonical)}"><meta property="og:title" content="${e(title)}"><meta property="og:description" content="${e(description)}"><meta property="og:url" content="${e(canonical)}"><meta property="og:image" content="${e(preview)}"><meta property="og:type" content="article"><link rel="stylesheet" href="/styles.css?v=${revision}"><link rel="stylesheet" href="/folio.css?v=${revision}"><link rel="stylesheet" href="/theme.css?v=${themeRevision}"></head>
<body><header class="site-header"><div class="container"><a class="brand" href="/">Rukopisy, snímek po snímku.</a></div></header><main class="container section folio-document">
<nav aria-label="Drobečková navigace"><ol class="folio-breadcrumbs"><li><a href="/">Rukopisy</a></li><li><a href="${e(new URL(doc.uri).pathname)}">${e(doc.shelfmark)}</a></li><li aria-current="page">${e(label)}</li></ol></nav>
<h1 data-pagefind-meta="title">${e(doc.shelfmark)} · ${e(label)}</h1><p>${e(doc.repository.name)}</p><p class="sample-notice">Pracovní výstupy bez odborné revize. Shoda modelů ani validita XML nepotvrzují správnost četby.</p>
<a class="btn btn--primary" href="${e(readerUrl(doc, folio))}">Otevřít v prohlížeči</a>${navigation}
<a href="${e(readerUrl(doc, folio))}"><img class="folio-preview" src="${e(preview)}" alt="${e(doc.shelfmark + ', ' + label)}" width="520" height="720"></a>
<div data-pagefind-body data-pagefind-filter="rukopis:${e(doc.id)}"><h2>HTR · ${e(page.models[model] || (page.blank ? 'bez vybraného hlavního textu' : 'zatím nepřepsáno'))}</h2>${hasText ? `<p>Neupravený výstup výchozího modelu. Další modely jsou dostupné v prohlížeči a ke stažení.</p><ol class="folio-htr">${lines}</ol><h2>Rekonstrukce a český překlad</h2>${passages}` : (page.blank ? '<p>Bez vybraného hlavního textu.</p>' : '<p>Zatím nepřepsáno.</p>')}</div>
<section aria-labelledby="folio-citation"><h2 id="folio-citation">Citace a stálý odkaz</h2><p class="citation">${e(doc.repository.name)}, ${e(doc.shelfmark)}, ${e(label)}. Rukopisy: pracovní HTR, rekonstrukce a český překlad bez odborné revize. <a href="${e(canonical)}">${e(canonical)}</a></p></section>
${downloads ? `<section><h2>Podklady ke stažení</h2><ul>${downloads}</ul></section>` : ''}</main><footer class="site-footer"><div class="container">Rukopis: ${e(doc.repository.name)}, ${e(doc.shelfmark)} · Manuscripty</div></footer></body></html>\n`;
}

export async function buildFolioPages(options = {}) {
  const manuscripts = await loadManuscripts(options), urls = new Set(), counts = {};
  for (const manuscript of manuscripts) {
    const {root, doc, data} = manuscript;
    const folder = path.join(root, 'rukopisy', doc.id);
    await fs.mkdir(folder, {recursive: true});
    counts[doc.id] = 0;
    for (let i = 0; i < data.pages.length; i++) {
      const header = data.pages[i], page = JSON.parse(await fs.readFile(await publicFile(header.data.replace(/^\//, ''), root), 'utf8'));
      if (page.folio !== header.folio || page.document_id !== doc.id) throw Error('Wrong source page identity');
      if (!Array.isArray(page.lines) || !Array.isArray(page.passages)) throw Error('Invalid page content');
      if (new Set(page.lines.map(l => l.id)).size !== page.lines.length) throw Error('Duplicate source line IDs');
      const ids = new Set(page.lines.map(l => l.id));
      for (const p of page.passages) if (p.line_ids.some(id => !ids.has(id))) throw Error('Unresolved passage source ID');
      const html = renderFolio(manuscript, page, i);
      await fs.writeFile(path.join(folder, header.folio + '.html'), html);
      urls.add(folioUrl(doc, header.folio));counts[doc.id]++;
    }
    urls.add(doc.uri);
    // Viewer URLs with doc query parameters remain distinct for future manuscripts.
    urls.add(doc.reader);
  }
  const root = options.root || publicRoot, origin = manuscripts[0].origin;
  urls.add(origin + '/');
  await fs.writeFile(path.join(root, 'sitemap.xml'), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + [...urls].sort().map(url => '<url><loc>' + escapeHtml(url) + '</loc></url>').join('\n') + '\n</urlset>\n');
  console.log(JSON.stringify({status:'passed',generated:counts,sitemap_urls:urls.size}));
  return counts;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await buildFolioPages();
