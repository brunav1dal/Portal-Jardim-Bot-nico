# Como ler os comentários do projeto

Objetivo: explicar o padrão de documentação usado nos arquivos para facilitar
a leitura, a investigação de erros e a manutenção manual do sistema.

## O que procurar primeiro

1. **Objetivo no início do arquivo:** resume a responsabilidade daquele arquivo.
2. **Descrição da função:** explica a operação executada e o resultado esperado.
3. **Comentários de bloco:** explicam etapas como carregar dados, validar,
   calcular, gravar e preparar a resposta.

Os comentários descrevem o comportamento atual. Ao mudar uma regra, atualize
também a explicação ao lado dela para que as duas informações continuem coerentes.

## Sintaxe por tipo de arquivo

| Tipo | Como reconhecer | O que está explicado |
| --- | --- | --- |
| Python | `"""Objetivo: ..."""`, descrições de funções e linhas com `#` | Rotas, validações, cálculos, persistência e testes. |
| HTML/Jinja | `{# ... #}` nos templates | Seções, formulários, repetições, condições, gráficos e scripts. Esses comentários são removidos pelo Flask. |
| HTML estático | `<!-- ... -->` | Estrutura da cópia demonstrativa em `docs/`. |
| JavaScript | `/* Objetivo: ... */` e `// ...` | Inicialização, funções, eventos, filtros, requisições e gráficos. |
| CSS | `/* ... */` | Componentes, estados de interação, animações e regras de responsividade. |
| YAML e configurações de texto | Linhas com `#` | Dependências, publicação e exclusões do Git. |
| SVG | `<!-- ... -->` | Objetivo do ícone e composição vetorial. |

## Termos usados nas explicações

- **Rota:** função que recebe uma URL e devolve uma página, dados ou um redirecionamento.
- **Serviço:** parte que executa uma regra ou prepara os dados usados por uma tela.
- **Repositório:** parte que lê ou grava dados, sem decidir a apresentação da página.
- **Sessão:** informações do usuário autenticado reutilizadas entre as requisições.
- **CSRF:** token que associa o envio do formulário à sessão que o abriu.
- **Template/Jinja:** HTML com espaços e condições preenchidos pelo servidor.
- **Evento:** interação do navegador, como clique, digitação ou mudança de seleção.
- **Seletor CSS:** expressão que indica quais elementos recebem uma regra visual.
- **Responsividade:** ajustes da interface para diferentes tamanhos de tela.
- **Transação:** conjunto de operações no banco confirmado ou desfeito como uma unidade.
- **Mock/substituição:** recurso dos testes para simular dependências sem alterar dados reais.

## Dados e arquivos gerados

CSV e JSON não receberam comentários internos, pois esses formatos são consumidos
automaticamente. Suas finalidades e campos estão descritos em
[DADOS.md](DADOS.md), [static/README.md](../static/README.md) e no
[dicionário de dados](DICIONARIO_DE_DADOS.md).

Fotos, vídeos e PDFs são materiais binários; consulte o
[mapa da arquitetura](ARQUITETURA.md) e [references/README.md](../references/README.md).
Bibliotecas da `.venv/`, caches, metadados Git e o checkout separado em
`.deploy-localizacao/` ficam fora da documentação do código desta aplicação.

As cópias existentes em `docs/` também receberam comentários. Ao exportar novamente,
os arquivos são gerados a partir dos templates e dos recursos de origem; as
explicações Jinja continuam disponíveis nos templates, enquanto os comentários
de CSS e JavaScript acompanham os recursos exportados.

Para decidir onde fazer uma alteração, use o
[guia de manutenção](MANUTENCAO.md) e siga o fluxo `rota → serviço → repositório`.
