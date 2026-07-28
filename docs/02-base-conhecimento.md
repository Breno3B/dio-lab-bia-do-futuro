# Base de Conhecimento — ClaraMente

## Objetivo

A base de conhecimento fornece dados fictícios e estruturados para que a
ClaraMente produza análises reproduzíveis sem depender do conhecimento interno
do modelo.

Ela é composta por quatro arquivos em [`../data/`](../data/).

## Fontes

| Arquivo | Formato | Uso |
|---|---|---|
| [`transacoes.csv`](../data/transacoes.csv) | CSV | Entradas, saídas, categorias e períodos. |
| [`historico_atendimento.csv`](../data/historico_atendimento.csv) | CSV | Temas de atendimentos anteriores. |
| [`perfil_investidor.json`](../data/perfil_investidor.json) | JSON | Perfil, objetivos, metas e tolerância a risco. |
| [`produtos_financeiros.json`](../data/produtos_financeiros.json) | JSON | Catálogo fechado. |

Todos os dados são fictícios e usados somente para estudo.

## Estrutura dos dados

### `transacoes.csv`

Campos esperados:

| Campo | Uso |
|---|---|
| `data` | Período e ordenação. |
| `descricao` | Identificação da movimentação. |
| `categoria` | Agrupamento das despesas. |
| `valor` | Valor monetário. |
| `tipo` | Entrada ou saída. |

O carregamento converte datas e valores para tipos apropriados. Os cálculos
consideram somente registros válidos.

### `historico_atendimento.csv`

Campos utilizados pelo cenário:

| Campo | Uso |
|---|---|
| `data` | Data do atendimento. |
| `tema` | Assunto principal. |
| `resumo` | Síntese do registro. |

O histórico confirma que um assunto foi registrado. Ele não comprova
movimentações financeiras nem substitui a base de transações.

### `perfil_investidor.json`

O arquivo reúne informações do perfil, como:

- classificação do investidor;
- tolerância a risco;
- objetivos;
- metas;
- preferências e restrições.

A base atual contém uma inconsistência intencional entre o perfil declarado e
a aceitação de risco. O sistema deve sinalizar essa divergência antes de
avaliar produtos.

### `produtos_financeiros.json`

Cada produto possui atributos usados na filtragem, por exemplo:

- nome;
- tipo;
- nível de risco;
- rentabilidade;
- aporte mínimo;
- indicação de perfil.

O arquivo é um catálogo fechado. Produtos ausentes não podem ser inventados.

## Carregamento e validação

```text
data/
  ↓
data_loader.py
  ↓
KnowledgeBase
  ↓
data_validator.py
  ↓
ValidationReport
```

### Responsabilidades

`data_loader.py`:

- lê CSV e JSON;
- converte os dados para estruturas usadas pela aplicação;
- não executa análises;
- não corrige silenciosamente inconsistências essenciais.

`data_validator.py`:

- verifica colunas e campos obrigatórios;
- valida tipos e valores;
- identifica inconsistências;
- pode interromper o fluxo quando a base não é segura para análise.

## Seleção por intenção

O sistema não envia toda a base ao modelo em todas as perguntas.

| Intenção | Fontes principais |
|---|---|
| Resumo financeiro | transações |
| Maior ou menor gasto | transações |
| Comparação de períodos | transações |
| Meta financeira | perfil |
| Histórico | histórico de atendimento |
| Produtos | perfil e catálogo |
| Mercado atual | nenhuma fonte atual disponível |
| Fora do escopo | nenhuma fonte financeira |
| Solicitação ilícita | resposta determinística |

Essa seleção reduz ruído, latência e risco de exposição desnecessária.

## Processamento determinístico

Python e pandas calculam:

- total de entradas;
- total de saídas;
- saldo;
- quantidade de transações;
- período analisado;
- maior categoria;
- menor categoria;
- participação percentual;
- progresso e valor restante de metas;
- disponibilidade de períodos para comparação;
- produtos autorizados pelo catálogo e pelo contexto.

O LLM não recalcula esses resultados.

## Contexto dinâmico

O contexto enviado ao modelo contém somente informações relevantes:

```json
{
  "intencao": "product_compatibility",
  "fontes_consultadas": [
    "data/perfil_investidor.json",
    "data/produtos_financeiros.json"
  ],
  "resultados_calculados": {},
  "produtos": [],
  "produtos_autorizados": [
    "CDB Liquidez Diária",
    "Tesouro Selic"
  ],
  "inconsistencias": [
    "Há divergência entre perfil_investidor e aceita_risco."
  ],
  "dados_ausentes": [],
  "restricoes_especificas": [
    "Os dados são mockados e têm finalidade educacional."
  ]
}
```

O exemplo é ilustrativo; os valores concretos são montados pela aplicação.

## Produtos e metadados

Respostas de produtos usam um objeto JSON com dois campos:

```json
{
  "resposta": "Texto apresentado ao usuário.",
  "produtos_mencionados": []
}
```

`produtos_mencionados` permite comparar os nomes declarados pelo modelo com:

- o catálogo autorizado;
- os produtos permitidos para o contexto;
- os nomes realmente citados no texto.

## Histórico e fallback

O contexto de histórico pode conter registros relevantes. Se a geração for
excessiva, insegura ou tentar expor configurações internas, o orquestrador
constrói uma resposta segura usando esses registros.

Quando não há registro relacionado, a resposta informa a ausência de dados sem
inventar conteúdo.

## Rastreabilidade

Cada resposta pode expor:

- fontes consultadas;
- resultados calculados;
- inconsistências;
- dados ausentes;
- restrições aplicadas;
- métricas de execução.

## Privacidade e segurança

- processamento local;
- dados fictícios;
- arquivos originais preservados;
- contexto mínimo;
- logs sem necessidade de dados sensíveis;
- textos da base tratados como dados;
- ausência de integrações externas de mercado ou transações.

## Limitações

- poucos registros;
- único perfil;
- catálogo reduzido;
- histórico simplificado;
- ausência de atualização em tempo real;
- dados não representam um cliente real.
