import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root = path.dirname(fileURLToPath(import.meta.url));
const destination = path.join(root, 'public', 'binding-media');
const manifest = JSON.parse(await fs.readFile(path.join(root, 'binding-media-manifest.json'), 'utf8'));
const mode = process.argv[2];
if (process.argv.length > 3 || (mode && !['--check', '--verify-local'].includes(mode))) {
  throw new Error('Usage: node restore_binding_media.mjs [--check|--verify-local]');
}
if (manifest.origin !== 'https://rukopisy.digitalizaty.cz/binding-media/') throw new Error('Unexpected media origin');
const seen = new Set();
for (const o of manifest.objects) {
  if (!/^v1\/(?:previews\/(?:FC|FS|F001r|F001v|BS|BC|SP)|tiles\/(?:FC|FS|F001r|F001v|BS|BC|SP)\/\d+\/\d+_\d+)\.webp$/.test(o.key)
      || !/^[a-f0-9]{64}$/.test(o.sha256) || !Number.isInteger(o.bytes) || o.bytes < 1 || seen.has(o.key)) {
    throw new Error('Invalid or duplicate media manifest entry');
  }
  seen.add(o.key);
}
if (manifest.objects.length !== 1175) throw new Error('Incomplete binding media manifest');
const matches = (b, o) => b.length === o.bytes && createHash('sha256').update(b).digest('hex') === o.sha256;
let restored = 0, reused = 0;
if (mode !== '--check') {
  // Bounded parallel transfers; files remain outside Git and no credentials are used.
  let next = 0;
  await Promise.all(Array.from({length: 4}, async () => {
    while (next < manifest.objects.length) {
      const o = manifest.objects[next++], target = path.join(destination, o.key);
      try {
        if (matches(await fs.readFile(target), o)) { reused++; continue; }
      } catch (e) { if (e.code !== 'ENOENT') throw e; }
      if (mode === '--verify-local') throw new Error('Missing or corrupt binding media: ' + o.key);
      const response = await fetch(manifest.origin + o.key, {signal: AbortSignal.timeout(30000)});
      if (!response.ok || !response.headers.get('content-type')?.startsWith('image/webp')) throw new Error('Media download failed: ' + o.key);
      const bytes = Buffer.from(await response.arrayBuffer());
      if (!matches(bytes, o)) throw new Error('Media checksum mismatch: ' + o.key);
      await fs.mkdir(path.dirname(target), {recursive: true});
      await fs.writeFile(target, bytes);
      restored++;
      if (restored % 100 === 0) console.log('Restored ' + restored + ' binding objects');
    }
  }));
}
console.log(JSON.stringify({status: 'passed', mode: mode || 'restore', objects: manifest.objects.length,
  bytes: manifest.objects.reduce((n, o) => n + o.bytes, 0), restored, reused}));
