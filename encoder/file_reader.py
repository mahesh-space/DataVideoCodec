"""
FileReader module for the DataVideoCodec Encoder.

Reads binary files and produces raw bytes with metadata
for the encoding pipeline.
"""

import mimetypes
from pathlib import Path
from typing import Dict, Tuple

from core.utils import get_logger

logger = get_logger("FileReader")


class FileReader:
    """Reads an input file and prepares it for the encoding pipeline.

    Validates file existence and permissions, reads the raw binary content,
    and extracts metadata (filename, size, MIME type).
    """

    @staticmethod
    def read(filepath: Path) -> Tuple[bytes, Dict[str, object]]:
        """Read a file and return its binary content and metadata.

        Args:
            filepath: Path to the input file.

        Returns:
            Tuple of (raw_bytes, metadata_dict).
            metadata_dict contains:
                - 'filename': Original filename (str)
                - 'filesize': File size in bytes (int)
                - 'mime_type': Detected MIME type (str)

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
            ValueError: If the file is empty.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Input file not found: {filepath}")
        if not filepath.is_file():
            raise ValueError(f"Path is not a file: {filepath}")

        raw_bytes = filepath.read_bytes()
        if len(raw_bytes) == 0:
            raise ValueError(f"Input file is empty: {filepath}")

        mime_type, _ = mimetypes.guess_type(str(filepath))
        if mime_type is None:
            mime_type = "application/octet-stream"

        metadata = {
            "filename": filepath.name,
            "filesize": len(raw_bytes),
            "mime_type": mime_type,
        }

        logger.info(
            f"Read file: {filepath.name} ({len(raw_bytes)} bytes, {mime_type})"
        )
        return raw_bytes, metadata
