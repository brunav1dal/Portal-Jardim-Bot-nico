"""Objetivo: Lê e grava tabelas CSV e mantém alterações em memória no modo demonstrativo."""
# Dependências usadas por este módulo.
import os
import pandas as pd
from banco_solar.config import DATA_DIR
from banco_solar.demo import demo_data

# Ativa dados demonstrativos quando a tabela mensal de benefícios não existe.
MODO_DEMONSTRACAO = not (DATA_DIR / 'beneficios_mensais.csv').exists()
DADOS_DEMONSTRACAO = demo_data() if MODO_DEMONSTRACAO else None


def load_csv(filename):
    """Carrega um arquivo CSV do diretório de dados."""
    filepath = os.path.join(DATA_DIR, filename)
    # Usa cópias em memória na demonstração; o login continua consultando usuarios.csv.
    if MODO_DEMONSTRACAO and filename in DADOS_DEMONSTRACAO and filename != 'usuarios.csv':
        return DADOS_DEMONSTRACAO[filename].copy()
    dados = pd.read_csv(filepath)
    # Compatibiliza planilhas antigas que ainda não possuem a coluna de energia distribuída.
    if filename == 'geracao_mensal.csv':
        for coluna in ('energia_beneficiarios_kwh',):
            if coluna not in dados:
                dados[coluna] = float('nan')
    return dados

def save_csv(filename, dados, **options):
    """Persiste uma tabela, ou atualiza sua cópia de demonstração."""
    # Mantém a demonstração em memória; na operação normal grava o CSV em disco.
    if MODO_DEMONSTRACAO:
        DADOS_DEMONSTRACAO[filename] = dados.copy()
    else:
        dados.to_csv(DATA_DIR / filename, index=False, **options)
