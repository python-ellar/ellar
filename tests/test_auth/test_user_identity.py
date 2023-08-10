from ellar.auth.identity import UserIdentity


def test_user_properties():
    user = UserIdentity(
        first_name="Mei",
        id=23,
        username="mei234",
        roles=["agent", "rank3", "rank4"],
        last_name="yuu",
        email="mei.yuu@example.com",
        issuer="http://testserver",
        auth_type="local",
    )

    assert user.email == "mei.yuu@example.com"
    assert user.issuer == "http://testserver"
    assert user.username == "mei234"
    assert user.last_name == "yuu"
    assert user.roles == ["agent", "rank3", "rank4"]
    assert user.id == 23
    assert user.auth_type == "local"
    assert user.first_name == "Mei"
