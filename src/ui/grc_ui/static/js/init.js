// Before the first paint: theme from localStorage, else the system preference.
(function () {
  var theme = null;
  try { theme = localStorage.getItem('gs-theme'); } catch (e) { /* storage blocked */ }
  if (theme !== 'fidonis-light' && theme !== 'fidonis-dark') {
    theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'fidonis-dark' : 'fidonis-light';
  }
  document.documentElement.setAttribute('data-theme', theme);
})();
