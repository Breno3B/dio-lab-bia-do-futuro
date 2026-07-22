# Execução local da ClaraMente

## Pré-requisitos

- Python 3.11 ou superior;
- Ollama instalado e em execução;
- modelo `qwen3:8b` disponível localmente.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:8b
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

## Execução

A partir da raiz do projeto:

```bash
streamlit run src/app.py
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Observações

- Os quatro arquivos originais devem permanecer na pasta `data/`.
- A aplicação não altera os arquivos; todas as transformações ocorrem em memória.
- Os dados são mockados e utilizados exclusivamente para estudo e demonstração.
