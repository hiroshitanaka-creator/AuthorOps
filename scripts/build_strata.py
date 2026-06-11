#!/usr/bin/env python3
"""build_strata.py — AuthorOps Phase A
git履歴を「章・段落単位の地層データ」に構造化してstrata.jsonを出力する。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


ANNOTATION_RE = re.compile(
    r"<!--\s*@(claim|premise|refutation|definition|citation)\s*[^>]*-->",
    re.IGNORECASE,
)


def run_git(*args: str, check: bool = False) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def get_commits(src: Path) -> list[dict]:
    out = run_git("log", "--format=%H|%as|%an|%s", "--", str(src))
    commits = []
    for line in out.split("\n"):
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "date": parts[1],
                "author": parts[2],
                "subject": parts[3],
            })
    return commits


def get_changed_files(commit_hash: str, src: Path) -> list[str]:
    out = run_git("show", "--name-only", "--format=", commit_hash, "--", str(src))
    return [f for f in out.split("\n") if f.strip().endswith(".md")]


def get_file_content(commit_hash: str, file_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{commit_hash}:{file_path}"],
        capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def analyze_content(content: str) -> dict:
    """Markdownコンテンツから統計情報を抽出する。"""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    word_count = len(re.findall(r"\S+", content))
    char_count = len(content)

    node_counts: dict[str, int] = {
        "claim": 0, "premise": 0, "refutation": 0,
        "definition": 0, "citation": 0,
    }
    for m in ANNOTATION_RE.finditer(content):
        kind = m.group(1).lower()
        if kind in node_counts:
            node_counts[kind] += 1

    return {
        "paragraphs": len(paragraphs),
        "chars": char_count,
        "words": word_count,
        "air_nodes": node_counts,
    }


def build_strata(src: Path, out: Path) -> dict:
    """git履歴を解析してstrata.jsonを生成する。"""
    commits = get_commits(src)

    layers = []
    for commit in commits:
        files_changed = get_changed_files(commit["hash"], src)
        if not files_changed:
            continue

        file_data = []
        for fpath in files_changed:
            content = get_file_content(commit["hash"], fpath)
            if content is not None:
                stats = analyze_content(content)
                file_data.append({
                    "file": fpath,
                    **stats,
                })

        if file_data:
            layers.append({
                "hash": commit["hash"],
                "short_hash": commit["hash"][:8],
                "date": commit["date"],
                "author": commit["author"],
                "subject": commit["subject"],
                "files": file_data,
                "summary": {
                    "files_changed": len(file_data),
                    "total_paragraphs": sum(f["paragraphs"] for f in file_data),
                    "total_chars": sum(f["chars"] for f in file_data),
                },
            })

    strata = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "total_commits": len(layers),
        "layers": layers,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(strata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(layers)} layers → {out}")
    return strata


def main() -> None:
    parser = argparse.ArgumentParser(description="Build strata.json from git history")
    parser.add_argument("--src", default="src", help="Markdown source directory")
    parser.add_argument("--out", default="data/strata.json", help="Output JSON path")
    args = parser.parse_args()

    strata = build_strata(Path(args.src), Path(args.out))
    if not strata["layers"]:
        print("⚠ No markdown commits found — generating empty strata.json")


if __name__ == "__main__":
    main()
