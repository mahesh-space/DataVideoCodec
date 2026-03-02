"""
EncoderController — orchestrates the complete encoding pipeline.

Coordinates FileReader → BitstreamConverter → ECCEncoder → FrameGenerator
→ VideoAssembler to transform an arbitrary file into a video.
"""

import time
from pathlib import Path
from typing import Callable, Optional, Tuple

from core.models import EncodingParams, Manifest
from core.utils import compute_hash, ensure_dir, get_logger
from encoder.file_reader import FileReader
from encoder.bitstream import BitstreamConverter
from encoder.ecc_encoder import ECCEncoder
from encoder.frame_generator import FrameGenerator
from encoder.video_assembler import VideoAssembler

logger = get_logger("EncoderController")


class EncoderController:
    """Orchestrates the full file-to-video encoding pipeline.

    Usage:
        controller = EncoderController()
        video_path, manifest_path = controller.run_encode(
            input_path="document.pdf",
            output_dir="./output",
            params=EncodingParams(resolution=(1280, 720), block_size=4, ecc_overhead=0.2),
        )
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """Initialize the encoder controller.

        Args:
            ffmpeg_path: Path to the FFmpeg executable.
        """
        self.ffmpeg_path = ffmpeg_path

    def run_encode(
        self,
        input_path: str,
        output_dir: str,
        params: Optional[EncodingParams] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[Path, Path]:
        """Run the complete encoding pipeline.

        Args:
            input_path: Path to the input file.
            output_dir: Directory for output files (video + manifest).
            params: Encoding parameters. Uses defaults if None.
            progress_cb: Optional callback function(percent, message) for GUI progress.

        Returns:
            Tuple of (video_path, manifest_path).

        Raises:
            FileNotFoundError: If input file doesn't exist.
            RuntimeError: If encoding fails.
        """
        if params is None:
            params = EncodingParams()

        input_path = Path(input_path)
        output_dir = Path(output_dir)
        ensure_dir(output_dir)

        start_time = time.time()

        def _progress(pct: float, msg: str):
            if progress_cb:
                progress_cb(pct, msg)
            logger.info(f"[{pct:.0f}%] {msg}")

        # Step 1: Read file
        _progress(5, "Reading input file...")
        raw_bytes, metadata = FileReader.read(input_path)
        original_hash = compute_hash(input_path)

        # Step 2: Build header + payload
        _progress(10, "Converting to bitstream...")
        header = BitstreamConverter.build_header(
            filename=metadata["filename"],
            filesize=metadata["filesize"],
        )
        full_data = header + raw_bytes

        # Step 3: Apply ECC encoding
        _progress(20, f"Applying Reed-Solomon ECC ({params.ecc_overhead*100:.0f}% overhead)...")
        ecc_encoded = ECCEncoder.encode(full_data, params.ecc_overhead)

        # Step 4: Convert to bits
        _progress(35, "Converting to bit array...")
        bit_array = BitstreamConverter.to_bits(ecc_encoded)

        # Step 5: Generate frames
        _progress(40, "Generating video frames...")
        frames = FrameGenerator.generate(
            bit_array=bit_array,
            block_size=params.block_size,
            resolution=params.resolution,
        )
        _progress(70, f"Generated {len(frames)} frames")

        # Step 6: Assemble video
        _progress(75, "Assembling video with FFmpeg...")
        video_filename = input_path.stem + "_encoded.mp4"
        video_path = output_dir / video_filename

        VideoAssembler.assemble(
            frames=frames,
            output_path=video_path,
            fps=params.fps,
            resolution=params.resolution,
            ffmpeg_path=self.ffmpeg_path,
        )
        _progress(90, "Video assembled successfully")

        # Step 7: Write manifest
        _progress(95, "Writing manifest...")
        manifest = Manifest(
            original_filename=metadata["filename"],
            original_filesize=metadata["filesize"],
            original_hash=original_hash,
            params=params,
            frame_count=len(frames),
            total_bits=len(raw_bytes) * 8,
            total_ecc_bits=len(ecc_encoded) * 8,
        )
        manifest_path = video_path.with_suffix(".json")
        manifest.save(manifest_path)

        elapsed = time.time() - start_time
        throughput = metadata["filesize"] / elapsed / 1024 if elapsed > 0 else 0

        _progress(
            100,
            f"Encoding complete in {elapsed:.1f}s "
            f"({throughput:.1f} KB/s) — {len(frames)} frames",
        )

        return video_path, manifest_path
