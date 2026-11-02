/* Objetivo: Controla reprodução e aparência do vídeo de abertura respeitando a redução de movimento. */
(() => {
  // Isola variáveis deste módulo e procura os elementos necessários nesta página.
  const hero = document.querySelector('.hero-video-banner');
  if (!hero) return;
  const video = hero.querySelector('video');
  const network = hero.querySelector('.hero-light-network');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Atualiza o estado visual de pausa do vídeo.
  function update() {
    hero.classList.toggle('is-paused', video.paused);
    if (network && typeof network.pauseAnimations === 'function') {
      if (video.paused) network.pauseAnimations(); else network.unpauseAnimations();
    }
  }
  // Tenta reproduzir o vídeo sem deixar uma falha de autoplay interromper a página.
  async function play() {
    try { await video.play(); } catch { /* Keep the poster when autoplay is unavailable. */ }
    update();
  }
  video.muted = true;
  const slowMotion = () => { video.defaultPlaybackRate = 0.5; video.playbackRate = 0.5; };
  slowMotion();
  // Aplica a velocidade de reprodução após carregar os metadados do vídeo.
  video.addEventListener('loadedmetadata', slowMotion);
  // Sincroniza os efeitos visuais com o início da reprodução.
  video.addEventListener('play', update);
  // Sincroniza os efeitos visuais com a pausa da reprodução.
  video.addEventListener('pause', update);
  // Apresenta o estado alternativo quando o recurso não pode ser reproduzido.
  video.addEventListener('error', () => { video.pause(); hero.classList.add('is-paused'); });
  // Sincroniza a interface após a mudança de seleção ou de preferência.
  motion.addEventListener('change', () => { if (motion.matches) video.pause(); else play(); });
  if (motion.matches) { video.autoplay = false; video.pause(); update(); }
  else play();
})();
