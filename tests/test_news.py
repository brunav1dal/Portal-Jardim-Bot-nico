"""Objetivo: Verifica publicação, edição, exclusão, imagens e controle de acesso às notícias."""
# Dependências usadas por este módulo.
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest

# Permite executar os testes a partir da raiz ou diretamente pelo arquivo.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app
from flask import Flask
from banco_solar.routes.noticias import init_news
from PIL import Image


def photo(fmt='PNG'):
    """Cria uma pequena imagem em memória para testar uploads sem arquivos externos."""
    data = BytesIO()
    Image.new('RGB', (80, 60), '#15803d').save(data, fmt)
    data.seek(0)
    return data


class NewsPublishingTests(unittest.TestCase):
    """Verifica publicação, edição, exclusão, imagens e controle de acesso às notícias."""
    def setUp(self):
        """Prepara dados e armazenamento isolados antes de cada teste."""
        self.folder = tempfile.TemporaryDirectory()
        self.previous = {key: app.config.get(key) for key in ['TESTING', 'NEWS_STORAGE_DIR', 'MAX_CONTENT_LENGTH']}
        app.config.update(TESTING=True, NEWS_STORAGE_DIR=self.folder.name)
        self.client = app.test_client()

    def tearDown(self):
        """Restaura as configurações e remove o armazenamento temporário após cada teste."""
        app.config.update(self.previous)
        self.folder.cleanup()

    def login(self, role='admin'):
        """Prepara uma sessão autenticada para o perfil necessário ao teste."""
        with self.client.session_transaction() as session:
            session.update(user_id='1', user_tipo=role, user_nome='Teste', news_csrf='test-csrf')

    def post(self, **overrides):
        """Envia um formulário válido de notícia, permitindo substituir campos no cenário testado."""
        data = {'csrf_token': 'test-csrf', 'titulo': 'Notícia da comunidade',
                'resumo': 'Resumo da atividade.', 'texto': 'Primeiro parágrafo.\n\nSegundo parágrafo.',
                'fotos': [(photo(), 'capa.png'), (photo('JPEG'), 'turma.jpg')]}
        data.update(overrides)
        return self.client.post('/admin/noticias', data=data, headers={'Accept': 'application/json'})

    def test_only_admin_can_publish(self):
        """Confere que visitantes e clientes não conseguem publicar notícias."""
        self.assertEqual(self.post().status_code, 403)
        self.login('cliente')
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse((Path(self.folder.name) / 'noticias.sqlite3').exists())

    def test_csrf_and_invalid_images_do_not_save(self):
        """Confere que token inválido ou foto incompatível impedem a gravação."""
        self.login()
        self.assertEqual(self.post(csrf_token='wrong').status_code, 403)
        self.assertEqual(self.post(fotos=[(BytesIO(b'<script>bad</script>'), 'fake.jpg')]).status_code, 400)
        self.assertEqual(self.post(fotos=[(photo('GIF'), 'fake.png')]).status_code, 400)
        self.assertFalse((Path(self.folder.name) / 'noticias.sqlite3').exists())

    def test_required_fields_and_photo_count(self):
        """Confere os campos obrigatórios e o limite de fotos por publicação."""
        self.login()
        self.assertEqual(self.post(titulo='').status_code, 400)
        self.assertEqual(self.post(texto='').status_code, 400)
        self.assertEqual(self.post(fotos=[]).status_code, 400)
        self.assertEqual(self.post(fotos=[(photo(), f'{i}.png') for i in range(6)]).status_code, 400)

    def test_publish_persists_and_public_feed_serves_reencoded_photos(self):
        """Confere persistência, feed público e conversão das fotos para JPEG sem metadados."""
        self.login()
        response = self.post()
        self.assertEqual(response.status_code, 201)
        article = response.get_json()['article']
        self.assertEqual(article['type'], 'internal')
        self.assertEqual(article['body'], ['Primeiro parágrafo.', 'Segundo parágrafo.'])
        self.assertEqual(len(article['images']), 2)
        feed = self.client.get('/api/noticias')
        self.assertEqual(feed.headers['Cache-Control'], 'no-store')
        self.assertEqual(feed.get_json()[0]['id'], article['id'])
        self.assertTrue(any(item['type'] == 'external' for item in feed.get_json()))
        image = self.client.get(article['images'][0]['src'])
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.mimetype, 'image/jpeg')
        with Image.open(BytesIO(image.data)) as saved:
            self.assertEqual(saved.format, 'JPEG')
            self.assertFalse(saved.getexif())
        image.close()
        restarted = Flask('news-restart-test', static_folder=str(ROOT / 'static'))
        restarted.config['NEWS_STORAGE_DIR'] = self.folder.name
        init_news(restarted)
        self.assertEqual(restarted.test_client().get('/api/noticias').get_json()[0]['id'], article['id'])

    def test_admin_form_has_preview_and_escapes_published_title(self):
        """Confere a prévia administrativa e a exibição segura de títulos com caracteres HTML."""
        self.login()
        self.assertEqual(self.post(titulo='<script>alert(1)</script>').status_code, 201)
        response = self.client.get('/admin?aba=noticias')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="adminNewsForm"', html)
        self.assertIn('id="newsPreviewImage"', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)

    def test_large_submission_is_actionable(self):
        """Confere que uploads grandes recebem uma mensagem clara sobre o limite permitido."""
        self.login()
        app.config['MAX_CONTENT_LENGTH'] = 200
        response = self.post()
        self.assertEqual(response.status_code, 413)
        self.assertIn('5 MB', response.get_json()['error'])

    def test_edit_preserves_photos_and_creation_date(self):
        """Confere que editar textos mantém as fotos e a data original de criação."""
        self.login()
        original = self.post().get_json()['article']
        response = self.client.post(f'/admin/noticias/{original["id"]}/editar', data={
            'csrf_token': 'test-csrf', 'titulo': 'Título atualizado', 'resumo': 'Novo resumo',
            'texto': 'Texto atualizado.'}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        article = response.get_json()['article']
        self.assertEqual(article['id'], original['id'])
        self.assertEqual(article['created_at'], original['created_at'])
        self.assertIn('updated_at', article)
        self.assertEqual([image['src'] for image in article['images']], [image['src'] for image in original['images']])
        self.assertEqual(self.client.get('/api/noticias').get_json()[0]['title'], 'Título atualizado')

    def test_edit_can_replace_photos(self):
        """Confere que a edição permite substituir as imagens da publicação."""
        self.login()
        original = self.post().get_json()['article']
        response = self.client.post(f'/admin/noticias/{original["id"]}/editar', data={
            'csrf_token': 'test-csrf', 'titulo': original['title'], 'texto': 'Texto revisado.',
            'fotos': (photo(), 'nova-capa.png')}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()['article']['images']), 1)
        self.assertNotEqual(response.get_json()['article']['images'][0]['src'], original['images'][0]['src'])

    def test_edit_and_delete_require_admin_and_csrf(self):
        """Confere perfil administrativo e token de sessão na edição e na exclusão."""
        self.login()
        article = self.post().get_json()['article']
        base = f'/admin/noticias/{article["id"]}'
        for action in ['editar', 'excluir']:
            response = self.client.post(base + '/' + action, data={'csrf_token': 'bad'}, headers={'Accept': 'application/json'})
            self.assertEqual(response.status_code, 403)
        self.login('cliente')
        self.assertEqual(self.client.get(base, headers={'Accept': 'application/json'}).status_code, 403)
        for action in ['editar', 'excluir']:
            response = self.client.post(base + '/' + action, data={'csrf_token': 'test-csrf'}, headers={'Accept': 'application/json'})
            self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get('/api/noticias').get_json()[0]['id'], article['id'])

    def test_delete_removes_article_from_feed_and_admin(self):
        """Confere que a exclusão retira a notícia do feed e da lista administrativa."""
        self.login()
        article = self.post().get_json()['article']
        base = f'/admin/noticias/{article["id"]}'
        self.assertEqual(self.client.get(base, headers={'Accept': 'application/json'}).status_code, 200)
        response = self.client.post(base + '/excluir', data={'csrf_token': 'test-csrf'}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(any(item.get('id') == article['id'] for item in self.client.get('/api/noticias').get_json()))
        self.assertEqual(self.client.get(article['images'][0]['src']).status_code, 404)
        self.assertEqual(self.client.get(base, headers={'Accept': 'application/json'}).status_code, 404)
        html = self.client.get('/admin').get_data(as_text=True)
        self.assertNotIn('data-news-id="' + article['id'] + '"', html)

    def test_invalid_edit_does_not_change_article(self):
        """Confere que uma edição inválida preserva os dados já publicados."""
        self.login()
        original = self.post().get_json()['article']
        response = self.client.post(f'/admin/noticias/{original["id"]}/editar', data={
            'csrf_token': 'test-csrf', 'titulo': 'Não deve ser salvo', 'texto': 'Texto.',
            'fotos': (BytesIO(b'invalid'), 'foto.jpg')}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/api/noticias').get_json()[0]['title'], original['title'])


# Executa este arquivo diretamente; importações não iniciam este bloco.
if __name__ == '__main__':
    unittest.main()
