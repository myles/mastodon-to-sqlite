import pytest
from click.testing import CliRunner

from mastodon_to_sqlite import cli


@pytest.mark.parametrize(
    "verify_auth_return_value, expected_stdout_startswith",
    (
        (True, "Successfully"),
        (False, "Failed"),
    ),
)
def test_verify_auth(
    verify_auth_return_value, expected_stdout_startswith, mocker
):
    mocker.patch(
        "mastodon_to_sqlite.cli.service.verify_auth",
        return_value=verify_auth_return_value,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.verify_auth, ["--auth", "tests/fixture-auth.json"]
    )

    assert result.stdout.startswith(expected_stdout_startswith)
