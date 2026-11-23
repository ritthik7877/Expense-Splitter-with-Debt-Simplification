from decimal import Decimal
from types import SimpleNamespace

import pytest

from expenses.services.splits import build_splits


@pytest.fixture
def members():
    return [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
        SimpleNamespace(id=3),
    ]


def test_equal_split_assigns_remainder_cents_in_member_order(members):
    shares = build_splits(Decimal("10.00"), "EQUAL", members, None)

    assert [amount for _, amount in shares] == [
        Decimal("3.34"),
        Decimal("3.33"),
        Decimal("3.33"),
    ]
    assert sum((amount for _, amount in shares), Decimal("0")) == Decimal("10.00")


def test_exact_split_requires_exact_total(members):
    shares = build_splits(
        Decimal("12.00"),
        "EXACT",
        members,
        [{"user_id": 1, "amount": "5.00"}, {"user_id": 2, "amount": "7.00"}],
    )

    assert sum((amount for _, amount in shares), Decimal("0")) == Decimal("12.00")
    with pytest.raises(ValueError, match="sum to the expense total"):
        build_splits(
            Decimal("12.00"),
            "EXACT",
            members,
            [{"user_id": 1, "amount": "11.99"}],
        )


def test_percentage_split_assigns_remainder_cents(members):
    shares = build_splits(
        Decimal("10.00"),
        "PERCENTAGE",
        members,
        [
            {"user_id": 1, "percentage": "33.33"},
            {"user_id": 2, "percentage": "33.33"},
            {"user_id": 3, "percentage": "33.34"},
        ],
    )

    assert sum((amount for _, amount in shares), Decimal("0")) == Decimal("10.00")


@pytest.mark.parametrize(
    ("split_type", "splits", "message"),
    [
        ("PERCENTAGE", [{"user_id": 1, "percentage": "99"}], "sum to 100"),
        ("EXACT", [{"user_id": 999, "amount": "10"}], "member"),
        ("EXACT", [{"user_id": 1, "amount": "-1"}], "non-negative"),
        ("OTHER", None, "Unsupported"),
    ],
)
def test_split_validation_errors(members, split_type, splits, message):
    with pytest.raises(ValueError, match=message):
        build_splits(Decimal("10.00"), split_type, members, splits)


def test_invalid_total_and_missing_members_are_rejected(members):
    with pytest.raises(ValueError, match="positive"):
        build_splits(Decimal("NaN"), "EQUAL", members, None)
    with pytest.raises(ValueError, match="at least one"):
        build_splits(Decimal("10.00"), "EQUAL", [], None)
    with pytest.raises(ValueError, match="Splits are required"):
        build_splits(Decimal("10.00"), "EXACT", members, None)
