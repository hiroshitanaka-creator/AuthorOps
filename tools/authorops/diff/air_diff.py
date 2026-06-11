"""Phase 2: 論証構造diff — 2つのAIRを比較して変化を検出する。"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import NamedTuple

from tools.authorops.air.models import AIR, Node


class NodeDiff(NamedTuple):
    kind: str       # claim / premise / refutation / definition / citation
    action: str     # added / removed / modified
    node_id: str
    text: str
    detail: str = ""


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _match_nodes(base_nodes: list[Node], head_nodes: list[Node]) -> tuple[
    list[Node], list[Node], list[tuple[Node, Node]]
]:
    """IDで突合し、ID不一致時はテキスト類似度でフォールバック。"""
    base_map = {n.id: n for n in base_nodes}
    head_map = {n.id: n for n in head_nodes}

    matched: list[tuple[Node, Node]] = []
    removed: list[Node] = []
    added: list[Node] = []

    for node_id, base_node in base_map.items():
        if node_id in head_map:
            matched.append((base_node, head_map[node_id]))
        else:
            # テキスト類似度でフォールバックマッチ
            best_score = 0.0
            best_head = None
            for hn in head_nodes:
                if hn.id not in base_map:
                    score = _similarity(base_node.text, hn.text)
                    if score > best_score:
                        best_score = score
                        best_head = hn
            if best_head and best_score >= 0.6:
                matched.append((base_node, best_head))
            else:
                removed.append(base_node)

    matched_head_ids = {h.id for _, h in matched}
    for node_id, head_node in head_map.items():
        if node_id not in matched_head_ids:
            added.append(head_node)

    return removed, added, matched


def diff_air(base: AIR, head: AIR) -> dict:
    """2つのAIRを比較して変化をまとめる。"""
    result: dict = {
        "added_claims": [],
        "removed_claims": [],
        "added_premises": [],
        "removed_premises": [],
        "added_refutations": [],
        "removed_refutations": [],
        "weakened": [],     # 前提が減ったclaim
        "strengthened": [],  # 前提が増えたclaim
        "modified": [],
    }

    for kind in ("claim", "premise", "refutation", "definition", "citation"):
        base_nodes = [n for n in base.nodes if n.kind == kind]
        head_nodes = [n for n in head.nodes if n.kind == kind]

        removed, added, matched = _match_nodes(base_nodes, head_nodes)

        key_added = f"added_{kind}s" if f"added_{kind}s" in result else None
        key_removed = f"removed_{kind}s" if f"removed_{kind}s" in result else None

        for n in added:
            diff = NodeDiff(kind=kind, action="added", node_id=n.id, text=n.text)
            if key_added:
                result[key_added].append(diff)
        for n in removed:
            diff = NodeDiff(kind=kind, action="removed", node_id=n.id, text=n.text)
            if key_removed:
                result[key_removed].append(diff)

        for base_n, head_n in matched:
            if base_n.text != head_n.text:
                result["modified"].append(
                    NodeDiff(kind=kind, action="modified", node_id=head_n.id,
                             text=head_n.text, detail=f"旧: {base_n.text[:60]}…")
                )

    # 前提の増減によるclaimの強弱を検出
    base_support: dict[str, int] = {}
    head_support: dict[str, int] = {}
    for n in base.nodes:
        if n.kind == "premise" and "for" in n.relation:
            base_support[n.relation["for"]] = base_support.get(n.relation["for"], 0) + 1
    for n in head.nodes:
        if n.kind == "premise" and "for" in n.relation:
            head_support[n.relation["for"]] = head_support.get(n.relation["for"], 0) + 1

    all_claims = {n.id for n in base.nodes + head.nodes if n.kind == "claim"}
    for claim_id in all_claims:
        base_cnt = base_support.get(claim_id, 0)
        head_cnt = head_support.get(claim_id, 0)
        if head_cnt < base_cnt:
            result["weakened"].append(
                NodeDiff(kind="claim", action="weakened", node_id=claim_id,
                         text="", detail=f"前提 {base_cnt}→{head_cnt}")
            )
        elif head_cnt > base_cnt:
            result["strengthened"].append(
                NodeDiff(kind="claim", action="strengthened", node_id=claim_id,
                         text="", detail=f"前提 {base_cnt}→{head_cnt}")
            )

    return result


def format_diff_as_markdown(diff: dict) -> str:
    """diffをMarkdownテーブルにフォーマットする。"""
    lines = ["## 🧩 論証構造の変化\n"]

    rows: list[tuple[str, str]] = []

    for n in diff.get("added_claims", []):
        rows.append(("➕ 追加された主張", f"`{n.node_id}`: {n.text[:80]}"))
    for n in diff.get("removed_claims", []):
        rows.append(("➖ 削除された主張", f"`{n.node_id}`: {n.text[:80]}"))
    for n in diff.get("added_premises", []):
        rows.append(("➕ 追加された前提", f"`{n.node_id}`: {n.text[:80]}"))
    for n in diff.get("removed_premises", []):
        rows.append(("➖ 削除された前提", f"`{n.node_id}`: {n.text[:80]}"))
    for n in diff.get("added_refutations", []):
        rows.append(("🔁 新しい反証", f"`{n.node_id}`: {n.text[:80]}"))
    for n in diff.get("removed_refutations", []):
        rows.append(("➖ 削除された反証", f"`{n.node_id}`"))
    for n in diff.get("weakened", []):
        rows.append(("⚠️ 前提が減った主張", f"`{n.node_id}` ({n.detail})"))
    for n in diff.get("strengthened", []):
        rows.append(("💪 前提が増えた主張", f"`{n.node_id}` ({n.detail})"))
    for n in diff.get("modified", []):
        rows.append(("✏️ 変更されたノード", f"`{n.node_id}` ({n.kind}): {n.text[:60]}"))

    if not rows:
        lines.append("論証構造の変化はありませんでした。")
        return "\n".join(lines)

    lines.append("| 種別 | 内容 |")
    lines.append("|---|---|")
    for label, content in rows:
        lines.append(f"| {label} | {content} |")

    return "\n".join(lines)
