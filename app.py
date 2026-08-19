"""
Banco Comunitário Jardim Botânico - Sistema de Gestão de Bancos Solares
Aplicação Flask com painel público, painel de cliente e painel administrativo.
"""

import os
import datetime
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'banco-solar-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB por upload

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BOLETOS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'boletos')
EXTENSOES_PERMITIDAS = {'pdf', 'png', 'jpg', 'jpeg'}

TARIFA_SOLAR_CLIENTE = 0.30  # R$/kWh cobrado pelo banco na fatura do cliente

# Coordenadas aproximadas dos bairros/cidades da região de João Pessoa (PB) onde as usinas parceiras estão instaladas
COORDENADAS_CIDADES = {
    'R. Arquivista Jonathas Carécas, 74 - Castelo Branco, João Pessoa - PB, 58057-034': (-7.1342, -34.8550),
}


def load_csv(filename):
    """Carrega um arquivo CSV do diretório de dados."""
    filepath = os.path.join(DATA_DIR, filename)
    return pd.read_csv(filepath)


def arquivo_permitido(nome_arquivo):
    """Verifica se a extensão do arquivo enviado é aceita."""
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS


def calcular_fatura(residencia_row):
    """Calcula o valor e o status da fatura atual do cliente junto ao banco."""
    valor = round(float(residencia_row['consumo_mensal_kwh']) * TARIFA_SOLAR_CLIENTE, 2)
    status = 'Paga' if residencia_row['em_dia_banco'] == 'sim' else 'Em Aberto'
    return {'valor': valor, 'status': status}


# ─────────────────────────── ROTAS PÚBLICAS ───────────────────────────

@app.route('/')
def index():
    """Página pública de transparência do banco solar."""
    usuarios = load_csv('usuarios.csv')
    usinas = load_csv('usinas.csv')
    geracao = load_csv('geracao_mensal.csv')

    clientes = usuarios[usuarios['tipo'] == 'cliente']

    transparencia = {
        'economia_kw': round(clientes['economia_kw'].sum(), 1),
        'creditos': round(clientes['creditos'].sum(), 1),
        'kw_recebidos': round(clientes['kw_recebidos'].sum(), 1),
        'investido': round(clientes['investido'].sum(), 2),
        'cashback_orquideas': round(clientes['cashback_orquideas'].sum(), 2),
        'geracao_total_kwh': round(geracao['geracao_kwh'].sum(), 1),
        'co2_evitado_total': round(geracao['co2_evitado_kg'].sum(), 1),
        'num_usinas': len(usinas),
        'num_clientes': len(clientes),
    }

    # Dados para gráficos
    geracao_por_mes = geracao.groupby('mes').agg({
        'geracao_kwh': 'sum',
        'co2_evitado_kg': 'sum'
    }).reset_index().to_dict('records')

    geracao_por_usina = geracao.groupby('usina_id').agg({
        'geracao_kwh': 'sum'
    }).reset_index()
    nomes_usinas = usinas[['id', 'nome']].rename(columns={'id': 'usina_id'})
    geracao_por_usina = geracao_por_usina.merge(nomes_usinas, on='usina_id')
    geracao_por_usina_dict = geracao_por_usina[['nome', 'geracao_kwh']].to_dict('records')

    # Localização das usinas para o mapa
    usinas_mapa = []
    for _, u in usinas.iterrows():
        lat, lng = COORDENADAS_CIDADES.get(u['localizacao'], (None, None))
        usinas_mapa.append({
            'nome': u['nome'],
            'localizacao': u['localizacao'],
            'status': u['status'],
            'capacidade_kw': u['capacidade_kw'],
            'lat': lat,
            'lng': lng,
        })

    return render_template('index.html',
                           transparencia=transparencia,
                           geracao_por_mes=geracao_por_mes,
                           geracao_por_usina=geracao_por_usina_dict,
                           usinas_mapa=usinas_mapa)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        usuarios = load_csv('usuarios.csv')
        user = usuarios[(usuarios['email'] == email) & (usuarios['senha'] == senha)]

        if not user.empty:
            user_data = user.iloc[0]
            session['user_id'] = int(user_data['id'])
            session['user_nome'] = user_data['nome']
            session['user_tipo'] = user_data['tipo']

            if user_data['tipo'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cliente_dashboard'))
        else:
            flash('E-mail ou senha incorretos. Tente novamente.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Encerrar sessão."""
    session.clear()
    return redirect(url_for('index'))


# ─────────────────────────── ROTAS DO CLIENTE ───────────────────────────

@app.route('/cliente')
def cliente_dashboard():
    """Painel do cliente."""
    if 'user_id' not in session or session.get('user_tipo') != 'cliente':
        return redirect(url_for('login'))

    usuarios = load_csv('usuarios.csv')
    residencias = load_csv('residencias.csv')

    user = usuarios[usuarios['id'] == session['user_id']].iloc[0]
    residencia = residencias[residencias['usuario_id'] == session['user_id']]

    user_data = {
        'nome': user['nome'],
        'economia_kw': user['economia_kw'],
        'creditos': user['creditos'],
        'kw_recebidos': user['kw_recebidos'],
        'investido': user['investido'],
        'cashback_orquideas': user['cashback_orquideas'],
        'data_cadastro': user['data_cadastro'],
    }

    residencia_data = None
    fatura = None
    if not residencia.empty:
        r = residencia.iloc[0]
        residencia_data = {
            'endereco': r['endereco'],
            'em_dia_banco': r['em_dia_banco'],
            'em_dia_concessionaria': r['em_dia_concessionaria'],
            'cashback_em_dia': r['cashback_em_dia'],
            'consumo_mensal_kwh': r['consumo_mensal_kwh'],
            'economia_mensal_rs': r['economia_mensal_rs'],
        }
        fatura = calcular_fatura(r)

    # Histórico de boletos da concessionária enviados pelo cliente
    boletos = load_csv('boletos.csv')
    boletos_cliente = boletos[boletos['usuario_id'] == session['user_id']]
    boletos_historico = boletos_cliente.sort_values('data_envio', ascending=False).to_dict('records')

    # Dados simulados de histórico mensal para o cliente
    meses = ['Set/25', 'Out/25', 'Nov/25', 'Dez/25', 'Jan/26', 'Fev/26', 'Mar/26', 'Abr/26']
    import random
    random.seed(session['user_id'])
    historico = {
        'meses': meses,
        'economia': [round(user['economia_kw'] / 8 * (0.8 + random.random() * 0.4), 1) for _ in meses],
        'creditos': [round(user['creditos'] / 8 * (0.7 + random.random() * 0.6), 1) for _ in meses],
        'kw_recebidos': [round(user['kw_recebidos'] / 8 * (0.8 + random.random() * 0.4), 1) for _ in meses],
    }

    # Comparação com os demais beneficiários
    clientes = usuarios[usuarios['tipo'] == 'cliente']
    metricas = ['economia_kw', 'creditos', 'kw_recebidos', 'cashback_orquideas']
    comparacao = {}
    for m in metricas:
        media = clientes[m].mean()
        valor = float(user[m])
        escala = max(valor, media, 0.01) * 1.15
        comparacao[m] = {
            'valor': valor,
            'media': round(media, 1),
            'diferenca_pct': round((valor - media) / media * 100, 1) if media else 0,
            'valor_pct': round(valor / escala * 100, 1),
            'media_pct': round(media / escala * 100, 1),
        }

    return render_template('cliente.html',
                           user=user_data,
                           residencia=residencia_data,
                           fatura=fatura,
                           historico=historico,
                           comparacao=comparacao,
                           boletos_historico=boletos_historico)


@app.route('/cliente/anexar-boleto', methods=['POST'])
def anexar_boleto():
    """Recebe o upload de um novo boleto da concessionária."""
    if 'user_id' not in session or session.get('user_tipo') != 'cliente':
        return redirect(url_for('login'))

    arquivo = request.files.get('boleto')
    if not arquivo or arquivo.filename == '':
        flash('Selecione um arquivo para anexar.', 'error')
        return redirect(url_for('cliente_dashboard'))

    if not arquivo_permitido(arquivo.filename):
        flash('Formato não suportado. Envie um arquivo PDF, PNG ou JPG.', 'error')
        return redirect(url_for('cliente_dashboard'))

    user_id = session['user_id']
    pasta_usuario = os.path.join(BOLETOS_DIR, str(user_id))
    os.makedirs(pasta_usuario, exist_ok=True)

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    nome_seguro = secure_filename(arquivo.filename)
    arquivo.save(os.path.join(pasta_usuario, f'{timestamp}_{nome_seguro}'))

    boletos = load_csv('boletos.csv')
    novo_id = int(boletos['id'].max()) + 1 if not boletos.empty else 1
    novo_boleto = pd.DataFrame([{
        'id': novo_id,
        'usuario_id': user_id,
        'nome_arquivo': arquivo.filename,
        'data_envio': datetime.date.today().isoformat(),
        'status': 'Enviado',
    }])
    boletos = pd.concat([boletos, novo_boleto], ignore_index=True)
    boletos.to_csv(os.path.join(DATA_DIR, 'boletos.csv'), index=False)

    flash('Boleto anexado com sucesso! Ele será analisado pela equipe do banco.', 'success')
    return redirect(url_for('cliente_dashboard'))


@app.route('/cliente/fatura')
def baixar_fatura():
    """Gera a fatura atual do cliente para download."""
    if 'user_id' not in session or session.get('user_tipo') != 'cliente':
        return redirect(url_for('login'))

    usuarios = load_csv('usuarios.csv')
    residencias = load_csv('residencias.csv')
    user = usuarios[usuarios['id'] == session['user_id']].iloc[0]
    residencia = residencias[residencias['usuario_id'] == session['user_id']]

    if residencia.empty:
        flash('Nenhuma residência associada à sua conta para gerar a fatura.', 'error')
        return redirect(url_for('cliente_dashboard'))

    r = residencia.iloc[0]
    fatura = calcular_fatura(r)

    conteudo = (
        'BANCO COMUNITÁRIO JARDIM BOTÂNICO\n'
        'Fatura Atual\n'
        '------------------------------------------\n'
        f"Beneficiário: {user['nome']}\n"
        f"Endereço: {r['endereco']}\n"
        f"Consumo do mês: {r['consumo_mensal_kwh']} kWh\n"
        f"Valor da fatura: R$ {fatura['valor']:.2f}\n"
        f"Status: {fatura['status']}\n"
        '------------------------------------------\n'
        'Fatura referente à energia solar fornecida pelo\n'
        'Banco Comunitário Jardim Botânico.\n'
    )

    return Response(
        conteudo,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=fatura_atual.txt'}
    )


# ─────────────────────────── ROTAS DO ADMIN ───────────────────────────

@app.route('/admin')
def admin_dashboard():
    """Painel administrativo."""
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return redirect(url_for('login'))

    usinas = load_csv('usinas.csv')
    geracao = load_csv('geracao_mensal.csv')
    residencias = load_csv('residencias.csv')
    usuarios = load_csv('usuarios.csv')

    # Dados das usinas
    usinas_data = usinas.to_dict('records')

    # Dados unificados
    total_capacidade = usinas['capacidade_kw'].sum()
    total_geracao_mensal = usinas['geracao_mensal_kwh'].sum()
    total_co2 = geracao['co2_evitado_kg'].sum()
    media_eficiencia = round(usinas['eficiencia_percent'].mean(), 1)

    dados_unificados = {
        'total_capacidade': total_capacidade,
        'total_geracao_mensal': total_geracao_mensal,
        'total_co2': total_co2,
        'media_eficiencia': media_eficiencia,
        'num_usinas_ativas': len(usinas[usinas['status'] == 'ativa']),
        'num_usinas_manutencao': len(usinas[usinas['status'] == 'manutencao']),
    }

    # Economia em relação à concessionária (tarifa média R$ 0,75/kWh)
    tarifa_concessionaria = 0.75
    tarifa_solar = 0.30
    economia_concessionaria = {
        'tarifa_concessionaria': tarifa_concessionaria,
        'tarifa_solar': tarifa_solar,
        'economia_percentual': round((1 - tarifa_solar / tarifa_concessionaria) * 100, 1),
        'economia_mensal_rs': round(total_geracao_mensal * (tarifa_concessionaria - tarifa_solar), 2),
    }

    # Residências beneficiárias
    res_com_usuarios = residencias.merge(
        usuarios[['id', 'nome']].rename(columns={'id': 'usuario_id'}),
        on='usuario_id'
    )
    residencias_data = res_com_usuarios.to_dict('records')

    # Meses dentro da cota de energia (simulação determinística por residência,
    # já que o histórico mensal de consumo por residência não existe nos dados)
    import random as random_res
    MESES_HISTORICO_RESIDENCIA = 6
    for r in residencias_data:
        random_res.seed(1000 + r['id'])
        cota = r['consumo_mensal_kwh'] * (0.85 + random_res.random() * 0.3)
        meses_dentro = 0
        for _ in range(MESES_HISTORICO_RESIDENCIA):
            consumo_mes = r['consumo_mensal_kwh'] * (0.8 + random_res.random() * 0.4)
            if consumo_mes <= cota:
                meses_dentro += 1
        r['meses_dentro_cota'] = meses_dentro
        r['meses_totais'] = MESES_HISTORICO_RESIDENCIA

    # Apenas os beneficiários que conseguiram ficar dentro da cota em pelo menos um mês
    residencias_dentro_cota = [r for r in residencias_data if r['meses_dentro_cota'] > 0]

    # Estatísticas das residências
    total_residencias = len(residencias)
    em_dia_banco = len(residencias[residencias['em_dia_banco'] == 'sim'])
    em_dia_conc = len(residencias[residencias['em_dia_concessionaria'] == 'sim'])
    cashback_ok = len(residencias[residencias['cashback_em_dia'] == 'sim'])

    stats_residencias = {
        'total': total_residencias,
        'em_dia_banco': em_dia_banco,
        'em_dia_banco_pct': round(em_dia_banco / total_residencias * 100, 1),
        'em_dia_concessionaria': em_dia_conc,
        'em_dia_concessionaria_pct': round(em_dia_conc / total_residencias * 100, 1),
        'cashback_em_dia': cashback_ok,
        'cashback_em_dia_pct': round(cashback_ok / total_residencias * 100, 1),
    }

    # Geração mensal por usina (para gráficos)
    geracao_por_mes = geracao.groupby('mes').agg({
        'geracao_kwh': 'sum',
        'co2_evitado_kg': 'sum',
        'receita_rs': 'sum'
    }).reset_index().to_dict('records')

    # Geração individual por usina e mês
    geracao_individual = {}
    for _, usina in usinas.iterrows():
        usina_geracao = geracao[geracao['usina_id'] == usina['id']].sort_values('mes')
        geracao_individual[usina['nome']] = {
            'meses': usina_geracao['mes'].tolist(),
            'geracao': usina_geracao['geracao_kwh'].tolist(),
            'co2': usina_geracao['co2_evitado_kg'].tolist(),
            'receita': usina_geracao['receita_rs'].tolist(),
        }

    return render_template('admin.html',
                           usinas=usinas_data,
                           dados_unificados=dados_unificados,
                           economia_concessionaria=economia_concessionaria,
                           residencias=residencias_data,
                           residencias_dentro_cota=residencias_dentro_cota,
                           stats_residencias=stats_residencias,
                           geracao_por_mes=geracao_por_mes,
                           geracao_individual=geracao_individual)


@app.route('/admin/residencia/<int:residencia_id>/atualizar', methods=['POST'])
def atualizar_residencia(residencia_id):
    """Atualiza os status (banco, concessionária, cashback) de uma residência."""
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return jsonify({'success': False, 'error': 'não autorizado'}), 403

    dados = request.get_json(silent=True) or {}
    campos_validos = {'em_dia_banco', 'em_dia_concessionaria', 'cashback_em_dia'}
    atualizacoes = {k: v for k, v in dados.items() if k in campos_validos and v in ('sim', 'nao')}

    if not atualizacoes:
        return jsonify({'success': False, 'error': 'dados inválidos'}), 400

    residencias_path = os.path.join(DATA_DIR, 'residencias.csv')
    residencias = pd.read_csv(residencias_path)

    if residencia_id not in residencias['id'].values:
        return jsonify({'success': False, 'error': 'residência não encontrada'}), 404

    for campo, valor in atualizacoes.items():
        residencias.loc[residencias['id'] == residencia_id, campo] = valor
    residencias.loc[residencias['id'] == residencia_id, 'ultima_atualizacao'] = datetime.date.today().isoformat()

    residencias.to_csv(residencias_path, index=False, float_format='%.2f')

    return jsonify({'success': True})


# ─────────────────────────── API ENDPOINTS ───────────────────────────

@app.route('/api/transparencia')
def api_transparencia():
    """API pública para dados de transparência."""
    usuarios = load_csv('usuarios.csv')
    geracao = load_csv('geracao_mensal.csv')
    clientes = usuarios[usuarios['tipo'] == 'cliente']

    return jsonify({
        'economia_kw': round(clientes['economia_kw'].sum(), 1),
        'creditos': round(clientes['creditos'].sum(), 1),
        'kw_recebidos': round(clientes['kw_recebidos'].sum(), 1),
        'investido': round(clientes['investido'].sum(), 2),
        'cashback_orquideas': round(clientes['cashback_orquideas'].sum(), 2),
        'geracao_total_kwh': round(geracao['geracao_kwh'].sum(), 1),
        'co2_evitado_total': round(geracao['co2_evitado_kg'].sum(), 1),
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
