from pathlib import Path
from typing import List, Sequence

from colorama import Fore, Style

from .models import Config, Pattern
from .pattern_applier import PatternApplier
from .section_splitter import SectionSplitter


class FileProcessor:
    def __init__(self, config: Config, splitter: SectionSplitter | None = None, applier: PatternApplier | None = None):
        self.config = config
        self.splitter = splitter or SectionSplitter()
        self.applier = applier or PatternApplier()

    def process_files(self, patterns: Sequence[Pattern]) -> None:
        if not patterns:
            print(f"{Fore.RED}No patterns to apply{Style.RESET_ALL}")
            return

        files = self._get_files()
        if not files:
            print(f"{Fore.YELLOW}No files found matching pattern{Style.RESET_ALL}")
            return

        for file_path in files:
            self._process_file(file_path, patterns)

    def _get_files(self) -> List[Path]:
        path = Path(self.config.path or '.')
        if path.is_file():
            return [path]

        pattern = self.config.pattern or '*'
        if self.config.recursive:
            return list(path.glob(f"**/{pattern}"))
        return list(path.glob(pattern))

    def _process_file(self, file_path: Path, patterns: Sequence[Pattern]) -> None:
        try:
            with open(file_path, 'rb') as handle:
                content_bytes = handle.read()
            ends_with_newline = content_bytes.endswith(b'\n')
            content = content_bytes.decode('utf-8')
        except Exception as error:
            print(f"{Fore.RED}Error processing {file_path}: {error}{Style.RESET_ALL}")
            return

        sections = self.splitter.split(content)
        new_content_parts: List[str] = []
        all_changes: List[tuple[int, str, str]] = []

        for section in sections:
            section_text = section.text
            for pattern in patterns:
                if section.is_code_block and pattern.skip_code_blocks:
                    continue
                if section.is_table and pattern.skip_tables:
                    continue
                section_text, changes = self.applier.apply(section_text, pattern, section.start_line)
                all_changes.extend(changes)
            new_content_parts.append(section_text)

        modified_content = ''.join(new_content_parts)
        if ends_with_newline and not modified_content.endswith('\n'):
            modified_content += '\n'
        elif not ends_with_newline and modified_content.endswith('\n'):
            modified_content = modified_content.rstrip('\n')

        if self.config.ensure_new_line:
            modified_content = modified_content.rstrip('\n') + "\n"

        if all_changes:
            self._report_changes(file_path, all_changes)

        if not self.config.dry_run and modified_content != content:
            with open(file_path, 'w', encoding='utf-8', newline='') as handle:
                handle.write(modified_content)

    def _report_changes(self, file_path: Path, changes: List[tuple[int, str, str]]) -> None:
        lines_changed = 0
        for line_num, old, new in sorted(changes, key=lambda item: item[0]):
            if not self.config.dry_run:
                line_num += lines_changed

            ending_old = self._count_substring_at_end(old, '\n') - 1
            ending_new = self._count_substring_at_end(new, '\n') - 1

            status = 'WOULD CHANGE' if self.config.dry_run else 'CHANGED'
            color = Fore.YELLOW if self.config.dry_run else Fore.GREEN
            print(f"{color}[{status}] {file_path}:{line_num}{Style.RESET_ALL}")

            red = f"{Fore.RED}"
            red += f"- {old.rstrip()}" if old else ''
            for _ in range(max(ending_old, 0)):
                red += '\n-'
            red += f"{Style.RESET_ALL}"

            green = f"{Fore.GREEN}"
            green += f"+ {new.rstrip()}" if new else ''
            for _ in range(max(ending_new, 0)):
                green += '\n+'
            green += f"{Style.RESET_ALL}"

            print(f"{red}\n{green}\n")

            lines_changed += new.count('\n') - old.count('\n')

    def _count_substring_at_end(self, value: str, substring: str) -> int:
        count = 0
        working = value
        while working.endswith(substring):
            count += 1
            working = working[: -len(substring)]
        return count
