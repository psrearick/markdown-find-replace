from dataclasses import dataclass
from typing import Optional


@dataclass
class Pattern:
    name: str
    find: str
    replace: str
    is_regex: bool = True
    skip_code_blocks: bool = False
    skip_tables: bool = False


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
    ensure_new_line: bool = False


@dataclass
class Section:
    start_line: int
    text: str
    is_code_block: bool
    is_table: bool
