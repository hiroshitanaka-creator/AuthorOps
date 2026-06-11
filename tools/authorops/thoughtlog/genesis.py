"""Phase 5: 思考ログ・メタ文書生成。
gitログとAIRスナップショットから論証構造の時系列変遷を生成する。
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class CommitSnapshot:
    hash: str
    date: str
    subject: str
    claim_count: int = 0
    premise_count: int = 0
    refutation_count: int = 0
    total_nodes: int = 0


@dataclass
class GenesisResult:
    snapshots: list[CommitSnapshot] = field(default_factory=list)
    markdown: str = ""
    json_data: dict[str, Any] = field(default_factory=dict)


def _get_commits(src_path: Path) -> list[dict]:
    """対象パスに関係するコミット一覧を取得する。"""
    result = subprocess.run(
        ["git", "log", "--format=%H|%as|%s", "--", str(src_path)],
        capture_output=True, text=True,
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def _get_air_at_commit(commit_hash: str, src_path: Path) -> dict:
    """特定コミット時点のAIRノード数を取得する（簡易版）。"""
    import re
    annotation_pattern = re.compile(
        r"<!--\s*@(claim|premise|refutation|definition|citation)\s*[^>]*-->",
        re.IGNORECASE,
    )

    result = subprocess.run(
        ["git", "show", f"{commit_hash}:{src_path}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # ディレクトリの場合はファイルを列挙
        ls_result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit_hash, str(src_path)],
            capture_output=True, text=True,
        )
        counts: dict[str, int] = {"claim": 0, "premise": 0, "refutation": 0}
        for fname in ls_result.stdout.strip().split("\n"):
            if not fname.endswith(".md"):
                continue
            file_result = subprocess.run(
                ["git", "show", f"{commit_hash}:{fname}"],
                capture_output=True, text=True,
            )
            for m in annotation_pattern.finditer(file_result.stdout):
                kind = m.group(1).lower()
                if kind in counts:
                    counts[kind] += 1
        return counts

    counts = {"claim": 0, "premise": 0, "refutation": 0}
    for m in annotation_pattern.finditer(result.stdout):
        kind = m.group(1).lower()
        if kind in counts:
            counts[kind] += 1
    return counts


def _build_mermaid_timeline(snapshots: list[CommitSnapshot]) -> str:
    """Mermaid XYChartでclaim/premise数の推移を表現する。"""
    if not snapshots:
        return ""

    dates = [s.date for s in snapshots]
    claims = [s.claim_count for s in snapshots]
    premises = [s.premise_count for s in snapshots]

    lines = ["```mermaid", "xychart-beta", '  title "論証構造の推移"', '  x-axis ["' + '","'.join(dates[-10:]) + '"]',
             "  y-axis 0 --> " + str(max(max(claims or [0]), max(premises or [0])) + 2),
             "  bar " + str(claims[-10:]).replace(" ", ""),
             "  line " + str(premises[-10:]).replace(" ", ""),
             "```"]
    return "\n".join(lines)


def generate_genesis(
    src_path: Path | str = Path("src"),
    out_md: Path | str = Path("docs/genesis.md"),
    out_json: Path | str = Path("docs/genesis.json"),
) -> GenesisResult:
    """論証構造の時系列変遷メタ文書を生成する。"""
    src_path = Path(src_path)
    out_md = Path(out_md)
    out_json = Path(out_json)

    commits = _get_commits(src_path)
    snapshots: list[CommitSnapshot] = []

    for commit in commits:
        counts = _get_air_at_commit(commit["hash"], src_path)
        snap = CommitSnapshot(
            hash=commit["hash"][:8],
            date=commit["date"],
            subject=commit["subject"],
            claim_count=counts.get("claim", 0),
            premise_count=counts.get("premise", 0),
            refutation_count=counts.get("refutation", 0),
            total_nodes=sum(counts.values()),
        )
        snapshots.append(snap)

    # Markdownを生成
    lines = [
        "# AuthorOps Genesis — 論証構造の変遷記録",
        "",
        f"生成日時: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## 概要",
        "",
        f"- 対象コミット数: {len(snapshots)}",
        f"- 最終claim数: {snapshots[0].claim_count if snapshots else 0}",
        f"- 最終premise数: {snapshots[0].premise_count if snapshots else 0}",
        "",
        "## 推移グラフ",
        "",
        _build_mermaid_timeline(snapshots),
        "",
        "## コミット別の論証構造",
        "",
        "| 日付 | コミット | 主題 | claim | premise | refutation |",
        "|---|---|---|---|---|---|",
    ]

    for s in snapshots:
        lines.append(f"| {s.date} | `{s.hash}` | {s.subject[:50]} | {s.claim_count} | {s.premise_count} | {s.refutation_count} |")

    markdown = "\n".join(lines)

    # JSONを生成
    json_data = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "schema_version": "1.0",
        "snapshots": [
            {
                "hash": s.hash,
                "date": s.date,
                "subject": s.subject,
                "nodes": {
                    "claim": s.claim_count,
                    "premise": s.premise_count,
                    "refutation": s.refutation_count,
                    "total": s.total_nodes,
                },
            }
            for s in snapshots
        ],
        # Po_core連携用エクスポートスキーマ（将来実装）
        "po_core_export": {
            "type": "genesis",
            "events": [],  # 将来: 各ノードの生成・変更・削除イベントを格納
        },
    }

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown, encoding="utf-8")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return GenesisResult(snapshots=snapshots, markdown=markdown, json_data=json_data)
