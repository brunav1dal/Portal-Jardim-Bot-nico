"""Objetivo: Valida as credenciais de acesso, inicia a sessão e encerra o login."""
# Dependências usadas por este módulo.
from flask import render_template, request, redirect, url_for, session, flash
from banco_solar.repositories import dados_csv


def login():
    """Página de login."""
    # GET mostra a tela; POST recebe e confere as credenciais informadas.
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        # Consulta a tabela de acesso e procura o par e-mail/senha do protótipo.
        usuarios = dados_csv.load_csv('usuarios.csv')
        user = usuarios[(usuarios['email'] == email) & (usuarios['senha'] == senha)]

        if not user.empty:
            user_data = user.iloc[0]
            # Guarda a identificação e o perfil na sessão para proteger as páginas internas.
            session['user_id'] = str(user_data['id'])
            session['user_nome'] = user_data['nome']
            session['user_tipo'] = user_data['tipo']

            # Direciona cada perfil ao painel correspondente após o login.
            if user_data['tipo'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cliente_dashboard'))
        else:
            flash('E-mail ou senha incorretos. Tente novamente.', 'error')

    return render_template('auth/login.html')


def logout():
    """Encerrar sessão."""
    session.clear()
    return redirect(url_for('index'))


# Relaciona as URLs públicas às funções sem alterar os nomes usados em url_for.
def register_routes(app):
    """Registra as URLs desta área na aplicação."""
    app.add_url_rule('/login', endpoint='login', view_func=login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', endpoint='logout', view_func=logout, methods=['GET'])
