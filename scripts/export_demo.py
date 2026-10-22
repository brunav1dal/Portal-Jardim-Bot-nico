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


def demo_data():
    users = [{'id': 1, 'nome': 'Administrador exemplo', 'email': 'admin@example.invalid',
              'senha': 'unused', 'tipo': 'admin', 'economia_kw': 0, 'creditos': 0,
              'kw_recebidos': 0, 'investido': 0, 'cashback_orquideas': 0,
              'data_cadastro': '2025-01-01'}]
    homes, benefits = [], []
    for i in range(1, 11):
        uid, name = i + 1, f'Pessoa exemplo {i:02d}'
        users.append(dict(users[0], id=uid, nome=name, email=f'pessoa{i}@example.invalid', tipo='cliente'))
        homes.append({'id': i, 'usuario_id': uid, 'endereco': f'UC ficticia {i:02d}',
                      'em_dia_banco': 'sim', 'em_dia_concessionaria': 'sim',
                      'cashback_em_dia': 'sim', 'consumo_mensal_kwh': 100,
                      'economia_mensal_rs': 30, 'ultima_atualizacao': '2025-02-01'})
        for month in ['2025-01', '2025-02']:
            benefits.append({'mes': month, 'usuario_id': uid, 'nome': name,
                             'percentual_cota': 10, 'cota_kwh': 100, 'consumo_total_kwh': 100,
                             'tarifa_social': 'nao', 'energia_recebida_kwh': 100,
                             'valor_beneficio_rs': 40, 'valor_projeto_rs': 20,
                             'creditos_acumulados': 0, 'vencimento': month + '-20',
                             'valor_energisa_rs': 30, 'excedeu_cota_kwh': 0, 'cashback_rs': 10})
    plants = [{'id': 1, 'nome': 'Usina demonstrativa', 'localizacao': 'Local ficticio',
               'capacidade_kw': 10, 'geracao_mensal_kwh': 1000, 'status': 'ativa',
               'data_instalacao': '2025-01-01', 'eficiencia_percent': 90}]
    generation = [{'mes': month, 'usina_id': 1, 'geracao_kwh': 1000,
                   'co2_evitado_kg': 100, 'receita_rs': 200,
                   'energia_beneficiarios_kwh': 1000, 'fonte': 'planilha'}
                  for month in ['2025-01', '2025-02']]
    return {'usuarios.csv': pd.DataFrame(users), 'residencias.csv': pd.DataFrame(homes),
            'beneficios_mensais.csv': pd.DataFrame(benefits), 'usinas.csv': pd.DataFrame(plants),
            'geracao_mensal.csv': pd.DataFrame(generation),
            'boletos.csv': pd.DataFrame(columns=['id', 'usuario_id', 'nome_arquivo', 'data_envio', 'status'])}


def export():
    frames = demo_data()
    app.config['TESTING'] = True
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
            assert '@example.invalid' not in html and 'unused' not in html
            html = '\n'.join(line.rstrip() for line in html.splitlines()) + '\n'
            (output / urls[route]).write_text(html, encoding='utf-8')
            print('Generated:', 'docs/' + urls[route])
    shutil.copyfile(ROOT / 'static/css/style.css', output / 'static/css/style.css')
    (output / 'fatura_atual.txt').write_text('FATURA FICTICIA PARA DEMONSTRACAO\nBeneficiario: Pessoa exemplo 01\nUC: UC ficticia 01\nValor ilustrativo: R$ 30,00\n', encoding='utf-8')


if __name__ == '__main__':
    export()
