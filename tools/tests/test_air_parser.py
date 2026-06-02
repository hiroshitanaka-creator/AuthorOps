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


# 将来的に追加するテストの例（今はコメントアウト）
# def test_claim_and_premise_are_correctly_linked(sample_path: str):
#     from tools.authorops.air.parser import parse_markdown_to_air
#     air = parse_markdown_to_air(sample_path)
#     # claimとpremiseの関係が正しく構築されているか、など
