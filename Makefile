.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: lib-dependencies
lib-dependencies: ## Create the lib for dependencies
	pip install -t lib/ -r requirements.txt

.PHONY: test
test: ## Run all tests
	./scripts/run_tests.sh

.PHONY: datastore
datastore: ## Run the datastore
	./scripts/run_datastore.sh

.PHONY: run
run: ## Run app - deprecated - use dev-server instead
	./scripts/run_app.sh

.PHONY: tail-logs
tail-logs: ## Tail logs
	gcloud app logs tail -s default   

.PHONY: deploy
deploy: ## Deploy
	gcloud app deploy
