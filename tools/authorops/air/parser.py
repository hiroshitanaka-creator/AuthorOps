from __future__ import annotations

import re
from pathlib import Path

from markdown_it import MarkdownIt

from tools.authorops.air.models import AIR, Node


# 注釈のパターン
ANNOTATION_PATTERN = re.compile(
    r"<!--\s*@(?P<kind>claim|premise|refutation|definition|citation)\s+"
    r"(?P<attrs>[^>]+?)\s*-->",
    re.IGNORECASE,
)


def parse_markdown_to_air(file_path: str | Path) -> AIR:
    """Markdownファイルを読み込み、AIR（論証中間表現）に変換する。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")

    md_content = path.read_text(encoding="utf-8")

    nodes: list[Node] = []
    # MarkdownItは将来的に本格パースで使用予定。現在は正規表現ベース。
    _ = MarkdownIt()  # noqa: F841

    for match in ANNOTATION_PATTERN.finditer(md_content):
        kind = match.group("kind").lower()
        attrs_str = match.group("attrs")

        # 属性を簡易パース
        attrs: dict[str, str] = {}
        for attr in re.finditer(r"(\w+)=([\w\-]+)", attrs_str):
            attrs[attr.group(1)] = attr.group(2)

        node_id = attrs.get("id", f"node_{len(nodes)}")

        # 注釈直後の本文を簡易的に取得
        start = match.end()
        next_match = ANNOTATION_PATTERN.search(md_content, start)
        end = next_match.start() if next_match else len(md_content)
        text = md_content[start:end].strip()

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

    air = AIR(nodes=nodes)
    return air
