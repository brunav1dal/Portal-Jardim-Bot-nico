(() => {
  const dialog = document.getElementById('historyImageDialog');
  if (!dialog) return;
  const image = dialog.querySelector('img');
  const caption = dialog.querySelector('[data-image-caption]');
  document.querySelectorAll('.coin-preview').forEach(button => {
    button.addEventListener('click', () => {
      const thumbnail = button.querySelector('img');
      image.src = thumbnail.currentSrc || thumbnail.src;
      image.alt = thumbnail.alt;
      caption.textContent = thumbnail.alt;
      dialog.showModal();
    });
  });
  dialog.querySelector('[data-close-image]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
})();
