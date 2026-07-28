"""Interface Streamlit da ClaraMente com layout inspirado em buscadores."""

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


QUICK_QUESTIONS = [
    "Qual é o meu saldo no período?",
    "Em que categoria estou gastando mais?",
    "Como está minha reserva de emergência?",
]


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
        st.session_state.messages = []
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = None


def inject_page_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 960px;
            }

            .claramente-hero {
                text-align: center;
                margin-top: 1rem;
                margin-bottom: 2rem;
            }

            .claramente-logo {
                font-size: 4rem;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 0.3rem;
            }

            .claramente-tagline {
                font-size: 1rem;
                color: #9ca3af;
                margin-bottom: 1rem;
            }

            .claramente-disclaimer {
                background: rgba(59, 130, 246, 0.12);
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 14px;
                padding: 0.9rem 1rem;
                margin: 0 auto 1.6rem auto;
                max-width: 780px;
                color: #bfdbfe;
                text-align: center;
            }

            .claramente-search-section {
                max-width: 820px;
                margin: 0 auto 2rem auto;
            }

            .claramente-latest-title,
            .claramente-history-title {
                font-size: 1.1rem;
                font-weight: 700;
                margin-top: 1rem;
                margin-bottom: 0.8rem;
            }

            .claramente-card {
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 18px;
                padding: 1rem 1.1rem;
                background: rgba(15, 23, 42, 0.28);
                margin-bottom: 1rem;
            }

            .claramente-user-label,
            .claramente-assistant-label {
                font-size: 0.84rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                margin-bottom: 0.4rem;
            }

            .claramente-user-label {
                color: #fca5a5;
            }

            .claramente-assistant-label {
                color: #fdba74;
            }

            .claramente-empty {
                border: 1px dashed rgba(148, 163, 184, 0.25);
                border-radius: 18px;
                padding: 1rem;
                color: #9ca3af;
                background: rgba(15, 23, 42, 0.15);
            }

            .claramente-quick-title {
                text-align: center;
                color: #9ca3af;
                font-size: 0.95rem;
                margin: 0.75rem 0;
            }

            div[data-testid="stChatInput"] {
                margin-bottom: 0.4rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(llm_client: OllamaLLMClient) -> None:
    with st.sidebar:
        st.header("Configuração")
        st.write(f"**Modelo:** `{SETTINGS.ollama_model}`")
        st.write(f"**Executor:** `{SETTINGS.ollama_host}`")

        status = llm_client.is_available()
        if status:
            st.success("Ollama disponível")
        else:
            st.error("Ollama indisponível")

        st.caption(
            "Todos os dados desta demonstração são fictícios e educacionais."
        )

        if st.button("Limpar conversa", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_message = None
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


def render_doodle() -> None:
    st.markdown(
        """
        <div class="claramente-hero">
            <div class="claramente-logo">🧠 ClaraMente</div>
            <div class="claramente-tagline">
                Clareza para cuidar da sua saúde financeira.
            </div>
            <div class="claramente-disclaimer">
                Protótipo educacional com dados mockados.
                Não representa recomendação financeira profissional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_search_area() -> str | None:
    with st.container():
        st.markdown(
            '<div class="claramente-search-section">',
            unsafe_allow_html=True,
        )

        typed_message = st.chat_input(
            "Pergunte sobre os dados financeiros do projeto",
            key="chat_input",
        )

        st.markdown(
            '<div class="claramente-quick-title">Perguntas rápidas</div>',
            unsafe_allow_html=True,
        )

        columns = st.columns(len(QUICK_QUESTIONS))
        selected_prompt = None

        for index, (column, suggestion) in enumerate(
            zip(columns, QUICK_QUESTIONS, strict=True)
        ):
            if column.button(
                suggestion,
                key=f"quick_question_{index}",
                use_container_width=True,
            ):
                selected_prompt = suggestion

        st.markdown("</div>", unsafe_allow_html=True)

    return selected_prompt or typed_message


def process_pending_message(
    knowledge_base,
    llm_client: OllamaLLMClient,
) -> None:
    user_message = st.session_state.pending_message
    if not user_message:
        return

    st.session_state.pending_message = None
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    try:
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
                "error_command": f"ollama pull {SETTINGS.ollama_model}",
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
                    "Ocorreu um erro inesperado. Consulte os logs da aplicação."
                ),
            }
        )


def render_latest_interaction() -> None:
    st.markdown(
        '<div class="claramente-latest-title">Última pergunta e resposta</div>',
        unsafe_allow_html=True,
    )

    if len(st.session_state.messages) < 2:
        st.markdown(
            """
            <div class="claramente-empty">
                Faça uma pergunta para visualizar aqui a resposta mais recente.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    last_user = None
    last_assistant = None

    for message in reversed(st.session_state.messages):
        if last_assistant is None and message["role"] == "assistant":
            last_assistant = message
            continue
        if last_assistant is not None and message["role"] == "user":
            last_user = message
            break

    if last_user is None or last_assistant is None:
        st.markdown(
            """
            <div class="claramente-empty">
                Ainda não há uma interação completa para exibir.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="claramente-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="claramente-user-label">Pergunta</div>',
        unsafe_allow_html=True,
    )
    st.markdown(last_user["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="claramente-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="claramente-assistant-label">Resposta</div>',
        unsafe_allow_html=True,
    )
    st.markdown(last_assistant["content"])

    response = last_assistant.get("response")
    if response is not None:
        render_context_details(response)

    error_command = last_assistant.get("error_command")
    if error_command:
        st.code(error_command, language="bash")

    st.markdown("</div>", unsafe_allow_html=True)


def render_history() -> None:
    st.markdown(
        '<div class="claramente-history-title">Histórico de perguntas e respostas</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        st.markdown(
            """
            <div class="claramente-empty">
                O histórico aparecerá aqui depois das primeiras interações.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    with st.expander("Abrir histórico completo", expanded=False):
        for index, message in enumerate(st.session_state.messages, start=1):
            label = "Pergunta" if message["role"] == "user" else "Resposta"
            st.markdown(f"**{index}. {label}**")
            st.markdown(message["content"])

            response = message.get("response")
            if response is not None:
                render_context_details(response)

            error_command = message.get("error_command")
            if error_command:
                st.code(error_command, language="bash")

            if index < len(st.session_state.messages):
                st.divider()


def main() -> None:
    st.set_page_config(
        page_title="ClaraMente",
        page_icon="🧠",
        layout="centered",
    )

    inject_page_styles()
    initialize_session()

    try:
        knowledge_base = get_knowledge_base()
        llm_client = get_llm_client()
    except ClaraMenteError as exc:
        st.error(str(exc))
        st.stop()

    render_sidebar(llm_client)
    render_doodle()

    user_message = render_search_area()
    if user_message:
        st.session_state.pending_message = user_message
        with st.spinner("Analisando os dados e consultando o modelo local..."):
            process_pending_message(knowledge_base, llm_client)
        st.rerun()

    render_latest_interaction()
    render_history()


if __name__ == "__main__":
    main()
