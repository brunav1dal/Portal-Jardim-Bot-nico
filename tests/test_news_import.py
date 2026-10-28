from email.message import Message
from io import BytesIO
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app
from news_import import ImportErrorMessage, fetch_public_resource, import_article, public_url
from PIL import Image


def photo():
    value = BytesIO()
    Image.new('RGB', (100, 60), '#15803d').save(value, 'PNG')
    return value.getvalue()


class MetadataImportTests(unittest.TestCase):
    def test_metadata_and_relative_cover(self):
        html = b'<title>Fallback</title><meta property="og:title" content="Aula &amp; comunidade"><meta name="description" content="Resumo da atividade"><meta property="og:image" content="/cover.jpg"><meta property="og:site_name" content="Jornal local">'
        with patch('news_import.fetch_public_resource', side_effect=[(html, 'https://jornal.example/noticia', 'utf-8'), (photo(), 'https://jornal.example/cover.jpg', 'utf-8')]) as fetch:
            preview = import_article('https://jornal.example/noticia')
        self.assertEqual(preview['title'], 'Aula & comunidade')
        self.assertEqual(preview['source'], 'Jornal local')
        self.assertTrue(preview['image_bytes'])
        self.assertEqual(fetch.call_args_list[1].args[0], 'https://jornal.example/cover.jpg')

    def test_title_fallback_and_missing_image_are_editable(self):
        with patch('news_import.fetch_public_resource', return_value=(b'<title>Uma noticia</title>', 'https://jornal.example/', 'utf-8')):
            preview = import_article('https://jornal.example/')
        self.assertEqual(preview['title'], 'Uma noticia')
        self.assertIsNone(preview['image_bytes'])
        self.assertTrue(preview['warning'])

    def test_private_urls_credentials_and_invalid_schemes_are_rejected(self):
        for value in ['http://127.0.0.1/', 'http://[::1]/', 'http://169.254.169.254/', 'http://10.0.0.1/', 'http://localhost/', 'http://service.internal/', 'https://user:pass@site.com/', 'file:///tmp/a', 'https://site.com:8080/', 'javascript:alert(1)']:
            with self.subTest(url=value), self.assertRaises(ImportErrorMessage):
                public_url(value)

    def test_dns_private_result_is_rejected_before_connection(self):
        with patch('news_import.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 80))]), patch('news_import.socket.create_connection') as connect:
            with self.assertRaises(ImportErrorMessage):
                fetch_public_resource('http://public.example/', 100, {'text/html'})
        connect.assert_not_called()

    def test_connection_uses_checked_ip_and_limits_response_size(self):
        response = MagicMock(status=200)
        response.headers = Message(); response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.read.return_value = b'hello'
        connection = MagicMock(); connection.getresponse.return_value = response
        with patch('news_import.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]) as resolve, patch('news_import.socket.create_connection') as connect, patch('news_import.http.client.HTTPConnection', return_value=connection):
            data, _, _ = fetch_public_resource('http://public.example/', 10, {'text/html'})
            self.assertEqual(data, b'hello')
            connect.assert_called_once_with(('93.184.216.34', 80), timeout=10)
            self.assertEqual(resolve.call_count, 1)
            response.read.assert_called_once_with(11)

    def test_redirect_to_private_address_is_rejected(self):
        response = MagicMock(status=302); response.getheader.return_value = 'http://127.0.0.1/admin'
        connection = MagicMock(); connection.getresponse.return_value = response
        with patch('news_import.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]), patch('news_import.socket.create_connection'), patch('news_import.http.client.HTTPConnection', return_value=connection):
            with self.assertRaises(ImportErrorMessage):
                fetch_public_resource('http://public.example/', 100, {'text/html'})


class ExternalPublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = {key: app.config.get(key) for key in ['NEWS_STORAGE_DIR', 'TESTING']}
        app.config.update(NEWS_STORAGE_DIR=self.temp.name, TESTING=True)
        self.client = app.test_client()
        self.metadata = {'title': 'Notícia externa', 'summary': 'Um resumo.', 'source': 'Jornal local',
                         'url': 'https://jornal.example/materia', 'image_bytes': photo(), 'warning': ''}

    def tearDown(self):
        app.config.update(self.old)
        self.temp.cleanup()

    def login(self):
        with self.client.session_transaction() as session:
            session.update(user_id='1', user_tipo='admin', news_csrf='csrf')

    def preview(self):
        with patch('news.import_article', return_value=self.metadata):
            return self.client.post('/admin/noticias/importar', data={'url': self.metadata['url'], 'csrf_token': 'csrf'}, headers={'Accept': 'application/json'})

    def test_preview_needs_admin_and_csrf(self):
        self.assertEqual(self.preview().status_code, 403)
        self.login()
        response = self.client.post('/admin/noticias/importar', data={'url': self.metadata['url']}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 403)

    def test_preview_does_not_publish_and_external_publish_reuses_cover(self):
        self.login()
        preview = self.preview()
        self.assertEqual(preview.status_code, 200)
        self.assertFalse((Path(self.temp.name) / 'noticias.sqlite3').exists())
        data = preview.get_json()['preview']
        self.assertEqual(data['title'], self.metadata['title'])
        image = self.client.get(data['images'][0]['src'])
        self.assertEqual(image.status_code, 200); image.close()
        published = self.client.post('/admin/noticias', data={'csrf_token': 'csrf', 'tipo': 'external', 'link_externo': data['url'], 'import_token': data['token'], 'titulo': 'Título revisado', 'resumo': data['summary']}, headers={'Accept': 'application/json'})
        self.assertEqual(published.status_code, 201)
        article = published.get_json()['article']
        self.assertEqual(article['type'], 'external')
        self.assertEqual(article['title'], 'Título revisado')
        self.assertEqual(article['url'], data['url'])
        self.assertEqual(article['source'], 'Jornal local')
        self.assertEqual(article['body'], [])
        self.assertEqual(article['images'], [{'src': data['images'][0]['src'], 'alt': 'Título revisado'}])
        self.assertEqual(self.client.get('/api/noticias').get_json()[0]['id'], article['id'])

    def test_missing_cover_allows_manual_photo(self):
        self.login(); self.metadata.update(image_bytes=None, warning='Envie uma foto.')
        preview = self.preview().get_json()
        self.assertEqual(preview['preview']['images'], [])
        self.assertTrue(preview['warning'])
        fields = {'csrf_token': 'csrf', 'tipo': 'external', 'link_externo': self.metadata['url'], 'titulo': self.metadata['title']}
        self.assertEqual(self.client.post('/admin/noticias', data=fields, headers={'Accept': 'application/json'}).status_code, 400)
        fields['fotos'] = (BytesIO(photo()), 'capa.png')
        self.assertEqual(self.client.post('/admin/noticias', data=fields, headers={'Accept': 'application/json'}).status_code, 201)

    def test_import_token_cannot_be_used_for_a_different_link(self):
        self.login()
        data = self.preview().get_json()['preview']
        response = self.client.post('/admin/noticias', data={'csrf_token': 'csrf', 'tipo': 'external', 'link_externo': 'https://outro.example/', 'import_token': data['token'], 'titulo': data['title']}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
