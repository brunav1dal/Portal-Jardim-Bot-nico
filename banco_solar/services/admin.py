"""Objetivo: Consolida indicadores de gestão, cotas e demonstrativos e atualiza residências."""
# Dependências usadas por este módulo.
import datetime
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from banco_solar.repositories import dados_csv
from banco_solar.services.beneficios import montar_demonstrativo_economia

def montar_painel_admin():
    """Consolida os dados usados na tela."""
    # Carrega as tabelas operacionais e restringe a geração aos registros importados.
    usinas = dados_csv.load_csv('usinas.csv')
    geracao = dados_csv.load_csv('geracao_mensal.csv')
    if 'fonte' in geracao:
        geracao = geracao[geracao['fonte'] == 'planilha']
    # Lê as residências para consolidar o painel ou aplicar a alteração solicitada.
    residencias = dados_csv.load_csv('residencias.csv')
    usuarios = dados_csv.load_csv('usuarios.csv')
    beneficios = dados_csv.load_csv('beneficios_mensais.csv')

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
    # Prepara o histórico de cota e os beneficiários que permaneceram dentro do limite.
    historico_cotas = []
    residencias_dentro_cota = []
    # Agrupa os meses por beneficiário para comparar energia recebida, consumo e cota.
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

    # Completa os registros exibidos na tabela com seus indicadores de cota.
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
    # Calcula o resumo acumulado dos beneficiários, além das visões mensais.
    todos_beneficios = pd.to_numeric(beneficios['valor_beneficio_rs'], errors='coerce').dropna()
    toda_energia = pd.to_numeric(beneficios['energia_recebida_kwh'], errors='coerce').dropna()
    beneficios_por_mes_cards['todos'] = {
        'beneficiarios': int(beneficios['usuario_id'].nunique()),
        'energia_kwh': float(toda_energia.sum()) if not toda_energia.empty else None,
        'economia_real_rs': float(todos_beneficios.sum() * 0.75) if not todos_beneficios.empty else None,
        'doado_banco_rs': float(todos_beneficios.sum() * 0.50) if not todos_beneficios.empty else None,
        'cashback_rs': float(todos_beneficios.sum() * 0.25) if not todos_beneficios.empty else None,
    }
    # Indexa o histórico por residência/usuário para os filtros do painel.
    historico_residencias = {}
    for _, registro in beneficios.iterrows():
        beneficio = pd.to_numeric(registro.get('valor_beneficio_rs'), errors='coerce')
        consumo = pd.to_numeric(registro.get('consumo_total_kwh'), errors='coerce')
        historico_residencias.setdefault(str(registro['usuario_id']), {})[str(registro['mes'])] = {
            'consumo_kwh': float(consumo) if pd.notna(consumo) else None,
            'economia_rs': float(beneficio * 0.75) if pd.notna(beneficio) else None,
        }
    # Prepara as opções de projeto disponíveis no filtro de beneficiários.
    projetos_beneficiarios = [{'id': 'todos', 'nome': 'Todos os projetos'}]
    if len(usinas_data) == 1:
        projetos_beneficiarios.append({'id': str(usinas_data[0]['id']), 'nome': usinas_data[0]['nome_exibicao']})

    # Monta as linhas e os totais monetários do demonstrativo de cada mês.
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

    # Entrega os dados para os cartões, tabelas, filtros e gráficos administrativos.
    return {
        'usinas': usinas_data,
        'dados_unificados': dados_unificados,
        'residencias': residencias_data,
        'residencias_dentro_cota': residencias_dentro_cota,
        'stats_residencias': stats_residencias,
        'historico_cotas': historico_cotas,
        'demonstrativo_economia': demonstrativo_economia,
        'demonstrativo_economia_todos': demonstrativo_economia_todos,
        'totais_economia_todos': totais_todas,
        'totais_economia': totais_economia,
        'meses_economia': meses_economia,
        'beneficios_por_mes_cards': beneficios_por_mes_cards,
        'historico_residencias': historico_residencias,
        'projetos_beneficiarios': projetos_beneficiarios,
        'geracao_por_mes': geracao_por_mes,
        'geracao_individual': geracao_individual
    }


def atualizar_status_residencia(residencia_id, atualizacoes):
    """Atualiza os campos já validados e informa se a residência existe."""
    # Lê as residências para consolidar o painel ou aplicar a alteração solicitada.
    residencias = dados_csv.load_csv('residencias.csv')

    # Interrompe a atualização quando o identificador não corresponde a uma residência.
    if residencia_id not in residencias['id'].values:
        return False

    # Altera somente os status já validados pela rota e registra a data da atualização.
    for campo, valor in atualizacoes.items():
        residencias.loc[residencias['id'] == residencia_id, campo] = valor
    residencias.loc[residencias['id'] == residencia_id, 'ultima_atualizacao'] = datetime.date.today().isoformat()

    dados_csv.save_csv('residencias.csv', residencias, float_format='%.2f')

    return True
