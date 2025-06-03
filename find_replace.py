#!/usr/bin/env python3
import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init()

@dataclass
class Pattern:
    name: str
    find: str
    replace: str
    is_regex: bool = True
    skip_code_blocks: bool = False

@dataclass
class MatchChange:
    start: int
    end: int
    line_num: int
    original: str
    replacement: str

@dataclass
class Config:
    path: Optional[str] = None
    pattern: Optional[str] = None
    find: Optional[str] = None
    replace: Optional[str] = None
    is_regex: bool = True
    recursive: bool = True
    dry_run: bool = False
    patterns_file: Optional[str] = None
    pattern_name: Optional[str] = None
    pattern_list_file: Optional[str] = None
    pattern_list_name: Optional[str] = None

class FindReplace:
    def __init__(self, config: Config, config_file_path: Optional[str] = None):
        self.config = config
        self.config_file_path = config_file_path
        self.patterns: List[Pattern] = []
        self._load_patterns()

    @staticmethod
    def _process_pattern(pattern: str) -> str:
        """Convert pattern to raw string format to handle escapes better."""
        # return str(pattern)
        return pattern

    def _load_patterns(self) -> None:
        """Load patterns from various sources based on configuration."""
        if self.config.find and self.config.replace:
            self.patterns.append(Pattern(
                name="command_line",
                find=self._process_pattern(self.config.find),
                replace=self._process_pattern(self.config.replace),
                is_regex=self.config.is_regex
            ))

        if self.config.patterns_file and self.config.pattern_name:
            patterns = self._load_yaml_or_json(self.config.patterns_file)
            if self.config.pattern_name in patterns:
                pattern = patterns[self.config.pattern_name]
                pattern['find'] = self._process_pattern(pattern['find'])
                pattern['replace'] = self._process_pattern(pattern['replace'])
                self.patterns.append(Pattern(**pattern))

        if self.config.pattern_list_file and self.config.pattern_list_name:
            if not self.config.patterns_file:
                print(f"{Fore.RED}Error: patterns file must be provided when using pattern lists{Style.RESET_ALL}")
                return

            patterns_dict = self._load_yaml_or_json(self.config.patterns_file)
            pattern_lists = self._load_yaml_or_json(self.config.pattern_list_file)

            if self.config.pattern_list_name in pattern_lists:
                pattern_names = pattern_lists[self.config.pattern_list_name]
                for pattern_name in pattern_names:
                    if pattern_name in patterns_dict:
                        pattern_data = patterns_dict[pattern_name].copy()
                        pattern_data['find'] = self._process_pattern(pattern_data['find'])
                        pattern_data['replace'] = self._process_pattern(pattern_data['replace'])
                        self.patterns.append(Pattern(**pattern_data))
                    else:
                        print(f"{Fore.YELLOW}Warning: Pattern '{pattern_name}' not found in patterns file{Style.RESET_ALL}")

    def _resolve_file_path(self, file_path: str) -> str:
        """Resolve file path, checking absolute first, then relative to config file."""
        if not file_path:
            return file_path

        path = Path(file_path)

        # If it's already absolute and exists, use it
        if path.is_absolute() and path.exists():
            return str(path)

        # If it's absolute but doesn't exist, return as-is for error handling
        if path.is_absolute():
            return str(path)

        # If we have a config file path, try relative to config file directory
        if self.config_file_path:
            config_dir = Path(self.config_file_path).parent
            relative_path = config_dir / file_path
            if relative_path.exists():
                return str(relative_path)

        # Return original path (will be resolved relative to current working directory)
        return file_path

    def _load_yaml_or_json(self, file_path: str) -> dict:
        """Load and parse YAML or JSON file based on extension."""
        resolved_path = self._resolve_file_path(file_path)
        with open(resolved_path, 'r') as f:
            if resolved_path.endswith('.yaml') or resolved_path.endswith('.yml'):
                return yaml.safe_load(f)
            return json.load(f)

    def _get_files(self) -> List[Path]:
        """Get list of files to process based on configuration."""
        path = Path(self.config.path or '.')
        if path.is_file():
            return [path]

        files = []
        if self.config.recursive:
            glob_pattern = f"**/{self.config.pattern or '*'}"
        else:
            glob_pattern = self.config.pattern or '*'

        return list(path.glob(glob_pattern))

    def _split_frontmatter(self, content: str) -> tuple[str, str, str]:
        """Split content into frontmatter and body.
        Returns tuple of (frontmatter_start, frontmatter_content, body)"""
        if content.startswith('---\n'):
            parts = content[4:].split('\n---\n', 1)
            if len(parts) == 2:
                return ('---\n', parts[0] + '\n', parts[1])
            elif parts[0].strip() and not content.strip().endswith('---'):  # Has content but no closing ---
                return ('', '', content)
            else:  # Just frontmatter with closing ---
                return ('---\n', parts[0] + '\n', '')
        return ('', '', content)

    def _split_content_sections(self, content: str) -> List[tuple[int, str, bool]]:
        """Split content into sections, marking code blocks.
        Returns list of (line_number, text, is_code_block) tuples."""
        sections = []
        current_section = []
        in_code_block = False
        in_yaml_block = False
        line_number = 1

        # First split into frontmatter and body if needed
        if content.startswith('---\n'):
            fm_start, fm_content, body = self._split_frontmatter(content)
            if fm_content:
                # Check if frontmatter content already ends with ---
                fm_content_with_markers = fm_start + fm_content
                if not fm_content.rstrip().endswith('---'):
                    fm_content_with_markers += '---\n'
                # Add frontmatter as a special "code block" section
                fm_lines = fm_content_with_markers.splitlines(True)
                sections.append((1, ''.join(fm_lines), True))
                line_number += len(fm_lines)
                content = body
            else:
                content = body  # In case there's no valid frontmatter

        # If no content after processing frontmatter, return early
        if not content:
            return sections

        # Process the rest of the content
        for line in content.splitlines(True):  # keepends=True to preserve newlines
            block_toggle = False
            if line.strip().startswith('---') and not in_code_block:
                in_yaml_block = not in_yaml_block
                block_toggle = True

            if line.strip().startswith('```') and not in_yaml_block:
                in_code_block = not in_code_block
                block_toggle = True

            if block_toggle and current_section:
                start_line = line_number - len(current_section)
                sections.append((start_line, ''.join(current_section), not in_code_block and not in_yaml_block))
                current_section = []
                block_toggle = False
            current_section.append(line)
            line_number += 1

        # Add the last section
        if current_section:
            start_line = line_number - len(current_section)
            sections.append((start_line, ''.join(current_section), in_code_block))

        return sections

    def _get_line_number(self, text: str, pos: int, base_line: int = 1) -> int:
        """Get line number for a position in text."""
        return base_line + text.count('\n', 0, pos)

    def _apply_pattern_to_section(self, section_text: str, pattern: Pattern, start_line: int) -> tuple[str, List[tuple[int, str, str]]]:
        """Apply pattern to a single section of text and track line numbers."""
        changes = []

        if pattern.is_regex:
            # Find all matches and their changes first
            matches = []
            for match in re.finditer(pattern.find, section_text, flags=re.MULTILINE):
                start, end = match.span()
                line_num = self._get_line_number(section_text, start, start_line)

                # Get original text and create replacement
                original = match.group(0)
                replace_pattern = re.sub(r'\$(\d+)', r'\\\1', pattern.replace)
                try:
                    replacement = match.expand(replace_pattern)
                except re.error:
                    replacement = replace_pattern

                if original != replacement:
                    matches.append(MatchChange(start, end, line_num, original, replacement))

            # Apply all changes to the text
            if matches:
                # Sort matches by position in reverse order
                matches.sort(key=lambda x: x.start, reverse=True)
                new_text = section_text

                # Apply changes from end to beginning to maintain positions
                for match in matches:
                    new_text = new_text[:match.start] + match.replacement + new_text[match.end:]
                    changes.append((match.line_num, match.original, match.replacement))

                return new_text, changes

            return section_text, changes
        else:
            new_lines = []
            for i, line in enumerate(section_text.splitlines(True)):
                new_line = line
                if pattern.find in line:
                    new_line = line.replace(pattern.find, pattern.replace)
                    if new_line != line:
                        changes.append((start_line + i, line, new_line))
                new_lines.append(new_line)

            return ''.join(new_lines), changes

    def _count_substring_at_end(self, string: str, substring: str) -> int:
        count = 0
        while string.endswith(substring):
            count += 1
            string = string[:-len(substring)]
        return count

    def process_files(self) -> None:
        """Process all files according to configuration."""
        if not self.patterns:
            print(f"{Fore.RED}No patterns to apply{Style.RESET_ALL}")
            return

        files = self._get_files()
        if not files:
            print(f"{Fore.YELLOW}No files found matching pattern{Style.RESET_ALL}")
            return

        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    content_bytes = f.read()
                    ends_with_newline = content_bytes.endswith(b'\n')
                    content = content_bytes.decode('utf-8')

                modified_content = content
                all_changes = []
                sections = self._split_content_sections(modified_content)
                content_changes = []
                new_content_parts = []

                current_text = ""

                for start_line, section_text, is_code_block in sections:
                    current_text = section_text

                    # Apply each pattern in sequence
                    for pattern in self.patterns:
                        if is_code_block and pattern.skip_code_blocks:
                            continue

                        new_section, changes = self._apply_pattern_to_section(
                            current_text, pattern, start_line)
                        content_changes.extend(changes)
                        current_text = new_section

                    new_content_parts.append(current_text)

                modified_content = ''.join(new_content_parts)
                all_changes.extend(content_changes)

                # Print all accumulated changes
                if all_changes:
                    lines_changed = 0
                    for line_num, old, new in sorted(all_changes, key=lambda x: x[0]):
                        if not self.config.dry_run:
                            line_num += lines_changed

                        additional_ending_old = self._count_substring_at_end(old, "\n") - 1
                        additional_ending_new = self._count_substring_at_end(new, "\n") - 1

                        print(f"{Fore.YELLOW if self.config.dry_run else Fore.GREEN}"
                            f"[{'WOULD CHANGE' if self.config.dry_run else 'CHANGED'}] "
                            f"{file_path}:{line_num}{Style.RESET_ALL}")

                        red = f"{Fore.RED}"
                        red += f"- {old.rstrip()}" if old else ""
                        for newline in range(0, additional_ending_old): red += "\n-"

                        red += f"{Style.RESET_ALL}"
                        green = f"{Fore.GREEN}"
                        green += f"+ {new.rstrip()}" if new else ""
                        for newline in range(0, additional_ending_new): green += "\n+"

                        print(f"{red}\n{green}{Style.RESET_ALL}\n")

                        lines_changed += new.count('\n') - old.count('\n')

                # Handle newline preservation
                if ends_with_newline and not modified_content.endswith('\n'):
                    modified_content += '\n'
                elif not ends_with_newline and modified_content.endswith('\n'):
                    modified_content = modified_content.rstrip('\n')

                if not self.config.dry_run and modified_content != content:
                    with open(file_path, 'w', newline='') as f:
                        f.write(modified_content)

            except Exception as e:
                print(f"{Fore.RED}Error processing {file_path}: {e}{Style.RESET_ALL}")

def load_config_file(config_path: str) -> Dict:
    """Load configuration from YAML or JSON file."""
    with open(config_path, 'r') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            return yaml.safe_load(f)
        return json.load(f)

def generate_config_dict(args: Optional[Any] = None) -> Dict:
    return {
        'path': args.path if args else None,
        'pattern': args.pattern if args else None,
        'find': args.find if args else None,
        'replace': args.replace if args else None,
        'is_regex': not args.no_regex if args and args.no_regex else None,
        'recursive': not args.no_recursive if args and args.no_recursive else None,
        'dry_run': args.dry_run if args and args.dry_run else None,
        'patterns_file': args.patterns_file if args else None,
        'pattern_name': args.pattern_name if args else None,
        'pattern_list_file': args.pattern_list_file if args else None,
        'pattern_list_name': args.pattern_list_name if args else None,
    }

def set_config_values(config: dict, config_path: str) -> Dict:
    file_config = load_config_file(config_path)

    # Start with file config
    merged_config = file_config.copy()

    # Override with command line args
    for k, v in config.items():
        # For boolean flags, only override if explicitly set
        if k == 'is_regex' and config['is_regex'] == False:
            merged_config[k] = False
            continue

        if k == 'recursive' and config['recursive'] == False:
            merged_config[k] = False
            continue

        if k == 'dry_run' and config['dry_run']:
            merged_config[k] = True
            continue

        if k in config and config[k] is not None:
            merged_config[k] = v
            continue

        if k not in merged_config:
            merged_config[k] = config[k]

    return merged_config

def main():
    parser = argparse.ArgumentParser(description='Advanced find and replace utility')
    parser.add_argument('--path', help='File or directory path to process')
    parser.add_argument('--pattern', help='File pattern to match (e.g., "*.md")')
    parser.add_argument('--find', help='Find pattern')
    parser.add_argument('--replace', help='Replace pattern')
    parser.add_argument('--no-regex', action='store_true', help='Treat find pattern as plain text')
    parser.add_argument('--no-recursive', action='store_true', help='Disable recursive directory search')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    parser.add_argument('--patterns-file', help='Path to patterns YAML/JSON file')
    parser.add_argument('--pattern-name', help='Name of pattern to use from patterns file')
    parser.add_argument('--pattern-list-file', help='Path to pattern list YAML/JSON file')
    parser.add_argument('--pattern-list-name', help='Name of pattern list to use')
    parser.add_argument('--config', help='Path to config YAML/JSON file')

    args = parser.parse_args()

    # Initialize config with default values
    config_dict = generate_config_dict(args)

    # Load and merge config file if provided
    if args.config:
        config_dict = set_config_values(config_dict, args.config)

    config = Config(**config_dict)
    find_replace = FindReplace(config, args.config if args.config else None)
    find_replace.process_files()

if __name__ == '__main__':
    main()
