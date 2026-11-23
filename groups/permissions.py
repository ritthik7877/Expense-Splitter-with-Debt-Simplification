from rest_framework.permissions import BasePermission

from .models import GroupMember


class IsGroupMember(BasePermission):
    def has_permission(self, request, view):
        group_id = view.kwargs.get("group_id") or view.kwargs.get("pk")
        return bool(
            request.user
            and request.user.is_authenticated
            and group_id
            and GroupMember.objects.filter(
                group_id=group_id, user=request.user
            ).exists()
        )
