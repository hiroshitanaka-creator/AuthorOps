# AuthorOps

**GitHubを執筆・論文・書籍執筆の最強運用基盤（Author Operations）に変えるリポジトリ**

GitHubの開発ベストプラクティスを「執筆」にそのまま持ち込むことで、バージョン管理・タスク管理・自動校正・自動製本を統合した、爆速かつ美しい執筆環境を実現します。

> 「これなら執筆が爆速で進むし、管理も美しくできる」という、イケてる執筆・論文用リポジトリ構成案と運用システムです。

---

## 📝 メモの使い方（アイデアを逃さない機構）

AuthorOpsでは、「思い付きを逃さない」ことを最優先に考えています。

### 基本方針

| アイデアの状態 | 使う場所 | 方法 |
|------------------------|------------------|--------|
| 軽い思い付き・断片 | `notes/ideas-index.md` | このファイルに直接追加 |
| もう少し掘り下げたい | Issue (`idea` テンプレート) | 新規Issue作成時に `idea.md` テンプレートを選択 |
| 実際に章として書く準備 | Issue (`chapter-draft` テンプレート) | `chapter-draft.md` テンプレートを使ってIssue作成 |

### メモの流れ例

1. 「この概念、後で使えそう」と思った
   → `notes/ideas-index.md` の「未分類の生アイデア」セクションに追加
2. そのアイデアをもう少し考えたい
   → `idea.md` テンプレートでIssueを作成
3. いざ章として書く準備ができた
   → `chapter-draft.md` テンプレートでIssueを作成し、進损管理を始める

---

## 📁 理想的なリポジトリ構成

```text
AuthorOps/
├── .github/
│   └── workflows/
│       ├── lint.yml         # 文章校正（textlint）の自動化
│       ├── deploy.yml       # PDF/HTML自動ビルド＆GitHub Pages
│       ├── strata.yml       # 思考の地層を構築・公開（Phase A+B）
│       └── semantic-diff.yml # PRで論旨の変化を自動コメント（Phase C）
├── scripts/
│   ├── build_strata.py      # Phase A: git履歴 → 段落地層JSON
│   └── semantic_diff.py     # Phase C: 論旨・根拠レベルの意味論diff
├── viewer/
│   └── strata.html          # Phase B: D3地層ビューア（GitHub Pages）
├── src/                     # 原稿の本体
│   ├── SUMMARY.md           # 目次・全体の構成定義
│   ├── chapter-01/          # 章ごとのディレクトリ
│   └── assets/              # 挿絵や図表、データファイル
├── notes/                   # 生アイデア・思考の受け皿
│   └── ideas-index.md
├── .github/ISSUE_TEMPLATE/  # Issueテンプレート
│   ├── idea.md
│   └── chapter-draft.md
├── textlintrc.json          # 校正ルールの設定
├── book.toml                # mdBook等のビルド設定
├── Makefile                 # ローカルビルド用コマンド集
└── README.md
```

---

## 🚀 執筆を「開発」に変える運用機構

### ① 構成とタスク管理（Issue & GitHub Projects）

- **章ごとにIssueを立てる**: 「第3章：○○の考察」といったIssueを作り、そこに参考文献のURLや、書きたいアイデアのメモをコメント感觚でスクラップします。
- **GitHub Projects**: 「未着手」「執筆中」「校正中」「完了」のカンバンを作り、原稿の進损を視覚的に管理できます。

### ② 推敷とバージョン管理（Branch & Pull Request）

- **1トピック = 1ブランチ**: 本文を修正するときは、メインブランチを直接弄らずに `draft/chapter-3` のようなブランチを切ります。
- **セルフPR（Pull Request）で推敷**: 原稿が書けたらメインブランチに向けてPRを作ります。差分（Diff）を見ることで「どこをどう書き直したか」が視覚的に一目了然になります。自分でコメント機能を使って「ここ表現が硬いから要修正」とメモを残すのも便利です。

### ③ 自動化エコシステム（CI/CD with GitHub Actions）

ここがGitHubを使う最大の強みです。

- **校正の自動化（textlint）**: GitHub Actionsを組ほみ、pushするたびに「ら括き言葉」「重複表現」「表記掺れ」を自動チェックさせます。エラーがあればPRにバッジがつきます。
- **自動製本・プレビュー**: 静的サイトジェネレーター（**mdBook** や **HonKit**）を連携させ、pushと同時に美しいWebサイト（GitBook風）やPDFを自動生成し、GitHub Pagesに公開または限定公開します。常に「完成形の見た目」を確認しながら執筆できます。

---

## 🪨 Strata（思考の地層）— 考えの堆積を可視化する

AuthorOpsの核心は「書くこと」だけではない。**「考えがどう変わり、堆積していったか」**を記録・可視化できることにある。

Strataは3層の仕組みで、執筆の履歴を「地質」として扱う。

### Layer A（Phase A）: 機械的構造化
`scripts/build_strata.py` が git 履歴を解析し、章・段落単位で
- いつ生まれたか（born_at）
- 何回書き直されたか（revisions）
- どれだけ揺れ動いたか（churn）
を `data/strata.json` に構造化する。

段落に `<!-- para:id=xxx -->` を付けると、改稿で文言が変わっても同一段落として追跡できる。

### Layer B（Phase B）: 視覚化
`viewer/strata.html`（D3.js）が地層断面図を描く。
- 横幅 = 改稿回数（厚いほどよく揺れた）
- 色 = 誕生時期（深層＝古い、表層＝新しい）
- 伏線（`<!-- foreshadow:id=xxx -->` / `<!-- payoff:id=xxx -->`）を「地下水脈」として可視化

GitHub Pages で自動公開される。

### Layer C（Phase C）: 意味論解析
PRで章を変更したとき、`scripts/semantic_diff.py` が
「文字の差分」ではなく「主張・根拠・前提がどう動いたか」を抽出する。

- ANTHROPIC_API_KEY があれば Claude で高精度解析
- 無ければヒューリスティックで概算（CIは落ちない）
- 結果はPRコメントに自動投稿（sticky）

### なぜこれが重要か

- 思考の履歴が残る（メタ認知支援）
- 長い執筆プロジェクトで「伏線を忘れる」ことを防ぐ
- 改稿の「質」を可視化できる（ただの文字数増加ではなく、論理の深化）

詳しくは [`docs/strata-system.md`](docs/strata-system.md) を参照。

---

## 🔬 更に尖らせるためのアイデア

- **Gitのコミットメッセージを思考のログにする**:
  `feat(ch2): ○○の概念を追加` / `fix(ch1): 矛盾していた論理を修正` のようにセマンティック・コミットを使うことで、自分の思考がどう変遷したかのメタデータを残せます。

- **プロンプトやスクリプトの埋め込み**:
  論文の論理チェックや、文章のトーン＆マナーを検証するローカルLLM用スクリプト（Python等）をリポジトリ内に同居させ、コミット前に自分の「思考のバグ」をスクリーニングする機構を作るのも一興です。

---

## 🚠 現在のセットアップ状況（2026-06-02 更新）

**Phase 0 完了**：基盤ファイルとCI/CDの初期改善が完了

- `.gitignore`, `LICENSE` (MIT), `package.json` 追加
- `lint.yml` 改善（npm ci + cache + timeout）
- `deploy.yml` 改善（PRトリガー追加、安定化）
- `dependabot.yml` 追加（依存自動更新）
- `SECURITY.md` / `CONTRIBUTING.md` / `PULL_REQUEST_TEMPLATE.md` 追加
- `docs/REVIEW_GUIDELINES.md` 作成
- Strataシステム（思考の地層）基盤追加（Phase A/B/C）

### 次のステップ（優先順位順）

1. **GitHub Projects カンバン作成**（最優先・手動で5分）
2. **第1章のドラフト執筆**（Issue #2 参照）
3. **textlintルールの微調整**
4. **mdBook設定の洗練とGitHub Pages確認**
5. **実際の長文コンテンツ追加と運用テスト**

---

## 📝 使い方

```bash
# ローカルでビルドしたい場合
make build

# 校正のチェック
make lint
# 自動修正
make lint:fix
```

---

**Public Repository** — このリポジトリは公開されており、Grokと共同で積極的に開発中です。誰でもIssue/PRで貢献可能！

作成日: 2026-05-30 | 最終更新: 2026-06-02