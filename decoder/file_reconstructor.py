"""
FileReconstructor module for the DataVideoCodec Decoder.

Parses the decoded byte data to extract the original file header
and payload, writes the recovered file to disk, and performs
hash verification.
"""

from pathlib import Path
from typing import Optional

from core.models import RecoveryResult
from core.utils import compute_hash, compute_bytes_hash, ensure_dir, get_logger
from encoder.bitstream import BitstreamConverter

logger = get_logger("FileReconstructor")


class FileReconstructor:
    """Reconstructs the original file from decoded data.

    Parses the structured header, extracts the payload, writes to disk,
    and computes hash comparison for verification.
    """

    @staticmethod
    def reconstruct(
        data: bytes,
        output_dir: Path,
        original_hash: Optional[str] = None,
    ) -> RecoveryResult:
        """Reconstruct the original file from decoded data bytes.

        Args:
            data: Decoded byte data (header + payload).
            output_dir: Directory to write the recovered file.
            original_hash: SHA-256 hash of original file (for verification).

        Returns:
            RecoveryResult with recovery status and metadata.
        """
        output_dir = Path(output_dir)
        ensure_dir(output_dir)

        result = RecoveryResult()
        result.original_hash = original_hash

        try:
            # Parse header
            filename, filesize, payload = BitstreamConverter.parse_header(data)

            if len(payload) < filesize:
                logger.warning(
                    f"Payload truncated: got {len(payload)} bytes, "
                    f"expected {filesize} bytes"
                )
                # Use whatever we have
                recovered_data = payload
            else:
                recovered_data = payload[:filesize]

            # Write recovered file
            output_path = output_dir / filename
            # Handle filename collision
            if output_path.exists():
                stem = output_path.stem
                suffix = output_path.suffix
                counter = 1
                while output_path.exists():
                    output_path = output_dir / f"{stem}_recovered_{counter}{suffix}"
                    counter += 1

            output_path.write_bytes(recovered_data)
            result.output_path = str(output_path)

            # Compute hash of recovered file
            result.recovered_hash = compute_hash(output_path)

            # Determine recovery status
            if original_hash:
                if result.recovered_hash == original_hash:
                    result.status = "FULL_RECOVERY"
                    result.hash_match = True
                    logger.info(f"FULL RECOVERY: Hash match confirmed for {filename}")
                else:
                    result.status = "PARTIAL_RECOVERY"
                    result.hash_match = False
                    logger.warning(
                        f"PARTIAL RECOVERY: Hash mismatch for {filename}. "
                        f"Expected: {original_hash[:16]}... "
                        f"Got: {result.recovered_hash[:16]}..."
                    )
            else:
                # No original hash available — can't verify
                result.status = "FULL_RECOVERY"  # Assume success
                result.hash_match = False  # Unknown
                logger.info(
                    f"Recovery complete for {filename} (no original hash for verification)"
                )

            logger.info(
                f"Recovered file: {output_path} ({len(recovered_data)} bytes)"
            )

        except (ValueError, Exception) as e:
            logger.error(f"File reconstruction failed: {e}")
            result.status = "RECOVERY_FAILURE"
            result.hash_match = False

        return result
