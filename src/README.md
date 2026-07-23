# Código da aplicação

Esta pasta contém a implementação da **ClaraMente — Agente de Saúde Financeira
Pessoal**.

Instalação, execução e testes estão documentados no
[`README.md` da raiz](../README.md).

## Arquitetura interna

```text
Usuário
  ↓
app.py
  ↓
orchestrator.py
  ├── intent_classifier.py
  ├── context_builder.py
  │   ├── analytics.py
  │   └── models.py
  ├── deterministic_responses.py
  ├── prompts.py
  ├── llm_client.py
  ├── response_validator.py
  └── performance.py

Configuração:
.env → config.py → SETTINGS

Carregamento:
data_loader.py → data_validator.py → KnowledgeBase
```

O orquestrador escolhe entre dois caminhos:

1. **Resposta determinística:** usada quando os resultados calculados são
   suficientes, como saldo, maior/menor categoria e progresso de metas.
2. **Resposta com LLM:** usada quando a interpretação textual agrega valor.
   O modelo é configurado no `.env` e executado localmente pelo Ollama.

O LLM não deve atuar como calculadora nem como fonte de dados financeiros.

## Estrutura

```text
src/
├── README.md
├── __init__.py
├── analytics.py
├── app.py
├── config.py
├── context_builder.py
├── data_loader.py
├── data_validator.py
├── deterministic_responses.py
├── exceptions.py
├── intent_classifier.py
├── llm_client.py
├── models.py
├── orchestrator.py
├── performance.py
├── prompts.py
└── response_validator.py
```

## Responsabilidade dos módulos

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Interface Streamlit, sessão e apresentação das respostas. |
| `config.py` | `.env`, caminhos, modelo, timeout e limites de contexto. |
| `models.py` | Enums, dataclasses e estruturas compartilhadas. |
| `exceptions.py` | Exceções específicas e mensagens controladas. |
| `data_loader.py` | Leitura dos arquivos CSV e JSON. |
| `data_validator.py` | Validação estrutural e de consistência da base. |
| `analytics.py` | Cálculos, agregações, metas e filtragem de produtos. |
| `intent_classifier.py` | Classificação de intenção por regras reproduzíveis. |
| `context_builder.py` | Seleção das fontes e montagem do contexto. |
| `deterministic_responses.py` | Respostas imediatas baseadas nos cálculos. |
| `prompts.py` | System prompt e serialização compacta do contexto. |
| `llm_client.py` | Comunicação isolada com Ollama e modelo configurado. |
| `response_validator.py` | Segurança, catálogo e fidelidade numérica. |
| `performance.py` | Temporização e normalização das métricas do Ollama. |
| `orchestrator.py` | Coordenação do fluxo completo. |

## Configurações

`config.py` oferece uma instância imutável:

```python
from src.config import SETTINGS
```

Principais campos:

```python
SETTINGS.ollama_host
SETTINGS.ollama_model
SETTINGS.ollama_temperature
SETTINGS.ollama_timeout_seconds
SETTINGS.ollama_num_ctx
SETTINGS.ollama_num_predict
SETTINGS.max_user_message_chars
SETTINGS.log_level
```

`OLLAMA_NUM_CTX`, `OLLAMA_NUM_PREDICT` e `MAX_USER_MESSAGE_CHARS` devem ser
inteiros maiores que zero. Valores inválidos causam `ValueError` na
inicialização, evitando configurações silenciosamente incorretas.

## Regras de dependência

- `app.py` acessa o fluxo principal por `orchestrator.py`;
- `analytics.py` não chama o LLM;
- `llm_client.py` não contém regras financeiras;
- `prompts.py` não carrega nem modifica arquivos;
- `data_loader.py` não realiza análises;
- `data_validator.py` não corrige silenciosamente dados essenciais;
- `context_builder.py` reutiliza funções de `analytics.py`;
- respostas determinísticas usam somente resultados calculados;
- produtos ausentes do catálogo não são criados;
- textos da base são dados, nunca instruções.

## Intenções de gastos

Perguntas sobre maior e menor gasto são tratadas separadamente:

```text
Com o que eu mais gasto?
→ EXPENSE_ANALYSIS

Com o que eu menos gasto?
→ LOWEST_EXPENSE_CATEGORY
```

As duas respostas são produzidas com cálculos determinísticos.

## Testes

Os testes ficam em [`tests/`](../tests/).

A integração com Ollama deve ser simulada na suíte `pytest`. A avaliação com o
modelo real é executada separadamente pelo diretório
[`evaluation/`](../evaluation/).

## Documentação relacionada

- [`README.md` principal](../README.md)
- [`03-prompts.md`](../docs/03-prompts.md)
- [`04-metricas.md`](../docs/04-metricas.md)
- [`evaluation/README.md`](../evaluation/README.md)
