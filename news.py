"""Administrator news publishing, independent from the energy spreadsheets."""
from datetime import datetime, timezone
from contextlib import closing
from io import BytesIO
from pathlib import Path
import hmac
import json
import os
import secrets
import sqlite3
import uuid
import warnings
from urllib.parse import urlsplit

from flask import abort, flash, jsonify, redirect, request, send_from_directory, session, url_for
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from news_import import ImportErrorMessage, import_article, public_url


def prepare_photo(data):
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(BytesIO(data)) as image:
            if image.format not in {'JPEG', 'PNG', 'WEBP'} or image.width * image.height > 24000000:
                raise ValueError('Imagem incompatível ou maior que 24 megapixels.')
            image.load()
            image = ImageOps.exif_transpose(image).convert('RGBA')
            image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            background = Image.new('RGB', image.size, 'white')
            background.paste(image, mask=image.getchannel('A'))
            output = BytesIO()
            background.save(output, 'JPEG', quality=90, optimize=True)
            return output.getvalue()


def init_news(app):
    app.config.setdefault('NEWS_STORAGE_DIR', os.environ.get('NEWS_STORAGE_DIR', str(Path(app.root_path) / 'runtime' / 'noticias')))

    def storage():
        return Path(app.config['NEWS_STORAGE_DIR'])

    def published():
        db = storage() / 'noticias.sqlite3'
        if not db.exists():
            return []
        with closing(sqlite3.connect(db)) as connection:
            rows = connection.execute('SELECT payload FROM news ORDER BY created_at DESC, id DESC').fetchall()
        return [json.loads(row[0]) for row in rows]

    def csrf_token():
        if 'news_csrf' not in session:
            session['news_csrf'] = secrets.token_urlsafe(32)
        return session['news_csrf']

    @app.context_processor
    def news_context():
        if request.endpoint != 'admin_dashboard' or session.get('user_tipo') != 'admin':
            return {}
        exporting = app.config.get('NEWS_STATIC_EXPORT', False)
        return {'noticias_publicadas': [] if exporting else published(),
                'news_csrf': '' if exporting else csrf_token(), 'news_static_export': exporting}

    @app.get('/api/noticias')
    def api_noticias():
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
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(success=False, error=message), status
        flash(message, 'error')
        return redirect(url_for('admin_dashboard', aba='noticias') + '#tab-noticias')

    @app.post('/admin/noticias/importar')
    def importar_noticia():
        if 'user_id' not in session or session.get('user_tipo') != 'admin':
            return failure('Entre com um perfil de administrador para importar notícias.', 403)
        token = request.form.get('csrf_token', '')
        if not token or not hmac.compare_digest(token, session.get('news_csrf', '')):
            return failure('Sua sessão expirou. Recarregue o painel.', 403)
        try:
            metadata = import_article(request.form.get('url', '').strip())
        except ImportErrorMessage as error:
            return failure(str(error))
        image_name = ''
        images = []
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
        draft = {'token': secrets.token_urlsafe(24), 'url': metadata['url'], 'source': metadata['source'], 'image_name': image_name}
        session['news_external_draft'] = draft
        response = jsonify(success=True, preview={'token': draft['token'], 'url': draft['url'],
                           'title': metadata['title'], 'summary': metadata['summary'],
                           'source': metadata['source'], 'images': images}, warning=metadata['warning'])
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/admin/noticias')
    def publicar_noticia():
        if 'user_id' not in session or session.get('user_tipo') != 'admin':
            return failure('Entre novamente com um perfil de administrador para publicar notícias.', 403)
        token = request.form.get('csrf_token', '')
        if not token or not hmac.compare_digest(token, session.get('news_csrf', '')):
            return failure('Sua sessão do formulário expirou. Recarregue o painel e tente novamente.', 403)
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
        if kind == 'external':
            try:
                article_url = public_url(request.form.get('link_externo', '').strip())
            except ImportErrorMessage as error:
                return failure(str(error))
            source = urlsplit(article_url).hostname
            draft = session.get('news_external_draft', {})
            if draft.get('url') == article_url and hmac.compare_digest(draft.get('token', ''), request.form.get('import_token', '')):
                source = draft.get('source') or source
                name = draft.get('image_name', '')
                if name and (storage() / 'fotos' / name).is_file():
                    imported_cover = name
        if len(photos) > 5 or (not photos and not imported_cover):
            return failure('Selecione de uma a cinco fotos JPG, PNG ou WebP.')
        # Validate every image before saving anything; re-encode to remove metadata and foreign content.
        processed = []
        try:
            for photo in photos:
                processed.append(prepare_photo(photo.read()))
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            return failure('Uma das fotos não é uma imagem válida. Envie fotos JPG, PNG ou WebP.')

        folder = storage() / 'fotos'
        paths = []
        article = {'id': uuid.uuid4().hex, 'type': kind, 'title': title,
                   'summary': summary or ' '.join(body.split())[:180],
                   'body': [paragraph.strip() for paragraph in body.split('\n\n') if paragraph.strip()] if kind == 'internal' else [],
                   'source': source, 'tags': [], 'images': [],
                   'created_at': datetime.now(timezone.utc).isoformat()}
        if kind == 'external':
            article['url'] = article_url
            if not photos and imported_cover:
                article['images'].append({'src': url_for('noticia_foto', filename=imported_cover), 'alt': title})
        try:
            folder.mkdir(parents=True, exist_ok=True)
            for data in processed:
                name = uuid.uuid4().hex + '.jpg'
                path = folder / name
                path.write_bytes(data)
                paths.append(path)
                article['images'].append({'src': url_for('noticia_foto', filename=name), 'alt': title})
            with closing(sqlite3.connect(storage() / 'noticias.sqlite3')) as connection:
                with connection:
                    connection.execute('CREATE TABLE IF NOT EXISTS news (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)')
                    connection.execute('INSERT INTO news VALUES (?, ?, ?)',
                                       (article['id'], article['created_at'], json.dumps(article, ensure_ascii=False)))
        except (OSError, sqlite3.Error):
            for path in paths:
                path.unlink(missing_ok=True)
            app.logger.exception('Unable to save news')
            return failure('Não foi possível salvar a notícia. Tente novamente.', 500)
        if kind == 'external':
            session.pop('news_external_draft', None)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(success=True, article=article), 201
        flash('Notícia publicada! Ela já está disponível na seção Notícias.', 'success')
        return redirect(url_for('admin_dashboard', aba='noticias') + '#tab-noticias')

    @app.errorhandler(RequestEntityTooLarge)
    def upload_too_large(error):
        if request.path == '/admin/noticias':
            return failure('As fotos e o texto devem somar no máximo 5 MB.', 413)
        return 'O arquivo enviado excede o limite de 5 MB.', 413
