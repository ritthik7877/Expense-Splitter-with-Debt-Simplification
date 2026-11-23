from django.urls import path

from expenses.views import GroupExpenseListCreateView
from .views import (
    AddMemberView,
    GroupBalancesView,
    GroupDetailView,
    GroupListCreateView,
    SettleGroupView,
    SimplifyGroupView,
)

urlpatterns = [
    path("", GroupListCreateView.as_view(), name="group-list"),
    path("<int:pk>/", GroupDetailView.as_view(), name="group-detail"),
    path("<int:group_id>/add-member/", AddMemberView.as_view(), name="add-member"),
    path(
        "<int:group_id>/expenses/",
        GroupExpenseListCreateView.as_view(),
        name="group-expenses",
    ),
    path(
        "<int:group_id>/balances/",
        GroupBalancesView.as_view(),
        name="group-balances",
    ),
    path(
        "<int:group_id>/simplify/",
        SimplifyGroupView.as_view(),
        name="group-simplify",
    ),
    path("<int:group_id>/settle/", SettleGroupView.as_view(), name="group-settle"),
]
