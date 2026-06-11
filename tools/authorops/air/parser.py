from __future__ import annotations

import re
from pathlib import Path

from tools.authorops.air.models import AIR, Node


ANNOTATION_PATTERN = re.compile(
    r"<!--\s*@(?P<kind>claim|premise|refutation|definition|citation)\s*"
    r"(?P<attrs>[^>]*?)\s*-->",
    re.IGNORECASE,
)


def _parse_attrs(attrs_str: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for attr in re.finditer(r"([\w]+)=([\w\-]+)", attrs_str):
        attrs[attr.group(1)] = attr.group(2)
    return attrs


def _extract_text(md_content: str, start: int) -> str:
    """注釈直後の段落テキストを取得する。"""
    next_match = ANNOTATION_PATTERN.search(md_content, start)
    end = next_match.start() if next_match else len(md_content)
    raw = md_content[start:end].strip()
    # 最初の空行で区切る（段落単位）
    paragraph = raw.split("\n\n")[0].strip()
    # 改行を空白に正規化
    return re.sub(r"\s+", " ", paragraph) if paragraph else "(empty)"


def parse_markdown_to_air(file_path: str | Path) -> AIR:
    """Markdownファイルを読み込み、AIR（論証中間表現）に変換する。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")

    md_content = path.read_text(encoding="utf-8")
    nodes: list[Node] = []
    edges: list[tuple[str, str, str]] = []

    matches = list(ANNOTATION_PATTERN.finditer(md_content))
    for i, match in enumerate(matches):
        kind = match.group("kind").lower()
        attrs = _parse_attrs(match.group("attrs"))

        node_id = attrs.get("id", f"node_{i}")
        text_start = match.end()
        text = _extract_text(md_content, text_start)

        # ref は refs リストへ、for/against は relation へ
        refs = [attrs["ref"]] if "ref" in attrs else []
        relation = {k: v for k, v in attrs.items() if k in {"for", "against"}}

        node = Node(
            id=node_id,
            kind=kind,  # type: ignore[arg-type]
            text=text,
            refs=refs,
            relation=relation,
            source={"file": str(path), "line": md_content[:match.start()].count("\n") + 1},
        )
        nodes.append(node)

        # エッジ構築
        if "for" in relation:
            edges.append((node_id, relation["for"], "support"))
        if "against" in relation:
            edges.append((node_id, relation["against"], "refute"))
        for ref in refs:
            edges.append((node_id, ref, "cite"))

    return AIR(nodes=nodes, edges=edges)
