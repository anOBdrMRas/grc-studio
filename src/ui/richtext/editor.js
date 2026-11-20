// Rich text editor of work instructions (TipTap, bundled at build time into static/vendor/richtext.min.js).
// Markup: <div data-richtext data-name="content" data-placeholder="…" data-labels='{"bold": "…"}'> with a
// <textarea hidden name="content"> inside; the editor keeps the textarea in sync (the form posts it).
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import { TableKit } from '@tiptap/extension-table';
import TextAlign from '@tiptap/extension-text-align';
import Highlight from '@tiptap/extension-highlight';
import { Placeholder } from '@tiptap/extensions';

const MAX_SIDE = 1400;
// an embedded image larger than this is encoded again, smaller (the whole text may have 8 MB)
const MAX_IMAGE = 900 * 1024;

function readImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => {
      const src = String(reader.result);
      if (file.type === 'image/svg+xml' || file.size < 200000) return resolve(src);
      const img = new window.Image();
      img.onerror = () => resolve(src);
      img.onload = () => {
        let side = MAX_SIDE;
        let quality = 0.85;
        let out = '';
        for (let i = 0; i < 6; i++) {
          const scale = Math.min(1, side / Math.max(img.width, img.height));
          const canvas = document.createElement('canvas');
          canvas.width = Math.round(img.width * scale);
          canvas.height = Math.round(img.height * scale);
          canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
          // PNG keeps screenshots sharp; when it gets too large, JPEG
          out = canvas.toDataURL(file.type === 'image/png' && i === 0 ? 'image/png' : 'image/jpeg', quality);
          if (out.length <= MAX_IMAGE) break;
          side = Math.round(side * 0.8);
          quality = Math.max(0.5, quality - 0.1);
        }
        resolve(out);
      };
      img.src = src;
    };
    reader.readAsDataURL(file);
  });
}

async function insertImages(editor, files, pos) {
  const images = [...files].filter((f) => f.type.startsWith('image/'));
  for (const f of images) {
    const src = await readImage(f);
    const chain = editor.chain().focus();
    (pos !== undefined ? chain.insertContentAt(pos, { type: 'image', attrs: { src, alt: f.name } }) : chain.setImage({ src, alt: f.name })).run();
  }
  return images.length > 0;
}

// toolbar: [key, label, run, active?]
const BUTTONS = [
  ['bold', 'B', (c) => c.toggleBold(), (e) => e.isActive('bold')],
  ['italic', 'I', (c) => c.toggleItalic(), (e) => e.isActive('italic')],
  ['underline', 'U', (c) => c.toggleUnderline(), (e) => e.isActive('underline')],
  ['strike', 'S', (c) => c.toggleStrike(), (e) => e.isActive('strike')],
  ['highlight', '▍', (c) => c.toggleHighlight(), (e) => e.isActive('highlight')],
  '|',
  ['bullet', '•', (c) => c.toggleBulletList(), (e) => e.isActive('bulletList')],
  ['ordered', '1.', (c) => c.toggleOrderedList(), (e) => e.isActive('orderedList')],
  ['quote', '❝', (c) => c.toggleBlockquote(), (e) => e.isActive('blockquote')],
  '|',
  ['left', '⇤', (c) => c.setTextAlign('left'), (e) => e.isActive({ textAlign: 'left' })],
  ['center', '↔', (c) => c.setTextAlign('center'), (e) => e.isActive({ textAlign: 'center' })],
  ['right', '⇥', (c) => c.setTextAlign('right'), (e) => e.isActive({ textAlign: 'right' })],
  '|',
  ['link', '🔗', null, (e) => e.isActive('link')],
  ['image', '🖼', null],
  ['table', '▦', (c) => c.insertTable({ rows: 3, cols: 3, withHeaderRow: true })],
  ['table-tools'],
  '|',
  ['undo', '↶', (c) => c.undo()],
  ['redo', '↷', (c) => c.redo()],
];
const TABLE = [
  ['addRow', '+Z', (c) => c.addRowAfter()],
  ['addCol', '+S', (c) => c.addColumnAfter()],
  ['delRow', '−Z', (c) => c.deleteRow()],
  ['delCol', '−S', (c) => c.deleteColumn()],
  ['header', '⊟', (c) => c.toggleHeaderRow()],
  ['delTable', '✕▦', (c) => c.deleteTable()],
];

function button(key, label, title, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'rt-btn';
  b.textContent = label;
  b.title = title || key;
  b.setAttribute('aria-label', title || key);
  b.dataset.key = key;
  b.addEventListener('mousedown', (ev) => ev.preventDefault());
  b.addEventListener('click', onClick);
  return b;
}

function mount(root) {
  if (root.dataset.mounted) return;
  root.dataset.mounted = '1';
  const field = root.querySelector('textarea');
  const labels = JSON.parse(root.dataset.labels || '{}');
  const t = (k) => labels[k] || k;
  const toolbar = document.createElement('div');
  toolbar.className = 'rt-toolbar';
  toolbar.setAttribute('role', 'toolbar');
  toolbar.setAttribute('aria-label', t('formatting'));
  const area = document.createElement('div');
  const file = document.createElement('input');
  file.type = 'file';
  file.accept = 'image/*';
  file.multiple = true;
  file.hidden = true;
  root.append(toolbar, area, file);

  let editor;
  const sync = () => {
    field.value = editor.isEmpty ? '' : editor.getHTML();
    field.dispatchEvent(new Event('change', { bubbles: true }));
  };
  editor = new Editor({
    element: area,
    // no <style> element (CSP style-src 'self'): the editor styles are in app.css
    injectCSS: false,
    content: field.value || '',
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] }, link: { openOnClick: false, autolink: true } }),
      Image.configure({ allowBase64: true, resize: { enabled: true, minWidth: 60, minHeight: 40, alwaysPreserveAspectRatio: true } }),
      TableKit.configure({ table: { resizable: true } }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Highlight,
      Placeholder.configure({ placeholder: root.dataset.placeholder || '' }),
    ],
    editorProps: {
      attributes: { class: 'rt-content', 'aria-label': t('content'), role: 'textbox', 'aria-multiline': 'true' },
      handlePaste: (_view, event) => {
        const files = event.clipboardData ? event.clipboardData.files : [];
        if (![...files].some((f) => f.type.startsWith('image/'))) return false;
        insertImages(editor, files);
        return true;
      },
      handleDrop: (view, event) => {
        const files = event.dataTransfer ? event.dataTransfer.files : [];
        if (![...files].some((f) => f.type.startsWith('image/'))) return false;
        const pos = view.posAtCoords({ left: event.clientX, top: event.clientY });
        insertImages(editor, files, pos ? pos.pos : undefined);
        return true;
      },
    },
    onUpdate: sync,
  });

  const block = document.createElement('select');
  block.className = 'select select-bordered select-xs';
  block.setAttribute('aria-label', t('paragraph'));
  for (const [v, l] of [['p', t('text')], ['h1', t('h1')], ['h2', t('h2')], ['h3', t('h3')]]) {
    const o = document.createElement('option');
    o.value = v;
    o.textContent = l;
    block.append(o);
  }
  block.addEventListener('change', () => {
    const c = editor.chain().focus();
    (block.value === 'p' ? c.setParagraph() : c.toggleHeading({ level: Number(block.value.slice(1)) })).run();
  });
  toolbar.append(block);

  const tableTools = document.createElement('span');
  tableTools.className = 'rt-table-tools';
  for (const [key, label, run] of TABLE) tableTools.append(button(key, label, t(key), () => run(editor.chain().focus()).run()));
  const buttons = [];
  for (const def of BUTTONS) {
    if (def === '|') {
      const s = document.createElement('span');
      s.className = 'rt-sep';
      toolbar.append(s);
      continue;
    }
    const [key, label, run, active] = def;
    if (key === 'table-tools') {
      toolbar.append(tableTools);
      continue;
    }
    const b = button(key, label, t(key), () => {
      if (key === 'image') return file.click();
      if (key === 'link') {
        const prev = editor.getAttributes('link').href;
        const url = window.prompt(t('linkPrompt'), prev || 'https://');
        if (url === null) return;
        const c = editor.chain().focus().extendMarkRange('link');
        (url.trim() ? c.setLink({ href: url.trim() }) : c.unsetLink()).run();
        return;
      }
      run(editor.chain().focus()).run();
    });
    buttons.push([b, key, active]);
    toolbar.append(b);
  }
  const refresh = () => {
    for (const [b, key, active] of buttons) {
      const on = active ? active(editor) : false;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', String(on));
      if (key === 'undo') b.disabled = !editor.can().undo();
      if (key === 'redo') b.disabled = !editor.can().redo();
    }
    tableTools.hidden = !editor.isActive('table');
    block.value = [1, 2, 3].find((l) => editor.isActive('heading', { level: l })) ? `h${[1, 2, 3].find((l) => editor.isActive('heading', { level: l }))}` : 'p';
  };
  editor.on('transaction', refresh);
  refresh();
  file.addEventListener('change', () => {
    const files = file.files;
    insertImages(editor, files).finally(() => (file.value = ''));
  });
  root.editor = editor;
}

window.GrcRichText = { mount };
