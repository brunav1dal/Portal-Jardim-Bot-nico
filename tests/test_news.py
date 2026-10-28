from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app
from flask import Flask
from news import init_news
from PIL import Image


def photo(fmt='PNG'):
    data = BytesIO()
    Image.new('RGB', (80, 60), '#15803d').save(data, fmt)
    data.seek(0)
    return data


class NewsPublishingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.previous = {key: app.config.get(key) for key in ['TESTING', 'NEWS_STORAGE_DIR', 'MAX_CONTENT_LENGTH']}
        app.config.update(TESTING=True, NEWS_STORAGE_DIR=self.folder.name)
        self.client = app.test_client()

    def tearDown(self):
        app.config.update(self.previous)
        self.folder.cleanup()

    def login(self, role='admin'):
        with self.client.session_transaction() as session:
            session.update(user_id='1', user_tipo=role, user_nome='Teste', news_csrf='test-csrf')

    def post(self, **overrides):
        data = {'csrf_token': 'test-csrf', 'titulo': 'Notícia da comunidade',
                'resumo': 'Resumo da atividade.', 'texto': 'Primeiro parágrafo.\n\nSegundo parágrafo.',
                'fotos': [(photo(), 'capa.png'), (photo('JPEG'), 'turma.jpg')]}
        data.update(overrides)
        return self.client.post('/admin/noticias', data=data, headers={'Accept': 'application/json'})

    def test_only_admin_can_publish(self):
        self.assertEqual(self.post().status_code, 403)
        self.login('cliente')
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse((Path(self.folder.name) / 'noticias.sqlite3').exists())

    def test_csrf_and_invalid_images_do_not_save(self):
        self.login()
        self.assertEqual(self.post(csrf_token='wrong').status_code, 403)
        self.assertEqual(self.post(fotos=[(BytesIO(b'<script>bad</script>'), 'fake.jpg')]).status_code, 400)
        self.assertEqual(self.post(fotos=[(photo('GIF'), 'fake.png')]).status_code, 400)
        self.assertFalse((Path(self.folder.name) / 'noticias.sqlite3').exists())

    def test_required_fields_and_photo_count(self):
        self.login()
        self.assertEqual(self.post(titulo='').status_code, 400)
        self.assertEqual(self.post(texto='').status_code, 400)
        self.assertEqual(self.post(fotos=[]).status_code, 400)
        self.assertEqual(self.post(fotos=[(photo(), f'{i}.png') for i in range(6)]).status_code, 400)

    def test_publish_persists_and_public_feed_serves_reencoded_photos(self):
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
        self.login()
        app.config['MAX_CONTENT_LENGTH'] = 200
        response = self.post()
        self.assertEqual(response.status_code, 413)
        self.assertIn('5 MB', response.get_json()['error'])


if __name__ == '__main__':
    unittest.main()
