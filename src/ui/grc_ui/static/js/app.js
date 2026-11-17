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

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-action]');
    if (!btn) return;
    var action = btn.getAttribute('data-action');
    if (action === 'toggle-theme') {
      setTheme(document.documentElement.getAttribute('data-theme') === 'fidonis-dark' ? 'fidonis-light' : 'fidonis-dark');
    } else if (action === 'close-modal') {
      var m = document.getElementById('modal');
      if (m && m.open) m.close();
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

  document.addEventListener('DOMContentLoaded', function () {
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
    var modal = document.getElementById('modal');
    if (modal) modal.addEventListener('close', function () { document.getElementById('modal-body').innerHTML = ''; });
  });
})();
