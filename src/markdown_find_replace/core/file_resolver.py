from pathlib import Path
from typing import Optional


class FileResolver:
    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path

    def resolve(self, file_path: str) -> str:
        if not file_path:
            return file_path

        path = Path(file_path)
        if path.is_absolute():
            return str(path)

        if self.config_file_path:
            config_dir = Path(self.config_file_path).parent
            candidate = config_dir / file_path
            if candidate.exists():
                return str(candidate)

        return file_path
