/* Open the thematic detail addressed by old or new summary fragment links. */
(() => {
  function revealFragment() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    let detail = target.closest('details');
    while (detail) {
      detail.open = true;
      detail = detail.parentElement.closest('details');
    }
    target.scrollIntoView();
  }
  window.addEventListener('hashchange', revealFragment);
  revealFragment();
})();
