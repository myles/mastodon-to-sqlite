import datetime
import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from sqlite_utils.db import Database, Table

from .client import MastodonClient


def open_database(db_file_path) -> Database:
    """
    Open the Mastodon SQLite database.
    """
    return Database(db_file_path)


def get_table(table_name: str, db: Database) -> Table:
    """
    Returns a Table from a given db Database object.
    """
    return Table(db=db, name=table_name)


def build_database(db: Database):
    """
    Build the Mastodon SQLite database structure.
    """
    accounts_table = get_table("accounts", db=db)
    following_table = get_table("following", db=db)
    statuses_table = get_table("statuses", db=db)

    if accounts_table.exists() is False:
        accounts_table.create(
            columns={
                "id": int,
                "username": str,
                "url": str,
                "display_name": str,
                "note": str,
            },
            pk="id",
        )
        accounts_table.enable_fts(
            ["username", "display_name", "note"], create_triggers=True
        )

    if following_table.exists() is False:
        following_table.create(
            columns={"followed_id": int, "follower_id": int, "first_seen": str},
            pk=("followed_id", "follower_id"),
            foreign_keys=(
                ("followed_id", "accounts", "id"),
                ("follower_id", "accounts", "id"),
            ),
        )

    following_indexes = {tuple(i.columns) for i in following_table.indexes}
    if ("followed_id",) not in following_indexes:
        following_table.create_index(["followed_id"])
    if ("follower_id",) not in following_indexes:
        following_table.create_index(["follower_id"])

    if statuses_table.exists() is False:
        statuses_table.create(
            columns={
                "id": int,
                "account_id": int,
                "content": str,
                "created_at": str,
            },
            pk="id",
            foreign_keys=(("account_id", "accounts", "id"),),
        )
        statuses_table.enable_fts(["content"], create_triggers=True)

    statuses_indexes = {tuple(i.columns) for i in statuses_table.indexes}
    if ("account_id",) not in statuses_indexes:
        statuses_table.create_index(["account_id"])

    status_activities_table = get_table("status_activities", db=db)
    if status_activities_table.exists() is False:
        status_activities_table.create(
            columns={
                "account_id": int,
                "activity": str,  # favourited, bookmarked
                "status_id": int,
            },
            pk=("account_id", "activity", "status_id"),
            foreign_keys=(
                ("account_id", "accounts", "id"),
                ("status_id", "statuses", "id"),
            ),
        )

    status_activities_indexes = {
        tuple(i.columns) for i in status_activities_table.indexes
    }
    if ("account_id", "activity") not in status_activities_indexes:
        status_activities_table.create_index(["account_id", "activity"])
    if ("status_id", "activity") not in status_activities_indexes:
        status_activities_table.create_index(["status_id", "activity"])


def get_client(auth_file_path: str) -> MastodonClient:
    """
    Returns a fully authenticated MastodonClient.
    """
    with Path(auth_file_path).absolute().open() as file_obj:
        raw_auth = file_obj.read()

    auth = json.loads(raw_auth)

    return MastodonClient(
        domain=auth["mastodon_domain"],
        access_token=auth["mastodon_access_token"],
    )


def verify_auth(auth_file_path: str) -> bool:
    """
    Verify Mastodon authentication.
    """
    client = get_client(auth_file_path)

    _, response = client.accounts_verify_credentials()

    if response.status_code == 200:
        return True

    return False


def get_authenticated_account(client: MastodonClient) -> Dict[str, Any]:
    """
    Returns the authenticated user's account and if the db is provided insert
    the account.
    """
    _, response = client.accounts_verify_credentials()
    response.raise_for_status()
    account = response.json()

    return account


def get_followers(
    account_id: str, client: MastodonClient
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Get authenticated account's followers.
    """
    for request, response in client.accounts_followers(account_id):
        yield response.json()


def get_followings(
    account_id: str, client: MastodonClient
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Get authenticated account's followers.
    """
    for request, response in client.accounts_following(account_id):
        yield response.json()


def transformer_account(account: Dict[str, Any]):
    """
    Transformer a Mastodon account, so it can be safely saved to the SQLite
    database.
    """
    to_remove = [
        k
        for k in account.keys()
        if k not in ("id", "username", "url", "display_name", "note")
    ]
    for key in to_remove:
        del account[key]


def save_accounts(
    db: Database,
    accounts: List[Dict[str, Any]],
    followed_id: Optional[str] = None,
    follower_id: Optional[str] = None,
):
    """
    Save Mastodon Accounts to the SQLite database.
    """
    assert not (followed_id and follower_id)

    build_database(db)
    accounts_table = get_table("accounts", db=db)
    following_table = get_table("following", db=db)

    for account in accounts:
        transformer_account(account)

    accounts_table.upsert_all(accounts, pk="id")

    if followed_id is not None or follower_id is not None:
        first_seen = datetime.datetime.now(datetime.timezone.utc).isoformat()

        following_table.upsert_all(
            (
                {
                    "followed_id": followed_id or account["id"],
                    "follower_id": follower_id or account["id"],
                    "first_seen": first_seen,
                }
                for account in accounts
            ),
            pk=("followed_id", "follower_id"),
        )


def get_statuses(
    account_id: str, client: MastodonClient
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Get authenticated account's statuses.
    """
    for request, response in client.accounts_statuses(account_id):
        yield response.json()


def transformer_status(status: Dict[str, Any]):
    """
    Transformer a Mastodon status, so it can be safely saved to the SQLite
    database.
    """
    account = status.pop("account")

    to_keep = (
        "id",
        "created_at",
        "content",
    )
    to_remove = [k for k in status.keys() if k not in to_keep]
    for key in to_remove:
        del status[key]

    status["account_id"] = account["id"]


def save_statuses(db: Database, statuses: List[Dict[str, Any]]):
    """
    Save Mastodon Statuses to the SQLite database.
    """
    build_database(db)
    statuses_table = get_table("statuses", db=db)

    for status in statuses:
        transformer_status(status)

    statuses_table.upsert_all(statuses, pk="id")


def get_bookmarks(
    client: MastodonClient,
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Get authenticated account's bookmarks.
    """
    for request, response in client.bookmarks():
        yield response.json()


def get_favourites(
    client: MastodonClient,
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Get authenticated account's favourites.
    """
    for request, response in client.favourites():
        yield response.json()


def save_activities(
    db: Database, account_id: str, activity: str, statuses: List[Dict[str, Any]]
):
    """
    Save Mastodon activities to the SQLite database.
    """
    build_database(db)
    statuses_table = get_table("statuses", db=db)
    status_activities_table = get_table("status_activities", db=db)

    for status in statuses:
        transformer_status(status)

    statuses_table.upsert_all(statuses, pk="id")

    status_activities_table.upsert_all(
        (
            {
                "account_id": account_id,
                "activity": activity,
                "status_id": status["id"],
            }
            for status in statuses
        ),
        pk=("account_id", "activity", "status_id"),
    )
