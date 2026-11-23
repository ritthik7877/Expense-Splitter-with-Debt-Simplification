from django.conf import settings
from django.db import models


class Expense(models.Model):
    class SplitType(models.TextChoices):
        EQUAL = "EQUAL", "Equal"
        EXACT = "EXACT", "Exact"
        PERCENTAGE = "PERCENTAGE", "Percentage"

    group = models.ForeignKey(
        "groups.Group", on_delete=models.CASCADE, related_name="expenses"
    )
    description = models.CharField(max_length=240)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="paid_expenses",
    )
    split_type = models.CharField(max_length=12, choices=SplitType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} ({self.amount})"


class ExpenseSplit(models.Model):
    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE, related_name="splits"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expense_splits",
    )
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("expense", "user"), name="unique_expense_split_user"
            )
        ]

    def __str__(self):
        return f"{self.user}: {self.amount_owed}"
