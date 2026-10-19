/** Geometry belongs to the full, oriented coordinate raster, not model masks. */
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
export function proposalCoordinates(context) {
 const source = context.coordinate_source;
 if (source === undefined || source === null) {
  if (context.document_id === 'vkol-m-i-259') throw Error('Chybí identifikace koordinačního obrazu.');
  return {};
 }
 if (typeof source !== 'object' || Array.isArray(source) || typeof source.id !== 'string' || !source.id.trim() || source.id.length > 1000 || !hash(source.sha256) || !hash(source.derived_from_sha256) || source.derived_from_sha256 !== context.source_sha256) throw Error('Neplatná identifikace koordinačního obrazu.');
 const fields=['id','sha256','width','height','frame','derived_from_sha256','original_tiff_frame','rotation_ccw_degrees','source_to_coordinate_pixel_edge_affine','bbox_format','origin'];
 if (JSON.stringify(Object.keys(source).sort()) !== JSON.stringify(fields.sort()) || !Number.isInteger(source.original_tiff_frame) || source.original_tiff_frame < 0 || source.frame !== 0) throw Error('Neúplný nebo neznámý popis koordinačního obrazu.');
 if (!Number.isInteger(source.width) || !Number.isInteger(source.height) || source.width <= 0 || source.height <= 0 || source.width !== context.width || source.height !== context.height || !Number.isInteger(source.frame) || source.frame < 0) throw Error('Rozměry nebo snímek koordinačního obrazu neodpovídají.');
 if (source.origin !== 'top-left' || source.bbox_format !== 'xywh' || ![0,90,180,270].includes(source.rotation_ccw_degrees)) throw Error('Neplatný souřadnicový systém koordinačního obrazu.');
 const m = source.source_to_coordinate_pixel_edge_affine;
 const expected = {0:[[1,0,0],[0,1,0],[0,0,1]],90:[[0,1,0],[-1,0,source.height],[0,0,1]],180:[[-1,0,source.width],[0,-1,source.height],[0,0,1]],270:[[0,-1,source.width],[1,0,0],[0,0,1]]}[source.rotation_ccw_degrees];
 if (JSON.stringify(m) !== JSON.stringify(expected)) throw Error('Neplatná transformace koordinačního obrazu: očekávají se hrany pixelů, nikoli jejich středy.');
 return {coordinate_source:structuredClone(source),coordinate_system:{origin:'top-left',units:'coordinate-image-pixels',bbox_format:['x','y','width','height'],coordinate_source_id:source.id,coordinate_source_sha256:source.sha256}};
}
export function checkCoordinateBox(box, source) {
 if (!Array.isArray(box) || box.length !== 4 || !box.every(Number.isInteger) || box[0] < 0 || box[1] < 0 || box[2] <= 0 || box[3] <= 0 || box[0]+box[2] > source.width || box[1]+box[3] > source.height) throw Error('Oblast leží mimo koordinační obraz nebo má neplatné rozměry.');
}
export function coordinateMarkdown(proposal) {
 const c = proposal.coordinate_source;
 return c ? ['- Koordinační obraz: '+c.id,'- SHA-256 koordinačního obrazu: '+c.sha256,'- Rozměry koordinačního obrazu: '+c.width+' × '+c.height+' px','- Otočení od původního TIFF: '+c.rotation_ccw_degrees+'° proti směru hodinových ručiček','- Souřadnice: pixely koordinačního obrazu, nikoli neotočeného TIFF.'] : [];
}
