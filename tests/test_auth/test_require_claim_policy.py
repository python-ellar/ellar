from unittest.mock import Mock

from ellar.auth import RequiredClaimsPolicy, UserIdentity


def mock_execution_context(**kwargs):
    user = UserIdentity(**kwargs)
    mock = Mock()
    mock.user = user
    return mock


async def test_require_claim_raises_an_exception(anyio_backend):
    context = mock_execution_context()
    claim = RequiredClaimsPolicy("article", "create", "publish")

    assert await claim.handle(context) is False

    context = mock_execution_context(article=[])
    assert await claim.handle(context) is False

    context = mock_execution_context(article="view")
    assert await claim.handle(context) is False

    context = mock_execution_context(article=["publish"])
    assert await claim.handle(context) is True

    context = mock_execution_context(article=["create"])
    assert await claim.handle(context) is True
