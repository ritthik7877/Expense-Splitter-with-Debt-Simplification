import heapq
from decimal import Decimal, ROUND_HALF_UP
from typing import Hashable, Mapping, TypedDict


CENT = Decimal("0.01")


class Transfer(TypedDict):
    from_user: Hashable
    to_user: Hashable
    amount: Decimal


def simplify_debts(balances: Mapping[Hashable, Decimal]) -> list[Transfer]:
    """Return a greedy minimum-transfer plan for cent-rounded net balances.

    The repeated largest-debtor/largest-creditor matching takes O(n log n)
    time and O(n) auxiliary space for n users.
    """
    raw_balances = {user: Decimal(value) for user, value in balances.items()}
    if sum(raw_balances.values(), Decimal("0")) != Decimal("0"):
        raise ValueError("Net balances must sum to zero.")
    rounded = {
        user: amount.quantize(CENT, rounding=ROUND_HALF_UP)
        for user, amount in raw_balances.items()
    }
    rounding_difference = sum(rounded.values(), Decimal("0"))
    if rounding_difference:
        largest_balance = max(raw_balances, key=lambda user: abs(raw_balances[user]))
        rounded[largest_balance] -= rounding_difference

    debtors = [
        (-abs(amount), index, user)
        for index, (user, amount) in enumerate(rounded.items())
        if amount < 0
    ]
    creditors = [
        (-amount, index, user)
        for index, (user, amount) in enumerate(rounded.items())
        if amount > 0
    ]
    heapq.heapify(debtors)
    heapq.heapify(creditors)
    transfers: list[Transfer] = []

    while debtors and creditors:
        negative_debt, debtor_index, debtor = heapq.heappop(debtors)
        negative_credit, creditor_index, creditor = heapq.heappop(creditors)
        amount = min(-negative_debt, -negative_credit).quantize(CENT)
        transfers.append(
            {"from_user": debtor, "to_user": creditor, "amount": amount}
        )
        remaining_debt = -negative_debt - amount
        remaining_credit = -negative_credit - amount
        if remaining_debt:
            heapq.heappush(debtors, (-remaining_debt, debtor_index, debtor))
        if remaining_credit:
            heapq.heappush(creditors, (-remaining_credit, creditor_index, creditor))

    return transfers
