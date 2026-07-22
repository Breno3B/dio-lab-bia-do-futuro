"""Exceções específicas da aplicação ClaraMente."""


class ClaraMenteError(Exception):
    """Erro base da aplicação."""


class DataLoadingError(ClaraMenteError):
    """Falha ao carregar um arquivo da base de conhecimento."""


class DataValidationError(ClaraMenteError):
    """A base de conhecimento contém erros que impedem seu uso."""


class LLMUnavailableError(ClaraMenteError):
    """O Ollama ou o modelo configurado não está disponível."""
