from src.orchestrator import answer_user_message


class FakeLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        assert "ClaraMente" in system_prompt
        assert "resultados_calculados" in user_prompt
        return "Resumo educacional com dados mockados."


def test_orchestrator_runs_full_flow(knowledge_base):
    response = answer_user_message(
        "Qual é o meu saldo?", knowledge_base, FakeLLMClient()
    )
    assert response.content.startswith("Resumo")
    assert response.context.calculated_results["saldo"] == 3230.0
