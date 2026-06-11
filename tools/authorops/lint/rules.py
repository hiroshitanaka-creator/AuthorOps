"""Phase 3: ルールベース論理リンター。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from tools.authorops.air.models import AIR, Node


@dataclass
class LintIssue:
    rule: str
    node_id: str
    message: str
    severity: Literal["error", "warning"] = "warning"
    source: dict = field(default_factory=dict)


def _check_undefined_concepts(air: AIR) -> list[LintIssue]:
    """定義されていない概念がclaim/premise内で使われていないか検査する。"""
    issues: list[LintIssue] = []
    defined = {n.id for n in air.nodes if n.kind == "definition"}
    # refs に定義ノードへの参照がないまま「定義」と見なせる語が使われるケースを検査
    for node in air.nodes:
        if node.kind not in ("claim", "premise"):
            continue
        for ref in node.refs:
            # refが文献キーでも既存ノードIDでもない場合
            node_ids = {n.id for n in air.nodes}
            if ref not in node_ids and ref not in defined:
                issues.append(LintIssue(
                    rule="undefined-concept",
                    node_id=node.id,
                    message=f"参照 '{ref}' が定義されていません（文献または定義ノードが必要）",
                    severity="warning",
                    source=node.source,
                ))
    return issues


def _check_uncited_claims(air: AIR) -> list[LintIssue]:
    """前提も引用もない「裸の断定」を検出する。"""
    issues: list[LintIssue] = []
    # claim を支える premise の対応表
    supported_claims = {
        n.relation["for"]
        for n in air.nodes
        if n.kind == "premise" and "for" in n.relation
    }
    for node in air.nodes:
        if node.kind != "claim":
            continue
        has_support = node.id in supported_claims
        has_ref = bool(node.refs)
        if not has_support and not has_ref:
            issues.append(LintIssue(
                rule="uncited-claim",
                node_id=node.id,
                message=f"主張 '{node.id}' に前提も引用もありません（裸の断定）",
                severity="warning",
                source=node.source,
            ))
    return issues


def _check_orphan_refutations(air: AIR) -> list[LintIssue]:
    """参照先のclaimが存在しない孤立した反証を検出する。"""
    issues: list[LintIssue] = []
    node_ids = {n.id for n in air.nodes}
    for node in air.nodes:
        if node.kind != "refutation":
            continue
        target = node.relation.get("against")
        if target is None:
            issues.append(LintIssue(
                rule="orphan-refutation",
                node_id=node.id,
                message=f"反証 '{node.id}' に 'against' 属性がありません",
                severity="error",
                source=node.source,
            ))
        elif target not in node_ids:
            issues.append(LintIssue(
                rule="orphan-refutation",
                node_id=node.id,
                message=f"反証 '{node.id}' の参照先 '{target}' が存在しません",
                severity="error",
                source=node.source,
            ))
    return issues


def _check_circular_references(air: AIR) -> list[LintIssue]:
    """premise→claim→premiseの循環参照を検出する。"""
    issues: list[LintIssue] = []
    # サポート関係のグラフを構築
    support_graph: dict[str, list[str]] = {n.id: [] for n in air.nodes}
    for node in air.nodes:
        if node.kind == "premise" and "for" in node.relation:
            support_graph[node.id].append(node.relation["for"])

    def has_cycle(start: str, current: str, visited: set[str]) -> bool:
        if current == start and len(visited) > 1:
            return True
        if current in visited:
            return False
        visited.add(current)
        for neighbor in support_graph.get(current, []):
            if has_cycle(start, neighbor, visited.copy()):
                return True
        return False

    for node in air.nodes:
        if node.kind == "premise":
            if has_cycle(node.id, node.id, set()):
                issues.append(LintIssue(
                    rule="circular-reference",
                    node_id=node.id,
                    message=f"ノード '{node.id}' が循環参照を形成しています",
                    severity="error",
                    source=node.source,
                ))

    return issues


def lint_air(air: AIR) -> list[LintIssue]:
    """AIRに対してすべてのルールベース検査を実行する。"""
    issues: list[LintIssue] = []
    issues.extend(_check_undefined_concepts(air))
    issues.extend(_check_uncited_claims(air))
    issues.extend(_check_orphan_refutations(air))
    issues.extend(_check_circular_references(air))
    return issues


def format_issues_as_markdown(issues: list[LintIssue]) -> str:
    """検査結果をMarkdownにフォーマットする。"""
    if not issues:
        return "✅ 論理検査: 問題は検出されませんでした。"

    lines = ["## ⚠️ 論理検査の結果\n", "| 重要度 | ルール | ノード | メッセージ |", "|---|---|---|---|"]
    for issue in issues:
        icon = "🔴" if issue.severity == "error" else "🟡"
        lines.append(f"| {icon} {issue.severity} | `{issue.rule}` | `{issue.node_id}` | {issue.message} |")
    return "\n".join(lines)
