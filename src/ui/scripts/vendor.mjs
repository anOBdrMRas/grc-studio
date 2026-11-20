// Copies the browser libraries, fonts and icons out of node_modules (build time only, no CDN).
import { cpSync, mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const nm = join(root, 'node_modules');
const stat = join(root, 'grc_ui', 'static');
const copy = (from, to) => {
  mkdirSync(dirname(to), { recursive: true });
  cpSync(join(nm, from), to, { recursive: true });
};

copy('htmx.org/dist/htmx.min.js', join(stat, 'vendor/htmx.min.js'));
copy('@alpinejs/csp/dist/cdn.min.js', join(stat, 'vendor/alpine-csp.min.js'));
copy('sortablejs/Sortable.min.js', join(stat, 'vendor/sortable.min.js'));
copy('bpmn-js/dist/bpmn-modeler.production.min.js', join(stat, 'vendor/bpmn-modeler.min.js'));
copy('bpmn-js/dist/bpmn-navigated-viewer.production.min.js', join(stat, 'vendor/bpmn-viewer.min.js'));
copy('bpmn-js/dist/assets/diagram-js.css', join(stat, 'vendor/bpmn/diagram-js.css'));
copy('bpmn-js/dist/assets/bpmn-js.css', join(stat, 'vendor/bpmn/bpmn-js.css'));
copy('bpmn-js/dist/assets/bpmn-font/css/bpmn.css', join(stat, 'vendor/bpmn/bpmn-font/css/bpmn.css'));
copy('bpmn-js/dist/assets/bpmn-font/font', join(stat, 'vendor/bpmn/bpmn-font/font'));

const fonts = [
  ['@fontsource/manrope/files/manrope-latin-500-normal.woff2', 'manrope-500.woff2'],
  ['@fontsource/manrope/files/manrope-latin-700-normal.woff2', 'manrope-700.woff2'],
  ['@fontsource/manrope/files/manrope-latin-800-normal.woff2', 'manrope-800.woff2'],
  ['@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-400-normal.woff2', 'plex-400.woff2'],
  ['@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-500-normal.woff2', 'plex-500.woff2'],
  ['@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-600-normal.woff2', 'plex-600.woff2'],
];
for (const [from, to] of fonts) copy(from, join(stat, 'fonts/files', to));

// the icon subset (Tabler outline), inlined by grc_ui/icons.py
const icons = ['home', 'pencil', 'trash', 'history', 'file-description', 'check', 'x', 'arrow-back-up', 'device-floppy', 'plus',
  'search', 'lock', 'logout', 'settings', 'sun', 'moon', 'eye', 'alert-triangle', 'chevron-down', 'refresh', 'user', 'zoom-in', 'zoom-out', 'focus-centered', 'download', 'upload', 'sparkles'];
for (const name of icons) {
  const src = join(nm, '@tabler/icons/icons/outline', `${name}.svg`);
  if (!existsSync(src)) throw new Error(`icon ${name} missing`);
  writeFileSync(join(root, 'grc_ui/icons', `${name}.svg`), readFileSync(src, 'utf8'));
}

// licences for THIRD_PARTY_LICENSES.md
for (const pkg of ['htmx.org', '@alpinejs/csp', 'sortablejs', 'bpmn-js', 'diagram-js', '@fontsource/manrope', '@fontsource/ibm-plex-sans', '@tabler/icons', '@tiptap/core', 'prosemirror-model', 'prosemirror-view', 'prosemirror-state']) {
  for (const f of ['LICENSE', 'LICENSE.md', 'LICENSE.txt']) {
    const p = join(nm, pkg, f);
    if (existsSync(p)) {
      copy(join(pkg, f), join(stat, 'vendor/licenses', `${pkg.replace(/[@/]/g, '_')}.txt`));
      break;
    }
  }
}
console.log('vendored');
