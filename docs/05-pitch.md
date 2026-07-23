# Pitch — ClaraMente

## Objetivo

Este documento apresenta um roteiro de aproximadamente três minutos para demonstrar a **ClaraMente — Agente de Saúde Financeira Pessoal**.

A apresentação deve priorizar:

- o problema enfrentado pelo usuário;
- a solução desenvolvida;
- uma demonstração prática;
- os diferenciais técnicos e de segurança;
- as limitações do protótipo.

> [!IMPORTANT]
> A ClaraMente é um projeto educacional. Os dados são fictícios e as respostas não representam recomendação financeira, contábil, jurídica ou de investimentos.

---

## Roteiro de três minutos

### 1. Abertura e problema — 30 segundos

> Organizar a vida financeira não depende apenas de saber quanto entrou e quanto saiu. As informações sobre despesas, metas, perfil de investidor e produtos disponíveis normalmente ficam dispersas, dificultando uma visão clara da situação.
>
> Além disso, um chatbot puramente generativo pode inventar valores, produtos ou características financeiras. Foi a partir desse problema que surgiu a ClaraMente.

### 2. Solução — 45 segundos

> A ClaraMente é uma agente local de saúde financeira pessoal desenvolvida com Python, pandas, Streamlit e Ollama.
>
> Ela analisa uma base de dados fictícia composta por transações, histórico de atendimento, perfil do investidor e catálogo de produtos. A aplicação identifica a intenção da pergunta, seleciona apenas as fontes necessárias e realiza os cálculos financeiros com Python.
>
> O modelo de linguagem não é usado como calculadora nem como fonte de verdade. Ele recebe resultados já calculados e os transforma em explicações claras e contextualizadas.

### 3. Demonstração — 60 segundos

Durante a gravação, mostrar a interface do Streamlit e executar três perguntas.

#### Pergunta 1 — resposta determinística

```text
Qual é o meu saldo no período?
```

Destacar:

- valor de entradas;
- valor de saídas;
- saldo calculado;
- período e quantidade de transações;
- resposta rápida sem uso do LLM.

#### Pergunta 2 — análise de gastos

```text
Em que categoria estou gastando mais?
```

Destacar:

- cálculo feito por pandas;
- categoria e percentual;
- ausência de julgamento automático;
- indicação das fontes e do período analisado.

#### Pergunta 3 — segurança e catálogo fechado

```text
Quais produtos combinam com meu perfil?
```

Destacar:

- uso do perfil e do catálogo;
- impossibilidade de inventar produtos;
- explicação dos critérios de compatibilidade;
- bloqueio da resposta quando o modelo viola as regras.

Uma opção adicional é demonstrar:

```text
Qual é a taxa Selic hoje?
```

A resposta deve informar que a base não possui dados em tempo real, em vez de inventar um valor.

### 4. Diferenciais técnicos — 30 segundos

> O principal diferencial da ClaraMente é a separação entre cálculo e geração de texto.
>
> Consultas simples utilizam respostas determinísticas. Nos casos em que o LLM agrega valor, a aplicação monta um contexto mínimo e valida a saída antes de apresentá-la.
>
> O projeto também inclui proteção contra prompt injection, catálogo fechado, validação de valores monetários e percentuais, testes automatizados e avaliação adversarial entre modelos.

### 5. Impacto e encerramento — 15 segundos

> A ClaraMente demonstra como a IA generativa pode apoiar a educação financeira com mais transparência e controle, sem tratar o modelo como fonte absoluta.
>
> O protótipo ainda utiliza dados fictícios e um único perfil, mas estabelece uma base segura e rastreável para evoluções futuras.
>
> ClaraMente: clareza para cuidar da sua saúde financeira.

---

## Versão contínua para gravação

> Organizar a vida financeira não depende apenas de saber quanto entrou e quanto saiu. Informações sobre despesas, metas, perfil de investidor e produtos normalmente ficam dispersas, dificultando uma visão clara da situação. Além disso, um chatbot puramente generativo pode inventar valores ou características financeiras.
>
> Para enfrentar esse problema, desenvolvi a ClaraMente, uma agente local de saúde financeira pessoal criada com Python, pandas, Streamlit e Ollama.
>
> A aplicação utiliza dados fictícios de transações, histórico de atendimento, perfil do investidor e um catálogo fechado de produtos. Quando o usuário faz uma pergunta, a ClaraMente identifica a intenção, seleciona somente as fontes necessárias e executa os cálculos com Python.
>
> Isso significa que o modelo de linguagem não funciona como calculadora nem como fonte de verdade. Ele recebe resultados estruturados e é utilizado somente quando a interpretação em linguagem natural agrega valor.
>
> Na interface, posso perguntar qual é o saldo do período. A resposta apresenta entradas, saídas, saldo e período analisado de forma determinística e rápida. Também posso perguntar em qual categoria ocorreu o maior gasto, e a aplicação mostra o resultado calculado com pandas, sem julgar automaticamente o comportamento do usuário.
>
> Em análises de produtos, a ClaraMente considera o perfil fictício e somente os itens existentes no catálogo. Caso o modelo invente um produto, altere um valor ou desrespeite o formato esperado, a resposta pode ser bloqueada pelo validador.
>
> O projeto também trata tentativas de prompt injection, recusa dados atuais sem uma fonte autorizada, diferencia informação ausente de valor zero e registra métricas de latência, tokens e velocidade de geração.
>
> Como resultado, a ClaraMente demonstra uma arquitetura em que cálculos determinísticos, IA generativa e validações trabalham em conjunto para produzir respostas mais seguras, explicáveis e rastreáveis.
>
> Este ainda é um protótipo educacional, com dados totalmente fictícios e um único perfil. Mesmo assim, ele estabelece uma base sólida para estudar agentes financeiros locais e responsáveis.
>
> ClaraMente: clareza para cuidar da sua saúde financeira.

---

## Sugestão de sequência visual

| Tempo | Tela |
|---:|---|
| 0:00–0:30 | Título, problema e objetivo |
| 0:30–0:55 | Diagrama simplificado da arquitetura |
| 0:55–1:55 | Demonstração no Streamlit |
| 1:55–2:25 | Segurança, validação e testes |
| 2:25–2:45 | Resultados adversariais iniciais |
| 2:45–3:00 | Limitações, impacto e encerramento |

---

## Resultados que podem ser mencionados

Na baseline atual:

- foram executados cinco casos adversariais;
- `qwen3:8b` e `qwen3:4b` aprovaram os cinco casos;
- quatro casos foram resolvidos deterministicamente;
- o único caso generativo foi bloqueado nos dois modelos;
- o bloqueio impediu que uma resposta insegura ou inválida chegasse ao usuário.

Apresente esses resultados como evidência da camada de proteção, não como comprovação definitiva da qualidade dos modelos.

---

## Checklist antes da gravação

- [ ] Confirmar que o Ollama está em execução.
- [ ] Confirmar que o modelo configurado está instalado.
- [ ] Iniciar o Streamlit antes da gravação.
- [ ] Limpar o histórico da conversa.
- [ ] Testar previamente as perguntas da demonstração.
- [ ] Evitar depender de uma geração longa ao vivo.
- [ ] Mostrar fontes, período, validações e métricas.
- [ ] Informar que os dados são fictícios.
- [ ] Informar que o agente não substitui profissionais.
- [ ] Manter a gravação próxima de três minutos.
- [ ] Garantir que textos e valores estejam legíveis.
- [ ] Revisar áudio, cortes e enquadramento.

---

## Link do vídeo

Adicionar após a gravação:

```text
[Link do pitch]
```
