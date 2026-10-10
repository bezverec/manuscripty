from pathlib import Path
import hashlib,json,zipfile,datetime
HERE=Path(__file__).resolve().parents[1]
TARGET=HERE/'proarc-ocr-next-100-pages.zip'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((HERE/'manifest.json').read_text());v=json.loads((HERE/'validation.json').read_text());assert v['all_checks_passed'] and m['status']=='success'
assert len(list((HERE/'import').glob('*.ocr.txt')))==len(list((HERE/'import').glob('*.ocr.xml')))==100
excluded={'proarc-ocr-next-100-pages.zip','proarc-ocr-next-100-pages.zip.sha256','package-check.json','SHA256SUMS.txt'}
files=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name not in excluded)
(HERE/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(HERE).as_posix()+'\n' for p in files),encoding='utf-8')
files.append(HERE/'SHA256SUMS.txt')
with zipfile.ZipFile(TARGET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,p.relative_to(HERE).as_posix())
with zipfile.ZipFile(TARGET) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)
 for p in files:assert hashlib.sha256(z.read(p.relative_to(HERE).as_posix())).hexdigest()==sha(p)
checksum=sha(TARGET)
(HERE/(TARGET.name+'.sha256')).write_text(checksum+'  '+TARGET.name+'\n',encoding='ascii')
result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'zip':TARGET.name,'zip_sha256':checksum,'zip_bytes':TARGET.stat().st_size,'members':len(files),'ocr_xml':100,'ocr_txt':100,'zip_crc_and_file_hashes_valid':True,'schema_valid_pages':100,'zero_width_words':0,'full_psp':False,'live_import_tested':False}
(HERE/'package-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result),flush=True)
