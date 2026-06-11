import pytest

from tools.authorops.air.models import AIR


@pytest.fixture
def sample_path() -> str:
    return "tools/tests/fixtures/sample-argument.md"


def test_parse_sample_argument_returns_air(sample_path: str):
    """サンプルMarkdownをパースするとAIRオブジェクトが返ることを確認する。"""
    from tools.authorops.air.parser import parse_markdown_to_air

    air: AIR = parse_markdown_to_air(sample_path)

    assert isinstance(air, AIR)
    assert len(air.nodes) > 0, "少なくとも1つ以上のノードが抽出されるはず"


def test_parse_extracts_claims(sample_path: str):
    from tools.authorops.air.parser import parse_markdown_to_air

    air = parse_markdown_to_air(sample_path)
    claims = [n for n in air.nodes if n.kind == "claim"]
    assert len(claims) >= 2


def test_parse_extracts_premises(sample_path: str):
    from tools.authorops.air.parser import parse_markdown_to_air

    air = parse_markdown_to_air(sample_path)
    premises = [n for n in air.nodes if n.kind == "premise"]
    assert len(premises) >= 1


def test_parse_extracts_refutations(sample_path: str):
    from tools.authorops.air.parser import parse_markdown_to_air

    air = parse_markdown_to_air(sample_path)
    refutations = [n for n in air.nodes if n.kind == "refutation"]
    assert len(refutations) >= 1


def test_parse_builds_edges(sample_path: str):
    from tools.authorops.air.parser import parse_markdown_to_air

    air = parse_markdown_to_air(sample_path)
    assert len(air.edges) > 0, "前提/反証からエッジが構築されるはず"


def test_parse_nonexistent_file():
    from tools.authorops.air.parser import parse_markdown_to_air

    with pytest.raises(FileNotFoundError):
        parse_markdown_to_air("nonexistent/path.md")


def test_node_ids_are_set(sample_path: str):
    from tools.authorops.air.parser import parse_markdown_to_air

    air = parse_markdown_to_air(sample_path)
    for node in air.nodes:
        assert node.id, "全ノードにIDが設定されているはず"
        assert node.text, "全ノードにテキストが設定されているはず"
