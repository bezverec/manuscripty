/** Shared, side-effect-free reader links and supplemental image readings. */
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export function resolveReaderHash(pages, hash) {
  let folio = pages.findIndex(page => page.folio === hash), key = '';
  if (folio < 0) {
    const match = pages.map((page, index) => ({page, index}))
      .filter(({page}) => hash.startsWith(page.folio + '-'))
      .sort((a, b) => b.page.folio.length - a.page.folio.length)[0];
    if (!match) return {page:0, line:0};
    folio = match.index;
    key = hash.slice(match.page.folio.length + 1);
  }
  const lines = pages[folio].lines;
  if (!lines) return {page:folio, line:key};
  let line = lines.findIndex(item => item.id === key);
  if (line < 0 && /^l\d+$/.test(key)) line = Number(key.slice(1)) - 1;
  if (line < 0 || line >= lines.length) line = 0;
  return {page:folio, line};
}

export function renderSupplementalReadings(readings = [], {language = 'both', pageLanguage = 'la'} = {}) {
  if (!readings.length) return '';
  const e = escapeHtml;
  const cards = readings.map(reading => {
    const image = new URL(reading.image);
    if (image.protocol !== 'https:') throw Error('Supplemental image must use HTTPS');
    return '<article class="reading-card" id="supplemental-' + e(reading.id) + '"><h3>Samostatné čtení výřezu ' + e(reading.id) + '</h3>' +
      '<p class="layer-id">Pracovní návrh, bez odborné revize. Výřez není přiřazen k HTR řádkům.</p>' +
      '<a href="' + e(image.href) + '" target="_blank" rel="noopener"><img class="line-crop" src="' + e(image.href) + '" alt="Samostatný obrazový podklad ' + e(reading.id) + '" loading="lazy"></a>' +
      (language !== 'czech' ? '<section lang="' + e(reading.language || pageLanguage) + '"><h4>Rekonstrukce (jazyk předlohy)</h4><p class="layer-reading">' + e(reading.reconstruction) + '</p></section>' : '') +
      (language !== 'latin' ? '<section lang="cs"><h4>Český překlad</h4><p class="layer-reading">' + e(reading.translation_cs) + '</p></section>' : '') +
      (reading.note_cs ? '<h4>Poznámky a nejistoty</h4><p class="layer-notes">' + e(reading.note_cs) + '</p>' : '') + '</article>';
  }).join('');
  return '<section class="supplemental-readings"><h2>Další obrazově čtené úseky strany</h2>' + cards + '</section>';
}
