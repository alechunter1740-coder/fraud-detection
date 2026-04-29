import pytest

from risk_rules import label_risk, score_transaction


CLEAN_TX = {
    "device_risk_score": 0,
    "is_international": 0,
    "amount_usd": 0,
    "velocity_24h": 0,
    "failed_logins_24h": 0,
    "prior_chargebacks": 0,
}


def _tx(**overrides):
    return {**CLEAN_TX, **overrides}


def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_clean_transaction_is_low_risk():
    assert score_transaction(CLEAN_TX) == 0
    assert label_risk(score_transaction(CLEAN_TX)) == "low"


def test_large_amount_adds_risk():
    assert score_transaction(_tx(amount_usd=1200)) >= 25
    assert score_transaction(_tx(amount_usd=600)) >= 10


@pytest.mark.parametrize(
    "feature,risky_value",
    [
        ("device_risk_score", 80),
        ("is_international", 1),
        ("amount_usd", 1500),
        ("velocity_24h", 8),
        ("failed_logins_24h", 6),
        ("prior_chargebacks", 3),
    ],
)
def test_each_risk_signal_increases_score(feature, risky_value):
    """Turning on any single risky signal must raise the score above a clean transaction."""
    baseline = score_transaction(CLEAN_TX)
    assert score_transaction(_tx(**{feature: risky_value})) > baseline


def test_stacked_high_risk_transaction_is_labelled_high():
    tx = _tx(
        device_risk_score=85,
        is_international=1,
        amount_usd=2000,
        velocity_24h=10,
        failed_logins_24h=6,
        prior_chargebacks=3,
    )
    score = score_transaction(tx)
    assert score >= 60
    assert label_risk(score) == "high"


def test_score_is_clamped_to_valid_range():
    extreme = _tx(
        device_risk_score=99,
        is_international=1,
        amount_usd=10_000,
        velocity_24h=50,
        failed_logins_24h=50,
        prior_chargebacks=10,
    )
    assert 0 <= score_transaction(extreme) <= 100
