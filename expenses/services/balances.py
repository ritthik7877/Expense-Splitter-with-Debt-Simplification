from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from groups.models import Group


def get_group_balances(group: "Group") -> dict[int, Decimal]:
    """Compute each member's net balance, including recorded payments."""
    balances: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for member_id in group.members.values_list("id", flat=True):
        balances[member_id] = Decimal("0.00")
    for expense in group.expenses.prefetch_related("splits").all():
        balances[expense.paid_by_id] += expense.amount
        for split in expense.splits.all():
            balances[split.user_id] -= split.amount_owed
    for settlement in group.settlements.all():
        balances[settlement.from_user_id] += settlement.amount
        balances[settlement.to_user_id] -= settlement.amount
    return {
        user_id: amount.quantize(Decimal("0.01"))
        for user_id, amount in balances.items()
    }
