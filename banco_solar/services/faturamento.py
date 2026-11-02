"""Objetivo: Calcula o valor e o status da fatura e monta o documento textual para download."""
# Dependências usadas por este módulo.
import pandas as pd
from banco_solar.config import TARIFA_SOLAR_CLIENTE


def calcular_fatura(residencia_row):
    """Calcula o valor e o status da fatura atual do cliente junto ao banco."""
    # Sem consumo ou situação de pagamento, não há dados suficientes para emitir a fatura.
    if pd.isna(residencia_row.get('em_dia_banco')) or pd.isna(residencia_row.get('consumo_mensal_kwh')):
        return None
    # Aplica a tarifa solar ao consumo e traduz o status cadastral para a fatura.
    valor = round(float(residencia_row['consumo_mensal_kwh']) * TARIFA_SOLAR_CLIENTE, 2)
    status = 'Paga' if residencia_row['em_dia_banco'] == 'sim' else 'Em Aberto'
    return {'valor': valor, 'status': status}


def montar_fatura_texto(user, r, fatura):
    """Formata o documento textual da fatura atual."""
    # Monta o comprovante textual com identificação, consumo, valor e situação do pagamento.
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

    return conteudo
