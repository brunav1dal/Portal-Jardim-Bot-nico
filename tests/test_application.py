"""Objetivo: Verifica os fluxos entre rotas, serviços, templates e dados sem alterar os registros reais."""
# Dependências usadas por este módulo.
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Permite executar os testes a partir da raiz ou diretamente pelo arquivo.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from banco_solar import create_app
from banco_solar.demo import demo_data
from scripts.export_demo import export


class ApplicationTests(unittest.TestCase):
    """Verifica os fluxos entre rotas, serviços, templates e dados sem alterar os registros reais."""
    def setUp(self):
        """Prepara dados e armazenamento isolados antes de cada teste."""
        self.frames = demo_data()
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
        self.reader = patch('banco_solar.repositories.dados_csv.load_csv',
                            side_effect=lambda name: self.frames[name].copy())
        self.reader.start()
        self.addCleanup(self.reader.stop)

    def login(self, role):
        """Prepara uma sessão autenticada para o perfil necessário ao teste."""
        user = self.frames['usuarios.csv'].query('tipo == @role').iloc[0]
        with self.client.session_transaction() as session:
            session.update(user_id=str(user['id']), user_tipo=role, user_nome=user['nome'])

    def test_public_pages_assets_and_protected_pages(self):
        """Confere páginas públicas, recursos e restrições de acesso aos painéis."""
        for path in ('/', '/login', '/api/transparencia', '/api/noticias',
                     '/static/css/style.css', '/static/js/header-menu.js'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()
        for path in ('/admin', '/cliente', '/cliente/fatura'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/login'))
        self.login('admin')
        self.assertEqual(self.client.get('/admin').status_code, 200)
        self.assertEqual(self.client.get('/cliente').status_code, 302)
        self.login('cliente')
        self.assertEqual(self.client.get('/cliente').status_code, 200)
        response = self.client.get('/cliente/fatura')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Fatura Atual', response.get_data(as_text=True))

    def test_login_redirects_and_logout(self):
        """Confere o destino de cada perfil após o login e a limpeza da sessão no logout."""
        for role, target in (('admin', '/admin'), ('cliente', '/cliente')):
            user = self.frames['usuarios.csv'].query('tipo == @role').iloc[0]
            response = self.client.post('/login', data={'email': user['email'], 'senha': user['senha']})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith(target))
            self.client.get('/logout')
            with self.client.session_transaction() as session:
                self.assertNotIn('user_id', session)

    def test_admin_update_uses_repository_and_checks_authorization(self):
        """Confere permissão, validação, registro inexistente e gravação do status administrativo."""
        path = '/admin/residencia/1/atualizar'
        self.assertEqual(self.client.post(path, json={'em_dia_banco': 'nao'}).status_code, 403)
        self.login('admin')
        # Isola dependências externas e gravações para proteger os dados locais.
        with patch('banco_solar.repositories.dados_csv.save_csv') as save:
            self.assertEqual(self.client.post(path, json={'em_dia_banco': 'invalido'}).status_code, 400)
            save.assert_not_called()
            self.assertEqual(self.client.post('/admin/residencia/99999/atualizar',
                                              json={'em_dia_banco': 'nao'}).status_code, 404)
            save.assert_not_called()
            self.assertEqual(self.client.post(path, json={'em_dia_banco': 'nao'}).status_code, 200)
            name, frame = save.call_args.args
            self.assertEqual(name, 'residencias.csv')
            self.assertEqual(frame.loc[frame['id'] == 1, 'em_dia_banco'].iloc[0], 'nao')

    def test_boleto_upload_keeps_csv_and_file_together(self):
        """Confere que o envio salva o documento e registra seu histórico no repositório."""
        self.login('cliente')
        # Isola dependências externas e gravações para proteger os dados locais.
        with tempfile.TemporaryDirectory() as folder, \
             patch('banco_solar.services.boletos.BOLETOS_DIR', folder), \
             patch('banco_solar.repositories.dados_csv.save_csv') as save:
            response = self.client.post('/cliente/anexar-boleto',
                                        data={'boleto': (BytesIO(b'%PDF-1.4 teste'), 'conta.pdf')})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(len(list(Path(folder).rglob('*.pdf'))), 1)
            self.assertEqual(save.call_args.args[0], 'boletos.csv')
            self.assertEqual(save.call_args.args[1].iloc[-1]['nome_arquivo'], 'conta.pdf')

    def test_static_export_does_not_read_local_csv_and_copies_assets(self):
        # O exportador também bloqueia pandas.read_csv internamente.
        """Confere a exportação com dados fictícios e a cópia dos recursos sem uploads."""
        self.reader.stop()
        # Isola dependências externas e gravações para proteger os dados locais.
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(StringIO()):
            export(folder)
            for filename in ('index.html', 'login.html', 'admin.html', 'cliente.html',
                             'static/css/project-flow.css', 'static/js/header-menu.js',
                             'static/img/orquidea-icon.svg', 'static/noticias.json'):
                self.assertTrue((Path(folder) / filename).is_file(), filename)
            self.assertFalse((Path(folder) / 'static/uploads').exists())
            self.assertNotIn('{{', (Path(folder) / 'index.html').read_text(encoding='utf-8'))


# Executa este arquivo diretamente; importações não iniciam este bloco.
if __name__ == '__main__':
    unittest.main()
