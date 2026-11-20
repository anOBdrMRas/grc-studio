// All page behaviour of GRC Studio (one IIFE, no texts of its own, no state store).
(function () {
  'use strict';

  function toast(kind, message) {
    var box = document.getElementById('toasts');
    if (!box || !message) return;
    var el = document.createElement('div');
    var cls = { success: 'alert alert-success', error: 'alert alert-error', warning: 'alert alert-warning', info: 'alert alert-info' };
    el.className = (cls[kind] || cls.info) + ' text-sm shadow';
    el.setAttribute('role', kind === 'error' || kind === 'warning' ? 'alert' : 'status');
    el.textContent = message;
    box.appendChild(el);
    setTimeout(function () { el.remove(); }, kind === 'error' ? 10000 : 5000);
  }
  window.gsToast = toast;

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('gs-theme', theme); } catch (e) { /* ignore */ }
    document.querySelectorAll('[data-action="toggle-theme"]').forEach(function (b) {
      b.setAttribute('aria-pressed', theme === 'fidonis-dark' ? 'true' : 'false');
    });
  }

  function closeModal() {
    var m = document.getElementById('modal');
    if (m && m.open) m.close();
  }
  // a fragment saved from the modal closes it (HX-Trigger: closeModal)
  document.body.addEventListener('closeModal', closeModal);

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-action]');
    if (!btn) return;
    var action = btn.getAttribute('data-action');
    if (action === 'toggle-theme') {
      setTheme(document.documentElement.getAttribute('data-theme') === 'fidonis-dark' ? 'fidonis-light' : 'fidonis-dark');
    } else if (action === 'close-modal') {
      closeModal();
    } else if (action === 'add-row') {
      var tpl = document.getElementById(btn.getAttribute('data-template'));
      var target = document.getElementById(btn.getAttribute('data-target'));
      if (tpl && target) target.appendChild(tpl.content.cloneNode(true));
    } else if (action === 'remove-row') {
      var row = btn.closest('[data-row]');
      if (row) row.remove();
    } else if (action === 'toggle-details') {
      var id = btn.getAttribute('aria-controls');
      var det = id && document.getElementById(id);
      if (det) {
        det.hidden = !det.hidden;
        btn.setAttribute('aria-expanded', det.hidden ? 'false' : 'true');
      }
    }
  });

  // a search box filtering check boxes (data-filter-choices + aria-controls)
  document.addEventListener('input', function (ev) {
    var input = ev.target;
    if (!input.hasAttribute || !input.hasAttribute('data-filter-choices')) return;
    var box = document.getElementById(input.getAttribute('aria-controls'));
    if (!box) return;
    var needle = input.value.trim().toLowerCase();
    box.querySelectorAll('[data-choice]').forEach(function (el) {
      el.hidden = needle !== '' && el.textContent.toLowerCase().indexOf(needle) === -1;
    });
  });

  // draggable divider between list and detail; the width is kept per browser
  var SPLIT_KEY = 'gs-split-list';
  function setSplit(split, px) {
    var max = split.clientWidth - 320;
    px = Math.max(220, Math.min(px, max));
    split.style.setProperty('--split-list', px + 'px');
    try { localStorage.setItem(SPLIT_KEY, String(Math.round(px))); } catch (e) { /* ignore */ }
  }
  function initSplit() {
    var handle = document.querySelector('[data-split-handle]');
    if (!handle) return;
    var split = handle.parentElement;
    var stored = null;
    try { stored = parseInt(localStorage.getItem(SPLIT_KEY), 10); } catch (e) { /* ignore */ }
    if (stored) split.style.setProperty('--split-list', stored + 'px');
    handle.addEventListener('pointerdown', function (ev) {
      ev.preventDefault();
      handle.setPointerCapture(ev.pointerId);
      handle.classList.add('is-dragging');
      document.body.classList.add('is-resizing');
      var left = split.getBoundingClientRect().left;
      function move(e) { setSplit(split, e.clientX - left); }
      function up() {
        handle.classList.remove('is-dragging');
        document.body.classList.remove('is-resizing');
        handle.removeEventListener('pointermove', move);
        handle.removeEventListener('pointerup', up);
      }
      handle.addEventListener('pointermove', move);
      handle.addEventListener('pointerup', up);
    });
    handle.addEventListener('keydown', function (ev) {
      var step = ev.shiftKey ? 80 : 20;
      var width = split.firstElementChild.getBoundingClientRect().width;
      if (ev.key === 'ArrowLeft') { setSplit(split, width - step); ev.preventDefault(); }
      if (ev.key === 'ArrowRight') { setSplit(split, width + step); ev.preventDefault(); }
    });
    handle.addEventListener('dblclick', function () {
      split.style.removeProperty('--split-list');
      try { localStorage.removeItem(SPLIT_KEY); } catch (e) { /* ignore */ }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initSplit();
    setTheme(document.documentElement.getAttribute('data-theme'));
    document.body.addEventListener('toast', function (ev) { toast(ev.detail.kind, ev.detail.message); });
    document.body.addEventListener('htmx:sendError', function () { toast('error', document.body.getAttribute('data-msg-unreachable')); });
    document.body.addEventListener('htmx:timeout', function () { toast('error', document.body.getAttribute('data-msg-unreachable')); });
    document.body.addEventListener('htmx:afterSwap', function (ev) {
      if (ev.detail.target && ev.detail.target.id === 'modal-body' && !ev.detail.xhr.getResponseHeader('HX-Reswap')) {
        var m = document.getElementById('modal');
        if (m && !m.open) m.showModal();
      }
    });
    // a chat form (data-chat) empties its question after an answer arrived and scrolls to it
    document.body.addEventListener('htmx:afterRequest', function (ev) {
      var form = ev.detail.elt;
      if (!ev.detail.successful || !form.matches || !form.matches('form[data-chat]')) return;
      var q = form.querySelector('[name="question"]');
      if (q) { q.value = ''; q.focus(); }
      var log = form.querySelector('[data-chat-log]');
      if (log) log.scrollTop = log.scrollHeight;
    });
    var modal = document.getElementById('modal');
    if (modal) modal.addEventListener('close', function () { document.getElementById('modal-body').innerHTML = ''; });
  });
})();
