from typing import Generator, Optional, Tuple, Union

from requests import PreparedRequest, Request, Response, Session
from requests.auth import AuthBase


class MastodonAuth(AuthBase):
    def __init__(self, access_token: str):
        self.access_token = access_token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.access_token}"
        return r


class MastodonClient:
    def __init__(self, domain: str, access_token: str):
        self.api_url = f"https://{domain}/api/v1"

        self.session = Session()
        self.session.auth = MastodonAuth(access_token)

        self.session.headers[
            "User-Agent"
        ] = "mastodon-to-sqlite (+https://github.com/myles/mastodon-to-sqlite)"

    def request(
        self,
        method: str,
        path: str,
        timeout: Optional[Tuple[int, int]] = None,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        full_url = f"{self.api_url}/{path}"

        request = Request(method=method.upper(), url=full_url, **kwargs)
        prepped = self.session.prepare_request(request)
        response = self.session.send(prepped, timeout=timeout)

        return prepped, response

    def request_paginated(
        self,
        method: str,
        path: str,
        timeout: Optional[Tuple[int, int]] = None,
        **kwargs,
    ) -> Generator[Tuple[PreparedRequest, Response], None, None]:
        next_path: Optional[str] = path

        while next_path is not None:
            request, response = self.request(
                method=method, path=next_path, timeout=timeout, **kwargs
            )
            yield request, response

            # If there is no Link header or the Link header does not contain a
            # next link, then we know there isn't pagination this endpoint or
            # there is no next page.
            if "Link" not in response.headers or "next" not in response.links:
                next_path = None
                continue

            next_url = response.links["next"]["url"]
            next_path = next_url.replace(f"{self.api_url}/", "")

    def accounts_verify_credentials(self) -> Tuple[PreparedRequest, Response]:
        return self.request("GET", "accounts/verify_credentials")

    def accounts_followers(
        self, account_id: str
    ) -> Generator[Tuple[PreparedRequest, Response], None, None]:
        return self.request_paginated("GET", f"accounts/{account_id}/followers")

    def accounts_following(
        self, account_id: str
    ) -> Generator[Tuple[PreparedRequest, Response], None, None]:
        return self.request_paginated("GET", f"accounts/{account_id}/following")

    def accounts_statuses(
        self, account_id: str
    ) -> Generator[Tuple[PreparedRequest, Response], None, None]:
        return self.request_paginated("GET", f"accounts/{account_id}/statuses")
