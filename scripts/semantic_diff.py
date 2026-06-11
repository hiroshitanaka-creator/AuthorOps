#!/usr/bin/env python3
"""semantic_diff.py — AuthorOps Phase C
PRの変更ファイルに対して論証構造レベルのdiffを実行し、Markdownサマリを出力する。
ANTHROPIC_API_KEY が設定されていれば、Claude によるセマンティック要約も追加する。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# tools/ を Python パスに追加（CI環境用）
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.authorops.air.parser import parse_markdown_to_air
from tools.authorops.diff.air_diff import diff_air, format_diff_as_markdown


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    return result.stdout.strip()


def get_changed_md_files(base: str, head: str, src: str) -> list[str]:
    out = run_git("diff", "--name-only", base, head, "--", f"{src}/**/*.md", src)
    return [f for f in out.split("\n") if f.strip().endswith(".md")]


def get_file_at_ref(ref: str, file_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{file_path}"],
        capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def analyze_file_diff(file_path: str, base_ref: str) -> str:
    """1ファイルの論証構造diffをMarkdownで返す。"""
    base_content = get_file_at_ref(base_ref, file_path)
    head_path = Path(file_path)

    if not head_path.exists():
        return f"### `{file_path}`\n\n> ファイルが削除されました。\n"

    # base が存在しない（新規ファイル）
    if base_content is None:
        try:
            head_air = parse_markdown_to_air(head_path)
        except Exception:
            return f"### `{file_path}`\n\n> パース失敗\n"

        if not head_air.nodes:
            return f"### `{file_path}`\n\n> 論証ノードなし（新規ファイル）\n"

        lines = [f"### `{file_path}` — 新規ファイル\n"]
        lines.append("| 種別 | 内容 |")
        lines.append("|---|---|")
        for node in head_air.nodes:
            if node.kind != "free":
                lines.append(f"| ➕ {node.kind} | `{node.id}`: {node.text[:80]} |")
        return "\n".join(lines) + "\n"

    # 両方存在 → diff
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(base_content)
        base_tmp = Path(f.name)

    try:
        base_air = parse_markdown_to_air(base_tmp)
        head_air = parse_markdown_to_air(head_path)
        diff = diff_air(base_air, head_air)
        result = format_diff_as_markdown(diff)
        return f"### `{file_path}`\n\n{result}\n"
    except Exception as e:
        return f"### `{file_path}`\n\n> 解析エラー: {e}\n"
    finally:
        base_tmp.unlink(missing_ok=True)


def llm_summarize(diff_md: str) -> str | None:
    """Anthropic APIを使って高レベルなセマンティック要約を生成する（オプション）。"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.getenv("AUTHOROPS_LLM_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"""以下はMarkdown文書の論証構造の変化サマリです。
この変化が論文・文章の主張にとってどのような意味を持つか、
2〜3文で日本語で要約してください。

{diff_md[:2000]}""",
            }],
        )
        return message.content[0].text
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic diff for AuthorOps")
    parser.add_argument("--base", required=True, help="Base git ref (e.g. origin/main)")
    parser.add_argument("--head", default="HEAD", help="Head git ref")
    parser.add_argument("--src", default="src", help="Source directory")
    parser.add_argument("--out", default="semantic_diff.md", help="Output Markdown file")
    args = parser.parse_args()

    changed_files = get_changed_md_files(args.base, args.head, args.src)

    if not changed_files:
        output = "論証構造に影響するMarkdownの変更はありませんでした。"
        Path(args.out).write_text(output, encoding="utf-8")
        print("✓ No changed Markdown files.")
        return

    sections = [
        "# 📖 セマンティック差分レポート\n",
        f"比較: `{args.base}` → `{args.head}`\n",
    ]

    for file_path in changed_files:
        sections.append(analyze_file_diff(file_path, args.base))

    diff_md = "\n".join(sections)

    # LLMによる要約（APIキーがあれば）
    summary = llm_summarize(diff_md)
    if summary:
        diff_md = f"## 🤖 AI要約\n\n{summary}\n\n---\n\n" + diff_md

    Path(args.out).write_text(diff_md, encoding="utf-8")
    print(f"✓ Semantic diff written to {args.out}")


if __name__ == "__main__":
    main()
