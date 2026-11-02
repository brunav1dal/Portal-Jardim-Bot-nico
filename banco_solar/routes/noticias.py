"""Objetivo: Gerencia notícias e fotos via HTTP, com permissões, CSRF e respostas para o editor."""
# Dependências usadas por este módulo.
from datetime import datetime, timezone
from pathlib import Path
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from urllib.parse import urlsplit

from flask import abort, flash, jsonify, redirect, request, send_from_directory, session, url_for
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from banco_solar.services.importacao_noticias import ImportErrorMessage, import_article, public_url


from banco_solar.services.imagens import prepare_photo
from banco_solar.config import ROOT_DIR
from banco_solar.repositories import noticias as noticias_repository


def init_news(app):
    """Registra o contexto, as rotas e o tratamento de uploads do módulo de notícias."""
    app.config.setdefault('NEWS_STORAGE_DIR', os.environ.get('NEWS_STORAGE_DIR', str(ROOT_DIR / 'runtime' / 'noticias')))

    def storage():
        """Retorna o diretório persistente configurado para banco e fotos das notícias."""
        return Path(app.config['NEWS_STORAGE_DIR'])

    def published():
        """Consulta as publicações cadastradas, ordenadas das mais recentes para as antigas."""
        return noticias_repository.listar(storage())

    def csrf_token():
        """Gera e reutiliza o token de proteção dos formulários na sessão atual."""
        if 'news_csrf' not in session:
            session['news_csrf'] = secrets.token_urlsafe(32)
        return session['news_csrf']

    @app.context_processor
    def news_context():
        """Disponibiliza publicações e token ao template administrativo, respeitando a exportação."""
        if request.endpoint != 'admin_dashboard' or session.get('user_tipo') != 'admin':
            return {}
        exporting = app.config.get('NEWS_STATIC_EXPORT', False)
        return {'noticias_publicadas': [] if exporting else published(),
                'news_csrf': '' if exporting else csrf_token(), 'news_static_export': exporting}

    @app.get('/api/noticias')
    def api_noticias():
        """Combina as notícias cadastradas com o arquivo inicial e responde JSON sem cache."""
        with (Path(app.static_folder) / 'noticias.json').open(encoding='utf-8') as source:
            seed = json.load(source)
        for article in seed:
            for photo in article.get('images', []):
                photo['src'] = url_for('static', filename=photo['src'])
        response = jsonify(published() + seed)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/noticias/fotos/<filename>')
    def noticia_foto(filename):
        """Entrega somente fotos com identificador hexadecimal e extensão JPEG esperados."""
        if len(filename) != 36 or not filename.endswith('.jpg'):
            abort(404)
        try:
            int(filename[:-4], 16)
        except ValueError:
            abort(404)
        response = send_from_directory(storage() / 'fotos', filename, mimetype='image/jpeg', max_age=31536000)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    def failure(message, status=400):
        """Converte falhas em JSON ou mensagem com redirecionamento, conforme o pedido do navegador."""
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(success=False, error=message), status
        flash(message, 'error')
        return redirect(url_for('admin_dashboard', aba='noticias') + '#tab-noticias')

    @app.post('/admin/noticias/importar')
    def importar_noticia():
        """Prepara um rascunho de matéria externa sem publicá-lo no portal."""
        # Confere o perfil administrativo antes de permitir a operação.
        if 'user_id' not in session or session.get('user_tipo') != 'admin':
            return failure('Entre com um perfil de administrador para importar notícias.', 403)
        # Valida o token da sessão para recusar envios de formulários externos ou expirados.
        token = request.form.get('csrf_token', '')
        if not token or not hmac.compare_digest(token, session.get('news_csrf', '')):
            return failure('Sua sessão expirou. Recarregue o painel.', 403)
        try:
            metadata = import_article(request.form.get('url', '').strip())
        except ImportErrorMessage as error:
            return failure(str(error))
        image_name = ''
        images = []
        # Reprocessa a capa importada e a salva como rascunho, ainda sem publicação.
        if metadata['image_bytes']:
            try:
                data = prepare_photo(metadata['image_bytes'])
                folder = storage() / 'fotos'
                folder.mkdir(parents=True, exist_ok=True)
                image_name = uuid.uuid4().hex + '.jpg'
                (folder / image_name).write_bytes(data)
                images.append({'src': url_for('noticia_foto', filename=image_name), 'alt': metadata['title']})
            except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                metadata['warning'] = 'Título e resumo importados. Envie uma foto: a imagem do site não pôde ser usada.'
                image_name = ''
        # Associa o rascunho ao link e a um token para validar seu uso na publicação.
        draft = {'token': secrets.token_urlsafe(24), 'url': metadata['url'], 'source': metadata['source'], 'image_name': image_name}
        session['news_external_draft'] = draft
        response = jsonify(success=True, preview={'token': draft['token'], 'url': draft['url'],
                           'title': metadata['title'], 'summary': metadata['summary'],
                           'source': metadata['source'], 'images': images}, warning=metadata['warning'])
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/admin/noticias/<article_id>')
    def consultar_noticia(article_id):
        """Retorna uma publicação para preencher o formulário de edição administrativa."""
        # Confere o perfil administrativo antes de permitir a operação.
        if 'user_id' not in session or session.get('user_tipo') != 'admin':
            return failure('Entre com um perfil de administrador para gerenciar notícias.', 403)
        article = next((item for item in published() if item['id'] == article_id), None)
        if not article:
            return failure('Esta notícia não foi encontrada.', 404)
        response = jsonify(success=True, article=article)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/admin/noticias/<article_id>/excluir')
    def excluir_noticia(article_id):
        """Exclui a publicação e remove fotos que nenhuma outra notícia utiliza."""
        # Confere o perfil administrativo antes de permitir a operação.
        if 'user_id' not in session or session.get('user_tipo') != 'admin':
            return failure('Entre com um perfil de administrador para gerenciar notícias.', 403)
        # Valida o token da sessão para recusar envios de formulários externos ou expirados.
        token = request.form.get('csrf_token', '')
        if not token or not hmac.compare_digest(token, session.get('news_csrf', '')):
            return failure('Sua sessão expirou. Recarregue o painel.', 403)
        article = next((item for item in published() if item['id'] == article_id), None)
        if not article:
            return failure('Esta notícia não foi encontrada.', 404)
        try:
            deleted = noticias_repository.excluir(storage(), article_id)
        except sqlite3.Error:
            return failure('Não foi possível excluir a notícia. Tente novamente.', 500)
        if not deleted:
            return failure('Esta notícia não foi encontrada.', 404)
        # Identifica fotos compartilhadas antes de limpar arquivos da notícia excluída.
        retained = {image['src'] for item in published() for image in item.get('images', [])}
        folder = (storage() / 'fotos').resolve()
        for image in article.get('images', []):
            if image['src'] in retained:
                continue
            name = image['src'].rsplit('/', 1)[-1]
            if len(name) != 36 or not name.endswith('.jpg'):
                continue
            try:
                int(name[:-4], 16)
                path = (folder / name).resolve()
                if path.parent == folder:
                    path.unlink(missing_ok=True)
            except (ValueError, OSError):
                app.logger.warning('Unable to clean up a deleted news image')
        return jsonify(success=True)

    @app.post('/admin/noticias')
    @app.post('/admin/noticias/<article_id>/editar')
    def publicar_noticia(article_id=None):
        """Valida o formulário e as imagens e grava uma publicação nova ou editada."""
        # Confere o perfil administrativo antes de permitir a operação.
        if 'user_id' not in session or session.get('user_tipo') != 'admin':
            return failure('Entre novamente com um perfil de administrador para publicar notícias.', 403)
        # Valida o token da sessão para recusar envios de formulários externos ou expirados.
        token = request.form.get('csrf_token', '')
        if not token or not hmac.compare_digest(token, session.get('news_csrf', '')):
            return failure('Sua sessão do formulário expirou. Recarregue o painel e tente novamente.', 403)
        existing = next((item for item in published() if item['id'] == article_id), None) if article_id else None
        if article_id and not existing:
            return failure('Esta notícia não foi encontrada.', 404)
        # Normaliza os campos e valida os limites de texto e o tipo da notícia.
        title = request.form.get('titulo', '').strip()
        kind = request.form.get('tipo', 'internal')
        if kind not in {'internal', 'external'}:
            return failure('Escolha notícia própria ou notícia de site externo.')
        summary = request.form.get('resumo', '').strip()
        body = request.form.get('texto', '').strip()
        photos = [photo for photo in request.files.getlist('fotos') if photo.filename]
        if not title or len(title) > 160 or (kind == 'internal' and not body) or len(body) > 12000 or len(summary) > 280:
            return failure('Informe título e texto. Limites: título 160, resumo 280 e texto 12.000 caracteres.')
        imported_cover = ''
        article_url = ''
        source = 'Projeto Orquídea Solar'
        # Para matérias externas, preserva o link e vincula somente a capa do rascunho correspondente.
        if kind == 'external':
            try:
                article_url = public_url(request.form.get('link_externo', '').strip())
            except ImportErrorMessage as error:
                return failure(str(error))
            source = urlsplit(article_url).hostname
            if existing and existing.get('url') == article_url:
                source = existing.get('source') or source
            draft = session.get('news_external_draft', {})
            if draft.get('url') == article_url and hmac.compare_digest(draft.get('token', ''), request.form.get('import_token', '')):
                source = draft.get('source') or source
                name = draft.get('image_name', '')
                if name and (storage() / 'fotos' / name).is_file():
                    imported_cover = name
        # Mantém as fotos atuais na edição e exige uma capa válida para publicações novas.
        existing_images = existing.get('images', []) if existing else []
        if len(photos) > 5 or (not photos and not imported_cover and not existing_images):
            return failure('Selecione de uma a cinco fotos JPG, PNG ou WebP.')
        # Valida todas as imagens antes de salvar; a conversão remove metadados e conteúdo externo.
        # Valida todas as fotos antes de iniciar a gravação dos arquivos da publicação.
        processed = []
        try:
            for photo in photos:
                processed.append(prepare_photo(photo.read()))
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            return failure('Uma das fotos não é uma imagem válida. Envie fotos JPG, PNG ou WebP.')

        folder = storage() / 'fotos'
        paths = []
        # Monta o registro persistido, preservando a data de criação nas edições.
        article = {'id': article_id or uuid.uuid4().hex, 'type': kind, 'title': title,
                   'summary': summary or ' '.join(body.split())[:180],
                   'body': [paragraph.strip() for paragraph in body.split('\n\n') if paragraph.strip()] if kind == 'internal' else [],
                   'source': source, 'tags': existing.get('tags', []) if existing else [], 'images': [],
                   'created_at': existing['created_at'] if existing else datetime.now(timezone.utc).isoformat()}
        if existing:
            article['updated_at'] = datetime.now(timezone.utc).isoformat()
        # Para matérias externas, preserva o link e vincula somente a capa do rascunho correspondente.
        if kind == 'external':
            article['url'] = article_url
            if not photos and imported_cover:
                article['images'].append({'src': url_for('noticia_foto', filename=imported_cover), 'alt': title})
        if not photos and not article['images']:
            article['images'] = [{**image, 'alt': title} for image in existing_images]
        try:
            # Grava as fotos processadas e depois salva a publicação em transação SQLite.
            folder.mkdir(parents=True, exist_ok=True)
            for data in processed:
                name = uuid.uuid4().hex + '.jpg'
                path = folder / name
                path.write_bytes(data)
                paths.append(path)
                article['images'].append({'src': url_for('noticia_foto', filename=name), 'alt': title})
            noticias_repository.salvar(storage(), article, atualizar=existing is not None)
        # Remove arquivos recém-criados caso a publicação não possa ser persistida.
        except (OSError, sqlite3.Error, LookupError) as error:
            for path in paths:
                path.unlink(missing_ok=True)
            app.logger.exception('Unable to save news')
            if isinstance(error, LookupError):
                return failure('Esta notícia não foi encontrada.', 404)
            return failure('Não foi possível salvar a notícia. Tente novamente.', 500)
        # Para matérias externas, preserva o link e vincula somente a capa do rascunho correspondente.
        if kind == 'external':
            session.pop('news_external_draft', None)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(success=True, article=article), 200 if existing else 201
        flash('Notícia publicada! Ela já está disponível na seção Notícias.', 'success')
        return redirect(url_for('admin_dashboard', aba='noticias') + '#tab-noticias')

    @app.errorhandler(RequestEntityTooLarge)
    def upload_too_large(error):
        """Retorna uma mensagem adequada quando o envio ultrapassa o limite configurado."""
        if request.path.startswith('/admin/noticias'):
            return failure('As fotos e o texto devem somar no máximo 5 MB.', 413)
        return 'O arquivo enviado excede o limite de 5 MB.', 413
