# Arquitetura e mapa do projeto

Objetivo: Explicar a arquitetura, as responsabilidades e a localização dos arquivos do projeto.

Este é um monólito modular com Flask: uma aplicação, dividida em módulos por
responsabilidade. As páginas são renderizadas no servidor com HTML/Jinja.
Os dados operacionais continuam em CSV e as notícias cadastradas em SQLite.

## Comece por aqui

1. Leia o mapa abaixo para localizar a área que deseja alterar.
2. Use [MANUTENCAO.md](MANUTENCAO.md) para investigar erros e verificar alterações.
3. Consulte [DICIONARIO_DE_DADOS.md](DICIONARIO_DE_DADOS.md) para entender as colunas.
4. Consulte [NOTICIAS.md](NOTICIAS.md) para administrar as notícias.
5. Use [COMENTARIOS.md](COMENTARIOS.md) para entender a sintaxe e os termos das explicações no código.

## Fluxo de uma requisição

```text
Navegador solicita /cliente
    ↓
routes/cliente.py verifica a sessão
    ↓
services/cliente.py prepara os indicadores
    ↓
repositories/dados_csv.py lê as tabelas em data/
    ↓
services/beneficios.py e faturamento.py aplicam os cálculos
    ↓
routes/cliente.py entrega templates/cliente/dashboard.html
    ↓
Navegador aplica static/css e executa static/js
```

As dependências seguem a direção `routes → services → repositories`.
Uma rota também pode consultar um repositório para uma operação simples, como
o login. Repositórios não importam rotas nem trabalham com sessão ou HTML.
Serviços recebem argumentos e retornam dados; a rota decide a resposta HTTP.

## Código Python

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Entrada local e de hospedagem. Expõe `app` e chama a fábrica. |
| `banco_solar/__init__.py` | `create_app()` cria o Flask, aplica configurações e registra os módulos. |
| `banco_solar/config.py` | Caminhos absolutos, tarifa solar, coordenadas, limite de upload e configurações de ambiente. |
| `routes/publico.py` | Entrega a página inicial e a API de transparência. |
| `routes/auth.py` | Login, criação da sessão e logout. |
| `routes/cliente.py` | Acesso do beneficiário, recebimento do boleto e resposta de download da fatura. |
| `routes/admin.py` | Acesso administrativo e validação dos status enviados pelo painel. |
| `routes/noticias.py` | Formulários, permissões, CSRF, publicação, edição, exclusão, feed e entrega das fotos. |
| `services/publico.py` | Consolida indicadores públicos, séries mensais e informações do mapa. |
| `services/cliente.py` | Prepara o painel individual, histórico, indicadores por período e comparação com a média. |
| `services/admin.py` | Prepara o painel de gestão e atualiza os status das residências. |
| `services/beneficios.py` | Calcula a economia, as parcelas monetárias e o demonstrativo do benefício. |
| `services/faturamento.py` | Calcula a fatura e formata seu texto. |
| `services/boletos.py` | Salva o documento e registra seu envio na tabela de boletos. |
| `services/arquivos.py` | Verifica as extensões de boleto permitidas. |
| `services/imagens.py` | Valida e converte fotos de notícias. |
| `services/importacao_noticias.py` | Consulta metadados de matérias externas e valida os destinos de rede. |
| `repositories/dados_csv.py` | Centraliza leitura e gravação das tabelas e o modo demonstrativo em memória. |
| `repositories/noticias.py` | Lista, salva e exclui notícias em transações SQLite. |

Os caminhos `routes/`, `services/` e `repositories/` acima ficam dentro de
`banco_solar/`. Os arquivos `__init__.py` tornam essas pastas pacotes Python.
Não existe uma classe de modelo por tabela, pois o projeto usa DataFrames do
Pandas diretamente; o contrato das tabelas está no dicionário de dados.

## URLs e telas

Os módulos usam `register_routes(app)` e `app.add_url_rule`. Isso mantém os
nomes de endpoint existentes, usados em `url_for`, nos templates e na exportação.
Notícias registra seus endpoints em `init_news(app)`.

| URL | Rota | Tela ou resposta |
| --- | --- | --- |
| `/` | `routes/publico.py` | `templates/public/index.html` |
| `/api/transparencia` | `routes/publico.py` | JSON de indicadores |
| `/login`, `/logout` | `routes/auth.py` | `templates/auth/login.html` e redirecionamentos |
| `/cliente` | `routes/cliente.py` | `templates/cliente/dashboard.html` |
| `/cliente/anexar-boleto` | `routes/cliente.py` | Recebe arquivo por POST |
| `/cliente/fatura` | `routes/cliente.py` | Download de texto |
| `/admin` | `routes/admin.py` | `templates/admin/dashboard.html` |
| `/admin/residencia/<id>/atualizar` | `routes/admin.py` | Recebe status por POST e responde JSON |
| `/api/noticias` | `routes/noticias.py` | JSON de notícias |
| `/admin/noticias` e subrotas | `routes/noticias.py` | Publicação, importação, consulta, edição e exclusão |
| `/noticias/fotos/<arquivo>` | `routes/noticias.py` | Foto processada |

`templates/base.html` contém a estrutura compartilhada e o cabeçalho.
`templates/components/project_flow.html` é um trecho incluído na página inicial.
`templates/admin/noticias.html` é incluído no painel administrativo.
`templates/components/parceiros.html` encerra o portal com os parceiros. A lista
no início do arquivo reúne nome, identificação e contribuição; `none` deixa o
verso sem descrição. As informações foram fornecidas pela equipe. A universidade
norueguesa foi retirada; permanecem DECODE, UFPB, UFRJ/LABIS, FGV Rio e CNPq.
Os PNGs locais e suas fontes estão em `static/img/parceiros/README.md`. A marca
DECODE foi fornecida pela usuária e convertida para PNG com transparência.
`templates/components/economia_partition.html` mostra a divisão percentual da
economia real no modal. É um exemplo por R$ 100 de energia solar, separado do
histórico mensal, com pagamento bruto e cashback identificados.

## Aparência e comportamento no navegador

| Arquivo em `static/` | Função |
| --- | --- |
| `css/style.css` | Estilos gerais e dos painéis. Procure a classe do elemento antes de editar. |
| `css/noticias.css` | Notícias e editor. |
| `css/project-flow.css` | Fluxo de funcionamento do projeto. |
| `css/solar-scenarios.css` | Cenários de cotas solares. |
| `css/parceiros.css` | Cards reversíveis dos parceiros, faces e adaptação a celulares. |
| `css/economia-breakdown.css` | Barra de 100%, legenda e resumo da composição da economia real. |
| `js/header-menu.js` | Menu responsivo. |
| `js/header-glass.js` | Efeito visual do cabeçalho. |
| `js/hero-video.js` | Vídeo de destaque. |
| `js/history-gallery.js` | Galeria de Nossa História. |
| `js/cenarios-solares.js` | Interações dos cenários solares. |
| `js/noticias.js` | Notícias e visualização de matérias no portal. |
| `js/admin-noticias.js` | Formulário de administração das notícias. |
| `js/parceiros.js` | Alternância dos cards por clique, toque e teclado e sincronização de acessibilidade. |
| `js/economia-breakdown.js` | Gráfico de composição 50%/25%/25% e ciclo de abertura e fechamento no modal. |
| `noticias.json` | Notícias externas iniciais, combinadas com as do SQLite. |
| `img/` | Logos, moedas, diagramas e fotos utilizadas pelo site. |
| `video/` | Vídeos utilizados pelo site. |

Ainda há scripts de gráficos e painéis dentro dos templates. Para investigá-los,
procure por `<script>` na tela correspondente. O CSS geral também continua em
um arquivo compartilhado: a reorganização preserva os seletores e sua ordem.

## Dados, artefatos e ferramentas

| Caminho | Conteúdo e uso |
| --- | --- |
| `data/usuarios.csv` | Cadastro, acesso e valores associados aos usuários. |
| `data/residencias.csv` | Unidades consumidoras e status de pagamento. |
| `data/usinas.csv` | Cadastro das usinas. |
| `data/geracao_mensal.csv` | Produção mensal e indicadores operacionais. |
| `data/beneficios_mensais.csv` | Cotas, consumo, benefícios e créditos por pessoa/mês. |
| `data/boletos.csv` | Histórico dos documentos enviados. |
| `data/credenciais_provisorias.csv` | Material auxiliar com acessos fictícios provisórios; não é a tabela consultada pelo login. |
| `runtime/noticias/` | SQLite e fotos cadastradas; caminho substituível por `NEWS_STORAGE_DIR`. |
| `runtime/` | Também contém temporários de verificações locais. Separar esses arquivos do backup das notícias. |
| `static/uploads/boletos/` | Documentos enviados no fluxo atual. Não são incluídos na exportação estática. |
| `banco_solar/demo.py` | Cria os registros fictícios da demonstração e do modo operacional demonstrativo. |
| `scripts/export_demo.py` | Renderiza as telas com dados fictícios e copia os recursos públicos para `docs/`. |
| `tests/test_application.py` | Jornadas de login, painéis, fatura, atualização, upload e exportação. |
| `tests/test_services.py` | Regras monetárias, arredondamento e fatura. |
| `tests/test_news.py` | Publicação e gerenciamento de notícias. |
| `tests/test_news_import.py` | Importação externa e validação dos destinos. |
| `documentation/` | Documentação técnica que você está lendo. |
| `docs/` | Site estático publicado pelo GitHub Pages. Saída de exportação; alterar a origem e gerar novamente. |
| `references/pdf/`, `references/jpeg/` | Fluxogramas e imagens de apoio antes soltos na raiz. |
| `.github/workflows/deploy-pages.yml` | Publica o conteúdo de `docs/` no GitHub Pages. |
| `requirements.txt` | Dependências Python. |
| `.gitignore` | Define arquivos locais que o Git deve ignorar. |
| `.venv/` | Bibliotecas e interpretador do ambiente local. |
| `__pycache__/` | Cache automático do Python. |
| `.git/` | Histórico e metadados do repositório. |
| `.deploy-localizacao/` | Checkout local separado encontrado no workspace; não é o código carregado por esta aplicação. |
| `db/` | Pasta local encontrada apenas com cache; não é o armazenamento SQLite de notícias. |

## Compatibilidade e limites

- `python app.py` e `gunicorn app:app` continuam sendo as entradas.
- As URLs, os nomes dos endpoints e os nomes/formatos dos CSVs foram mantidos.
- `docs/` foi mantida para preservar o fluxo de publicação existente.
- Os antigos `news.py` e `news_import.py` foram substituídos pelos módulos descritos acima.
- Esta mudança organiza o código; não migra os CSVs para outro banco nem altera
  as regras de autenticação e cobrança.
- O modo demonstrativo operacional ainda é decidido pela ausência de
  `data/beneficios_mensais.csv`. A exportação usa dados fictícios explicitamente,
  independentemente desse modo.
