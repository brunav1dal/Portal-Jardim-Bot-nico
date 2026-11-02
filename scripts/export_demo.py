"""Objetivo: Gera a demonstração estática com dados fictícios e copia os recursos públicos para docs/."""
# Dependências usadas por este módulo.
from pathlib import Path
from unittest.mock import patch
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flask import url_for
from banco_solar import create_app
from contextlib import ExitStack

from banco_solar.demo import demo_data

app = create_app()




def export(output_dir=None):
    """Renderiza as telas com dados fictícios e prepara os arquivos da demonstração estática."""
    # Cria as tabelas fictícias e configura uma exportação sem dados cadastrais reais.
    frames = demo_data()
    app.config['TESTING'] = True
    app.config['NEWS_STATIC_EXPORT'] = True
    output = Path(output_dir) if output_dir else ROOT / 'docs'
    output.mkdir(parents=True, exist_ok=True)
    # Relaciona os endpoints Flask aos nomes dos arquivos HTML estáticos.
    with app.test_request_context():
        urls = {url_for(endpoint): filename for endpoint, filename in {
            'index': 'index.html', 'login': 'login.html', 'logout': 'index.html',
            'admin_dashboard': 'admin.html', 'cliente_dashboard': 'cliente.html',
            'baixar_fatura': 'fatura_atual.txt'}.items()}
    # Bloqueia leituras diretas de CSV para impedir a exportação acidental de cadastros locais.
    # Substitui o repositório por dados fictícios e bloqueia leituras diretas de CSV.
    with ExitStack() as stack:
        stack.enter_context(patch('banco_solar.repositories.dados_csv.load_csv', side_effect=lambda name: frames[name].copy()))
        stack.enter_context(patch('pandas.read_csv', side_effect=RuntimeError('CSV reads forbidden in demo export')))
        client = stack.enter_context(app.test_client())
        # Renderiza cada tela com uma sessão demonstrativa apropriada ao perfil.
        for route, role in [('/', None), ('/login', None), ('/admin', 'admin'), ('/cliente', 'cliente')]:
            with client.session_transaction() as session:
                session.clear()
                if role:
                    user = frames['usuarios.csv'].query('tipo == @role').iloc[0]
                    session.update(user_id=int(user['id']), user_tipo=role, user_nome=str(user['nome']))
            response = client.get(route)
            assert response.status_code == 200, route
            html = response.get_data(as_text=True)
            # Adapta caminhos e formulários para a navegação sem backend na demonstração.
            html = re.sub(r'((?:href|src)=")(/[^"?#]*)([^"\n]*)"',
                          lambda match: match[1] + (match[2][1:] if match[2].startswith('/static/')
                          else urls.get(match[2], match[2])) + match[3] + '"', html)
            if route == '/':
                html = html.replace('data-news-source="/api/noticias"', 'data-news-source="static/noticias.json"')
            # Ajusta as ações administrativas para que a demonstração não grave dados.
            if route == '/admin':
                html = html.replace('action="/admin/noticias"', 'action="#"')
            if route == '/login':
                html = re.sub(r'<form\b.*?</form>', '''<p class="subtitle">Demonstracao com dados inteiramente ficticios.</p>
<div class="form-group">
<a href="admin.html" class="btn btn-primary login-btn" style="display:block;text-align:center;margin-bottom:1rem;">Ver painel administrativo</a>
<a href="cliente.html" class="btn btn-outline login-btn" style="display:block;text-align:center;">Ver painel do cliente</a>
</div>''', html, flags=re.S)
            marker = '<p class="flash-success">Demonstracao estatica: pessoas e valores ficticios. Alteracoes nao sao gravadas no servidor.</p>'
            if role:
                html = html.replace('<div class="container dashboard">', '<div class="container dashboard">' + marker, 1)
            elif route == '/':
                html = html.replace('<div class="container">', '<div class="container">' + marker, 1)
            # Ajusta as ações administrativas para que a demonstração não grave dados.
            if route == '/admin':
                html, count = re.subn(r"fetch\('/admin/residencia/' \+ painelResidenciaId \+ '/atualizar', \{.*?\n    \}\)",
                                     'Promise.resolve({ json: () => Promise.resolve({ success: true }) })', html, flags=re.S)
                assert count == 1
            # Desativa o envio de documentos na cópia estática.
            if route == '/cliente':
                html = re.sub(r'<form\b[^>]*class="upload-form"[^>]*>',
                              '<form class="upload-form" onsubmit="event.preventDefault(); alert(\'Envio indisponivel na demonstracao estatica.\');">', html)
            # Interrompe a exportação se houver template não resolvido ou credencial demonstrativa exposta.
            assert '{{' not in html and '{%' not in html
            assert '@example.invalid' not in html and 'value="unused"' not in html
            html = '\n'.join(line.rstrip() for line in html.splitlines()) + '\n'
            (output / urls[route]).write_text(html, encoding='utf-8')
            print('Generated:', urls[route])
    # Copia recursos públicos e exclui os documentos enviados pelos usuários.
    shutil.copytree(ROOT / 'static', output / 'static', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('uploads'))
    (output / 'fatura_atual.txt').write_text('FATURA FICTICIA PARA DEMONSTRACAO\nBeneficiario: Pessoa exemplo 01\nUC: UC ficticia 01\nValor ilustrativo: R$ 30,00\n', encoding='utf-8')


# Executa este arquivo diretamente; importações não iniciam este bloco.
if __name__ == '__main__':
    export()
