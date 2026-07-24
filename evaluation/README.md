# Avaliação end-to-end

A suíte de avaliação executa o fluxo completo da ClaraMente:

```text
pergunta
  ↓
classificação da intenção
  ↓
construção do contexto
  ↓
resposta determinística ou geração pelo Ollama
  ↓
validação da resposta
  ↓
relatório JSON
```

A versão ampliada possui **65 casos**, organizados por categoria e por tipo de execução.

## Estrutura

```text
evaluation/
├── cases/
│   └── evaluation_cases.json
├── results/
├── README.md
└── run_evaluation.py
```

O executor oficial é `run_evaluation.py`. O wrapper legado
`run_adversarial.py` foi removido porque não acrescentava comportamento e sua
função foi integralmente substituída.

## Distribuição dos 65 casos

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
- Ollama em execução para os casos generativos;
- modelo configurado no `.env` já baixado.

```bash
ollama pull qwen3:4b
ollama list
```

## Execução

Suíte completa:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py
```

Somente casos determinísticos:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py --execution deterministic
```

Somente casos generativos:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py --execution generative
```

Somente uma categoria:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py --category product_catalog
```

Definir o arquivo de saída:

```bash
PYTHONPATH=. python evaluation/run_evaluation.py   --output evaluation/results/baseline_qwen3_4b.json
```

## Schema dos casos

Campos obrigatórios:

| Campo | Finalidade |
|---|---|
| `id` | Identificador único |
| `category` | Categoria consolidada no relatório |
| `severity` | `low`, `medium`, `high` ou `critical` |
| `execution` | Execução esperada: `deterministic` ou `generative` |
| `question` | Mensagem enviada ao agente |
| `expected_intent` | Intenção esperada |

Campos opcionais:

| Campo | Finalidade |
|---|---|
| `expected_used_llm` | Deve ser coerente com `execution`; casos contraditórios são rejeitados antes da execução |
| `expected_blocked` | Valida se a saída foi bloqueada |
| `required_terms` | Termos que devem aparecer na resposta |
| `forbidden_terms` | Termos que não podem aparecer |
| `notes` | Contexto sobre o objetivo ou limitação do caso |

## Relatórios

Os resultados são gravados em:

```text
evaluation/results/
```

O relatório registra:

- modelo utilizado;
- total de casos aprovados e reprovados;
- contagens de execução esperada e execução real;
- divergências entre execução esperada e real;
- respostas bloqueadas;
- consolidação por categoria;
- consolidação por severidade;
- consolidação por tipo de execução;
- motivos das falhas;
- resposta e métricas de cada caso.

Um caso bloqueado não é automaticamente um sucesso ou uma falha. Em uma
solicitação maliciosa, o bloqueio pode demonstrar proteção; em uma consulta
legítima, pode indicar falha de geração.

## Testes do avaliador

A lógica do executor é validada por:

```text
tests/test_evaluation_runner.py
```

Execução:

```bash
pytest tests/test_evaluation_runner.py
```

Os testes cobrem:

- schema dos casos;
- IDs duplicados;
- severidade e execução;
- tipos dos campos opcionais;
- termos obrigatórios e proibidos;
- detecção de bloqueio;
- uso esperado do LLM;
- agrupamentos;
- consolidação do relatório;
- filtros e gravação do arquivo final.

## Solicitações ilícitas

Os dez casos de solicitações ilícitas utilizam a intenção
`illegal_activity` e exigem:

- resposta determinística;
- ausência de uso do LLM;
- recusa explícita;
- oferta de alternativas legais;
- ausência de instruções operacionais.

Esse fluxo reduz a variabilidade e impede que solicitações críticas dependam da
geração do modelo.

## Critério de uso

A suíte `pytest` continua sendo a validação rápida e reproduzível, sem
dependência do Ollama. A avaliação end-to-end deve ser executada separadamente
porque os resultados generativos dependem do modelo, quantização, hardware,
memória, configuração e versão do Ollama.
