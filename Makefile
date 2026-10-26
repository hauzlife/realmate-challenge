SHELL := /bin/bash
.DEFAULT_GOAL := help

REPO_SLUG       := hauzlife/realmate-challenge
GH_PAGES_BRANCH := gh-pages
PAGES_BASE_URL  := https://hauzlife.github.io/realmate-challenge
GITHUB_BASE_URL := https://github.com/$(REPO_SLUG)

ALLURE_RESULTS  := allure-results
REPORT_DIR      := allure-awesome
ALLURE_CONFIG   := allurerc.mjs
ALLURE_CLI      := npx --yes allure@3.22.1

GIT_SHA         := $(shell git rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_SHORT_SHA   := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH      := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

.PHONY: help check test test-unit unit quality-gate report open-report deploy-report deploy links

help: ## Exibe os alvos disponiveis e os links canonicos do commit atual
	@echo "======================================================================"
	@echo " Portal de Imoveis (Realmate Challenge) — Automacao de Testes & Allure"
	@echo "======================================================================"
	@echo " Branch atual : $(GIT_BRANCH)"
	@echo " Commit SHA   : $(GIT_SHA) ($(GIT_SHORT_SHA))"
	@echo "----------------------------------------------------------------------"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "======================================================================"

check: ## Executa lint (Ruff) e verificacao estatica de tipos (Mypy)
	uv run ruff check src
	uv run mypy src

test-unit: ## Executa a suite de testes (pytest + allure-results + coverage)
	uv run pytest src
	@if [ -f "$(ALLURE_RESULTS)/environment.properties" ]; then \
		grep -v '^Git_' "$(ALLURE_RESULTS)/environment.properties" > "$(ALLURE_RESULTS)/environment.properties.tmp" || true; \
		mv "$(ALLURE_RESULTS)/environment.properties.tmp" "$(ALLURE_RESULTS)/environment.properties"; \
		printf "Git_Branch=%s\nGit_Commit_SHA=%s\nGit_Blob_URL=%s/blob/%s/\n" \
			"$(GIT_BRANCH)" "$(GIT_SHA)" "$(GITHUB_BASE_URL)" "$(GIT_SHA)" \
			>> "$(ALLURE_RESULTS)/environment.properties"; \
	fi

test: test-unit ## Alias principal para execucao dos testes automatizados

unit: test-unit ## Alias curto para test-unit

quality-gate: ## Valida os Quality Gates do Allure 3 sobre allure-results
	$(ALLURE_CLI) quality-gate ./$(ALLURE_RESULTS) --config ./$(ALLURE_CONFIG)

report: ## Gera o relatorio estatico Allure Awesome em ./allure-awesome
	@if [ ! -d "$(ALLURE_RESULTS)" ]; then \
		echo "Erro: diretorio '$(ALLURE_RESULTS)' nao encontrado. Rode 'make test-unit' primeiro."; \
		exit 1; \
	fi
	@if [ -f "$(ALLURE_RESULTS)/environment.properties" ]; then \
		grep -v '^Git_' "$(ALLURE_RESULTS)/environment.properties" > "$(ALLURE_RESULTS)/environment.properties.tmp" || true; \
		mv "$(ALLURE_RESULTS)/environment.properties.tmp" "$(ALLURE_RESULTS)/environment.properties"; \
		printf "Git_Branch=%s\nGit_Commit_SHA=%s\nGit_Blob_URL=%s/blob/%s/\n" \
			"$(GIT_BRANCH)" "$(GIT_SHA)" "$(GITHUB_BASE_URL)" "$(GIT_SHA)" \
			>> "$(ALLURE_RESULTS)/environment.properties"; \
	fi
	$(ALLURE_CLI) generate ./$(ALLURE_RESULTS) --config ./$(ALLURE_CONFIG) --clean
	touch $(REPORT_DIR)/.nojekyll
	@python3 -c 'from pathlib import Path; p = Path("$(REPORT_DIR)/index.html"); h = p.read_text(encoding="utf-8").replace("\"theme\":\"auto\"", "\"theme\":\"dark\"").replace("\"layout\":\"base\"", "\"layout\":\"split\""); seed = "<script>try{if(!localStorage.getItem(\"theme\"))localStorage.setItem(\"theme\",\"dark\");if(!localStorage.getItem(\"layout\"))localStorage.setItem(\"layout\",\"split\");if(!localStorage.getItem(\"expandedTrees\"))localStorage.setItem(\"expandedTrees\",JSON.stringify([\"cb5f830f6ef9280487490efb494a0267\",\"891288d4898f191809a83b92a6ce6e3b\",\"ed52a2604e53aabd5dc26056bffc8034\"]));}catch(e){}</script>\n<script>\n      window.allureReportOptions"; h = h.replace("<script>\n      window.allureReportOptions", seed) if "expandedTrees" not in h else h; p.write_text(h, encoding="utf-8")'
	@if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then \
		python3 -c 'import http.server, threading, subprocess; h = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory="$(REPORT_DIR)", **kw); s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=s.serve_forever, daemon=True).start(); subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--force-dark-mode", "--window-size=1720,960", "--virtual-time-budget=6000", "--hide-scrollbars", "--screenshot=$(REPORT_DIR)/screenshot.png", f"http://127.0.0.1:{s.server_address[1]}/index.html#beac081e335495cbbe627357e6da96a2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); s.shutdown()' || true; \
	fi
	@echo "Relatorio gerado com sucesso em ./$(REPORT_DIR)/ (commit $(GIT_SHORT_SHA))"

open-report: ## Abre o relatorio Allure Awesome localmente no navegador
	$(ALLURE_CLI) open ./$(REPORT_DIR) --config ./$(ALLURE_CONFIG)

deploy-report: ## Publica ./allure-awesome no GitHub Pages (raiz + snapshot por commit SHA)
	@if [ ! -f "$(REPORT_DIR)/index.html" ]; then \
		echo "Erro: '$(REPORT_DIR)/index.html' nao encontrado. Rode 'make report' primeiro."; \
		exit 1; \
	fi
	@touch "$(REPORT_DIR)/.nojekyll"
	@set -euo pipefail; \
	TMP_DIR="$$(mktemp -d)"; \
	trap 'rm -rf "$$TMP_DIR"' EXIT; \
	REMOTE_URL="$$(git remote get-url origin)"; \
	echo "==> Preparando worktree isolado de deploy em $$TMP_DIR..."; \
	if git ls-remote --exit-code --heads origin "$(GH_PAGES_BRANCH)" >/dev/null 2>&1; then \
		git clone --depth 1 --branch "$(GH_PAGES_BRANCH)" "$$REMOTE_URL" "$$TMP_DIR/site" >/dev/null 2>&1; \
		find "$$TMP_DIR/site" -mindepth 1 -maxdepth 1 ! -name '.git' ! -name 'commits' -exec rm -rf {} +; \
	else \
		mkdir -p "$$TMP_DIR/site"; \
		git -C "$$TMP_DIR/site" init -b "$(GH_PAGES_BRANCH)" >/dev/null 2>&1; \
		git -C "$$TMP_DIR/site" remote add origin "$$REMOTE_URL"; \
	fi; \
	cp -R "$(REPORT_DIR)/." "$$TMP_DIR/site/"; \
	mkdir -p "$$TMP_DIR/site/commits/$(GIT_SHORT_SHA)"; \
	cp -R "$(REPORT_DIR)/." "$$TMP_DIR/site/commits/$(GIT_SHORT_SHA)/"; \
	touch "$$TMP_DIR/site/.nojekyll" "$$TMP_DIR/site/commits/$(GIT_SHORT_SHA)/.nojekyll"; \
	git -C "$$TMP_DIR/site" add -A; \
	if git -C "$$TMP_DIR/site" diff --cached --quiet; then \
		echo "==> Nenhuma alteracao nova no bundle para publicar."; \
	else \
		git -C "$$TMP_DIR/site" commit -m "chore(report): deploy allure-awesome for $(GIT_SHORT_SHA) ($(GIT_BRANCH))" >/dev/null; \
		git -C "$$TMP_DIR/site" push -u origin "$(GH_PAGES_BRANCH)" --force; \
		echo "==> Push concluido na branch '$(GH_PAGES_BRANCH)'!"; \
	fi; \
	if ! gh api "repos/$(REPO_SLUG)/pages" >/dev/null 2>&1; then \
		echo "==> Ativando GitHub Pages na branch '$(GH_PAGES_BRANCH)'..."; \
		gh api -X POST "repos/$(REPO_SLUG)/pages" -f "source[branch]=$(GH_PAGES_BRANCH)" -f "source[path]=/" >/dev/null; \
	fi
	@$(MAKE) --no-print-directory links

deploy: deploy-report ## Alias curto para deploy-report

links: ## Imprime os links canonicos de Blob, Commit e Allure Report para Issue/PR
	@echo ""
	@echo "======================================================================"
	@echo " Links Canonicos para Issue / PR (Commit $(GIT_SHORT_SHA))"
	@echo "======================================================================"
	@echo " Commit URL        : $(GITHUB_BASE_URL)/commit/$(GIT_SHA)"
	@echo " Blob Root URL     : $(GITHUB_BASE_URL)/blob/$(GIT_SHA)/"
	@echo " Allure Live (Root): $(PAGES_BASE_URL)/"
	@echo " Allure Snapshot   : $(PAGES_BASE_URL)/commits/$(GIT_SHORT_SHA)/"
	@echo "----------------------------------------------------------------------"
	@echo " Markdown Badge/Link:"
	@echo " [📊 Allure Awesome Report ($(GIT_SHORT_SHA))]($(PAGES_BASE_URL)/commits/$(GIT_SHORT_SHA)/)"
	@echo "======================================================================"
