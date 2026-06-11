"""Phase 2: air_diff のテスト。"""
import pytest
from tools.authorops.air.models import AIR, Node
from tools.authorops.diff.air_diff import diff_air, format_diff_as_markdown


def make_air(*nodes: Node) -> AIR:
    return AIR(nodes=list(nodes))


def claim(node_id: str, text: str) -> Node:
    return Node(id=node_id, kind="claim", text=text, source={})


def premise(node_id: str, text: str, for_id: str) -> Node:
    return Node(id=node_id, kind="premise", text=text, relation={"for": for_id}, source={})


def refutation(node_id: str, text: str, against_id: str) -> Node:
    return Node(id=node_id, kind="refutation", text=text, relation={"against": against_id}, source={})


def test_added_claim():
    base = make_air(claim("c1", "主張A"))
    head = make_air(claim("c1", "主張A"), claim("c2", "新しい主張B"))
    diff = diff_air(base, head)
    assert len(diff["added_claims"]) == 1
    assert diff["added_claims"][0].node_id == "c2"


def test_removed_claim():
    base = make_air(claim("c1", "主張A"), claim("c2", "削除される主張"))
    head = make_air(claim("c1", "主張A"))
    diff = diff_air(base, head)
    assert len(diff["removed_claims"]) == 1
    assert diff["removed_claims"][0].node_id == "c2"


def test_weakened_claim():
    base = make_air(
        claim("c1", "主張A"),
        premise("p1", "前提1", "c1"),
        premise("p2", "前提2", "c1"),
    )
    head = make_air(
        claim("c1", "主張A"),
        premise("p1", "前提1", "c1"),
    )
    diff = diff_air(base, head)
    assert any(d.node_id == "c1" for d in diff["weakened"])


def test_strengthened_claim():
    base = make_air(claim("c1", "主張A"), premise("p1", "前提1", "c1"))
    head = make_air(
        claim("c1", "主張A"),
        premise("p1", "前提1", "c1"),
        premise("p2", "前提2", "c1"),
    )
    diff = diff_air(base, head)
    assert any(d.node_id == "c1" for d in diff["strengthened"])


def test_added_refutation():
    base = make_air(claim("c1", "主張A"))
    head = make_air(claim("c1", "主張A"), refutation("r1", "反証", "c1"))
    diff = diff_air(base, head)
    assert len(diff["added_refutations"]) == 1


def test_no_diff():
    air = make_air(claim("c1", "主張A"), premise("p1", "前提1", "c1"))
    diff = diff_air(air, air)
    assert not diff["added_claims"]
    assert not diff["removed_claims"]
    assert not diff["weakened"]


def test_format_as_markdown():
    base = make_air(claim("c1", "主張A"))
    head = make_air(claim("c1", "主張A"), claim("c2", "新主張"))
    diff = diff_air(base, head)
    md = format_diff_as_markdown(diff)
    assert "論証構造の変化" in md
    assert "c2" in md
