/* Apply the saved/system theme before first paint; keep manuscript pixels intact. */
(() => {
  'use strict';
  const key = 'manuscripty-theme';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let preference = null;
  try {
    const saved = localStorage.getItem(key);
    if (saved === 'light' || saved === 'dark') preference = saved;
  } catch { /* The toggle also works when browser storage is unavailable. */ }
  function apply() {
    const dark = (preference || (system.matches ? 'dark' : 'light')) === 'dark';
    root.dataset.theme = dark ? 'dark' : 'light';
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.setAttribute('aria-pressed', String(dark));
      button.title = dark ? 'Zapnout světlý režim' : 'Zapnout noční režim';
      button.querySelector('[data-theme-icon]').innerHTML = dark
        ? '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"></path>'
        : '<path d="M20.5 13A8.5 8.5 0 0 1 11 3.5 8.5 8.5 0 1 0 20.5 13Z"></path>';
    });
  }
  apply();
  function mount() {
    const host = document.querySelector('.app-header .app-actions') || document.querySelector('.site-header .container');
    if (!host || host.querySelector('[data-theme-toggle]')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn--sm theme-toggle';
    button.setAttribute('data-theme-toggle', '');
    button.setAttribute('aria-label', 'Noční režim');
    button.innerHTML = '<svg data-theme-icon width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"></svg><span class="theme-label">Noční režim</span>';
    button.addEventListener('click', () => {
      preference = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(key, preference); } catch { /* Session-only choice. */ }
      apply();
    });
    if (host.classList.contains('app-actions')) host.prepend(button);
    else host.append(button);
    apply();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once:true});
  else mount();
  system.addEventListener('change', () => { if (!preference) apply(); });
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    preference = event.newValue === 'dark' || event.newValue === 'light' ? event.newValue : null;
    apply();
  });
})();
