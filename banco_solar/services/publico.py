"""Objetivo: Consolida geração, benefícios e localização das usinas para o portal e a API pública."""
# Dependências usadas por este módulo.
import pandas as pd
from banco_solar.repositories import dados_csv
from banco_solar.config import COORDENADAS_CIDADES
from banco_solar.services.beneficios import calcular_economia_efetiva

def montar_pagina_publica():
    """Consolida os dados usados na tela."""
    # Carrega as bases de usuários, usinas, geração e benefícios do portal.
    usuarios = dados_csv.load_csv('usuarios.csv')
    usinas = dados_csv.load_csv('usinas.csv')
    # Carrega as tabelas usadas na resposta JSON de transparência.
    geracao = dados_csv.load_csv('geracao_mensal.csv')
    beneficios = dados_csv.load_csv('beneficios_mensais.csv')
    # Usa geração importada e encontra o último mês presente também nos benefícios.
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

    # Monta os indicadores consolidados que os cartões públicos vão apresentar.
    transparencia = {
        'familias_beneficiadas': len(dados_csv.load_csv('residencias.csv')),
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

    # Prepara séries por mês para o filtro de período aplicado no navegador.
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

    # Entrega o contrato de dados consumido pelo template ou pela resposta JSON.
    return {
        'transparencia': transparencia,
        'geracao_por_mes': geracao_por_mes,
        'beneficios_por_mes': beneficios_por_mes,
        'geracao_por_usina': geracao_por_usina_dict,
        'usinas_mapa': usinas_mapa
    }


def montar_transparencia():
    """Retorna indicadores do último mês com geração e benefícios disponíveis."""
    # Carrega as tabelas usadas na resposta JSON de transparência.
    geracao = dados_csv.load_csv('geracao_mensal.csv')
    beneficios = dados_csv.load_csv('beneficios_mensais.csv')
    geracao = geracao[geracao['fonte'] == 'planilha'] if 'fonte' in geracao else geracao.iloc[0:0]
    # Seleciona o mês comum mais recente para manter os indicadores comparáveis.
    meses = sorted(set(beneficios['mes'].astype(str)) & set(geracao['mes'].astype(str)))
    mes = meses[-1] if meses else None
    b = beneficios[beneficios['mes'].astype(str) == mes] if mes else beneficios.iloc[0:0]
    g = geracao[geracao['mes'].astype(str) == mes] if mes else geracao.iloc[0:0]
    soma = lambda serie: float(serie.sum()) if not serie.empty and serie.notna().any() else 0.0
    economia_total_rs = calcular_economia_efetiva(b)
    # Entrega o contrato de dados consumido pelo template ou pela resposta JSON.
    return {
        'economia_kw': round(soma(b['energia_recebida_kwh']), 1),
        'economia_total_rs': round(float(economia_total_rs), 2) if pd.notna(economia_total_rs) else 0.0,
        'creditos': round(soma(b['creditos_acumulados']), 1),
        'kw_recebidos': round(soma(b['energia_recebida_kwh']), 1),
        'investido': round(soma(b['valor_projeto_rs']), 2),
        'cashback_orquideas': round(soma(b['cashback_rs']), 2),
        'geracao_total_kwh': round(soma(g['geracao_kwh']), 1),
        'co2_evitado_total': round(soma(g['co2_evitado_kg']), 1),
        'mes_referencia': mes,
    }
