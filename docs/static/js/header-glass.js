(() => {
  const header = document.querySelector('.navbar');
  if (!header) return;
  const hero = document.querySelector('.hero-video-banner');
  let pending = false;
  function update() {
    pending = false;
    const bounds = hero && hero.getBoundingClientRect();
    const height = header.getBoundingClientRect().height;
    header.classList.toggle('is-over-video', Boolean(bounds && bounds.top < height && bounds.bottom > height));
  }
  function schedule() {
    if (!pending) { pending = true; requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  window.addEventListener('pageshow', update);
  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(schedule);
    observer.observe(header);
    if (hero) observer.observe(hero);
  }
  update();
})();
