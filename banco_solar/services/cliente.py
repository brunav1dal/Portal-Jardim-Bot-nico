"""Objetivo: Prepara os benefícios, a fatura, o histórico e as comparações de um beneficiário."""
# Dependências usadas por este módulo.
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from banco_solar.repositories import dados_csv
from banco_solar.services.beneficios import calcular_parcela_beneficio
from banco_solar.services.faturamento import calcular_fatura

def montar_painel_cliente(usuario_id):
    """Consolida os dados usados na tela."""
    # Carrega as tabelas necessárias para montar a visão individual do beneficiário.
    usuarios = dados_csv.load_csv('usuarios.csv')
    residencias = dados_csv.load_csv('residencias.csv')

    # Filtra todos os dados pelo usuário recebido e seleciona o benefício mais recente.
    user = usuarios[usuarios['id'].astype(str) == str(usuario_id)].iloc[0]
    residencia = residencias[residencias['usuario_id'].astype(str) == str(usuario_id)]
    beneficios = dados_csv.load_csv('beneficios_mensais.csv')
    beneficios_cliente = beneficios[beneficios['usuario_id'].astype(str) == str(usuario_id)].sort_values('mes')
    beneficio_atual = beneficios_cliente.iloc[-1] if not beneficios_cliente.empty else None

    # Converte campos ausentes para None, permitindo exibir Não informado na tela.
    valor_usuario = lambda campo: None if pd.isna(user[campo]) else user[campo]
    valor_beneficio = lambda campo: None if beneficio_atual is None or pd.isna(beneficio_atual[campo]) else float(beneficio_atual[campo])
    # Deriva as parcelas de economia, projeto e cashback a partir do benefício atual.
    valor_beneficio_atual = valor_beneficio('valor_beneficio_rs')
    economia_real_atual = calcular_parcela_beneficio(valor_beneficio_atual, '0.75')
    valor_projeto_atual = calcular_parcela_beneficio(valor_beneficio_atual, '0.50')
    cashback_atual = calcular_parcela_beneficio(valor_beneficio_atual, '0.25')
    # Organiza o contrato de dados usado pelos cartões do template.
    user_data = {
        'nome': user['nome'],
        'economia_real_rs': economia_real_atual,
        'creditos': valor_beneficio('creditos_acumulados'),
        'kw_recebidos': valor_beneficio('energia_recebida_kwh'),
        'investido': valor_projeto_atual,
        'cashback_orquideas': cashback_atual,
        'data_cadastro': valor_usuario('data_cadastro'),
    }

    # Prepara os dados da unidade e calcula a fatura quando há residência cadastrada.
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
    boletos = dados_csv.load_csv('boletos.csv')
    boletos_cliente = boletos[boletos['usuario_id'].astype(str) == str(usuario_id)]
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
        """Soma valores válidos e aplica a proporção antes do arredondamento final."""
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
        """Monta os indicadores de um período, usando o último saldo de créditos disponível."""
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

    # Calcula uma visão acumulada e uma visão para cada mês disponível no seletor.
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
        # Evita comparações sem base e escalas inválidas quando faltam valores.
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

    # Retorna somente dados; a rota é responsável por renderizar a página HTML.
    return {
        'user': user_data,
        'residencia': residencia_data,
        'fatura': fatura,
        'historico': historico,
        'kpis_por_periodo': kpis_por_periodo,
        'comparacao': comparacao,
        'boletos_historico': boletos_historico
    }
