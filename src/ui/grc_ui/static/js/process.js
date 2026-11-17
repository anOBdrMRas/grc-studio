// BPMN editor island (deviation A3): the diagram is edited in the browser and saved through the interface to the API.
(function () {
  'use strict';
  var el = document.getElementById('bpmn-canvas');
  if (!el || !window.BpmnJS) return;
  var pid = el.getAttribute('data-process');
  var editable = el.getAttribute('data-editable') === 'true';
  var modeler = new window.BpmnJS({ container: el });
  var version = null;
  var dirty = false;
  var saveBtn = document.querySelector('[data-action="save-diagram"]');
  var state = document.getElementById('diagram-state');
  var ACTIVITIES = ['bpmn:Task', 'bpmn:UserTask', 'bpmn:ServiceTask', 'bpmn:ManualTask', 'bpmn:ScriptTask', 'bpmn:BusinessRuleTask',
    'bpmn:SendTask', 'bpmn:ReceiveTask', 'bpmn:SubProcess', 'bpmn:CallActivity'];

  function csrf() {
    try { return JSON.parse(document.body.getAttribute('hx-headers'))['X-CSRF-Token']; } catch (e) { return ''; }
  }

  function setVersion(v) {
    if (!v) return;
    version = String(v);
    // keep the version of the other forms of this page current (workflow bar, step panel)
    document.querySelectorAll('#wfbar input[name="version"], #step-panel input[name="version"]').forEach(function (i) { i.value = version; });
  }

  function setDirty(d) {
    dirty = d;
    if (saveBtn) saveBtn.disabled = !d;
    if (state) state.textContent = d ? state.getAttribute('data-msg-dirty') : '';
  }

  function badges() {
    fetch('/processes/' + encodeURIComponent(pid) + '/badges.json', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (counts) {
        var overlays = modeler.get('overlays');
        overlays.remove({ type: 'roles' });
        Object.keys(counts).forEach(function (id) {
          var badge = document.createElement('span');
          badge.className = 'bpmn-badge';
          badge.textContent = counts[id] + ' R';
          try { overlays.add(id, 'roles', { position: { top: -9, right: 12 }, html: badge }); } catch (e) { /* element no longer in the diagram */ }
        });
      });
  }

  fetch('/processes/' + encodeURIComponent(pid) + '/diagram.xml', { credentials: 'same-origin' })
    .then(function (r) { setVersion(r.headers.get('X-Version')); return r.text(); })
    .then(function (xml) { return modeler.importXML(xml); })
    .then(function () {
      modeler.get('canvas').zoom('fit-viewport');
      badges();
      if (editable) modeler.on('commandStack.changed', function () { setDirty(true); });
    });

  modeler.on('element.click', function (e) {
    var bo = e.element.businessObject;
    if (!bo || ACTIVITIES.indexOf(bo.$type) === -1) return;
    var url = '/processes/' + encodeURIComponent(pid) + '/steps/' + encodeURIComponent(e.element.id) + '?name=' + encodeURIComponent(bo.name || '');
    window.htmx.ajax('GET', url, { target: '#step-panel', swap: 'innerHTML' });
  });

  document.body.addEventListener('htmx:afterSettle', function () {
    // the newest version is on the workflow bar or the step panel, whichever was swapped last
    var holders = document.querySelectorAll('[data-process-version]');
    var max = null;
    holders.forEach(function (h) { var v = Number(h.getAttribute('data-process-version')); if (max === null || v > max) max = v; });
    if (max !== null && String(max) !== version) setVersion(max);
  });
  document.body.addEventListener('badgesChanged', badges);

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-action]');
    if (!btn) return;
    var canvas = modeler.get('canvas');
    var action = btn.getAttribute('data-action');
    if (action === 'zoom-in') canvas.zoom(canvas.zoom() * 1.2);
    else if (action === 'zoom-out') canvas.zoom(canvas.zoom() / 1.2);
    else if (action === 'zoom-fit') canvas.zoom('fit-viewport');
    else if (action === 'save-diagram') {
      btn.disabled = true;
      modeler.saveXML({ format: true }).then(function (res) {
        return fetch('/processes/' + encodeURIComponent(pid) + '/diagram', {
          method: 'PUT',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf() },
          body: JSON.stringify({ xml: res.xml, version: Number(version) })
        });
      }).then(function (r) {
        return r.json().then(function (body) { return { ok: r.ok, body: body }; });
      }).then(function (res) {
        if (res.ok) {
          setVersion(res.body.version);
          setDirty(false);
          if (state) state.textContent = state.getAttribute('data-msg-saved');
          window.gsToast('success', res.body.message);
          badges();
          document.body.dispatchEvent(new CustomEvent('processChanged'));
        } else {
          btn.disabled = false;
          window.gsToast('error', res.body.message);
        }
      });
    }
  });

  window.addEventListener('beforeunload', function (ev) {
    if (dirty) { ev.preventDefault(); ev.returnValue = el.getAttribute('data-msg-unsaved-leave'); }
  });
})();
