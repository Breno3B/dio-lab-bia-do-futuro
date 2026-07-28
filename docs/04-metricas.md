# Avaliação e Métricas — ClaraMente

## Objetivo

A avaliação verifica se a ClaraMente produz respostas corretas, seguras,
fundamentadas e coerentes com o fluxo planejado.

Ela separa três níveis:

1. testes automatizados;
2. avaliação end-to-end;
3. revisão humana.

## Testes automatizados

Comandos:

```bash
ruff check .
pytest
pytest --cov=src --cov-report=term-missing
```

Resultado final:

```text
All checks passed!
148 passed in 0.65s
```

Os testes usam clientes simulados para não depender do Ollama.

Principais áreas cobertas:

- carregamento e validação dos dados;
- cálculos financeiros;
- classificação de intenção;
- contexto dinâmico;
- respostas determinísticas;
- configuração;
- cliente Ollama;
- prompts;
- validação pós-geração;
- fallbacks de produtos e histórico;
- executor da avaliação;
- consolidação de relatórios.

## Avaliação end-to-end

Fluxo:

```text
pergunta
  ↓
classificação
  ↓
contexto
  ↓
resposta determinística ou Ollama
  ↓
validação e fallback
  ↓
relatório JSON
```

Os casos ficam em
[`../evaluation/cases/evaluation_cases.json`](../evaluation/cases/evaluation_cases.json).

## Distribuição dos 65 casos

| Categoria | Quantidade | Resultado final |
|---|---:|---:|
| Classificação de intenção | 15 | 15 aprovados |
| Respostas determinísticas | 12 | 12 aprovados |
| Solicitações ilícitas e segurança | 10 | 10 aprovados |
| Prompt injection | 8 | 8 aprovados |
| Catálogo e produtos | 8 | 8 aprovados |
| Fidelidade numérica | 5 | 5 aprovados |
| Dados ausentes e limitações | 4 | 4 aprovados |
| Atualidade e fora do escopo | 3 | 3 aprovados |
| **Total** | **65** | **65 aprovados** |

## Baseline final

Relatório:

```text
evaluation/results/evaluation_20260728_012712.json
```

Configuração:

| Item | Valor |
|---|---|
| Modelo | `qwen3:4b` |
| Casos | 65 |
| Execuções determinísticas esperadas | 51 |
| Execuções generativas esperadas | 14 |
| `OLLAMA_NUM_PREDICT` | 512 |
| `OLLAMA_TIMEOUT_SECONDS` | 360 |

Resultado consolidado:

```json
{
  "model": "qwen3:4b",
  "total": 65,
  "passed": 65,
  "failed": 0,
  "blocked": 0,
  "execution_mismatches": 0,
  "expected_execution_counts": {
    "deterministic": 51,
    "generative": 14
  },
  "actual_execution_counts": {
    "deterministic": 51,
    "generative": 14
  },
  "critical_failures": [],
  "numeric_failures": []
}
```

## Métricas principais

### Taxa de aprovação

```text
casos aprovados / total de casos
```

Baseline final:

```text
65 / 65 = 100%
```

### Correspondência de execução

Verifica se cada caso percorreu o caminho esperado:

- determinístico;
- generativo.

Baseline final:

```text
execution_mismatches = 0
```

### Fidelidade numérica

Compara valores de `response.context.calculated_results` com
`expected_values`, usando tolerância absoluta.

Baseline final:

```text
numeric_failures = []
```

### Segurança

Avalia:

- solicitações ilícitas;
- prompt injection;
- produtos inventados;
- garantias de retorno;
- dados atuais sem fonte;
- exposição de configurações internas;
- valores não fundamentados.

Baseline final:

```text
critical_failures = []
```

### Catálogo

Verifica:

- JSON válido;
- resposta não vazia;
- lista `produtos_mencionados`;
- produto existente no catálogo;
- produto permitido no contexto;
- produto declarado quando citado no texto;
- uso do fallback em pedidos adversariais.

### Histórico

Verifica:

- uso esperado do LLM;
- limite de resposta;
- ausência de valores inventados;
- proteção contra acesso a instruções internas;
- fallback com registros relevantes.

### Métricas técnicas

Cada caso pode registrar:

- `total_ms`;
- `validation_ms`;
- `classification_ms`;
- `context_ms`;
- `deterministic_ms`;
- `prompt_ms`;
- `llm_ms`;
- `response_validation_ms`;
- `prompt_eval_count`;
- `eval_count`;
- duração da avaliação do prompt;
- duração da geração;
- duração do carregamento;
- tokens por segundo;
- tamanho de entrada e saída.

Essas métricas ajudam a comparar configurações, mas não substituem a avaliação
de qualidade e segurança.

## Execução

Suíte completa:

```bash
OLLAMA_TIMEOUT_SECONDS=360 \
OLLAMA_NUM_PREDICT=512 \
PYTHONPATH=. \
python evaluation/run_evaluation.py
```

Somente uma categoria:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py \
  --category product_catalog
```

Somente um tipo de execução:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py \
  --execution deterministic
```

## Consolidação

O consolidador exige um ou mais caminhos:

```bash
PYTHONPATH=. python evaluation/summarize_results.py \
  evaluation/results/evaluation_20260728_012712.json
```

Relatório mais recente:

```bash
PYTHONPATH=. python evaluation/summarize_results.py \
  "$(ls -t evaluation/results/*.json | head -n 1)"
```

Todos os relatórios:

```bash
PYTHONPATH=. python evaluation/summarize_results.py \
  evaluation/results/*.json
```

## Critérios de aceitação

A versão é considerada aprovada quando:

- Ruff passa sem erros;
- a suíte unitária passa;
- não há falha crítica;
- não há falha numérica;
- a execução real coincide com a esperada;
- consultas legítimas não terminam em bloqueio técnico;
- solicitações adversariais recebem recusa, fallback ou resposta segura;
- o modelo e a configuração estão registrados.

## Interpretação dos bloqueios

Um conteúdo reprovado pelo validador não precisa resultar em uma interação
final marcada como bloqueada.

Nos fluxos de produtos e histórico, o sistema pode:

1. detectar uma violação;
2. descartar a saída do modelo;
3. apresentar fallback determinístico;
4. registrar um aviso;
5. concluir o caso sem expor o conteúdo inseguro.

Por isso, a baseline final possui `blocked: 0`, embora alguns casos tenham
acionado fallbacks internos.

## Limitações da avaliação

- cobre o conjunto atual de 65 casos;
- usa uma base fictícia;
- não garante comportamento para toda pergunta possível;
- resultados generativos dependem do modelo e do hardware;
- uma troca de prompt, modelo ou limite exige nova baseline;
- 100% neste conjunto não equivale a ausência de risco em produção.

## Melhoria contínua

Após mudanças relevantes:

1. executar `ruff check .`;
2. executar `pytest`;
3. executar casos determinísticos;
4. executar casos generativos;
5. executar a suíte completa;
6. consolidar o relatório;
7. comparar com a baseline anterior;
8. revisar respostas e métricas;
9. versionar o relatório aprovado.
