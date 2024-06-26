import factory
from django.utils import timezone
from user.tests.fixtures import UserFactory
from friend_request.tests.fixtures import FriendRequestFactory


def test_search_by_email(user, authenticated_client, email):
    response = authenticated_client.get(f"/api/users/?email={email}")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["email"] == email


def test_search_by_email_case_insensitive(user, authenticated_client, email):
    assert email != email.upper()

    response = authenticated_client.get(f"/api/users/?email={email.upper()}")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["email"] == email


def test_search_by_email_partial(user, authenticated_client, email):
    response = authenticated_client.get(f"/api/users/?search={email[:2]}")

    assert response.status_code == 200
    assert len(response.data["results"]) == 0


def test_search_by_name_empty_result(user, authenticated_client):
    response = authenticated_client.get("/api/users/?search=SomeName")

    assert response.status_code == 200
    assert len(response.data["results"]) == 0


def test_search_by_name_find_by_part_of_name(authenticated_client):
    names = {"Amarendra", "Amar", "aman", "Abhirama"}
    UserFactory.create_batch(len(names), first_name=factory.Iterator(names))
    UserFactory.create(first_name="Egor", last_name="Empty")

    response = authenticated_client.get("/api/users/?search=am")

    assert response.status_code == 200
    assert len(response.data["results"]) == 4
    assert {user["first_name"] for user in response.data["results"]} == names


def test_ten_records_per_page(authenticated_client):
    UserFactory.create_batch(15)

    response = authenticated_client.get("/api/users/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 10


def test_view_friends(authenticated_client, user, another_user):
    FriendRequestFactory(
        from_user=user, to_user=another_user, accepted_at=timezone.now()
    )
    FriendRequestFactory(
        from_user=user, accepted_at=timezone.now(), rejected_at=timezone.now()
    )
    UserFactory()

    response = authenticated_client.get("/api/users/?is_friend=true")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] == str(another_user.id)


def test_view_not_friends(authenticated_client, user, another_user):
    FriendRequestFactory(
        from_user=user, to_user=another_user, accepted_at=timezone.now()
    )
    rejected = FriendRequestFactory(
        from_user=user, accepted_at=timezone.now(), rejected_at=timezone.now()
    ).to_user
    never_friend = UserFactory()

    response = authenticated_client.get("/api/users/?is_friend=false")

    assert response.status_code == 200
    assert len(response.data["results"]) == 2
    assert {user["id"] for user in response.data["results"]} == {
        str(rejected.id),
        str(never_friend.id),
    }
