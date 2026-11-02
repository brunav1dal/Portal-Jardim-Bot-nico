"""Objetivo: Calcula parcelas monetárias, economia e demonstrativos com arredondamento decimal."""
# Dependências usadas por este módulo.
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd


def calcular_economia_efetiva(beneficios):
    """Calcula a economia líquida como 75% do valor individual do benefício."""
    # Diferencia ausência de registros de uma economia efetivamente igual a zero.
    if beneficios.empty:
        return None
    # Usa Decimal e arredonda após a soma para evitar diferenças monetárias acumuladas.
    total = sum(
        (Decimal(str(valor)) * Decimal('0.75') for valor in pd.to_numeric(beneficios['valor_beneficio_rs'], errors='coerce').dropna()),
        Decimal('0'),
    )
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_parcela_beneficio(valor, proporcao):
    """Calcula uma parcela monetária do benefício, arredondada a centavos."""
    # Preserva valores não informados em vez de convertê-los artificialmente em zero.
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
    # Acumula cada coluna monetária e acompanha quais totais possuem valores válidos.
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
        """Converte um valor informado para Decimal e preserva a ausência de informação."""
        return None if pd.isna(valor) else Decimal(str(valor))

    def moeda(valor):
        """Formata centavos com vírgula e identifica valores que não foram informados."""
        if valor is None:
            return 'Não informado'
        return f"{valor.quantize(centavo, rounding=ROUND_HALF_UP):.2f}".replace('.', ',')

    # Calcula os cenários de pagamento e economia para cada beneficiário do mês.
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
        # Soma apenas campos informados; lacunas permanecem identificáveis no demonstrativo.
        for campo, valor in valores_linha.items():
            if valor is not None:
                totais[campo] += valor
                tem_valor[campo] = True

        linhas.append({
            'usuario_id': registro['usuario_id'],
            'nome': registro['nome'],
            **{campo: moeda(valor) for campo, valor in valores_linha.items()},
        })

    # Formata linhas e totais para exibição, preservando a indicação de dados ausentes.
    totais_formatados = {
        campo: moeda(valor) if tem_valor[campo] else 'Não informado'
        for campo, valor in totais.items()
    }
    return linhas, totais_formatados
