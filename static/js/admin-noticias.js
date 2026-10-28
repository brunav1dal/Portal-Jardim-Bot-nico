(() => {
  const form = document.getElementById('adminNewsForm');
  if (!form) return;
  const title = document.getElementById('newsTitle');
  const summary = document.getElementById('newsSummary');
  const photos = document.getElementById('newsPhotos');
  const cover = document.getElementById('newsPreviewImage');
  const thumbnails = document.getElementById('newsPhotoPreviews');
  const status = document.getElementById('adminNewsStatus');
  const type = document.getElementById('newsType');
  const link = document.getElementById('newsExternalUrl');
  const importButton = document.getElementById('newsImportButton');
  const importToken = document.getElementById('newsImportToken');
  const body = document.getElementById('newsBody');
  const publishButton = form.querySelector('[type="submit"]');
  let urls = [], imported = null, importing = false;
  const external = () => type.value === 'external';
  const importedCover = () => external() && imported && imported.url === link.value.trim() && imported.images.length > 0;
  function message(text, error = false) { status.textContent = text; status.dataset.error = String(error); }
  function updateText() {
    document.getElementById('newsPreviewTitle').textContent = title.value.trim() || 'O título da sua notícia aparece aqui';
    document.getElementById('newsPreviewSummary').textContent = summary.value.trim() || 'Escolha as fotos e escreva o resumo para visualizar a capa.';
    document.getElementById('newsPreviewSource').textContent = external() ? `Na imprensa · ${imported ? imported.source : 'Site externo'}` : 'Notícia do projeto';
    document.getElementById('newsPreviewRead').textContent = external() ? 'Ler matéria completa ↗' : 'Ler notícia →';
    document.getElementById('newsPreviewHelp').textContent = external() ? 'Ao clicar, o visitante abre a matéria completa no site de origem.' : 'O visitante verá o texto completo e as fotos ao abrir a notícia.';
  }
  function updatePhotos() {
    urls.forEach(url => URL.revokeObjectURL(url)); urls = [];
    thumbnails.replaceChildren(); cover.hidden = true; cover.removeAttribute('src');
    const files = Array.from(photos.files).slice(0, 5);
    files.forEach((file, i) => {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return;
      const url = URL.createObjectURL(file); urls.push(url);
      if (!i) { cover.src = url; cover.hidden = false; }
      const image = document.createElement('img'); image.src = url; image.alt = `Foto ${i + 1}${i === 0 ? ' (capa)' : ''}`; thumbnails.append(image);
    });
    if (!files.length && importedCover()) { cover.src = imported.images[0].src; cover.hidden = false; }
    photos.required = !importedCover();
    document.getElementById('newsPhotosLabel').textContent = importedCover() ? 'Trocar foto de capa (opcional)' : 'Fotos';
  }
  function updateType() {
    const isExternal = external();
    form.querySelectorAll('[data-news-kind]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.newsKind === type.value)));
    document.getElementById('newsExternalFields').hidden = !isExternal;
    document.getElementById('newsBodyFields').hidden = isExternal;
    link.disabled = !isExternal; link.required = isExternal;
    body.disabled = isExternal; body.required = !isExternal;
    updateText(); updatePhotos();
  }
  async function importLink() {
    if (form.dataset.staticDemo || !external() || importing || !link.value || !link.checkValidity()) return;
    importing = true; importButton.disabled = true; publishButton.disabled = true;
    const requestedUrl = link.value.trim();
    message('Buscando título e imagem da matéria…');
    try {
      const payload = new FormData(); payload.set('url', requestedUrl); payload.set('csrf_token', form.elements.csrf_token.value);
      const response = await fetch(importButton.dataset.importUrl, { method: 'POST', body: payload, headers: { Accept: 'application/json' } });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || 'Não foi possível importar. Preencha os campos manualmente.');
      if (requestedUrl !== link.value.trim() || !external()) return;
      imported = data.preview; link.value = imported.url; importToken.value = imported.token;
      title.value = imported.title; summary.value = imported.summary; photos.value = '';
      updateText(); updatePhotos();
      message(data.warning || 'Título, resumo e capa importados. Revise a prévia e clique em Publicar notícia.');
    } catch (error) { message(error.message || 'Não foi possível importar. Preencha os campos manualmente.', true); }
    finally { importing = false; importButton.disabled = false; publishButton.disabled = false; }
  }
  title.addEventListener('input', updateText); summary.addEventListener('input', updateText);
  photos.addEventListener('change', updatePhotos); type.addEventListener('change', updateType);
  form.querySelectorAll('[data-news-kind]').forEach(button => button.addEventListener('click', () => {
    type.value = button.dataset.newsKind;
    updateType();
  }));
  importButton.addEventListener('click', importLink);
  link.addEventListener('input', () => { imported = null; importToken.value = ''; updateText(); updatePhotos(); });
  link.addEventListener('paste', () => setTimeout(importLink, 0));
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (form.dataset.staticDemo || importing) return;
    const files = Array.from(photos.files);
    if ((!files.length && !importedCover()) || files.length > 5) { message('Selecione de uma a cinco fotos ou importe a capa pelo link.', true); return; }
    if (files.reduce((sum, file) => sum + file.size, 0) > 4.8 * 1024 * 1024) { message('Reduza o tamanho das fotos: o envio completo deve ter até 5 MB.', true); return; }
    publishButton.disabled = true; message('Publicando notícia…');
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || 'Não foi possível publicar. Tente novamente.');
      const item = document.createElement('li');
      const name = document.createElement('strong'); name.textContent = data.article.title;
      const detail = document.createElement('span'); detail.textContent = `${data.article.images.length} foto(s) · `;
      const site = document.createElement('a'); site.href = '/#noticias'; site.target = '_blank'; site.rel = 'noopener noreferrer'; site.textContent = 'Ver no site ↗';
      detail.append(site); item.append(name, detail); document.getElementById('adminNewsList').prepend(item);
      document.getElementById('adminNewsEmpty').hidden = true;
      imported = null; form.reset(); updateType();
      message('Notícia publicada! Ela já aparece no carrossel de Notícias.');
    } catch (error) { message(error.message || 'Não foi possível publicar.', true); }
    finally { publishButton.disabled = false; }
  });
  updateType();
  if (new URLSearchParams(window.location.search).get('aba') === 'noticias') showTab('noticias');
})();
