"""Objetivo: Inicia o servidor local e expõe a aplicação Flask para a hospedagem."""
# Dependências usadas por este módulo.
from banco_solar import create_app

app = create_app()

# Executa este arquivo diretamente; importações não iniciam este bloco.
if __name__ == '__main__':
    app.run(debug=True, port=5000)
