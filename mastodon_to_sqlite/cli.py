import json
from pathlib import Path

import click

from . import service


@click.group()
@click.version_option()
def cli():
    """
    Save data from Mastodon to a SQLite database.
    """


@cli.command()
@click.option(
    "-a",
    "--auth",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default="auth.json",
    help="Path to save tokens to, defaults to auth.json",
)
def auth(auth):
    """
    Save Mastodon authentication credentials to a JSON file.
    """
    auth_file_path = Path(auth).absolute()

    mastodon_domain = click.prompt("Mastodon domain")
    click.echo("")

    click.echo(
        f"Create a new application here: https://{mastodon_domain}/settings/applications/new"
    )
    click.echo(
        "Then navigate to newly created application and paste in the following:"
    )
    click.echo("")

    access_token = click.prompt("Your access token")

    auth_file_content = json.dumps(
        {
            "mastodon_domain": mastodon_domain,
            "mastodon_access_token": access_token,
        },
        indent=4,
    )

    with auth_file_path.open("w") as file_obj:
        file_obj.write(auth_file_content + "\n")


@cli.command()
@click.option(
    "-a",
    "--auth",
    type=click.Path(
        file_okay=True, dir_okay=False, allow_dash=True, exists=True
    ),
    default="auth.json",
    help="Path to auth.json token file",
)
def verify_auth(auth):
    """
    Verify the authentication to the Mastodon server.
    """
    if service.verify_auth(auth) is True:
        click.echo("Successfully authenticated with the Mastodon server.")
    else:
        click.echo(
            "Failed to authenticated with the Mastodon server.", err=True
        )


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option(
    "-a",
    "--auth",
    type=click.Path(
        file_okay=True, dir_okay=False, allow_dash=True, exists=True
    ),
    default="auth.json",
    help="Path to auth.json token file",
)
def followers(db_path, auth):
    """
    Save followers for the authenticated user.
    """
    db = service.open_database(db_path)
    client = service.get_client(auth)

    authenticated_account = service.get_authenticated_account(client)
    account_id = authenticated_account["id"]

    service.save_accounts(db, [authenticated_account])

    with click.progressbar(
        service.get_followers(account_id, client),
        label="Importing followers",
        show_pos=True,
    ) as bar:
        for followers in bar:
            service.save_accounts(db, followers, follower_id=account_id)


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option(
    "-a",
    "--auth",
    type=click.Path(
        file_okay=True, dir_okay=False, allow_dash=True, exists=True
    ),
    default="auth.json",
    help="Path to auth.json token file",
)
def followings(db_path, auth):
    """
    Save followings for the authenticated user.
    """
    db = service.open_database(db_path)
    client = service.get_client(auth)

    authenticated_account = service.get_authenticated_account(client)
    account_id = authenticated_account["id"]

    service.save_accounts(db, [authenticated_account])

    with click.progressbar(
        service.get_followings(account_id, client),
        label="Importing followings",
        show_pos=True,
    ) as bar:
        for followers in bar:
            service.save_accounts(db, followers, followed_id=account_id)


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option(
    "-a",
    "--auth",
    type=click.Path(
        file_okay=True, dir_okay=False, allow_dash=True, exists=True
    ),
    default="auth.json",
    help="Path to auth.json token file",
)
def statuses(db_path, auth):
    """
    Save statuses for the authenticated user.
    """
    db = service.open_database(db_path)
    client = service.get_client(auth)

    authenticated_account = service.get_authenticated_account(client)
    account_id = authenticated_account["id"]

    service.save_accounts(db, [authenticated_account])

    with click.progressbar(
        service.get_statuses(account_id, client),
        label="Importing statuses",
        show_pos=True,
    ) as bar:
        for statuses in bar:
            service.save_statuses(db, statuses)
