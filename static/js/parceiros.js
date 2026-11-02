/* Objetivo: virar os cards de parceiros por clique, toque ou teclado e sincronizar a leitura acessível das faces. */
(() => {
  const cards = document.querySelectorAll('[data-partner-card]');

  // Cada face expõe somente seu conteúdo ativo; o rótulo do botão informa a próxima ação.
  function setFlipped(card, flipped) {
    card.classList.toggle('is-flipped', flipped);
    card.setAttribute('aria-expanded', String(flipped));
    card.querySelector('.partner-front').setAttribute('aria-hidden', String(flipped));
    card.querySelector('.partner-back').setAttribute('aria-hidden', String(!flipped));
    // O nome permanece nos dados do botão mesmo com a frente exibindo somente o logo.
    const name = card.dataset.partnerName;
    card.setAttribute('aria-label', flipped ? `Voltar à apresentação de ${name}` : `Conhecer a contribuição de ${name}`);
    // Associa a contribuição visível ao botão para que leitores de tela anunciem também o conteúdo do verso.
    if (flipped && card.querySelector('.partner-contribution')) {
      card.setAttribute('aria-describedby', card.getAttribute('aria-controls'));
    } else {
      card.removeAttribute('aria-describedby');
    }
  }

  cards.forEach(card => {
    // O botão nativo também transforma Enter e Espaço em clique, sem tratamento duplicado.
    card.addEventListener('click', () => setFlipped(card, card.getAttribute('aria-expanded') !== 'true'));
    // Escape permite voltar à frente sem retirar o foco do parceiro selecionado.
    card.addEventListener('keydown', event => {
      if (event.key === 'Escape') setFlipped(card, false);
    });
  });
})();
