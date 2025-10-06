import re
from typing import List, Tuple

from .models import Pattern


class PatternApplier:
    def apply(self, text: str, pattern: Pattern, start_line: int) -> Tuple[str, List[Tuple[int, str, str]]]:
        if pattern.is_regex:
            return self._apply_regex(text, pattern, start_line)
        return self._apply_plain_text(text, pattern, start_line)

    def _apply_regex(self, text: str, pattern: Pattern, start_line: int) -> Tuple[str, List[Tuple[int, str, str]]]:
        matches = []
        for match in re.finditer(pattern.find, text, flags=re.MULTILINE):
            start, end = match.span()
            line_num = self._line_number(text, start, start_line)
            original = match.group(0)
            replacement = self._expand_replacement(match, pattern.replace)
            if original != replacement:
                matches.append((start, end, line_num, original, replacement))

        if not matches:
            return text, []

        new_text = text
        for start, end, _, original, replacement in sorted(matches, key=lambda item: item[0], reverse=True):
            new_text = new_text[:start] + replacement + new_text[end:]

        return new_text, [(line_num, original, replacement) for (_, _, line_num, original, replacement) in matches]

    def _apply_plain_text(self, text: str, pattern: Pattern, start_line: int) -> Tuple[str, List[Tuple[int, str, str]]]:
        changes: List[Tuple[int, str, str]] = []
        lines = []
        for index, line in enumerate(text.splitlines(True)):
            if pattern.find in line:
                new_line = line.replace(pattern.find, pattern.replace)
                if new_line != line:
                    line_num = start_line + index
                    changes.append((line_num, line, new_line))
                    lines.append(new_line)
                else:
                    lines.append(line)
            else:
                lines.append(line)
        return ''.join(lines), changes

    def _expand_replacement(self, match: re.Match, replacement: str) -> str:
        replace_pattern = re.sub(r'\$(\d+)', r'\\\1', replacement)
        try:
            return match.expand(replace_pattern)
        except re.error:
            return replace_pattern

    def _line_number(self, text: str, position: int, base_line: int) -> int:
        return base_line + text.count('\n', 0, position)
