from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import Settings
from src.data_loader import load_knowledge_base


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    transactions = """data,descricao,categoria,valor,tipo
2025-10-01,Salário,receita,5000.00,entrada
2025-10-02,Aluguel,moradia,1200.00,saida
2025-10-03,Supermercado,alimentacao,450.00,saida
2025-10-10,Restaurante,alimentacao,120.00,saida
"""
    history = """data,canal,tema,resumo,resolvido
2025-10-01,chat,Tesouro Selic,Cliente pediu explicação,sim
2025-10-12,chat,Metas financeiras,Cliente acompanhou a reserva,sim
"""
    profile = {
        "nome": "João Silva", "idade": 32, "profissao": "Analista",
        "renda_mensal": 5000.0, "perfil_investidor": "moderado",
        "objetivo_principal": "Construir reserva de emergência",
        "patrimonio_total": 15000.0, "reserva_emergencia_atual": 10000.0,
        "aceita_risco": False,
        "metas": [{"meta": "Completar reserva de emergência", "valor_necessario": 15000.0, "prazo": "2026-06"}],
    }
    products = [
        {"nome": "Tesouro Selic", "categoria": "renda_fixa", "risco": "baixo",
         "rentabilidade": "100% da Selic", "aporte_minimo": 30.0,
         "indicado_para": "Reserva de emergência e iniciantes"},
        {"nome": "Fundo de Ações", "categoria": "fundo", "risco": "alto",
         "rentabilidade": "Variável", "aporte_minimo": 100.0,
         "indicado_para": "Perfil arrojado"},
    ]
    (tmp_path / "transacoes.csv").write_text(transactions, encoding="utf-8")
    (tmp_path / "historico_atendimento.csv").write_text(history, encoding="utf-8")
    (tmp_path / "perfil_investidor.json").write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "produtos_financeiros.json").write_text(json.dumps(products, ensure_ascii=False), encoding="utf-8")
    return tmp_path


@pytest.fixture
def settings(data_dir: Path) -> Settings:
    return Settings(data_dir=data_dir)


@pytest.fixture
def knowledge_base(settings: Settings):
    return load_knowledge_base(settings)
