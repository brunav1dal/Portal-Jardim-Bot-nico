/* Objetivo: Abre e fecha o menu responsivo e mantém os estados de foco e acessibilidade sincronizados. */
(() => {
  // Isola variáveis deste módulo e procura os elementos necessários nesta página.
  const header = document.querySelector('.navbar');
  const toggle = header?.querySelector('.navbar-toggle');
  const content = header?.querySelector('.navbar-content');
  if (!toggle || !content) return;
  const compact = window.matchMedia('(max-width: 1100px)');
  // Sincroniza abertura, aria-expanded, foco e bloqueio dos links do menu recolhido.
  function setOpen(open, returnFocus = false) {
    toggle.setAttribute('aria-expanded', String(open));
    header.classList.toggle('is-menu-open', open);
    content.inert = compact.matches && !open;
    if (returnFocus) toggle.focus();
  }
  // Alterna a abertura ao pressionar o botão do menu.
  toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
  // Recolhe o menu depois que o visitante escolhe um link.
  content.addEventListener('click', event => {
    if (event.target.closest('a')) setOpen(false);
  });
  // Recolhe o menu quando o clique ocorre fora do cabeçalho.
  document.addEventListener('click', event => {
    if (!header.contains(event.target)) setOpen(false);
  });
  // Fecha com Escape e devolve o foco ao botão de abertura.
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setOpen(false, true);
  });
  // Recolhe o menu ao atravessar o limite entre navegação compacta e ampla.
  compact.addEventListener('change', () => setOpen(false));
  setOpen(false);
})();
