import responses
from responses import matchers

from mastodon_to_sqlite.client import MastodonClient


@responses.activate
def test_mastodon_client__request():
    domain = "mastodon.example"
    access_token = 'IAmAnAccessToken'

    path = "accounts/verify_credentials"

    url = f'https://{domain}/api/v1/{path}'

    responses.add(
        responses.Response(method="GET", url=url),
    )

    client = MastodonClient(domain=domain, access_token=access_token)
    client.request("GET", path)

    assert len(responses.calls) == 1


@responses.activate
def test_mastodon_client__request_paginated():
    domain = "mastodon.example"
    access_token = 'IAmAnAccessToken'

    path = "accounts/1234567890/followers"

    url = f'https://{domain}/api/v1/{path}'

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={'Link': f'<{url}?max_id=9876543210>; rel="next"'},
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=url,
            headers={'Link': f'<{url}>; rel="previous"'},
            match=[matchers.query_string_matcher("max_id=9876543210")],
        )
    )

    client = MastodonClient(domain=domain, access_token=access_token)
    list(client.request_paginated("GET", path))

    assert len(responses.calls) == 2
