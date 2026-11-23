from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from groups.models import Group, GroupMember
from groups.permissions import IsGroupMember
from .models import Expense, ExpenseSplit
from .serializers import ExpenseCreateSerializer, ExpenseSerializer
from .services.splits import build_splits


class GroupExpenseListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    serializer_class = ExpenseCreateSerializer

    @extend_schema(responses=ExpenseSerializer(many=True))
    def get(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        expenses = (
            Expense.objects.filter(group=group)
            .select_related("paid_by")
            .prefetch_related("splits__user")
            .order_by("-created_at")
        )
        return Response(ExpenseSerializer(expenses, many=True).data)

    @extend_schema(
        request=ExpenseCreateSerializer,
        responses={201: ExpenseSerializer},
    )
    def post(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        serializer = ExpenseCreateSerializer(
            data=request.data, context={"group": group}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        members = list(group.members.order_by("id"))
        user_splits = data.get("splits")
        try:
            shares = build_splits(
                data["amount"],
                data["split_type"],
                members,
                user_splits,
            )
        except ValueError as exc:
            raise serializers.ValidationError({"splits": str(exc)}) from exc
        with transaction.atomic():
            expense = Expense.objects.create(
                group=group,
                description=data["description"],
                amount=data["amount"],
                paid_by_id=data["paid_by_id"],
                split_type=data["split_type"],
            )
            ExpenseSplit.objects.bulk_create(
                [
                    ExpenseSplit(expense=expense, user=user, amount_owed=amount)
                    for user, amount in shares
                ]
            )
        expense = Expense.objects.prefetch_related("splits__user").get(pk=expense.pk)
        return Response(
            ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED
        )
