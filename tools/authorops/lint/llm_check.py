"""Phase 3-2: LLM検査アダプター（オプショナル）。
CIではデフォルトoff。`make lint:logic:llm` で手動実行。
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod

from tools.authorops.air.models import AIR
from tools.authorops.lint.rules import LintIssue


class LLMAdapter(ABC):
    """LLMバックエンドの交換可能なインターフェース。"""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """プロンプトを渡してLLMの応答を返す。"""


class AnthropicAdapter(LLMAdapter):
    """Claude (Anthropic) アダプター。ANTHROPIC_API_KEY 環境変数が必要。"""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("AUTHOROPS_LLM_MODEL", "claude-haiku-4-5-20251001")

    def generate(self, prompt: str) -> str:
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic パッケージが必要です: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 環境変数が設定されていません")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


def get_default_adapter() -> LLMAdapter | None:
    """環境変数に基づいてデフォルトアダプターを返す。APIキーがなければNone。"""
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicAdapter()
    return None


def llm_check_air(air: AIR, adapter: LLMAdapter | None = None) -> list[LintIssue]:
    """LLMを使った論理検査（オプショナル）。adapterがNoneなら空リストを返す。"""
    if adapter is None:
        adapter = get_default_adapter()
    if adapter is None:
        return []

    nodes_summary = "\n".join(
        f"[{n.kind}:{n.id}] {n.text[:100]}" for n in air.nodes if n.kind != "free"
    )
    prompt = f"""以下は論証構造の要約です。論理的な問題（矛盾、飛躍、前章との不整合）を日本語で指摘してください。
各指摘は「ノードID: 問題の説明」の形式で出力してください。問題がなければ「問題なし」とだけ答えてください。

{nodes_summary}"""

    try:
        response = adapter.generate(prompt)
    except Exception as e:
        return [LintIssue(
            rule="llm-check-error",
            node_id="(llm)",
            message=f"LLM検査中にエラーが発生しました: {e}",
            severity="warning",
        )]

    if "問題なし" in response:
        return []

    issues: list[LintIssue] = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            node_id, message = line.split(":", 1)
            issues.append(LintIssue(
                rule="llm-logic-check",
                node_id=node_id.strip(),
                message=message.strip(),
                severity="warning",
            ))
    return issues
