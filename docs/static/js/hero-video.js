(() => {
  const hero = document.querySelector('.hero-video-banner');
  if (!hero) return;
  const video = hero.querySelector('video');
  const button = hero.querySelector('.hero-motion');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  function update() {
    hero.classList.toggle('is-paused', video.paused);
    button.textContent = video.paused ? 'Reproduzir vídeo' : 'Pausar vídeo';
    button.setAttribute('aria-label', video.paused ? 'Reproduzir vídeo de fundo e animação' : 'Pausar vídeo de fundo e animação');
  }
  async function play() {
    try { await video.play(); } catch { /* Keep the poster when autoplay is unavailable. */ }
    update();
  }
  video.muted = true;
  button.hidden = false;
  video.addEventListener('play', update);
  video.addEventListener('pause', update);
  video.addEventListener('error', () => { video.pause(); button.hidden = true; hero.classList.add('is-paused'); });
  button.addEventListener('click', () => { if (video.paused) play(); else video.pause(); });
  motion.addEventListener('change', () => { if (motion.matches) video.pause(); });
  if (motion.matches) { video.autoplay = false; video.pause(); update(); }
  else play();
})();
