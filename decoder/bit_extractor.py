"""
BitExtractor module for the DataVideoCodec Decoder.

Extracts bit values from pixel blocks in the Y-channel of video frames
using threshold-based decision logic.
"""

import numpy as np

from core.constants import THRESHOLD, SYNC_ROWS
from core.utils import get_logger

logger = get_logger("BitExtractor")


class BitExtractor:
    """Extracts binary data from video frames.

    Reads pixel blocks from the Y-channel, computes the average intensity
    per block, and applies a threshold to decide each bit value (0 or 1).
    """

    @staticmethod
    def extract_frame(
        frame: np.ndarray,
        block_size: int,
        resolution: tuple,
    ) -> np.ndarray:
        """Extract bits from a single aligned video frame using NumPy vectorization.

        Args:
            frame: Aligned frame in YCbCr (height, width, 3).
            block_size: Pixel block size used during encoding.
            resolution: Video resolution as (width, height).

        Returns:
            1-D numpy array of extracted bits (0s and 1s) from this frame.
        """
        width, height = resolution
        sync_pixel_rows = SYNC_ROWS * block_size
        cols = width // block_size
        rows = height // block_size - SYNC_ROWS  # rows in usable area

        # Extract usable Y-channel area
        frame_y = frame[sync_pixel_rows : sync_pixel_rows + rows * block_size, : cols * block_size, 0]
        
        # Reshape frame into blocks: (rows, block_size, cols, block_size)
        blocks = frame_y.reshape(rows, block_size, cols, block_size)
        
        # Compute average intensity per block (mean over axis 1 and 3)
        avg_intensities = blocks.mean(axis=(1, 3))
        
        # Applying threshold decision (vectorized)
        bits = (avg_intensities >= THRESHOLD).astype(np.uint8)
        return bits.flatten()

    @staticmethod
    def extract(
        frames: list,
        block_size: int,
        resolution: tuple,
        total_bits: int = None,
    ) -> np.ndarray:
        """Compatibility method for non-streaming calls."""
        all_bits = []
        for frame in frames:
            all_bits.append(BitExtractor.extract_frame(frame, block_size, resolution))
        
        if not all_bits:
            return np.array([], dtype=np.uint8)
            
        result = np.concatenate(all_bits)
        if total_bits is not None:
            result = result[:total_bits]
        return result
