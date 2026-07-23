# Avaliação adversarial end-to-end

O executor usa a base local, o classificador, o construtor de contexto, o Ollama real e o validador final.

```bash
PYTHONPATH=. python evaluation/run_adversarial.py
```

Os relatórios são gravados em `evaluation/results/` e registram intenção, resposta, bloqueios, falhas e métricas de performance.

A suíte `pytest` continua sem depender do Ollama. Este executor deve ser usado separadamente porque seu resultado depende do modelo e do hardware locais.
