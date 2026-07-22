from src.data_validator import validate_knowledge_base


def test_validation_accepts_base_and_reports_profile_conflict(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)
    assert report.is_valid
    assert any("divergência" in warning for warning in report.warnings)
