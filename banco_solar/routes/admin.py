"""Objetivo: Controla o painel administrativo e valida as alterações de status das residências."""
# Dependências usadas por este módulo.
from flask import render_template, request, redirect, url_for, session, jsonify
from banco_solar.services.admin import montar_painel_admin, atualizar_status_residencia


def admin_dashboard():
    """Entrega a página após validar o acesso."""
    # Restringe a visualização e as alterações ao perfil administrador.
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html', **montar_painel_admin())


def atualizar_residencia(residencia_id):
    """Atualiza os status (banco, concessionária, cashback) de uma residência."""
    # Restringe a visualização e as alterações ao perfil administrador.
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return jsonify({'success': False, 'error': 'não autorizado'}), 403

    # Aceita somente campos de status conhecidos com valores sim ou nao.
    dados = request.get_json(silent=True) or {}
    campos_validos = {'em_dia_banco', 'em_dia_concessionaria', 'cashback_em_dia'}
    atualizacoes = {k: v for k, v in dados.items() if k in campos_validos and v in ('sim', 'nao')}

    if not atualizacoes:
        return jsonify({'success': False, 'error': 'dados inválidos'}), 400

    # Delega a gravação ao serviço e traduz residência ausente para HTTP 404.
    if not atualizar_status_residencia(residencia_id, atualizacoes):
        return jsonify({'success': False, 'error': 'resid?ncia n?o encontrada'}), 404

    return jsonify({'success': True})


# Relaciona as URLs públicas às funções sem alterar os nomes usados em url_for.
def register_routes(app):
    """Registra as URLs desta área na aplicação."""
    app.add_url_rule('/admin', endpoint='admin_dashboard', view_func=admin_dashboard, methods=['GET'])
    app.add_url_rule('/admin/residencia/<int:residencia_id>/atualizar', endpoint='atualizar_residencia', view_func=atualizar_residencia, methods=['POST'])
