"""
Banco Comunitário Jardim Botânico - Sistema de Gestão de Bancos Solares
Aplicação Flask com painel público, painel de cliente e painel administrativo.
"""

import os
import datetime
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from scripts.demo_data import demo_data
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from werkzeug.utils import secure_filename
from news import init_news

app = Flask(__name__)
app.secret_key = 'banco-solar-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB por upload
init_news(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODO_DEMONSTRACAO = not os.path.exists(os.path.join(DATA_DIR, 'beneficios_mensais.csv'))
DADOS_DEMONSTRACAO = demo_data() if MODO_DEMONSTRACAO else None


@app.context_processor
def contexto_demonstracao():
    return {'modo_demonstracao': MODO_DEMONSTRACAO}


BOLETOS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'boletos')
EXTENSOES_PERMITIDAS = {'pdf', 'png', 'jpg', 'jpeg'}

TARIFA_SOLAR_CLIENTE = 0.30  # R$/kWh cobrado pelo banco na fatura do cliente

# Localização anterior cadastrada para a usina.
COORDENADAS_CIDADES = {
    'R. Arquivista Jonathas Carécas, 74 - Castelo Branco, João Pessoa - PB, 58057-034': (-7.1342, -34.8550),
}


def load_csv(filename):
    """Carrega um arquivo CSV do diretório de dados."""
    filepath = os.path.join(DATA_DIR, filename)
    if MODO_DEMONSTRACAO and filename in DADOS_DEMONSTRACAO and filename != 'usuarios.csv':
        return DADOS_DEMONSTRACAO[filename].copy()
    dados = pd.read_csv(filepath)
    if filename == 'geracao_mensal.csv':
        for coluna in ('energia_beneficiarios_kwh',):
            if coluna not in dados:
                dados[coluna] = float('nan')
    return dados


def arquivo_permitido(nome_arquivo):
    """Verifica se a extensão do arquivo enviado é aceita."""
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS


def calcular_fatura(residencia_row):
    """Calcula o valor e o status da fatura atual do cliente junto ao banco."""
    if pd.isna(residencia_row.get('em_dia_banco')) or pd.isna(residencia_row.get('consumo_mensal_kwh')):
        return None
    valor = round(float(residencia_row['consumo_mensal_kwh']) * TARIFA_SOLAR_CLIENTE, 2)
    status = 'Paga' if residencia_row['em_dia_banco'] == 'sim' else 'Em Aberto'
    return {'valor': valor, 'status': status}


def calcular_economia_efetiva(beneficios):
    """Calcula a economia líquida como 75% do valor individual do benefício."""
    if beneficios.empty:
        return None
    total = sum(
        (Decimal(str(valor)) * Decimal('0.75') for valor in pd.to_numeric(beneficios['valor_beneficio_rs'], errors='coerce').dropna()),
        Decimal('0'),
    )
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_parcela_beneficio(valor, proporcao):
    """Calcula uma parcela monetária do benefício, arredondada a centavos."""
    if valor is None or pd.isna(valor):
        return None
    return float(
        (Decimal(str(valor)) * Decimal(str(proporcao))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    )


def montar_demonstrativo_economia(beneficios_mes):
    """Monta linhas e totais do demonstrativo com valores derivados da planilha."""
    centavo = Decimal('0.01')
    totais = {
        'valor_energisa_rs': Decimal('0'),
        'valor_beneficio_rs': Decimal('0'),
        'valor_doado_banco_rs': Decimal('0'),
        'sem_economia_rs': Decimal('0'),
        'com_economia_sem_cashback_rs': Decimal('0'),
        'com_economia_com_cashback_rs': Decimal('0'),
        'economia_real_rs': Decimal('0'),
    }
    tem_valor = {campo: False for campo in totais}
    linhas = []

    def decimal_ou_none(valor):
        return None if pd.isna(valor) else Decimal(str(valor))

    def moeda(valor):
        if valor is None:
            return 'Não informado'
        return f"{valor.quantize(centavo, rounding=ROUND_HALF_UP):.2f}".replace('.', ',')

    for _, registro in beneficios_mes.iterrows():
        beneficio = decimal_ou_none(registro['valor_beneficio_rs'])
        energisa = decimal_ou_none(registro['valor_energisa_rs'])
        doado = beneficio / 2 if beneficio is not None else None
        sem_economia = energisa + beneficio if energisa is not None and beneficio is not None else None
        com_economia_sem_cashback = energisa + beneficio / 2 if energisa is not None and beneficio is not None else None
        com_economia_com_cashback = energisa + beneficio / 4 if energisa is not None and beneficio is not None else None
        economia_real = beneficio * Decimal('0.75') if beneficio is not None else None

        valores_linha = {
            'valor_energisa_rs': energisa,
            'valor_beneficio_rs': beneficio,
            'valor_doado_banco_rs': doado,
            'sem_economia_rs': sem_economia,
            'com_economia_sem_cashback_rs': com_economia_sem_cashback,
            'com_economia_com_cashback_rs': com_economia_com_cashback,
            'economia_real_rs': economia_real,
        }
        for campo, valor in valores_linha.items():
            if valor is not None:
                totais[campo] += valor
                tem_valor[campo] = True

        linhas.append({
            'usuario_id': registro['usuario_id'],
            'nome': registro['nome'],
            **{campo: moeda(valor) for campo, valor in valores_linha.items()},
        })

    totais_formatados = {
        campo: moeda(valor) if tem_valor[campo] else 'Não informado'
        for campo, valor in totais.items()
    }
    return linhas, totais_formatados


# ─────────────────────────── ROTAS PÚBLICAS ───────────────────────────

@app.route('/')
def index():
    """Página pública de transparência do banco solar."""
    usuarios = load_csv('usuarios.csv')
    usinas = load_csv('usinas.csv')
    geracao = load_csv('geracao_mensal.csv')
    beneficios = load_csv('beneficios_mensais.csv')
    geracao_real = geracao[geracao['fonte'] == 'planilha'] if 'fonte' in geracao else geracao.iloc[0:0]
    meses_beneficios = set(beneficios['mes'].astype(str))
    meses_geracao = set(geracao_real['mes'].astype(str))
    meses_completos = sorted(meses_beneficios & meses_geracao)
    mes_referencia = meses_completos[-1] if meses_completos else None
    beneficios_referencia = beneficios[beneficios['mes'].astype(str) == mes_referencia] if mes_referencia else beneficios.iloc[0:0]
    geracao_referencia = geracao_real[geracao_real['mes'].astype(str) == mes_referencia] if mes_referencia else geracao_real.iloc[0:0]

    clientes = usuarios[usuarios['tipo'] == 'cliente']
    soma = lambda serie: float(serie.sum()) if not serie.empty and serie.notna().any() else 0.0
    economia_total_rs = calcular_economia_efetiva(beneficios_referencia)

    transparencia = {
        'familias_beneficiadas': len(load_csv('residencias.csv')),
        'economia_kw': round(soma(beneficios_referencia['energia_recebida_kwh']), 1),
        'economia_total_rs': round(float(economia_total_rs), 2) if pd.notna(economia_total_rs) else 0.0,
        'creditos': round(soma(beneficios_referencia['creditos_acumulados']), 1),
        'kw_recebidos': round(soma(beneficios_referencia['energia_recebida_kwh']), 1),
        'investido': round(soma(beneficios_referencia['valor_projeto_rs']), 2),
        'cashback_orquideas': round(soma(beneficios_referencia['cashback_rs']), 2),
        'geracao_total_kwh': round(soma(geracao_referencia['geracao_kwh']), 1),
        'co2_evitado_total': round(soma(geracao_referencia['co2_evitado_kg']), 1),
        'mes_referencia': mes_referencia,
        'num_usinas': len(usinas),
        'num_clientes': len(clientes),
    }

    # Dados para gráficos
    geracao_por_mes = geracao_real.groupby('mes').agg({
        'geracao_kwh': 'sum',
        'co2_evitado_kg': 'sum',
        'energia_beneficiarios_kwh': 'sum'
    }).reset_index().to_dict('records')

    geracao_por_usina = geracao_real.groupby('usina_id').agg({
        'geracao_kwh': 'sum'
    }).reset_index()
    nomes_usinas = usinas[['id', 'nome']].rename(columns={'id': 'usina_id'})
    geracao_por_usina = geracao_por_usina.merge(nomes_usinas, on='usina_id', how='left')
    geracao_por_usina['nome'] = geracao_por_usina.apply(
        lambda row: row['nome'] if pd.notna(row['nome']) and str(row['nome']).strip() else f"Usina ID {row['usina_id']}", axis=1
    )
    geracao_por_usina_dict = geracao_por_usina[['nome', 'geracao_kwh']].to_dict('records')

    beneficios_por_mes = []
    meses_disponiveis = sorted(set(geracao_real['mes'].astype(str)) | meses_beneficios)
    for mes in meses_disponiveis:
        b = beneficios[beneficios['mes'].astype(str) == mes]
        g = geracao_real[geracao_real['mes'].astype(str) == mes]
        economia_mes_rs = calcular_economia_efetiva(b)
        beneficios_por_mes.append({
            'mes': mes,
            'energia_rateio_kwh': soma(b['energia_recebida_kwh']),
            'economia_efetiva_rs': round(float(economia_mes_rs), 2) if pd.notna(economia_mes_rs) else None,
            'creditos_acumulados': soma(b['creditos_acumulados']),
            'energia_beneficiarios_kwh': soma(g['energia_beneficiarios_kwh']),
            'investido': soma(b['valor_projeto_rs']),
            'cashback': soma(b['cashback_rs']),
            'tem_beneficios': not b.empty,
        })

    # Localização das usinas para o mapa
    usinas_mapa = []
    for _, u in usinas.iterrows():
        localizacao = u.get('localizacao')
        lat, lng = COORDENADAS_CIDADES.get(localizacao, (None, None))
        usinas_mapa.append({
            'nome': u['nome'] if pd.notna(u['nome']) and str(u['nome']).strip() else f"Usina ID {u['id']}",
            'localizacao': localizacao if pd.notna(localizacao) else None,
            'status': u['status'] if pd.notna(u['status']) else None,
            'capacidade_kw': u['capacidade_kw'] if pd.notna(u['capacidade_kw']) else None,
            'lat': lat,
            'lng': lng,
        })

    return render_template('index.html',
                           transparencia=transparencia,
                           geracao_por_mes=geracao_por_mes,
                           beneficios_por_mes=beneficios_por_mes,
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
            session['user_id'] = str(user_data['id'])
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

    user = usuarios[usuarios['id'].astype(str) == str(session['user_id'])].iloc[0]
    residencia = residencias[residencias['usuario_id'].astype(str) == str(session['user_id'])]
    beneficios = load_csv('beneficios_mensais.csv')
    beneficios_cliente = beneficios[beneficios['usuario_id'].astype(str) == str(session['user_id'])].sort_values('mes')
    beneficio_atual = beneficios_cliente.iloc[-1] if not beneficios_cliente.empty else None

    valor_usuario = lambda campo: None if pd.isna(user[campo]) else user[campo]
    valor_beneficio = lambda campo: None if beneficio_atual is None or pd.isna(beneficio_atual[campo]) else float(beneficio_atual[campo])
    valor_beneficio_atual = valor_beneficio('valor_beneficio_rs')
    economia_real_atual = calcular_parcela_beneficio(valor_beneficio_atual, '0.75')
    valor_projeto_atual = calcular_parcela_beneficio(valor_beneficio_atual, '0.50')
    cashback_atual = calcular_parcela_beneficio(valor_beneficio_atual, '0.25')
    user_data = {
        'nome': user['nome'],
        'economia_real_rs': economia_real_atual,
        'creditos': valor_beneficio('creditos_acumulados'),
        'kw_recebidos': valor_beneficio('energia_recebida_kwh'),
        'investido': valor_projeto_atual,
        'cashback_orquideas': cashback_atual,
        'data_cadastro': valor_usuario('data_cadastro'),
    }

    residencia_data = None
    fatura = None
    if not residencia.empty:
        r = residencia.iloc[0]
        residencia_data = {
            'endereco': None if pd.isna(r['endereco']) else r['endereco'],
            'em_dia_banco': None if pd.isna(r['em_dia_banco']) else r['em_dia_banco'],
            'em_dia_concessionaria': None if pd.isna(r['em_dia_concessionaria']) else r['em_dia_concessionaria'],
            'cashback_em_dia': None if pd.isna(r['cashback_em_dia']) else r['cashback_em_dia'],
            'consumo_mensal_kwh': r['consumo_mensal_kwh'],
            'economia_mensal_rs': None if pd.isna(r['economia_mensal_rs']) else r['economia_mensal_rs'],
        }
        fatura = calcular_fatura(r)

    # Histórico de boletos da concessionária enviados pelo cliente
    boletos = load_csv('boletos.csv')
    boletos_cliente = boletos[boletos['usuario_id'].astype(str) == str(session['user_id'])]
    boletos_historico = boletos_cliente.sort_values('data_envio', ascending=False).to_dict('records')

    # Histórico mensal baseado somente nos registros importados.
    meses = beneficios_cliente['mes'].tolist()
    historico_coluna = lambda coluna: [None if pd.isna(v) else float(v) for v in beneficios_cliente[coluna].tolist()]
    historico_beneficio = historico_coluna('valor_beneficio_rs')
    historico = {
        'meses': meses,
        'economia': [calcular_parcela_beneficio(v, '0.75') for v in historico_beneficio],
        'creditos': historico_coluna('creditos_acumulados'),
        'kw_recebidos': historico_coluna('energia_recebida_kwh'),
        'investido': [calcular_parcela_beneficio(v, '0.50') for v in historico_beneficio],
        'cashback': [calcular_parcela_beneficio(v, '0.25') for v in historico_beneficio],
    }
    def somar_parcelas(valores, proporcao=None):
        valores = pd.to_numeric(valores, errors='coerce').dropna()
        if valores.empty:
            return None
        if proporcao is not None:
            total = sum(
                (Decimal(str(valor)) * Decimal(str(proporcao)) for valor in valores),
                Decimal('0'),
            )
            return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        return round(float(valores.sum()), 2)

    def metricas_cliente(registros):
        beneficios_periodo = pd.to_numeric(registros['valor_beneficio_rs'], errors='coerce')
        creditos_periodo = pd.to_numeric(registros['creditos_acumulados'], errors='coerce').dropna()
        energia_periodo = pd.to_numeric(registros['energia_recebida_kwh'], errors='coerce')
        return {
            'economia_real_rs': somar_parcelas(beneficios_periodo, '0.75'),
            'creditos': float(creditos_periodo.iloc[-1]) if not creditos_periodo.empty else None,
            'kw_recebidos': somar_parcelas(energia_periodo),
            'investido': somar_parcelas(beneficios_periodo, '0.50'),
            'cashback_orquideas': somar_parcelas(beneficios_periodo, '0.25'),
        }

    kpis_por_periodo = {'todos': metricas_cliente(beneficios_cliente)}
    for mes in meses:
        kpis_por_periodo[mes] = metricas_cliente(beneficios_cliente[beneficios_cliente['mes'].astype(str) == str(mes)])

    # Comparação com os demais beneficiários
    colunas_comparacao = {
        'economia_real_rs': 'valor_beneficio_rs',
        'creditos': 'creditos_acumulados',
        'kw_recebidos': 'energia_recebida_kwh',
        'cashback_orquideas': 'cashback_rs',
    }
    comparacao = {}
    mes_atual = beneficio_atual['mes'] if beneficio_atual is not None else None
    beneficios_mes = beneficios[beneficios['mes'] == mes_atual] if mes_atual is not None else beneficios.iloc[0:0]
    for chave, coluna in colunas_comparacao.items():
        if chave == 'economia_real_rs':
            valor = economia_real_atual
            valores_mes = pd.to_numeric(beneficios_mes['valor_beneficio_rs'], errors='coerce').dropna() * 0.75
        elif chave == 'cashback_orquideas':
            valor = cashback_atual
            valores_mes = (beneficios_mes['valor_beneficio_rs'].dropna() / 4)
        else:
            valor = valor_beneficio(coluna)
            valores_mes = beneficios_mes[coluna].dropna()
        if valor is None or valores_mes.empty:
            comparacao[chave] = None
            continue
        media = valores_mes.mean()
        escala = max(valor, media, 0.01) * 1.15
        comparacao[chave] = {
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
                           kpis_por_periodo=kpis_por_periodo,
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
    if MODO_DEMONSTRACAO:
        DADOS_DEMONSTRACAO['boletos.csv'] = boletos.copy()
    else:
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
    user = usuarios[usuarios['id'].astype(str) == str(session['user_id'])].iloc[0]
    residencia = residencias[residencias['usuario_id'].astype(str) == str(session['user_id'])]

    if residencia.empty:
        flash('Nenhuma residência associada à sua conta para gerar a fatura.', 'error')
        return redirect(url_for('cliente_dashboard'))

    r = residencia.iloc[0]
    fatura = calcular_fatura(r)
    if fatura is None:
        flash('O valor e o status desta fatura ainda não foram informados.', 'error')
        return redirect(url_for('cliente_dashboard'))

    conteudo = (
        'BANCO COMUNITÁRIO JARDIM BOTÂNICO\n'
        'Fatura Atual\n'
        '------------------------------------------\n'
        f"Beneficiário: {user['nome']}\n"
        f"UC de fornecimento: {r['endereco']}\n"
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
    if 'fonte' in geracao:
        geracao = geracao[geracao['fonte'] == 'planilha']
    residencias = load_csv('residencias.csv')
    usuarios = load_csv('usuarios.csv')
    beneficios = load_csv('beneficios_mensais.csv')

    # Dados das usinas
    usinas_data = usinas.to_dict('records')
    mes_producao_mais_recente = geracao['mes'].max() if not geracao.empty else None
    for u in usinas_data:
        producao = geracao[(geracao['usina_id'].astype(str) == str(u['id'])) & (geracao['mes'] == mes_producao_mais_recente)] if mes_producao_mais_recente else geracao.iloc[0:0]
        u['nome_exibicao'] = u['nome'] if pd.notna(u['nome']) and str(u['nome']).strip() else f"Usina ID {u['id']}"
        u['geracao_mensal_kwh'] = producao['geracao_kwh'].sum() if not producao.empty else None
        u['mes_geracao_label'] = f"{mes_producao_mais_recente[5:7]}/{mes_producao_mais_recente[:4]}" if mes_producao_mais_recente else None
        for campo in ('localizacao', 'capacidade_kw', 'status', 'eficiencia_percent'):
            if pd.isna(u.get(campo)):
                u[campo] = None

    # Dados unificados
    total_capacidade = usinas['capacidade_kw'].sum(min_count=1)
    total_capacidade = None if pd.isna(total_capacidade) else float(total_capacidade)
    total_geracao_mensal = geracao[geracao['mes'] == mes_producao_mais_recente]['geracao_kwh'].sum() if mes_producao_mais_recente else 0
    total_co2 = geracao['co2_evitado_kg'].sum()
    media_eficiencia_valor = usinas['eficiencia_percent'].mean()
    media_eficiencia = round(media_eficiencia_valor, 1) if pd.notna(media_eficiencia_valor) else None

    dados_unificados = {
        'total_capacidade': total_capacidade,
        'total_geracao_mensal': total_geracao_mensal,
        'total_co2': total_co2,
        'media_eficiencia': media_eficiencia,
        'num_usinas_ativas': int((usinas['status'] == 'ativa').sum()) if usinas['status'].notna().any() else None,
        'num_usinas_manutencao': int((usinas['status'] == 'manutencao').sum()) if usinas['status'].notna().any() else None,
    }

    # Residências beneficiárias
    residencias['usuario_id'] = residencias['usuario_id'].astype(str)
    usuarios['id'] = usuarios['id'].astype(str)
    res_com_usuarios = residencias.merge(
        usuarios[['id', 'nome']].rename(columns={'id': 'usuario_id'}),
        on='usuario_id'
    )
    residencias_data = res_com_usuarios.to_dict('records')

    # A cota pode ser calculada quando houver geração real e percentual cadastrado;
    # energia recebida só aparece nos meses com registro de consumo do beneficiário.
    meses_cotas = sorted(
        set(beneficios['mes'].dropna().astype(str)) |
        (set(geracao['mes'].dropna().astype(str)) if 'mes' in geracao else set())
    )
    geracao_cotas = geracao.groupby(geracao['mes'].astype(str))['geracao_kwh'].sum(min_count=1).to_dict() if not geracao.empty else {}
    historico_cotas = []
    residencias_dentro_cota = []
    for usuario_id, registros in beneficios.groupby(beneficios['usuario_id'].astype(str), sort=True):
        registros = registros.sort_values('mes').drop_duplicates('mes', keep='last').set_index('mes')
        nome = next((str(n).strip() for n in registros['nome'] if pd.notna(n) and str(n).strip()), f'Usuário {usuario_id}')
        cotas = []
        recebidas = []
        consumos_elegiveis = []
        meses_status = []
        percentual_atual = None
        for mes in meses_cotas:
            registro = registros.loc[mes] if mes in registros.index else None
            percentual_registro = pd.to_numeric(registro['percentual_cota'], errors='coerce') if registro is not None else None
            if percentual_registro is not None and pd.notna(percentual_registro):
                percentual_atual = float(percentual_registro)
            cota = pd.to_numeric(registro['cota_kwh'], errors='coerce') if registro is not None else None
            recebida = pd.to_numeric(registro['energia_recebida_kwh'], errors='coerce') if registro is not None else None
            consumo = pd.to_numeric(registro['consumo_total_kwh'], errors='coerce') if registro is not None else None
            excedente = pd.to_numeric(registro['excedeu_cota_kwh'], errors='coerce') if registro is not None and 'excedeu_cota_kwh' in registro.index else None
            tarifa_social = str(registro['tarifa_social']).strip().lower() if registro is not None and pd.notna(registro.get('tarifa_social')) else ''
            cota = float(cota) if cota is not None and pd.notna(cota) else None
            recebida = float(recebida) if recebida is not None and pd.notna(recebida) else None
            consumo = float(consumo) if consumo is not None and pd.notna(consumo) else None
            excedente = float(excedente) if excedente is not None and pd.notna(excedente) else None
            if consumo is not None and tarifa_social in ('sim', 's', 'true', '1'):
                consumo_elegivel = max(consumo - 80, 0)
            elif consumo is not None and tarifa_social in ('nao', 'não', 'n', 'false', '0'):
                consumo_elegivel = consumo
            else:
                consumo_elegivel = None
            if cota is None and percentual_atual is not None and pd.notna(geracao_cotas.get(mes)):
                cota = float(geracao_cotas[mes]) * percentual_atual / 100
            cotas.append(cota)
            recebidas.append(recebida)
            consumos_elegiveis.append(consumo_elegivel)
            dados_comparaveis = consumo_elegivel is not None and cota is not None
            excedeu = (consumo_elegivel > cota if dados_comparaveis else False) or (excedente is not None and excedente > 0)
            dentro = not excedeu if dados_comparaveis or (excedente is not None and excedente > 0) else None
            meses_status.append({
                'mes': mes,
                'mes_label': f'{mes[5:7]}/{mes[:4]}',
                'dentro_cota': dentro,
                'cota_kwh': cota,
                'energia_recebida_kwh': recebida,
                'consumo_elegivel_kwh': consumo_elegivel,
                'excedeu_cota_kwh': excedente,
            })

        validos = [item for item in meses_status if item['dentro_cota'] is not None]
        meses_dentro = sum(item['dentro_cota'] is True for item in validos)
        historico_cotas.append({
            'usuario_id': usuario_id,
            'nome': nome,
            'meses': [f'{mes[5:7]}/{mes[:4]}' for mes in meses_cotas],
            'cotas_kwh': cotas,
            'energia_recebida_kwh': recebidas,
            'consumo_elegivel_kwh': consumos_elegiveis,
        })
        if meses_dentro > 0:
            residencias_dentro_cota.append({
                'nome': nome,
                'meses_totais': len(validos),
                'meses_dentro_cota': meses_dentro,
                'historico_meses': meses_status,
            })

    for r in residencias_data:
        for campo in ('endereco', 'em_dia_banco', 'em_dia_concessionaria', 'cashback_em_dia', 'economia_mensal_rs'):
            if pd.isna(r.get(campo)):
                r[campo] = None

    # Estatísticas das residências
    total_residencias = len(residencias)
    em_dia_banco = len(residencias[residencias['em_dia_banco'] == 'sim'])
    em_dia_conc = len(residencias[residencias['em_dia_concessionaria'] == 'sim'])
    cashback_ok = len(residencias[residencias['cashback_em_dia'] == 'sim'])

    stats_residencias = {
        'total': total_residencias,
        'em_dia_banco': em_dia_banco,
        'em_dia_banco_pct': round(em_dia_banco / total_residencias * 100, 1),
        'em_dia_banco_nao_informado': int(residencias['em_dia_banco'].isna().sum()),
        'em_dia_concessionaria': em_dia_conc,
        'em_dia_concessionaria_pct': round(em_dia_conc / total_residencias * 100, 1),
        'em_dia_concessionaria_nao_informado': int(residencias['em_dia_concessionaria'].isna().sum()),
        'cashback_em_dia': cashback_ok,
        'cashback_em_dia_pct': round(cashback_ok / total_residencias * 100, 1),
        'cashback_nao_informado': int(residencias['cashback_em_dia'].isna().sum()),
    }

    # Indicadores mensais dos beneficiários para filtros de projeto e referência.
    beneficios_por_mes_cards = {}
    for mes in sorted(beneficios['mes'].dropna().astype(str).unique()):
        registros_mes = beneficios[beneficios['mes'].astype(str) == mes]
        beneficio_mes = pd.to_numeric(registros_mes['valor_beneficio_rs'], errors='coerce').dropna()
        energia_mes = pd.to_numeric(registros_mes['energia_recebida_kwh'], errors='coerce').dropna()
        beneficios_por_mes_cards[mes] = {
            'beneficiarios': int(len(registros_mes)),
            'energia_kwh': float(energia_mes.sum()) if not energia_mes.empty else None,
            'economia_real_rs': float(beneficio_mes.sum() * 0.75) if not beneficio_mes.empty else None,
            'doado_banco_rs': float(beneficio_mes.sum() * 0.50) if not beneficio_mes.empty else None,
            'cashback_rs': float(beneficio_mes.sum() * 0.25) if not beneficio_mes.empty else None,
        }
    todos_beneficios = pd.to_numeric(beneficios['valor_beneficio_rs'], errors='coerce').dropna()
    toda_energia = pd.to_numeric(beneficios['energia_recebida_kwh'], errors='coerce').dropna()
    beneficios_por_mes_cards['todos'] = {
        'beneficiarios': int(beneficios['usuario_id'].nunique()),
        'energia_kwh': float(toda_energia.sum()) if not toda_energia.empty else None,
        'economia_real_rs': float(todos_beneficios.sum() * 0.75) if not todos_beneficios.empty else None,
        'doado_banco_rs': float(todos_beneficios.sum() * 0.50) if not todos_beneficios.empty else None,
        'cashback_rs': float(todos_beneficios.sum() * 0.25) if not todos_beneficios.empty else None,
    }
    historico_residencias = {}
    for _, registro in beneficios.iterrows():
        beneficio = pd.to_numeric(registro.get('valor_beneficio_rs'), errors='coerce')
        consumo = pd.to_numeric(registro.get('consumo_total_kwh'), errors='coerce')
        historico_residencias.setdefault(str(registro['usuario_id']), {})[str(registro['mes'])] = {
            'consumo_kwh': float(consumo) if pd.notna(consumo) else None,
            'economia_rs': float(beneficio * 0.75) if pd.notna(beneficio) else None,
        }
    projetos_beneficiarios = [{'id': 'todos', 'nome': 'Todos os projetos'}]
    if len(usinas_data) == 1:
        projetos_beneficiarios.append({'id': str(usinas_data[0]['id']), 'nome': usinas_data[0]['nome_exibicao']})

    demonstrativo_economia = []
    totais_economia = []
    meses_economia = []
    for mes in sorted(beneficios['mes'].astype(str).unique()):
        beneficios_mes = beneficios[beneficios['mes'].astype(str) == mes]
        linhas_mes, totais_mes = montar_demonstrativo_economia(beneficios_mes)
        mes_label = f"{mes[5:7]}/{mes[:4]}"
        meses_economia.append({'valor': mes, 'label': mes_label})
        demonstrativo_economia.extend({**linha, 'mes': mes} for linha in linhas_mes)
        totais_economia.append({'mes': mes, 'mes_label': mes_label, **totais_mes})

    _, totais_todas = montar_demonstrativo_economia(beneficios)
    demonstrativo_economia_todos = demonstrativo_economia.copy()

    # Geração mensal por usina (para gráficos)
    geracao_por_mes = geracao.groupby('mes').agg({
        'geracao_kwh': 'sum',
        'co2_evitado_kg': 'sum',
        'receita_rs': lambda valores: valores.sum(min_count=1)
    }).reset_index().to_dict('records')

    # Doação mensal ao banco: metade do benefício calculado, somada sem
    # arredondar cada beneficiário antes do total do mês.
    doacoes_banco_por_mes = {}
    for mes in beneficios['mes'].dropna().astype(str).unique():
        valores_beneficio = pd.to_numeric(
            beneficios.loc[beneficios['mes'].astype(str) == mes, 'valor_beneficio_rs'],
            errors='coerce'
        ).dropna()
        total_doado = sum(
            (Decimal(str(valor)) / Decimal('2') for valor in valores_beneficio),
            Decimal('0')
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        doacoes_banco_por_mes[mes] = float(total_doado)

    # Geração individual por usina e mês
    geracao_individual = {}
    for _, usina in usinas.iterrows():
        usina_geracao = geracao[geracao['usina_id'].astype(str) == str(usina['id'])].sort_values('mes')
        nome_usina = usina['nome'] if pd.notna(usina['nome']) and str(usina['nome']).strip() else f"Usina ID {usina['id']}"
        geracao_individual[nome_usina] = {
            'meses': usina_geracao['mes'].tolist(),
            'geracao': usina_geracao['geracao_kwh'].tolist(),
            'co2': usina_geracao['co2_evitado_kg'].tolist(),
            'receita': usina_geracao['receita_rs'].tolist(),
            # A planilha de beneficiários não informa usina_id. Com a única
            # usina cadastrada, o total doado pode ser associado a este gráfico.
            'doado_banco': [
                doacoes_banco_por_mes.get(str(mes)) if len(usinas) == 1 else None
                for mes in usina_geracao['mes']
            ],
        }

    return render_template('admin.html',
                           usinas=usinas_data,
                           dados_unificados=dados_unificados,
                           residencias=residencias_data,
                           residencias_dentro_cota=residencias_dentro_cota,
                           stats_residencias=stats_residencias,
                           historico_cotas=historico_cotas,
                           demonstrativo_economia=demonstrativo_economia,
                           demonstrativo_economia_todos=demonstrativo_economia_todos,
                           totais_economia_todos=totais_todas,
                           totais_economia=totais_economia,
                           meses_economia=meses_economia,
                           beneficios_por_mes_cards=beneficios_por_mes_cards,
                           historico_residencias=historico_residencias,
                           projetos_beneficiarios=projetos_beneficiarios,
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
    residencias = load_csv('residencias.csv')

    if residencia_id not in residencias['id'].values:
        return jsonify({'success': False, 'error': 'residência não encontrada'}), 404

    for campo, valor in atualizacoes.items():
        residencias.loc[residencias['id'] == residencia_id, campo] = valor
    residencias.loc[residencias['id'] == residencia_id, 'ultima_atualizacao'] = datetime.date.today().isoformat()

    if MODO_DEMONSTRACAO:
        DADOS_DEMONSTRACAO['residencias.csv'] = residencias.copy()
    else:
        residencias.to_csv(residencias_path, index=False, float_format='%.2f')

    return jsonify({'success': True})


# ─────────────────────────── API ENDPOINTS ───────────────────────────

@app.route('/api/transparencia')
def api_transparencia():
    geracao = load_csv('geracao_mensal.csv')
    beneficios = load_csv('beneficios_mensais.csv')
    geracao = geracao[geracao['fonte'] == 'planilha'] if 'fonte' in geracao else geracao.iloc[0:0]
    meses = sorted(set(beneficios['mes'].astype(str)) & set(geracao['mes'].astype(str)))
    mes = meses[-1] if meses else None
    b = beneficios[beneficios['mes'].astype(str) == mes] if mes else beneficios.iloc[0:0]
    g = geracao[geracao['mes'].astype(str) == mes] if mes else geracao.iloc[0:0]
    soma = lambda serie: float(serie.sum()) if not serie.empty and serie.notna().any() else 0.0
    economia_total_rs = calcular_economia_efetiva(b)
    return jsonify({
        'economia_kw': round(soma(b['energia_recebida_kwh']), 1),
        'economia_total_rs': round(float(economia_total_rs), 2) if pd.notna(economia_total_rs) else 0.0,
        'creditos': round(soma(b['creditos_acumulados']), 1),
        'kw_recebidos': round(soma(b['energia_recebida_kwh']), 1),
        'investido': round(soma(b['valor_projeto_rs']), 2),
        'cashback_orquideas': round(soma(b['cashback_rs']), 2),
        'geracao_total_kwh': round(soma(g['geracao_kwh']), 1),
        'co2_evitado_total': round(soma(g['co2_evitado_kg']), 1),
        'mes_referencia': mes,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
