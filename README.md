# mastodon-to-sqlite

Save data from Mastodon to a SQLite database.

## Install

```console
foo@bar:~$ pip install -e git+https://github.com/myles/mastodon-to-sqlite.git#egg=mastodon-to-sqlite
```

## Authentication

First you will need to create an application on your Mastodon server. You
can find that on your Mastodon serer.

```console
foo@bar:~$ mastodon-to-sqlite auth
Mastodon domain: xxx

Create a new application here: https://mastodon.social/settings/applications/new
Then navigate to newly created application and paste in the following:

Your access token: xxx
```

You can verify that your authentication by running `mastodon-to-sqlite
verify-auth`.

## Retrieving Mastodon followers

The `followers` command will retrieve all the details about your Mastodon 
followers.

```console
foo@bar:~$ mastodon-to-sqlite followers mastodon.db
```

## Retrieving Mastodon followings

The `followings` command will retrieve all the details about your Mastodon 
followings.

```console
foo@bar:~$ mastodon-to-sqlite followings mastodon.db
```

## Retrieving Mastodon statuses

The `statuses` command will retrieve all the details about your Mastodon 
statuses.

```console
foo@bar:~$ mastodon-to-sqlite statuses mastodon.db
```
