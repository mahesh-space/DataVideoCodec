"""
SyncDetector module for the DataVideoCodec Decoder.

Detects the synchronization marker pattern in each video frame
to establish correct pixel grid alignment, compensating for
compression-induced spatial shifts.
"""

import numpy as np

from core.constants import LUMA_HIGH, LUMA_LOW, SYNC_PATTERN, SYNC_ROWS, THRESHOLD
from core.utils import get_logger

logger = get_logger("SyncDetector")


class SyncDetector:
    """Detects sync markers and aligns frames for bit extraction.

    Uses cross-correlation with the expected sync pattern to find
    the horizontal offset of the pixel grid. Vertical offset is
    assumed to be at the top of the frame.
    """

    @staticmethod
    def _build_reference_pattern(width: int, block_size: int) -> np.ndarray:
        """Build the expected sync pattern for cross-correlation.

        Args:
            width: Frame width in pixels.
            block_size: Pixel block size.

        Returns:
            1-D numpy array of expected intensity values across one row.
        """
        pattern_len = len(SYNC_PATTERN)
        ref = np.zeros(width, dtype=np.float32)
        for col in range(0, width, block_size):
            idx = (col // block_size) % pattern_len
            ref[col:col + block_size] = SYNC_PATTERN[idx]
        return ref

    @staticmethod
    def detect_offset(frame_y: np.ndarray, block_size: int) -> int:
        """Detect horizontal offset of the sync pattern using dot-product sweep.

        Args:
            frame_y: Y-channel of the frame.
            block_size: Pixel block size.

        Returns:
            Horizontal pixel offset.
        """
        width = frame_y.shape[1]
        ref_pattern = SyncDetector._build_reference_pattern(width, block_size)

        # Average the sync marker rows to reduce noise
        sync_row = np.mean(
            frame_y[:SYNC_ROWS * block_size, :].astype(np.float32), axis=0
        )

        best_offset = 0
        best_corr = -np.inf

        max_shift = min(block_size * 2, width // 4)
        for offset in range(-max_shift, max_shift + 1):
            if offset >= 0:
                shifted = sync_row[offset:]
                ref_slice = ref_pattern[:len(shifted)]
            else:
                shifted = sync_row[:offset]
                ref_slice = ref_pattern[-offset:]

            if len(shifted) == 0 or len(ref_slice) == 0:
                continue

            min_len = min(len(shifted), len(ref_slice))
            corr = np.dot(shifted[:min_len], ref_slice[:min_len])

            if corr > best_corr:
                best_corr = corr
                best_offset = offset

        return best_offset

    @staticmethod
    def align(frame: np.ndarray, block_size: int) -> np.ndarray:
        """Align a frame by detecting and correcting sync marker offset.

        Args:
            frame: Full frame in YCbCr (height, width, 3).
            block_size: Pixel block size.

        Returns:
            Aligned frame (may be shifted horizontally).
        """
        frame_y = frame[:, :, 0]
        offset = SyncDetector.detect_offset(frame_y, block_size)

        if offset == 0:
            return frame

        logger.info(f"Detected sync offset: {offset} pixels")

        # Shift the frame horizontally
        if offset > 0:
            aligned = np.zeros_like(frame)
            aligned[:, :frame.shape[1] - offset, :] = frame[:, offset:, :]
        else:
            aligned = np.zeros_like(frame)
            aligned[:, -offset:, :] = frame[:, :frame.shape[1] + offset, :]

        return aligned
