"""Objetivo: Armazena o boleto recebido e registra os dados do envio no histórico operacional."""
# Dependências usadas por este módulo.
import datetime
import os
import pandas as pd
from werkzeug.utils import secure_filename
from banco_solar.config import BOLETOS_DIR
from banco_solar.repositories import dados_csv


def registrar_boleto(user_id, arquivo):
    """Salva um arquivo já validado pela rota e registra o envio."""
    # Separa os documentos por usuário e cria a pasta de destino quando necessário.
    pasta_usuario = os.path.join(BOLETOS_DIR, str(user_id))
    os.makedirs(pasta_usuario, exist_ok=True)

    # Combina data/hora e nome sanitizado para gravar o arquivo recebido.
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    nome_seguro = secure_filename(arquivo.filename)
    arquivo.save(os.path.join(pasta_usuario, f'{timestamp}_{nome_seguro}'))

    # Lê o histórico para atribuir um identificador ao novo envio.
    boletos = dados_csv.load_csv('boletos.csv')
    novo_id = int(boletos['id'].max()) + 1 if not boletos.empty else 1
    # Registra nome original, beneficiário, data e status inicial do documento.
    novo_boleto = pd.DataFrame([{
        'id': novo_id,
        'usuario_id': user_id,
        'nome_arquivo': arquivo.filename,
        'data_envio': datetime.date.today().isoformat(),
        'status': 'Enviado',
    }])
    boletos = pd.concat([boletos, novo_boleto], ignore_index=True)
    # Persiste o histórico pelo mesmo repositório utilizado pelas outras tabelas.
    dados_csv.save_csv('boletos.csv', boletos)
