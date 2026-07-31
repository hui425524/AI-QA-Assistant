from app.qa_service import MockQaProvider


def test_incomplete_requirement_is_blocked():
    result = MockQaProvider().analyze("使用者可以登入系統")

    assert result.readiness_state == "blocked"
    assert result.is_complete is False
    assert result.missing_items
    assert len(result.clarification_questions) <= 5


def test_complete_requirement_is_ready(complete_requirement):
    result = MockQaProvider().analyze(complete_requirement)

    assert result.readiness_state == "ready"
    assert result.is_complete is True
    assert result.requirement_score == 100
    assert result.missing_items == []


def test_generation_is_deterministic():
    provider = MockQaProvider()

    first = provider.generate("需求 A")
    second = provider.generate("需求 A")

    assert first == second
    assert [case.case_id for case in first] == ["TC001", "TC002", "TC003"]
