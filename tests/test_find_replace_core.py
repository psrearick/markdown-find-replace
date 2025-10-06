import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from markdown_find_replace import Config, FindReplace, Pattern, set_config_values
from markdown_find_replace.pattern_applier import PatternApplier
from markdown_find_replace.section_splitter import SectionSplitter


def test_split_content_sections_identifies_frontmatter_code_and_tables():
    splitter = SectionSplitter()
    text = (
        "---\n"
        "title: Sample\n"
        "---\n"
        "\n"
        "Paragraph text.\n"
        "\n"
        "```python\n"
        "print('hi')   \n"
        "```\n"
        "\n"
        "| h1 | h2 |\n"
        "| --- | --- |\n"
        "| v1 | v2 |\n"
    )

    sections = splitter.split(text)

    assert sections[0].is_code_block is True
    assert any(section.is_code_block and "print('hi')" in section.text for section in sections)
    assert any(section.is_table and "| h1 |" in section.text for section in sections)


def test_apply_plain_text_pattern_reports_changes():
    pattern = Pattern(
        name="plain",
        find="foo",
        replace="bar",
        is_regex=False,
        skip_code_blocks=False,
        skip_tables=False,
    )
    applier = PatternApplier()
    text = "leading\nfoo appears here\n"
    result, changes = applier.apply(text, pattern, start_line=10)

    assert result == "leading\nbar appears here\n"
    assert changes == [(11, "foo appears here\n", "bar appears here\n")]


def test_process_files_applies_patterns(tmp_path):
    target = tmp_path / "sample.md"
    target.write_text("content foo\n", encoding="utf-8")

    config = Config(
        path=str(tmp_path),
        pattern="*.md",
        find="foo",
        replace="bar",
        is_regex=False,
        recursive=False,
        dry_run=False,
    )
    engine = FindReplace(config)
    engine.process_files()

    assert target.read_text(encoding="utf-8") == "content bar\n"


def test_process_files_respects_dry_run(tmp_path):
    target = tmp_path / "sample.md"
    target.write_text("content foo\n", encoding="utf-8")

    config = Config(
        path=str(tmp_path),
        pattern="*.md",
        find="foo",
        replace="bar",
        is_regex=False,
        recursive=False,
        dry_run=True,
    )
    engine = FindReplace(config)
    engine.process_files()

    assert target.read_text(encoding="utf-8") == "content foo\n"


def test_skip_code_blocks_when_applying_patterns(tmp_path):
    target = tmp_path / "sample.md"
    content = textwrap.dedent(
        """
        ```
        code   
        ```

        line with trailing spaces   
        """
    ).lstrip("\n")
    target.write_text(content, encoding="utf-8")

    config = Config(
        path=str(target),
        patterns_file="config/fr_patterns.yaml",
        pattern_name="remove_trailing_spaces",
        recursive=False,
    )
    engine = FindReplace(config)
    engine.process_files()

    expected = textwrap.dedent(
        """
        ```
        code   
        ```

        line with trailing spaces
        """
    ).lstrip("\n")
    assert target.read_text(encoding="utf-8") == expected


def test_resolve_file_path_relative_to_config(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data = config_dir / "data.yaml"
    data.write_text("{}\n", encoding="utf-8")
    config_path = config_dir / "fr_config.yaml"
    config_path.write_text("{}\n", encoding="utf-8")

    engine = FindReplace(Config(), config_file_path=str(config_path))
    resolved = Path(engine.resolve_path("data.yaml"))

    assert resolved == data


def test_set_config_values_overrides_file_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "pattern: '*.md'\nrecursive: true\ndry_run: false\n",
        encoding="utf-8",
    )
    overrides = {
        "path": "from_cli",
        "dry_run": True,
        "recursive": False,
        "is_regex": False,
    }

    merged = set_config_values(overrides, str(config_file))

    assert merged["path"] == "from_cli"
    assert merged["dry_run"] is True
    assert merged["recursive"] is False
    assert merged["is_regex"] is False
