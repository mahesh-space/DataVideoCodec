"""
Integration test: Full encode → decode round-trip.

Verifies that a file can be encoded into a video and decoded
back with a matching SHA-256 hash (FULL_RECOVERY).
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import EncodingParams
from core.utils import compute_hash
from encoder.controller import EncoderController
from decoder.controller import DecoderController


@pytest.fixture
def test_env():
    """Create a temporary directory with a small test file."""
    temp_dir = tempfile.mkdtemp(prefix="dvcodec_test_")
    test_file = Path(temp_dir) / "test_input.txt"

    # Create a small test file (1 KB)
    content = b"DataVideoCodec Integration Test! " * 32  # ~1 KB
    test_file.write_bytes(content)

    yield {
        "temp_dir": temp_dir,
        "test_file": test_file,
        "output_dir": Path(temp_dir) / "encoded",
        "recover_dir": Path(temp_dir) / "recovered",
    }

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRoundTrip:
    """Full encode → decode integration tests."""

    def test_roundtrip_default_params(self, test_env):
        """Encode and decode with default parameters should achieve FULL_RECOVERY."""
        params = EncodingParams(
            resolution=(640, 480),  # Small resolution for fast test
            block_size=4,
            ecc_overhead=0.2,
            fps=1,  # 1 FPS for fewer frames
        )

        # Encode
        encoder = EncoderController()
        video_path, manifest_path = encoder.run_encode(
            input_path=str(test_env["test_file"]),
            output_dir=str(test_env["output_dir"]),
            params=params,
        )

        assert Path(video_path).exists(), "Video file should exist"
        assert Path(manifest_path).exists(), "Manifest file should exist"

        # Decode
        decoder = DecoderController()
        result = decoder.run_decode(
            video_path=str(video_path),
            output_dir=str(test_env["recover_dir"]),
            manifest_path=str(manifest_path),
        )

        assert result.status == "FULL_RECOVERY", (
            f"Expected FULL_RECOVERY, got {result.status}"
        )
        assert result.hash_match is True, "Hash should match"
        assert result.output_path is not None, "Output path should be set"

        # Verify file content
        original_hash = compute_hash(test_env["test_file"])
        recovered_hash = compute_hash(result.output_path)
        assert original_hash == recovered_hash, "SHA-256 hash mismatch"

    def test_roundtrip_large_block(self, test_env):
        """Round trip with 8x8 block size."""
        params = EncodingParams(
            resolution=(640, 480),
            block_size=8,
            ecc_overhead=0.2,
            fps=1,
        )

        encoder = EncoderController()
        video_path, manifest_path = encoder.run_encode(
            str(test_env["test_file"]), str(test_env["output_dir"]), params,
        )

        decoder = DecoderController()
        result = decoder.run_decode(
            str(video_path), str(test_env["recover_dir"]),
            manifest_path=str(manifest_path),
        )

        assert result.status == "FULL_RECOVERY"
        assert result.hash_match is True

    def test_roundtrip_high_ecc(self, test_env):
        """Round trip with 40% ECC overhead."""
        params = EncodingParams(
            resolution=(640, 480),
            block_size=4,
            ecc_overhead=0.4,
            fps=1,
        )

        encoder = EncoderController()
        video_path, manifest_path = encoder.run_encode(
            str(test_env["test_file"]), str(test_env["output_dir"]), params,
        )

        decoder = DecoderController()
        result = decoder.run_decode(
            str(video_path), str(test_env["recover_dir"]),
            manifest_path=str(manifest_path),
        )

        assert result.status == "FULL_RECOVERY"
        assert result.hash_match is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
