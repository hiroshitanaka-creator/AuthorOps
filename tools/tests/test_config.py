"""Phase 4: config ローダーのテスト。"""
import pytest
from tools.authorops.config import AuthorOpsConfig, is_excluded


def test_default_config():
    config = AuthorOpsConfig()
    assert "src/**/*.md" in config.include
    assert "src/human-only/**" in config.exclude


def test_human_only_excluded():
    config = AuthorOpsConfig()
    assert is_excluded("src/human-only/chapter-01.md", config)


def test_ai_assisted_not_excluded():
    config = AuthorOpsConfig()
    assert not is_excluded("src/ai-assisted/chapter-01.md", config)


def test_regular_src_not_excluded():
    config = AuthorOpsConfig()
    assert not is_excluded("src/chapter-01/01-intro.md", config)


def test_custom_exclude():
    config = AuthorOpsConfig(exclude=["src/drafts/**"])
    assert is_excluded("src/drafts/rough.md", config)
    assert not is_excluded("src/chapter-01/01-intro.md", config)
