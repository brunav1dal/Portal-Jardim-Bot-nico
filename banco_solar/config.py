"""Objetivo: Centraliza caminhos, limites de upload, tarifa e configurações de ambiente."""
# Dependências usadas por este módulo.
import os
from pathlib import Path

# Resolve os caminhos a partir do arquivo, sem depender da pasta aberta no terminal.
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / 'data'
BOLETOS_DIR = ROOT_DIR / 'static' / 'uploads' / 'boletos'
# Reúne os formatos de boleto aceitos e a tarifa usada no cálculo da fatura.
EXTENSOES_PERMITIDAS = {'pdf', 'png', 'jpg', 'jpeg'}
TARIFA_SOLAR_CLIENTE = 0.30
# Relaciona o endereço cadastrado às coordenadas usadas pelo mapa público.
COORDENADAS_CIDADES = {
    'R. Arquivista Jonathas Carécas, 74 - Castelo Branco, João Pessoa - PB, 58057-034': (-7.1342, -34.8550),
}

# Lê variáveis do ambiente e fornece os padrões de configuração do Flask.
class Config:
    """Fornece os padrões carregados pela fábrica da aplicação Flask."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'banco-solar-secret-key-2026')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    NEWS_STORAGE_DIR = os.environ.get('NEWS_STORAGE_DIR', str(ROOT_DIR / 'runtime' / 'noticias'))
