# Código da Aplicação

Esta pasta contém a implementação da **ClaraMente — Agente de Saúde Financeira Pessoal**.

O código é organizado em módulos com responsabilidades específicas para separar interface, processamento de dados, regras financeiras, engenharia de prompts e comunicação com o modelo local.

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

Carregamento inicial:
data_loader.py → data_validator.py → KnowledgeBase
```

O fluxo mantém duas responsabilidades centrais separadas:

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
| `config.py` | Caminhos, parâmetros do Ollama, timeout e configurações de logs. |
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

## Fluxo de uma Pergunta

1. `app.py` recebe a mensagem do usuário.
2. `orchestrator.py` inicia o processamento.
3. `intent_classifier.py` identifica a intenção provável.
4. `context_builder.py` escolhe as fontes e os cálculos necessários.
5. `analytics.py` produz os resultados numéricos.
6. `prompts.py` combina o system prompt, o contexto estruturado e a pergunta.
7. `llm_client.py` envia as mensagens ao Qwen3 8B por meio do Ollama.
8. `response_validator.py` procura sinais de resposta insegura ou não fundamentada.
9. `app.py` exibe a resposta, as fontes, limitações e possíveis alertas.

---

## Regras de Dependência

Para preservar a separação de responsabilidades:

- `app.py` deve acessar o fluxo principal por meio de `orchestrator.py`;
- `analytics.py` não deve chamar o LLM;
- `llm_client.py` não deve conter regras financeiras;
- `prompts.py` não deve carregar ou modificar arquivos;
- `data_loader.py` não deve realizar análises;
- `data_validator.py` deve validar sem corrigir silenciosamente dados essenciais;
- `context_builder.py` deve reutilizar funções de `analytics.py`, sem duplicar cálculos;
- o LLM não deve calcular totais, saldos, percentuais ou progresso de metas;
- produtos ausentes do catálogo não devem ser criados pelo código ou pelo modelo;
- textos presentes nos dados não devem ser tratados como instruções.

---

## Dados e Imutabilidade

Os módulos acessam os arquivos da pasta [`data/`](../data/).

Os arquivos originais devem permanecer inalterados. Toda transformação ocorre em memória, incluindo:

- conversão de datas;
- normalização de textos;
- conversão de valores;
- filtros por período;
- agregações;
- cálculo de indicadores;
- seleção de produtos;
- montagem do contexto.

Esse comportamento melhora a rastreabilidade e permite reproduzir as análises.

---

## Contexto Enviado ao LLM

O modelo não recebe toda a base em todas as perguntas.

O `context_builder.py` seleciona somente as informações necessárias:

```text
INTENÇÃO
FONTES CONSULTADAS
PERÍODO ANALISADO
FILTROS APLICADOS
RESULTADOS CALCULADOS
DADOS RELEVANTES DO PERFIL
PRODUTOS ENCONTRADOS
INCONSISTÊNCIAS
DADOS AUSENTES
LIMITAÇÕES
```

Os resultados calculados pela aplicação são a referência numérica da resposta. Caso o modelo identifique uma possível inconsistência, deve sinalizá-la sem recalcular ou substituir os valores.

---

## Como Adicionar uma Nova Intenção

Exemplo: análise de despesas recorrentes.

1. Inclua o novo valor no enum de intenções.
2. Adicione termos ou regras em `intent_classifier.py`.
3. Implemente o cálculo determinístico em `analytics.py`.
4. Atualize `context_builder.py` para selecionar as fontes e montar o resultado.
5. Adicione exemplos ou edge cases em [`docs/03-prompts.md`](../docs/03-prompts.md).
6. Crie testes unitários para classificação, cálculo e contexto.
7. Atualize esta documentação caso um novo módulo seja criado.

A implementação deve começar com uma função pequena e testável antes de alterar o fluxo completo.

---

## Como Adicionar um Novo Arquivo de Dados

1. Documente o arquivo em [`docs/02-base-conhecimento.md`](../docs/02-base-conhecimento.md).
2. Adicione o caminho em `config.py`.
3. Implemente a leitura em `data_loader.py`.
4. Defina a estrutura correspondente em `models.py`, quando necessário.
5. Adicione as validações em `data_validator.py`.
6. Selecione somente os campos necessários em `context_builder.py`.
7. Crie testes com dados válidos e inválidos.

Nunca inclua dados pessoais ou financeiros reais no repositório público.

---

## Tratamento de Erros

Use as exceções de `exceptions.py` para erros esperados:

- arquivo ausente;
- estrutura inválida;
- base inconsistente;
- Ollama indisponível;
- modelo não instalado;
- falha de geração.

Erros conhecidos devem resultar em mensagens compreensíveis na interface. Exceções inesperadas devem ser registradas nos logs sem expor o conteúdo completo dos dados.

---

## Testes

Os testes ficam em [`tests/`](../tests/) e devem refletir a estrutura dos módulos.

| Módulo | Testes principais |
|---|---|
| `data_loader.py` | Arquivos existentes, ausentes e formatos inválidos. |
| `data_validator.py` | Campos obrigatórios, tipos, duplicidades e conflitos. |
| `analytics.py` | Totais, saldo, categorias, metas e produtos. |
| `intent_classifier.py` | Intenções conhecidas, ambíguas e fora do escopo. |
| `context_builder.py` | Fontes, filtros, resultados e limitações. |
| `response_validator.py` | Frases proibidas, produtos ausentes e avisos esperados. |
| `orchestrator.py` | Fluxo integrado com cliente LLM simulado. |

A integração com Ollama deve ser simulada nos testes automatizados para evitar dependência do modelo local e tornar os resultados reproduzíveis.

---

## Arquivos Locais

O `.gitignore` da raiz impede o versionamento de:

- ambientes virtuais;
- caches do Python e das ferramentas;
- arquivos `.env`;
- segredos do Streamlit;
- logs e saídas locais;
- arquivos grandes de modelos;
- configurações pessoais de IDE.

Os dados mockados da pasta `data/` e o arquivo `.env.example` permanecem versionados.

---

## Boas Práticas Adotadas

- type hints;
- dataclasses e enums para estruturas compartilhadas;
- configurações centralizadas;
- funções pequenas e com responsabilidade única;
- dependências direcionadas entre módulos;
- exceções específicas;
- logs sem dados sensíveis;
- cálculos determinísticos fora do LLM;
- validação antes e depois da geração;
- testes sem dependência do serviço externo;
- dados mockados;
- catálogo fechado de produtos.

---

## Documentação Relacionada

- [`README.md` principal](../README.md)
- [`01-documentacao-agente.md`](../docs/01-documentacao-agente.md)
- [`02-base-conhecimento.md`](../docs/02-base-conhecimento.md)
- [`03-prompts.md`](../docs/03-prompts.md)
- [`04-metricas.md`](../docs/04-metricas.md)
