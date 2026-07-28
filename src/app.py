"""Interface Streamlit da ClaraMente."""

from __future__ import annotations

import logging

import streamlit as st

from src.config import SETTINGS
from src.data_loader import load_knowledge_base
from src.data_validator import validate_knowledge_base
from src.exceptions import ClaraMenteError, LLMUnavailableError
from src.llm_client import OllamaLLMClient
from src.orchestrator import answer_user_message

logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_knowledge_base():
    knowledge_base = load_knowledge_base()
    validate_knowledge_base(knowledge_base, raise_on_error=True)
    return knowledge_base


@st.cache_resource(show_spinner=False)
def get_llm_client() -> OllamaLLMClient:
    return OllamaLLMClient()


def initialize_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Eu sou a **ClaraMente**. "
                    "Posso analisar os dados financeiros "
                    "mockados do projeto, explicar gastos, "
                    "metas e produtos do catálogo."
                ),
            }
        ]


def render_sidebar(llm_client: OllamaLLMClient) -> None:
    with st.sidebar:
        st.header("Configuração")
        st.write(f"**Modelo:** `{SETTINGS.ollama_model}`")
        st.write(f"**Executor:** `{SETTINGS.ollama_host}`")

        status = llm_client.is_available()
        st.success("Ollama disponível") if status else st.error(
            "Ollama indisponível"
        )

        st.caption(
            "Todos os dados desta demonstração são fictícios "
            "e educacionais."
        )

        if st.button("Limpar conversa", use_container_width=True):
            del st.session_state.messages
            st.rerun()


def render_context_details(response) -> None:
    with st.expander("Fontes, contexto e validações"):
        st.write("**Intenção:**", response.intent.value)
        st.write("**Fontes:**")

        if response.context.sources:
            for source in response.context.sources:
                st.markdown(f"- `{source}`")
        else:
            st.write("Nenhuma")

        period = response.context.period
        period_label = (
            period.get("descricao")
            if isinstance(period, dict)
            else None
        )
        st.write(
            "**Período:**",
            period_label or period or "Não aplicável",
        )

        if response.context.limitations:
            st.write("**Limitações:**")
            for limitation in response.context.limitations:
                st.write(f"- {limitation}")

        if response.warnings:
            st.warning(
                "Validação automática encontrou pontos para revisão:"
            )
            for warning in response.warnings:
                st.write(f"- {warning}")

        if response.performance_metrics:
            metrics = response.performance_metrics
            st.write("**Performance:**")
            st.write(
                f"- Tempo total: {metrics.get('total_ms', 0):.2f} ms"
            )
            st.write(
                "- Geração: "
                + (
                    "Ollama"
                    if metrics.get("used_llm")
                    else "resposta determinística"
                )
            )

            if metrics.get("used_llm"):
                st.write(
                    f"- Tempo do LLM: "
                    f"{metrics.get('llm_ms', 0):.2f} ms"
                )

                if metrics.get("eval_count") is not None:
                    st.write(
                        f"- Tokens gerados: {metrics['eval_count']}"
                    )

                if metrics.get("tokens_per_second") is not None:
                    st.write(
                        "- Velocidade: "
                        f"{metrics['tokens_per_second']:.2f} tokens/s"
                    )


def render_prompt_input() -> str | None:
    """Exibe o campo de texto e as sugestões logo abaixo dele."""

    suggestions = [
        "Qual é o meu saldo no período?",
        "Em que categoria estou gastando mais?",
        "Como está minha reserva de emergência?",
    ]

    with st.container():
        typed_message = st.chat_input(
            "Pergunte sobre os dados financeiros do projeto",
            key="chat_input",
        )

        st.caption("Perguntas rápidas")
        columns = st.columns(len(suggestions))

        selected_prompt = None
        for index, (column, suggestion) in enumerate(
            zip(columns, suggestions, strict=True)
        ):
            if column.button(
                suggestion,
                key=f"suggestion_{index}",
                use_container_width=True,
            ):
                selected_prompt = suggestion

    return selected_prompt or typed_message


def process_pending_message(
    knowledge_base,
    llm_client: OllamaLLMClient,
) -> None:
    """Processa uma pergunta armazenada na sessão."""

    user_message = st.session_state.pop("pending_message", None)
    if not user_message:
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    try:
        with st.spinner(
            "Analisando os dados e consultando o modelo local..."
        ):
            response = answer_user_message(
                user_message,
                knowledge_base,
                llm_client,
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response.content,
                "response": response,
            }
        )
    except LLMUnavailableError as exc:
        logger.warning("Ollama indisponível: %s", exc)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": str(exc),
                "error_command": (
                    f"ollama pull {SETTINGS.ollama_model}"
                ),
            }
        )
    except ClaraMenteError as exc:
        logger.exception("Erro controlado na aplicação")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": str(exc),
            }
        )
    except Exception:
        logger.exception("Erro inesperado")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Ocorreu um erro inesperado. "
                    "Consulte os logs da aplicação."
                ),
            }
        )

    st.rerun()


def render_conversation() -> None:
    """Renderiza todas as mensagens já processadas."""

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            response = message.get("response")
            if response is not None:
                render_context_details(response)

            error_command = message.get("error_command")
            if error_command:
                st.code(error_command, language="bash")


def main() -> None:
    st.set_page_config(
        page_title="ClaraMente",
        page_icon="🧠",
        layout="centered",
    )

    st.title("🧠 ClaraMente")
    st.caption("Clareza para cuidar da sua saúde financeira.")
    st.info(
        "Protótipo educacional com dados mockados. "
        "Não representa recomendação financeira profissional."
    )

    initialize_session()

    try:
        knowledge_base = get_knowledge_base()
        llm_client = get_llm_client()
    except ClaraMenteError as exc:
        st.error(str(exc))
        st.stop()

    render_sidebar(llm_client)

    process_pending_message(knowledge_base, llm_client)
    render_conversation()

    user_message = render_prompt_input()
    if user_message:
        st.session_state.pending_message = user_message
        st.rerun()


if __name__ == "__main__":
    _ = main()
