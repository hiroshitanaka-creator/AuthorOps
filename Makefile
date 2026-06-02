.PHONY: help lint lint-fix build serve clean install

help:
	@echo "AuthorOps ビルド・運用コマンド"
	@echo "  make help      - このヘルプを表示"
	@echo "  make install   - 依存関係をインストール (npm ci)"
	@echo "  make lint      - textlintで校正チェック"
	@echo "  make lint-fix  - textlintで自動修正"
	@echo "  make build     - mdBookでビルド"
	@echo "  make serve     - ローカルプレビューサーバー起動"
	@echo "  make clean     - ビルド成果物を削除"

install:
	npm ci

lint:
	textlint "src/**/*.md"

lint-fix:
	textlint --fix "src/**/*.md"

build:
	mdbook build

serve:
	mdbook serve --open

clean:
	rm -rf book
