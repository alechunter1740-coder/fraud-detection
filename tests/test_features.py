import pandas as pd
import pytest

from features import build_model_frame


@pytest.fixture
def accounts():
    return pd.DataFrame(
        [
            {"account_id": 1, "customer_name": "A", "prior_chargebacks": 0},
            {"account_id": 2, "customer_name": "B", "prior_chargebacks": 2},
        ]
    )


@pytest.fixture
def transactions():
    return pd.DataFrame(
        [
            {"transaction_id": 100, "account_id": 1, "amount_usd": 999.99, "failed_logins_24h": 0},
            {"transaction_id": 101, "account_id": 1, "amount_usd": 1000.00, "failed_logins_24h": 1},
            {"transaction_id": 102, "account_id": 2, "amount_usd": 50.00, "failed_logins_24h": 4},
        ]
    )


def test_merges_account_columns(accounts, transactions):
    df = build_model_frame(transactions, accounts)
    assert {"customer_name", "prior_chargebacks"}.issubset(df.columns)
    assert df.loc[df["transaction_id"] == 102, "prior_chargebacks"].iloc[0] == 2


def test_is_large_amount_threshold_at_1000(accounts, transactions):
    df = build_model_frame(transactions, accounts)
    flags = dict(zip(df["transaction_id"], df["is_large_amount"]))
    assert flags[100] == 0  # 999.99 -> not large
    assert flags[101] == 1  # 1000.00 -> large
    assert flags[102] == 0


def test_login_pressure_buckets(accounts, transactions):
    df = build_model_frame(transactions, accounts)
    pressure = dict(zip(df["transaction_id"], df["login_pressure"].astype(str)))
    assert pressure[100] == "none"  # 0
    assert pressure[101] == "low"   # 1 -> (0, 2]
    assert pressure[102] == "high"  # 4 -> (2, 100]


def test_unmatched_account_yields_nan(accounts):
    transactions = pd.DataFrame(
        [{"transaction_id": 200, "account_id": 999, "amount_usd": 10.0, "failed_logins_24h": 0}]
    )
    df = build_model_frame(transactions, accounts)
    assert df["customer_name"].isna().all()
    assert len(df) == 1
