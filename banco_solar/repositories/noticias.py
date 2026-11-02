"""Objetivo: Lista, inclui, edita e exclui publicações em transações no banco SQLite."""
# Dependências usadas por este módulo.
from contextlib import closing
import json
import sqlite3
from pathlib import Path


def listar(storage):
    """Retorna as publicações mais recentes; instalação nova começa vazia."""
    db = Path(storage) / 'noticias.sqlite3'
    # Uma instalação sem banco é tratada como lista vazia ou registro inexistente.
    if not db.exists():
        return []
    # Fecha a conexão ao sair do bloco; as gravações usam transação com commit ou rollback.
    with closing(sqlite3.connect(db)) as connection:
        rows = connection.execute(
            'SELECT payload FROM news ORDER BY created_at DESC, id DESC'
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


def excluir(storage, article_id):
    """Exclui pelo identificador e informa se o registro existia."""
    db = Path(storage) / 'noticias.sqlite3'
    # Uma instalação sem banco é tratada como lista vazia ou registro inexistente.
    if not db.exists():
        return False
    # Fecha a conexão ao sair do bloco; as gravações usam transação com commit ou rollback.
    with closing(sqlite3.connect(db)) as connection:
        with connection:
            return bool(connection.execute(
                'DELETE FROM news WHERE id = ?', (article_id,)
            ).rowcount)


def salvar(storage, article, *, atualizar=False):
    """Grava a publicação em transação; edição não recria notícia excluída."""
    # Fecha a conexão ao sair do bloco; as gravações usam transação com commit ou rollback.
    with closing(sqlite3.connect(Path(storage) / 'noticias.sqlite3')) as connection:
        with connection:
            connection.execute(
                'CREATE TABLE IF NOT EXISTS news '
                '(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)'
            )
            payload = json.dumps(article, ensure_ascii=False)
            # Uma edição só altera o registro existente; não recria uma notícia removida.
            if atualizar:
                changed = connection.execute(
                    'UPDATE news SET payload = ? WHERE id = ?',
                    (payload, article['id']),
                ).rowcount
                if not changed:
                    raise LookupError('Article no longer exists')
            else:
                connection.execute('INSERT INTO news VALUES (?, ?, ?)',
                                   (article['id'], article['created_at'], payload))
