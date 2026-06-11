"""Phase 3: logic linter rules のテスト。"""
import pytest
from tools.authorops.air.models import AIR, Node
from tools.authorops.lint.rules import (
    lint_air, LintIssue,
    _check_undefined_concepts,
    _check_uncited_claims,
    _check_orphan_refutations,
    _check_circular_references,
)


def make_air(*nodes: Node) -> AIR:
    return AIR(nodes=list(nodes))


def claim(node_id: str, text: str, refs: list[str] | None = None) -> Node:
    return Node(id=node_id, kind="claim", text=text, refs=refs or [], source={})


def premise(node_id: str, text: str, for_id: str, refs: list[str] | None = None) -> Node:
    return Node(id=node_id, kind="premise", text=text, relation={"for": for_id},
                refs=refs or [], source={})


def refutation(node_id: str, text: str, against_id: str | None = None) -> Node:
    rel = {"against": against_id} if against_id else {}
    return Node(id=node_id, kind="refutation", text=text, relation=rel, source={})


def definition(node_id: str, text: str) -> Node:
    return Node(id=node_id, kind="definition", text=text, source={})


# --- 未定義概念 ---

def test_undefined_concept_detected():
    air = make_air(claim("c1", "主張", refs=["unknown_ref"]))
    issues = _check_undefined_concepts(air)
    assert any(i.rule == "undefined-concept" for i in issues)


def test_known_ref_no_issue():
    air = make_air(
        claim("c1", "主張", refs=["p1"]),
        premise("p1", "前提", "c1"),
    )
    issues = _check_undefined_concepts(air)
    assert not issues


# --- 裸の断定 ---

def test_uncited_claim_detected():
    air = make_air(claim("c1", "前提も引用もない主張"))
    issues = _check_uncited_claims(air)
    assert any(i.rule == "uncited-claim" and i.node_id == "c1" for i in issues)


def test_cited_claim_no_issue():
    air = make_air(claim("c1", "引用あり", refs=["watsuji1934"]))
    issues = _check_uncited_claims(air)
    assert not issues


def test_supported_claim_no_issue():
    air = make_air(
        claim("c1", "主張"),
        premise("p1", "前提", "c1"),
    )
    issues = _check_uncited_claims(air)
    assert not issues


# --- 孤立した反証 ---

def test_orphan_refutation_no_against():
    air = make_air(refutation("r1", "against属性なし"))
    issues = _check_orphan_refutations(air)
    assert any(i.rule == "orphan-refutation" and i.node_id == "r1" for i in issues)


def test_orphan_refutation_missing_target():
    air = make_air(refutation("r1", "参照先がない反証", "nonexistent"))
    issues = _check_orphan_refutations(air)
    assert any(i.rule == "orphan-refutation" for i in issues)


def test_valid_refutation_no_issue():
    air = make_air(
        claim("c1", "主張"),
        premise("p1", "前提", "c1"),
        refutation("r1", "正しい反証", "c1"),
    )
    issues = _check_orphan_refutations(air)
    assert not issues


# --- 循環参照 ---

def test_no_circular_reference():
    air = make_air(
        claim("c1", "主張"),
        premise("p1", "前提", "c1"),
    )
    issues = _check_circular_references(air)
    assert not issues


# --- 統合テスト ---

def test_lint_air_clean():
    air = make_air(
        claim("c1", "主張"),
        premise("p1", "前提", "c1"),
        refutation("r1", "反証", "c1"),
        definition("d1", "定義"),
    )
    issues = lint_air(air)
    # refutationはc1に対して正しく指定されているので孤立なし
    # c1はp1で支えられているので裸の断定なし
    orphan_issues = [i for i in issues if i.rule == "orphan-refutation"]
    assert not orphan_issues
    uncited = [i for i in issues if i.rule == "uncited-claim"]
    assert not uncited
