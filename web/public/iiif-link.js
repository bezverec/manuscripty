(() => {
 const link=document.getElementById('manifest-link');
 if (!link) return;
 if (window.MANUSCRIPT_FEATURES?.iiifManifest !== true) {link.hidden=true;link.removeAttribute('href');return;}
 link.href='/iiif/vkol-m-ii-220/manifest.json';link.hidden=false;
})();
