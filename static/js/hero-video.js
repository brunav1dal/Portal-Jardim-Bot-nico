(() => {
  const hero = document.querySelector('.hero-video-banner');
  if (!hero) return;
  const video = hero.querySelector('video');
  const network = hero.querySelector('.hero-light-network');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  function update() {
    hero.classList.toggle('is-paused', video.paused);
    if (network && typeof network.pauseAnimations === 'function') {
      if (video.paused) network.pauseAnimations(); else network.unpauseAnimations();
    }
  }
  async function play() {
    try { await video.play(); } catch { /* Keep the poster when autoplay is unavailable. */ }
    update();
  }
  video.muted = true;
  const slowMotion = () => { video.defaultPlaybackRate = 0.5; video.playbackRate = 0.5; };
  slowMotion();
  video.addEventListener('loadedmetadata', slowMotion);
  video.addEventListener('play', update);
  video.addEventListener('pause', update);
  video.addEventListener('error', () => { video.pause(); hero.classList.add('is-paused'); });
  motion.addEventListener('change', () => { if (motion.matches) video.pause(); else play(); });
  if (motion.matches) { video.autoplay = false; video.pause(); update(); }
  else play();
})();
