"""Phase 4: .authorops.toml 共通設定ローダー。
全ツール（parser/diff/lint）がこの設定を読んで include/exclude を尊重する。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


DEFAULT_CONFIG_PATH = Path(".authorops.toml")


@dataclass
class AuthorOpsConfig:
    include: list[str] = field(default_factory=lambda: ["src/**/*.md"])
    exclude: list[str] = field(default_factory=lambda: ["src/human-only/**"])
    human_only_paths: list[str] = field(default_factory=lambda: ["src/human-only/"])
    ai_assisted_paths: list[str] = field(default_factory=lambda: ["src/ai-assisted/"])
    llm_lint_enabled: bool = False
    llm_model: str = "claude-haiku-4-5-20251001"


def load_config(config_path: Path | None = None) -> AuthorOpsConfig:
    """設定ファイルを読み込む。ファイルがなければデフォルト値を使用。"""
    path = config_path or DEFAULT_CONFIG_PATH

    if not Path(path).exists() or tomllib is None:
        return AuthorOpsConfig()

    raw = Path(path).read_text(encoding="utf-8")
    if tomllib is None:
        return AuthorOpsConfig()

    data = tomllib.loads(raw)
    cfg = AuthorOpsConfig()

    if "include" in data:
        cfg.include = data["include"]
    if "exclude" in data:
        cfg.exclude = data["exclude"]
    if "human_only_paths" in data:
        cfg.human_only_paths = data["human_only_paths"]
    if "ai_assisted_paths" in data:
        cfg.ai_assisted_paths = data["ai_assisted_paths"]
    if "llm_lint_enabled" in data:
        cfg.llm_lint_enabled = data["llm_lint_enabled"]
    if "llm_model" in data:
        cfg.llm_model = data["llm_model"]

    return cfg


def is_excluded(file_path: str | Path, config: AuthorOpsConfig | None = None) -> bool:
    """ファイルが除外対象かどうかを判定する（human-only等）。"""
    if config is None:
        config = load_config()
    path_str = str(file_path).replace("\\", "/")
    for pattern in config.human_only_paths + config.exclude:
        # 簡易マッチ: パスの前方一致または glob 的なパターン
        clean = pattern.rstrip("*").rstrip("/")
        if clean and path_str.startswith(clean):
            return True
    return False
