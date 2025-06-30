import pytest
from click.testing import CliRunner

from mastodon_to_sqlite import cli


@pytest.mark.parametrize(
    "verify_auth_return_value, expected_stdout, expected_stderr, expected_exit_code",
    (
        (True, "Successfully authenticated with the Mastodon server.\n", "", 0),
        (
            False,
            "",
            "Error: Failed to authenticate with the Mastodon server.\n",
            1,
        ),
    ),
)
def test_verify_auth(
    verify_auth_return_value,
    expected_stdout,
    expected_stderr,
    expected_exit_code,
    mocker,
):
    mocker.patch(
        "mastodon_to_sqlite.cli.service.verify_auth",
        return_value=verify_auth_return_value,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.verify_auth, ["--auth", "tests/fixture-auth.json"]
    )

    assert result.stdout == expected_stdout
    assert result.stderr == expected_stderr
    assert result.exit_code == expected_exit_code
