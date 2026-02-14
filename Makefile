.PHONY: format lint test docs examples-readme benchmark benchmark-json benchmark-report benchmark-report-all benchmark-json-resolve benchmark-report-resolve

format:
	uv run ruff format .
	uv run ruff check --fix-only .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

test:
	uv run pytest tests/ --cov=src/achrome --cov-report=term-missing

docs:
	rm -rf docs/_build
	uv run sphinx-build -b html docs docs/_build/html
