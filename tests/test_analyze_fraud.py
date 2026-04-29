import pandas as pd
import pytest

from analyze_fraud import score_transactions, summarize_results


@pytest.fixture
def accounts():
    return pd.DataFrame(
        [
            {"account_id": 1, "prior_chargebacks": 0},
            {"account_id": 2, "prior_chargebacks": 3},
        ]
    )


@pytest.fixture
def transactions():
    # tx 1: clean -> low; tx 2: max-risk -> high; tx 3: medium-ish
    return pd.DataFrame(
        [
            {
                "transaction_id": 1,
                "account_id": 1,
                "amount_usd": 20.0,
                "device_risk_score": 5,
                "is_international": 0,
                "velocity_24h": 0,
                "failed_logins_24h": 0,
            },
            {
                "transaction_id": 2,
                "account_id": 2,
                "amount_usd": 1500.0,
                "device_risk_score": 90,
                "is_international": 1,
                "velocity_24h": 8,
                "failed_logins_24h": 6,
            },
            {
                "transaction_id": 3,
                "account_id": 1,
                "amount_usd": 600.0,
                "device_risk_score": 50,
                "is_international": 0,
                "velocity_24h": 3,
                "failed_logins_24h": 2,
            },
        ]
    )


@pytest.fixture
def chargebacks():
    return pd.DataFrame([{"transaction_id": 2}])


def test_score_transactions_attaches_score_and_label(transactions, accounts):
    scored = score_transactions(transactions, accounts)
    assert {"risk_score", "risk_label"}.issubset(scored.columns)
    assert len(scored) == len(transactions)
    by_id = dict(zip(scored["transaction_id"], scored["risk_label"]))
    assert by_id[1] == "low"
    assert by_id[2] == "high"
    assert by_id[3] in {"medium", "high"}


def test_summarize_results_shape_and_chargeback_rate(transactions, accounts, chargebacks):
    scored = score_transactions(transactions, accounts)
    summary = summarize_results(scored, chargebacks)

    assert {
        "risk_label",
        "transactions",
        "total_amount_usd",
        "avg_amount_usd",
        "chargebacks",
        "chargeback_rate",
    }.issubset(summary.columns)

    # transactions count totals match input
    assert summary["transactions"].sum() == len(transactions)

    # chargeback for tx 2 should land in the "high" bucket
    high_row = summary.loc[summary["risk_label"] == "high"].iloc[0]
    assert high_row["chargebacks"] == 1
    assert high_row["chargeback_rate"] == pytest.approx(1.0 / high_row["transactions"])

    # rates are valid probabilities
    assert (summary["chargeback_rate"] >= 0).all()
    assert (summary["chargeback_rate"] <= 1).all()


def test_summarize_handles_no_chargebacks(transactions, accounts):
    scored = score_transactions(transactions, accounts)
    empty_chargebacks = pd.DataFrame({"transaction_id": pd.Series(dtype="int64")})
    summary = summarize_results(scored, empty_chargebacks)
    assert (summary["chargebacks"].fillna(0) == 0).all()
    assert (summary["chargeback_rate"].fillna(0) == 0).all()


def test_chargeback_rate_rises_with_risk_label_on_sample_data():
    """End-to-end check on the bundled CSVs: chargeback rate should be monotonic
    across low -> medium -> high once the scoring rules are correct."""
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[1] / "data"
    accounts = pd.read_csv(data_dir / "accounts.csv")
    transactions = pd.read_csv(data_dir / "transactions.csv")
    chargebacks = pd.read_csv(data_dir / "chargebacks.csv")

    scored = score_transactions(transactions, accounts)
    summary = summarize_results(scored, chargebacks).set_index("risk_label")

    rates = {label: summary.loc[label, "chargeback_rate"] for label in ("low", "medium", "high") if label in summary.index}
    ordered = [rates[l] for l in ("low", "medium", "high") if l in rates]
    assert ordered == sorted(ordered), f"chargeback_rate not monotonic: {rates}"
