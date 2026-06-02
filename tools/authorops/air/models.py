from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class Node(BaseModel):
    """論証の最小単位（主張・前提・反論など）。"""

    id: str = Field(..., description="ノードの一意なID（例: c1, p1）")
    kind: Literal[
        "claim",       # 主張
        "premise",     # 主張を支える前提・根拠
        "refutation",  # 主張に対する反論
        "definition",  # 用語の定義
        "citation",    # 引用・出典
        "free",        # 注釈のない通常の文章
    ] = Field(..., description="ノードの種類")
    text: str = Field(..., description="本文テキスト")
    refs: list[str] = Field(
        default_factory=list,
        description="参照する文献IDや他のノードID（例: ['watsuji1934', 'c2']）",
    )
    relation: dict[str, str] = Field(
        default_factory=dict,
        description="他のノードとの関係（例: {'for': 'c1', 'against': 'c3'}）",
    )
    source: dict = Field(
        default_factory=dict,
        description="出典情報（例: {'file': 'chapter-01.md', 'line': 42}）",
    )


class AIR(BaseModel):
    """論証全体を表す中間表現（Argument Intermediate Representation）。"""

    nodes: list[Node] = Field(
        default_factory=list, description="論証を構成する全ノード"
    )
    edges: list[tuple[str, str, str]] = Field(
        default_factory=list,
        description="ノード間の関係（from_id, to_id, relation_type）のリスト",
    )
