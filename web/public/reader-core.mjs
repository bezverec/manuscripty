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

/** Later editorial proposals never replace raw HTR or the earlier interpretation. */
export function renderReadingAddenda(readings = [], {language = 'both', lineId = null, idPrefix = 'reading'} = {}) {
  const selected = readings.filter(r => !lineId || r.line_ids.includes(lineId));
  if (!selected.length) return '';
  const e = escapeHtml;
  const cards = selected.map(r => {
    if (r.status !== 'proposed' || r.expert_review !== false) throw Error('Reading addendum must remain proposed');
    const links = (r.sources || []).map(s => {
      const url = new URL(s.url);
      if (url.protocol !== 'https:') throw Error('Reading source must use HTTPS');
      return '<a href="' + e(url.href) + '" target="_blank" rel="noopener">' + e(s.label) + '</a>';
    }).join(' · ');
    return '<article class="reading-card" id="' + e(idPrefix + '-' + r.id) + '"><h3>Zpřesněná četba AI · ' + e(r.date) + '</h3>' +
      '<p class="sample-notice">Pracovní návrh bez odborné revize. Doplňuje starší výklad; původní HTR i dřívější interpretace zůstávají zachované. Hranaté závorky a otazníky označují nejistoty.</p>' +
      '<p class="layer-id">Podklad: ' + e(r.line_ids.join(', ')) + '</p>' +
      (language !== 'czech' ? '<section lang="la"><h4>Rozvedená četba</h4><p class="layer-reading">' + e(r.reconstruction) + '</p>' + (r.context_continuation ? '<h4>Pokračování v následujícím řádku</h4><p class="layer-reading">' + e(r.context_continuation) + '</p>' : '') + '</section>' : '') +
      (language !== 'latin' ? '<section lang="cs"><h4>Český překlad</h4><p class="layer-reading">' + e(r.translation_cs) + '</p></section>' : '') +
      '<h4>Poznámky a nejistoty</h4><p class="layer-notes">' + e(r.note_cs) + '</p>' +
      (links ? '<p class="layer-notes">Podklady: ' + links + '</p>' : '') + '</article>';
  }).join('');
  return '<section class="reading-addenda"><h2>Novější návrh čtení a překladu</h2>' + cards + '</section>';
}
