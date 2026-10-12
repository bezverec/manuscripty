(() => {
  'use strict';
  const body = document.querySelector('.app-body');
  const left = document.getElementById('thumbs');
  const right = document.getElementById('text-panel');
  const divider = document.getElementById('panel-resizer');
  const leftButton = document.getElementById('toggle-thumbs');
  const rightButton = document.getElementById('toggle-text-panel');
  const desktop = window.matchMedia('(min-width: 961px)');
  const storageKey = 'manuscripty:viewer-layout:v1';
  const minimumPanel = 320, minimumScan = 320;
  let preferences = { left: true, right: true, width: null };
  let drag = null;
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    if (saved && typeof saved === 'object') {
      if (typeof saved.left === 'boolean') preferences.left = saved.left;
      if (typeof saved.right === 'boolean') preferences.right = saved.right;
      if (Number.isFinite(saved.width)) preferences.width = Math.max(minimumPanel, Math.min(2400, saved.width));
    }
  } catch { /* Layout also works without browser storage. */ }
  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify(preferences)); } catch {}
  }
  function limits() {
    const narrow = window.matchMedia('(max-width: 1100px)').matches;
    const thumbnailWidth = preferences.left ? (narrow ? 76 : 100) : 0;
    return { defaultWidth: narrow ? 440 : 520, max: Math.max(minimumPanel, body.clientWidth - thumbnailWidth - 12 - minimumScan) };
  }
  function render() {
    const bounds = limits();
    const width = Math.round(Math.min(bounds.max, Math.max(minimumPanel, preferences.width ?? bounds.defaultWidth)));
    left.hidden = !preferences.left;
    right.hidden = !preferences.right;
    body.classList.toggle('without-thumbs', !preferences.left);
    body.classList.toggle('without-text-panel', !preferences.right);
    body.style.setProperty('--text-panel-width', width + 'px');
    const leftLabel = preferences.left ? 'Skrýt náhledy' : 'Zobrazit náhledy';
    leftButton.setAttribute('aria-label', leftLabel); leftButton.title = leftLabel;
    leftButton.querySelector('path').setAttribute('d', preferences.left ? 'M15 6l-6 6 6 6' : 'M9 6l6 6-6 6');
    const rightLabel = preferences.right ? 'Skrýt textový panel' : 'Zobrazit textový panel';
    rightButton.setAttribute('aria-label', rightLabel); rightButton.title = rightLabel;
    rightButton.querySelector('path').setAttribute('d', preferences.right ? 'M9 6l6 6-6 6' : 'M15 6l-6 6 6 6');
    leftButton.setAttribute('aria-expanded', String(preferences.left));
    rightButton.setAttribute('aria-expanded', String(preferences.right));
    divider.parentElement.hidden = !preferences.right || !desktop.matches;
    divider.setAttribute('aria-valuemin', String(minimumPanel));
    divider.setAttribute('aria-valuemax', String(Math.round(bounds.max)));
    divider.setAttribute('aria-valuenow', String(width));
    divider.setAttribute('aria-valuetext', width + ' pixelů');
  }
  function setWidth(width) {
    preferences.width = Math.round(Math.max(minimumPanel, Math.min(limits().max, width)));
    render();
  }
  function finishDrag() {
    if (!drag) return;
    const id = drag.id;
    drag = null;
    body.classList.remove('is-resizing');
    if (divider.hasPointerCapture(id)) divider.releasePointerCapture(id);
    save();
  }
  leftButton.addEventListener('click', () => { preferences.left = !preferences.left; render(); save(); });
  rightButton.addEventListener('click', () => { finishDrag(); preferences.right = !preferences.right; render(); save(); });
  window.addEventListener('manuscripty:show-panel', () => {
    if (!preferences.right) { preferences.right = true; render(); save(); }
  });
  divider.addEventListener('pointerdown', event => {
    if (event.button !== 0 || !desktop.matches) return;
    event.preventDefault();
    drag = { id: event.pointerId, x: event.clientX, width: right.getBoundingClientRect().width };
    divider.focus();
    divider.setPointerCapture(event.pointerId);
    body.classList.add('is-resizing');
  });
  divider.addEventListener('pointermove', event => {
    if (drag && drag.id === event.pointerId) setWidth(drag.width + drag.x - event.clientX);
  });
  divider.addEventListener('pointerup', finishDrag);
  divider.addEventListener('pointercancel', finishDrag);
  divider.addEventListener('lostpointercapture', finishDrag);
  window.addEventListener('blur', finishDrag);
  divider.addEventListener('keydown', event => {
    const width = right.getBoundingClientRect().width;
    const step = event.shiftKey ? 100 : 40;
    const next = event.key === 'ArrowLeft' ? width + step : event.key === 'ArrowRight' ? width - step : event.key === 'Home' ? minimumPanel : event.key === 'End' ? limits().max : null;
    if (next !== null) { event.preventDefault(); setWidth(next); save(); }
  });
  divider.addEventListener('dblclick', () => { preferences.width = null; render(); save(); });
  window.addEventListener('resize', () => { finishDrag(); render(); });
  desktop.addEventListener('change', render);
  render();
})();
