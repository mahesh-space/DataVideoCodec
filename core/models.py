"""
Data models for the DataVideoCodec System.

Defines dataclasses for encoding parameters, recovery results,
and manifest metadata used across all modules.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Tuple
import json


@dataclass
class EncodingParams:
    """Configuration parameters for encoding/decoding operations.

    Attributes:
        resolution: Video resolution as (width, height) tuple.
        block_size: Pixel block size (2, 4, or 8). Each bit maps to a block_size x block_size area.
        ecc_overhead: Reed-Solomon ECC overhead as a fraction (0.1, 0.2, or 0.4).
        fps: Video frame rate (default 30).
    """
    resolution: Tuple[int, int] = (1280, 720)
    block_size: int = 4
    ecc_overhead: float = 0.2
    fps: int = 30

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EncodingParams":
        """Create from dictionary."""
        return cls(
            resolution=tuple(data["resolution"]),
            block_size=data["block_size"],
            ecc_overhead=data["ecc_overhead"],
            fps=data.get("fps", 30),
        )


@dataclass
class RecoveryResult:
    """Result of a decode/recovery operation.

    Attributes:
        output_path: Path to the recovered file (if any).
        status: One of 'FULL_RECOVERY', 'PARTIAL_RECOVERY', or 'RECOVERY_FAILURE'.
        ber_before_ecc: Bit Error Rate before ECC correction.
        ber_after_ecc: Bit Error Rate after ECC correction.
        errors_corrected: Total number of symbol errors corrected by ECC.
        errors_uncorrectable: Number of ECC blocks that could not be corrected.
        hash_match: Whether SHA-256 hash of recovered file matches original.
        original_hash: SHA-256 hash of original file (if known).
        recovered_hash: SHA-256 hash of recovered file.
    """
    output_path: Optional[str] = None
    status: str = "RECOVERY_FAILURE"
    ber_before_ecc: float = 0.0
    ber_after_ecc: float = 0.0
    errors_corrected: int = 0
    errors_uncorrectable: int = 0
    hash_match: bool = False
    original_hash: Optional[str] = None
    recovered_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Manifest:
    """Encoding manifest saved alongside the video file.

    Contains all parameters and metadata needed to decode the video
    back into the original file.

    Attributes:
        original_filename: Name of the original input file.
        original_filesize: Size of the original file in bytes.
        original_hash: SHA-256 hash of the original file.
        params: Encoding parameters used.
        frame_count: Total number of video frames generated.
        total_bits: Total number of data bits (before ECC).
        total_ecc_bits: Total number of bits after ECC encoding.
        version: Manifest format version.
    """
    original_filename: str = ""
    original_filesize: int = 0
    original_hash: str = ""
    params: EncodingParams = field(default_factory=EncodingParams)
    frame_count: int = 0
    total_bits: int = 0
    total_ecc_bits: int = 0
    version: str = "1.0"

    def save(self, filepath: Path) -> None:
        """Save manifest to JSON file."""
        data = {
            "original_filename": self.original_filename,
            "original_filesize": self.original_filesize,
            "original_hash": self.original_hash,
            "params": self.params.to_dict(),
            "frame_count": self.frame_count,
            "total_bits": self.total_bits,
            "total_ecc_bits": self.total_ecc_bits,
            "version": self.version,
        }
        filepath = Path(filepath)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: Path) -> "Manifest":
        """Load manifest from JSON file."""
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            original_filename=data["original_filename"],
            original_filesize=data["original_filesize"],
            original_hash=data["original_hash"],
            params=EncodingParams.from_dict(data["params"]),
            frame_count=data["frame_count"],
            total_bits=data["total_bits"],
            total_ecc_bits=data["total_ecc_bits"],
            version=data.get("version", "1.0"),
        )
