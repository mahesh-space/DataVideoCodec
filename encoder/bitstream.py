"""
BitstreamConverter module for the DataVideoCodec Encoder.

Converts raw file bytes (with a structured header) into a flat
bit array for pixel-level encoding, and provides the inverse
conversion for the decoder.
"""

import struct
import numpy as np

from core.constants import HEADER_MAGIC, HEADER_FILESIZE_BYTES, HEADER_FILENAME_BYTES, HEADER_TOTAL_BYTES
from core.utils import get_logger

logger = get_logger("BitstreamConverter")


class BitstreamConverter:
    """Converts between byte data and bit arrays.

    The encoding format prepends a structured header to the file payload:
      - 4 bytes: Magic identifier ('DVCD')
      - 4 bytes: File size (uint32, big-endian)
      - 256 bytes: Filename (UTF-8, null-padded)
      - N bytes: File payload
    """

    @staticmethod
    def build_header(filename: str, filesize: int) -> bytes:
        """Build the binary header for the encoded bitstream.

        Args:
            filename: Original filename (will be truncated to 255 chars).
            filesize: Original file size in bytes.

        Returns:
            264-byte header as bytes.
        """
        # Magic bytes
        header = HEADER_MAGIC

        # File size as 4-byte big-endian unsigned int
        header += struct.pack(">I", filesize)

        # Filename: UTF-8 encoded, padded with null bytes to 256 bytes
        name_bytes = filename.encode("utf-8")[:HEADER_FILENAME_BYTES]
        name_bytes = name_bytes.ljust(HEADER_FILENAME_BYTES, b"\x00")
        header += name_bytes

        assert len(header) == HEADER_TOTAL_BYTES, f"Header size mismatch: {len(header)}"
        return header

    @staticmethod
    def to_bits(data: bytes) -> np.ndarray:
        """Convert byte data to a flat bit array (big-endian bit ordering).

        Args:
            data: Raw byte data (typically header + payload).

        Returns:
            1-D numpy array of uint8 values (0 or 1).
        """
        byte_array = np.frombuffer(data, dtype=np.uint8)
        # Unpack each byte into 8 bits (big-endian: MSB first)
        bits = np.unpackbits(byte_array)
        logger.info(f"Converted {len(data)} bytes to {len(bits)} bits")
        return bits

    @staticmethod
    def to_bytes(bits: np.ndarray) -> bytes:
        """Convert a bit array back to bytes.

        Args:
            bits: 1-D numpy array of 0s and 1s. Length will be padded
                  to a multiple of 8 if necessary.

        Returns:
            Byte data.
        """
        # Pad to multiple of 8
        remainder = len(bits) % 8
        if remainder != 0:
            bits = np.concatenate([bits, np.zeros(8 - remainder, dtype=np.uint8)])
        byte_array = np.packbits(bits)
        return byte_array.tobytes()

    @staticmethod
    def parse_header(data: bytes):
        """Parse the structured header from decoded byte data.

        Args:
            data: Raw byte data starting with the header.

        Returns:
            Tuple of (filename, filesize, payload_bytes).

        Raises:
            ValueError: If magic bytes don't match or data is too short.
        """
        if len(data) < HEADER_TOTAL_BYTES:
            raise ValueError(
                f"Data too short for header: {len(data)} < {HEADER_TOTAL_BYTES}"
            )

        magic = data[:4]
        if magic != HEADER_MAGIC:
            raise ValueError(
                f"Invalid magic bytes: {magic!r} (expected {HEADER_MAGIC!r})"
            )

        filesize = struct.unpack(">I", data[4:8])[0]

        filename_raw = data[8:8 + HEADER_FILENAME_BYTES]
        filename = filename_raw.rstrip(b"\x00").decode("utf-8", errors="replace")

        payload = data[HEADER_TOTAL_BYTES:HEADER_TOTAL_BYTES + filesize]

        logger.info(f"Parsed header: filename={filename}, filesize={filesize}")
        return filename, filesize, payload
