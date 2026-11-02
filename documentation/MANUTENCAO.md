# Como localizar alterações e investigar erros

Objetivo: Orientar a localização de alterações e a investigação de erros no terminal e no navegador.

## Executar e verificar

Na raiz do projeto, no PowerShell:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abra `http://127.0.0.1:5000`. O terminal mostra as requisições e os erros Python.
Para encerrar, pressione `Ctrl+C`.

Para verificar as jornadas sem alterar os CSVs reais:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes de notícias usam diretórios temporários. Os testes de aplicação usam
dados fictícios e substituem as operações de escrita.

## Onde começar conforme o problema

| Sintoma ou alteração | Primeiro arquivo | Depois confira |
| --- | --- | --- |
| Texto da página inicial | `templates/public/index.html` | `templates/components/project_flow.html` para o fluxo |
| Menu, logo ou navegação compartilhada | `templates/base.html` | `static/js/header-menu.js` e `static/css/style.css` |
| Cor, tamanho ou alinhamento | CSS associado à seção | A classe HTML e a aba Computed do navegador |
| Economia ou cashback incorreto | `banco_solar/services/beneficios.py` | `data/beneficios_mensais.csv` e serviço da área |
| Indicadores públicos incorretos | `banco_solar/services/publico.py` | Mês de referência e coluna `fonte` da geração |
| Histórico individual incorreto | `banco_solar/services/cliente.py` | `usuario_id` e mês nos CSVs |
| Dados do administrador | `banco_solar/services/admin.py` | CSV que fornece o indicador |
| Tarifa solar | `banco_solar/config.py` | `services/faturamento.py` e `services/admin.py` |
| Fatura e seu texto | `banco_solar/services/faturamento.py` | `routes/cliente.py` para o download |
| Login ou redirecionamento | `banco_solar/routes/auth.py` | `data/usuarios.csv` e sessão |
| Alteração de status não é salva | `routes/admin.py` → `services/admin.py` | `repositories/dados_csv.py` e permissões do arquivo |
| Boleto não é enviado | `routes/cliente.py` → `services/boletos.py` | Extensão, limite e diretório de upload |
| Notícia não é publicada | `routes/noticias.py` | Resposta HTTP, sessão e `repositories/noticias.py` |
| Foto de notícia rejeitada | `services/imagens.py` | Formato, dimensões e tamanho total do envio |
| Link de matéria não importa | `services/importacao_noticias.py` | Metadados do site e mensagem retornada |
| Mudança aparece localmente, mas não na demo | `scripts/export_demo.py` | Regenerar `docs/` e verificar publicação |

Os caminhos abreviados de `routes/`, `services/` e `repositories/` pertencem ao
pacote `banco_solar/`.

## Ler um erro Python

Leia o final do traceback primeiro: ele informa o tipo e a mensagem do erro.
Depois localize a última linha que aponta para um arquivo do projeto.

- `TemplateNotFound`: confira o caminho passado em `render_template` ou `include`.
- `BuildError`: confira o nome usado em `url_for` e o endpoint registrado na rota.
- `KeyError`: uma chave de dicionário ou coluna CSV não foi encontrada.
- `FileNotFoundError`: confira o caminho e a existência do arquivo.
- `ValueError` ou `TypeError`: confira os valores e tipos recebidos pelo cálculo.
- `sqlite3.OperationalError`: confira o diretório, o banco e a permissão de escrita.

Um erro em `services/cliente.py`, por exemplo, deve ser investigado nessa camada
e nos dados usados por ela. O `app.py` apenas inicia a aplicação.

## Investigar pelo navegador

Abra as ferramentas de desenvolvimento com `F12`:

1. **Elements/Elementos:** selecione o item visual e descubra sua classe e o CSS aplicado.
2. **Console:** veja erros JavaScript; clique no arquivo e na linha indicados.
3. **Network/Rede:** repita a ação e abra a requisição que falhou.
4. Confira o endereço, os dados enviados e a resposta do servidor.

Respostas comuns: `302` redireciona; `400` indica dados inválidos; `403` indica
acesso ou CSRF recusado; `404` indica recurso não encontrado; `413` indica envio
acima do limite; `500` exige olhar o traceback no terminal.

## Buscar um texto ou função

Com `rg` instalado:

```powershell
rg -n "calcular_parcela_beneficio" banco_solar
rg -n "Nossa história" templates
rg -n "cashback" banco_solar templates static/js
rg -n "navbar" templates static/css static/js
```

Você também pode usar a busca global do editor (`Ctrl+Shift+F`). Pesquise primeiro
nas pastas de origem; resultados em `docs/` são cópias exportadas.

## Fazer uma alteração pequena com confiança

1. Descreva o comportamento esperado e anote a tela ou URL afetada.
2. Localize a rota, o serviço e a origem do dado usando o mapa da arquitetura.
3. Altere a camada responsável. Um texto pertence ao template; um cálculo, ao serviço.
4. Execute os testes e reproduza o fluxo no navegador.
5. Para mudanças visuais, confira também uma largura de celular.
6. Revise `git diff` para identificar mudanças fora do esperado.

Ao criar uma nova rota, escreva a função e registre-a em `register_routes(app)`
do módulo correspondente. Para um módulo novo, registre-o também em `create_app()`.
Adicione serviço ou repositório quando houver regra ou persistência própria;
não é necessário criar uma classe para cada função.

## Atualizar a demonstração estática

```powershell
.\.venv\Scripts\python.exe scripts/export_demo.py
```

Isso reescreve as páginas demonstrativas em `docs/` e copia os recursos de
`static/`, excluindo uploads. O exportador usa dados fictícios e bloqueia leituras
de CSV durante a renderização. Login real, publicação e uploads exigem Flask.

O workflow publica `docs/`; a exportação local não publica nada por conta própria.
Notícias cadastradas no SQLite não entram automaticamente no snapshot estático.

## Dados e configurações

Faça uma cópia de segurança antes de editar os CSVs operacionais. Preserve os
nomes das colunas e os identificadores que conectam usuários, residências e benefícios.
Para notícias, faça backup de `noticias.sqlite3` e de `fotos/` juntos.

`SECRET_KEY` e `NEWS_STORAGE_DIR` podem ser definidos no ambiente antes de iniciar:

```powershell
$env:NEWS_STORAGE_DIR = "C:\caminho\persistente\noticias"
```

O projeto não carrega `.env` automaticamente. Na hospedagem, configure as
variáveis no painel do serviço. Os caminhos padrão ficam em `banco_solar/config.py`.
