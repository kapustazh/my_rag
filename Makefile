
BOLD   := \033[1m
CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
GRAY   := \033[2m
RESET  := \033[0m

.DEFAULT_GOAL := help

help:
	@printf "$(BOLD)$(CYAN)rag-against-the-machine$(RESET)\n"
	@printf "$(GRAY)Retrieval Augmented Generation$(RESET)\n\n"
	@printf "$(YELLOW)Usage:$(RESET) make $(GREEN)<target>$(RESET)\n\n"
	@printf "$(BOLD)Targets:$(RESET)\n"
	@printf "  $(GREEN)install$(RESET)      $(GRAY)- Install dependencies$(RESET)\n"
	@printf "  $(GREEN)run$(RESET)          $(GRAY)- Run the application$(RESET)\n"
	@printf "  $(GREEN)debug$(RESET)        $(GRAY)- Run with debugging$(RESET)\n"
	@printf "  $(GREEN)clean$(RESET)        $(GRAY)- Remove caches and bytecode$(RESET)\n"
	@printf "  $(GREEN)lint$(RESET)         $(GRAY)- Run linting$(RESET)\n"
	@printf "  $(GREEN)lint-strict$(RESET)  $(GRAY)- Run strict linting$(RESET)\n"
	@printf "  $(GREEN)test$(RESET)         $(GRAY)- Run tests$(RESET)\n"

install:
	@mkdir -p .cache/uv_cache .cache/hf_cache
	UV_CACHE_DIR=.cache/uv_cache \
	HF_HOME=.cache/hf_cache \
	@uv sync --python 3.10

run:
	@uv run -m src.__main__ $(ARGS)

debug:
	@uv run -m pdb -m src.__main__ $(ARGS)

clean:
	@find . -type f -name '*.py[co]' -delete
	@rm -rf .mypy_cache .pytest_cache .cache data/processed data/output
	@find . -type d -name __pycache__ -exec rm -rf {} +

lint:
	@uv run flake8 src
	@uv run mypy src \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs \
		--disallow-untyped-calls \
		--exclude '(^\.venv/)'

lint-strict:
	@uv run flake8 src
	@uv run mypy src --strict --exclude

test:
	@uv run pytest tests/

.PHONY: help install run debug clean lint lint-strict test
