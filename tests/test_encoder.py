"""
Unit tests for the Encoder module.

Tests BitstreamConverter, ECCEncoder, and FrameGenerator independently.
"""

import numpy as np
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from encoder.bitstream import BitstreamConverter
from encoder.ecc_encoder import ECCEncoder
from encoder.frame_generator import FrameGenerator
from core.constants import LUMA_HIGH, LUMA_LOW, SYNC_ROWS, HEADER_TOTAL_BYTES


class TestBitstreamConverter:
    """Tests for BitstreamConverter."""

    def test_build_header_correct_size(self):
        """Header should always be exactly HEADER_TOTAL_BYTES."""
        header = BitstreamConverter.build_header("test.txt", 1024)
        assert len(header) == HEADER_TOTAL_BYTES

    def test_build_header_magic(self):
        """Header should start with magic bytes DVCD."""
        header = BitstreamConverter.build_header("test.txt", 100)
        assert header[:4] == b"DVCD"

    def test_to_bits_length(self):
        """Bit array length should be 8 * byte count."""
        data = b"\xAB\xCD\xEF"
        bits = BitstreamConverter.to_bits(data)
        assert len(bits) == 24

    def test_to_bits_and_back(self):
        """Round-trip: bytes → bits → bytes should be identity."""
        original = b"Hello, World! 12345"
        bits = BitstreamConverter.to_bits(original)
        recovered = BitstreamConverter.to_bytes(bits)
        assert recovered == original

    def test_parse_header_round_trip(self):
        """Build a header, prepend to payload, parse it back."""
        filename = "myfile.pdf"
        payload = b"X" * 512
        header = BitstreamConverter.build_header(filename, len(payload))
        full_data = header + payload

        parsed_name, parsed_size, parsed_payload = BitstreamConverter.parse_header(full_data)
        assert parsed_name == filename
        assert parsed_size == len(payload)
        assert parsed_payload == payload

    def test_parse_header_invalid_magic(self):
        """Should raise ValueError for wrong magic bytes."""
        with pytest.raises(ValueError, match="Invalid magic bytes"):
            BitstreamConverter.parse_header(b"XXXX" + b"\x00" * 300)


class TestECCEncoder:
    """Tests for ECCEncoder."""

    def test_encode_increases_size(self):
        """ECC encoding should produce more bytes than input."""
        data = b"A" * 200
        encoded = ECCEncoder.encode(data, 0.2)
        assert len(encoded) > len(data)

    def test_overhead_levels(self):
        """Higher overhead should produce larger output."""
        data = b"B" * 500
        size_10 = len(ECCEncoder.encode(data, 0.1))
        size_20 = len(ECCEncoder.encode(data, 0.2))
        size_40 = len(ECCEncoder.encode(data, 0.4))
        assert size_10 < size_20 < size_40

    def test_get_block_size(self):
        """Block size k should decrease with higher overhead."""
        k_10 = ECCEncoder.get_block_size(0.1)
        k_20 = ECCEncoder.get_block_size(0.2)
        k_40 = ECCEncoder.get_block_size(0.4)
        assert k_10 > k_20 > k_40
        assert k_10 + k_20 + k_40 > 0  # All positive


class TestFrameGenerator:
    """Tests for FrameGenerator."""

    def test_frame_resolution(self):
        """Generated frames should have correct dimensions."""
        bits = np.array([0, 1] * 100, dtype=np.uint8)
        frames = FrameGenerator.generate(bits, block_size=4, resolution=(1280, 720))
        assert frames[0].shape == (720, 1280, 3)

    def test_frame_has_sync_marker(self):
        """First rows should contain sync marker (alternating pattern)."""
        bits = np.array([1] * 50, dtype=np.uint8)
        frames = FrameGenerator.generate(bits, block_size=4, resolution=(640, 480))
        frame_y = frames[0][:, :, 0]

        # Check sync area has non-uniform values (alternating pattern)
        sync_area = frame_y[:SYNC_ROWS * 4, :]
        unique_values = np.unique(sync_area)
        assert len(unique_values) >= 2  # Should have at least LOW and HIGH

    def test_bit_encoding_values(self):
        """Bit 1 should map to LUMA_HIGH, bit 0 to LUMA_LOW."""
        bits = np.array([1, 0], dtype=np.uint8)
        frames = FrameGenerator.generate(bits, block_size=4, resolution=(640, 480))
        frame_y = frames[0][:, :, 0]

        # First data block (after sync rows)
        sync_h = SYNC_ROWS * 4
        block1 = frame_y[sync_h:sync_h + 4, 0:4]
        block2 = frame_y[sync_h:sync_h + 4, 4:8]

        assert np.all(block1 == LUMA_HIGH)  # bit 1
        assert np.all(block2 == LUMA_LOW)   # bit 0

    def test_capacity_calculation(self):
        """Should compute correct bits per frame."""
        cap = FrameGenerator._compute_capacity((1280, 720), 4)
        # Width: 1280/4 = 320 cols
        # Usable height: 720 - 2*4 = 712, rows: 712/4 = 178
        expected = 320 * 178
        assert cap == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
