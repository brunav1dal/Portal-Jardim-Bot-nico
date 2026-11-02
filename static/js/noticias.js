/* Objetivo: Carrega as notícias, controla o carrossel e abre matérias próprias em uma janela de leitura. */
(() => {
  // Isola variáveis deste módulo e procura os elementos necessários nesta página.
  const carousel = document.querySelector('[data-news-carousel]');
  if (!carousel) return;
  const track = carousel.querySelector('.news-track');
  const viewport = carousel.querySelector('.news-viewport');
  const controls = carousel.querySelector('.news-controls');
  const nextButton = carousel.querySelector('[data-news-next]');
  const previousButton = carousel.querySelector('[data-news-prev]');
  const count = carousel.querySelector('.news-count');
  const credit = carousel.querySelector('.news-credit');
  const status = carousel.querySelector('.news-sr-status');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let slides = [], articleStarts = [], index = 0, timer = null, paused = motion.matches, reading = false, swiped = false;
  // Interrompe o temporizador de avanço automático do carrossel.
  function stop() { clearTimeout(timer); timer = null; }
  // Agenda o próximo avanço respeitando foco, visibilidade, leitura e redução de movimento.
  function schedule() {
    stop();
    const keyboardFocus = viewport.contains(document.activeElement) && document.activeElement.matches(':focus-visible');
    if (slides.length > 1 && !paused && !reading && !document.hidden && !keyboardFocus) {
      timer = setTimeout(() => go(index + 1), 5000);
    }
  }
  // Seleciona um slide, atualiza a posição e sincroniza contador e informações de acessibilidade.
  function go(next, manual = false) {
    index = (next + slides.length) % slides.length;
    track.style.transform = `translateX(-${index * 100}%)`;
    Array.from(track.children).forEach((slide, i) => {
      slide.inert = i !== index;
      slide.setAttribute('aria-hidden', String(i !== index));
    });
    const current = slides[index];
    count.textContent = `Notícia ${current.articleNumber} de ${articleStarts.length} · Foto ${current.photo + 1} de ${current.article.images.length}`;
    credit.textContent = current.article.type === 'external' ? `Fonte e fotos: ${current.article.source}` : 'Notícia do projeto';
    if (manual) status.textContent = `${current.article.title}. ${count.textContent}.`;
    schedule();
  }
  // Confere protocolo e, quando exigido, origem antes de usar links e imagens recebidos.
  function safeUrl(value, base, sameOrigin = false) {
    const url = new URL(value, base);
    if (url.protocol !== 'https:' && url.origin !== window.location.origin) throw new Error('Unsupported news URL');
    if (sameOrigin && url.origin !== window.location.origin) throw new Error('News asset must be local');
    return url.href;
  }
  // Abre o texto e as fotos da notícia própria em um diálogo e pausa o carrossel.
  function ownStory(article) {
    reading = true;
    stop();
    const dialog = document.createElement('dialog');
    dialog.className = 'news-dialog';
    const close = document.createElement('button');
    close.type = 'button'; close.textContent = '×'; close.setAttribute('aria-label', 'Fechar notícia');
    // Responde ao clique deste controle e sincroniza sua ação com a interface.
    close.addEventListener('click', () => dialog.close());
    const title = document.createElement('h3'); title.textContent = article.title; title.id = 'ownNewsTitle';
    dialog.setAttribute('aria-labelledby', title.id);
    dialog.append(close, title);
    const gallery = document.createElement('div'); gallery.className = 'news-dialog-gallery';
    article.images.forEach(photo => {
      const image = document.createElement('img');
      image.src = safeUrl(photo.src, new URL(carousel.dataset.newsSource, window.location.href), true);
      image.alt = photo.alt || article.title; image.loading = 'lazy';
      gallery.append(image);
    });
    const paragraphs = Array.isArray(article.body) ? article.body : [article.body || article.summary];
    paragraphs.forEach(text => { const p = document.createElement('p'); p.textContent = text; dialog.append(p); });
    dialog.append(gallery);
    // Limpa o estado temporário ao encerrar o diálogo.
    dialog.addEventListener('close', () => { dialog.remove(); reading = false; schedule(); });
    document.body.append(dialog); dialog.showModal();
  }
  // Carrega o feed e monta os slides; mantém o conteúdo inicial se a requisição falhar.
  async function init() {
    try {
      const dataUrl = new URL(carousel.dataset.newsSource, window.location.href);
      const response = await fetch(dataUrl, { cache: 'no-store' });
      if (!response.ok) throw new Error('News unavailable');
      const articles = await response.json();
      const fragment = document.createDocumentFragment();
      articles.forEach(article => {
        if (!article.title || !Array.isArray(article.images) || !article.images.length) return;
        articleStarts.push(slides.length);
        const articleNumber = articleStarts.length;
        article.images.forEach((photo, photoIndex) => {
          const slide = document.createElement(article.type === 'external' ? 'a' : 'button');
          slide.className = 'news-slide';
          if (article.type === 'external') {
            slide.href = safeUrl(article.url, dataUrl); slide.target = '_blank'; slide.rel = 'noopener noreferrer';
          } else {
            slide.type = 'button'; slide.setAttribute('aria-haspopup', 'dialog');
            // Responde ao clique deste controle e sincroniza sua ação com a interface.
            slide.addEventListener('click', () => ownStory(article));
          }
          const image = document.createElement('img');
          image.className = 'news-photo'; image.src = safeUrl(photo.src, dataUrl, true);
          image.alt = photo.alt || article.title; image.width = 1600; image.height = 900;
          image.loading = slides.length === 0 ? 'eager' : 'lazy'; image.decoding = 'async';
          const caption = document.createElement('span'); caption.className = 'news-caption';
          const source = document.createElement('span'); source.className = 'news-source';
          source.textContent = article.type === 'external' ? `Na imprensa · ${article.source}` : 'Notícia do projeto';
          const title = document.createElement('h4'); title.textContent = article.title;
          const summary = document.createElement('p'); summary.textContent = article.summary || '';
          const read = document.createElement('span'); read.className = 'news-read';
          read.textContent = article.type === 'external' ? 'Ler matéria completa ↗' : 'Ler notícia →';
          const tags = document.createElement('span'); tags.className = 'news-tags';
          tags.textContent = (article.tags || []).map(tag => `#${tag}`).join(' ');
          caption.append(source, title, summary, read, tags); slide.append(image, caption); fragment.append(slide);
          slides.push({ article, photo: photoIndex, articleNumber });
        });
      });
      if (!slides.length) return;
      track.replaceChildren(fragment);
      controls.hidden = false;
      nextButton.disabled = articleStarts.length < 2;
      previousButton.disabled = articleStarts.length < 2;
      go(0);
    } catch {
      // Mantém a matéria inicial legível e com link caso o feed não possa ser carregado.
      controls.hidden = true;
    }
  }
  // Navega entre matérias usando o primeiro slide de cada publicação.
  function changeArticle(direction) {
    if (articleStarts.length < 2) return;
    const currentArticle = slides[index].articleNumber - 1;
    const target = (currentArticle + direction + articleStarts.length) % articleStarts.length;
    go(articleStarts[target], true);
  }
  // Responde ao clique deste controle e sincroniza sua ação com a interface.
  nextButton.addEventListener('click', () => changeArticle(1));
  // Responde ao clique deste controle e sincroniza sua ação com a interface.
  previousButton.addEventListener('click', () => changeArticle(-1));
  // Ajusta o avanço automático quando o visitante navega pelos controles.
  carousel.addEventListener('focusin', event => { if (viewport.contains(event.target) && event.target.matches(':focus-visible')) stop(); else schedule(); });
  // Reavalia o avanço depois que o foco deixa o conteúdo.
  carousel.addEventListener('focusout', () => setTimeout(schedule, 0));
  // Permite controlar a interface pelo teclado.
  carousel.addEventListener('keydown', event => {
    if (!slides.length || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault(); go(index + (event.key === 'ArrowRight' ? 1 : -1), true);
  });
  // Suspende ou retoma o avanço conforme a visibilidade da página.
  document.addEventListener('visibilitychange', schedule);
  // Sincroniza a interface após a mudança de seleção ou de preferência.
  motion.addEventListener('change', () => { paused = motion.matches; schedule(); });
  let startX = null;
  // Registra o início do gesto de toque para navegar no carrossel.
  viewport.addEventListener('pointerdown', event => { if (event.pointerType === 'touch') startX = event.clientX; });
  // Calcula o deslocamento do toque e decide se deve trocar o slide.
  viewport.addEventListener('pointerup', event => {
    if (startX === null || !slides.length) return;
    const delta = event.clientX - startX; startX = null;
    if (Math.abs(delta) > 45) { swiped = true; go(index + (delta < 0 ? 1 : -1), true); setTimeout(() => { swiped = false; }, 350); }
  });
  // Responde ao clique deste controle e sincroniza sua ação com a interface.
  viewport.addEventListener('click', event => { if (swiped) { event.preventDefault(); event.stopPropagation(); swiped = false; } }, true);
  // Descarta o gesto de toque cancelado.
  viewport.addEventListener('pointercancel', () => { startX = null; });
  init();
})();
