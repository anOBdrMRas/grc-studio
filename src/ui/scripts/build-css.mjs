// brand + app → static/app.css (Tailwind takes one input; the @tailwind directives lead).
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const input = join(root, '.tailwind.input.css');
writeFileSync(input, readFileSync(join(root, 'tailwind.brand.css'), 'utf8') + '\n' + readFileSync(join(root, 'tailwind.app.css'), 'utf8'));
const args = [join(root, 'node_modules/tailwindcss/lib/cli.js'), '-c', join(root, 'tailwind.config.js'), '-i', input, '-o', join(root, 'grc_ui/static/app.css'), '--minify',
  '--content', `${join(root, 'grc_ui/templates')}/**/*.html,${join(root, 'grc_ui/static/js')}/*.js,${join(root, 'grc_ui')}/*.py`];
if (process.argv.includes('--watch')) args.push('--watch');
execFileSync(process.execPath, args, { stdio: 'inherit' });
