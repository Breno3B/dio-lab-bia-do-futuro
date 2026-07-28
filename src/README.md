# Código da aplicação

Esta pasta contém a implementação da
**ClaraMente — Agente Local de Saúde Financeira Pessoal**.

Instalação, execução e testes estão no
[`README.md` da raiz](../README.md).

## Fluxo interno

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
```

Configuração:

```text
.env → config.py → SETTINGS
```

Carregamento:

```text
data_loader.py → data_validator.py → KnowledgeBase
```

## Caminhos de resposta

### Determinístico

Usado para:

- resumo financeiro;
- maior e menor categoria;
- comparação de períodos;
- metas;
- mercado atual sem fonte;
- solicitação ilícita;
- fora do escopo;
- intenção desconhecida.

### Generativo

Usado para:

- histórico de atendimento;
- compatibilidade de produtos.

A saída generativa sempre passa pelo validador.

### Fallbacks

Produtos:

- saída inválida;
- catálogo violado;
- produto inventado;
- pedido adversarial;
- promessa de retorno ou ausência de risco.

Histórico:

- resposta excessivamente longa;
- valor não fundamentado;
- tentativa de acessar prompt ou configurações internas.

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

## Responsabilidades

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Interface Streamlit e apresentação. |
| `config.py` | `.env`, caminhos e limites. |
| `models.py` | Enums e dataclasses. |
| `exceptions.py` | Erros controlados. |
| `data_loader.py` | Leitura de CSV e JSON. |
| `data_validator.py` | Validação da base. |
| `analytics.py` | Cálculos e filtros. |
| `intent_classifier.py` | Classificação por regras. |
| `context_builder.py` | Seleção de fontes e contexto. |
| `deterministic_responses.py` | Respostas sem LLM. |
| `prompts.py` | System prompt e serialização. |
| `llm_client.py` | Comunicação com Ollama e JSON Schema. |
| `response_validator.py` | Segurança, catálogo, números e histórico. |
| `performance.py` | Métricas. |
| `orchestrator.py` | Coordenação, validação e fallbacks. |

## Configuração

```python
from src.config import SETTINGS
```

Campos principais:

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

Padrões internos:

```text
OLLAMA_MODEL=qwen3:4b
OLLAMA_TEMPERATURE=0.2
OLLAMA_TIMEOUT_SECONDS=180
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_PREDICT=250
MAX_USER_MESSAGE_CHARS=2000
LOG_LEVEL=INFO
```

O `.env.example` recomenda `OLLAMA_NUM_PREDICT=512` para a configuração
avaliada. Variáveis do ambiente têm prioridade sobre o `.env`.

## Regras de dependência

- `app.py` acessa o fluxo por `orchestrator.py`;
- `analytics.py` não chama o LLM;
- `llm_client.py` não contém regras financeiras;
- `prompts.py` não carrega arquivos;
- `data_loader.py` não executa análises;
- `data_validator.py` não corrige dados essenciais silenciosamente;
- `context_builder.py` usa resultados de `analytics.py`;
- respostas determinísticas usam resultados calculados;
- textos da base são dados, não instruções;
- produtos ausentes não são criados.

## Testes

Os testes estão em [`../tests/`](../tests/).

```bash
ruff check .
pytest
```

Estado final:

```text
All checks passed!
148 passed
```

A integração real com Ollama é avaliada separadamente em
[`../evaluation/`](../evaluation/).

## Documentação relacionada

- [`README.md` principal](../README.md)
- [`01-documentacao-agente.md`](../docs/01-documentacao-agente.md)
- [`03-prompts.md`](../docs/03-prompts.md)
- [`04-metricas.md`](../docs/04-metricas.md)
- [`evaluation/README.md`](../evaluation/README.md)
