from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Expense, ExpenseSplit

User = get_user_model()


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = ("user_id", "username", "amount_owed")


class ExpenseSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "group",
            "description",
            "amount",
            "paid_by",
            "split_type",
            "created_at",
            "splits",
        )


class ExpenseCreateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=240)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_by_id = serializers.IntegerField()
    split_type = serializers.ChoiceField(choices=Expense.SplitType.choices)
    splits = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=False
    )

    def validate(self, attrs):
        group = self.context["group"]
        member_ids = set(group.members.values_list("id", flat=True))
        if attrs["paid_by_id"] not in member_ids:
            raise serializers.ValidationError(
                {"paid_by_id": "Payer must be a member of this group."}
            )
        for split in attrs.get("splits", []):
            user_id = split.get("user_id")
            if not isinstance(user_id, int) or isinstance(user_id, bool):
                raise serializers.ValidationError(
                    {"splits": "Each split needs an integer user_id."}
                )
        return attrs
