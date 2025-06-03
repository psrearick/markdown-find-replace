# Markdown Find and Replace

A powerful Python utility for performing advanced find and replace operations on Markdown files with support for regex patterns, batch processing, and smart code block handling.

## Features

- **Regex and Plain Text Support**: Use regular expressions or plain text for find and replace operations
- **Smart Code Block Handling**: Optionally skip code blocks and frontmatter during replacements
- **Batch Processing**: Apply multiple patterns at once using pattern lists
- **Configuration Files**: Store patterns and settings in YAML/JSON files for reusability
- **Dry Run Mode**: Preview changes without modifying files
- **Recursive Directory Processing**: Process entire directory trees
- **Colorized Output**: Clear visual feedback with colored terminal output
- **Frontmatter Preservation**: Safely handle YAML frontmatter in Markdown files

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd markdown-find-replace
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

Replace text in a single file:
```bash
python find_replace.py --path "document.md" --find "old text" --replace "new text"
```

Process all Markdown files in a directory:
```bash
python find_replace.py --path "docs/" --pattern "*.md" --find "old text" --replace "new text"
```

### Using Configuration Files

Apply predefined patterns:
```bash
python find_replace.py --config config/fr_config.yaml
```

Use a specific pattern from a patterns file:
```bash
python find_replace.py --patterns-file config/fr_patterns.yaml --pattern-name normalize_list_spaces
```

Apply a pattern list (multiple patterns at once):
```bash
python find_replace.py --patterns-file config/fr_patterns.yaml --pattern-list-file config/fr_list.yaml --pattern-list-name normalize_markdown
```

## Command Line Options

| Option                | Description                                       |
| --------------------- | ------------------------------------------------- |
| `--path`              | File or directory path to process                 |
| `--pattern`           | File pattern to match (e.g., "*.md")              |
| `--find`              | Find pattern (text or regex)                      |
| `--replace`           | Replace pattern                                   |
| `--no-regex`          | Treat find pattern as plain text instead of regex |
| `--no-recursive`      | Disable recursive directory search                |
| `--dry-run`           | Show changes without applying them                |
| `--patterns-file`     | Path to patterns YAML/JSON file                   |
| `--pattern-name`      | Name of pattern to use from patterns file         |
| `--pattern-list-file` | Path to pattern list YAML/JSON file               |
| `--pattern-list-name` | Name of pattern list to use                       |
| `--config`            | Path to config YAML/JSON file                     |

## Configuration Files

### Config File (`fr_config.yaml`)

```yaml
pattern: "*.md"
recursive: true
dry_run: false
pattern_list_file: "fr_list.yaml"
patterns_file: "fr_patterns.yaml"
pattern_list_name: "normalize_markdown"
```

### Patterns File (`fr_patterns.yaml`)

Define reusable find/replace patterns:

```yaml
normalize_list_spaces:
  name: "normalize_list_spaces"
  find: "(\\n{0,})\\n*^( *)([\\*\\-.]|\\d+\\.*) {2,}"
  replace: "$1$2$3 "
  is_regex: true
  skip_code_blocks: true

remove_trailing_spaces:
  name: "remove_trailing_spaces"
  find: " +$"
  replace: ""
  is_regex: true
  skip_code_blocks: true
```

### Pattern Lists File (`fr_list.yaml`)

Group patterns into lists for batch processing:

```yaml
normalize_markdown:
  - "tabs_to_spaces"
  - "normalize_list_spaces"
  - "remove_list_blank_lines"
  - "start_lists_with_dashes"
  - "remove_bold_headings"
  - "remove_trailing_spaces"

clean_formatting:
  - "remove_inline_code"
  - "remove_remaining_bold"
  - "remove_remaining_italicized"
```

## Built-in Pattern Lists

The project includes several pre-configured pattern lists:

### `normalize_markdown`
A comprehensive set of patterns to standardize Markdown formatting:
- Convert tabs to spaces
- Normalize list spacing and indentation
- Standardize list markers (use dashes)
- Remove bold from headings
- Fix line breaks around headings
- Replace smart quotes with regular quotes
- Remove trailing spaces
- And more...

### `remove_bold_italics_backticks`
Selectively remove formatting while preserving important elements:
- Protect first-level bold list items
- Remove inline code backticks
- Remove remaining bold and italic formatting
- Restore protected formatting

## Pattern Configuration Options

Each pattern supports the following options:

- `name`: Pattern identifier
- `find`: The search pattern (regex or plain text)
- `replace`: The replacement text (supports regex groups like `$1`, `$2`)
- `is_regex`: Whether to treat the find pattern as regex (default: true)
- `skip_code_blocks`: Whether to skip code blocks and frontmatter (default: false)

## Examples

### Clean up Markdown formatting
```bash
python find_replace.py --path "docs/" --pattern "*.md" --patterns-file config/fr_patterns.yaml --pattern-list-file config/fr_list.yaml --pattern-list-name normalize_markdown
```

### Remove all bold formatting from a file
```bash
python find_replace.py --path "document.md" --find "\\*\\*(.+?)\\*\\*" --replace "$1"
```

### Preview changes without applying them
```bash
python find_replace.py --path "docs/" --pattern "*.md" --find "old text" --replace "new text" --dry-run
```

### Convert smart quotes to regular quotes
```bash
python find_replace.py --path "document.md" --find """ --replace "\"" --no-regex
```

## Smart Code Block Handling

When `skip_code_blocks` is enabled, the tool will:
- Skip content within code fences (```)
- Skip YAML frontmatter (content between `---` markers)
- Skip inline code (content between backticks)

This ensures that code examples and metadata aren't accidentally modified.

## Regular Expression Support

The tool supports full Python regex functionality:
- Capture groups: `(pattern)`
- Backreferences: `$1`, `$2`, etc.
- Multiline matching
- Common flags like case-insensitive matching

### Regex Examples

Replace headings with title case:
```bash
--find "^(#+) (.+)" --replace "$1 \u$2"
```

Remove extra whitespace:
```bash
--find "\\s+" --replace " "
```

## Error Handling

The tool includes comprehensive error handling:
- File encoding detection and handling
- Graceful handling of binary files
- Detailed error messages with file paths
- Continues processing other files if one fails

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
