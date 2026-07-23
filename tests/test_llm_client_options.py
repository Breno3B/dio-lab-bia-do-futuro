from src.llm_client import OllamaLLMClient


def test_chat_options_limit_context_and_generation(settings):
    configured = settings.__class__(
        data_dir=settings.data_dir,
        ollama_num_ctx=2048,
        ollama_num_predict=120,
    )
    client = OllamaLLMClient(configured)
    assert client._chat_options()["num_ctx"] == 2048
    assert client._chat_options()["num_predict"] == 120
