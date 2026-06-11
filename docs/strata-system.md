# Strata システム — 地層ビューア

## 概要

Strata（地層）は、AuthorOps の3層アーキテクチャのうち **Phase A + B** に当たる機能です。原稿の変更履歴を「地層の堆積」として可視化し、論証構造がどのように積み重なってきたかを直感的に把握できます。

```
Phase A: git履歴の構造化 (build_strata.py → strata.json)
Phase B: D3.js による地層ビューア (viewer/strata.html)
Phase C: セマンティック差分 (semantic_diff.py → PRコメント)
```

## Phase A: 地層データの生成

`scripts/build_strata.py` が `src/**/*.md` のコミット履歴を解析し、`data/strata.json` を生成します。

### strata.json の構造

```json
{
  "generated": "2026-06-11T00:00:00Z",
  "total_commits": 10,
  "layers": [
    {
      "hash": "abc12345",
      "short_hash": "abc12345",
      "date": "2026-06-01",
      "author": "Author Name",
      "subject": "feat(ch1): add introduction",
      "files": [
        {
          "file": "src/chapter-01/01-intro.md",
          "paragraphs": 5,
          "chars": 400,
          "words": 80,
          "air_nodes": {
            "claim": 2,
            "premise": 3,
            "refutation": 1,
            "definition": 0,
            "citation": 0
          }
        }
      ],
      "summary": {
        "files_changed": 1,
        "total_paragraphs": 5,
        "total_chars": 400
      }
    }
  ]
}
```

### 実行方法

```bash
# ローカルで生成
python scripts/build_strata.py --src src --out data/strata.json

# Makefile経由
make strata
```

## Phase B: 地層ビューア

`viewer/strata.html` は D3.js を使ったインタラクティブなビジュアライザです。

### 見方

- **X軸**: AIR ノードの数（claim・premise・refutation などの積み上げ棒グラフ）
- **Y軸**: コミット（古い順 → 新しい順）
- **色**: ノードの種類ごとに色分け
- **クリック**: コミットをクリックすると右パネルに詳細表示

### GitHub Pages での公開

`strata.yml` ワークフローが `main` への push 時に自動でビルド・デプロイします。

```yaml
# .github/workflows/strata.yml
on:
  push:
    branches: [main]
    paths:
      - "src/**/*.md"
```

## Phase C: セマンティック差分

`scripts/semantic_diff.py` は PR の変更に対して論証構造レベルの差分を解析し、PR コメントとして投稿します。

### 出力例

```markdown
# 📖 セマンティック差分レポート

### `src/chapter-01/01-intro.md`

## 🧩 論証構造の変化

| 種別 | 内容 |
|---|---|
| ➕ 追加された主張 | `c3`: 新しい主張のテキスト |
| ⚠️ 前提が減った主張 | `c1` (前提 2→1) |
```

### ANTHROPIC_API_KEY の設定

リポジトリの Secrets に `ANTHROPIC_API_KEY` を設定すると、Claude による高レベルなセマンティック要約が追加されます。設定がない場合はルールベースの差分のみが出力されます。

## ローカル開発

```bash
# 依存インストール
pip install -e ".[test]"

# strata.json を生成してビューアを確認
python scripts/build_strata.py
# viewer/strata.html をブラウザで開く
```
