import pytest
from rest_framework.test import APIClient

from groups.models import Group

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def register(api, username):
    response = api.post(
        "/api/auth/register/",
        {
            "username": username,
            "email": f"{username}@example.com",
            "password": "Strong-test-password-2026!",
        },
        format="json",
    )
    assert response.status_code == 201
    return response.data["id"]


def login(api, username):
    response = api.post(
        "/api/auth/login/",
        {"username": username, "password": "Strong-test-password-2026!"},
        format="json",
    )
    assert response.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")


def test_auth_registration_and_login(api):
    register(api, "alice")
    response = api.post(
        "/api/auth/login/",
        {"username": "alice", "password": "Strong-test-password-2026!"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]


def test_group_api_requires_auth_and_hides_nonmember_groups(api):
    response = api.get("/api/groups/")
    assert response.status_code == 401

    alice_id = register(api, "alice")
    bob_id = register(api, "bob")
    login(api, "alice")
    group_response = api.post(
        "/api/groups/",
        {"name": "Alice's group"},
        format="json",
    )
    assert group_response.status_code == 201
    group = Group.objects.get(pk=group_response.data["id"])
    assert group.members.count() == 1

    login(api, "bob")
    assert api.get("/api/groups/").data == []
    assert api.get(f"/api/groups/{group.id}/").status_code == 403
    assert api.post(
        f"/api/groups/{group.id}/expenses/",
        {
            "description": "Hidden",
            "amount": "5.00",
            "paid_by_id": alice_id,
            "split_type": "EQUAL",
        },
        format="json",
    ).status_code == 403
    assert bob_id != alice_id


def test_all_expense_split_types_and_invalid_totals(api):
    alice_id = register(api, "alice")
    bob_id = register(api, "bob")
    login(api, "alice")
    group = api.post(
        "/api/groups/",
        {"name": "Trip", "member_ids": [bob_id]},
        format="json",
    ).data
    path = f"/api/groups/{group['id']}/expenses/"

    equal = api.post(
        path,
        {
            "description": "Equal",
            "amount": "10.00",
            "paid_by_id": alice_id,
            "split_type": "EQUAL",
        },
        format="json",
    )
    assert equal.status_code == 201
    assert [split["amount_owed"] for split in equal.data["splits"]] == [
        "5.00",
        "5.00",
    ]

    exact = api.post(
        path,
        {
            "description": "Exact",
            "amount": "10.00",
            "paid_by_id": alice_id,
            "split_type": "EXACT",
            "splits": [
                {"user_id": alice_id, "amount": "3.00"},
                {"user_id": bob_id, "amount": "7.00"},
            ],
        },
        format="json",
    )
    assert exact.status_code == 201
    assert [split["amount_owed"] for split in exact.data["splits"]] == [
        "3.00",
        "7.00",
    ]

    percentage = api.post(
        path,
        {
            "description": "Percentage",
            "amount": "10.00",
            "paid_by_id": alice_id,
            "split_type": "PERCENTAGE",
            "splits": [
                {"user_id": alice_id, "percentage": "25"},
                {"user_id": bob_id, "percentage": "75"},
            ],
        },
        format="json",
    )
    assert percentage.status_code == 201
    assert [split["amount_owed"] for split in percentage.data["splits"]] == [
        "2.50",
        "7.50",
    ]
    balances = api.get(f"/api/groups/{group['id']}/balances/")
    assert balances.status_code == 200
    assert sum((entry["balance"] for entry in balances.data), start=0) == 0

    invalid = api.post(
        path,
        {
            "description": "Bad exact",
            "amount": "10.00",
            "paid_by_id": alice_id,
            "split_type": "EXACT",
            "splits": [{"user_id": bob_id, "amount": "9.99"}],
        },
        format="json",
    )
    assert invalid.status_code == 400


def test_member_can_add_member_and_record_settlement(api):
    alice_id = register(api, "alice")
    bob_id = register(api, "bob")
    login(api, "alice")
    group = api.post("/api/groups/", {"name": "Friends"}, format="json").data
    root = f"/api/groups/{group['id']}/"

    assert api.post(
        f"{root}add-member/", {"user_id": bob_id}, format="json"
    ).status_code == 201
    payment = api.post(
        f"{root}settle/",
        {"from_user_id": bob_id, "to_user_id": alice_id, "amount": "4.25"},
        format="json",
    )
    assert payment.status_code == 201
    assert api.get(f"{root}balances/").status_code == 200
    assert api.get(f"{root}simplify/").status_code == 200
    assert api.get(f"{root}expenses/").status_code == 200
