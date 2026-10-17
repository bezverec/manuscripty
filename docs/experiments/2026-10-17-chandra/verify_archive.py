"""Verify text-only publication and recorded evidence, without original scans."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,re
from urllib.parse import urlsplit,unquote

ARCHIVE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))

def main():
    manifest=load(ARCHIVE/'publication-manifest.json')
    for entry in manifest['files']:
        assert sha(ARCHIVE/entry['published'])==entry['published_sha256'],entry['published']
    assert len(manifest['files'])==manifest['file_count']==85
    assert sum(e['bytes'] for e in manifest['files'])==manifest['total_bytes']
    files=[p for p in ARCHIVE.rglob('*') if p.is_file()]
    disallowed={'.png','.jpg','.jpeg','.webp','.tif','.tiff','.gif','.svg','.bin','.safetensors','.pt','.mlmodel','.zip'}
    credentials=re.compile(r'AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{30,}')
    embedded_image=re.compile(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]{120,}')
    parsed_json=0; parsed_python=0
    for p in files:
        assert p.suffix.lower() not in disallowed,p
        assert p.name not in {'.env','index.html'},p
        text=p.read_text(encoding='utf-8')
        assert not credentials.search(text),f'Credential signature in {p.relative_to(ARCHIVE)}'
        assert not embedded_image.search(text),f'Embedded image in {p.relative_to(ARCHIVE)}'
        if p.suffix=='.json':load(p);parsed_json+=1
        if p.suffix=='.py':ast.parse(text);parsed_python+=1
    broken=[]; link_count=0
    authored=[ARCHIVE/'README.md',*(ARCHIVE/n/'report.md' for n in ['chandra-segmentation-pilot-20261017','chandra-kraken-hybrid-20261017'])]
    for p in authored:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            parsed=urlsplit(target)
            if parsed.scheme or not parsed.path:continue
            resolved=(p.parent/unquote(parsed.path)).resolve()
            if resolved==ARCHIVE/'archive-validation.json':continue
            link_count+=1
            if not resolved.is_file():broken.append({'file':str(p.relative_to(ARCHIVE)),'target':target})
    assert not broken,broken
    hybrid=ARCHIVE/'chandra-kraken-hybrid-20261017'
    summary=load(hybrid/'summary.json');control=load(hybrid/'scale-control-335v.json')
    assert summary['status']=='complete' and len(summary['pages'])==8
    assert control['status']=='complete' and control['line_count']==20
    assert load(hybrid/'local-run-validation.json')['passed']
    assert load(ARCHIVE/'chandra-segmentation-pilot-20261017/local-run-validation.json')['passed']
    expected={('mii220-335v','tight'):23,('mii220-335v','padding64'):28,('mii220-20v','tight'):82,('mii220-20v','padding64'):86,('mii153-5r','tight'):80,('mii153-5r','padding64'):80,('mii220-335v-header-original','tight'):5,('mii220-335v-header-original','padding64'):5}
    for result in summary['pages']:
        assert expected[(result['id'],result['variant'])]==result['line_count']
        assert not result['errors']
        assert result==load(hybrid/result['id']/result['variant']/'result.json')
    result=dict(passed=True,checked_utc=datetime.now(timezone.utc).isoformat(),
                scope='Text-only Git archive, separate from archived original local-run validation with images',
                manifest_entries_verified=85,json_files_parsed=parsed_json,python_sources_parsed=parsed_python,
                local_markdown_links_checked=link_count,broken_local_markdown_links=broken,
                manuscript_images_included=False,model_weights_included=False,
                credential_signature_scan='No matches in included UTF-8 files; not a full repository-history audit',
                hybrid_variants_verified=8,scale_control_segments=20,
                recognition_accuracy_measured=False,expert_reference_available=False,
                conclusion='Incremental benefit of Chandra not demonstrated on these pilot samples; page-height normalization is a confounding factor exposed by the scale control.')
    (ARCHIVE/'archive-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
