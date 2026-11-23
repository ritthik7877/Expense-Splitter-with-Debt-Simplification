from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from expenses.services.balances import get_group_balances
from expenses.services.simplify import simplify_debts
from settlements.models import Settlement
from .models import Group, GroupMember
from .permissions import IsGroupMember
from .serializers import (
    AddMemberSerializer,
    BalanceSerializer,
    GroupSerializer,
    SettlementInputSerializer,
    TransferSerializer,
)


class GroupListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer

    def get_queryset(self):
        return (
            Group.objects.filter(members=self.request.user)
            .distinct()
            .prefetch_related("members")
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class GroupDetailView(generics.RetrieveAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    queryset = Group.objects.prefetch_related("members")


class AddMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    serializer_class = AddMemberSerializer

    def post(self, request, group_id):
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, pk=group_id)
        GroupMember.objects.get_or_create(
            group=group, user=serializer.validated_data["user"]
        )
        return Response(
            {"detail": "Member added."}, status=status.HTTP_201_CREATED
        )


class GroupBalancesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    serializer_class = BalanceSerializer

    def get(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        balances = get_group_balances(group)
        members = {
            member.id: member
            for member in group.members.all()
        }
        return Response(
            [
                {
                    "user_id": user_id,
                    "username": members[user_id].username,
                    "balance": amount,
                }
                for user_id, amount in sorted(balances.items())
            ]
        )


class SimplifyGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    serializer_class = TransferSerializer

    def get(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        plan = simplify_debts(get_group_balances(group))
        users = {
            member.id: member.username for member in group.members.all()
        }
        return Response(
            [
                {
                    **transfer,
                    "from_username": users[transfer["from_user"]],
                    "to_username": users[transfer["to_user"]],
                }
                for transfer in plan
            ]
        )


class SettleGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    serializer_class = SettlementInputSerializer

    def post(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from_user_id = data["from_user_id"]
        to_user_id = data["to_user_id"]
        member_ids = set(group.members.values_list("id", flat=True))
        if from_user_id not in member_ids or to_user_id not in member_ids:
            raise serializers.ValidationError("Both users must be group members.")
        if from_user_id == to_user_id:
            raise serializers.ValidationError("Payer and recipient must be different.")
        with transaction.atomic():
            settlement = Settlement.objects.create(
                group=group,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=data["amount"],
            )
        return Response(
            {
                "id": settlement.id,
                "from_user_id": settlement.from_user_id,
                "to_user_id": settlement.to_user_id,
                "amount": settlement.amount,
            },
            status=status.HTTP_201_CREATED,
        )
