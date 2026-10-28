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
  const importActions = document.getElementById('newsImportActions');
  const importToken = document.getElementById('newsImportToken');
  const body = document.getElementById('newsBody');
  const editor = document.getElementById('adminNewsEditor');
  const publishButton = form.querySelector('[type="submit"]');
  let urls = [], imported = null, importing = false, importTimer = null, controller = null, version = 0, lastAttempt = '';
  const external = () => type.value === 'external';
  const importedCover = () => external() && imported && imported.url === link.value.trim() && imported.images.length > 0;
  function message(text, error = false) { status.textContent = text; status.dataset.error = String(error); }
  function cancelImport() {
    clearTimeout(importTimer); importTimer = null; version++;
    if (controller) controller.abort();
    controller = null; importing = false;
    importButton.disabled = Boolean(form.dataset.staticDemo);
    publishButton.disabled = Boolean(form.dataset.staticDemo);
  }
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
    cancelImport(); lastAttempt = ''; importActions.hidden = true; summary.required = false;
    const isExternal = external();
    form.querySelectorAll('[data-news-kind]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.newsKind === type.value)));
    document.getElementById('newsExternalFields').hidden = !isExternal;
    document.getElementById('newsBodyFields').hidden = isExternal;
    link.disabled = !isExternal; link.required = isExternal;
    body.disabled = isExternal; body.required = !isExternal;
    updateText(); updatePhotos();
  }
  async function importLink(force = false) {
    const requestedUrl = link.value.trim();
    if (form.dataset.staticDemo || !external() || !requestedUrl || !link.checkValidity() || (!force && requestedUrl === lastAttempt)) return;
    cancelImport();
    const requestVersion = version;
    controller = new AbortController();
    importing = true; importButton.disabled = true; publishButton.disabled = true; importActions.hidden = true;
    lastAttempt = requestedUrl;
    const previousTitle = title.value, previousSummary = summary.value;
    message('Buscando automaticamente o título, o resumo e a foto da matéria…');
    try {
      const payload = new FormData(); payload.set('url', requestedUrl); payload.set('csrf_token', form.elements.csrf_token.value);
      const response = await fetch(importButton.dataset.importUrl, { method: 'POST', body: payload, signal: controller.signal, headers: { Accept: 'application/json' } });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error('Import unavailable');
      if (requestVersion !== version || requestedUrl !== link.value.trim() || !external()) return;
      imported = data.preview; link.value = imported.url; lastAttempt = imported.url; importToken.value = imported.token;
      if (title.value === previousTitle) title.value = imported.title;
      if (summary.value === previousSummary) summary.value = imported.summary;
      summary.required = !summary.value.trim();
      updateText(); updatePhotos();
      importActions.hidden = !data.warning;
      message(data.warning ? `${data.warning} Tente novamente ou preencha o título, o resumo e envie uma foto.` : 'Dados importados. Confira a publicação e clique em Publicar notícia.');
    } catch {
      if (requestVersion !== version || requestedUrl !== link.value.trim() || !external()) return;
      summary.required = true; importActions.hidden = false;
      message('Não foi possível buscar os dados deste link. Tente novamente ou preencha o título e o resumo e adicione uma foto manualmente.', true);
    } finally {
      if (requestVersion === version) {
        importing = false; controller = null;
        importButton.disabled = false; publishButton.disabled = false;
      }
    }
  }
  function scheduleImport(delay = 850) {
    clearTimeout(importTimer);
    if (external() && link.value.trim() && link.checkValidity()) importTimer = setTimeout(() => importLink(), delay);
  }
  document.getElementById('openNewsEditor').addEventListener('click', () => {
    editor.showModal();
    form.querySelector('[data-news-kind]').focus();
    if (external()) scheduleImport(0);
  });
  document.getElementById('closeNewsEditor').addEventListener('click', () => editor.close());
  editor.addEventListener('close', cancelImport);
  title.addEventListener('input', updateText); summary.addEventListener('input', updateText);
  photos.addEventListener('change', updatePhotos); type.addEventListener('change', updateType);
  form.querySelectorAll('[data-news-kind]').forEach(button => button.addEventListener('click', () => {
    type.value = button.dataset.newsKind; updateType(); message('');
    if (external()) scheduleImport(0);
  }));
  importButton.addEventListener('click', () => importLink(true));
  document.getElementById('newsManualButton').addEventListener('click', () => {
    cancelImport(); lastAttempt = link.value.trim(); importActions.hidden = true; summary.required = true;
    message('Preencha o título e o resumo e envie a foto de capa. O link será usado para abrir a matéria original.');
    title.focus();
  });
  link.addEventListener('input', () => {
    if (imported) {
      if (title.value === imported.title) title.value = '';
      if (summary.value === imported.summary) summary.value = '';
    }
    cancelImport(); lastAttempt = ''; imported = null; importToken.value = ''; importActions.hidden = true;
    summary.required = false; updateText(); updatePhotos(); scheduleImport();
  });
  link.addEventListener('paste', () => { setTimeout(() => scheduleImport(0), 0); });
  link.addEventListener('change', () => scheduleImport(0));
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (form.dataset.staticDemo || importing) return;
    clearTimeout(importTimer);
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
      imported = null; form.reset(); updateType(); editor.close();
      document.getElementById('adminNewsNotice').textContent = 'Notícia publicada! Ela já aparece no portal público, na seção Notícias.';
      message('');
    } catch (error) { message(error.message || 'Não foi possível publicar. Tente novamente.', true); }
    finally { publishButton.disabled = false; }
  });
  updateType();
  if (new URLSearchParams(window.location.search).get('aba') === 'noticias') showTab('noticias');
})();
