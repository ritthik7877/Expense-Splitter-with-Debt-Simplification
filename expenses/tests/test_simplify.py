from decimal import Decimal

import pytest

from expenses.services.simplify import simplify_debts


def test_simple_three_person_case():
    plan = simplify_debts(
        {
            1: Decimal("10.00"),
            2: Decimal("-4.00"),
            3: Decimal("-6.00"),
        }
    )

    assert plan == [
        {"from_user": 3, "to_user": 1, "amount": Decimal("6.00")},
        {"from_user": 2, "to_user": 1, "amount": Decimal("4.00")},
    ]


def test_circular_debts_need_no_transfers():
    balances = {
        "A": Decimal("0.00"),
        "B": Decimal("0.00"),
        "C": Decimal("0.00"),
    }

    assert simplify_debts(balances) == []


def test_large_balanced_random_case_settles_every_balance():
    balances = {
        index: Decimal((index * 7919) % 20001 - 10000) / Decimal("100")
        for index in range(100)
    }
    balances[0] -= sum(balances.values(), Decimal("0"))

    plan = simplify_debts(balances)
    settled = dict.fromkeys(balances, Decimal("0.00"))
    for transfer in plan:
        settled[transfer["from_user"]] += transfer["amount"]
        settled[transfer["to_user"]] -= transfer["amount"]

    assert all(value + settled[user] == 0 for user, value in balances.items())
    assert sum((item["amount"] for item in plan), Decimal("0")) > 0
    assert len(plan) <= len(balances) - 1


def test_cent_rounding_keeps_plan_balanced():
    plan = simplify_debts(
        {
            "a": Decimal("0.005"),
            "b": Decimal("0.005"),
            "c": Decimal("-0.010"),
        }
    )

    assert sum((item["amount"] for item in plan), Decimal("0")) == Decimal("0.02")
    net = {user: Decimal("0.00") for user in ("a", "b", "c")}
    for transfer in plan:
        net[transfer["from_user"]] -= transfer["amount"]
        net[transfer["to_user"]] += transfer["amount"]
    assert sum(net.values(), Decimal("0")) == Decimal("0.00")


def test_unbalanced_input_is_rejected():
    with pytest.raises(ValueError, match="sum to zero"):
        simplify_debts({1: Decimal("1.00"), 2: Decimal("-0.99")})
