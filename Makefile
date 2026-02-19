.PHONY: format lint test docs generate-suites

SDEF_APP ?= all

format:
	uv run ruff format .
	uv run ruff check --fix-only .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

test:
	uv run pytest tests/ --cov=openmac --cov-report=term-missing

generate-suites:
	uv run python tools/sdef/generate_openmac_suites.py --app $(SDEF_APP)
	make format
	make format

docs:
	rm -rf docs/_build
	uv run --group docs sphinx-build -W -b html docs docs/_build/html
