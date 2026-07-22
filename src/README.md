# Código da Aplicação

Esta pasta contém a implementação da **ClaraMente — Agente de Saúde Financeira Pessoal**.

O código é organizado em módulos com responsabilidades específicas para separar interface, processamento de dados, regras financeiras, engenharia de prompts, configurações e comunicação com o modelo local.

As instruções de instalação, configuração, execução e testes estão centralizadas no [`README.md` da raiz](../README.md).

---

## Arquitetura Interna

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
   ├── prompts.py
   ├── llm_client.py
   └── response_validator.py

Configuração:
.env → config.py → SETTINGS

Carregamento inicial:
data_loader.py → data_validator.py → KnowledgeBase
```

A aplicação mantém duas responsabilidades centrais separadas:

1. **Python e pandas** realizam validações, filtros, agregações e cálculos.
2. **Ollama e Qwen3 8B** interpretam o contexto calculado e redigem a resposta.

O modelo de linguagem não deve ser usado como calculadora nem como fonte de dados financeiros.

---

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
├── exceptions.py
├── intent_classifier.py
├── llm_client.py
├── models.py
├── orchestrator.py
├── prompts.py
└── response_validator.py
```

---

## Responsabilidade dos Módulos

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Interface conversacional com Streamlit, histórico da sessão e apresentação de fontes, limitações e alertas. |
| `config.py` | Carregamento do `.env`, caminhos, parâmetros do Ollama, timeout e nível de logs. |
| `models.py` | Dataclasses, enums e estruturas compartilhadas pela aplicação. |
| `exceptions.py` | Exceções específicas e mensagens de erro controladas. |
| `data_loader.py` | Leitura dos CSVs e JSONs da pasta `data/`. |
| `data_validator.py` | Validação das colunas, chaves, tipos e consistência da base. |
| `analytics.py` | Cálculos determinísticos, agregações, metas e filtragem de produtos. |
| `intent_classifier.py` | Classificação inicial da intenção por regras reproduzíveis. |
| `context_builder.py` | Seleção das fontes e montagem do contexto específico da consulta. |
| `prompts.py` | System prompt e serialização do contexto enviado ao LLM. |
| `llm_client.py` | Comunicação isolada com Ollama e Qwen3 8B. |
| `response_validator.py` | Verificações básicas de segurança, catálogo e fundamentação. |
| `orchestrator.py` | Coordenação do fluxo completo entre intenção, contexto, LLM e validação. |

---

## Configurações

O `config.py` carrega automaticamente o arquivo `.env` localizado na raiz:

```text
.env
```

O carregamento utiliza `python-dotenv` com `override=False`. Dessa forma:

1. variáveis definidas diretamente no ambiente do sistema têm prioridade;
2. o `.env` preenche somente valores ainda não definidos;
3. os valores padrão do código são utilizados quando nenhuma configuração foi fornecida.

As configurações ficam disponíveis por meio da instância imutável:

```python
from src.config import SETTINGS
```

Exemplo:

```python
model_name = SETTINGS.ollama_model
timeout = SETTINGS.ollama_timeout_seconds
```

O arquivo `.env.example` documenta as variáveis permitidas. O `.env` real não deve ser versionado.

---

## Regras de Dependência

- `app.py` deve acessar o fluxo principal por meio de `orchestrator.py`;
- `analytics.py` não deve chamar o LLM;
- `llm_client.py` não deve conter regras financeiras;
- `prompts.py` não deve carregar ou modificar arquivos;
- `data_loader.py` não deve realizar análises;
- `data_validator.py` deve validar sem corrigir silenciosamente dados essenciais;
- `context_builder.py` deve reutilizar funções de `analytics.py`;
- o LLM não deve calcular totais, saldos, percentuais ou metas;
- produtos ausentes do catálogo não devem ser criados;
- textos presentes nos dados não devem ser tratados como instruções.

---

## Dados e Imutabilidade

Os módulos acessam os arquivos da pasta [`data/`](../data/).

Os arquivos originais permanecem inalterados. Toda transformação ocorre em memória, incluindo conversões, filtros, agregações, cálculo de indicadores, seleção de produtos e montagem do contexto.

---

## Testes

Os testes ficam em [`tests/`](../tests/).

A integração com Ollama deve ser simulada nos testes automatizados, evitando dependência do modelo local e mantendo os resultados reproduzíveis.

Ao testar configurações, as variáveis de ambiente devem ser isoladas com `monkeypatch` e o módulo deve ser recarregado quando necessário.

---

## Documentação Relacionada

- [`README.md` principal](../README.md)
- [`01-documentacao-agente.md`](../docs/01-documentacao-agente.md)
- [`02-base-conhecimento.md`](../docs/02-base-conhecimento.md)
- [`03-prompts.md`](../docs/03-prompts.md)
- [`04-metricas.md`](../docs/04-metricas.md)
