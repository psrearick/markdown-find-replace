# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from markdown_find_replace import Pattern
from markdown_find_replace.pattern_applier import PatternApplier


def load_pattern_catalog():
    path = Path("config/fr_patterns.yaml")
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return {name: Pattern(**spec) for name, spec in raw.items()}


PATTERN_CATALOG = load_pattern_catalog()
APPLIER = PatternApplier()


PATTERN_CASES = [
    ("normalize_list_spaces", "-   item\n", "- item\n"),
    ("remove_list_blank_lines", "- item\n\n\n- another\n", "- item\n- another\n"),
    ("round_indentations_to_four", "      indent\n", "        indent\n"),
    ("start_lists_with_dashes", "* item\n", "- item\n"),
    ("remove_bold_headings", "# **Title**\n", "# Title\n"),
    ("add_new_line_after_headings", "# Heading\nNext line\n", "# Heading\n\nNext line\n"),
    ("ensure_two_line_breaks_before_headings", "Paragraph text\n# Heading\n", "Paragraph text\n\n# Heading\n"),
    ("add_new_line_after_bold_or_italicized_lines", "*Bold line*\nNext line\n", "*Bold line*\n\nNext line\n"),
    ("add_new_line_before_lists", "Paragraph\n- Item\n", "Paragraph\n\n- Item\n"),
    ("add_new_line_after_lists", "- Item\nNext paragraph\n", "- Item\n\nNext paragraph\n"),
    ("add_new_line_after_paragraphs", "Paragraph one\nParagraph two\n", "Paragraph one\n\nParagraph two\n"),
    ("remove_double_spaces", "Word   word\n", "Word word\n"),
    ("remove_bold_headings_with_preceding_text", "## Intro **Bold**\n", "## Intro Bold\n"),
    ("remove_line_breaks_surrounding_headings", "Text before\n\n\n# Heading\n\n\nText after\n", "Text before\n\n# Heading\n\nText after\n"),
    ("remove_trailing_spaces", "Trailing spaces   \n", "Trailing spaces\n"),
    ("replace_left_single_smart_quote", "‘quoted\n", "'quoted\n"),
    ("replace_right_single_smart_quote", "quoted’\n", "quoted'\n"),
    ("replace_left_double_smart_quote", "“quote\n", '"quote\n'),
    ("replace_right_double_smart_quote", "quote”\n", 'quote"\n'),
    ("remove_blank_lines", "Line\n\n\n\nNext\n", "Line\n\nNext\n"),
    ("tabs_to_spaces", "Column\tvalue\n", "Column    value\n"),
    ("replace_ellipsis", "Wait…\n", "Wait...\n"),
    ("replace_bold_lists_after_first_level_with_italicized", "  - **Item**\n", "  - *Item*\n"),
    ("protect_first_level_bold_list", "- **Item**\n", "- @@PROTECTED_BOLD_START@@Item@@PROTECTED_BOLD_END@@\n"),
    ("protect_subsequent_level_italicized_list", "  - *Item*\n", "  - @@PROTECTED_ITALICIZED_START@@Item@@PROTECTED_ITALICIZED_END@@\n"),
    ("protect_first_level_bold_list_tag", "- **Item:**\n", "- @@PROTECTED_BOLD_START@@Item:@@PROTECTED_BOLD_END@@\n"),
    ("protect_subsequent_level_italicized_list_tag", "  - *Item:*\n", "  - @@PROTECTED_ITALICIZED_START@@Item:@@PROTECTED_ITALICIZED_END@@\n"),
    ("protect_leading_asterisk", " * item\n", "@@PROTECTED_ASTERISK@@item\n"),
    ("remove_inline_code", "Use `code` here\n", "Use code here\n"),
    ("remove_remaining_bold", "**Bold**\n", "Bold\n"),
    ("remove_remaining_italicized", "*Italic*\n", "Italic\n"),
    ("restore_protected_bold", "@@PROTECTED_BOLD_START@@Item:@@PROTECTED_BOLD_END@@\n", "**Item:**\n"),
    ("restore_protected_italicized", "@@PROTECTED_ITALICIZED_START@@Item:@@PROTECTED_ITALICIZED_END@@\n", "*Item:*\n"),
    ("restore_leading_asterisk", "@@PROTECTED_ASTERISK@@rest\n", "* rest\n"),
]


@pytest.mark.parametrize("pattern_key,text,expected", PATTERN_CASES)
def test_pattern_transforms(pattern_key, text, expected):
    pattern = PATTERN_CATALOG[pattern_key]
    result, changes = APPLIER.apply(text, pattern, start_line=1)
    assert result == expected
    assert (text == expected and not changes) or changes
