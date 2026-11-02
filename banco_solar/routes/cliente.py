"""Objetivo: Controla o acesso ao painel individual, o envio de boletos e o download da fatura."""
# Dependências usadas por este módulo.
from flask import render_template, request, redirect, url_for, session, flash, Response
from banco_solar.repositories import dados_csv
from banco_solar.services.arquivos import arquivo_permitido
from banco_solar.services.faturamento import calcular_fatura, montar_fatura_texto
from banco_solar.services.boletos import registrar_boleto
from banco_solar.services.cliente import montar_painel_cliente


def cliente_dashboard():
    """Entrega a página após validar o acesso."""
    # Confere sessão e perfil antes de consultar ou alterar informações individuais.
    if 'user_id' not in session or session.get('user_tipo') != 'cliente':
        return redirect(url_for('login'))
    return render_template('cliente/dashboard.html', **montar_painel_cliente(session['user_id']))


def anexar_boleto():
    """Recebe o upload de um novo boleto da concessionária."""
    # Confere sessão e perfil antes de consultar ou alterar informações individuais.
    if 'user_id' not in session or session.get('user_tipo') != 'cliente':
        return redirect(url_for('login'))

    # Recusa envios vazios antes de verificar o formato do documento.
    arquivo = request.files.get('boleto')
    if not arquivo or arquivo.filename == '':
        flash('Selecione um arquivo para anexar.', 'error')
        return redirect(url_for('cliente_dashboard'))

    # Valida a extensão antes de salvar o arquivo e registrar seu histórico.
    if not arquivo_permitido(arquivo.filename):
        flash('Formato não suportado. Envie um arquivo PDF, PNG ou JPG.', 'error')
        return redirect(url_for('cliente_dashboard'))

    registrar_boleto(session['user_id'], arquivo)

    flash('Boleto anexado com sucesso! Ele será analisado pela equipe do banco.', 'success')
    return redirect(url_for('cliente_dashboard'))


def baixar_fatura():
    """Gera a fatura atual do cliente para download."""
    # Confere sessão e perfil antes de consultar ou alterar informações individuais.
    if 'user_id' not in session or session.get('user_tipo') != 'cliente':
        return redirect(url_for('login'))

    # Busca o beneficiário e a residência associados ao identificador da sessão.
    usuarios = dados_csv.load_csv('usuarios.csv')
    residencias = dados_csv.load_csv('residencias.csv')
    user = usuarios[usuarios['id'].astype(str) == str(session['user_id'])].iloc[0]
    residencia = residencias[residencias['usuario_id'].astype(str) == str(session['user_id'])]

    # Informa a ausência de residência em vez de tentar gerar uma fatura incompleta.
    if residencia.empty:
        flash('Nenhuma residência associada à sua conta para gerar a fatura.', 'error')
        return redirect(url_for('cliente_dashboard'))

    r = residencia.iloc[0]
    fatura = calcular_fatura(r)
    if fatura is None:
        flash('O valor e o status desta fatura ainda não foram informados.', 'error')
        return redirect(url_for('cliente_dashboard'))

    conteudo = montar_fatura_texto(user, r, fatura)

    # Entrega o texto como anexo, com o nome de arquivo esperado pelo navegador.
    return Response(
        conteudo,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=fatura_atual.txt'}
    )


# Relaciona as URLs públicas às funções sem alterar os nomes usados em url_for.
def register_routes(app):
    """Registra as URLs desta área na aplicação."""
    app.add_url_rule('/cliente', endpoint='cliente_dashboard', view_func=cliente_dashboard, methods=['GET'])
    app.add_url_rule('/cliente/anexar-boleto', endpoint='anexar_boleto', view_func=anexar_boleto, methods=['POST'])
    app.add_url_rule('/cliente/fatura', endpoint='baixar_fatura', view_func=baixar_fatura, methods=['GET'])
