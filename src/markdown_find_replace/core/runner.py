from typing import Optional, Sequence

from .file_processor import FileProcessor
from .file_resolver import FileResolver
from .models import Config, Pattern
from .pattern_applier import PatternApplier
from .pattern_loader import PatternLoader
from .section_splitter import SectionSplitter


class FindReplace:
    def __init__(
        self,
        config: Config,
        config_file_path: Optional[str] = None,
        pattern_loader: Optional[PatternLoader] = None,
        file_processor: Optional[FileProcessor] = None,
    ):
        self.config = config
        self.resolver = FileResolver(config_file_path)
        self.pattern_loader = pattern_loader or PatternLoader(config, self.resolver)
        splitter = SectionSplitter()
        applier = PatternApplier()
        self.file_processor = file_processor or FileProcessor(config, splitter, applier)
        self.patterns: Sequence[Pattern] = self.pattern_loader.load()

    def process_files(self) -> None:
        self.file_processor.process_files(self.patterns)

    def resolve_path(self, file_path: str) -> str:
        return self.resolver.resolve(file_path)
