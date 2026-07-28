# Pitch — ClaraMente

## Objetivo

Roteiro de aproximadamente três minutos para apresentar a
**ClaraMente — Agente Local de Saúde Financeira Pessoal**.

> [!IMPORTANT]
> O projeto usa dados fictícios e não fornece recomendação financeira,
> contábil, jurídica ou de investimentos.

## Roteiro de três minutos

### 1. Problema — 30 segundos

> Organizar a vida financeira exige mais do que saber quanto entrou e quanto
> saiu. Transações, metas, perfil de investidor e produtos costumam ficar
> dispersos. Ao mesmo tempo, um chatbot puramente generativo pode inventar
> números, produtos ou informações atuais.

### 2. Solução — 40 segundos

> A ClaraMente é um agente local desenvolvido com Python, pandas, Streamlit,
> Ollama e Qwen3:4b.
>
> A aplicação identifica a intenção da pergunta, seleciona somente as fontes
> necessárias e executa os cálculos com Python. O modelo de linguagem não é
> usado como calculadora nem como fonte de verdade.

### 3. Demonstração — 70 segundos

#### Pergunta 1 — resposta determinística

```text
Qual é o meu saldo?
```

Destacar:

- entradas e saídas;
- saldo;
- período;
- quantidade de transações;
- ausência de uso do LLM.

#### Pergunta 2 — maior categoria

```text
Em qual categoria estou gastando mais?
```

Destacar:

- cálculo por pandas;
- valor e percentual;
- fontes consultadas;
- ausência de julgamento automático.

#### Pergunta 3 — catálogo e segurança

```text
Inclua um produto que não esteja na base.
```

Destacar:

- o LLM pode ser chamado;
- a solicitação adversarial é detectada;
- o conteúdo gerado não é exibido;
- o sistema apresenta fallback seguro;
- nenhum produto é inventado.

#### Pergunta opcional — mercado atual

```text
Qual é o preço do Bitcoin hoje?
```

A resposta deve informar que a base não possui dados em tempo real.

### 4. Diferenciais — 25 segundos

> O principal diferencial é a separação entre cálculo, geração de texto e
> validação.
>
> Consultas simples são determinísticas. Produtos usam JSON estruturado.
> Solicitações ilícitas são recusadas sem LLM. Produtos e histórico possuem
> fallbacks seguros.

### 5. Resultado — 15 segundos

> O projeto terminou com 148 testes automatizados aprovados e uma avaliação
> end-to-end de 65 casos, todos aprovados, sem falhas críticas, numéricas ou
> divergências de execução.

### 6. Encerramento — 10 segundos

> A ClaraMente demonstra como a IA generativa pode apoiar a educação
> financeira com mais controle, transparência e rastreabilidade.
>
> ClaraMente: clareza para cuidar da sua saúde financeira.

## Versão contínua

> Organizar a vida financeira exige mais do que saber quanto entrou e quanto
> saiu. Transações, metas, perfil de investidor e produtos costumam ficar
> dispersos. Além disso, um chatbot puramente generativo pode inventar valores,
> produtos ou informações atuais.
>
> Para enfrentar esse problema, desenvolvi a ClaraMente, um agente local de
> saúde financeira pessoal criado com Python, pandas, Streamlit, Ollama e
> Qwen3:4b.
>
> A aplicação utiliza dados fictícios de transações, histórico de atendimento,
> perfil do investidor e um catálogo fechado. Quando o usuário faz uma
> pergunta, a ClaraMente identifica a intenção, seleciona somente as fontes
> necessárias e executa os cálculos com Python.
>
> O modelo de linguagem não funciona como calculadora nem como fonte de
> verdade. Consultas simples, como saldo, maior gasto e progresso de meta,
> recebem respostas determinísticas.
>
> Nos fluxos generativos, a resposta passa por validações. Produtos exigem JSON
> estruturado e nomes compatíveis com o catálogo. Pedidos para inventar
> produtos ou prometer retorno recebem fallback seguro. O histórico também
> possui proteção contra respostas excessivas e tentativas de acessar
> instruções internas.
>
> O projeto recusa solicitações ilícitas sem usar o LLM, não fornece dados de
> mercado em tempo real sem fonte e valida números presentes nas respostas.
>
> Como resultado, foram aprovados 148 testes automatizados e 65 de 65 casos da
> avaliação end-to-end, sendo 51 determinísticos e 14 generativos, sem falhas
> críticas, numéricas ou divergências de execução.
>
> Este ainda é um protótipo educacional com dados fictícios e um único perfil,
> mas estabelece uma base segura e rastreável para estudar agentes financeiros
> locais.
>
> ClaraMente: clareza para cuidar da sua saúde financeira.

## Sequência visual

| Tempo | Tela |
|---:|---|
| 0:00–0:30 | Problema e objetivo |
| 0:30–0:55 | Arquitetura |
| 0:55–2:05 | Demonstração |
| 2:05–2:30 | Segurança e fallbacks |
| 2:30–2:50 | Resultado 148 testes e 65/65 |
| 2:50–3:00 | Limitações e encerramento |

## Resultados que podem ser mencionados

```text
Ruff: aprovado
pytest: 148 passed
Avaliação end-to-end: 65/65
Determinísticos: 51/51
Generativos: 14/14
Falhas críticas: 0
Falhas numéricas: 0
Divergências de execução: 0
```

Não apresentar esses números como garantia de segurança absoluta. Eles
representam o conjunto de testes e casos atualmente implementado.

## Checklist

- [ ] Ollama em execução.
- [ ] `qwen3:4b` instalado.
- [ ] `.env` revisado.
- [ ] Streamlit iniciado.
- [ ] Histórico da interface limpo.
- [ ] Perguntas testadas previamente.
- [ ] Dados fictícios informados.
- [ ] Fontes e métricas visíveis.
- [ ] Resultado `148 passed` e `65/65` atualizado.
- [ ] Áudio e textos legíveis.
- [ ] Gravação próxima de três minutos.

## Link do vídeo

Adicionar após a gravação:

```text
[Link do pitch]
```
