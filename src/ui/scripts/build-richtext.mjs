// The rich text editor (TipTap) as one browser file: static/vendor/richtext.min.js (build time only).
import { build } from 'esbuild';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
await build({
  entryPoints: [join(root, 'richtext/editor.js')],
  outfile: join(root, 'grc_ui/static/vendor/richtext.min.js'),
  bundle: true,
  minify: true,
  format: 'iife',
  target: 'es2020',
  legalComments: 'eof',
});
console.log('richtext bundled');
