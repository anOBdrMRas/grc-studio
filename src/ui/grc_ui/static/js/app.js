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

  // questions before deleting, revoking …: the application's own dialog instead of window.confirm
  var pendingConfirm = null;
  document.addEventListener('htmx:confirm', function (ev) {
    var question = ev.detail.question;
    var dlg = document.getElementById('confirm-dialog');
    if (!question || !dlg) return;
    ev.preventDefault();
    var label = (ev.detail.elt.textContent || '').trim() || ev.detail.elt.getAttribute('aria-label') || '';
    var yes = dlg.querySelector('[data-confirm=yes]');
    yes.textContent = label && label.length <= 30 ? label : yes.getAttribute('data-default-label');
    dlg.querySelector('[data-confirm-text]').textContent = question;
    pendingConfirm = ev.detail;
    dlg.showModal();
    dlg.querySelector('[data-confirm=no]').focus();
  });
  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest('#confirm-dialog [data-confirm]');
    if (!btn) return;
    var detail = pendingConfirm;
    pendingConfirm = null;
    document.getElementById('confirm-dialog').close();
    if (detail && btn.getAttribute('data-confirm') === 'yes') detail.issueRequest(true);
  });

  document.addEventListener('DOMContentLoaded', function () {
    var cd = document.getElementById('confirm-dialog');
    if (cd) cd.addEventListener('close', function () { pendingConfirm = null; });
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
