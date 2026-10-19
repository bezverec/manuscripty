export const LEGACY_DOCUMENT = 'vkol-m-ii-220';
export const COMMON_FIELDS = ['schema','id','created_utc','document_id','manuscript','folio','source_sha256','reason_cs','source_url','status','expert_review','coordinate_source','coordinate_system'];
export const HTR_FIELDS = [...COMMON_FIELDS,'line_id','source_segment_ids','bbox','model','model_label','original_htr','proposed_htr','crop_url'];
export const SEGMENTATION_FIELDS = [...COMMON_FIELDS,'document_uri','source_original','image_width','image_height','operation','original_segments','proposed_regions','preview_url'];
export const HTR_TEXT_FIELDS = new Set(['original_htr','proposed_htr']);
export function issueFormUrl(proposal, template, fields, title) {
 const url = new URL('https://github.com/bezverec/manuscripty/issues/new');
 url.searchParams.set('template',template);url.searchParams.set('title',title);
 for(const key of fields) if(proposal[key]!==undefined)url.searchParams.set(key,typeof proposal[key]==='string'&&!HTR_TEXT_FIELDS.has(key)?proposal[key]:JSON.stringify(proposal[key]));
 return url.href.length<=7500?url.href:null;
}
export function openProposalNumbers(index,documentId,folio,line) {
 const namespace=index?.documents?.[documentId] ?? (documentId===LEGACY_DOCUMENT?index:null);
 return [...new Set([namespace?.[folio]?.[line],namespace?.[folio]?.['*']].flatMap(v=>Array.isArray(v)?v:[]))].filter(n=>Number.isSafeInteger(n)&&n>0).sort((a,b)=>a-b);
}
