# Dicionário de dados — Banco Solar

Os dados persistidos estão em CSV. Valores calculados, configurações e estruturas montadas pela aplicação estão em `app.py`. Itens em **negrito** possuem campos, listas ou registros internos.

## Dados persistidos

| Campo ou item | Descrição / regra | Categoria atualizada | Localização atual |
| --- | --- | --- | --- |
| `id` | Identificador único do usuário. | Cadastro e administração | `data/usuarios.csv` |
| `nome` | Nome completo do cliente ou administrador. | Cadastro e administração | `data/usuarios.csv` |
| `email` | E-mail usado para acesso; deve ser único. | Cadastro e administração | `data/usuarios.csv` |
| `senha` | Senha de acesso; em produção, armazenar somente hash. | Cadastro e administração | `data/usuarios.csv` |
| `tipo` | Perfil de acesso: `admin` ou `cliente`. | Cadastro e administração | `data/usuarios.csv` |
| `data_cadastro` | Data de criação do cadastro. | Cadastro e administração | `data/usuarios.csv` |
| `investido` | Valor investido pelo beneficiário, em reais. | Cadastro e administração | `data/usuarios.csv` |
| `economia_kw` | Economia acumulada de energia atribuída ao cliente. | Consumo | `data/usuarios.csv` |
| `creditos` | Saldo de créditos de energia do cliente. | Consumo | `data/usuarios.csv` |
| `kw_recebidos` | Energia recebida ou compensada pelo beneficiário. | Consumo | `data/usuarios.csv` |
| `cashback_orquideas` | Valor acumulado de cashback Orquídeas. | Moeda Orquídeas | `data/usuarios.csv` |
| `id` | Identificador único da residência. | Cadastro e administração | `data/residencias.csv` |
| `usuario_id` | Usuário associado à residência; referência para `usuarios.id`. | Cadastro e administração | `data/residencias.csv` |
| `endereco` | Endereço da unidade consumidora. | Cadastro e administração | `data/residencias.csv` |
| `em_dia_banco` | Pagamento junto ao Banco Solar: `sim` ou `nao`. | Cadastro e administração | `data/residencias.csv` |
| `em_dia_concessionaria` | Situação da conta tradicional: `sim` ou `nao`. | Cadastro e administração | `data/residencias.csv` |
| `cashback_em_dia` | Regularidade no programa Orquídeas: `sim` ou `nao`. | Cadastro e administração | `data/residencias.csv` |
| `consumo_mensal_kwh` | Consumo mensal da unidade consumidora. | Consumo | `data/residencias.csv` |
| `economia_mensal_rs` | Economia mensal estimada, em reais. | Consumo | `data/residencias.csv` |
| `ultima_atualizacao` | Data da última alteração dos status. | Cadastro e administração | `data/residencias.csv` |
| `id` | Identificador único da usina. | Produção da usina | `data/usinas.csv` |
| `nome` | Nome de apresentação da usina. | Produção da usina | `data/usinas.csv` |
| `localizacao` | Endereço/localização exibido no mapa. | Produção da usina | `data/usinas.csv` |
| `capacidade_kw` | Potência instalada da usina. | Produção da usina | `data/usinas.csv` |
| `geracao_mensal_kwh` | Geração mensal de referência. | Produção da usina | `data/usinas.csv` |
| `status` | Situação operacional: `ativa` ou `manutencao`. | Produção da usina | `data/usinas.csv` |
| `data_instalacao` | Data de instalação ou entrada em operação. | Produção da usina | `data/usinas.csv` |
| `eficiencia_percent` | Eficiência operacional da usina. | Produção da usina | `data/usinas.csv` |
| `mes` | Mês de referência da medição. | Produção da usina | `data/geracao_mensal.csv` |
| `usina_id` | Usina da medição; referência para `usinas.id`. | Produção da usina | `data/geracao_mensal.csv` |
| `geracao_kwh` | Energia gerada pela usina no mês. | Produção da usina | `data/geracao_mensal.csv` |
| `co2_evitado_kg` | Emissões de CO₂ evitadas no mês. | Produção da usina | `data/geracao_mensal.csv` |
| `receita_rs` | Receita associada à geração mensal. | Produção da usina | `data/geracao_mensal.csv` |
| `id` | Identificador único do envio. | Cadastro e administração | `data/boletos.csv` |
| `usuario_id` | Cliente que enviou o boleto; referência para `usuarios.id`. | Cadastro e administração | `data/boletos.csv` |
| `nome_arquivo` | Nome original do documento anexado. | Cadastro e administração | `data/boletos.csv` |
| `data_envio` | Data de envio do boleto. | Cadastro e administração | `data/boletos.csv` |
| `status` | Status: `Enviado`, `Em Análise` ou `Confirmado`. | Cadastro e administração | `data/boletos.csv` |
| `arquivo_boleto` | Documento físico associado ao boleto. | Cadastro e administração | `static/uploads/boletos/{usuario_id}/` |

## Configurações, cálculos e estruturas da aplicação

| Campo ou item | Descrição / regra | Categoria atualizada | Localização atual |
| --- | --- | --- | --- |
| `TARIFA_SOLAR_CLIENTE` | Tarifa solar única: R$ 0,30 por kWh. | Cadastro e administração | `app.py` |
| `tarifa_concessionaria` | Tarifa de referência: R$ 0,75 por kWh. | Concessionária | `app.py` |
| **`COORDENADAS_CIDADES`** | Dicionário: **`usinas.localizacao`** → **`(latitude, longitude)`**. | Produção da usina | `app.py` |
| **`fatura`** | Objeto: **`valor`** (consumo × tarifa) e **`status`** (`Paga` ou `Em Aberto`). | Dados calculados e consolidados | `app.py`, `calcular_fatura` |
| **`transparencia`** | Indicadores: **`economia_kw`**, **`creditos`**, **`kw_recebidos`**, **`investido`**, **`cashback_orquideas`**, **`geracao_total_kwh`**, **`co2_evitado_total`**, **`num_usinas`**, **`num_clientes`**. | Dados calculados e consolidados | `app.py`, `/` e `/api/transparencia` |
| **`geracao_por_mes`** | Lista de registros: **`mes`**, **`geracao_kwh`**, **`co2_evitado_kg`** e, no admin, **`receita_rs`**. | Dados calculados e consolidados | `app.py` |
| **`geracao_por_usina`** | Lista de registros: **`nome`**, **`geracao_kwh`**. | Dados calculados e consolidados | `app.py` |
| **`dados_unificados`** | Objeto: **`total_capacidade`**, **`total_geracao_mensal`**, **`total_co2`**, **`media_eficiencia`**, **`num_usinas_ativas`**, **`num_usinas_manutencao`**. | Dados calculados e consolidados | `app.py`, `/admin` |
| **`economia_concessionaria`** | Objeto: **`tarifa_concessionaria`**, **`tarifa_solar`**, **`economia_percentual`**, **`economia_mensal_rs`**. | Dados calculados e consolidados | `app.py`, `/admin` |
| **`stats_residencias`** | Objeto: **`total`**, **`em_dia_banco`**, **`em_dia_banco_pct`**, **`em_dia_concessionaria`**, **`em_dia_concessionaria_pct`**, **`cashback_em_dia`**, **`cashback_em_dia_pct`**. | Dados calculados e consolidados | `app.py`, `/admin` |
| `meses_dentro_cota` | Simulação determinística de seis meses; não persistida. | Dados calculados e consolidados | `app.py`, `/admin` |
| `meses_totais` | Quantidade de meses da simulação: 6. | Cadastro e administração | `app.py`, `/admin` |
| **`historico`** | Objeto de listas simuladas: **`meses`**, **`economia`**, **`creditos`**, **`kw_recebidos`**. | Consumo | `app.py`, `/cliente` |
| **`comparacao`** | Dicionário por métrica; cada registro contém **`valor`**, **`media`**, **`diferenca_pct`**, **`valor_pct`**, **`media_pct`**. | Dados calculados e consolidados | `app.py`, `/cliente` |
| **`boletos_historico`** | Lista de boletos do cliente, ordenada por `data_envio`. | Cadastro e administração | `app.py`, `/cliente` |
| **`usinas_mapa`** | Lista de registros: **`nome`**, **`localizacao`**, **`status`**, **`capacidade_kw`**, **`lat`**, **`lng`**. | Produção da usina | `app.py`, `/` |
| **`geracao_individual`** | Dicionário por usina com listas de **`meses`**, **`geracao`**, **`co2`**, **`receita`**. | Produção da usina | `app.py`, `/admin` |
| `MAX_CONTENT_LENGTH` | Tamanho máximo para boleto: 5 MB. | Cadastro e administração | `app.py` |
| **`EXTENSOES_PERMITIDAS`** | Conjunto: **`pdf`**, **`png`**, **`jpg`**, **`jpeg`**. | Cadastro e administração | `app.py` |

## Estruturas compostas em destaque

Há **14 estruturas compostas**: `COORDENADAS_CIDADES`, `fatura`, `transparencia`, `geracao_por_mes`, `geracao_por_usina`, `dados_unificados`, `economia_concessionaria`, `stats_residencias`, `historico`, `comparacao`, `boletos_historico`, `usinas_mapa`, `geracao_individual` e `EXTENSOES_PERMITIDAS`.
