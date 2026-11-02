"""Objetivo: Verifica se a extensão de um boleto está entre os formatos aceitos pelo sistema."""
# Dependências usadas por este módulo.
from banco_solar.config import EXTENSOES_PERMITIDAS


def arquivo_permitido(nome_arquivo):
    """Verifica se a extensão do arquivo enviado é aceita."""
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS
