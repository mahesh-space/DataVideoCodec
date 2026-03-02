"""
FrameGenerator module for the DataVideoCodec Encoder.

Maps an encoded bitstream to video frames by assigning pixel intensity
values in the Luma (Y) channel of YCbCr color space. Each bit is
represented as a block of pixels for robustness against compression.
"""

import numpy as np

from core.constants import (
    LUMA_HIGH,
    LUMA_LOW,
    CHROMA_NEUTRAL,
    SYNC_PATTERN,
    SYNC_ROWS,
)
from core.utils import get_logger

logger = get_logger("FrameGenerator")


class FrameGenerator:
    """Generates video frames from a bit array.

    Each frame is a NumPy array in YCbCr color space (3 channels).
    Bits are mapped to block_size × block_size pixel blocks in the Y channel.
    Cb and Cr channels are set to neutral (128). Sync markers are embedded
    in the first rows of each frame for decoder alignment.
    """

    @staticmethod
    def _compute_capacity(resolution: tuple, block_size: int) -> int:
        """Compute the number of bits that can be stored in one frame.

        The usable area excludes the sync marker rows at the top.

        Args:
            resolution: (width, height) tuple.
            block_size: Pixel block size (2, 4, or 8).

        Returns:
            Number of bits per frame.
        """
        width, height = resolution
        usable_height = height - (SYNC_ROWS * block_size)
        cols = width // block_size
        rows = usable_height // block_size
        return cols * rows

    @staticmethod
    def _embed_sync_marker(frame_y: np.ndarray, block_size: int) -> None:
        """Embed synchronization marker pattern in the top rows of a frame.

        The sync pattern is an alternating LUMA_LOW/LUMA_HIGH pattern
        repeated across the full frame width, occupying the first
        SYNC_ROWS * block_size pixel rows.

        Args:
            frame_y: The Y-channel of the frame (modified in-place).
            block_size: Pixel block size.
        """
        width = frame_y.shape[1]
        pattern_len = len(SYNC_PATTERN)
        sync_row_height = SYNC_ROWS * block_size

        for row in range(sync_row_height):
            for col in range(0, width, block_size):
                pattern_idx = (col // block_size) % pattern_len
                value = SYNC_PATTERN[pattern_idx]
                frame_y[row, col:col + block_size] = value

    @staticmethod
    def generate(bit_array: np.ndarray, block_size: int, resolution: tuple) -> list:
        """Generate video frames from a bit array.

        Args:
            bit_array: 1-D numpy array of 0s and 1s.
            block_size: Size of pixel blocks (2, 4, or 8).
            resolution: Video resolution as (width, height).

        Returns:
            List of numpy arrays, each of shape (height, width, 3) in
            YCbCr color space (uint8).
        """
        width, height = resolution
        bits_per_frame = FrameGenerator._compute_capacity(resolution, block_size)
        total_frames = (len(bit_array) + bits_per_frame - 1) // bits_per_frame

        logger.info(
            f"Generating {total_frames} frames: {width}x{height}, "
            f"block_size={block_size}, bits_per_frame={bits_per_frame}, "
            f"total_bits={len(bit_array)}"
        )

        # Pad bit_array to fill all frames completely (with 0s or neutral)
        # However, we should stay consistent with original logic: 
        # actual data is mapped, remaining capacity in the last frame is neutral gray.
        total_capacity = total_frames * bits_per_frame
        padded_bits = np.full(total_capacity, -1, dtype=np.int8)  # -1 for padding/neutral
        padded_bits[:len(bit_array)] = bit_array

        sync_pixel_rows = SYNC_ROWS * block_size
        usable_height = height - sync_pixel_rows
        cols = width // block_size
        rows = usable_height // block_size

        # Reshape bits into [frames, rows, cols]
        bit_blocks = padded_bits.reshape((total_frames, rows, cols))

        # Map bit values to intensities
        # -1 -> CHROMA_NEUTRAL, 0 -> LUMA_LOW, 1 -> LUMA_HIGH
        intensity_map = np.array([CHROMA_NEUTRAL, LUMA_LOW, LUMA_HIGH], dtype=np.uint8)
        # Shift values from [-1, 0, 1] to [0, 1, 2] for indexing
        frame_data = intensity_map[bit_blocks + 1]

        frames = []
        for i in range(total_frames):
            # Create full frame base
            frame = np.full((height, width, 3), CHROMA_NEUTRAL, dtype=np.uint8)
            frame_y = frame[:, :, 0]

            # Embed sync marker
            FrameGenerator._embed_sync_marker(frame_y, block_size)

            # Upscale blocks to full resolution Y-channel
            # Each bit in frame_data[i] is a block of block_size x block_size
            upscaled = np.repeat(np.repeat(frame_data[i], block_size, axis=0), block_size, axis=1)
            
            # Place upscaled bits into the usable area of the Y channel
            frame_y[sync_pixel_rows : sync_pixel_rows + rows * block_size, : cols * block_size] = upscaled

            frames.append(frame)

            if (i + 1) % 50 == 0 or i == total_frames - 1:
                logger.info(f"  Frame {i + 1}/{total_frames} generated vectorized")

        return frames
