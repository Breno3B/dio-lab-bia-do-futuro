# Avaliação end-to-end

A suíte executa o fluxo completo da ClaraMente:

```text
pergunta
  ↓
classificação da intenção
  ↓
construção do contexto
  ↓
resposta determinística ou Ollama
  ↓
validação e fallback
  ↓
relatório JSON
```

A versão atual possui **65 casos**.

## Estrutura

```text
evaluation/
├── cases/
│   └── evaluation_cases.json
├── results/
│   └── evaluation_20260728_012712.json
├── README.md
├── run_evaluation.py
└── summarize_results.py
```

Outros relatórios podem existir em `results/` quando são feitas comparações.

## Distribuição

| Categoria | Quantidade |
|---|---:|
| Classificação de intenção | 15 |
| Respostas determinísticas | 12 |
| Solicitações ilícitas e segurança | 10 |
| Prompt injection | 8 |
| Catálogo e produtos | 8 |
| Fidelidade numérica | 5 |
| Dados ausentes e limitações | 4 |
| Atualidade e fora do escopo | 3 |
| **Total** | **65** |

## Pré-requisitos

- ambiente virtual ativado;
- dependências instaladas;
- Ollama em execução para casos generativos;
- modelo configurado e baixado.

```bash
ollama pull qwen3:4b
ollama list
```

## Execução

Suíte completa:

```bash
OLLAMA_TIMEOUT_SECONDS=360 \
OLLAMA_NUM_PREDICT=512 \
PYTHONPATH=. \
python evaluation/run_evaluation.py
```

Somente determinísticos:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py \
  --execution deterministic
```

Somente generativos:

```bash
OLLAMA_TIMEOUT_SECONDS=360 \
OLLAMA_NUM_PREDICT=512 \
PYTHONPATH=. \
python evaluation/run_evaluation.py \
  --execution generative
```

Somente uma categoria:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py \
  --category product_catalog
```

Arquivo de saída explícito:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py \
  --output evaluation/results/minha_baseline.json
```

## Schema dos casos

Campos obrigatórios:

| Campo | Finalidade |
|---|---|
| `id` | Identificador único. |
| `category` | Categoria. |
| `severity` | `low`, `medium`, `high` ou `critical`. |
| `execution` | `deterministic` ou `generative`. |
| `question` | Mensagem enviada. |
| `expected_intent` | Intenção esperada. |
| `expected_used_llm` | Uso esperado do modelo. |

Campos opcionais:

| Campo | Finalidade |
|---|---|
| `expected_blocked` | Estado final esperado. |
| `expected_values` | Valores calculados esperados. |
| `expected_value_tolerance` | Tolerância absoluta; padrão `0.01`. |
| `required_terms` | Termos obrigatórios. |
| `forbidden_terms` | Termos proibidos. |
| `notes` | Contexto do caso. |

## Execução esperada e real

O relatório mantém:

- contagens esperadas;
- contagens reais;
- divergências de execução;
- uso do LLM em cada caso.

Uma divergência gera falha explícita.

## Fallbacks e bloqueios

Um conteúdo gerado pode ser reprovado internamente e ainda resultar em uma
resposta final segura.

Exemplo:

```text
LLM gera conteúdo inválido
  ↓
validador reprova
  ↓
orquestrador descarta a saída
  ↓
fallback seguro
```

Por isso, `blocked: 0` não significa que o validador nunca atuou. Significa que
nenhuma interação final permaneceu bloqueada na baseline.

## Relatórios

Os arquivos são gravados em:

```text
evaluation/results/
```

Cada relatório registra:

- modelo;
- total, aprovados, reprovados e bloqueados;
- execução esperada e real;
- agrupamentos por categoria e severidade;
- motivos de falha;
- resposta final;
- avisos;
- métricas técnicas.

## Consolidação

O script exige pelo menos um relatório.

Relatório específico:

```bash
PYTHONPATH=. python evaluation/summarize_results.py \
  evaluation/results/evaluation_20260728_012712.json
```

Mais recente:

```bash
PYTHONPATH=. python evaluation/summarize_results.py \
  "$(ls -t evaluation/results/*.json | head -n 1)"
```

Todos:

```bash
PYTHONPATH=. python evaluation/summarize_results.py \
  evaluation/results/*.json
```

## Baseline final

```json
{
  "file": "evaluation/results/evaluation_20260728_012712.json",
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

## Testes do avaliador

```bash
pytest tests/test_evaluation_runner.py
```

A suíte unitária completa possui 148 testes aprovados.

## Critério de uso

- `pytest` é rápido e reproduzível;
- a avaliação determinística não depende do Ollama;
- a avaliação generativa depende do modelo, hardware e configuração;
- mudanças em modelo, prompt, schema, validador ou limites exigem nova
  baseline;
- relatórios de modelos ou configurações diferentes devem permanecer
  separados.
