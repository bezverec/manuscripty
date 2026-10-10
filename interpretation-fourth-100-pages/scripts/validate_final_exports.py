"""Read back all 100 fourth-batch exports and validate their recorded evidence."""
from pathlib import Path
import json, hashlib, datetime
from lxml import etree as E
J=Path(__file__).resolve().parents[1]
ROOT=J.parent
assert J.name=="interpretation-fourth-100-pages"
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b""): h.update(block)
 return h.hexdigest()
raw=read(ROOT/"htr-fourth-100-pages/manifest.json")
manifest=read(J/"manifest.json")
validation=read(J/"validation.json")
assert len(raw["pages"])==100 and len(manifest["pages"])==100
assert manifest["status"]=="complete" and validation["status"]=="passed"
assert manifest["new_interpretations_completed"]==100
assert validation["tei_rng_valid_files"]==100 and validation["local_html_links_valid"] is True
schema=ROOT/"medieval-manuscript-transcription/schemas/tei-p5-4.12.0/tei_all.rng"
assert sha(schema)==manifest["rng_sha256"]
rng=E.RelaxNG(E.parse(str(schema),E.XMLParser(no_network=True,resolve_entities=False)))
assert {p["folio"] for p in raw["pages"]}=={p["folio"] for p in manifest["pages"]}
records={p["folio"]:p for p in manifest["pages"]}
checks={p["folio"]:p for p in validation["checks"]}
details=[]
for n,src in enumerate(raw["pages"],1):
 f=src["folio"]; out=J/f; rec=records[f]; check=checks[f]
 d=read(out/"reconstruction.json")
 cat=read(ROOT/"htr-fourth-100-pages/pages"/f/"catmus.candidates.json")["lines"]
 med=read(ROOT/"htr-fourth-100-pages/pages"/f/"medusa.candidates.json")["lines"]
 ids=[x["id"] for x in cat]
 assert ids==[x["id"] for x in med]==[x for p in d["passages"] for x in p["source_segment_ids"]],f+" coverage/order"
 assert len(ids)==len(set(ids))
 assert d["expert_reference"] is False and d["cer"] is None and d["wer"] is None
 assert all(p["human_reviewed"] is False and p["status"]=="proposed" for p in d["passages"])
 if "human_reviewed" in d: assert d["human_reviewed"] is False
 if "status" in d: assert d["status"]=="proposed"
 assert sha(ROOT/src["original"])==src["original_sha256"]==rec["original_sha256"]==d["source_sha256"]
 assert sha(out/"reconstruction.json")==rec["reconstruction_sha256"]
 assert sha(ROOT/"htr-fourth-100-pages/pages"/f/"catmus.candidates.json")==rec["original_catmus_sha256"]
 assert sha(ROOT/"htr-fourth-100-pages/pages"/f/"medusa.candidates.json")==rec["original_medusa_sha256"]
 for name,digest in rec["exports_sha256"].items(): assert sha(out/name)==digest,(f,name)
 tei=E.parse(str(out/"reconstruction.tei.xml"),E.XMLParser(no_network=True,resolve_entities=False))
 assert rng.validate(tei),(f,str(rng.error_log))
 assert tei.getroot().get("version")=="4.12.0"
 assert check["tei_rng_valid"] is True and check["all_segments_covered_once_in_order"] is True
 assert check["opened_native_tiles_pixel_verified"] is True
 assert check["native_zone_coverage_verified"] is True
 details.append({"folio":f,"tei_disk_relaxng_valid":True,"sha_original_and_recorded_outputs_match":True,
                 "both_htr_exact_id_order_and_passage_coverage":True,
                 "native_pixels_and_selected_zone_coverage_export_verified":True})
 if n%25==0: print("DISK_READBACK",n,"/ 100",flush=True)
report={"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"status":"passed",
        "pages":100,"previous_interpretations":330,"total_interpretations":430,"segments":sum(x["segments"] for x in manifest["pages"]),
        "passages":sum(x["passages"] for x in manifest["pages"]),
        "tei_relaxng_version":"4.12.0","tei_disk_relaxng_valid_files":100,"rng_sha256":sha(schema),
        "html_link_existence_and_fragments_export_verified":True,
        "html_links_checked":validation["local_html_links_checked"],
        "expert_reference":False,"does_not_establish_paleographic_or_translation_correctness":True,
        "checks":details}
(J/"final-readback-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("FINAL_READBACK_PASSED",report["pages"],report["segments"],report["passages"],flush=True)
