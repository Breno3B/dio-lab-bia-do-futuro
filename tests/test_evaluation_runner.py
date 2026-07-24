"""Testes do executor da suíte end-to-end."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from evaluation import run_evaluation
from src.models import AgentContext, AgentResponse, Intent


def make_case(**overrides):
    case = {
        "id": "case_001",
        "category": "test_category",
        "severity": "medium",
        "execution": "deterministic",
        "question": "Qual é o meu saldo?",
        "expected_intent": "financial_summary",
        "expected_used_llm": False,
        "required_terms": ["saldo"],
        "forbidden_terms": ["valor inventado"],
    }
    case.update(overrides)
    return case


def make_response(
    *,
    content="Seu saldo foi calculado.",
    intent=Intent.FINANCIAL_SUMMARY,
    used_llm=False,
    warnings=None,
):
    context = AgentContext(
        intent=intent,
        user_message="Qual é o meu saldo?",
    )
    return AgentResponse(
        content=content,
        intent=intent,
        context=context,
        warnings=warnings or [],
        performance_metrics={"used_llm": used_llm},
    )


def test_validate_cases_accepts_valid_case():
    cases = [make_case()]

    assert run_evaluation._validate_cases(cases) == cases


@pytest.mark.parametrize("cases", [None, {}, [], "invalid"])
def test_validate_cases_rejects_non_empty_list_requirement(cases):
    with pytest.raises(
        ValueError,
        match="lista não vazia",
    ):
        run_evaluation._validate_cases(cases)


def test_validate_cases_rejects_item_that_is_not_object():
    with pytest.raises(
        TypeError,
        match="deve ser um objeto JSON",
    ):
        run_evaluation._validate_cases(["invalid"])


def test_validate_cases_rejects_missing_required_field():
    case = make_case()
    del case["question"]

    with pytest.raises(
        ValueError,
        match="campos obrigatórios",
    ):
        run_evaluation._validate_cases([case])


def test_validate_cases_rejects_empty_id():
    with pytest.raises(ValueError, match="id vazio"):
        run_evaluation._validate_cases([make_case(id="  ")])


def test_validate_cases_rejects_duplicate_id():
    cases = [
        make_case(),
        make_case(question="Outra pergunta"),
    ]

    with pytest.raises(ValueError, match="ID de caso duplicado"):
        run_evaluation._validate_cases(cases)


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "expected_message"),
    [
        ("execution", "manual", "Execução inválida"),
        ("severity", "urgent", "Severidade inválida"),
    ],
)
def test_validate_cases_rejects_invalid_enum_values(
    field_name,
    invalid_value,
    expected_message,
):
    with pytest.raises(ValueError, match=expected_message):
        run_evaluation._validate_cases(
            [make_case(**{field_name: invalid_value})]
        )


@pytest.mark.parametrize(
    "field_name",
    ["required_terms", "forbidden_terms"],
)
def test_validate_cases_rejects_invalid_term_lists(field_name):
    with pytest.raises(ValueError, match=field_name):
        run_evaluation._validate_cases(
            [make_case(**{field_name: ["", 123]})]
        )


@pytest.mark.parametrize(
    "field_name",
    ["expected_used_llm", "expected_blocked"],
)
def test_validate_cases_rejects_non_boolean_expectations(field_name):
    with pytest.raises(ValueError, match="deve ser booleano"):
        run_evaluation._validate_cases(
            [make_case(**{field_name: "false"})]
        )


def test_is_blocked_detects_validator_warning():
    response = make_response(
        warnings=["Resposta bloqueada: produto não autorizado."]
    )

    assert run_evaluation._is_blocked(response) is True


def test_is_blocked_returns_false_without_block_warning():
    response = make_response(warnings=["Aviso informativo."])

    assert run_evaluation._is_blocked(response) is False


def test_evaluate_case_passes_when_all_expectations_match():
    case = make_case(expected_blocked=False)
    response = make_response()

    result = run_evaluation._evaluate_case(case, response)

    assert result["passed"] is True
    assert result["failures"] == []
    assert result["used_llm"] is False
    assert result["blocked"] is False


def test_evaluate_case_reports_all_detected_failures():
    case = make_case(
        execution="generative",
        expected_intent="expense_analysis",
        expected_used_llm=True,
        expected_blocked=True,
        required_terms=["termo ausente"],
        forbidden_terms=["saldo"],
    )
    response = make_response()

    result = run_evaluation._evaluate_case(case, response)

    assert result["passed"] is False
    assert len(result["failures"]) == 5
    assert any("Intenção esperada" in item for item in result["failures"])
    assert any("Termo obrigatório ausente" in item for item in result["failures"])
    assert any("Termo proibido presente" in item for item in result["failures"])
    assert any("Bloqueio esperado" in item for item in result["failures"])
    assert any("Execução esperada" in item for item in result["failures"])


def test_group_summary_consolidates_results():
    results = [
        {
            "category": "alpha",
            "passed": True,
            "blocked": False,
            "used_llm": False,
        },
        {
            "category": "alpha",
            "passed": False,
            "blocked": True,
            "used_llm": True,
        },
        {
            "category": "beta",
            "passed": True,
            "blocked": False,
            "used_llm": True,
        },
    ]

    summary = run_evaluation._group_summary(results, "category")

    assert summary["alpha"] == {
        "total": 2,
        "passed": 1,
        "failed": 1,
        "blocked": 1,
        "used_llm": 1,
    }
    assert summary["beta"]["total"] == 1
    assert summary["beta"]["passed"] == 1


def test_build_summary_consolidates_totals(monkeypatch):
    monkeypatch.setattr(
        run_evaluation,
        "SETTINGS",
        SimpleNamespace(ollama_model="test-model"),
    )
    results = [
        {
            "category": "alpha",
            "severity": "high",
            "expected_execution": "deterministic",
            "actual_execution": "deterministic",
            "execution_matches": True,
            "passed": True,
            "blocked": False,
            "used_llm": False,
            "failures": [],
        },
        {
            "category": "beta",
            "severity": "critical",
            "expected_execution": "generative",
            "actual_execution": "generative",
            "execution_matches": True,
            "passed": False,
            "blocked": True,
            "used_llm": True,
            "failures": ["Falha controlada."],
        },
    ]

    summary = run_evaluation._build_summary(results)

    assert summary["model"] == "test-model"
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["blocked"] == 1
    assert summary["expected_execution_counts"] == {
        "deterministic": 1,
        "generative": 1,
    }
    assert summary["actual_execution_counts"] == {
        "deterministic": 1,
        "generative": 1,
    }
    assert summary["execution_mismatches"] == 0
    assert summary["failure_reasons"] == {"Falha controlada.": 1}


def test_run_applies_filters_and_writes_report(tmp_path, monkeypatch):
    cases_file = tmp_path / "cases.json"
    output_file = tmp_path / "results" / "report.json"
    cases_file.write_text(
        json.dumps(
            [
                make_case(
                    id="deterministic_001",
                    category="summary",
                ),
                make_case(
                    id="generative_001",
                    category="products",
                    execution="generative",
                    expected_intent="product_compatibility",
                    expected_used_llm=True,
                ),
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        run_evaluation,
        "load_knowledge_base",
        lambda: object(),
    )
    monkeypatch.setattr(
        run_evaluation,
        "OllamaLLMClient",
        lambda: object(),
    )
    monkeypatch.setattr(
        run_evaluation,
        "answer_user_message",
        lambda question, knowledge_base, client: make_response(),
    )

    destination = run_evaluation.run(
        cases_file,
        output_file,
        execution="deterministic",
    )

    report = json.loads(destination.read_text(encoding="utf-8"))

    assert destination == output_file
    assert report["total"] == 1
    assert report["results"][0]["id"] == "deterministic_001"
    assert report["passed"] == 1


def test_run_rejects_filters_without_results(tmp_path):
    cases_file = tmp_path / "cases.json"
    cases_file.write_text(
        json.dumps([make_case()], ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Nenhum caso corresponde",
    ):
        run_evaluation.run(
            cases_file,
            execution="generative",
        )


def test_validate_cases_rejects_missing_expected_used_llm():
    case = make_case()
    del case["expected_used_llm"]

    with pytest.raises(
        ValueError,
        match="campos obrigatórios",
    ):
        run_evaluation._validate_cases([case])


@pytest.mark.parametrize(
    ("execution", "expected_used_llm"),
    [
        ("deterministic", True),
        ("generative", False),
    ],
)
def test_validate_cases_rejects_execution_llm_inconsistency(
    execution,
    expected_used_llm,
):
    with pytest.raises(
        ValueError,
        match="Configuração incoerente",
    ):
        run_evaluation._validate_cases(
            [
                make_case(
                    execution=execution,
                    expected_used_llm=expected_used_llm,
                )
            ]
        )


def test_evaluate_case_distinguishes_expected_and_actual_execution():
    case = make_case(
        execution="generative",
        expected_used_llm=True,
    )
    response = make_response(used_llm=False)

    result = run_evaluation._evaluate_case(case, response)

    assert result["expected_execution"] == "generative"
    assert result["actual_execution"] == "deterministic"
    assert result["execution_matches"] is False
    assert result["passed"] is False


def test_build_summary_separates_expected_and_actual_execution(monkeypatch):
    monkeypatch.setattr(
        run_evaluation,
        "SETTINGS",
        SimpleNamespace(ollama_model="test-model"),
    )
    results = [
        {
            "category": "alpha",
            "severity": "high",
            "expected_execution": "deterministic",
            "actual_execution": "deterministic",
            "execution_matches": True,
            "passed": True,
            "blocked": False,
            "used_llm": False,
            "failures": [],
        },
        {
            "category": "beta",
            "severity": "critical",
            "expected_execution": "generative",
            "actual_execution": "deterministic",
            "execution_matches": False,
            "passed": False,
            "blocked": False,
            "used_llm": False,
            "failures": ["Uso do LLM esperado=True, obtido=False."],
        },
    ]

    summary = run_evaluation._build_summary(results)

    assert summary["expected_execution_counts"] == {
        "deterministic": 1,
        "generative": 1,
    }
    assert summary["actual_execution_counts"] == {
        "deterministic": 2,
        "generative": 0,
    }
    assert summary["execution_mismatches"] == 1
    assert "by_expected_execution" in summary
    assert "by_actual_execution" in summary


def test_validate_cases_rejects_expected_values_that_are_not_object():
    with pytest.raises(TypeError, match="expected_values"):
        run_evaluation._validate_cases(
            [make_case(expected_values=["saldo", 1.0])]
        )


@pytest.mark.parametrize(
    "expected_values",
    [
        {"": 1.0},
        {"saldo": "2511.10"},
        {"saldo": True},
    ],
)
def test_validate_cases_rejects_invalid_expected_values(expected_values):
    with pytest.raises(ValueError, match="expected_values"):
        run_evaluation._validate_cases(
            [make_case(expected_values=expected_values)]
        )


@pytest.mark.parametrize("tolerance", [-0.01, "0.01", True])
def test_validate_cases_rejects_invalid_expected_value_tolerance(tolerance):
    with pytest.raises(ValueError, match="expected_value_tolerance"):
        run_evaluation._validate_cases(
            [make_case(expected_value_tolerance=tolerance)]
        )


def test_get_nested_value_reads_dicts_and_lists():
    data = {
        "summary": {
            "goals": [
                {"progress": 66.67},
            ]
        }
    }

    assert (
        run_evaluation._get_nested_value(
            data,
            "summary.goals.0.progress",
        )
        == 66.67
    )


def test_evaluate_case_accepts_matching_structured_values():
    case = make_case(
        expected_values={
            "saldo": 2511.10,
            "maior_categoria.valor": 1380.00,
        }
    )
    response = make_response()
    response.context.calculated_results = {
        "saldo": 2511.10,
        "maior_categoria": {"valor": 1380.00},
    }

    result = run_evaluation._evaluate_case(case, response)

    assert result["passed"] is True
    assert result["value_matches"] is True
    assert result["actual_values"] == {
        "saldo": 2511.10,
        "maior_categoria.valor": 1380.00,
    }


def test_evaluate_case_reports_structured_value_difference():
    case = make_case(
        expected_values={"saldo": 2511.10},
        expected_value_tolerance=0.01,
    )
    response = make_response()
    response.context.calculated_results = {"saldo": 2500.00}

    result = run_evaluation._evaluate_case(case, response)

    assert result["passed"] is False
    assert result["value_matches"] is False
    assert any(
        "Valor esperado em saldo" in failure
        for failure in result["failures"]
    )


def test_evaluate_case_reports_missing_structured_value():
    case = make_case(expected_values={"saldo": 2511.10})
    response = make_response()
    response.context.calculated_results = {}

    result = run_evaluation._evaluate_case(case, response)

    assert result["passed"] is False
    assert result["actual_values"] == {"saldo": None}
    assert any(
        "Valor esperado não encontrado" in failure
        for failure in result["failures"]
    )


def test_execution_mismatch_has_explicit_failure_message():
    case = make_case(
        execution="generative",
        expected_used_llm=True,
    )
    response = make_response(used_llm=False)

    result = run_evaluation._evaluate_case(case, response)

    assert result["execution_matches"] is False
    assert any(
        failure
        == "Execução esperada=generative, obtida=deterministic."
        for failure in result["failures"]
    )
