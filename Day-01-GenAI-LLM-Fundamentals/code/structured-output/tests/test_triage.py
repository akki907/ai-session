import pytest

from it_support_triage import Category, Priority, call_triage


@pytest.mark.parametrize(
    "message,expected_category",
    [
        ("My VPN keeps disconnecting.", Category.VPN),
        ("I forgot my Windows password.", Category.PASSWORD),
        ("I need access to the production database.", Category.ACCESS),
        ("Where is the WFH policy?", Category.POLICY),
    ],
)
def test_category(message, expected_category):
    decision = call_triage(message)
    assert decision.category == expected_category


def test_priority_is_valid_enum():
    decision = call_triage("Production is down, pages firing.")
    assert decision.priority in {Priority.LOW, Priority.MEDIUM, Priority.HIGH}


def test_reasoning_is_nonempty():
    decision = call_triage("Laptop won't turn on.")
    assert len(decision.reasoning) > 0


def test_requires_ticket_is_bool():
    decision = call_triage("My laptop screen is broken.")
    assert isinstance(decision.requires_ticket, bool)


def test_suggested_action_is_nonempty():
    decision = call_triage("I cannot log in to Salesforce.")
    assert len(decision.suggested_action) > 0
