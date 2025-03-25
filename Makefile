.PHONY: lint fix check clean test format

## usage
# prerequisites: install ruff and pytest
# make lint FILE=your_file.py for a single file
# make lint for all files


FILE ?= .
TEST ?=

lint:
	ruff check $(FILE)

fix:
	ruff check $(FILE) --fix

check:
	ruff format $(FILE) --check

format:
	ruff format $(FILE)

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -r {} +

test:
	PYTHONPATH=. pytest -v tests/$(TEST)
