"""Objetivo: Cria a aplicação Flask, carrega configurações e conecta os módulos de rotas."""
# Dependências usadas por este módulo.
from flask import Flask
from banco_solar.config import Config, ROOT_DIR
from banco_solar.repositories import dados_csv


def create_app(config=None):
    """Cria uma aplicação; aceita configurações específicas para testes."""
    # Aponta explicitamente para os templates e recursos públicos da raiz.
    app = Flask(__name__, template_folder=str(ROOT_DIR / 'templates'),
                static_folder=str(ROOT_DIR / 'static'))
    # Carrega os padrões e permite substituições específicas para testes ou execução.
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    @app.context_processor
    def contexto_demonstracao():
        """Informa aos templates se os dados operacionais estão em modo de demonstração."""
        return {'modo_demonstracao': dados_csv.MODO_DEMONSTRACAO}

    # Conecta as áreas ao servidor depois de criar a instância Flask.
    from banco_solar.routes import publico, auth, cliente, admin, noticias
    for module in (publico, auth, cliente, admin):
        module.register_routes(app)
    noticias.init_news(app)
    return app
