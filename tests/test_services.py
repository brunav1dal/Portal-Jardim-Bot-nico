"""Objetivo: Verifica percentuais, arredondamento monetário e cálculo da fatura."""
# Dependências usadas por este módulo.
from decimal import Decimal
from pathlib import Path
import sys
import unittest
import pandas as pd

# Permite executar os testes a partir da raiz ou diretamente pelo arquivo.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from banco_solar.services.beneficios import calcular_economia_efetiva, calcular_parcela_beneficio
from banco_solar.services.faturamento import calcular_fatura


class FinancialRulesTests(unittest.TestCase):
    """Verifica percentuais, arredondamento monetário e cálculo da fatura."""
    def test_benefit_shares_round_half_up_and_keep_missing_values(self):
        """Confere o arredondamento das parcelas e a preservação dos valores não informados."""
        self.assertEqual(calcular_parcela_beneficio('10.02', '0.25'), 2.51)
        self.assertEqual(calcular_parcela_beneficio(100, '0.75'), 75)
        self.assertIsNone(calcular_parcela_beneficio(None, '0.75'))
        self.assertIsNone(calcular_parcela_beneficio(float('nan'), '0.75'))

    def test_total_economy_rounds_after_summing(self):
        """Confere que a economia total é arredondada depois da soma das parcelas."""
        values = pd.DataFrame({'valor_beneficio_rs': ['10.01', '10.01', None]})
        self.assertEqual(calcular_economia_efetiva(values), Decimal('15.02'))
        self.assertIsNone(calcular_economia_efetiva(values.iloc[:0]))

    def test_invoice_uses_solar_tariff_and_payment_status(self):
        """Confere tarifa, situação de pagamento e dados insuficientes na fatura."""
        self.assertEqual(calcular_fatura({'consumo_mensal_kwh': 100, 'em_dia_banco': 'sim'}),
                         {'valor': 30.0, 'status': 'Paga'})
        self.assertEqual(calcular_fatura({'consumo_mensal_kwh': 100, 'em_dia_banco': 'nao'})['status'],
                         'Em Aberto')
        self.assertIsNone(calcular_fatura({'consumo_mensal_kwh': None, 'em_dia_banco': 'sim'}))
