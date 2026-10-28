(() => {
  const hero = document.querySelector('.hero-video-banner');
  if (!hero) return;
  const video = hero.querySelector('video');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  function update() {
    hero.classList.toggle('is-paused', video.paused);
  }
  async function play() {
    try { await video.play(); } catch { /* Keep the poster when autoplay is unavailable. */ }
    update();
  }
  video.muted = true;
  video.addEventListener('play', update);
  video.addEventListener('pause', update);
  video.addEventListener('error', () => { video.pause(); hero.classList.add('is-paused'); });
  motion.addEventListener('change', () => { if (motion.matches) video.pause(); else play(); });
  if (motion.matches) { video.autoplay = false; video.pause(); update(); }
  else play();
})();
