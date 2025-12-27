import json
from typing import Dict, List

import yaml
from colorama import Fore, Style

from .file_resolver import FileResolver
from .models import Config, Pattern


class PatternLoader:
    def __init__(self, config: Config, resolver: FileResolver):
        self.config = config
        self.resolver = resolver

    def load(self) -> List[Pattern]:
        patterns: List[Pattern] = []
        if self.config.find and self.config.replace:
            patterns.append(
                Pattern(
                    name="command_line",
                    find=self._normalize(self.config.find),
                    replace=self._normalize(self.config.replace),
                    is_regex=self.config.is_regex,
                )
            )

        patterns.extend(self._load_from_files())
        return patterns

    def _load_from_files(self) -> List[Pattern]:
        patterns: List[Pattern] = []

        if self.config.patterns_file and self.config.pattern_name:
            catalog = self._load_yaml_or_json(self.config.patterns_file)
            pattern_data = catalog.get(self.config.pattern_name)
            if pattern_data:
                patterns.append(self._build_pattern(pattern_data))

        if self.config.pattern_list_file and self.config.pattern_list_name:
            if not self.config.patterns_file:
                print(
                    f"{Fore.RED}Error: patterns file must be provided when using pattern lists{Style.RESET_ALL}"
                )
                return patterns

            catalog = self._load_yaml_or_json(self.config.patterns_file)
            lists = self._load_yaml_or_json(self.config.pattern_list_file)
            for pattern_name in lists.get(self.config.pattern_list_name, []):
                pattern_data = catalog.get(pattern_name)
                if pattern_data:
                    patterns.append(self._build_pattern(pattern_data))
                else:
                    print(
                        f"{Fore.YELLOW}Warning: Pattern '{pattern_name}' not found in patterns file{Style.RESET_ALL}"
                    )

        return patterns

    def _build_pattern(self, raw: Dict) -> Pattern:
        data = raw.copy()
        data["find"] = self._normalize(data["find"])
        data["replace"] = self._normalize(data["replace"])
        return Pattern(**data)

    def _normalize(self, pattern: str) -> str:
        return pattern

    def _load_yaml_or_json(self, file_path: str) -> Dict:
        resolved_path = self.resolver.resolve(file_path)
        with open(resolved_path, encoding="utf-8") as handle:
            if resolved_path.endswith((".yaml", ".yml")):
                return yaml.safe_load(handle)
            return json.load(handle)
