# Recursos do navegador

Objetivo: orientar a leitura dos estilos, scripts e mídias usados pelas páginas.

- `css/`: cada arquivo começa com seu objetivo e comenta os grupos de seletores,
  os estados de interação e os ajustes de responsividade.
- `js/`: cada arquivo resume sua função e comenta inicialização, funções e eventos.
- `img/`: logos, diagramas, moedas e fotos; arquivos binários são explicados no
  [mapa da arquitetura](../documentation/ARQUITETURA.md).
- `video/`: vídeos de abertura referenciados pelo template público.
- `noticias.json`: notícias iniciais combinadas com as publicações do SQLite.
- `uploads/`: documentos recebidos pelo fluxo de boletos; não entram na exportação.

## Estrutura de noticias.json

JSON não aceita comentários. Cada objeto representa uma notícia, com campos como:

| Campo | Objetivo |
| --- | --- |
| `id`, `type` | Identificar a notícia e distinguir matéria externa de publicação própria. |
| `title`, `summary` | Fornecer título e resumo para os cartões do portal. |
| `url`, `source` | Informar o endereço de destino e o nome da fonte. |
| `tags` | Listar os marcadores apresentados junto à matéria. |
| `images` | Listar as fotos: `src` indica o caminho e `alt` descreve a imagem. |

A cópia em `docs/static/noticias.json` é o snapshot usado pela demonstração.
O carregamento e a apresentação estão comentados em `js/noticias.js`.
