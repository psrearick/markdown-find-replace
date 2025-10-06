import json
from typing import Any, Dict, Optional

import yaml


def load_config_file(config_path: str) -> Dict:
    with open(config_path, encoding='utf-8') as handle:
        if config_path.endswith(('.yaml', '.yml')):
            return yaml.safe_load(handle)
        return json.load(handle)


def generate_config_dict(args: Optional[Any] = None) -> Dict:
    return {
        'path': args.path if args else None,
        'pattern': args.pattern if args else None,
        'find': args.find if args else None,
        'replace': args.replace if args else None,
        'is_regex': (not args.no_regex) if args and args.no_regex else None,
        'recursive': (not args.no_recursive) if args and args.no_recursive else None,
        'dry_run': args.dry_run if args and args.dry_run else None,
        'patterns_file': args.patterns_file if args else None,
        'pattern_name': args.pattern_name if args else None,
        'pattern_list_file': args.pattern_list_file if args else None,
        'pattern_list_name': args.pattern_list_name if args else None,
    }


def set_config_values(config: Dict, config_path: str) -> Dict:
    file_config = load_config_file(config_path)
    merged_config = file_config.copy()

    for key, value in config.items():
        if key == 'is_regex' and config.get('is_regex') is False:
            merged_config[key] = False
            continue
        if key == 'recursive' and config.get('recursive') is False:
            merged_config[key] = False
            continue
        if key == 'dry_run' and config.get('dry_run'):
            merged_config[key] = True
            continue
        if value is not None:
            merged_config[key] = value
            continue
        if key not in merged_config:
            merged_config[key] = value

    return merged_config
