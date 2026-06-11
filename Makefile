.PHONY: help lint lint-fix build serve clean install \
        install-py test strata strata-view \
        lint-logic lint-logic-llm genesis air-diff

help:
	@echo "AuthorOps ビルド・運用コマンド"
	@echo ""
	@echo "  [基本]"
	@echo "  make install       - Node依存関係をインストール (npm ci)"
	@echo "  make install-py    - Python依存関係をインストール"
	@echo "  make lint          - textlintで日本語校正チェック"
	@echo "  make lint-fix      - textlintで自動修正"
	@echo "  make build         - mdBookでビルド"
	@echo "  make serve         - ローカルプレビューサーバー起動"
	@echo "  make clean         - ビルド成果物を削除"
	@echo ""
	@echo "  [Python解析層]"
	@echo "  make test          - Pytestで全テスト実行"
	@echo "  make strata        - git履歴からstrata.jsonを生成"
	@echo "  make lint-logic    - ルールベース論理リンター実行"
	@echo "  make lint-logic-llm - LLM論理検査を実行（APIキー必要）"
	@echo "  make genesis       - 思考ログ・メタ文書を生成"
	@echo "  make air-diff      - AIR差分を表示（BASE=<ref> HEAD=<ref>）"

install:
	npm ci

install-py:
	pip install -e ".[test]"

lint:
	textlint "src/**/*.md"

lint-fix:
	textlint --fix "src/**/*.md"

build:
	mdbook build

serve:
	mdbook serve --open

clean:
	rm -rf book data/_site

test:
	pytest tools/tests/ -v

strata:
	python scripts/build_strata.py --src src --out data/strata.json

strata-view: strata
	@echo "viewer/strata.html をブラウザで開いてください"

lint-logic:
	python -c "\
import sys; sys.path.insert(0, '.'); \
from pathlib import Path; \
from tools.authorops.air.parser import parse_markdown_to_air; \
from tools.authorops.lint.rules import lint_air, format_issues_as_markdown; \
from tools.authorops.config import load_config, is_excluded; \
config = load_config(); \
issues = [i for f in sorted(Path('src').rglob('*.md')) if not is_excluded(f, config) \
  for i in lint_air(parse_markdown_to_air(f))]; \
print(format_issues_as_markdown(issues))"

lint-logic-llm:
	AUTHOROPS_LLM_ENABLED=1 python -c "\
import sys; sys.path.insert(0, '.'); \
from pathlib import Path; \
from tools.authorops.air.parser import parse_markdown_to_air; \
from tools.authorops.lint.rules import lint_air; \
from tools.authorops.lint.llm_check import llm_check_air, get_default_adapter; \
from tools.authorops.lint.rules import format_issues_as_markdown; \
adapter = get_default_adapter(); \
issues = [i for f in sorted(Path('src').rglob('*.md')) \
  for i in lint_air(parse_markdown_to_air(f)) + llm_check_air(parse_markdown_to_air(f), adapter)]; \
print(format_issues_as_markdown(issues))"

genesis:
	python -c "\
import sys; sys.path.insert(0, '.'); \
from tools.authorops.thoughtlog.genesis import generate_genesis; \
r = generate_genesis(); \
print(f'✓ docs/genesis.md ({len(r.snapshots)} snapshots)')"

air-diff:
	python -c "\
import sys; sys.path.insert(0, '.'); \
from tools.authorops.air.parser import parse_markdown_to_air; \
from tools.authorops.diff.air_diff import diff_air, format_diff_as_markdown; \
import tempfile, subprocess; \
base = '$(BASE)'; head = '$(HEAD)' or 'HEAD'; \
print('AIR diff:', base, '->', head)"
