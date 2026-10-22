# Banco Solar — Plataforma de Gestão de Energia Compartilhada

<p align="center">
  <a href="https://brunav1dal.github.io/Portal-Jardim-Bot-nico/" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/▶_Acessar_demonstração_online-007A33?style=for-the-badge" alt="Acessar demonstração online do Banco Solar">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10 ou superior">
  <img src="https://img.shields.io/badge/Flask-3.1.1-000000?logo=flask&logoColor=white" alt="Flask 3.1.1">
  <img src="https://img.shields.io/badge/Pandas-2.2.3-150458?logo=pandas&logoColor=white" alt="Pandas 2.2.3">
  <img src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Chart.js-FF6384?logo=chart.js&logoColor=white" alt="Chart.js">
  <img src="https://img.shields.io/badge/Leaflet-199900?logo=leaflet&logoColor=white" alt="Leaflet">
</p>

Aplicação web para organizações que administram programas de energia solar compartilhada e precisam transformar dados operacionais em uma experiência clara para beneficiários, gestores e parceiros.

O Banco Solar centraliza a consulta de créditos de energia, economia estimada, indicadores de impacto e informações de atendimento em uma única plataforma. A solução foi concebida como um protótipo funcional, com fluxos demonstráveis e uma base técnica preparada para evoluir para uma operação integrada.

> **Ambiente demonstrativo:** os cadastros, indicadores, credenciais e valores exibidos são fictícios. Não representam faturamento, medição, contratos ou operação de uma distribuidora.

## Proposta de valor

Para uma empresa que opera ou estrutura programas de energia compartilhada, a plataforma oferece uma camada digital de relacionamento e gestão:

- **Transparência para beneficiários:** visualização simples de créditos, economia e histórico de consumo/compensação.
- **Eficiência operacional:** consolidação de residências, status de atendimento, indicadores e documentos em um painel administrativo.
- **Comunicação de impacto:** apresentação pública de geração, emissões evitadas e alcance social do programa.
- **Base para escala:** arquitetura web leve que pode ser conectada a fontes de dados validadas, sistemas de cobrança e canais de atendimento.

## Funcionalidades

| Módulo | Recursos principais | Público |
| --- | --- | --- |
| Portal público | Indicadores de transparência, dados de geração, impacto ambiental e mapa de unidades parceiras | Comunidade, parceiros e visitantes |
| Área do cliente | Créditos disponíveis, economia estimada, histórico ilustrativo, fatura e envio de boleto da concessionária | Beneficiários cadastrados |
| Painel administrativo | Acompanhamento de unidades, geração, tarifas, residências e situação dos beneficiários | Equipe gestora |

O painel administrativo inicia com um resumo visual do **Meu Solar**, reunindo
potência instalada, usinas disponíveis, geração mensal, CO₂ evitado e eficiência
média antes das abas detalhadas.
| API de transparência | Exposição dos indicadores públicos em JSON | Integrações e interfaces futuras |

A home possui navegação por seções no menu superior: **Dados**, **Nossa
história** e **Como funciona**. Os links levam diretamente à parte
correspondente da página e também funcionam a partir das telas internas.

## Fluxo da plataforma

```text
Dados operacionais e cadastrais
              ↓
       Camada de consolidação
              ↓
  Banco Solar (aplicação web)
       ↙              ↓              ↘
Portal público   Área do cliente   Administração
```

Em uma implantação de produção, os dados demonstrativos podem ser substituídos por integrações com sistemas de monitoramento, faturamento, CRM, atendimento ou bases homologadas pela operação.

## Diferenciais para contratação

- Interface orientada à compreensão do cliente, reduzindo dúvidas sobre créditos e economia.
- Visões separadas por perfil, com foco na jornada de cada público.
- Dados organizados para apoiar comunicação institucional, gestão e prestação de contas.
- Protótipo navegável, útil para validação de produto, apresentação comercial e levantamento de requisitos.
- Caminho claro de evolução para autenticação robusta, banco de dados, integrações e governança.

## Arquitetura técnica

O projeto utiliza uma arquitetura web monolítica simples, adequada para demonstração e evolução incremental.

| Camada | Tecnologia | Responsabilidade |
| --- | --- | --- |
| Backend | Python 3 + Flask 3.1.1 | Rotas, autenticação demonstrativa, regras de apresentação e API |
| Dados | Pandas 2.2.3 + CSV | Leitura e atualização dos dados do protótipo |
| Frontend | HTML, CSS e JavaScript | Interfaces públicas, do cliente e administrativas |
| Visualização | Chart.js e Leaflet | Gráficos de indicadores e mapa |

### Estrutura do repositório

```text
Eng_soc/
├── app.py                 # Rotas, regras de negócio e API
├── requirements.txt       # Dependências Python
├── data/                  # Dados demonstrativos em CSV
│   ├── usuarios.csv
│   ├── usinas.csv
│   ├── residencias.csv
│   ├── geracao_mensal.csv
│   └── boletos.csv
├── templates/             # Telas renderizadas pelo Flask
├── static/                # Estilos, imagens e uploads demonstrativos
└── docs/                  # Versão estática para publicação demonstrativa
```

## Rotas principais

| Rota | Descrição |
| --- | --- |
| `/` | Painel público de transparência |
| `/login` | Autenticação de demonstração |
| `/cliente` | Painel do cliente autenticado |
| `/cliente/anexar-boleto` | Recebimento de PDF, PNG ou JPG de até 5 MB |
| `/cliente/fatura` | Geração da fatura textual atual |
| `/admin` | Painel administrativo autenticado |
| `/api/transparencia` | Indicadores públicos em JSON |

## Executar localmente

**Pré-requisito:** Python 3.10 ou superior.

```powershell
cd Eng_soc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:5000` no navegador.

### Acessos de demonstração

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Administrador | `admin@bancosolar.com` | `admin123` |
| Cliente | `maria@email.com` | `user123` |

As credenciais são exclusivamente para demonstração e não devem ser reutilizadas em produção.

## Escopo atual e evolução recomendada

O repositório entrega uma prova de conceito funcional. Para uma contratação voltada à produção, recomenda-se incluir as seguintes frentes no escopo:

1. **Dados e integrações:** banco de dados transacional, integração com fontes operacionais homologadas e rotinas de conciliação.
2. **Segurança:** autenticação forte, hash de senhas, gestão de perfis, trilhas de auditoria, segredos em variáveis de ambiente e proteção de uploads.
3. **Confiabilidade:** validações, observabilidade, backups, testes automatizados, deploy contínuo e ambiente de homologação.
4. **Proteção de dados:** política de retenção, controles de acesso e adequação à LGPD conforme o papel de cada organização.
5. **Produto:** notificações, atendimento, relatórios exportáveis, indicadores configuráveis e experiência mobile aprimorada.

## Observações importantes

- Os arquivos CSV são um armazenamento local de demonstração; não são adequados para operação concorrente ou produção.
- A pasta `docs/` contém uma versão estática: autenticação e envio de arquivos não funcionam nela.
- Regras comerciais, compensação, faturamento e integrações devem ser definidas e validadas no projeto de implantação.

## Licença

Não há licença declarada. Antes de reutilizar, publicar ou comercializar o código, defina a licença aplicável e realize a revisão jurídica, técnica e de proteção de dados necessária.


## Interface e dados locais

A interface inclui filtros por periodo, demonstrativo de economia em reais,
acompanhamento de cotas e indicadores de familias beneficiadas. Os templates
Flask e a demonstracao estatica em `docs/` compartilham o mesmo visual.

Os CSVs publicados continuam sendo os exemplos ficticios do repositorio.
Nenhuma planilha privada e necessaria para iniciar a demonstracao. Na ausencia
de `beneficios_mensais.csv`, a aplicacao ativa um modo de demonstracao
identificado na tela, com pessoas e valores inteiramente ficticios definidos
em `scripts/demo_data.py`. Os logins publicados continuam disponiveis.
Alteracoes nesse modo ficam apenas na memoria e podem ser perdidas ao reiniciar.

Nao inclua CSVs locais, credenciais, faturas ou exportacoes com dados pessoais
em commits. As paginas estaticas usam pessoas e valores inteiramente ficticios gerados
em memoria. Para atualizar a interface em `docs/`, execute
`python scripts/export_demo.py`. O exportador bloqueia a leitura de CSVs e
nao utiliza a pasta de dados privados.
