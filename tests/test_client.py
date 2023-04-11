import pytest
import responses
from responses import matchers

from mastodon_to_sqlite.client import MastodonClient

from . import fixtures


@responses.activate
def test_mastodon_client__request():
    domain = "mastodon.example"
    access_token = "IAmAnAccessToken"
    path = "accounts/verify_credentials"
    url = f"https://{domain}/api/v1/{path}"

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            json=fixtures.ACCOUNT_ONE,
        )
    )

    client = MastodonClient(domain=domain, access_token=access_token)
    client.request("GET", path)

    assert len(responses.calls) == 1
    call = responses.calls[-1]

    assert call.request.url == url

    assert "Authorization" in call.request.headers
    assert call.request.headers["Authorization"] == f"Bearer {access_token}"

    assert "User-Agent" in call.request.headers
    assert (
        call.request.headers["User-Agent"]
        == "mastodon-to-sqlite (+https://github.com/myles/mastodon-to-sqlite)"
    )


@responses.activate
def test_mastodon_client__request_paginated():
    domain = "mastodon.example"
    access_token = "IAmAnAccessToken"

    path = "accounts/1234567890/followers"

    url = f"https://{domain}/api/v1/{path}"

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={"Link": f'<{url}?max_id=9876543210>; rel="next"'},
            json=fixtures.ACCOUNT_ONE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={"Link": f'<{url}>; rel="previous"'},
            match=[matchers.query_string_matcher("max_id=9876543210")],
            json=fixtures.ACCOUNT_TWO,
        )
    )

    client = MastodonClient(domain=domain, access_token=access_token)
    list(client.request_paginated("GET", path))

    assert len(responses.calls) == 2


@responses.activate
@pytest.mark.parametrize("since_id", (None, 1234))
def test_mastodon_client__accounts_statuses(since_id):
    domain = "mastodon.example"
    account_id = "1234567890"

    url = f"https://{domain}/api/v1/accounts/{account_id}/statuses"

    first_response_match = []
    if since_id is not None:
        first_response_match.append(
            matchers.query_param_matcher(
                {"since_id": since_id, "limit": 40}, strict_match=True
            )
        )

    second_response_match = [
        matchers.query_param_matcher({"max_id": 9876543210}, strict_match=True)
    ]

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={"Link": f'<{url}?max_id=9876543210>; rel="next"'},
            match=first_response_match,
            json=fixtures.STATUS_ONE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={"Link": f'<{url}>; rel="previous"'},
            match=second_response_match,
            json=fixtures.STATUS_TWO,
        )
    )

    client = MastodonClient(domain=domain, access_token="IAmAnAccessToken")
    list(client.accounts_statuses(account_id=account_id, since_id=since_id))

    assert len(responses.calls) == 2
