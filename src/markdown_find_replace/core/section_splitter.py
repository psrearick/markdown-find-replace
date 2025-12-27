import re
from typing import List, Optional

from .models import Section

TABLE_SEPARATOR_RE = re.compile(r'^\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?$')


class SectionSplitter:
    def split(self, content: str) -> List[Section]:
        sections: List[Section] = []
        working_content = content
        line_number = 1

        if working_content.startswith('---\n'):
            frontmatter_header, frontmatter_body, remaining = self._split_frontmatter(working_content)
            if frontmatter_body:
                frontmatter_text = frontmatter_header + frontmatter_body
                if not frontmatter_body.rstrip().endswith('---'):
                    frontmatter_text += '---\n'
                sections.append(Section(start_line=1, text=frontmatter_text, is_code_block=True, is_table=False))
                line_number += frontmatter_text.count('\n')
                working_content = remaining
            else:
                working_content = remaining

        if not working_content:
            return sections

        collected_lines: List[str] = []
        in_code_block = False
        in_yaml_block = False

        for line in working_content.splitlines(True):
            stripped = line.strip()
            toggled = False

            if stripped.startswith('---') and not in_code_block:
                in_yaml_block = not in_yaml_block
                toggled = True

            if stripped.startswith('```') and not in_yaml_block:
                in_code_block = not in_code_block
                toggled = True

            if toggled and collected_lines:
                start_line = line_number - len(collected_lines)
                section_text = ''.join(collected_lines)
                sections.append(
                    Section(
                        start_line=start_line,
                        text=section_text,
                        is_code_block=not in_code_block and not in_yaml_block,
                        is_table=False,
                    )
                )
                collected_lines = []

            collected_lines.append(line)
            line_number += 1

        if collected_lines:
            start_line = line_number - len(collected_lines)
            section_text = ''.join(collected_lines)
            sections.append(
                Section(
                    start_line=start_line,
                    text=section_text,
                    is_code_block=in_code_block,
                    is_table=False,
                )
            )

        return self._mark_table_sections(sections)

    def _split_frontmatter(self, content: str) -> tuple[str, str, str]:
        if not content.startswith('---\n'):
            return '', '', content

        parts = content[4:].split('\n---\n', 1)
        if len(parts) == 2:
            return '---\n', parts[0] + '\n', parts[1]
        if parts[0].strip() and not content.strip().endswith('---'):
            return '', '', content
        return '---\n', parts[0] + '\n', ''

    def _mark_table_sections(self, sections: List[Section]) -> List[Section]:
        processed: List[Section] = []

        for section in sections:
            if section.is_code_block:
                processed.append(section)
                continue

            lines = section.text.splitlines(True)
            if not lines:
                processed.append(section)
                continue

            segment_lines: List[str] = []
            segment_start = section.start_line
            current_is_table: Optional[bool] = None

            for offset, line in enumerate(lines):
                stripped = line.strip()
                is_table_line = self._is_table_line(stripped) if stripped else False

                if segment_lines and is_table_line != current_is_table:
                    processed.append(
                        Section(
                            start_line=segment_start,
                            text=''.join(segment_lines),
                            is_code_block=False,
                            is_table=bool(current_is_table),
                        )
                    )
                    segment_lines = []
                    segment_start = section.start_line + offset

                if not segment_lines:
                    segment_start = section.start_line + offset

                segment_lines.append(line)
                current_is_table = is_table_line

            if segment_lines:
                processed.append(
                    Section(
                        start_line=segment_start,
                        text=''.join(segment_lines),
                        is_code_block=False,
                        is_table=bool(current_is_table),
                    )
                )

        return processed

    def _is_table_line(self, stripped_line: str) -> bool:
        if '|' not in stripped_line:
            return False

        pipe_count = stripped_line.count('|')
        if stripped_line.startswith('|') and pipe_count >= 2:
            return True
        if stripped_line.endswith('|') and pipe_count >= 2:
            return True
        if TABLE_SEPARATOR_RE.match(stripped_line):
            return True
        if ' | ' in stripped_line:
            return True
        if pipe_count >= 2:
            return True
        if ' |' in stripped_line or '| ' in stripped_line:
            return True
        return False
