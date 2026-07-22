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
                    "Olá! Eu sou a **ClaraMente**. Posso analisar os dados financeiros "
                    "mockados do projeto, explicar gastos, metas e produtos do catálogo."
                ),
            }
        ]


def render_sidebar(llm_client: OllamaLLMClient) -> None:
    with st.sidebar:
        st.header("Configuração")
        st.write(f"**Modelo:** `{SETTINGS.ollama_model}`")
        st.write(f"**Executor:** `{SETTINGS.ollama_host}`")
        status = llm_client.is_available()
        st.success("Ollama disponível") if status else st.error("Ollama indisponível")
        st.caption("Todos os dados desta demonstração são fictícios e educacionais.")
        if st.button("Limpar conversa", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def render_context_details(response) -> None:
    with st.expander("Fontes, contexto e validações"):
        st.write("**Intenção:**", response.intent.value)
        st.write("**Fontes:**", response.context.sources or "Nenhuma")
        st.write("**Período:**", response.context.period or "Não aplicável")
        if response.context.limitations:
            st.write("**Limitações:**")
            for limitation in response.context.limitations:
                st.write(f"- {limitation}")
        if response.warnings:
            st.warning("Validação automática encontrou pontos para revisão:")
            for warning in response.warnings:
                st.write(f"- {warning}")


def main() -> None:
    st.set_page_config(page_title="ClaraMente", page_icon="🧠", layout="centered")
    st.title("🧠 ClaraMente")
    st.caption("Clareza para cuidar da sua saúde financeira.")
    st.info("Protótipo educacional com dados mockados. Não representa recomendação financeira profissional.")

    initialize_session()

    try:
        knowledge_base = get_knowledge_base()
        llm_client = get_llm_client()
    except ClaraMenteError as exc:
        st.error(str(exc))
        st.stop()

    render_sidebar(llm_client)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.write("**Sugestões:**")
    cols = st.columns(3)
    suggestions = [
        "Qual é o meu saldo no período?",
        "Em que categoria estou gastando mais?",
        "Como está minha reserva de emergência?",
    ]
    selected_prompt = None
    for column, suggestion in zip(cols, suggestions, strict=True):
        if column.button(suggestion, use_container_width=True):
            selected_prompt = suggestion

    user_message = selected_prompt or st.chat_input("Pergunte sobre os dados financeiros do projeto")
    if not user_message:
        return

    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analisando os dados e consultando o modelo local..."):
                response = answer_user_message(user_message, knowledge_base, llm_client)
            st.markdown(response.content)
            render_context_details(response)
            st.session_state.messages.append({"role": "assistant", "content": response.content})
        except LLMUnavailableError as exc:
            logger.warning("Ollama indisponível: %s", exc)
            st.error(str(exc))
            st.code(f"ollama pull {SETTINGS.ollama_model}", language="bash")
        except ClaraMenteError as exc:
            logger.exception("Erro controlado na aplicação")
            st.error(str(exc))
        except Exception:
            logger.exception("Erro inesperado")
            st.error("Ocorreu um erro inesperado. Consulte os logs da aplicação.")


if __name__ == "__main__":
    main()
