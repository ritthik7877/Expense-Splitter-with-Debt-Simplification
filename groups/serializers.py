from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Group, GroupMember

User = get_user_model()


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class GroupSerializer(serializers.ModelSerializer):
    members = MemberSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Group
        fields = ("id", "name", "created_by", "created_at", "members", "member_ids")
        read_only_fields = ("id", "created_by", "created_at", "members")

    def create(self, validated_data):
        members = validated_data.pop("member_ids", [])
        group = Group.objects.create(**validated_data)
        GroupMember.objects.create(group=group, user=group.created_by)
        for member in members:
            GroupMember.objects.get_or_create(group=group, user=member)
        return group


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user"
    )


class BalanceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)


class TransferSerializer(serializers.Serializer):
    from_user = serializers.IntegerField()
    to_user = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    from_username = serializers.CharField()
    to_username = serializers.CharField()


class SettlementInputSerializer(serializers.Serializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return amount
