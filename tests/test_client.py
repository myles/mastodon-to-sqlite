import datetime

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
            headers={
                "Link": f'<{url}?max_id=9876543210>; rel="next"',
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "99",
            },
            json=fixtures.ACCOUNT_ONE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={
                "Link": f'<{url}>; rel="previous"',
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "98",
            },
            match=[matchers.query_string_matcher("max_id=9876543210")],
            json=fixtures.ACCOUNT_TWO,
        )
    )

    client = MastodonClient(domain=domain, access_token=access_token)
    list(client.request_paginated("GET", path))

    assert len(responses.calls) == 2


@responses.activate
def test_mastodon_client__request_paginated__rate_limit(mocker):
    try:
        mock_now = datetime.datetime.now(datetime.UTC)
    except AttributeError:
        mock_now = datetime.datetime.now(datetime.timezone.utc)

    rate_limit_reset_at = mock_now + datetime.timedelta(
        hours=1, minutes=1, seconds=30
    )

    mocker.patch(
        "mastodon_to_sqlite.client.get_utc_now",
        return_value=mock_now,
    )

    mock_sleep = mocker.patch(
        "mastodon_to_sqlite.client.sleep", return_value=None
    )

    domain = "mastodon.example"
    access_token = "IAmAnAccessToken"
    path = "accounts/verify_credentials"
    url = f"https://{domain}/api/v1/{path}"

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={
                "Link": f'<{url}?max_id=9876543210>; rel="next"',
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "1",
                "X-RateLimit-Reset": rate_limit_reset_at.isoformat(),
            },
            json=fixtures.ACCOUNT_ONE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={
                "Link": f'<{url}>; rel="previous"',
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "99",
                "X-RateLimit-Reset": rate_limit_reset_at.isoformat(),
            },
            match=[matchers.query_string_matcher("max_id=9876543210")],
            json=fixtures.ACCOUNT_TWO,
        )
    )

    client = MastodonClient(domain=domain, access_token=access_token)
    list(client.request_paginated("GET", path))

    mock_sleep.assert_called_once_with(3690)
