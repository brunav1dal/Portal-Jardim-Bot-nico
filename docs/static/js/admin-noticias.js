(() => {
  const form = document.getElementById('adminNewsForm');
  if (!form) return;
  const title = document.getElementById('newsTitle');
  const summary = document.getElementById('newsSummary');
  const photos = document.getElementById('newsPhotos');
  const cover = document.getElementById('newsPreviewImage');
  const thumbnails = document.getElementById('newsPhotoPreviews');
  const status = document.getElementById('adminNewsStatus');
  let urls = [];
  const updateText = () => {
    document.getElementById('newsPreviewTitle').textContent = title.value.trim() || 'O título da sua notícia aparece aqui';
    document.getElementById('newsPreviewSummary').textContent = summary.value.trim() || 'Escolha as fotos e escreva o resumo para visualizar a capa.';
  };
  title.addEventListener('input', updateText); summary.addEventListener('input', updateText);
  function updatePhotos() {
    urls.forEach(url => URL.revokeObjectURL(url)); urls = [];
    thumbnails.replaceChildren(); cover.hidden = true; cover.removeAttribute('src');
    Array.from(photos.files).slice(0, 5).forEach((file, i) => {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return;
      const url = URL.createObjectURL(file); urls.push(url);
      if (!i) { cover.src = url; cover.hidden = false; }
      const image = document.createElement('img'); image.src = url; image.alt = `Foto ${i + 1}${i === 0 ? ' (capa)' : ''}`; thumbnails.append(image);
    });
  }
  photos.addEventListener('change', updatePhotos);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (form.dataset.staticDemo) return;
    const files = Array.from(photos.files);
    if (!files.length || files.length > 5) { status.textContent = 'Selecione de uma a cinco fotos.'; return; }
    if (files.reduce((sum, file) => sum + file.size, 0) > 4.8 * 1024 * 1024) { status.textContent = 'Reduza o tamanho das fotos: o envio completo deve ter até 5 MB.'; return; }
    const button = form.querySelector('[type="submit"]'); button.disabled = true;
    status.textContent = 'Publicando notícia…'; status.dataset.error = 'false';
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || 'Não foi possível publicar. Tente novamente.');
      const item = document.createElement('li');
      const name = document.createElement('strong'); name.textContent = data.article.title;
      const detail = document.createElement('span'); detail.textContent = `${data.article.images.length} foto(s) · `;
      const link = document.createElement('a'); link.href = '/#historia'; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Ver no site ↗';
      detail.append(link); item.append(name, detail); document.getElementById('adminNewsList').prepend(item);
      document.getElementById('adminNewsEmpty').hidden = true;
      form.reset(); updateText(); updatePhotos();
      status.textContent = 'Notícia publicada! Ela já aparece no carrossel de Nossa História.';
    } catch (error) { status.textContent = error.message || 'Não foi possível publicar.'; status.dataset.error = 'true'; }
    finally { button.disabled = false; }
  });
  if (new URLSearchParams(window.location.search).get('aba') === 'noticias') showTab('noticias');
})();
