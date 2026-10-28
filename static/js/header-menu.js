(() => {
  const header = document.querySelector('.navbar');
  const toggle = header?.querySelector('.navbar-toggle');
  const content = header?.querySelector('.navbar-content');
  if (!toggle || !content) return;
  const compact = window.matchMedia('(max-width: 1100px)');
  function setOpen(open, returnFocus = false) {
    toggle.setAttribute('aria-expanded', String(open));
    header.classList.toggle('is-menu-open', open);
    content.inert = compact.matches && !open;
    if (returnFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
  content.addEventListener('click', event => {
    if (event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('click', event => {
    if (!header.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setOpen(false, true);
  });
  compact.addEventListener('change', () => setOpen(false));
  setOpen(false);
})();
