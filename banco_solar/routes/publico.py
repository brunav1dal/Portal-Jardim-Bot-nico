"""Objetivo: Entrega a página pública e a API JSON dos indicadores de transparência."""
# Dependências usadas por este módulo.
from flask import render_template, jsonify
from banco_solar.services.publico import montar_pagina_publica, montar_transparencia


def index():
    """Entrega a página após validar o acesso."""
    return render_template('public/index.html', **montar_pagina_publica())


def api_transparencia():
    """Indicadores públicos em JSON."""
    return jsonify(montar_transparencia())


# Relaciona as URLs públicas às funções sem alterar os nomes usados em url_for.
def register_routes(app):
    """Registra as URLs desta área na aplicação."""
    app.add_url_rule('/', endpoint='index', view_func=index, methods=['GET'])
    app.add_url_rule('/api/transparencia', endpoint='api_transparencia', view_func=api_transparencia, methods=['GET'])
