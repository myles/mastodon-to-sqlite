.PHONY: all
all: clean setup test lint mypy

.PHONY: setup
setup: pyproject.toml
	poetry check
	poetry install

.PHONY: test
test:
	poetry run pytest --cov=mastodon_to_sqlite/ --cov-report=xml

.PHONY: lint
lint:
	poetry run black --check .
	poetry run isort --check .
	poetry run ruff check .

.PHONY: lintfix
lintfix:
	poetry run black .
	poetry run isort .
	poetry run ruff check . --fix

.PHONY: mypy
mypy:
	poetry run mypy mastodon_to_sqlite/

.PHONY: clean
clean:
	rm -fr ./.mypy_cache
	rm -fr ./.pytest_cache
	rm -fr ./.ruff_cache
	rm -fr ./dist
	rm -f .coverage
	rm -f coverage.xml
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

.PHONY: mastodon.db
mastodon.db: auth.json
	poetry run mastodon-to-sqlite verify-auth --auth $?
	poetry run mastodon-to-sqlite followers $@ --auth $?
	poetry run mastodon-to-sqlite followings $@ --auth $?
	poetry run mastodon-to-sqlite statuses $@ --auth $?
	poetry run mastodon-to-sqlite bookmarks $@ --auth $?
	poetry run mastodon-to-sqlite favourites $@ --auth $?

.PHONY: datasette
datasette: mastodon.db
	poetry run datasette serve $? --metadata metadata.json
