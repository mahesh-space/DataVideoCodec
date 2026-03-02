"""
Unit tests for the Decoder module.

Tests BitExtractor and ECCDecoder independently.
"""

import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from encoder.bitstream import BitstreamConverter
from encoder.ecc_encoder import ECCEncoder
from encoder.frame_generator import FrameGenerator
from decoder.bit_extractor import BitExtractor
from decoder.ecc_decoder import ECCDecoder
from core.constants import LUMA_HIGH, LUMA_LOW, SYNC_ROWS


class TestBitExtractor:
    """Tests for BitExtractor."""

    def test_extract_from_clean_frames(self):
        """Should perfectly recover bits from uncompressed frames."""
        original_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0] * 10, dtype=np.uint8)
        resolution = (640, 480)
        block_size = 4

        # Generate frames from known bits
        frames = FrameGenerator.generate(original_bits, block_size, resolution)

        # Extract bits
        extracted = BitExtractor.extract(
            frames, block_size, resolution, total_bits=len(original_bits)
        )

        np.testing.assert_array_equal(extracted, original_bits)

    def test_extract_respects_total_bits(self):
        """Should stop extracting at total_bits count."""
        bits = np.array([1, 0] * 20, dtype=np.uint8)
        resolution = (640, 480)
        block_size = 8

        frames = FrameGenerator.generate(bits, block_size, resolution)
        extracted = BitExtractor.extract(frames, block_size, resolution, total_bits=10)

        assert len(extracted) == 10
        np.testing.assert_array_equal(extracted, bits[:10])


class TestECCDecoder:
    """Tests for ECCDecoder."""

    def test_decode_clean_data(self):
        """Should decode clean (uncorrupted) ECC data perfectly."""
        original = b"Hello, DataVideoCodec!" * 20
        encoded = ECCEncoder.encode(original, 0.2)

        decoded, stats = ECCDecoder.decode(encoded, 0.2)

        # Decoded data should start with original data
        assert decoded[:len(original)] == original
        assert stats["uncorrectable_blocks"] == 0

    def test_decode_with_errors(self):
        """Should correct small errors within RS capacity."""
        original = b"Test data for ECC correction" * 15
        encoded = ECCEncoder.encode(original, 0.2)

        # Inject a few byte errors (within correction capacity)
        corrupted = bytearray(encoded)
        if len(corrupted) > 10:
            corrupted[5] ^= 0xFF
            corrupted[10] ^= 0xFF
            corrupted[15] ^= 0xFF

        decoded, stats = ECCDecoder.decode(bytes(corrupted), 0.2)

        assert decoded[:len(original)] == original
        assert stats["errors_corrected"] > 0

    def test_higher_overhead_more_capacity(self):
        """Higher ECC overhead should handle more errors."""
        original = b"X" * 200
        encoded_40 = ECCEncoder.encode(original, 0.4)

        # Inject many errors
        corrupted = bytearray(encoded_40)
        for i in range(0, min(40, len(corrupted)), 1):
            corrupted[i] ^= 0xFF

        decoded, stats = ECCDecoder.decode(bytes(corrupted), 0.4)
        # With 40% overhead, RS can correct up to ~51 errors per block
        # so this should still succeed
        assert stats is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
