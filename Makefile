.PHONY: help lint build serve clean

help:
	@echo "AuthorOps ビルドコマンド"
	@echo "  make lint   - textlintで校正チェック"
	@echo "  make build  - mdBookでビルド"
	@echo "  make serve  - ローカルプレビューサーバー起動"

lint:
	textlint "src/**/*.md"

build:
	mdbook build

serve:
	mdbook serve --open

clean:
	rm -rf book
