# Cadastro de notícias

No aplicativo Flask, entre com perfil de administrador e abra **Notícias**. Informe título, resumo opcional, texto e de uma a cinco fotos. A primeira foto será a capa. A publicação aparece imediatamente no carrossel de Nossa História; ao clicar, o visitante abre o texto completo e as fotos.

O envio completo aceita até 5 MB. As imagens JPG, PNG e WebP são verificadas, orientadas e convertidas em JPEG com até 2.400 pixels no maior lado, sem metadados. O cadastro não altera as planilhas de energia ou os dados dos beneficiários.

## Matérias de sites externos

Selecione **Notícia de site externo** e cole o link da matéria. O painel busca título, resumo e foto de capa pelos metadados públicos Open Graph/Twitter do site. O botão **Buscar informações** permite repetir a busca. Confira a prévia, ajuste o título ou o resumo se precisar e clique em **Publicar notícia**. A importação sozinha não publica.

Ao clicar no card, o visitante abre a matéria completa no site original. A foto importada é validada e armazenada junto às fotos do projeto. Se o site bloquear a leitura, não informar metadados ou não liberar a imagem, preencha o título e envie uma foto manualmente; o link continua sendo usado como destino da matéria. Vídeos e páginas que dependem de execução de JavaScript não são importados como mídia incorporada.

## Armazenamento na Render

As notícias e fotos usam um diretório independente, configurado pela variável `NEWS_STORAGE_DIR`. Por padrão ele é `runtime/noticias` no projeto, ignorado pelo Git. Esse diretório contém `noticias.sqlite3` e a pasta `fotos`.

Para manter os cadastros após reinícios e novas implantações na Render, monte um disco persistente no serviço e defina, por exemplo, `NEWS_STORAGE_DIR=/var/data/noticias`, quando `/var/data` for o ponto de montagem do disco. O diretório precisa permitir escrita pelo processo do aplicativo. Faça backup do banco SQLite e das fotos juntos.

Sem disco persistente, as publicações podem desaparecer quando a Render substituir a instância. Este repositório não configura automaticamente um disco na conta da Render.

## Demonstração estática no GitHub Pages

O cadastro requer o backend Flask. A cópia estática em `docs/` exibe uma prévia do formulário, com publicação desativada. Ela usa o arquivo `docs/static/noticias.json` como snapshot; as notícias cadastradas na Render não são enviadas automaticamente ao GitHub.

Notícias externas do arquivo `static/noticias.json` continuam sendo exibidas junto às publicações próprias no aplicativo. Os dados reais locais dos beneficiários não são enviados ao site de demonstração.
