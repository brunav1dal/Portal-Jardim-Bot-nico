/* Objetivo: Amplia as imagens da história em um diálogo com legenda e fechamento por clique. */
(() => {
  // Isola variáveis deste módulo e procura os elementos necessários nesta página.
  const dialog = document.getElementById('historyImageDialog');
  if (!dialog) return;
  const image = dialog.querySelector('img');
  const caption = dialog.querySelector('[data-image-caption]');
  document.querySelectorAll('.coin-preview').forEach(button => {
    // Responde ao clique deste controle e sincroniza sua ação com a interface.
    button.addEventListener('click', () => {
      const thumbnail = button.querySelector('img');
      image.src = thumbnail.currentSrc || thumbnail.src;
      image.alt = thumbnail.alt;
      caption.textContent = thumbnail.alt;
      dialog.showModal();
    });
  });
  // Responde ao clique deste controle e sincroniza sua ação com a interface.
  dialog.querySelector('[data-close-image]').addEventListener('click', () => dialog.close());
  // Responde ao clique deste controle e sincroniza sua ação com a interface.
  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
})();
