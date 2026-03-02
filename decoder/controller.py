"""
DecoderController — orchestrates the complete decoding pipeline.

Coordinates FrameExtractor → SyncDetector → BitExtractor → ECCDecoder
→ FileReconstructor to recover an original file from a video.
"""

import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from core.models import EncodingParams, Manifest, RecoveryResult
from core.utils import get_logger
from encoder.bitstream import BitstreamConverter
from decoder.frame_extractor import FrameExtractor
from decoder.sync_detector import SyncDetector
from decoder.bit_extractor import BitExtractor
from decoder.ecc_decoder import ECCDecoder
from decoder.file_reconstructor import FileReconstructor

logger = get_logger("DecoderController")


class DecoderController:
    """Orchestrates the full video-to-file decoding pipeline.

    Usage:
        controller = DecoderController()
        result = controller.run_decode(
            video_path="document_encoded.mp4",
            output_dir="./recovered",
            manifest_path="document_encoded.json",
        )
        print(result.status)  # FULL_RECOVERY, PARTIAL_RECOVERY, or RECOVERY_FAILURE
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """Initialize the decoder controller.

        Args:
            ffmpeg_path: Path to the FFmpeg executable.
        """
        self.ffmpeg_path = ffmpeg_path

    def run_decode(
        self,
        video_path: str,
        output_dir: str,
        params: Optional[EncodingParams] = None,
        manifest_path: Optional[str] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
    ) -> RecoveryResult:
        """Run the complete decoding pipeline.

        Args:
            video_path: Path to the encoded video file.
            output_dir: Directory for the recovered file.
            params: Decoding parameters. Loaded from manifest if available.
            manifest_path: Path to the encoding manifest JSON.
            progress_cb: Optional callback function(percent, message) for GUI progress.

        Returns:
            RecoveryResult with recovery status and metrics.
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)

        start_time = time.time()
        original_hash = None
        total_ecc_bits = None

        def _progress(pct: float, msg: str):
            if progress_cb:
                progress_cb(pct, msg)
            logger.info(f"[{pct:.0f}%] {msg}")

        # Step 1: Load manifest (if available)
        _progress(5, "Loading manifest...")
        if manifest_path:
            try:
                manifest = Manifest.load(Path(manifest_path))
                params = manifest.params
                original_hash = manifest.original_hash
                total_ecc_bits = manifest.total_ecc_bits
                _progress(8, f"Manifest loaded: {manifest.original_filename}")
            except Exception as e:
                logger.warning(f"Could not load manifest: {e}")

        if params is None:
            params = EncodingParams()
            logger.warning("No manifest found; using default parameters")

        # Step 2: Extract and process frames streaming
        _progress(10, "Initializing video stream...")
        video_info = FrameExtractor.get_video_info(video_path)
        total_frames = video_info["frame_count"]
        
        all_bits = []
        frame_idx = 0
        cached_offset = None  # Cache sync offset after first frame
        
        # Use generator for streaming
        for frame in FrameExtractor.extract(video_path, ffmpeg_path=self.ffmpeg_path):
            frame_idx += 1
            
            # Step 3: Align frame (skip if offset is consistently 0)
            if cached_offset is None:
                aligned = SyncDetector.align(frame, params.block_size)
                frame_y = frame[:, :, 0]
                cached_offset = SyncDetector.detect_offset(frame_y, params.block_size)
            elif cached_offset == 0:
                aligned = frame  # No alignment needed
            else:
                aligned = SyncDetector.align(frame, params.block_size)
            
            # Step 4: Extract bits from this frame
            frame_bits = BitExtractor.extract_frame(
                frame=aligned,
                block_size=params.block_size,
                resolution=params.resolution,
            )
            all_bits.append(frame_bits)
            
            # Update progress smoothly
            if total_frames > 0:
                pct = 10 + (frame_idx / total_frames) * 55
                if frame_idx % 10 == 0 or frame_idx == total_frames:
                    _progress(pct, f"Processing frame {frame_idx}/{total_frames}")
            else:
                if frame_idx % 20 == 0:
                    _progress(10, f"Processing frame {frame_idx}...")

        if not all_bits:
            raise RuntimeError("No bits extracted from video")
            
        raw_bits = np.concatenate(all_bits)
        if total_ecc_bits is not None:
            raw_bits = raw_bits[:total_ecc_bits]
            
        _progress(65, f"Extracted {len(raw_bits)} bits from {frame_idx} frames")

        # Step 5: Convert bits to bytes
        _progress(70, "Converting bitstream to bytes...")
        ecc_bytes = BitstreamConverter.to_bytes(raw_bits)

        # Step 6: ECC decoding
        _progress(75, "Applying Reed-Solomon ECC decoding...")
        corrected_bytes, error_stats = ECCDecoder.decode(ecc_bytes, params.ecc_overhead)
        _progress(
            85,
            f"ECC decoded: {error_stats['errors_corrected']} errors corrected, "
            f"{error_stats['uncorrectable_blocks']} uncorrectable blocks",
        )

        # Step 7: Reconstruct file
        _progress(90, "Reconstructing original file...")
        result = FileReconstructor.reconstruct(
            data=corrected_bytes,
            output_dir=output_dir,
            original_hash=original_hash,
        )

        # Add error stats to result
        result.errors_corrected = error_stats["errors_corrected"]
        result.errors_uncorrectable = error_stats["uncorrectable_blocks"]

        elapsed = time.time() - start_time

        _progress(
            100,
            f"Decoding complete in {elapsed:.1f}s — Status: {result.status}",
        )

        return result
