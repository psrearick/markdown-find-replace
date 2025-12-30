#!/usr/bin/env python3
import argparse
from importlib.resources import files
from .core import Config, FindReplace, generate_config_dict, set_config_values

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Advanced find and replace utility')
    parser.add_argument('--path', help='File or directory path to process')
    parser.add_argument('--pattern', help='File pattern to match (e.g., "*.md")')
    parser.add_argument('--find', help='Find pattern')
    parser.add_argument('--replace', help='Replace pattern')
    parser.add_argument('--frontmatter_in_body', action='store_true', help='Has frontmatter in mardown body')
    parser.add_argument('--no-regex', action='store_true', help='Treat find pattern as plain text')
    parser.add_argument('--no-recursive', action='store_true', help='Disable recursive directory search')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    parser.add_argument('--patterns-file', help='Path to patterns YAML/JSON file')
    parser.add_argument('--pattern-name', help='Name of pattern to use from patterns file')
    parser.add_argument('--pattern-list-file', help='Path to pattern list YAML/JSON file')
    parser.add_argument('--pattern-list-name', help='Name of pattern list to use')
    parser.add_argument('--ensure-new-line', action='store_true', help='End output files in a new line')
    parser.add_argument('--config', help='Path to config YAML/JSON file')
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config_dict = generate_config_dict(args)

    if not args.config:
        args.config = str(files('markdown_find_replace.config').joinpath('fr_config.yaml'))

    config_dict = set_config_values(config_dict, args.config)

    config = Config(**config_dict)
    FindReplace(config, args.config).process_files()
