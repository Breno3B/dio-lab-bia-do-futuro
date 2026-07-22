from src.data_loader import load_knowledge_base


def test_load_knowledge_base(settings):
    kb = load_knowledge_base(settings)
    assert len(kb.transactions) == 4
    assert kb.transactions["data"].notna().all()
    assert kb.investor_profile["nome"] == "João Silva"
    assert len(kb.financial_products) == 2
