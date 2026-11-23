from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from expenses.models import Expense, ExpenseSplit
from groups.models import Group, GroupMember

User = get_user_model()


class Command(BaseCommand):
    help = "Create a demo SplitSmart group, users, and expenses."

    @transaction.atomic
    def handle(self, *args, **options):
        demo_users = []
        for username, email in (
            ("alice", "alice@example.com"),
            ("bob", "bob@example.com"),
            ("carol", "carol@example.com"),
        ):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            if created:
                user.set_password("SplitSmart123!")
                user.save(update_fields=["password"])
            demo_users.append(user)

        group, _ = Group.objects.get_or_create(
            name="Weekend Trip",
            created_by=demo_users[0],
        )
        for user in demo_users:
            GroupMember.objects.get_or_create(group=group, user=user)

        samples = (
            ("Groceries", Decimal("60.00"), demo_users[0]),
            ("Taxi", Decimal("30.00"), demo_users[1]),
        )
        for description, amount, payer in samples:
            expense, created = Expense.objects.get_or_create(
                group=group,
                description=description,
                defaults={
                    "amount": amount,
                    "paid_by": payer,
                    "split_type": Expense.SplitType.EQUAL,
                },
            )
            if created:
                base_cents, remainder = divmod(int(amount * 100), len(demo_users))
                ExpenseSplit.objects.bulk_create(
                    [
                        ExpenseSplit(
                            expense=expense,
                            user=user,
                            amount_owed=Decimal(base_cents + (index < remainder))
                            / Decimal("100"),
                        )
                        for index, user in enumerate(demo_users)
                    ]
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo ready: alice, bob, carol (password: SplitSmart123!)"
            )
        )
