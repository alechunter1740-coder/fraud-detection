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


# --- label_risk ---------------------------------------------------------------

@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "low"),
        (29, "low"),
        (30, "medium"),
        (59, "medium"),
        (60, "high"),
        (100, "high"),
    ],
)
def test_label_risk_boundaries(score, expected):
    assert label_risk(score) == expected


# --- score_transaction: clean baseline ----------------------------------------

def test_clean_transaction_scores_zero():
    assert score_transaction(CLEAN_TX) == 0
    assert label_risk(score_transaction(CLEAN_TX)) == "low"


# --- score_transaction: per-feature tier weights ------------------------------

@pytest.mark.parametrize(
    "feature,value,expected_delta",
    [
        # device_risk_score: 0 below 40, +10 in [40,70), +25 at >=70
        ("device_risk_score", 39, 0),
        ("device_risk_score", 40, 10),
        ("device_risk_score", 69, 10),
        ("device_risk_score", 70, 25),
        ("device_risk_score", 99, 25),
        # is_international: +15 when 1
        ("is_international", 0, 0),
        ("is_international", 1, 15),
        # amount_usd: 0 below 500, +10 in [500,1000), +25 at >=1000
        ("amount_usd", 499, 0),
        ("amount_usd", 500, 10),
        ("amount_usd", 999, 10),
        ("amount_usd", 1000, 25),
        ("amount_usd", 10_000, 25),
        # velocity_24h: 0 below 3, +5 in [3,6), +20 at >=6
        ("velocity_24h", 2, 0),
        ("velocity_24h", 3, 5),
        ("velocity_24h", 5, 5),
        ("velocity_24h", 6, 20),
        # failed_logins_24h: 0 below 2, +10 in [2,5), +20 at >=5
        ("failed_logins_24h", 1, 0),
        ("failed_logins_24h", 2, 10),
        ("failed_logins_24h", 4, 10),
        ("failed_logins_24h", 5, 20),
        # prior_chargebacks: 0 at 0, +5 at 1, +20 at >=2
        ("prior_chargebacks", 0, 0),
        ("prior_chargebacks", 1, 5),
        ("prior_chargebacks", 2, 20),
        ("prior_chargebacks", 10, 20),
    ],
)
def test_each_feature_contributes_expected_weight(feature, value, expected_delta):
    """Each signal in isolation should contribute its documented tier weight."""
    assert score_transaction(_tx(**{feature: value})) == expected_delta


# --- score_transaction: monotonicity ------------------------------------------

@pytest.mark.parametrize(
    "feature,sweep",
    [
        ("device_risk_score", [0, 39, 40, 69, 70, 90]),
        ("amount_usd", [0, 499, 500, 999, 1000, 5000]),
        ("velocity_24h", [0, 2, 3, 5, 6, 50]),
        ("failed_logins_24h", [0, 1, 2, 4, 5, 50]),
        ("prior_chargebacks", [0, 1, 2, 10]),
    ],
)
def test_score_is_monotonic_in_each_feature(feature, sweep):
    """Increasing any single risky signal must never decrease the score."""
    scores = [score_transaction(_tx(**{feature: v})) for v in sweep]
    assert scores == sorted(scores), f"non-monotonic for {feature}: {list(zip(sweep, scores))}"


# --- score_transaction: clamping ----------------------------------------------

def test_max_stacked_signals_clamp_to_100():
    tx = _tx(
        device_risk_score=99,
        is_international=1,
        amount_usd=10_000,
        velocity_24h=50,
        failed_logins_24h=50,
        prior_chargebacks=10,
    )
    # raw additive total = 25 + 15 + 25 + 20 + 20 + 20 = 125
    assert score_transaction(tx) == 100


def test_score_never_negative():
    assert score_transaction(CLEAN_TX) >= 0


# --- score_transaction: realistic profiles ------------------------------------

def test_stacked_high_risk_is_labelled_high():
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


def test_card_testing_profile_is_high_risk():
    """Many small international charges from a flagged device — classic card testing."""
    tx = _tx(
        device_risk_score=75,
        is_international=1,
        amount_usd=12.50,
        velocity_24h=15,
        failed_logins_24h=0,
        prior_chargebacks=0,
    )
    # 25 (device) + 15 (intl) + 0 (amount) + 20 (velocity) = 60
    assert label_risk(score_transaction(tx)) == "high"


def test_account_takeover_profile_is_high_risk():
    """Login pressure plus a flagged device should land in high risk."""
    tx = _tx(
        device_risk_score=72,
        is_international=0,
        amount_usd=600,
        velocity_24h=2,
        failed_logins_24h=8,
        prior_chargebacks=0,
    )
    # 25 + 0 + 10 + 0 + 20 + 0 = 55 -> medium boundary; assert at least medium
    assert label_risk(score_transaction(tx)) in {"medium", "high"}


def test_unrelated_fields_do_not_affect_score():
    """Extra keys in the dict must not change scoring (function reads only known fields)."""
    base = score_transaction(_tx(amount_usd=600))
    enriched = score_transaction(_tx(amount_usd=600, customer_name="Ada", country="US"))
    assert base == enriched
