/* Objetivo: Ajusta o contraste do cabeçalho conforme sua posição sobre o vídeo de abertura. */
(() => {
  // Isola variáveis deste módulo e procura os elementos necessários nesta página.
  const header = document.querySelector('.navbar');
  if (!header) return;
  const hero = document.querySelector('.hero-video-banner');
  let pending = false;
  // Confere se o cabeçalho ainda sobrepõe o vídeo e ajusta sua classe de contraste.
  function update() {
    pending = false;
    const bounds = hero && hero.getBoundingClientRect();
    const height = header.getBoundingClientRect().height;
    header.classList.toggle('is-over-video', Boolean(bounds && bounds.top < height && bounds.bottom > height));
  }
  // Agrupa eventos de rolagem em um único quadro de renderização para reduzir trabalho repetido.
  function schedule() {
    if (!pending) { pending = true; requestAnimationFrame(update); }
  }
  // Reavalia o estado visual durante a rolagem sem bloquear o evento.
  window.addEventListener('scroll', schedule, { passive: true });
  // Recalcula a apresentação quando o tamanho da janela muda.
  window.addEventListener('resize', schedule);
  // Sincroniza a apresentação quando a página é exibida ou restaurada.
  window.addEventListener('pageshow', update);
  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(schedule);
    observer.observe(header);
    if (hero) observer.observe(hero);
  }
  update();
})();
