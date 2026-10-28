"""Export public pages with synthetic records, without reading any CSV."""
from pathlib import Path
from unittest.mock import patch
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from flask import url_for
from app import app
from scripts.demo_data import demo_data




def export():
    frames = demo_data()
    app.config['TESTING'] = True
    app.config['NEWS_STATIC_EXPORT'] = True
    output = ROOT / 'docs'
    with app.test_request_context():
        urls = {url_for(endpoint): filename for endpoint, filename in {
            'index': 'index.html', 'login': 'login.html', 'logout': 'index.html',
            'admin_dashboard': 'admin.html', 'cliente_dashboard': 'cliente.html',
            'baixar_fatura': 'fatura_atual.txt'}.items()}
    # Fail closed: even a future direct CSV read must not publish local records.
    with patch('app.load_csv', side_effect=lambda name: frames[name].copy()), \
         patch('pandas.read_csv', side_effect=RuntimeError('CSV reads forbidden in demo export')), \
         app.test_client() as client:
        for route, role in [('/', None), ('/login', None), ('/admin', 'admin'), ('/cliente', 'cliente')]:
            with client.session_transaction() as session:
                session.clear()
                if role:
                    user = frames['usuarios.csv'].query('tipo == @role').iloc[0]
                    session.update(user_id=int(user['id']), user_tipo=role, user_nome=str(user['nome']))
            response = client.get(route)
            assert response.status_code == 200, route
            html = response.get_data(as_text=True)
            html = re.sub(r'((?:href|src)=")(/[^"?#]*)([^"\n]*)"',
                          lambda match: match[1] + (match[2][1:] if match[2].startswith('/static/')
                          else urls.get(match[2], match[2])) + match[3] + '"', html)
            if route == '/':
                html = html.replace('data-news-source="/api/noticias"', 'data-news-source="static/noticias.json"')
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
            if route == '/admin':
                html, count = re.subn(r"fetch\('/admin/residencia/' \+ painelResidenciaId \+ '/atualizar', \{.*?\n    \}\)",
                                     'Promise.resolve({ json: () => Promise.resolve({ success: true }) })', html, flags=re.S)
                assert count == 1
            if route == '/cliente':
                html = re.sub(r'<form\b[^>]*class="upload-form"[^>]*>',
                              '<form class="upload-form" onsubmit="event.preventDefault(); alert(\'Envio indisponivel na demonstracao estatica.\');">', html)
            assert '{{' not in html and '{%' not in html
            assert '@example.invalid' not in html and 'value="unused"' not in html
            html = '\n'.join(line.rstrip() for line in html.splitlines()) + '\n'
            (output / urls[route]).write_text(html, encoding='utf-8')
            print('Generated:', 'docs/' + urls[route])
    shutil.copyfile(ROOT / 'static/css/style.css', output / 'static/css/style.css')
    (output / 'fatura_atual.txt').write_text('FATURA FICTICIA PARA DEMONSTRACAO\nBeneficiario: Pessoa exemplo 01\nUC: UC ficticia 01\nValor ilustrativo: R$ 30,00\n', encoding='utf-8')


if __name__ == '__main__':
    export()
