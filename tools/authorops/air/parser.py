from __future__ import annotations

import re
from pathlib import Path

from markdown_it import MarkdownIt

from tools.authorops.air.models import AIR, Node


# 注釈のパターン
ANNOTATION_PATTERN = re.compile(
    r"<!--\s*@(?P<kind>claim|premise|refutation|definition|citation)\s+"  # @kind
    r"(?P<attrs>[^>]+?)\s*-->",  # 属性部分
    re.IGNORECASE,
)


def parse_markdown_to_air(file_path: str | Path) -> AIR:
    """Markdownファイルを読み込み、AIR（論証中間表現）に変換する。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")

    md_content = path.read_text(encoding="utf-8")

    nodes: list[Node] = []
    md = MarkdownIt()

    # 簡易実装：HTMLコメントを検出してノードを抽出
    # （本格的にはブロック単位で解析する必要があるが、Phase 1では簡易版）
    current_pos = 0
    for match in ANNOTATION_PATTERN.finditer(md_content):
        kind = match.group("kind").lower()
        attrs_str = match.group("attrs")

        # 属性を簡易パース（id=xxx, for=yyy など）
        attrs = {}
        for attr in re.finditer(r'(\w+)=([\w\-]+)', attrs_str):
            attrs[attr.group(1)] = attr.group(2)

        node_id = attrs.get("id", f"node_{len(nodes)}")

        # 注釈直後の本文を簡易的に取得（次の注釈まで or 段落）
        start = match.end()
        next_match = ANNOTATION_PATTERN.search(md_content, start)
        end = next_match.start() if next_match else len(md_content)
        text = md_content[start:end].strip()

        # 最初の行だけをtextとして使う（簡易版）
        if "\n" in text:
            text = text.split("\n", 1)[0].strip()

        node = Node(
            id=node_id,
            kind=kind,  # type: ignore[arg-type]
            text=text or "(empty)",
            relation={
                k: v for k, v in attrs.items() if k in {"for", "against", "ref"}
            },
            source={"file": str(path), "match_start": match.start()},
        )
        nodes.append(node)

    # freeノードは一旦省略（Phase 1では注釈付きのみ扱う）
    air = AIR(nodes=nodes)
    return air
