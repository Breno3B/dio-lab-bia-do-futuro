# Avaliação adversarial end-to-end

O executor adversarial testa o fluxo completo da ClaraMente com o modelo real:

```text
pergunta
→ classificação da intenção
→ construção do contexto
→ geração pelo Ollama
→ validação da resposta
→ relatório
```

## Pré-requisitos

- ambiente virtual ativado;
- dependências instaladas;
- Ollama em execução;
- modelo configurado no `.env` já baixado.

Exemplo:

```bash
ollama pull qwen3:4b
ollama list
```

## Execução

Na raiz do projeto:

```bash
PYTHONPATH=. python evaluation/run_adversarial.py
```

## Casos avaliados

Os casos ficam em:

```text
evaluation/adversarial_cases.json
```

Cada caso pode avaliar aspectos como:

- prompt injection;
- tentativa de revelar o system prompt;
- produto ou valor inventado;
- atividade financeira ilícita;
- ausência de dados;
- uso de informação atual sem fonte;
- exposição de contexto interno.

## Relatórios

Os resultados são gravados em:

```text
evaluation/results/
```

O relatório registra, quando disponível:

- modelo;
- pergunta;
- intenção detectada;
- resposta;
- bloqueios e avisos;
- critérios aprovados e reprovados;
- tempo total;
- tokens de entrada e saída;
- velocidade de geração.

## Critério de uso

A suíte `pytest` não depende do Ollama e deve ser usada para validações rápidas e
reproduzíveis.

A avaliação adversarial deve ser executada separadamente porque os resultados
dependem de:

- modelo;
- quantização;
- hardware;
- memória disponível;
- contexto configurado;
- temperatura;
- versão do Ollama.

## Comparação entre modelos

Para comparar modelos, altere `OLLAMA_MODEL` no `.env`, confirme que o modelo
está instalado e execute novamente o avaliador.

Exemplo:

```dotenv
OLLAMA_MODEL=qwen3:4b
```

Depois:

```bash
PYTHONPATH=. python evaluation/run_adversarial.py
```

Registre separadamente os resultados de cada modelo para não misturar
baselines.

## Hardware de referência

As recomendações atuais foram avaliadas para:

- Intel Core i7-7500U;
- 15,51 GiB de RAM;
- NVIDIA GeForce 940MX;
- Pop!_OS 24.04 LTS.

Nesse equipamento, `qwen3:4b` é o modelo inicial recomendado. Modelos maiores
podem apresentar maior latência ou uso de swap.
