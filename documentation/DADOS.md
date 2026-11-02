# Dados operacionais

Objetivo: explicar os arquivos de dados sem inserir comentários dentro dos CSVs,
preservando sua leitura pelo Pandas e pelo Excel.

| Arquivo | Resumo do objetivo |
| --- | --- |
| `usuarios.csv` | Armazenar os cadastros, perfis de acesso e valores associados aos usuários. |
| `residencias.csv` | Relacionar unidades consumidoras aos usuários e registrar seus status. |
| `usinas.csv` | Armazenar as características e a situação operacional das usinas. |
| `geracao_mensal.csv` | Registrar a geração e os indicadores operacionais de cada usina por mês. |
| `beneficios_mensais.csv` | Registrar cotas, consumo, energia recebida, benefícios e créditos por pessoa e mês. |
| `boletos.csv` | Registrar identificação, nome original, data e status dos documentos enviados. |
| `credenciais_provisorias.csv` | Listar credenciais fictícias provisórias para apoio ao cadastro. |

Cada linha de cabeçalho define as colunas; as demais linhas representam registros.
`usuario_id` faz referência a `usuarios.id` e `usina_id` a `usinas.id`.
As medições mensais usam também `mes` para identificar o período.

Os blocos de leitura e gravação estão comentados em
`banco_solar/repositories/dados_csv.py`. Consulte o
[dicionário de dados](../documentation/DICIONARIO_DE_DADOS.md) para entender os campos
e o [guia de manutenção](../documentation/MANUTENCAO.md) para investigar divergências.
