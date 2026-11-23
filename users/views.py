from django.shortcuts import render
from rest_framework import generics, permissions

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


def frontend_page(request, page, group_id=None):
    return render(request, f"{page}.html", {"group_id": group_id})
