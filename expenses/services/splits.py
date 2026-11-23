from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Any


CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def build_splits(
    total: Decimal, split_type: str, members: list[Any], input_splits: list[dict] | None
) -> list[tuple[Any, Decimal]]:
    """Validate a split request and return exact, cent-precision member shares."""
    if not total.is_finite() or total <= 0 or total.as_tuple().exponent < -2:
        raise ValueError("Expense amount must be positive with at most two decimals.")
    if not members:
        raise ValueError("An expense requires at least one group member.")
    if split_type == "EQUAL":
        cents = int((total / CENT).to_integral_exact())
        base, remainder = divmod(cents, len(members))
        return [
            (member, Decimal(base + (index < remainder)) * CENT)
            for index, member in enumerate(members)
        ]

    if split_type not in {"EXACT", "PERCENTAGE"}:
        raise ValueError("Unsupported split type.")
    if not input_splits:
        raise ValueError("Splits are required for EXACT and PERCENTAGE expenses.")
    member_map = {member.id: member for member in members}
    parsed: list[tuple[Any, Decimal]] = []
    seen: set[int] = set()
    for entry in input_splits:
        user_id = entry.get("user_id")
        if user_id not in member_map:
            raise ValueError("Every split user must be a member of this group.")
        if user_id in seen:
            raise ValueError("A user may appear only once in the splits.")
        seen.add(user_id)
        try:
            key = "amount" if split_type == "EXACT" else "percentage"
            value = Decimal(str(entry[key]))
        except (KeyError, ArithmeticError, ValueError):
            raise ValueError("Every split requires a valid decimal amount.")
        if not value.is_finite() or value < 0:
            raise ValueError("Split values must be finite and non-negative.")
        parsed.append((member_map[user_id], value))

    if split_type == "EXACT":
        if any(value.as_tuple().exponent < -2 for _, value in parsed):
            raise ValueError("Exact shares must have at most two decimal places.")
        if sum((value for _, value in parsed), Decimal("0")) != total:
            raise ValueError("Exact split amounts must sum to the expense total.")
        return parsed

    if split_type == "PERCENTAGE":
        if sum((value for _, value in parsed), Decimal("0")) != HUNDRED:
            raise ValueError("Split percentages must sum to 100.")
        shares = []
        for member, percentage in parsed:
            share = (total * percentage / HUNDRED).quantize(
                CENT, rounding=ROUND_DOWN
            )
            shares.append((member, share))
        leftover = total - sum((share for _, share in shares), Decimal("0"))
        cents_left = int((leftover / CENT).to_integral_value(rounding=ROUND_HALF_UP))
        for index in range(cents_left):
            member, share = shares[index % len(shares)]
            shares[index % len(shares)] = (member, share + CENT)
        return shares

    raise ValueError("Unsupported split type.")
