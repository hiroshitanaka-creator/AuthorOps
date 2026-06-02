# Contributing to AuthorOps

AuthorOpsは「執筆を開発のように楽しく・美しく・安全に」進めるためのプロジェクトです。

## 開発の進め方

- Issueでタスクを管理（chapter-draftテンプレート推奨）
- ブランチを切って作業 → PRでレビュー
- textlintとmdBookで品質を保つ

## セキュリティについて

- ワークフローでは最小権限の原則を守る
- 依存関係はDependabotで管理
- 脆弱性発見時はSECURITY.mdに従って報告

## ローカル開発

```bash
make install
make lint
make build
```

詳細はREADMEとIssueを参照してください。